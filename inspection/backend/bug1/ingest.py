from __future__ import annotations

import csv
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Index version stamp.  Bump this string whenever the document
# schema changes to force a full rebuild on next startup.
# ─────────────────────────────────────────────────────────────
_INDEX_VERSION = "v2-labelled"
_VERSION_FILE  = os.path.join("faiss_index", ".index_version")

# LIAR-dataset label → normalised verdict mapping
_LABEL_MAP: dict[str, str] = {
    "true":        "Supported",
    "mostly-true": "Supported",
    "false":       "Refuted",
    "pants-fire":  "Refuted",
    "barely-true": "Refuted",
    "half-true":   "Uncertain",
}


def _map_label(raw: str) -> str | None:
    """Return normalised verdict string or None if label is unknown."""
    return _LABEL_MAP.get(raw.strip().lower())


def _index_is_current() -> bool:
    """Return True iff an up-to-date index exists on disk."""
    if not os.path.exists("faiss_index"):
        return False
    if not os.path.exists(_VERSION_FILE):
        return False
    with open(_VERSION_FILE, "r", encoding="utf-8") as f:
        return f.read().strip() == _INDEX_VERSION


def _write_version_stamp() -> None:
    os.makedirs("faiss_index", exist_ok=True)
    with open(_VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(_INDEX_VERSION)


def _load_documents_from_tsv(filepath: str) -> list:
    """
    Parse a LIAR-format TSV and return a list of langchain Document objects
    with the following metadata preserved per document:

        label    – normalised verdict: "Supported" | "Refuted" | "Uncertain"
        raw_label – original LIAR label string (e.g. "pants-fire")
        speaker  – name of the person who made the claim (col 4)
        context  – venue / context string (col 13)
    """
    from langchain_core.documents import Document

    documents: list[Document] = []
    seen: set[str] = set()  # deduplicate by claim text

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 3:
                continue

            raw_label  = row[1].strip().lower()
            claim_text = row[2].strip()
            verdict    = _map_label(raw_label)

            # Skip unknown labels or empty claims
            if not verdict or not claim_text:
                continue

            # Deduplicate
            key = claim_text.lower()
            if key in seen:
                continue
            seen.add(key)

            # For Refuted claims, prefix the stored text so the embedding
            # space captures the contradiction polarity.
            if verdict == "Refuted":
                page_content = f"It is false that {claim_text}"
            else:
                page_content = claim_text

            metadata: dict[str, str] = {
                "label":     verdict,
                "raw_label": raw_label,
                "speaker":   row[4].strip()  if len(row) > 4  else "",
                "context":   row[13].strip() if len(row) > 13 else "",
                "claim":     claim_text,      # original un-prefixed text
            }

            documents.append(Document(page_content=page_content, metadata=metadata))

    return documents


def _load_documents_from_txt(filepath: str) -> list:
    """Fallback: flat data.txt, no metadata.  Labels will be absent."""
    from langchain_core.documents import Document

    documents: list[Document] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                documents.append(Document(page_content=line, metadata={}))
    return documents


def _vector_count(db: Any) -> int | None:
    index_obj = getattr(db, "index", None) or getattr(db, "_index", None) or getattr(db, "faiss_index", None)
    if index_obj is None:
        return None
    return getattr(index_obj, "ntotal", None) or getattr(index_obj, "nlist", None)


def _create_fallback_corpus() -> list:
    """
    Create a minimal fallback corpus when data files are missing.
    This ensures the system never completely fails on startup.
    """
    from langchain_core.documents import Document
    
    fallback_claims = [
        ("The Earth orbits the Sun.", "Supported"),
        ("Water boils at 100 degrees Celsius.", "Supported"),
        ("The Moon is made of green cheese.", "Refuted"),
        ("COVID-19 is a real pandemic.", "Supported"),
        ("1+1 equals 3.", "Refuted"),
    ]
    
    documents: list[Document] = []
    for claim, verdict in fallback_claims:
        doc = Document(
            page_content=claim,
            metadata={
                "label": verdict,
                "raw_label": "fallback",
                "speaker": "system-fallback",
                "context": "fallback-corpus",
                "claim": claim,
            }
        )
        documents.append(doc)
    
    logger.warning("Using fallback minimal corpus. Deploy train.tsv or data.txt for full functionality.")
    return documents


def ensure_faiss_index():
    """
    Build (or load) the FAISS vector store.

    Build order:
      1. train.tsv  – preferred; full metadata preserved
      2. data.txt   – legacy fallback; no metadata

    The index is automatically rebuilt when _INDEX_VERSION changes.
    """
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # ── Load existing up-to-date index ──────────────────────────────────
    if _index_is_current():
        logger.info("FAISS index exists and version is current. Loading from disk.")
        try:
            db = FAISS.load_local(
                "faiss_index",
                embeddings,
                allow_dangerous_deserialization=True,
            )
            count = _vector_count(db)
            logger.info("Loaded FAISS index with %s vectors.", count if count is not None else "unknown")
            return db
        except Exception as exc:
            logger.exception("Failed to load FAISS index, rebuilding from source: %s", exc)

    # ── Build a fresh index ──────────────────────────────────────────────
    logger.info("Building FAISS index (schema %s)…", _INDEX_VERSION)

    tsv_path = "train.tsv"
    txt_path = "data.txt"

    if os.path.exists(tsv_path):
        documents = _load_documents_from_tsv(tsv_path)
        logger.info("Loaded %s labelled documents from %s.", len(documents), tsv_path)
    elif os.path.exists(txt_path):
        logger.warning("train.tsv not found – falling back to %s (no labels).", txt_path)
        documents = _load_documents_from_txt(txt_path)
        logger.info("Loaded %s documents from %s.", len(documents), txt_path)
    else:
        logger.warning("No data source found. Using minimal fallback corpus.")
        documents = _create_fallback_corpus()

    if not documents:
        raise RuntimeError("Document list is empty after parsing.  Check your data files.")

    db = FAISS.from_documents(documents, embeddings)
    db.save_local("faiss_index")
    _write_version_stamp()
    logger.info("Saved FAISS index (%s documents, version %s).", len(documents), _INDEX_VERSION)
    return db  # ✅ THIS LINE MUST EXIST