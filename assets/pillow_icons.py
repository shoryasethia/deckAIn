"""
deckAIn - Pillow-based Icon Generator
Creates clean PNG icons using Pillow drawing - no cairosvg/Cairo dependency.
Also generates certification badge images.
"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import math

from utils.logger import setup_logger

logger = setup_logger(__name__)

ICONS_DIR = Path(__file__).parent / "icons"
PNG_CACHE_DIR = ICONS_DIR / "pillow_cache"
CERT_CACHE_DIR = ICONS_DIR / "cert_cache"

# Ensure cache dirs exist
PNG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CERT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back gracefully."""
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
        "segoeui.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_shape_icon(draw: ImageDraw.Draw, shape: str, bbox: Tuple, color: str):
    """Draw a simple shape-based icon inside the given bounding box."""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    w = x2 - x1
    h = y2 - y1
    pad = w * 0.15

    if shape == "trophy":
        # Cup shape
        cup_top = y1 + pad
        cup_bot = y1 + h * 0.65
        draw.rectangle([x1 + pad * 2, cup_top, x2 - pad * 2, cup_bot], fill=color)
        # Handles
        draw.arc([x1 + pad * 0.5, cup_top, x1 + pad * 3, cup_bot - pad], 180, 360, fill=color, width=2)
        draw.arc([x2 - pad * 3, cup_top, x2 - pad * 0.5, cup_bot - pad], 0, 180, fill=color, width=2)
        # Base
        draw.rectangle([cx - w * 0.12, cup_bot, cx + w * 0.12, y2 - pad * 1.5], fill=color)
        draw.rectangle([cx - w * 0.25, y2 - pad * 1.8, cx + w * 0.25, y2 - pad], fill=color)

    elif shape == "globe":
        r = min(w, h) * 0.35
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        draw.ellipse([cx - r * 0.5, cy - r, cx + r * 0.5, cy + r], outline=color, width=2)
        draw.line([cx - r, cy, cx + r, cy], fill=color, width=2)
        draw.line([cx, cy - r, cx, cy + r], fill=color, width=2)

    elif shape == "chart_up" or shape == "graph":
        # Bar chart with upward trend
        bar_w = w * 0.12
        bars = [0.3, 0.5, 0.4, 0.7, 0.9]
        for i, h_pct in enumerate(bars):
            bx = x1 + pad + i * (w - 2 * pad) / len(bars)
            bar_h = (h - 2 * pad) * h_pct
            by = y2 - pad - bar_h
            draw.rectangle([bx, by, bx + bar_w, y2 - pad], fill=color)

    elif shape == "shield":
        # Shield shape using polygon
        pts = [
            (cx, y1 + pad * 0.5),
            (x2 - pad, y1 + pad * 1.5),
            (x2 - pad, cy + pad * 0.5),
            (cx, y2 - pad * 0.5),
            (x1 + pad, cy + pad * 0.5),
            (x1 + pad, y1 + pad * 1.5),
        ]
        draw.polygon(pts, outline=color, width=2)
        # Checkmark inside
        draw.line([(cx - w * 0.1, cy), (cx - w * 0.02, cy + h * 0.1), (cx + w * 0.15, cy - h * 0.1)], fill=color, width=2)

    elif shape == "rocket":
        # Simple rocket
        draw.polygon([(cx, y1 + pad), (cx + w * 0.15, cy), (cx - w * 0.15, cy)], fill=color)
        draw.rectangle([cx - w * 0.12, cy, cx + w * 0.12, y2 - pad * 2], fill=color)
        # Fins
        draw.polygon([(cx - w * 0.12, y2 - pad * 3), (cx - w * 0.25, y2 - pad * 1.5), (cx - w * 0.12, y2 - pad * 2)], fill=color)
        draw.polygon([(cx + w * 0.12, y2 - pad * 3), (cx + w * 0.25, y2 - pad * 1.5), (cx + w * 0.12, y2 - pad * 2)], fill=color)
        # Flame
        draw.polygon([(cx - w * 0.06, y2 - pad * 2), (cx, y2 - pad * 0.5), (cx + w * 0.06, y2 - pad * 2)], fill="#FF6B35")

    elif shape == "handshake":
        # Two hands meeting
        draw.arc([x1 + pad, cy - h * 0.2, cx, cy + h * 0.2], 0, 180, fill=color, width=3)
        draw.arc([cx, cy - h * 0.2, x2 - pad, cy + h * 0.2], 0, 180, fill=color, width=3)
        draw.line([x1 + pad * 1.5, cy, cx, cy], fill=color, width=3)
        draw.line([cx, cy, x2 - pad * 1.5, cy], fill=color, width=3)

    elif shape == "lightbulb":
        r = min(w, h) * 0.25
        draw.ellipse([cx - r, y1 + pad, cx + r, y1 + pad + 2 * r], outline=color, width=2)
        # Filament lines
        draw.line([cx - r * 0.3, y1 + pad + 2 * r, cx - r * 0.3, y1 + pad + 2 * r + h * 0.12], fill=color, width=2)
        draw.line([cx + r * 0.3, y1 + pad + 2 * r, cx + r * 0.3, y1 + pad + 2 * r + h * 0.12], fill=color, width=2)
        draw.rectangle([cx - r * 0.4, y1 + pad + 2 * r + h * 0.08, cx + r * 0.4, y2 - pad], outline=color, width=2)

    elif shape == "star":
        r_out = min(w, h) * 0.35
        r_in = r_out * 0.4
        pts = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
        draw.polygon(pts, fill=color)

    elif shape == "diamond":
        draw.polygon([(cx, y1 + pad), (x2 - pad, cy), (cx, y2 - pad), (x1 + pad, cy)], outline=color, width=2)
        draw.line([(x1 + pad, cy), (x2 - pad, cy)], fill=color, width=1)

    elif shape == "gear":
        r = min(w, h) * 0.28
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        draw.ellipse([cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4], fill=color)
        for i in range(6):
            angle = i * math.pi / 3
            tx = cx + r * 1.15 * math.cos(angle)
            ty = cy + r * 1.15 * math.sin(angle)
            tooth_r = r * 0.2
            draw.ellipse([tx - tooth_r, ty - tooth_r, tx + tooth_r, ty + tooth_r], fill=color)

    elif shape == "target":
        for i in range(3, 0, -1):
            r = min(w, h) * 0.12 * i
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color)

    elif shape == "users" or shape == "people":
        # Two person silhouettes
        r = min(w, h) * 0.12
        # Person 1 (left)
        p1x = cx - w * 0.15
        draw.ellipse([p1x - r, y1 + pad, p1x + r, y1 + pad + 2 * r], fill=color)
        draw.arc([p1x - r * 1.5, y1 + pad + 2 * r, p1x + r * 1.5, y1 + pad + 2 * r + h * 0.3], 0, 180, fill=color, width=int(r * 1.2))
        # Person 2 (right)
        p2x = cx + w * 0.15
        draw.ellipse([p2x - r, y1 + pad, p2x + r, y1 + pad + 2 * r], fill=color)
        draw.arc([p2x - r * 1.5, y1 + pad + 2 * r, p2x + r * 1.5, y1 + pad + 2 * r + h * 0.3], 0, 180, fill=color, width=int(r * 1.2))

    elif shape == "factory" or shape == "building":
        # Building with chimney
        draw.rectangle([x1 + pad * 1.5, cy - h * 0.1, x2 - pad * 1.5, y2 - pad], outline=color, width=2)
        draw.rectangle([x1 + pad * 2, y1 + pad, x1 + pad * 3, cy - h * 0.1], fill=color)
        # Windows
        ww = w * 0.1
        for wy in [cy + h * 0.05, cy + h * 0.2]:
            for wx in [cx - w * 0.15, cx + w * 0.08]:
                draw.rectangle([wx, wy, wx + ww, wy + ww], fill=color)

    elif shape == "briefcase":
        draw.rectangle([x1 + pad, cy - h * 0.1, x2 - pad, y2 - pad * 1.5], outline=color, width=2)
        draw.rectangle([cx - w * 0.15, y1 + pad * 1.5, cx + w * 0.15, cy - h * 0.1], outline=color, width=2)
        draw.line([x1 + pad, cy + h * 0.08, x2 - pad, cy + h * 0.08], fill=color, width=2)

    elif shape == "award":
        # Medal
        r = min(w, h) * 0.22
        draw.ellipse([cx - r, cy - r * 0.5, cx + r, cy + r * 1.5], outline=color, width=2)
        # Ribbon
        draw.polygon([(cx - r, cy - r * 0.3), (cx - w * 0.05, y1 + pad), (cx + w * 0.05, y1 + pad), (cx + r, cy - r * 0.3)], fill=color)
        # Star inside
        sr = r * 0.4
        pts = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            rr = sr if i % 2 == 0 else sr * 0.4
            pts.append((cx + rr * math.cos(angle), cy + r * 0.5 - rr * math.sin(angle)))
        draw.polygon(pts, fill=color)

    else:
        # Default: checkmark in circle
        r = min(w, h) * 0.3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        draw.line([(cx - r * 0.4, cy), (cx - r * 0.1, cy + r * 0.3), (cx + r * 0.4, cy - r * 0.3)], fill=color, width=3)


