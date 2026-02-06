"""
deckAIn - Icon Helper
Provides icons for PPTX slides. Uses pre-downloaded Bootstrap Icons.
Converts SVG to PNG for python-pptx compatibility.
"""

from pathlib import Path
from typing import Optional
import io
import tempfile

from utils.logger import setup_logger

logger = setup_logger(__name__)

ICONS_DIR = Path(__file__).parent / "icons"
PNG_CACHE_DIR = ICONS_DIR / "png_cache"

# Map keywords to icon files
ICON_MAPPING = {
    # Business/Company
    "business": "building",
    "company": "building",
    "headquarters": "building",
    "facility": "building",
    "infrastructure": "building",
    
    # Financial
    "revenue": "bar-chart",
    "financial": "bar-chart",
    "growth": "graph-up",
    "profit": "cash-coin",
    "margin": "bar-chart",
    "ebitda": "bar-chart",
    
    # Team/People
    "team": "people",
    "employee": "people",
    "workforce": "people",
    "customer": "people",
    
    # Global/Market
    "global": "globe",
    "international": "globe",
    "market": "globe",
    "export": "globe",
    
    # Operations
    "operations": "gear",
    "manufacturing": "gear",
    "production": "gear",
    "technology": "gear",
    "capacity": "gear",
    
    # Quality/Awards
    "certification": "shield-check",
    "quality": "shield-check",
    "compliance": "shield-check",
    "iso": "shield-check",
    "award": "trophy",
    "achievement": "trophy",
    "success": "check-circle",
    
    # Default
    "default": "check-circle",
}


class IconHelper:
    """
    Provide icons for PPTX slides.
    Converts SVG to PNG for python-pptx compatibility.
    """
    
    def __init__(self):
        """Initialize icon helper."""
        self.icons_available = ICONS_DIR.exists() and any(ICONS_DIR.glob("*.svg"))
        self.cairosvg_available = False
        
        # Try to import cairosvg for SVG to PNG conversion
        # Note: cairosvg requires Cairo C library which may not be installed
        try:
            import cairosvg
            self.cairosvg_available = True
            PNG_CACHE_DIR.mkdir(exist_ok=True)
            logger.info("cairosvg available - PNG icons enabled")
        except (ImportError, OSError) as e:
            # OSError occurs when Cairo C library is missing
            logger.info(f"cairosvg not available - using fallback icons ({type(e).__name__})")
        
        if self.icons_available:
            logger.info(f"IconHelper: {len(list(ICONS_DIR.glob('*.svg')))} SVG icons available")
        else:
            logger.warning("IconHelper: No icons found")
    
    def get_icon_png_path(self, keyword: str, size: int = 48) -> Optional[Path]:
        """
        Get PNG icon path based on keyword.
        Converts SVG to PNG if needed.
        
        Args:
            keyword: Keyword to match icon
            size: Icon size in pixels
            
        Returns:
            Path to PNG icon or None
        """
        if not self.cairosvg_available:
            return None
        
        keyword_lower = keyword.lower()
        
        # Find matching icon
        icon_name = None
        for key, icon in ICON_MAPPING.items():
            if key in keyword_lower:
                icon_name = icon
                break
        
        if not icon_name:
            icon_name = ICON_MAPPING["default"]
        
        svg_path = ICONS_DIR / f"{icon_name}.svg"
        png_path = PNG_CACHE_DIR / f"{icon_name}_{size}.png"
        
        if not svg_path.exists():
            return None
        
        # Convert if PNG doesn't exist
        if not png_path.exists():
            try:
                import cairosvg
                cairosvg.svg2png(
                    url=str(svg_path),
                    write_to=str(png_path),
                    output_width=size,
                    output_height=size
                )
                logger.debug(f"Converted {icon_name}.svg to PNG")
            except Exception as e:
                logger.debug(f"SVG to PNG conversion failed: {e}")
                return None
        
        return png_path if png_path.exists() else None
    
    def get_icon_for_highlight(self, highlight_text: str, size: int = 48) -> Optional[Path]:
        """
        Get appropriate PNG icon for an investment highlight.
        
        Args:
            highlight_text: Full text of the highlight
            size: Icon size in pixels
            
        Returns:
            Path to PNG icon
        """
        return self.get_icon_png_path(highlight_text, size)
