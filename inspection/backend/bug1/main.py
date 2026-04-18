from __future__ import annotations

import asyncio
import io
import logging
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Any
from datetime import datetime

from rag import verify_claim
from utils import clean_text, configure_tesseract, extract_text_from_image, extract_text_from_url, parse_response


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fact-Checking API",
    description="Verify claims from text, image, or URL using retrieval-augmented generation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextRequest(BaseModel):
    text: str = Field(..., max_length=15000, description="The textual claim to fact-check")


class URLRequest(BaseModel):
    url: HttpUrl = Field(..., description="The source URL to scrape and fact-check")


class HistoryItem(BaseModel):
    claim_text: str = Field(..., max_length=2000)
    verdict: str = Field(..., max_length=100)
    timestamp: str = Field(..., max_length=100)

def init_db():
    with sqlite3.connect("history.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_text TEXT,
                verdict TEXT,
                timestamp TEXT
            )
        """)

def _structured_response(result: dict[str, object]) -> dict[str, object]:
    parsed = parse_response(result)
    res = {
        "status": parsed["status"],
        "confidence": parsed["confidence"],
        "summary": parsed["summary"],
        "evidence": result.get("evidence", []) if isinstance(result, dict) else [],
    }
    return res


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    configure_tesseract()
    
    # Validate environment setup for production
    gemini_keys = [
        os.getenv("GEMINI_API_KEY_1"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3"),
        os.getenv("GEMINI_API_KEY_4"),
    ]
    valid_keys = [k for k in gemini_keys if k]
    
    if not valid_keys:
        logger.warning("⚠️ No GEMINI_API_KEY_n environment variables found. Set them in production via Render dashboard.")
    else:
        logger.info("✓ Found %d valid Gemini API key(s) configured.", len(valid_keys))
    
    try:
        from rag import get_qa_chain
        qa_chain = get_qa_chain()
        logger.info("✓ RAG pipeline initialized successfully")
    except Exception as e:
        logger.exception("RAG warmup failed during startup: %s", e)
    
    logger.info("✓ Fact-checking API started")
    logger.info("✓ System ready")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Fact-checking API is running"}


@app.get("/health")
def health() -> dict[str, object]:
    """Diagnostic endpoint to check deployment status (development only)."""
    gemini_keys = [
        os.getenv("GEMINI_API_KEY_1"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3"),
        os.getenv("GEMINI_API_KEY_4"),
    ]
    valid_gemini_count = sum(1 for k in gemini_keys if k)
    
    faiss_exists = os.path.exists("faiss_index") and os.path.exists("faiss_index/.index_version")
    data_exists = os.path.exists("train.tsv") or os.path.exists("data.txt")
    
    return {
        "status": "running",
        "gemini_api_keys_configured": valid_gemini_count,
        "faiss_index_exists": faiss_exists,
        "data_sources_available": data_exists,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/history")
def get_history() -> list[HistoryItem]:
    try:
        with sqlite3.connect("history.db") as conn:
            cur = conn.execute("SELECT claim_text, verdict, timestamp FROM history ORDER BY id DESC LIMIT 10")
            return [HistoryItem(claim_text=row[0], verdict=row[1], timestamp=row[2]) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"DB Read Error: {e}")
        return []


@app.post("/history")
def post_history(item: HistoryItem) -> dict[str, str]:
    try:
        with sqlite3.connect("history.db") as conn:
            conn.execute(
                "INSERT INTO history (claim_text, verdict, timestamp) VALUES (?, ?, ?)",
                (item.claim_text, item.verdict, item.timestamp)
            )
        return {"message": "History saved"}
    except Exception as e:
        logger.error(f"DB Write Error: {e}")
        return {"message": "Failed to save history"}


@app.post("/verify-text")
async def verify_text(req: TextRequest) -> dict[str, object]:
    text = clean_text(req.text)
    if not text:
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")

    try:
        result = await asyncio.to_thread(verify_claim, text)
        return _structured_response(result)
    except Exception:
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "The claim could not be verified due to an unexpected backend error.",
            "evidence": [],
        }


@app.post("/verify")
async def verify_legacy(req: TextRequest) -> dict[str, object]:
    return await verify_text(req)


@app.post("/verify-url")
async def verify_url(req: URLRequest) -> dict[str, object]:
    try:
        text = await extract_text_from_url(str(req.url))
    except Exception:
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "The URL could not be scraped or did not contain enough readable text.",
            "evidence": [],
        }
    if not text:
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "The URL could not be scraped or did not contain enough readable text.",
            "evidence": [],
        }

    try:
        result = await asyncio.to_thread(verify_claim, text)
        return _structured_response(result)
    except Exception:
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "The URL content could not be verified due to an unexpected backend error.",
            "evidence": [],
        }


@app.post("/verify-image")
async def verify_image(file: UploadFile = File(...)) -> dict[str, object]:
    try:
        contents = await file.read()
        from PIL import Image, UnidentifiedImageError

        image = Image.open(io.BytesIO(contents))
        logger.info(f"📸 Image loaded: {file.filename} ({image.format}, {image.size})")
        
        try:
            text = await asyncio.to_thread(extract_text_from_image, image)
        except RuntimeError as e:
            # Tesseract not installed
            logger.error(f"⚠️ Tesseract error: {str(e)}")
            return {
                "status": "Uncertain",
                "confidence": 0,
                "summary": f"OCR service unavailable: {str(e)}. The system cannot extract text from images yet.",
                "evidence": [],
            }
            
    except (UnidentifiedImageError, OSError):
        logger.error("❌ Invalid image format or corrupted file")
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "The uploaded file could not be processed as a readable image. Try JPG, PNG, or WEBP format.",
            "evidence": [],
        }
    except Exception as e:
        logger.exception(f"❌ Image processing error: {e}")
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": f"The image could not be verified due to an error: {str(e)[:100]}",
            "evidence": [],
        }

    if not text or len(text.strip()) < 3:
        logger.warning("⚠️ No text detected in image (or text too short)")
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "No readable text was found in the image. Try: clearer text, higher resolution, better lighting.",
            "evidence": [],
        }

    logger.info(f"✓ Extracted {len(text)} characters from image")

    try:
        result = await asyncio.to_thread(verify_claim, text)
        logger.info(f"✓ Verification complete: {result.get('status')}")
        return _structured_response(result)
    except Exception as e:
        logger.exception(f"❌ Verification failed: {e}")
        return {
            "status": "Uncertain",
            "confidence": 0,
            "summary": "The image text could not be verified due to an unexpected backend error.",
            "evidence": [],
        }
            "evidence": [],
        }