# Map highlight keywords to icon shapes
HIGHLIGHT_ICON_MAP = {
    # Growth/Market
    "market": "globe",
    "global": "globe",
    "international": "globe",
    "export": "globe",
    "footprint": "globe",
    "regional": "globe",
    "expansion": "rocket",
    "growth": "chart_up",
    "scaling": "chart_up",
    "capitaliz": "chart_up",
    "super-cycle": "chart_up",
    
    # Competition/Quality
    "moat": "shield",
    "compliance": "shield",
    "barrier": "shield",
    "resilience": "shield",
    "certification": "shield",
    "technical": "shield",
    
    # Innovation
    "innovation": "lightbulb",
    "technology": "lightbulb",
    "smart": "lightbulb",
    "r&d": "lightbulb",
    "digital": "lightbulb",
    "edge": "lightbulb",
    
    # People/Customers
    "customer": "handshake",
    "oem": "handshake",
    "stickiness": "handshake",
    "partner": "handshake",
    "relationship": "handshake",
    "integration": "handshake",
    "blue-chip": "handshake",
    
    # Strategy
    "strategic": "star",
    "value": "star",
    "synergy": "star",
    "diversif": "star",
    "multi-sector": "star",
    
    # Performance
    "financial": "chart_up",
    "revenue": "chart_up",
    "profit": "chart_up",
    "margin": "chart_up",
    
    # Operations
    "operational": "gear",
    "efficiency": "gear",
    "asset": "gear",
    "optimiz": "gear",
    "capacity": "factory",
    "manufactur": "factory",
    "facility": "factory",
    
    # Awards
    "award": "award",
    "recognized": "award",
    "leader": "trophy",
    "leading": "trophy",
    "dominant": "trophy",
}

