from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from typing import Any

from ingest import ensure_faiss_index

logger = logging.getLogger(__name__)
from utils import clean_text, parse_response
from multi_ai_fallback import multi_model_verify

# ─────────────────────────────────────────────────────────────
# Normalised verdict labels (match what ingest.py stores in
# document.metadata["label"]).  Raw LIAR labels are NOT used
# here anymore – the mapping lives entirely in ingest.py.
# ─────────────────────────────────────────────────────────────
SUPPORTED_VERDICT = "Supported"
REFUTED_VERDICT   = "Refuted"
UNCERTAIN_VERDICT = "Uncertain"

PROMPT_TEMPLATE = """
You are a strict, evidence-based fact-checking assistant.

Analyse the claim using ONLY the provided context.

Rules:
- Return "Supported"  if the context clearly confirms the claim is true.
- Return "Refuted"    if the context clearly contradicts the claim.
  * Explain precisely WHY the claim is false.
  * State what the correct fact is.
  * Mention the likely origin of the misinformation if apparent
    (e.g., outdated statistics, social-media rumour, misattributed quote).
- Return "Uncertain"  if the context is missing, weak, mixed, or unrelated.
  * Do NOT guess when evidence is insufficient.

Context (retrieved from a verified fact-check database):
{context}

Claim to verify:
{question}

Return EXACTLY one JSON object and nothing else:
{{"status":"Supported|Refuted|Uncertain","confidence":0-100,"summary":"one or two sentences with clear reasoning; if Refuted, state the falsehood, the truth, and the origin"}}
""".strip()


class QAChain:
    def __init__(self, retriever: Any, generator: Any | None) -> None:
        self.retriever = retriever
        self.generator = generator
        self.input_key = "question"

    def _compose_prompt(self, question: str, context: str) -> str:
        return PROMPT_TEMPLATE.format(question=question, context=context)

    def _generate_answer(self, prompt: str) -> str:
        if self.generator is None:
            return ""

        try:
            generated = self.generator(
                prompt,
                max_new_tokens=300,
                do_sample=False,
                temperature=0.0,
                return_full_text=False,
            )
        except Exception:
            return ""

        if isinstance(generated, list) and generated:
            first = generated[0]
            if isinstance(first, dict):
                return str(first.get("generated_text", "") or first.get("text", ""))
            return str(first)

        if isinstance(generated, dict):
            return str(generated.get("generated_text", "") or generated.get("text", ""))

        return str(generated)

    def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        question  = clean_text(str(inputs.get(self.input_key, inputs.get("query", ""))))
        documents = self.retriever.get_relevant_documents(question)
        context   = "\n\n".join(getattr(doc, "page_content", "") for doc in documents)

        if not context.strip():
            final_result = {
                "status":     UNCERTAIN_VERDICT,
                "confidence": 15,
                "summary":    "No related fact-check evidence was found in the knowledge base.",
            }
            return {"result": json.dumps(final_result), "source_documents": documents}

        prompt       = self._compose_prompt(question, context)
        model_answer = self._generate_answer(prompt)

        final_result = _finalize_verdict(question, documents, model_answer)
        return {"result": json.dumps(final_result), "source_documents": documents}


