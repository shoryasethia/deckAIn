"""
deckAIn - PowerPoint Template with Kelp Branding
Fully branded PPTX template following Kelp branding guidelines
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT, MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement

from config.settings import KELP_COLORS, KELP_FOOTER_TEXT, KELP_FONT_HEAD, KELP_FONT_BODY
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PPTTemplate:
    """
    Create and configure Kelp-branded PowerPoint template.
    Follows branding guidelines with proper colors, typography, and layouts.
    """
    
    def __init__(self):
        """Initialize template."""
        self.prs = Presentation()
        self.prs.slide_width = Inches(10)
        self.prs.slide_height = Inches(5.625) # 16:9 Aspect Ratio (Widescreen)
        logger.info("PPTTemplate initialized")
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _add_kelp_logo(self, slide):
        """
        Add Kelp logo placeholder to top of slide.
        
        Args:
            slide: Slide object
        """
        logo_box = slide.shapes.add_textbox(
            Inches(0.4), Inches(0.2), Inches(1.5), Inches(0.4)
        )
        text_frame = logo_box.text_frame
        text_frame.text = "KELP"
        
        p = text_frame.paragraphs[0]
        p.font.name = KELP_FONT_HEAD
        p.font.size = Pt(18)
        p.font.bold = True
        
        # Pink-orange gradient effect (using orange for simplicity)
        rgb = self._hex_to_rgb(KELP_COLORS["gradient_orange"])
        p.font.color.rgb = RGBColor(*rgb)
    
    def _add_footer(self, slide, text: str = None, y_pos: float = 7.0):
        """
        Add footer to slide per branding spec.
        
        Args:
            slide: Slide object
            text: Footer text (defaults to Kelp standard)
            y_pos: Y-position in inches (default 7.0)
        """
        if text is None:
            text = KELP_FOOTER_TEXT
        
        footer_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(y_pos), Inches(9), Inches(0.35)
        )
        footer_frame = footer_box.text_frame
        footer_frame.text = text
        
        footer_para = footer_frame.paragraphs[0]
        footer_para.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
        footer_para.font.size = Pt(9)  # Exactly 9pt per spec
        footer_para.font.name = KELP_FONT_BODY
        rgb = self._hex_to_rgb(KELP_COLORS["text_body"])
        footer_para.font.color.rgb = RGBColor(*rgb)
    
    def create_title_slide(self, company_codename: str) -> object:
        """
        Create title slide with modern gradient effect and premium styling.
        
        Args:
            company_codename: Anonymized project name
        
        Returns:
            Slide object
        """
        slide_layout = self.prs.slide_layouts[6]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Fill background with dark indigo/violet
        background = slide.background
        fill = background.fill
        fill.solid()
        rgb = self._hex_to_rgb(KELP_COLORS["primary_dark"])
        fill.fore_color.rgb = RGBColor(*rgb)
        
        # --- Modern Design: Gradient overlay shapes ---
        # Top-right decorative gradient shape
        gradient_shape = slide.shapes.add_shape(
            1,  # Rectangle
            Inches(6), Inches(0), Inches(4), Inches(3)
        )
        gradient_shape.fill.solid()
        rgb = self._hex_to_rgb(KELP_COLORS["gradient_pink"])
        gradient_shape.fill.fore_color.rgb = RGBColor(*rgb)
        gradient_shape.fill.fore_color.brightness = 0.3
        gradient_shape.line.fill.background()
        
        # Bottom-left decorative shape
        accent_shape = slide.shapes.add_shape(
            1,
            Inches(0), Inches(5), Inches(3), Inches(2.5)
        )
        accent_shape.fill.solid()
        rgb = self._hex_to_rgb(KELP_COLORS["gradient_orange"])
        accent_shape.fill.fore_color.rgb = RGBColor(*rgb)
        accent_shape.fill.fore_color.brightness = 0.2
        accent_shape.line.fill.background()
        
        # --- Kelp logo (larger, more prominent) ---
        logo_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.3), Inches(2), Inches(0.6)
        )
        text_frame = logo_box.text_frame
        text_frame.text = "KELP"
        
        p = text_frame.paragraphs[0]
        p.font.name = KELP_FONT_HEAD
        p.font.size = Pt(24)
        p.font.bold = True
        rgb = self._hex_to_rgb(KELP_COLORS["gradient_orange"])
        p.font.color.rgb = RGBColor(*rgb)
        
        # --- Main title (larger, bolder, centered) ---
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(2.5), Inches(9), Inches(2)
        )
        title_frame = title_box.text_frame
        title_frame.word_wrap = True
        title_frame.text = company_codename
        
        title_para = title_frame.paragraphs[0]
        title_para.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
        title_para.font.name = KELP_FONT_HEAD
        title_para.font.size = Pt(48)  # Larger for impact
        title_para.font.bold = True
        rgb = self._hex_to_rgb(KELP_COLORS["text_light"])
        title_para.font.color.rgb = RGBColor(*rgb)
        
        # --- Decorative accent line under title ---
        accent_line = slide.shapes.add_shape(
            1,  # Rectangle as thin line
            Inches(3.5), Inches(4.5), Inches(3), Inches(0.05)
        )
        accent_line.fill.solid()
        rgb = self._hex_to_rgb(KELP_COLORS["cyan_blue"])
        accent_line.fill.fore_color.rgb = RGBColor(*rgb)
        accent_line.line.fill.background()
        
        # --- Subtitle with refined styling ---
        subtitle_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(4.8), Inches(9), Inches(0.6)
        )
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.text = "Investment Teaser  |  Strictly Confidential"
        
        subtitle_para = subtitle_frame.paragraphs[0]
        subtitle_para.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
        subtitle_para.font.name = KELP_FONT_BODY
        subtitle_para.font.size = Pt(18)
        subtitle_para.font.italic = True
        rgb = self._hex_to_rgb(KELP_COLORS["cyan_blue"])
        subtitle_para.font.color.rgb = RGBColor(*rgb)
        
        # Footer
        self._add_footer(slide)
        
        logger.debug("Title slide created with modern Kelp branding")
        return slide
    
    def create_content_slide(self, title: str) -> object:
        """
        Create content slide with modern white background and premium title bar.
        
        Args:
            title: Slide title
        
        Returns:
            Slide object
        """
        slide_layout = self.prs.slide_layouts[6]  # Blank
        slide = self.prs.slides.add_slide(slide_layout)
        
        # White background 
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(255, 255, 255)
        
        # --- Modern Logo styling ---
        logo_box = slide.shapes.add_textbox(
            Inches(0.4), Inches(0.15), Inches(1.5), Inches(0.4)
        )
        text_frame = logo_box.text_frame
        text_frame.text = "KELP"
        
        p = text_frame.paragraphs[0]
        p.font.name = KELP_FONT_HEAD
        p.font.size = Pt(16)
        p.font.bold = True
        rgb = self._hex_to_rgb(KELP_COLORS["gradient_orange"])
        p.font.color.rgb = RGBColor(*rgb)
        
        # --- Thicker, more modern accent bar ---
        accent_bar = slide.shapes.add_shape(
            1,  # Rectangle
            Inches(0), Inches(0.6), Inches(10), Inches(0.6)
        )
        accent_fill = accent_bar.fill
        accent_fill.solid()
        rgb = self._hex_to_rgb(KELP_COLORS["primary_dark"])  # Dark indigo per branding
        accent_fill.fore_color.rgb = RGBColor(*rgb)
        accent_bar.line.fill.background()
        
        # --- Title text (larger, on colored bar) ---
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.68), Inches(9), Inches(0.5)
        )
        title_frame = title_box.text_frame
        title_frame.text = title.upper()
        
        # Title Styling
        title_para = title_frame.paragraphs[0]
        title_para.font.name = KELP_FONT_HEAD
        title_para.font.size = Pt(24)
        title_para.font.bold = True
        rgb = self._hex_to_rgb(KELP_COLORS["text_light"])
        title_para.font.color.rgb = RGBColor(*rgb)
        
        # --- Subtle bottom accent line ---
        bottom_accent = slide.shapes.add_shape(
            1,  # Rectangle as thin line
            Inches(0), Inches(7.0), Inches(10), Inches(0.04)
        )
        bottom_accent.fill.solid()
        rgb = self._hex_to_rgb(KELP_COLORS["primary_dark"])  # Dark indigo line
        bottom_accent.fill.fore_color.rgb = RGBColor(*rgb)
        bottom_accent.line.fill.background()
        
        # Footer (below line)
        self._add_footer(slide, y_pos=7.1)
        
        logger.debug(f"Content slide created (Modern White): {title}")
        return slide
    
    def save(self, output_path: str):
        """
        Save presentation to file.
        
        Args:
            output_path: Output file path
        """
        self.prs.save(output_path)
        logger.info(f" Presentation saved: {output_path}")