# Icon colors (vibrant, professional palette)
ICON_COLORS = [
    "#D11563",  # Magenta/Pink
    "#303F9F",  # Indigo
    "#00B8D9",  # Cyan
    "#8B5CF6",  # Purple
    "#10B981",  # Green
    "#F59E0B",  # Gold
]


def generate_icon_png(keyword: str, size: int = 64, icon_index: int = 0) -> Optional[Path]:
    """
    Generate a PNG icon based on keyword matching.
    
    Args:
        keyword: Text to match against icon mapping
        size: Output size in pixels
        icon_index: Index for color selection
        
    Returns:
        Path to generated PNG, or None
    """
    keyword_lower = keyword.lower()
    
    # Find matching shape
    shape = "check"  # default
    for key, icon_shape in HIGHLIGHT_ICON_MAP.items():
        if key in keyword_lower:
            shape = icon_shape
            break
    
    cache_key = f"{shape}_{size}_{icon_index % len(ICON_COLORS)}"
    cache_path = PNG_CACHE_DIR / f"{cache_key}.png"
    
    if cache_path.exists():
        return cache_path
    
    try:
        color = ICON_COLORS[icon_index % len(ICON_COLORS)]
        
        # Create image with transparency
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        _draw_shape_icon(draw, shape, (0, 0, size, size), color)
        
        img.save(str(cache_path), "PNG")
        logger.debug(f"Generated icon: {shape} -> {cache_path.name}")
        return cache_path
    except Exception as e:
        logger.debug(f"Icon generation failed: {e}")
        return None


# ============================================================================
# CERTIFICATION BADGE GENERATOR
# ============================================================================

