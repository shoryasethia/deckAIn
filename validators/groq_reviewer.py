"""
deckAIn - Slide Reviewer (Groq Vision)
Uses Groq Llama Vision to review slides and return structured fixes.
"""

import base64
import json
import os
from typing import Dict, List, Optional, Any
from groq import Groq

from config.settings import GROQ_API_KEY, GROQ_MODEL
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GroqReviewer:
    """
    Review slides for visual quality and return structured JSON fixes.
    """
    
    def __init__(self):
        """Initialize Groq client."""
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set. Reviewer disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=GROQ_API_KEY)
            logger.info(f"GroqReviewer initialized with model: {GROQ_MODEL}")
    
    def review_slide_for_fixes(self, image_path: str, slide_context: str) -> Dict[str, Any]:
        """
        Review a slide and return structured JSON fixes.
        
        Args:
            image_path: Path to slide image
            slide_context: Description of what slide should contain
            
        Returns:
            Dict with 'score' (0-10) and 'fixes' (list of fix dicts)
        """
        if not self.client or not os.path.exists(image_path):
            return {"score": 10, "fixes": [], "skipped": True}
        
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            logger.info(f"Requesting structured fixes from Groq ({GROQ_MODEL})...")
            
            # Structured JSON prompt
            system_prompt = """You are a Senior Presentation Designer reviewing PowerPoint slides for Kelp Global.

KELP BRANDING REQUIREMENTS (CRITICAL):
1. Header: Must have "Kelp" text/logo at top left + slide title
2. Footer: Must say "Strictly Private & Confidential – Prepared by Kelp M&A Team" (9pt, centered)
3. Colors: Dark indigo headers (#1A237E), white backgrounds, professional palette
4. Typography: Arial headings (20-24pt), body text (10-12pt)
5. Layout: Clean, 3-4 quadrants, no text walls, professional imagery

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{
  "score": <0-10>,
  "issues": ["issue1", "issue2", "issue3"],
  "fixes": [
    {"type": "font", "shape": <shape_index>, "size": <pt_size>, "bold": <true/false>},
    {"type": "color", "shape": <shape_index>, "color": "<hex>"},
    {"type": "position", "shape": <shape_index>, "y": <inches>},
    {"type": "chart_label", "chart": <chart_index>, "size": <pt_size>}
  ]
}

Fix types available:
- font: change text size/bold/italic (shape = shape index 0-based)
- color: change text color (hex like "#333333")
- position: move shape (x, y, width, height in inches)
- chart_label: change chart data label size

Score 8+ means no fixes needed. Focus on: Kelp branding compliance, text readability, visual hierarchy, professional appearance. Max 5 fixes per review."""

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Slide context: {slide_context}\n\nReview and return JSON:"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                model=GROQ_MODEL,
                temperature=0.2,
                max_tokens=500
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            
            # Parse JSON (handle markdown code blocks)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            
            # Validate structure
            if "score" not in result:
                result["score"] = 5
            if "fixes" not in result:
                result["fixes"] = []
            
            logger.info(f"Groq review: score={result['score']}, fixes={len(result.get('fixes', []))}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Groq JSON: {e}")
            return {"score": 7, "fixes": [], "parse_error": True}
        except Exception as e:
            error_msg = str(e)
            if "messages[1].content must be a string" in error_msg:
                logger.warning(f"Groq Model {GROQ_MODEL} is text-only. Skipping.")
            elif "model_not_found" in error_msg or "404" in error_msg:
                logger.warning(f"Groq Model {GROQ_MODEL} not found.")
            else:
                logger.error(f"Groq review failed: {e}")
            return {"score": 10, "fixes": [], "error": str(e)}
    
    def review_slide(self, image_path: str, slide_context: str) -> str:
        """Legacy method - returns prose for markdown report."""
        result = self.review_slide_for_fixes(image_path, slide_context)
        
        if result.get("skipped") or result.get("error"):
            return f"Review skipped: {result.get('error', 'No API key')}"
        
        output = [f"**Score: {result['score']}/10**"]
        
        if result.get("issues"):
            output.append("\n**Issues:**")
            for issue in result["issues"][:3]:
                output.append(f"- {issue}")
        
        if result.get("fixes"):
            output.append(f"\n**Fixes Applied:** {len(result['fixes'])}")
        
        return "\n".join(output)

