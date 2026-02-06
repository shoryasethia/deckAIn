"""
deckAIn - Visual Reviewer (Gemini Vision)
Uses LLM to review slides and provide optimization feedback.
replaces the deprecated GroqReviewer.
"""

import base64
import os
from typing import Optional
from config.settings import GOOGLE_API_KEY, GEMINI_MODEL
from utils.logger import setup_logger
from google import genai
from google.genai import types

logger = setup_logger(__name__)

class VisualReviewer:
    """
    Review slides for visual quality and content using Gemini Vision.
    """
    
    def __init__(self):
        """Initialize Gemini client."""
        if not GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set. Reviewer disabled.")
            self.client = None
        else:
            self.client = genai.Client(api_key=GOOGLE_API_KEY)
            # Use a vision-capable model. GEMINI_MODEL (gemini-3-flash-preview) is multimodal.
            self.model = GEMINI_MODEL 
            logger.info(f"VisualReviewer initialized with model: {self.model}")
            
    def review_slide(self, image_path: str, slide_context: str) -> str:
        """
        Review a slide image and return critique + optimization tips.
        
        Args:
            image_path: Path to slide image (JPG/PNG)
            slide_context: Text description of slide content
        
        Returns:
            Review feedback string
        """
        if not self.client or not os.path.exists(image_path):
            return "Review skipped (No API key or Image)"
            
        try:
            # Read image bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                
            logger.info(f"Sending slide to Gemini ({self.model})...")
            
            prompt = """You are a Senior Presentation Designer & Investment Banker.
            
            TASK: Critique this PowerPoint slide and provide strict, actionable refactoring code/design instructions.
            
            CONTEXT:
            """ + slide_context + """
            
            Analyze the Visual Layout, Typography, and White Space.
            
            OUTPUT FORMAT:
            1. **Score**: X/10
            2. **Critique**: 2-3 bullet points on what's wrong.
            3. **Optimization Instructions**: Specific changes to make this "Premium/MBB Style" (e.g. "Change header font size to 24pt", "Use a 3-column grid", "Add light gray background #F5F5F5").
            
            Keep it concise."""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=prompt)
                ],
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=1000
                )
            )
            
            feedback = response.text
            logger.info("Gemini visual review received")
            return feedback
            
        except Exception as e:
            logger.error(f"Visual review failed: {e}")
            return f"Review failed: {e}"