# ─────────────────────────────────────────────────────────────
# Optional local generator (disabled by default for portability)
# ─────────────────────────────────────────────────────────────
def _build_generator() -> Any | None:
    enable = os.getenv("ENABLE_LOCAL_GENERATOR", "0").strip().lower()
    if enable not in {"1", "true", "yes", "on"}:
        return None

    model_name = os.getenv("FACT_CHECK_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    try:
        from transformers import pipeline
    except ImportError:
        return None

    try:
        return pipeline(
            task="text-generation",
            model=model_name,
            max_new_tokens=300,
            do_sample=False,
            temperature=0.0,
            return_full_text=False,
        )
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_qa_chain() -> QAChain:
    db        = ensure_faiss_index()
    retriever = db.as_retriever(search_kwargs={"k": 8})   # fetch 8 for broader recall in production
    return QAChain(retriever=retriever, generator=_build_generator())


# ─────────────────────────────────────────────────────────────
# Context relevance check
# ─────────────────────────────────────────────────────────────
def _context_relevance(question: str, documents: list[Any], min_overlap: int = 2) -> bool:
    """
    FIXED: Stricter relevance check - requires AT LEAST 2 term overlaps.
    
    This prevents the fallback from being triggered on weak matches,
    which was a major source of hallucinations.
    """
    if not documents:
        logger.debug("[RELEVANCE] No documents provided")
        return False

    question_terms = {
        term for term in re.findall(r"[a-z0-9]+", question.lower())
        if len(term) > 2
    }
    if not question_terms:
        logger.debug("[RELEVANCE] No valid terms in question")
        return False

    context_text = " ".join(
        getattr(doc, "page_content", "") for doc in documents
    ).lower()
    if not context_text.strip():
        logger.debug("[RELEVANCE] No context text available")
        return False

    overlap = sum(1 for term in question_terms if term in context_text)
    is_relevant = overlap >= min_overlap
    
    logger.info(f"[RELEVANCE] Q-terms={len(question_terms)}, overlaps={overlap}, min_required={min_overlap}, result={is_relevant}")
    
    return is_relevant


# ─────────────────────────────────────────────────────────────
# Label aggregation from document metadata
# ─────────────────────────────────────────────────────────────
def _label_from_documents(documents: list[Any]) -> str:
    """
    Aggregate the normalised verdict labels stored in document metadata
    (set by ingest.py).  Majority-wins with Refuted taking priority on ties.

    Returns one of "Supported", "Refuted", "Uncertain", or "" if no labels.
    """
    supported_count = 0
    refuted_count   = 0
    uncertain_count = 0

    for doc in documents:
        metadata = getattr(doc, "metadata", {}) or {}
        label    = str(metadata.get("label", "")).strip()

        if label == SUPPORTED_VERDICT:
            supported_count += 1
        elif label == REFUTED_VERDICT:
            refuted_count += 1
        elif label == UNCERTAIN_VERDICT:
            uncertain_count += 1

    total = supported_count + refuted_count + uncertain_count
    if total == 0:
        return ""  # index was built without metadata (legacy)

    if refuted_count > 0 and supported_count == 0:
        return REFUTED_VERDICT
    if supported_count > 0 and refuted_count == 0:
        return SUPPORTED_VERDICT
    if refuted_count > 0 and supported_count > 0:
        # Mixed signals – Refuted wins on tie (conservative / safety-first)
        return REFUTED_VERDICT if refuted_count >= supported_count else SUPPORTED_VERDICT
    if uncertain_count > 0:
        return UNCERTAIN_VERDICT

    return ""


# ─────────────────────────────────────────────────────────────
# Directional-contradiction detector (e.g. "X orbits Y" vs "Y orbits X")
# ─────────────────────────────────────────────────────────────
def _normalize_relation_text(text: str) -> str:
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_orbit_relation(text: str) -> tuple[str, str] | None:
    match = re.match(r"^(.*?)\s+orbits\s+(.*?)$", _normalize_relation_text(text))
    if not match:
        return None
    subject = match.group(1).strip()
    obj     = match.group(2).strip()
    if not subject or not obj:
        return None
    return subject, obj


def _is_directional_contradiction(question: str, documents: list[Any]) -> bool:
    question_relation = _extract_orbit_relation(question)
    if not question_relation or not documents:
        return False

    context_text     = getattr(documents[0], "page_content", "")
    context_relation = _extract_orbit_relation(context_text)
    if not context_relation:
        return False

    q_sub, q_obj = question_relation
    c_sub, c_obj = context_relation
    return q_sub == c_obj and q_obj == c_sub


# ─────────────────────────────────────────────────────────────
# Rich summary builder
# ─────────────────────────────────────────────────────────────
def _build_evidence_text(documents: list[Any], max_chars: int = 240) -> str:
    """Return the most informative snippet from retrieved documents."""
    snippets = []
    for doc in documents:
        content = getattr(doc, "page_content", "").strip()
        if content:
            snippets.append(content)
    combined = " ".join(snippets)
    return clean_text(combined)[:max_chars] if combined else ""


def _make_summary(documents: list[Any], model_answer: str, status: str) -> str:
    """
    Compose a rich, human-readable summary that includes:
      - WHY the claim was supported or refuted
      - The relevant evidence text
      - Speaker attribution when available
    """
    # ── 1. Prefer the model-generated summary if it is rich enough ───────
    if model_answer:
        parsed  = parse_response(model_answer)
        summary = parsed.get("summary", "").strip()
        # Accept model summary if substantial (>40 chars) and not a generic fallback
        if summary and len(summary) > 40 and "No relevant" not in summary and "Not enough" not in summary:
            return summary

    # ── 2. Build summary from document evidence ───────────────────────────
    evidence_text = _build_evidence_text(documents)

    # Collect speaker information for attribution
    speakers = [
        meta.get("speaker", "")
        for doc in documents
        if (meta := getattr(doc, "metadata", {}) or {}) and meta.get("speaker")
    ]
    speaker_attr = f" (claimed by {speakers[0]})" if speakers else ""

    if status == UNCERTAIN_VERDICT:
        if evidence_text:
            return (
                f"Evidence in the knowledge base is insufficient or mixed to render a "
                f"clear verdict{speaker_attr}. Best available context: {evidence_text[:180]}"
            )
        return "The knowledge base does not contain sufficient evidence to verify this claim."

    if status == REFUTED_VERDICT:
        if evidence_text:
            return (
                f"This claim is false{speaker_attr}. "
                f"Fact-check evidence states: {evidence_text}"
            )
        return (
            f"This claim is contradicted by verified fact-check records{speaker_attr}. "
            f"The claim is likely based on misinformation or outdated sources."
        )

    if status == SUPPORTED_VERDICT:
        if evidence_text:
            return (
                f"This claim is supported by verified evidence{speaker_attr}. "
                f"Retrieved context: {evidence_text}"
            )
        return f"The claim is confirmed by retrieved fact-check records{speaker_attr}."

    return "The retrieved evidence is inconclusive."


# ─────────────────────────────────────────────────────────────
# Verdict finalisation — the core decision engine
# ─────────────────────────────────────────────────────────────
def _finalize_verdict(
    question: str,
    documents: list[Any],
    model_answer: str,
) -> dict[str, Any]:
    """
    Combine signals from three sources to produce the final verdict:
      1. Directional-contradiction heuristic (highest priority)
      2. FAISS document metadata labels   (primary signal)
      3. Local LLM model output           (secondary signal, used when labels absent)

    Confidence scoring rationale
    ────────────────────────────
    • Both label & model agree   → 85-92 (strong consensus)
    • Label only (model uncertain) → 76 (label dominates)
    • Model only (no label)       → model's own confidence
    • Label overrides model       → max(model_conf, 72)
    • No relevant context         → 15 (Uncertain)
    """

    # ── Priority 1: directional contradiction ─────────────────────────────
    if _is_directional_contradiction(question, documents):
        return {
            "status":     REFUTED_VERDICT,
            "confidence": 90,
            "summary":    (
                "The retrieved evidence directly contradicts this claim's direction. "
                "The relationship between the entities is the opposite of what is stated."
            ),
        }

    # ── Priority 2: context relevance gate ────────────────────────────────
    if not _context_relevance(question, documents):
        return {
            "status":     UNCERTAIN_VERDICT,
            "confidence": 15,
            "summary":    (
                "No sufficiently related fact-check evidence was found in the knowledge base. "
                "The claim may be outside the dataset's domain."
            ),
        }

    # ── Gather signals ────────────────────────────────────────────────────
    model_parsed = parse_response(model_answer)
    label_verdict = _label_from_documents(documents)

    model_status     = model_parsed["status"]
    model_confidence = model_parsed["confidence"]

    # ── Resolve the final status ──────────────────────────────────────────
    if not label_verdict:
        # No metadata in index (legacy build) — trust model output directly
        status     = model_status
        confidence = model_confidence

    elif label_verdict == model_status:
        # ✅ Full consensus between metadata labels and LLM
        consensus_boost = 7
        status     = label_verdict
        confidence = min(100, max(model_confidence, 82) + consensus_boost)

    elif model_status == UNCERTAIN_VERDICT:
        # LLM unsure, but labels are clear → label wins
        status     = label_verdict
        confidence = 76

    else:
        # Disagreement: label vs model → label takes priority (more reliable)
        status     = label_verdict
        confidence = max(model_confidence, 72)

    # ── Final override: still Uncertain despite clear labels ──────────────
    if status == UNCERTAIN_VERDICT and label_verdict in {SUPPORTED_VERDICT, REFUTED_VERDICT}:
        status     = label_verdict
        confidence = 72

    return {
        "status":     status,
        "confidence": max(0, min(100, int(confidence))),
        "summary":    _make_summary(documents, model_answer, status),
    }


# ─────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────
def verify_claim(text: str) -> Any:
    """
    Run the full RAG pipeline on *text*.
    
    FIXED: Fallback only triggers for TRUE EXCEPTIONS.
    No longer triggers for Uncertain results or missing context.
    """
    evidence_snippets: list[dict[str, str]] = []

    def _fallback(reason: str) -> dict[str, Any]:
        """ONLY use fallback for genuine failures (no docs, exception)."""
        logger.warning(f"[FALLBACK] Triggered: {reason}")
        fallback_ans = multi_model_verify(text)
        parsed = parse_response(fallback_ans)
        parsed["evidence"] = evidence_snippets
        return parsed

    logger.info(f"[VERIFY] Question: {text[:100]}")
    try:
        qa_chain = get_qa_chain()

        if qa_chain.generator is None:
            logger.warning("[VERIFY] Local generator disabled")
            return _fallback("Local text generator disabled or unavailable")

        result = qa_chain.invoke({"question": text})
        answer = str(result.get("result", "") or "").strip()
        documents = result.get("source_documents", []) or []

        logger.info(f"[VERIFY] Retrieved {len(documents)} documents")
        context_preview = " ".join(getattr(doc, "page_content", "") for doc in documents)[:200]
        logger.info(f"[VERIFY] Context: {context_preview}")

        # ONLY use fallback if no docs retrieved (genuine failure)
        if not documents:
            logger.warning("[VERIFY] No documents retrieved")
            return _fallback("No documents retrieved from FAISS")

        for doc in documents[:8]:
            content = getattr(doc, "page_content", "") or ""
            if content.strip():
                meta = getattr(doc, "metadata", {}) or {}
                speaker = str(meta.get("speaker", "")).strip()
                title = str(meta.get("context", "")).strip() or "Fact-Check Source"
                evidence_snippets.append({
                    "title": speaker if speaker else title,
                    "text": content[:300] + ("..." if len(content) > 300 else "")
                })

        if not any(evidence["text"].strip() for evidence in evidence_snippets):
            logger.warning("[VERIFY] No usable evidence text")
            return _fallback("Retrieved documents contain no usable text")

        if not answer:
            logger.warning("[VERIFY] Empty answer from chain")
            return _fallback("Local chain returned an empty answer")

        parsed = parse_response(answer)
        logger.info(f"[VERIFY] Status={parsed.get('status')} Confidence={parsed.get('confidence')}")

        if parsed.get("status") not in {SUPPORTED_VERDICT, REFUTED_VERDICT, UNCERTAIN_VERDICT}:
            logger.warning(f"[VERIFY] Invalid status: {parsed.get('status')}")
            return _fallback("Local chain produced an invalid status")

        # FIXED: DO NOT trigger fallback for Uncertain or low confidence
        # These are valid results! Uncertain is a legitimate verdict.
        logger.info(f"[VERIFY] Final result: {parsed.get('status')} ({parsed.get('confidence')}%)")
        
        parsed["evidence"] = evidence_snippets
        return parsed
    except Exception as exc:
        logger.exception("[VERIFY] Exception in verify_claim")
        return _fallback("Unexpected exception in verify_claim")
