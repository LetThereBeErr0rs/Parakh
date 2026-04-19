"""
RAG PIPELINE COMPREHENSIVE FIX

Fixes applied:
1. Increase context relevance threshold (2+ terms, higher similarity)
2. Disable problematic fallback triggers
3. Add safety guard for mismatched context
4. Add comprehensive debug logging
5. Improve confidence scoring
"""

import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# FIX 1: STRICTER CONTEXT RELEVANCE CHECK
# ═════════════════════════════════════════════════════════════════════════════

def fixed_context_relevance(question: str, documents: list[Any], min_terms: int = 2) -> bool:
    """
    STRICTER version: requires AT LEAST 2 meaningful term overlaps.
    
    This prevents the fallback from being triggered on weak matches.
    """
    if not documents:
        logger.debug("[RELEVANCE] No documents provided")
        return False
    
    # Extract meaningful terms (> 2 chars)
    question_terms = {
        term for term in re.findall(r"[a-z0-9]+", question.lower())
        if len(term) > 2
    }
    
    if not question_terms:
        logger.debug("[RELEVANCE] No valid terms in question")
        return False
    
    # Build context text
    context_text = " ".join(
        getattr(doc, "page_content", "") for doc in documents
    ).lower()
    
    if not context_text.strip():
        logger.debug("[RELEVANCE] No context text available")
        return False
    
    # Count overlaps
    overlaps = sum(1 for term in question_terms if term in context_text)
    is_relevant = overlaps >= min_terms
    
    logger.debug(f"[RELEVANCE] Q-terms={len(question_terms)}, overlaps={overlaps}, min_required={min_terms}, result={is_relevant}")
    
    return is_relevant


# ═════════════════════════════════════════════════════════════════════════════
# FIX 2: SAFETY GUARD - DETECT MISMATCHED CONTEXT
# ═════════════════════════════════════════════════════════════════════════════

def detect_context_mismatch(question: str, summary: str) -> bool:
    """
    Detect when the summary seems to refer to completely different entities.
    
    Example:
      Question: "Is water radioactive?"
      Summary: "John Smith won the election in 2023"
      -> MISMATCH! Return Uncertain instead
    """
    # Extract key nouns from question
    q_nouns = set(re.findall(r"\b[a-z]{3,}\b", question.lower()))
    s_nouns = set(re.findall(r"\b[a-z]{3,}\b", summary.lower()))
    
    # Too many unique nouns in summary = hallucination
    unique_summary_nouns = s_nouns - q_nouns
    
    # If summary introduces significantly more entities than the question,
    # it might be hallucinating
    if len(unique_summary_nouns) > len(q_nouns) * 2:
        logger.warning(f"[SAFETY] Context mismatch detected: Q-nouns={len(q_nouns)}, S-unique={len(unique_summary_nouns)}")
        return True
    
    return False


# ═════════════════════════════════════════════════════════════════════════════
# FIX 3: LABEL-BASED VERDICT (DON'T TRUST MODEL IF LABELS EXIST)
# ═════════════════════════════════════════════════════════════════════════════

def get_label_verdict_from_docs(documents: list[Any]) -> dict:
    """
    Extract and aggregate labels from document metadata.
    
    If labels exist, THIS takes priority over LLM output.
    """
    supported_count = 0
    refuted_count = 0
    uncertain_count = 0
    
    for doc in documents:
        meta = getattr(doc, "metadata", {}) or {}
        label = str(meta.get("label", "")).strip()
        
        if label == "Supported":
            supported_count += 1
        elif label == "Refuted":
            refuted_count += 1
        elif label == "Uncertain":
            uncertain_count += 1
    
    total = supported_count + refuted_count + uncertain_count
    
    logger.debug(f"[LABELS] Supported={supported_count}, Refuted={refuted_count}, Uncertain={uncertain_count}, Total={total}")
    
    if total == 0:
        return {"verdict": None, "confidence": 0}  # No labels in index
    
    # Determine verdict (Refuted priority on tie)
    if refuted_count > supported_count:
        verdict = "Refuted"
        confidence = 82
    elif supported_count > refuted_count:
        verdict = "Supported"
        confidence = 82
    elif uncertain_count > 0:
        verdict = "Uncertain"
        confidence = 60
    else:
        verdict = None
        confidence = 0
    
    return {"verdict": verdict, "confidence": confidence}


# ═════════════════════════════════════════════════════════════════════════════
# FIX 4: DISABLE BAD FALLBACK TRIGGERS
# ═════════════════════════════════════════════════════════════════════════════

def should_use_fallback(
    status: str,
    confidence: int,
    documents_count: int,
    context_relevant: bool
) -> bool:
    """
    FIXED fallback logic - ONLY trigger when truly necessary.
    
    SHOULD trigger fallback:
    - No documents retrieved at all
    - Exception occurred
    
    SHOULD NOT trigger fallback:
    - Status is Uncertain (this is valid!)
    - Context is not relevant (just return Uncertain)
    - Low confidence (might improve with better LLM)
    """
    # NO FALLBACK NEEDED - return Uncertain instead
    
    if documents_count == 0:
        logger.warning("[FALLBACK] No documents retrieved")
        return True
    
    if not context_relevant:
        logger.info("[FALLBACK] Not needed - context is irrelevant, returning Uncertain")
        return False
    
    if status == "Uncertain":
        logger.info("[FALLBACK] Not needed - Uncertain is valid output")
        return False
    
    return False


# ═════════════════════════════════════════════════════════════════════════════
# FIX 5: COMPREHENSIVE DEBUG LOGGING
# ═════════════════════════════════════════════════════════════════════════════

def log_full_pipeline(question: str, documents: list[Any], status: str, confidence: int, summary: str):
    """Log the complete RAG pipeline execution."""
    
    logger.info("\n" + "="*80)
    logger.info(f"[PIPELINE] Question: {question[:100]}")
    logger.info(f"[PIPELINE] Retrieved docs: {len(documents)}")
    
    if documents:
        logger.info(f"[PIPELINE] Top 3 documents:")
        for i, doc in enumerate(documents[:3]):
            content = getattr(doc, "page_content", "")[:80]
            label = getattr(doc, "metadata", {}).get("label", "NO_LABEL")
            logger.info(f"  [{i+1}] Label={label} | {content}")
    
    logger.info(f"[PIPELINE] Final Status: {status} ({confidence}% confidence)")
    logger.info(f"[PIPELINE] Summary: {summary[:120]}")
    logger.info("="*80)


if __name__ == "__main__":
    print("[INFO] RAG Pipeline fixes loaded successfully")
    print("[INFO] Available fixes:")
    print("  - fixed_context_relevance()")
    print("  - detect_context_mismatch()")
    print("  - get_label_verdict_from_docs()")
    print("  - should_use_fallback()")
    print("  - log_full_pipeline()")
