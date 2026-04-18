from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - handled gracefully at runtime
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - handled gracefully at runtime
    BeautifulSoup = None

try:
    import pytesseract
except ImportError:  # pragma: no cover - handled gracefully at runtime
    pytesseract = None


STATUS_VALUES = {"Supported", "Refuted", "Uncertain"}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_text(text: str) -> str:
    return normalize_text(text)


def configure_tesseract() -> bool:
    """Configure pytesseract to find Tesseract executable."""
    if pytesseract is None:
        return False

    # Try environment variable first (user-set)
    if os.getenv("TESSERACT_CMD"):
        tesseract_cmd = Path(os.getenv("TESSERACT_CMD"))
        if tesseract_cmd.exists():
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_cmd)
            import logging
            logging.getLogger(__name__).info(f"[CONFIG] Using TESSERACT_CMD env var: {tesseract_cmd}")
            return True

    # Standard Windows locations
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"D:\programs\tesseract\tesseract.exe",
        "/usr/bin/tesseract",  # Linux
        "/usr/local/bin/tesseract",  # macOS
        "/opt/homebrew/bin/tesseract",  # M1/M2 macOS
    ]

    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate_path)
            import logging
            logging.getLogger(__name__).info(f"[CONFIG] Found Tesseract at: {candidate_path}")
            return True

    import logging
    logging.getLogger(__name__).warning(
        "[CONFIG] Tesseract not found in standard locations. "
        "Set TESSERACT_CMD environment variable to the full path of tesseract.exe"
    )
    return False


def extract_text_from_image(image: Any) -> str:
    """Extract text from image using Tesseract OCR with enhanced preprocessing."""
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed. Install with: pip install pytesseract")

    import logging
    logger = logging.getLogger(__name__)

    # CRITICAL: Configure Tesseract path FIRST
    if not configure_tesseract():
        logger.warning("[OCR] Tesseract not found - will try anyway (may fail)")

    try:
        from PIL import Image, ImageEnhance, ImageFilter

        # 1. Resize (upscale 2x for better text extraction if not already huge)
        width, height = image.size
        original_size = (width, height)
        logger.info(f"[OCR] Original image size: {original_size}")
        
        if width < 2000 and height < 2000:
            resample_method = getattr(Image, "Resampling", Image).LANCZOS
            image = image.resize((width * 2, height * 2), resample_method)
            logger.info(f"[OCR] Upscaled to: {image.size}")

        # 2. Convert to Grayscale
        image = image.convert("L")
        logger.info("[OCR] Converted to grayscale")

        # 3. Increase Contrast (more aggressive for better text detection)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        logger.info("[OCR] Enhanced contrast (2.5x)")

        # 4. Increase Brightness (helps with dark text)
        brightness_enhancer = ImageEnhance.Brightness(image)
        image = brightness_enhancer.enhance(1.2)
        logger.info("[OCR] Enhanced brightness (1.2x)")

        # 5. Apply Noise Reduction (Median Blur)
        image = image.filter(ImageFilter.MedianFilter(size=3))
        logger.info("[OCR] Applied noise reduction")
        
        # 6. Optional: Apply Sharpening for crisp text
        image = image.filter(ImageFilter.SHARPEN)
        logger.info("[OCR] Applied sharpening")

    except Exception as e:
        logger.warning(f"[OCR] Image preprocessing failed: {e}. Falling back to raw image.")

    try:
        logger.info("[OCR] Starting Tesseract OCR processing...")
        
        # Use enhanced OCR config for better accuracy
        custom_config = r'--oem 3 --psm 6'
        extracted = pytesseract.image_to_string(image, config=custom_config)
        
        logger.info(f"[OCR] Extracted {len(extracted)} characters")
        if extracted.strip():
            logger.info(f"[OCR] Text preview: {extracted[:100]}")
        else:
            logger.warning("[OCR] No text detected in image")
            
    except FileNotFoundError as e:
        logger.error(f"[OCR] Tesseract executable not found: {e}")
        raise RuntimeError(
            "Tesseract OCR not installed or not found. Download from: "
            "https://github.com/UB-Mannheim/tesseract/wiki and install, "
            "then restart the backend."
        )
    except Exception as e:
        logger.error(f"[OCR] Tesseract processing failed: {e}")
        extracted = ""

    return clean_text(extracted)


async def extract_text_from_url(url: str) -> str:
    try:
        import httpx
    except ImportError:
        return ""
        
    if BeautifulSoup is None:
        return ""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FactCheckBot/1.0)"},
                follow_redirects=True,
            )
            response.raise_for_status()
    except httpx.RequestError:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        element.extract()

    text = soup.get_text(separator=" ", strip=True)
    return clean_text(text[:50000])[:4000]


def _coerce_confidence(value: Any, default: int = 50) -> int:
    try:
        confidence = int(float(value))
    except (TypeError, ValueError):
        confidence = default

    return max(0, min(100, confidence))


def _extract_json_blob(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    blob = match.group(0)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        blob = blob.replace("'", '"')
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return None


def parse_response(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        if {"status", "confidence", "summary"}.issubset(response.keys()):
            return {
                "status": response.get("status", "Uncertain"),
                "confidence": _coerce_confidence(response.get("confidence"), 50),
                "summary": str(response.get("summary", "Not enough evidence.")),
            }

        if "result" in response:
            return parse_response(response["result"])

    text = normalize_text(str(response or ""))
    if not text:
        return {
            "status": "Uncertain",
            "confidence": 20,
            "summary": "No usable model output was returned.",
        }

    parsed = _extract_json_blob(text)
    if isinstance(parsed, dict):
        status = str(parsed.get("status", "Uncertain")).strip().title()
        if status not in STATUS_VALUES:
            status = "Uncertain"

        return {
            "status": status,
            "confidence": _coerce_confidence(parsed.get("confidence"), 50 if status == "Uncertain" else 75),
            "summary": normalize_text(str(parsed.get("summary", "Not enough evidence."))) or "Not enough evidence.",
        }

    lowered = text.lower()
    if any(keyword in lowered for keyword in ("supported", "consistent with", "confirmed", "accurate")):
        status = "Supported"
        confidence = 78
        summary = text
    elif any(keyword in lowered for keyword in ("refuted", "false", "contradict", "incorrect", "unsupported")):
        status = "Refuted"
        confidence = 78
        summary = text
    else:
        status = "Uncertain"
        confidence = 30
        summary = text

    if len(summary) > 220:
        summary = summary[:217].rstrip() + "..."

    return {
        "status": status,
        "confidence": confidence,
        "summary": summary,
    }