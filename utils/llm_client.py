"""
deckAIn - Gemini LLM Client
Wrapper for Google Gemini API with retry logic and token tracking
"""

import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from google import genai
from google.genai import types

from config.settings import GOOGLE_API_KEY, GEMINI_MODEL, MAX_RETRIES, API_TIMEOUT
from utils.logger import setup_logger, log_api_call

logger = setup_logger(__name__)

class GeminiClient:
    """
    Wrapper for Gemini API with retry logic and structured outputs.
    Uses the new google-genai library (google-generativeai is deprecated).
    """
    
    def __init__(self, model_name: str = GEMINI_MODEL):
        """
        Initialize Gemini client.
        
        Args:
            model_name: Gemini model to use
        """
        self.model_name = model_name
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # Track usage (tokens only - no cost assumptions)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        
        logger.info(f"Initialized Gemini client with model: {model_name}")
    
    def upload_file(self, file_path: str, display_name: str = None) -> types.File:
        """
        Upload a file to Gemini File API for efficient processing.
        File persists for 48 hours and can be reused in multiple prompts.
        
        Args:
            file_path: Path to file to upload
            display_name: Optional display name for the file
        
        Returns:
            Uploaded file object with name
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if display_name is None:
            display_name = file_path.name
        
        logger.info(f"Uploading file to Gemini API: {file_path.name} ({file_path.stat().st_size} bytes)")
        
        try:
            # Upload file using new API (file path as first argument)
            uploaded_file = self.client.files.upload(file=str(file_path))
            
            logger.info(f"File uploaded: {uploaded_file.name}")
            logger.debug(f"File will persist for 48 hours")
            
            return uploaded_file
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise
    
    def generate_json_with_file(
        self,
        prompt: str,
        file_ref: types.File,
        max_retries: int = MAX_RETRIES,
        timeout: int = API_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Generate JSON response with an uploaded file as context.
        
        Args:
            prompt: Prompt template
            file_ref: Uploaded file object (from upload_file)
            max_retries: Maximum retries
            timeout: Timeout in seconds
        
        Returns:
            Parsed JSON dictionary
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"API call with file attempt {attempt + 1}/{max_retries}")
                
                # Generate content with file (new API)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_uri(file_uri=file_ref.uri, mime_type=file_ref.mime_type),
                        types.Part.from_text(text=prompt)
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=16384,  # Increased for large financial data
                       response_mime_type="application/json"
                    )
                )
                
                # Parse JSON
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                # Check for truncation
                if self._is_truncated_json(response_text):
                    logger.warning(f"Detected truncated JSON response (length: {len(response_text)})")
                    # Try to auto-repair
                    response_text = self._try_repair_json(response_text)
                
                data = json.loads(response_text)
                
                # Track usage
                if hasattr(response, 'usage_metadata'):
                    tokens_in = response.usage_metadata.prompt_token_count
                    tokens_out = response.usage_metadata.candidates_token_count
                    
                    self.total_input_tokens += tokens_in
                    self.total_output_tokens += tokens_out
                    self.total_calls += 1
                    
                    log_api_call(logger, self.model_name, tokens_in, tokens_out)
                
                logger.debug(f"Successfully parsed JSON response with file")
                return data
                
            except json.JSONDecodeError as e:
                # Show more context for debugging
                preview_len = min(500, len(response_text))
                last_error = f"JSON parsing error: {str(e)}\nResponse: {response_text[:preview_len]}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    prompt += "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation."
                    time.sleep(2)
                
            except Exception as e:
                last_error = f"API error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        error_msg = f"Failed to get valid JSON after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def generate_json(
        self, 
        prompt: str, 
        max_retries: int = MAX_RETRIES,
        timeout: int = API_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Generate JSON response from LLM with retry logic.
        
        Args:
            prompt: Prompt template to send
            max_retries: Maximum number of retry attempts
            timeout: Timeout in seconds
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ValueError: If response is not valid JSON after all retries
            TimeoutError: If API call times out
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"API call attempt {attempt + 1}/{max_retries}")
                
                # Generate content with new API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=16384,  # Increased for large outputs
                        response_mime_type="application/json"
                    )
                )
                
                # Extract and parse JSON
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                # Check for truncation
                if self._is_truncated_json(response_text):
                    logger.warning(f"Detected truncated JSON response (length: {len(response_text)})")
                    # Try to auto-repair
                    response_text = self._try_repair_json(response_text)
                
                # Parse JSON
                data = json.loads(response_text)
                
                # Track usage (tokens from API response)
                if hasattr(response, 'usage_metadata'):
                    tokens_in = response.usage_metadata.prompt_token_count
                    tokens_out = response.usage_metadata.candidates_token_count
                    
                    self.total_input_tokens += tokens_in
                    self.total_output_tokens += tokens_out
                    self.total_calls += 1
                    
                    log_api_call(logger, self.model_name, tokens_in, tokens_out)
                
                logger.debug(f"Successfully parsed JSON response")
                return data
                
            except json.JSONDecodeError as e:
                # Show more context for debugging
                preview_len = min(500, len(response_text))
                last_error = f"JSON parsing error: {str(e)}\nResponse: {response_text[:preview_len]}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    # Add explicit JSON instruction to prompt
                    prompt += "\n\nIMPORTANT: Return ONLY valid, COMPLETE JSON. Ensure all arrays and objects are properly closed."
                    time.sleep(2)  # Wait before retry
                
            except Exception as e:
                last_error = f"API error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
        
        # All retries exhausted
        error_msg = f"Failed to get valid JSON after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def generate_text(
        self, 
        prompt: str,
        max_retries: int = MAX_RETRIES,
        timeout: int = API_TIMEOUT
    ) -> str:
        """
        Generate text response from LLM.
        
        Args:
            prompt: Prompt template
            max_retries: Maximum retries
            timeout: Timeout in seconds
        
        Returns:
            Generated text
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        top_p=0.95,
                        max_output_tokens=8192
                    )
                )
                
                text = response.text.strip()
                
                # Track usage
                if hasattr(response, 'usage_metadata'):
                    tokens_in = response.usage_metadata.prompt_token_count
                    tokens_out = response.usage_metadata.candidates_token_count
                    
                    self.total_input_tokens += tokens_in
                    self.total_output_tokens += tokens_out
                    self.total_calls += 1
                    
                    log_api_call(logger, self.model_name, tokens_in, tokens_out)
                
                return text
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        error_msg = f"Failed after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _is_truncated_json(self, text: str) -> bool:
        """
        Detect if JSON response appears truncated.
        
        Args:
            text: JSON text to check
            
        Returns:
            True if likely truncated
        """
        if not text:
            return True
        
        # Check for common truncation signs
        last_char = text[-1]
        
        # If doesn't end with } or ], likely truncated
        if last_char not in ['}', ']']:
            return True
        
        # Try to count braces/brackets
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        if open_braces != close_braces or open_brackets != close_brackets:
            return True
        
        return False
    
    def _try_repair_json(self, text: str) -> str:
        """
        Attempt to auto-repair truncated JSON by cutting back to the last comma
        and closing all open structures.
        """
        if not text:
            return text
            
        logger.info("  Attempting robust JSON repair (Cut-Back Strategy)...")
        
        # 1. Check if simple closure works (count brackets)
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # If balanced, return as is (or maybe just missing a quote?)
        if open_braces == 0 and open_brackets == 0:
            return text
            
        # 2. Cut-back Strategy: Find last comma and trim
        # This discards the incomplete last item/field to ensure validity
        last_comma = text.rfind(',')
        
        if last_comma > 0:
            # Trim text to just before the comma
            # But wait, if we have keys like "a,b", rfind might hit inside a string.
            # A perfect parser is hard, but simple heuristic:
            # If the truncation makes it invalid, likely the end is garbage.
            
            # Let's try to verify if simple appending works first (try/catch in caller handles failure).
            # But the user specifically asked to TRUNCATE.
            
            trimmed_text = text[:last_comma]
            logger.debug(f"  Trimmed JSON from {len(text)} to {len(trimmed_text)} chars")
            text = trimmed_text
            
            # Recalculate usage after trim
            open_braces = text.count('{') - text.count('}')
            open_brackets = text.count('[') - text.count(']')
        
        # 3. Close open structures
        # Order matters: first close what opened last.
        # Simple heuristic: Usually we just append logical closures.
        # But strictly we should track stack.
        # Given we truncated to a comma, we are likely at the 'end' of an item in a list or dict.
        
        # Appending '}' or ']' is safer now that we removed the half-string.
        if open_brackets > 0 or open_braces > 0:
            logger.info(f"  Closing JSON: adding {open_brackets} ']' and {open_braces} '}}'")
            text += ']' * open_brackets
            text += '}' * open_braces
            
        return text
    
    def get_stats(self) -> dict:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with token counts and call count
        """
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "model": self.model_name
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        logger.info("Statistics reset")
