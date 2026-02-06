"""
deckAIn - PowerPoint Renderer
Uses win32com to export slides as images for visual review.
Requires Microsoft PowerPoint installed on Windows.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PPTRenderer:
    """
    Render PPTX slides to images using COM automation.
    Allows Groq to 'see' the slides.
    """
    
    def __init__(self):
        """Initialize renderer."""
        self.available = False
        if sys.platform == 'win32':
            try:
                import win32com.client
                self.available = True
            except ImportError:
                logger.warning("pywin32 not installed. Cannot render slides.")
        else:
            logger.warning("Not on Windows. Cannot render slides.")
            
    def export_slide_as_image(self, pptx_path: str, slide_index: int, output_path: str) -> Optional[str]:
        """
        Export a specific slide as an image (JPG).
        Includes retry logic for file locks.
        """
        if not self.available:
            return None
            
        import win32com.client
        from pywintypes import com_error
        
        pptx_path = os.path.abspath(pptx_path)
        output_path = os.path.abspath(output_path)
        
        # Check if file exists
        if not os.path.exists(pptx_path):
            logger.error(f"PPTX file not found: {pptx_path}")
            return None
        
        ppt_app = None
        presentation = None
        
        max_retries = 3  # Reduced from 5 for faster feedback
        retry_delay = 2.0  # Increased delay
        
        for attempt in range(max_retries):
            try:
                # Close any existing PowerPoint instances first (aggressive cleanup)
                if attempt > 0:
                    try:
                        import win32process
                        import win32api
                        # Give PowerPoint time to release the file
                        time.sleep(retry_delay)
                    except:
                        pass
                
                # Connect to PowerPoint (create new instance)
                ppt_app = win32com.client.DispatchEx("PowerPoint.Application")  # DispatchEx creates new instance
                
                # CRITICAL FIX: Don't hide the window - PowerPoint 2016+ doesn't allow it in some scenarios
                # Setting Visible = 1 prevents the "Invalid request. Hiding the application window is not allowed" error
                ppt_app.Visible = 1  # Keep visible to avoid COM errors
                
                # Wait a moment before opening
                time.sleep(0.5)
                
                # Open presentation (Read-only = 1, Untitled = 0, WithWindow = 1 for compatibility)
                # Using WithWindow=1 to ensure proper rendering
                presentation = ppt_app.Presentations.Open(
                    pptx_path, 
                    ReadOnly=1,      # Read-only
                    Untitled=0,      # Not untitled
                    WithWindow=1     # Show window (required for export in some PowerPoint versions)
                )
                
                # PowerPoint uses 1-based indexing
                if slide_index + 1 > presentation.Slides.Count:
                    logger.error(f"Slide index {slide_index + 1} out of range (total: {presentation.Slides.Count})")
                    return None
                    
                slide = presentation.Slides(slide_index + 1)
                
                # Export (Width/Height in pixels)
                slide.Export(output_path, "JPG", 2048, 1536)
                
                logger.debug(f"Exported slide {slide_index + 1} to {output_path}")
                return output_path
                
            except com_error as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    logger.debug(f"Export attempt {attempt+1}/{max_retries} failed: {error_msg}")
                    logger.debug(f"Retrying in {retry_delay}s...")
                else:
                    logger.warning(f"Failed to export slide as image (PowerPoint might be busy/file open): {e}")
            except Exception as e:
                logger.warning(f"Unexpected error during slide export: {e}")
                break
            finally:
                # Always cleanup
                if presentation:
                    try:
                        presentation.Close()
                        presentation = None
                    except:
                        pass
                if ppt_app:
                    try:
                        ppt_app.Quit()
                        ppt_app = None
                    except:
                        pass
                # Force garbage collection
                import gc
                gc.collect()
                
        return None