# Known certification logos - we'll draw stylized badges for these
CERT_STYLES = {
    "iso": {"bg": "#1A5276", "fg": "#FFFFFF", "text": "ISO", "subtitle": "Certified"},
    "iso 9001": {"bg": "#1A5276", "fg": "#FFFFFF", "text": "ISO\n9001", "subtitle": ""},
    "iso 14001": {"bg": "#1E8449", "fg": "#FFFFFF", "text": "ISO\n14001", "subtitle": ""},
    "iso 27001": {"bg": "#7D3C98", "fg": "#FFFFFF", "text": "ISO\n27001", "subtitle": ""},
    "iatf 16949": {"bg": "#B71C1C", "fg": "#FFFFFF", "text": "IATF\n16949", "subtitle": ""},
    "iatf": {"bg": "#B71C1C", "fg": "#FFFFFF", "text": "IATF", "subtitle": "16949"},
    "cmmi": {"bg": "#0D47A1", "fg": "#FFFFFF", "text": "CMMI", "subtitle": "Level 5"},
    "gmp": {"bg": "#2E7D32", "fg": "#FFFFFF", "text": "GMP", "subtitle": "Certified"},
    "who-gmp": {"bg": "#2E7D32", "fg": "#FFFFFF", "text": "WHO\nGMP", "subtitle": ""},
    "ce": {"bg": "#1565C0", "fg": "#FFFFFF", "text": "CE", "subtitle": "Mark"},
    "fda": {"bg": "#1B5E20", "fg": "#FFFFFF", "text": "FDA", "subtitle": "Approved"},
    "ts 16949": {"bg": "#B71C1C", "fg": "#FFFFFF", "text": "TS\n16949", "subtitle": ""},
    "ohsas": {"bg": "#E65100", "fg": "#FFFFFF", "text": "OHSAS", "subtitle": "18001"},
    "haccp": {"bg": "#00695C", "fg": "#FFFFFF", "text": "HACCP", "subtitle": ""},
    "bis": {"bg": "#283593", "fg": "#FFFFFF", "text": "BIS", "subtitle": "India"},
    "nabl": {"bg": "#4527A0", "fg": "#FFFFFF", "text": "NABL", "subtitle": ""},
    "fssai": {"bg": "#2E7D32", "fg": "#FFFFFF", "text": "FSSAI", "subtitle": ""},
    "crisil": {"bg": "#1565C0", "fg": "#FFFFFF", "text": "CRISIL", "subtitle": "Rated"},
    "sa 8000": {"bg": "#6A1B9A", "fg": "#FFFFFF", "text": "SA\n8000", "subtitle": ""},
}


def generate_cert_badge(cert_name: str, width: int = 120, height: int = 80) -> Optional[Path]:
    """
    Generate a professional certification badge PNG.
    
    Args:
        cert_name: Certification name (e.g., "ISO 9001", "IATF 16949")
        width: Badge width in pixels
        height: Badge height in pixels
        
    Returns:
        Path to badge PNG, or None
    """
    cert_key = cert_name.strip().lower()
    cache_path = CERT_CACHE_DIR / f"cert_{cert_key.replace(' ', '_')}_{width}x{height}.png"
    
    if cache_path.exists():
        return cache_path
    
    # Find matching style
    style = None
    for key, s in CERT_STYLES.items():
        if key in cert_key or cert_key in key:
            style = s
            break
    
    if not style:
        # Generic badge
        style = {"bg": "#37474F", "fg": "#FFFFFF", "text": cert_name[:6].upper(), "subtitle": ""}
    
    try:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Parse colors
        bg = style["bg"]
        fg = style["fg"]
        
        # Draw rounded rectangle background
        radius = min(width, height) // 6
        draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=bg, outline=bg)
        
        # Draw inner border (subtle)
        draw.rounded_rectangle(
            [2, 2, width - 3, height - 3], 
            radius=radius - 1, 
            outline="#FFFFFF40",
            width=1
        )
        
        # Main text
        main_text = style["text"]
        lines = main_text.split("\n")
        
        if len(lines) == 1:
            font_size = min(width // max(len(main_text), 1), height // 2)
            font_size = max(font_size, 10)
            font = _get_font(font_size, bold=True)
            bbox = draw.textbbox((0, 0), main_text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            
            text_y = (height - th) // 2
            if style["subtitle"]:
                text_y = height // 4
            
            draw.text(((width - tw) // 2, text_y), main_text, fill=fg, font=font)
            
            # Subtitle
            if style["subtitle"]:
                sub_font = _get_font(max(font_size // 2, 8), bold=False)
                bbox2 = draw.textbbox((0, 0), style["subtitle"], font=sub_font)
                sw = bbox2[2] - bbox2[0]
                draw.text(((width - sw) // 2, height * 3 // 5), style["subtitle"], fill="#FFFFFFCC", font=sub_font)
        else:
            # Multi-line (e.g., "ISO\n9001")
            total_h = 0
            line_data = []
            for i, line in enumerate(lines):
                fs = min(width // max(len(line), 1), height // (len(lines) + 1))
                fs = max(fs, 10)
                f = _get_font(fs, bold=(i == 0))
                bbox = draw.textbbox((0, 0), line, font=f)
                lw = bbox[2] - bbox[0]
                lh = bbox[3] - bbox[1]
                line_data.append((line, f, lw, lh))
                total_h += lh + 2
            
            cur_y = (height - total_h) // 2
            for line, f, lw, lh in line_data:
                draw.text(((width - lw) // 2, cur_y), line, fill=fg, font=f)
                cur_y += lh + 2
        
        img.save(str(cache_path), "PNG")
        logger.debug(f"Generated cert badge: {cert_name} -> {cache_path.name}")
        return cache_path
    except Exception as e:
        logger.debug(f"Cert badge generation failed for '{cert_name}': {e}")
        return None
