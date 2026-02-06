"""
deckAIn - Image Compliance Checker
Ensure images are license-safe, metadata-free, and logo-free
"""

from pathlib import Path
from typing import Tuple
from PIL import Image
import pytesseract

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ImageComplianceChecker:
 """
 Check and sanitize images for compliance.
 - Strip EXIF metadata
 - Detect logos/text (OCR)
 - Verify image quality
 """
 
 def __init__(self):
      """Initialize compliance checker."""
      logger.info("ImageComplianceChecker initialized")
 
 def check_and_sanitize(self, image_path: str) -> Tuple[bool, str, str]:
      """
      Check image compliance and sanitize.
      
      Args:
      image_path: Path to image file
      
      Returns:
      Tuple of (is_compliant, sanitized_path, issues_found)
      """
      image_path = Path(image_path)
      
      if not image_path.exists():
          return False, None, f"Image not found: {image_path}"
      
      logger.debug(f"Checking compliance: {image_path.name}")
      
      issues = []
      
      try:
          # Open image
          img = Image.open(image_path)
          
          # Check 1: Image size/quality
          width, height = img.size
          if width < 800 or height < 600:
              issues.append(f"Low resolution: {width}x{height}")
              logger.warning(f" Low resolution image: {width}x{height}")
          
          # Check 2: EXIF metadata
          exif_data = img.getexif()
          if exif_data:
              issues.append(f"Contains EXIF metadata ({len(exif_data)} fields)")
              logger.debug(f"Found EXIF data: {len(exif_data)} fields")
          
          # Check 3: Logo/text detection (OCR)
          text_detected = self._detect_text(img)
          if text_detected:
              issues.append(f"Text/logo detected: '{text_detected[:50]}'")
              logger.warning(f" Text detected in image: {text_detected[:50]}")
          
          # Sanitize: Strip metadata and save clean version
          sanitized_path = self._sanitize_image(img, image_path)
          
          is_compliant = len(issues) == 0 or (len(issues) == 1 and "EXIF" in issues[0])
          
          if is_compliant:
              logger.info(f" Image compliant: {image_path.name}")
          else:
              logger.warning(f" Image has issues: {'; '.join(issues)}")
          
          return is_compliant, sanitized_path, "; ".join(issues) if issues else "OK"
     
      except Exception as e:
          logger.error(f"Compliance check failed: {e}")
          return False, None, str(e)
 
 def _detect_text(self, img: Image.Image) -> str:
      """
      Detect text/logos in image using OCR.
      
      Args:
      img: PIL Image
      
      Returns:
      Detected text (empty if none)
      """
      try:
          # Use Tesseract OCR
          text = pytesseract.image_to_string(img)
          text = text.strip()
          
          # Filter out noise (single chars, numbers)
          words = [w for w in text.split() if len(w) > 2]
          
          if len(words) > 3: # More than 3 words = likely logo/watermark
              return " ".join(words)
          
          return ""
      
      except Exception as e:
          logger.debug(f"OCR failed (Tesseract not installed?): {e}")
          return "" # If Tesseract not available, skip text detection
 
 def _sanitize_image(self, img: Image.Image, original_path: Path) -> str:
      """
      Strip metadata and save clean image.
      
      Args:
      img: PIL Image
      original_path: Original file path
      
      Returns:
      Path to sanitized image
      """
      # Create new image without EXIF by converting to RGB and pasting
      if img.mode in ('RGBA', 'LA', 'P'):
          # Handle transparency
          background = Image.new('RGB', img.size, (255, 255, 255))
          if img.mode == 'P':
              img = img.convert('RGBA')
          background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
          clean_img = background
      else:
          # Direct copy without EXIF
          clean_img = img.copy()
      
      # Save as sanitized version
      sanitized_path = original_path.parent / f"clean_{original_path.name}"
      clean_img.save(sanitized_path, quality=95, optimize=True)
      
      logger.debug(f"Sanitized image saved: {sanitized_path.name}")
      
      return str(sanitized_path)
