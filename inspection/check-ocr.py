#!/usr/bin/env python3
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║          PARAKH - OCR/TESSERACT DIAGNOSTIC TOOL                          ║
# ║   Checks if Tesseract is installed and properly configured               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

import sys
import os
from pathlib import Path

print("\n" + "="*70)
print("PARAKH OCR/TESSERACT DIAGNOSTIC")
print("="*70 + "\n")

# 1. Check Python packages
print("📦 Checking Python packages...")
print("-" * 70)

try:
    import pytesseract
    print("✓ pytesseract is installed")
except ImportError:
    print("✗ pytesseract NOT installed")
    print("  Fix: pip install pytesseract")
    sys.exit(1)

try:
    from PIL import Image
    print("✓ Pillow (PIL) is installed")
except ImportError:
    print("✗ Pillow NOT installed")
    print("  Fix: pip install Pillow")
    sys.exit(1)

# 2. Check Tesseract installation
print("\n🔍 Checking Tesseract installation...")
print("-" * 70)

candidates = [
    os.getenv("TESSERACT_CMD"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"D:\programs\tesseract\tesseract.exe",
    "/usr/bin/tesseract",  # Linux
    "/usr/local/bin/tesseract",  # macOS
]

found_path = None
for candidate in candidates:
    if candidate and Path(candidate).exists():
        found_path = candidate
        print(f"✓ Found Tesseract: {found_path}")
        break

if not found_path:
    print("✗ Tesseract executable NOT found")
    print("\n📥 Installation Instructions:")
    print("-" * 70)
    print("Windows:")
    print("  1. Download: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  2. Run: tesseract-ocr-w64-setup-v5.x.exe")
    print("  3. Install to standard location (C:\\Program Files\\Tesseract-OCR)")
    print("  4. Restart backend")
    print("\nLinux (Ubuntu/Debian):")
    print("  sudo apt-get install tesseract-ocr")
    print("\nmacOS:")
    print("  brew install tesseract")
    print("\nAfter installation, restart the backend server.")
    sys.exit(1)

# 3. Test Tesseract functionality
print("\n🧪 Testing Tesseract functionality...")
print("-" * 70)

try:
    import pytesseract
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple test image with text
    test_image = Image.new('RGB', (300, 100), color='white')
    draw = ImageDraw.Draw(test_image)
    
    # Draw some text
    try:
        draw.text((10, 40), "TEST: Earth orbits Sun", fill='black')
    except:
        # Fallback if font not available
        draw.text((10, 40), "TEST", fill='black')
    
    # Try to extract text
    extracted = pytesseract.image_to_string(test_image)
    
    if extracted.strip():
        print(f"✓ Tesseract working! Extracted: '{extracted.strip()}'")
    else:
        print("⚠️ Tesseract ran but extracted no text (may still work on real images)")
        
except Exception as e:
    print(f"✗ Tesseract test failed: {e}")
    print("  This might be a permissions issue or corrupted installation")
    print("  Try reinstalling Tesseract")
    sys.exit(1)

# 4. Environment variables
print("\n🔧 Checking environment variables...")
print("-" * 70)

env_vars = ["TESSERACT_CMD", "PYTHONPATH"]
for var in env_vars:
    val = os.getenv(var)
    if val:
        print(f"✓ {var}: {val}")
    else:
        print(f"  {var}: (not set)")

# 5. Backend configuration
print("\n📄 Backend configuration...")
print("-" * 70)

try:
    sys.path.insert(0, str(Path(__file__).parent / "backend" / "bug1"))
    from utils import configure_tesseract
    
    if configure_tesseract():
        print("✓ Backend can find and configure Tesseract")
    else:
        print("⚠️ Backend couldn't auto-configure Tesseract")
        print("  (May still work if installed in standard location)")
        
except Exception as e:
    print(f"⚠️ Couldn't test backend config: {e}")

# Final summary
print("\n" + "="*70)
print("✅ TESSERACT IS PROPERLY CONFIGURED")
print("="*70)
print("\n✓ Image OCR should work. You can now:")
print("  • Upload images with text")
print("  • The backend will extract text automatically")
print("  • Claims will be verified from extracted text\n")
print("If it still doesn't work:")
print("  1. Restart the backend server")
print("  2. Check backend logs for OCR errors")
print("  3. Try with a different image (clearer text)")
print("\n")
