"""
deckAIn - Generative Layout Engine
Uses LLM to write python-pptx code at runtime for dynamic slide layouts.
"""

import re
import traceback
from typing import Dict, Any, Callable
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT as PP_ALIGN
from utils.logger import setup_logger, log_stage
from utils.llm_client import GeminiClient
from config.prompts import LAYOUT_GENERATION_PROMPT
from config.settings import KELP_COLORS, KELP_FONT_HEAD, KELP_FONT_BODY

logger = setup_logger(__name__)

class LayoutEngine:
    """
    Generates and executes Python code for slide layouts.
    """
    
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client
        logger.info("LayoutEngine initialized")
        
    def generate_and_execute(self, slide: Any, content: Dict, context_globals: Dict, prompt_template: str = LAYOUT_GENERATION_PROMPT) -> bool:
        """
        Generate rendering code for content and execute it on the slide.
        
        Args:
            slide: The slide object to render onto.
            content: The JSON content block to render.
            context_globals: Dictionary of globals (Inches, Pt, RGBColor)
            prompt_template: specific prompt to use (default: standard layout)
            
        Returns:
            True if successful, False if failed.
        """
        log_stage(logger, 4, "Generative Layout", "START")
        
        try:
            # 1. Generate Code
            prompt = prompt_template.format(content_json=content)
            
            logger.info("Requesting layout code from LLM...")
            # We use generate_text as we want text (code), not JSON
            response_text = self.llm.generate_text(prompt)
            
            # 2. Extract Code Block
            code_block = self._extract_code(response_text)
            if not code_block:
                # Sanitize response for logging to avoid UnicodeEncodeError on Windows consoles
                try:
                    safe_response = response_text.encode('ascii', 'replace').decode('ascii')
                except:
                    safe_response = "Unprintable response"
                logger.error(f"No code block found in LLM response. Raw response:\n{safe_response}")
                return False
            
            # 2.5. Validate Code for Common Errors
            validation_issues = self._validate_generated_code(code_block)
            if validation_issues:
                logger.warning(f"Code validation found {len(validation_issues)} potential issues:")
                for issue in validation_issues:
                    logger.warning(f"  - {issue}")
                # Continue anyway, but log warnings
                
            logger.debug(f"Generated Code ({len(code_block)} chars)")
            
            # 3. Prepare Execution Context
            # We need to inject standard variables + colors
            
            # --- Smart Wrapper for Charts (Fixes KeyError: 0) ---
            class SmartDict(dict):
                def __getitem__(self, key):
                    # If integer index, return values list item
                    if isinstance(key, int):
                        return list(self.values())[key]
                    return super().__getitem__(key)
            
            # Wrap chart_specs if present in content
            if "chart_specs" in content:
                # Convert regular dict to SmartDict
                sd = SmartDict()
                sd.update(content["chart_specs"])
                content["chart_specs"] = sd
            
            # CRITICAL FIX: Also wrap in context_globals for execution
            if "chart_specs" in context_globals:
                 sd_exec = SmartDict()
                 sd_exec.update(context_globals["chart_specs"])
                 context_globals["chart_specs"] = sd_exec
                
            # --- Smart Color Wrapper (Fixes KeyError: 'accent') ---
            class SafeColorDict(dict):
                def __getitem__(self, key):
                    if key not in self:
                        logger.warning(f"AI requested non-existent color '{key}'. Defaulting to primary_indigo.")
                        return self.get("primary_indigo", "#303F9F")
                    return super().__getitem__(key)

            local_scope = {}
            exec_globals = context_globals.copy()
            
            # Wrap KELP_COLORS
            safe_colors = SafeColorDict()
            safe_colors.update(KELP_COLORS)
            
            # --- Safe Slide Proxy (Blocks direct add_shape/box calls) ---
            class SafeSlideProxy:
                def __init__(self, real_slide):
                    self._real_slide = real_slide
                def __getattr__(self, name):
                    # Block brittle methods to force usage of robust primitives
                    if name in ["add_shape", "add_textbox", "add_picture", "add_connector", "add_chart"]:
                        logger.warning(f"AI attempted bypass calling 'slide.{name}'. BLOCKING.")
                        raise AttributeError(f"Direct '{name}' is DISABLED. Use 'draw_rect', 'draw_text_box', 'draw_image_box', 'draw_line' or 'charts_creator' instead.")
                    return getattr(self._real_slide, name)
                @property
                def shapes(self):
                    return self._real_slide.shapes

            exec_globals.update({
                "KELP_COLORS": safe_colors,
                "KELP_FONT_HEAD": KELP_FONT_HEAD,
                "KELP_FONT_BODY": KELP_FONT_BODY,
                "MSO_CONNECTOR": MSO_CONNECTOR, # Fix for LINE error
                "MSO_SHAPE": MSO_SHAPE,
                "PP_ALIGN": PP_ALIGN  # Make alignment enum available
            })
            if "slide" in exec_globals:
                exec_globals["slide"] = SafeSlideProxy(exec_globals["slide"])
            
            # 4. Execute Definition
            # This runs the 'def render(slide):' block
            exec(code_block, exec_globals, local_scope)
            
            if "render" not in local_scope:
                logger.error("Generated code did not define 'render(slide)' function")
                return False
                
            render_func = local_scope["render"]
            
            # 5. Run Render
            logger.info("Executing generated render() function...")
            render_func(slide)
            
            log_stage(logger, 4, "Generative Layout", "DONE")
            return True
            
        except Exception as e:
            logger.error(f"Layout Generation Failed: {e}")
            try:
                # Debug info: what was actually in the scope?
                logger.debug(f"Execution Globals Keys: {list(exec_globals.keys())}")
                if "chart_specs" in exec_globals:
                    logger.debug(f"Chart Specs Type: {type(exec_globals['chart_specs'])}")
            except:
                pass
            logger.error(traceback.format_exc())
            return False
    
    def _validate_generated_code(self, code: str) -> list:
        """
        Validate generated code for common LLM mistakes.
        Returns list of issues found.
        """
        issues = []
        
        # Check for common errors
        if 'line.fore_color' in code or 'line.fill.fore_color' in code:
            issues.append("Code uses 'line.fore_color' which doesn't exist. Should use 'line.color.rgb' instead.")
        
        # Check for raw integer alignment values
        if re.search(r'\.alignment\s*=\s*\d+', code):
            issues.append("Code uses raw integer for alignment (e.g., alignment = 0). Should use PP_ALIGN constants.")
        
        # Check for foreground_color typo
        if 'foreground_color' in code:
            issues.append("Code uses 'foreground_color'. Should be 'fore_color'.")
        
        # Check if code uses blocked methods
        if 'slide.add_shape' in code or 'slide.add_textbox' in code:
            issues.append("Code attempts to use 'slide.add_shape/add_textbox' directly. Should use helper functions.")
        
        return issues
            
    def _extract_code(self, text: str) -> str:
        """Extract code from ```python ... ``` block."""
        match = re.search(r"```python(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: look for generic code block
        match = re.search(r"```(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        return None
