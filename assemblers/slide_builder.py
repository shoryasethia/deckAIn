"""
deckAIn - Slide Builder
Stage 6: Assemble complete PowerPoint presentation
"""

from pathlib import Path
from typing import Dict, List, Optional
from pptx.util import Inches, Pt
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT as PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image as PILImage

from extractors.schemas import SlideContent, ChartSpec, FinancialData
from assemblers.ppt_template import PPTTemplate
from assemblers.native_charts import NativeChartsCreator
from assemblers.components import (
    draw_section_header, draw_timeline, draw_stat_grid,
    draw_rect, draw_line, draw_text_box, draw_image_box,
    draw_bullet_point, draw_decorative_bar
)
from config.settings import (
    KELP_COLORS, KELP_FOOTER_TEXT, KELP_FONT_HEAD, KELP_FONT_BODY,
    OUTPUT_DIR
)
from config.prompts import LAYOUT_GENERATION_WITH_CHARTS_PROMPT
from generators.layout_engine import LayoutEngine
from assets.icon_helper import IconHelper
from assets.pillow_icons import generate_icon_png, generate_cert_badge
from utils.logger import setup_logger, log_stage

logger = setup_logger(__name__)

class SlideBuilder:
    """
    Constructs presentation slides using content and template.
    Now supports Generative Layouts via LayoutEngine.
    """
    
    def __init__(self, ppt_template: PPTTemplate, layout_engine: LayoutEngine = None):
        """
        Initialize builder.
        
        Args:
            ppt_template: Initialized template handler
            layout_engine: Optional Generative Layout Engine
        """
        self.template = ppt_template
        self.charts_creator = NativeChartsCreator()
        self.icon_helper = IconHelper()
        self.layout_engine = layout_engine
        self.layout_variant = None
        logger.info(f"SlideBuilder initialized (Premium Mode, LayoutEngine: {'Active' if layout_engine else 'Inactive'})")
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _format_text_with_bold_numbers(self, text_frame, text: str, font_name: str, font_size: int, color_rgb: tuple):
        """Format text with numbers in bold and rest in regular."""
        import re
        # Split text into parts (numbers vs text)
        parts = re.split(r'(\d+[.,]?\d*%?)', text)
        
        p = text_frame.paragraphs[0]
        for i, part in enumerate(parts):
            if not part:
                continue
            run = p.add_run() if i > 0 else p.runs[0] if p.runs else p.add_run()
            run.text = part
            run.font.name = font_name
            run.font.size = Pt(font_size)
            run.font.color.rgb = RGBColor(*color_rgb)
            # Bold if it's a number
            if re.match(r'^\d+[.,]?\d*%?$', part):
                run.font.bold = True
            else:
                run.font.bold = False
    
    def build_presentation(
        self,
        content: SlideContent,
        financial_data: FinancialData, # Added this
        chart_specs: Dict[str, ChartSpec],
        images: Dict[str, Dict],
        output_filename: str = None,
        company_output_dir: Path = None,
        sector: str = None,
        layout_variant: str = None
        ) -> str:
        """
        Build complete 5-slide presentation.
        """
        log_stage(logger, 6, "PPT Assembly", "START")
        
        self.layout_variant = layout_variant or self._select_layout_variant(sector)

        # Slide 1: Cover Slide (Dark Theme + Image)
        logger.info("Building Slide 1: Cover")
        self._build_cover_slide(content, images.get("image_1"))
        
        # Slide 2: Business Profile
        logger.info("Building Slide 2: Business Profile")
        self._build_business_profile_slide(content, images)
        
        # Slide 3: Financials
        logger.info("Building Slide 3: Financials")
        self._build_financial_slide(content, financial_data, chart_specs, images)
        
        # Slide 4: Investment Highlights
        logger.info("Building Slide 4: Investment Highlights")
        self._build_highlights_slide(content, images.get("image_3"))
        
        # Slide 5: Disclaimer / End (Dark Theme)
        logger.info("Building Slide 5: Disclaimer")
        self._build_end_slide(content)
        
        # Save
        if output_filename is None:
            safe_name = content.company_codename.replace(" ", "_").replace("/", "-")
            output_filename = f"{safe_name}_Investment_Teaser.pptx"
        
        output_dir = company_output_dir if company_output_dir else OUTPUT_DIR
        output_path = output_dir / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.template.save(str(output_path))
        
        log_stage(logger, 6, "PPT Assembly", "DONE")
        logger.info(f"Presentation created: {output_path} (5 slides)")
        
        return str(output_path)

    # =========================================================================
    # SLIDE 1: COVER
    # =========================================================================
    def _build_cover_slide(self, content: SlideContent, image_data: Dict = None):
        """Build Slide 1: Cover Slide (EXACT replica of pg1.png)"""
        # Create blank slide
        layout = self.template.prs.slide_layouts[6] 
        slide = self.template.prs.slides.add_slide(layout)
        
        # Colors matching pg1.png exactly
        KELP_BLUE = RGBColor(0, 51, 153)        # Left sidebar blue #003399
        DEEP_PURPLE = RGBColor(45, 20, 70)      # Main background #2D1446
        MAGENTA_OVERLAY = RGBColor(209, 21, 99) # Pink/Magenta overlay #D11563
        
        # 1. Main Background (Deep Purple gradient-like)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.63))
        bg.fill.solid()
        bg.fill.fore_color.rgb = DEEP_PURPLE
        bg.line.fill.background()
        
        # 2. Left Sidebar (Solid Blue Bar)
        sidebar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.85), Inches(5.63))
        sidebar.fill.solid()
        sidebar.fill.fore_color.rgb = KELP_BLUE
        sidebar.line.fill.background()
        
        # 3. Large Magenta Diamond/Rectangle Overlay (Top-Left Geometric Shape)
        # This creates the dramatic pink overlay seen in pg1.png
        overlay1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(0), Inches(4.5), Inches(3.2))
        overlay1.fill.solid()
        overlay1.fill.fore_color.rgb = MAGENTA_OVERLAY
        overlay1.line.fill.background()
        overlay1.rotation = 0
        
        # 4. Smaller Magenta Triangle (creates depth effect)
        triangle = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(1.2), Inches(2.8), Inches(3.5), Inches(3.0))
        triangle.rotation = 45
        triangle.fill.solid()
        triangle.fill.fore_color.rgb = MAGENTA_OVERLAY
        triangle.fill.transparency = 0.3
        triangle.line.fill.background()
        
        # 5. Kelp Logo (Icon + Text) at Top Left - Using actual logo image
        logo_path = Path("assets/kelp_logo.png")
        if logo_path.exists():
            try:
                # Logo image already contains both icon and "Kelp" text
                slide.shapes.add_picture(str(logo_path), Inches(1.5), Inches(0.35), height=Inches(0.9))
            except Exception as e:
                logger.warning(f"Could not add logo: {e}")
                # Fallback to text if image fails
                kelp_text = slide.shapes.add_textbox(Inches(1.5), Inches(0.45), Inches(2.0), Inches(0.7))
                kelp_p = kelp_text.text_frame.paragraphs[0]
                kelp_p.text = "Kelp"
                kelp_p.font.name = "Arial"
                kelp_p.font.size = Pt(48)
                kelp_p.font.bold = True
                kelp_p.font.color.rgb = RGBColor(255, 255, 255)
        else:
            # Fallback if logo doesn't exist
            kelp_text = slide.shapes.add_textbox(Inches(1.5), Inches(0.45), Inches(2.0), Inches(0.7))
            kelp_p = kelp_text.text_frame.paragraphs[0]
            kelp_p.text = "Kelp"
            kelp_p.font.name = "Arial"
            kelp_p.font.size = Pt(48)
            kelp_p.font.bold = True
            kelp_p.font.color.rgb = RGBColor(255, 255, 255)

        # 6. Title "Project [Codename]" (Large, White, positioned prominently)
        title_box = slide.shapes.add_textbox(Inches(1.5), Inches(1.6), Inches(7.5), Inches(1.5))
        p = title_box.text_frame.paragraphs[0]
        p.text = content.company_codename
        p.font.name = "Arial"
        p.font.size = Pt(72)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.line_spacing = 1.0
        
        # 7. Subtitle "Investment Brief"
        sub_box = slide.shapes.add_textbox(Inches(1.5), Inches(3.8), Inches(5.0), Inches(0.6))
        p1 = sub_box.text_frame.paragraphs[0]
        p1.text = "Investment Brief"
        p1.font.name = "Arial"
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(255, 255, 255)
        
        # 8. Website URL (italic, lighter)
        url_box = slide.shapes.add_textbox(Inches(1.5), Inches(4.4), Inches(4.0), Inches(0.4))
        p2 = url_box.text_frame.paragraphs[0]
        p2.text = "kelpglobal.com"
        p2.font.name = "Arial"
        p2.font.size = Pt(14)
        p2.font.italic = True
        p2.font.color.rgb = RGBColor(200, 200, 200)

    def _apply_kelp_branding(self, slide, title_text: str):
        """
        Apply standard Kelp branding (Header/Footer) to a slide.
        This provides a Fixed Scaffolding for perfect alignment.
        """
        # --- HEADER BAR ---
        # Dark Indigo Band at top
        header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(0.8))
        header.fill.solid()
        header.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        header.line.fill.background()
        
        # --- TITLE (Top Left) ---
        tbox = slide.shapes.add_textbox(Inches(0.3), Inches(0.15), Inches(6.0), Inches(0.5))
        p = tbox.text_frame.paragraphs[0]
        p.text = title_text.upper()
        p.font.name = "Arial"
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        
        # --- KELP LOGO (Top Right) ---
        logo_path = Path("assets/kelp_logo.png")
        if logo_path.exists():
            try:
                # Logo image contains both icon and text - place on right side (within boundaries)
                slide.shapes.add_picture(str(logo_path), Inches(8.3), Inches(0.1), height=Inches(0.6))
            except Exception as e:
                logger.warning(f"Could not add logo to header: {e}")
                # Fallback to text only on right
                kelp_box = slide.shapes.add_textbox(Inches(8.3), Inches(0.15), Inches(1.3), Inches(0.5))
                kelp_p = kelp_box.text_frame.paragraphs[0]
                kelp_p.text = "Kelp"
                kelp_p.font.name = "Arial"
                kelp_p.font.size = Pt(20)
                kelp_p.font.bold = True
                kelp_p.font.color.rgb = RGBColor(255, 255, 255)
        else:
            # Fallback to text if no logo
            kelp_box = slide.shapes.add_textbox(Inches(8.5), Inches(0.15), Inches(1.3), Inches(0.5))
            kelp_p = kelp_box.text_frame.paragraphs[0]
            kelp_p.text = "Kelp"
            kelp_p.font.name = "Arial"
            kelp_p.font.size = Pt(20)
            kelp_p.font.bold = True
            kelp_p.font.color.rgb = RGBColor(255, 255, 255)
            
        # --- FOOTER ---
        # Light Grey Band at bottom
        footer = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(5.3), Inches(10), Inches(0.33))
        footer.fill.solid()
        footer.fill.fore_color.rgb = RGBColor(245, 245, 245)
        footer.line.fill.background() # No border
        
        # Footer Text (9pt as per spec - DO NOT CHANGE)
        fbox = slide.shapes.add_textbox(Inches(0.5), Inches(5.35), Inches(9.0), Inches(0.25))
        p = fbox.text_frame.paragraphs[0]
        p.text = KELP_FOOTER_TEXT
        p.font.size = Pt(9)
        p.font.color.rgb = RGBColor(100, 100, 100)
        p.alignment = PP_ALIGN.CENTER

    def _select_layout_variant(self, sector: str) -> str:
        """Pick a layout variant by sector for visual variety."""
        if not sector:
            return "classic"

        sector_key = sector.lower()
        split_sectors = ["consumer", "d2c", "technology", "services", "logistics"]
        if any(key in sector_key for key in split_sectors):
            return "split"
        return "classic"

    # =========================================================================
    # SLIDE 2: BUSINESS PROFILE
    # =========================================================================
    def _build_business_profile_slide(self, content: SlideContent, images_dict: Dict = None):
        """Build Slide 2: Business Profile (Generative Layout)."""
        # Create blank slide
        layout = self.template.prs.slide_layouts[6] 
        slide = self.template.prs.slides.add_slide(layout)
        
        # 1. FIXED BRANDING SCAFFOLDING
        self._apply_kelp_branding(slide, "Business Overview")
        
        biz_data = content.slide_2_business_overview

        if self.layout_variant == "split":
            self._build_business_profile_variant_split(slide, biz_data, images_dict)
            return
        
        # === DENSE 3-COLUMN PROFESSIONAL LAYOUT ===
        logger.info("Building dense 3-column Business Profile layout")
        
        # === LEFT COLUMN (0.3" - 5.0") - MAIN CONTENT ===
        
        # Section 1: Business Overview
        sec1_bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.3), Inches(0.85), Inches(4.7), Inches(0.28)
        )
        sec1_bg.fill.solid()
        sec1_bg.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        sec1_bg.line.fill.background()
        
        sec1_title = slide.shapes.add_textbox(Inches(0.4), Inches(0.88), Inches(4.5), Inches(0.22))
        s1_p = sec1_title.text_frame.paragraphs[0]
        s1_p.text = "Business Overview:"
        s1_p.font.name = KELP_FONT_HEAD
        s1_p.font.size = Pt(11)
        s1_p.font.bold = True
        s1_p.font.color.rgb = RGBColor(255, 255, 255)
        
        # Dense bullet points - Complete sentences, no truncation
        bullets_data = []
        if biz_data.operational_highlights:
            bullets_data.extend(biz_data.operational_highlights[:6])  # Use full highlights
        
        y_bullet = 1.18
        for bullet in bullets_data[:6]:
            b_box = slide.shapes.add_textbox(Inches(0.4), Inches(y_bullet), Inches(4.4), Inches(0.4))
            b_box.text_frame.word_wrap = True
            b_p = b_box.text_frame.paragraphs[0]
            b_p.text = f"■ {bullet}"
            b_p.font.name = KELP_FONT_BODY
            b_p.font.size = Pt(8.5)  # Smaller font for density
            b_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_body"]))
            b_p.line_spacing = 1.0
            y_bullet += 0.35  # Slightly more spacing for full text
        
        # Section 2: Product Portfolio / Growth Timeline
        sec2_y = y_bullet + 0.15
        sec2_bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.3), Inches(sec2_y), Inches(4.7), Inches(0.42)
        )
        sec2_bg.fill.solid()
        sec2_bg.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        sec2_bg.line.fill.background()
        
        sec2_title = slide.shapes.add_textbox(Inches(0.4), Inches(sec2_y + 0.03), Inches(4.5), Inches(0.36))
        sec2_title.text_frame.word_wrap = True
        s2_p = sec2_title.text_frame.paragraphs[0]
        s2_p.text = "Growth led through its growing product portfolio and offering solutions to diverse sectors"
        s2_p.font.name = KELP_FONT_HEAD
        s2_p.font.size = Pt(8)
        s2_p.font.bold = True
        s2_p.font.color.rgb = RGBColor(255, 255, 255)
        s2_p.line_spacing = 1.1
        
        # Product Portfolio Grid (2 columns x 4 rows, dashed boxes with icons)
        if biz_data.product_categories:
            grid_y = sec2_y + 0.4
            for idx, product in enumerate(biz_data.product_categories[:8]):
                col = idx % 2
                row = idx // 2
                x_pos = 0.4 + (col * 2.3)
                y_pos = grid_y + (row * 0.32)
                
                prod_box = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(x_pos), Inches(y_pos), Inches(2.15), Inches(0.28)
                )
                prod_box.fill.solid()
                prod_box.fill.fore_color.rgb = RGBColor(250, 252, 255)  # Very light blue tint
                prod_box.line.color.rgb = RGBColor(200, 210, 225)
                prod_box.line.width = Pt(0.75)
                
                p_text = slide.shapes.add_textbox(Inches(x_pos + 0.08), Inches(y_pos + 0.05), Inches(2.0), Inches(0.18))
                p_p = p_text.text_frame.paragraphs[0]
                p_p.text = product
                p_p.font.name = KELP_FONT_BODY
                p_p.font.size = Pt(8)
                p_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_dark"]))
                p_p.alignment = PP_ALIGN.CENTER
        
        # === MIDDLE COLUMN (5.2" - 7.0") - CUSTOMERS ===
        cust_bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(5.2), Inches(0.85), Inches(1.8), Inches(0.28)
        )
        cust_bg.fill.solid()
        cust_bg.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        cust_bg.line.fill.background()
        
        cust_title = slide.shapes.add_textbox(Inches(5.3), Inches(0.88), Inches(1.6), Inches(0.22))
        ct_p = cust_title.text_frame.paragraphs[0]
        ct_p.text = "Key Select Customers"
        ct_p.font.name = KELP_FONT_HEAD
        ct_p.font.size = Pt(10)
        ct_p.font.bold = True
        ct_p.font.color.rgb = RGBColor(255, 255, 255)
        
        # Customer boxes - use real data from content
        customer_y = 1.2
        if biz_data.key_customers:
            customer_names = biz_data.key_customers[:4]
        else:
            customer_names = ["Leading Pharmaceutical\nCompanies", "Global Generic\nManufacturers", "Healthcare\nProviders", "...and others"]
        for cust_name in customer_names:
            cust_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(5.3), Inches(customer_y), Inches(1.6), Inches(0.45)
            )
            cust_box.fill.solid()
            cust_box.fill.fore_color.rgb = RGBColor(250, 250, 250)
            cust_box.line.color.rgb = RGBColor(200, 200, 200)
            cust_box.line.width = Pt(0.5)
            
            c_text = slide.shapes.add_textbox(Inches(5.32), Inches(customer_y + 0.03), Inches(1.56), Inches(0.38))
            c_text.text_frame.word_wrap = True
            c_text.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            c_text.text_frame.margin_left = Inches(0.03)
            c_text.text_frame.margin_right = Inches(0.03)
            c_p = c_text.text_frame.paragraphs[0]
            c_p.text = cust_name
            c_p.font.name = KELP_FONT_BODY
            c_p.font.size = Pt(7)
            c_p.font.bold = True
            c_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_dark"]))
            c_p.alignment = PP_ALIGN.CENTER
            c_p.line_spacing = 0.95
            
            customer_y += 0.5
        
        # === RIGHT COLUMN (7.1" - 9.7") - AT A GLANCE ===
        glance_bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(7.1), Inches(0.85), Inches(2.6), Inches(0.28)
        )
        glance_bg.fill.solid()
        glance_bg.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        glance_bg.line.fill.background()
        
        glance_title = slide.shapes.add_textbox(Inches(7.2), Inches(0.88), Inches(2.4), Inches(0.22))
        gt_p = glance_title.text_frame.paragraphs[0]
        gt_p.text = f"{biz_data.main_text.split()[0] if biz_data.main_text else 'Company'} at a Glance"
        gt_p.font.name = KELP_FONT_HEAD
        gt_p.font.size = Pt(10)
        gt_p.font.bold = True
        gt_p.font.color.rgb = RGBColor(255, 255, 255)
        
        # Stats cards with icons (matching professional sample quality)
        if biz_data.key_stats:
            stat_y = 1.2
            colors = [RGBColor(0, 118, 168), RGBColor(255, 102, 0), RGBColor(106, 27, 154)]
            # Icon keywords for stats - match common stat types
            stat_icon_keywords = ["people", "building", "globe"]  # employee, facility, export/global
            
            for idx, stat in enumerate(biz_data.key_stats[:3]):
                # Icon circle (professional colored background)
                circle = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Inches(7.25), Inches(stat_y), Inches(0.45), Inches(0.45)
                )
                circle.fill.solid()
                circle.fill.fore_color.rgb = colors[idx % 3]
                circle.line.fill.background()
                
                # Add icon inside circle if available
                if self.icon_helper:
                    stat_label = stat.get("label", "")
                    # Try to match icon to stat type
                    icon_keyword = stat_icon_keywords[idx % 3]
                    if "employee" in stat_label.lower() or "team" in stat_label.lower():
                        icon_keyword = "people"
                    elif "facility" in stat_label.lower() or "unit" in stat_label.lower() or "plant" in stat_label.lower():
                        icon_keyword = "building"
                    elif "export" in stat_label.lower() or "global" in stat_label.lower() or "reach" in stat_label.lower():
                        icon_keyword = "globe"
                    
                    icon_path = self.icon_helper.get_icon_png_path(icon_keyword, size=28)
                    if icon_path:
                        try:
                            slide.shapes.add_picture(
                                str(icon_path), 
                                Inches(7.34), Inches(stat_y + 0.085), 
                                Inches(0.27), Inches(0.27)
                            )
                        except Exception as e:
                            logger.debug(f"Could not add stat icon: {e}")
                
                # Value + Label (side by side for compactness)
                vbox = slide.shapes.add_textbox(Inches(7.8), Inches(stat_y), Inches(1.8), Inches(0.22))
                vp = vbox.text_frame.paragraphs[0]
                value_text = str(stat.get("value", ""))
                vp.text = value_text
                vp.font.name = KELP_FONT_HEAD
                if len(value_text) <= 4:
                    vp.font.size = Pt(15)
                elif len(value_text) <= 7:
                    vp.font.size = Pt(13)
                else:
                    vp.font.size = Pt(11)
                vp.font.bold = True
                vp.font.color.rgb = colors[idx % 3]
                
                lbox = slide.shapes.add_textbox(Inches(7.8), Inches(stat_y + 0.25), Inches(1.8), Inches(0.18))
                lp = lbox.text_frame.paragraphs[0]
                lp.text = str(stat.get("label", ""))
                lp.font.name = KELP_FONT_BODY
                lp.font.size = Pt(7.5)
                lp.font.color.rgb = RGBColor(100, 100, 100)
                
                stat_y += 0.55
        
        # Certifications section
        cert_y = stat_y + 0.15
        cert_bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(7.1), Inches(cert_y), Inches(2.6), Inches(0.28)
        )
        cert_bg.fill.solid()
        cert_bg.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        cert_bg.line.fill.background()
        
        cert_title = slide.shapes.add_textbox(Inches(7.2), Inches(cert_y + 0.03), Inches(2.4), Inches(0.22))
        cert_p = cert_title.text_frame.paragraphs[0]
        cert_p.text = "Certifications"
        cert_p.font.name = KELP_FONT_HEAD
        cert_p.font.size = Pt(10)
        cert_p.font.bold = True
        cert_p.font.color.rgb = RGBColor(255, 255, 255)
        
        # Certification badges grid (3x3) - Use certifications from content
        cert_grid_y = cert_y + 0.4
        # Get certifications from business overview data, fallback to defaults
        if hasattr(biz_data, 'certifications') and biz_data.certifications:
            cert_names = biz_data.certifications
        else:
            # Fallback to common certifications (sector-agnostic)
            cert_names = ["ISO", "CMMI"]
        
        for idx, cert in enumerate(cert_names[:9]):
            col = idx % 3
            row = idx // 3
            x_pos = 7.2 + (col * 0.85)
            y_pos = cert_grid_y + (row * 0.4)
            
            # Try Pillow-generated badge image first
            badge_img = generate_cert_badge(cert, width=100, height=60)
            if badge_img:
                try:
                    slide.shapes.add_picture(
                        str(badge_img),
                        Inches(x_pos), Inches(y_pos),
                        Inches(0.75), Inches(0.32)
                    )
                    continue  # Skip text fallback
                except Exception:
                    pass
            
            # Fallback: text badge
            badge = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(x_pos), Inches(y_pos), Inches(0.75), Inches(0.35)
            )
            badge.fill.solid()
            badge.fill.fore_color.rgb = RGBColor(248, 249, 250)
            badge.line.color.rgb = RGBColor(200, 206, 212)
            badge.line.width = Pt(0.75)
            
            b_text = slide.shapes.add_textbox(Inches(x_pos + 0.05), Inches(y_pos + 0.08), Inches(0.65), Inches(0.18))
            b_p = b_text.text_frame.paragraphs[0]
            b_p.text = cert
            b_p.font.name = KELP_FONT_BODY
            b_p.font.size = Pt(7.0)
            b_p.font.bold = True
            b_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
            b_p.alignment = PP_ALIGN.CENTER
        
        # Add image at bottom spanning full left column to fill white space
        # Reduced height to prevent footer overlap (footer at ~5.3")
        if images_dict and images_dict.get("image_2"):
            img_path = images_dict["image_2"].get("path")
            if not draw_image_box(slide, img_path, 0.5, 4.8, 4.5, 0.4):
                # Add placeholder with industry visual
                img_placeholder = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(0.5), Inches(4.8), Inches(4.5), Inches(0.4)
                )
                img_placeholder.fill.solid()
                img_placeholder.fill.fore_color.rgb = RGBColor(245, 248, 252)
                img_placeholder.line.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_indigo"]))
                img_placeholder.line.width = Pt(1)
        else:
            # Add placeholder if no image - optimized size
            img_placeholder = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(0.5), Inches(4.8), Inches(4.5), Inches(0.4)
            )
            img_placeholder.fill.solid()
            img_placeholder.fill.fore_color.rgb = RGBColor(245, 248, 252)
            img_placeholder.line.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_indigo"]))
            img_placeholder.line.width = Pt(1)

    def _build_business_profile_variant_split(self, slide, biz_data, images_dict: Dict = None):
        """Variant layout with split columns and timeline block."""
        logger.info("Building split Business Profile layout")

        # Left column: Overview + highlights + products
        draw_text_box(
            slide,
            biz_data.main_text,
            0.6, 1.05, 5.8, 1.05,
            size=9, color_key="text_body"
        )

        # Operational highlights
        highlight_y = 2.25
        for item in biz_data.operational_highlights[:4]:
            draw_text_box(
                slide,
                f"■ {item}",
                0.7, highlight_y, 5.6, 0.3,
                size=8.5, color_key="text_body"
            )
            highlight_y += 0.28

        # Product segments
        draw_section_header(slide, "Product Segments", 0.5, 3.45, width=6.0)
        prod_y = 3.75
        for idx, product in enumerate(biz_data.product_categories[:6]):
            col = idx % 2
            row = idx // 2
            x_pos = 0.6 + (col * 3.0)
            y_pos = prod_y + (row * 0.32)
            prod_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(x_pos), Inches(y_pos), Inches(2.8), Inches(0.26)
            )
            prod_box.fill.solid()
            prod_box.fill.fore_color.rgb = RGBColor(240, 245, 255)
            prod_box.line.color.rgb = RGBColor(200, 210, 225)
            prod_box.line.width = Pt(0.75)

            p_text = slide.shapes.add_textbox(Inches(x_pos + 0.06), Inches(y_pos + 0.04), Inches(2.6), Inches(0.18))
            p_p = p_text.text_frame.paragraphs[0]
            p_p.text = product
            p_p.font.name = KELP_FONT_BODY
            p_p.font.size = Pt(8)
            p_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_dark"]))
            p_p.alignment = PP_ALIGN.CENTER

        # Right column: stats + customers + certifications
        draw_section_header(slide, "At a Glance", 6.7, 0.95, width=2.6)
        draw_stat_grid(slide, biz_data.key_stats, 6.8, 1.32, 2.4, 1.0)

        draw_section_header(slide, "Key Customers", 6.7, 2.65, width=2.6)
        cust_y = 2.92
        for cust in biz_data.key_customers[:3]:  # Max 3 to leave room for certs
            c_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(6.8), Inches(cust_y), Inches(2.4), Inches(0.32)
            )
            c_box.fill.solid()
            c_box.fill.fore_color.rgb = RGBColor(250, 250, 250)
            c_box.line.color.rgb = RGBColor(200, 200, 200)
            c_box.line.width = Pt(0.5)

            c_text = slide.shapes.add_textbox(Inches(6.85), Inches(cust_y + 0.03), Inches(2.3), Inches(0.26))
            c_text.text_frame.word_wrap = True
            c_text.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            c_p = c_text.text_frame.paragraphs[0]
            c_p.text = cust
            c_p.font.name = KELP_FONT_BODY
            c_p.font.size = Pt(7)
            c_p.font.bold = True
            c_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_dark"]))
            c_p.alignment = PP_ALIGN.CENTER
            cust_y += 0.38

        # Certifications positioned dynamically after customers
        cert_header_y = cust_y + 0.08
        draw_section_header(slide, "Certifications", 6.7, cert_header_y, width=2.6)
        certs = biz_data.certifications or ["ISO", "CMMI"]
        cert_y = cert_header_y + 0.42  # Below the pink underline (at y+0.35+0.03)
        for idx, cert in enumerate(certs[:4]):
            col = idx % 2
            row = idx // 2
            x_pos = 6.8 + (col * 1.2)
            y_pos = cert_y + (row * 0.3)

            # Try Pillow-generated badge image first
            badge_img = generate_cert_badge(cert, width=120, height=80)
            if badge_img:
                try:
                    slide.shapes.add_picture(
                        str(badge_img),
                        Inches(x_pos), Inches(y_pos),
                        Inches(1.1), Inches(0.28)
                    )
                    continue  # Skip text fallback
                except Exception:
                    pass

            # Fallback: text badge
            badge = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(x_pos), Inches(y_pos), Inches(1.1), Inches(0.28)
            )
            badge.fill.solid()
            badge.fill.fore_color.rgb = RGBColor(248, 249, 250)
            badge.line.color.rgb = RGBColor(200, 206, 212)
            badge.line.width = Pt(0.75)

            b_text = slide.shapes.add_textbox(Inches(x_pos + 0.05), Inches(y_pos + 0.06), Inches(1.0), Inches(0.16))
            b_p = b_text.text_frame.paragraphs[0]
            b_p.text = cert
            b_p.font.name = KELP_FONT_BODY
            b_p.font.size = Pt(7.5)
            b_p.font.bold = True
            b_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
            b_p.alignment = PP_ALIGN.CENTER

    def _build_highlights_variant_split(self, slide, highlights: List, image_data: Dict = None):
        """Variant layout with image on right and highlight cards on left."""
        # Right image
        image_added = False
        if image_data and image_data.get("path"):
            if draw_image_box(slide, image_data.get("path"), 5.95, 1.05, 3.7, 4.1):
                image_added = True

        if not image_added:
            placeholder = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(5.95), Inches(1.05), Inches(3.7), Inches(4.1)
            )
            placeholder.fill.solid()
            placeholder.fill.fore_color.rgb = RGBColor(240, 245, 250)
            placeholder.line.color.rgb = RGBColor(200, 210, 225)
            placeholder.line.width = Pt(1)

        # Highlight cards - 2 columns, max 4 cards for clean 2x2 grid
        display_highlights = highlights[:4]
        start_x = 0.3
        start_y = 1.1
        col_w = 2.6
        col_gap = 0.2
        row_h = 1.9  # Two rows fill the available vertical space

        for idx, hl in enumerate(display_highlights):
            col = idx % 2
            row = idx // 2
            x = start_x + (col * (col_w + col_gap))
            y = start_y + (row * (row_h + 0.15))

            # Card with consistent subtle border
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(x), Inches(y), Inches(col_w), Inches(row_h)
            )
            card.fill.solid()
            card.fill.fore_color.rgb = RGBColor(248, 249, 252)
            card.line.color.rgb = RGBColor(200, 210, 225)
            card.line.width = Pt(1)

            # Icon from Pillow generator
            icon_png = generate_icon_png(hl.title, size=64, icon_index=idx)
            if icon_png:
                try:
                    slide.shapes.add_picture(
                        str(icon_png),
                        Inches(x + 0.12), Inches(y + 0.15),
                        Inches(0.28), Inches(0.28)
                    )
                except Exception:
                    pass
            else:
                # Fallback: colored circle with letter
                icon_colors = ["gradient_pink", "primary_indigo", "cyan_blue", "gradient_purple"]
                icon_circ = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Inches(x + 0.12), Inches(y + 0.15), Inches(0.28), Inches(0.28)
                )
                icon_circ.fill.solid()
                icon_circ.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS[icon_colors[idx % 4]]))
                icon_circ.line.fill.background()
                icon_text = slide.shapes.add_textbox(Inches(x + 0.13), Inches(y + 0.15), Inches(0.28), Inches(0.28))
                ip = icon_text.text_frame.paragraphs[0]
                ip.text = (hl.title[:1] if hl.title else "•")
                ip.font.name = KELP_FONT_HEAD
                ip.font.size = Pt(11)
                ip.font.bold = True
                ip.font.color.rgb = RGBColor(255, 255, 255)
                ip.alignment = PP_ALIGN.CENTER

            # Title — word wrap enabled for long titles
            title_box = slide.shapes.add_textbox(Inches(x + 0.48), Inches(y + 0.08), Inches(col_w - 0.6), Inches(0.35))
            title_box.text_frame.word_wrap = True
            t_p = title_box.text_frame.paragraphs[0]
            t_p.text = hl.title
            t_p.font.name = KELP_FONT_HEAD
            t_p.font.size = Pt(8.5)
            t_p.font.bold = True
            t_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))

            # Body text with plenty of room
            body_box = slide.shapes.add_textbox(Inches(x + 0.12), Inches(y + 0.5), Inches(col_w - 0.24), Inches(row_h - 0.6))
            body_box.text_frame.word_wrap = True
            b_p = body_box.text_frame.paragraphs[0]
            b_p.text = hl.text
            b_p.font.name = KELP_FONT_BODY
            b_p.font.size = Pt(7.5)
            b_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_body"]))
            b_p.line_spacing = 1.15


    # =========================================================================
    # SLIDE 3: FINANCIALS
    # =========================================================================
    def _build_financial_slide(self, content: SlideContent, financial_data: FinancialData, chart_specs: Dict[str, ChartSpec] = None, images_dict: Dict = None):
        """Build Slide 3: Financials (Rule-based Dense Layout)."""
        # --- FIX: Removed redundant self.template.create_content_slide call which created a blank slide ---
        layout = self.template.prs.slide_layouts[6]
        slide = self.template.prs.slides.add_slide(layout)
        self._apply_kelp_branding(slide, "Key Financial Metrics")
        
        # --- GENERATIVE LAYOUT ATTEMPT ---
        if self.layout_engine:
            logger.info("Attempting Generative Layout for Financials...")
            context = {
                "Inches": Inches, "Pt": Pt, "RGBColor": RGBColor, 
                "MSO_SHAPE": MSO_SHAPE, "PP_ALIGN": PP_ALIGN,
                "MSO_ANCHOR": MSO_ANCHOR, "MSO_AUTO_SIZE": MSO_AUTO_SIZE,
                "slide": slide,
                "charts_creator": self.charts_creator,
                "chart_specs": chart_specs or {},
                "draw_rect": draw_rect,
                "draw_line": draw_line,
                "draw_text_box": draw_text_box,
                "hex_to_rgb": self._hex_to_rgb
            }
            
            # Prepare content
            content_dict = {
                "narrative": content.slide_3_growth_narrative,
                "financial_summary": "See charts for data." 
            }
            
            try:
                success = self.layout_engine.generate_and_execute(slide, content_dict, context, LAYOUT_GENERATION_WITH_CHARTS_PROMPT)
            except Exception as e:
                logger.error(f"Layout engine exception: {e}")
                success = False
            
            if success:
                logger.info("Generative Financial Layout Applied!")
                return
            else:
                logger.warning("Generative Layout failed, fallback to standard")

        # --- PREMIUM FINANCIAL DASHBOARD ---
        financials = financial_data
        
        # Pull real data with safe defaults and proper formatting
        rev_val = f"₹ {financials.revenue_by_year[-1]:.1f} Cr" if financials.revenue_by_year else "₹ TBD Cr"
        cagr_val = f"{financials.revenue_cagr:.1f}%" if financials.revenue_cagr else "TBD%"
        ebitda_val = f"{financials.ebitda_margin_latest:.1f}%" if financials.ebitda_margin_latest else "N/A"
        # Format PAT properly - round to 1 decimal, handle large numbers
        if financials.pat_by_year:
            pat_num = financials.pat_by_year[-1]
            pat_val = f"₹ {pat_num:.1f} Cr" if abs(pat_num) < 1000 else f"₹ {pat_num:.0f} Cr"
        else:
            pat_val = "N/A"

        # --- TOP KPI CARDS (4 FINANCIAL-ONLY metrics, no business stats) ---
        kpi_cards_data = [
            ("Latest Revenue", rev_val, "gradient_pink"),
            ("Revenue CAGR", cagr_val, "cyan_blue"),
            ("EBITDA Margin", ebitda_val, "gradient_orange"),
            ("Latest PAT", pat_val, "success_green")
        ]
        
        # Calculate symmetric spacing: 4 cards of 2.2" each = 8.8", spacing = (9.5 - 8.8) / 5 = 0.14"
        card_width = 2.2
        total_cards_width = card_width * 4
        available_space = 9.5
        spacing = (available_space - total_cards_width) / 5
        
        x_positions = [
            0.5 + spacing,
            0.5 + spacing + card_width + spacing,
            0.5 + spacing + (card_width + spacing) * 2,
            0.5 + spacing + (card_width + spacing) * 3
        ]
        
        for i, (label, value, color_key) in enumerate(kpi_cards_data):
            # Card background
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(x_positions[i]), Inches(1.15), Inches(card_width), Inches(0.65)
            )
            card.fill.solid()
            card.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS[color_key]))
            card.line.fill.background()
            
            # Value text box
            tf_box = slide.shapes.add_textbox(
                Inches(x_positions[i] + 0.05), Inches(1.2),
                Inches(card_width - 0.1), Inches(0.35)
            )
            tf = tf_box.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            
            p = tf.paragraphs[0]
            p.text = value
            p.font.bold = True
            # Auto-adjust font size based on text length
            p.font.size = Pt(14) if len(value) > 12 else Pt(16)
            p.font.color.rgb = RGBColor(255, 255, 255)
            p.alignment = PP_ALIGN.CENTER
            
            # Label below
            lbl_box = slide.shapes.add_textbox(
                Inches(x_positions[i] + 0.1), Inches(1.55),
                Inches(card_width - 0.2), Inches(0.2)
            )
            lbl_p = lbl_box.text_frame.paragraphs[0]
            lbl_p.text = label
            lbl_p.font.size = Pt(8)
            lbl_p.font.bold = False
            lbl_p.font.color.rgb = RGBColor(255, 255, 255)
            lbl_p.alignment = PP_ALIGN.CENTER

        # --- DUAL CHART LAYOUT ---
        if chart_specs:
            # Main Chart (Financial Trends) - Left, Larger
            if "financial_trends" in chart_specs:
                self.charts_creator.add_chart_to_slide(
                    slide,
                    chart_specs["financial_trends"],
                    x=0.5, y=2.3, width=5.0, height=2.8
                )
            
            # Second Chart (Margins) - Right, Smaller
            if "margin_evolution" in chart_specs:
                self.charts_creator.add_chart_to_slide(
                    slide,
                    chart_specs["margin_evolution"],
                    x=5.7, y=2.3, width=4.0, height=2.8
                )
        else:
            # Fallback: single chart
            if chart_specs and "financial_trends" in chart_specs:
                self.charts_creator.add_chart_to_slide(
                    slide,
                    chart_specs["financial_trends"],
                    x=0.5, y=2.3, width=6.5, height=2.8
                )

    # =========================================================================
    # SLIDE 4: HIGHLIGHTS
    # =========================================================================
    def _build_highlights_slide(self, content: SlideContent, image_data: Dict = None):
        """Build Slide 4: Highlights (Generative Layout)."""
        # Create blank slide
        layout = self.template.prs.slide_layouts[6] 
        slide = self.template.prs.slides.add_slide(layout)
        
        self._apply_kelp_branding(slide, "Investment Highlights")
        
        highlights = content.slide_4_investment_highlights
        
        # --- GENERATIVE LAYOUT ATTEMPT ---
        success = False  # Initialize before conditional
        if self.layout_engine:
            logger.info("Attempting Generative Layout for Highlights...")
            
            context = {
                "Inches": Inches, "Pt": Pt, "RGBColor": RGBColor, 
                "MSO_SHAPE": MSO_SHAPE, "PP_ALIGN": PP_ALIGN,
                "MSO_ANCHOR": MSO_ANCHOR, "MSO_AUTO_SIZE": MSO_AUTO_SIZE,
                "slide": slide,
                "draw_section_header": draw_section_header,
                "draw_rect": draw_rect,
                "draw_line": draw_line,
                "draw_text_box": draw_text_box,
                "draw_image_box": draw_image_box,
                "hex_to_rgb": self._hex_to_rgb
            }
            
            # Wrap list in dict for JSON
            content_dict = {"highlights": [h.dict() for h in highlights]}
            if image_data and image_data.get("path"):
                content_dict["image_path"] = str(image_data["path"])
            
            try:
                success = self.layout_engine.generate_and_execute(slide, content_dict, context)
            except Exception as e:
                logger.error(f"Layout engine exception: {e}")
                success = False
                
        # Apply fallback layout (disabled generative for now)
        if not success:
            logger.info("Building Premium Highlights Layout")

        if self.layout_variant == "split":
            self._build_highlights_variant_split(slide, highlights, image_data)
            return
        
        # --- PREMIUM HIGHLIGHTS LAYOUT ---
        
        # --- LEFT: Feature Image (Compact to prevent footer overlap) ---
        image_added = False
        if image_data and image_data.get("path"):
            if draw_image_box(slide, image_data.get("path"), 0.5, 1.2, 3.5, 3.6):
                image_added = True
                logger.info("Added feature image to highlights slide")
        
        # Fallback: colored placeholder if no image
        if not image_added:
            placeholder = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(0.5), Inches(1.2),
                Inches(3.5), Inches(3.6)
            )
            placeholder.fill.solid()
            placeholder.fill.fore_color.rgb = RGBColor(240, 245, 250)
            placeholder.line.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_indigo"]))
            placeholder.line.width = Pt(2)
            
            # Add placeholder text
            placeholder_text = slide.shapes.add_textbox(
                Inches(1.0), Inches(2.7),
                Inches(2.5), Inches(0.8)
            )
            pt_p = placeholder_text.text_frame.paragraphs[0]
            pt_p.text = "Image Placeholder\n(Pharma Industry)"
            pt_p.font.name = KELP_FONT_BODY
            pt_p.font.size = Pt(14)
            pt_p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_dark"]))
            pt_p.alignment = PP_ALIGN.CENTER
                
        # --- RIGHT: Enhanced Highlight Cards (Optimized spacing) ---
        start_y = 1.15
        item_h = 0.95  # Larger cards for 4 highlights
        
        for i, hl in enumerate(highlights[:4]):  # Max 4 highlights
            y = start_y + (i * item_h)
            
            # Highlight Card Background
            card_bg = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(4.2), Inches(y), Inches(5.5), Inches(0.88)
            )
            card_bg.fill.solid()
            if i % 2 == 0:
                card_bg.fill.fore_color.rgb = RGBColor(248, 249, 252)
            else:
                card_bg.fill.fore_color.rgb = RGBColor(255, 255, 255)
            card_bg.line.color.rgb = RGBColor(200, 210, 225)
            card_bg.line.width = Pt(1)
            
            # Icon from Pillow generator
            icon_png = generate_icon_png(hl.title, size=64, icon_index=i)
            if icon_png:
                try:
                    slide.shapes.add_picture(
                        str(icon_png), 
                        Inches(4.35), Inches(y + 0.2), 
                        Inches(0.42), Inches(0.42)
                    )
                except Exception:
                    pass
            else:
                # Fallback: colored circle with letter
                icon_colors = ["gradient_pink", "primary_indigo", "cyan_blue", "gradient_purple"]
                icon_circ = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL, 
                    Inches(4.35), Inches(y + 0.2), 
                    Inches(0.42), Inches(0.42)
                )
                icon_circ.fill.solid()
                icon_circ.fill.fore_color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS[icon_colors[i % 4]]))
                icon_circ.line.fill.background()
                icon_text = slide.shapes.add_textbox(Inches(4.44), Inches(y + 0.26), Inches(0.28), Inches(0.28))
                ip = icon_text.text_frame.paragraphs[0]
                ip.text = (hl.title[:1] if hl.title else "•")
                ip.font.name = KELP_FONT_HEAD
                ip.font.size = Pt(11)
                ip.font.bold = True
                ip.font.color.rgb = RGBColor(255, 255, 255)
                ip.alignment = PP_ALIGN.CENTER
            
            # Text inside card (Title + Description)
            tf_box = slide.shapes.add_textbox(
                Inches(4.9), Inches(y + 0.08), 
                Inches(4.65), Inches(0.75)
            )
            tf = tf_box.text_frame
            tf.word_wrap = True
            tf.margin_left = Inches(0.05)
            tf.margin_right = Inches(0.05)
            tf.margin_top = Inches(0.03)
            tf.vertical_anchor = MSO_ANCHOR.TOP
            
            p = tf.paragraphs[0]
            p.text = hl.title
            p.font.name = KELP_FONT_HEAD
            p.font.size = Pt(9.5)
            p.font.bold = True
            p.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
            p.line_spacing = 1.05
            
            p2 = tf.add_paragraph()
            # Show full description, let word wrap handle it
            p2.text = hl.text
            p2.font.name = KELP_FONT_BODY
            p2.font.size = Pt(7.2)
            p2.font.color.rgb = RGBColor(*self._hex_to_rgb(KELP_COLORS["text_body"]))
            p2.line_spacing = 1.05
            p2.space_before = Pt(3)

    # =========================================================================
    # SLIDE 5: END / DISCLAIMER
    # =========================================================================
    def _build_end_slide(self, content: SlideContent):
        """Build Slide 5: Disclaimer (Matches 'Disclaimer' Screenshot)."""
        layout = self.template.prs.slide_layouts[6] 
        slide = self.template.prs.slides.add_slide(layout)
        
        # Color from Kelp Brand
        KELP_BLUE = RGBColor(*self._hex_to_rgb(KELP_COLORS["primary_dark"]))
        
        # 1. Background (Full Slide)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.63))
        bg.fill.solid()
        bg.fill.fore_color.rgb = KELP_BLUE
        
        # 2. "Kelp" Logo (Top Left)
        logo_path = Path("assets/kelp_logo.png")
        if logo_path.exists():
            try:
                slide.shapes.add_picture(str(logo_path), Inches(0.5), Inches(0.35), height=Inches(0.9))
            except Exception as e:
                logger.warning(f"Could not add logo to disclaimer: {e}")
                # Fallback to text
                kelp_logo_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(2.0), Inches(0.6))
                kelp_p = kelp_logo_box.text_frame.paragraphs[0]
                kelp_p.text = "Kelp"
                kelp_p.font.name = "Arial"
                kelp_p.font.size = Pt(32)
                kelp_p.font.bold = True
                kelp_p.font.color.rgb = RGBColor(255, 255, 255)
        else:
            # Fallback
            kelp_logo_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(2.0), Inches(0.6))
            kelp_p = kelp_logo_box.text_frame.paragraphs[0]
            kelp_p.text = "Kelp"
            kelp_p.font.name = "Arial"
            kelp_p.font.size = Pt(32)
            kelp_p.font.bold = True
            kelp_p.font.color.rgb = RGBColor(255, 255, 255)

        # 3. Title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9.0), Inches(0.8))
        p = title_box.text_frame.paragraphs[0]
        p.text = "Important Notice & Disclaimer"
        p.font.name = "Arial"
        p.font.size = Pt(36)
        p.font.bold = False
        p.font.color.rgb = RGBColor(255, 255, 255)
        
        # 4. Body Text
        body_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.2), Inches(9.0), Inches(2.5))
        tf = body_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ("Strictly Private & Confidential. This presentation is prepared by Kelp Global exclusively "
                  "for the intended recipient and may not be reproduced or distributed without prior written consent. "
                  "This document is for informational purposes only and does not constitute an offer to sell or a solicitation "
                  "of an offer to buy any securities. While all information is obtained from sources believed to be reliable, "
                  "Kelp Global makes no representation or warranty regarding its accuracy or completeness.")
        p.font.name = "Arial"
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.JUSTIFY
        
        # 5. Footer
        fbox = slide.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(9.0), Inches(0.3))
        p = fbox.text_frame.paragraphs[0]
        p.text = "Strictly Private & Confidential – Prepared by Kelp M&A Team"
        p.font.size = Pt(9)
        p.font.color.rgb = RGBColor(200, 200, 200)
        p.alignment = PP_ALIGN.CENTER

        

        



    # Helper for Images
    def _add_image_to_slide(self, slide, image_path: str, left, top, width, height):
        if Path(image_path).exists():
            slide.shapes.add_picture(str(image_path), Inches(left), Inches(top), width=Inches(width), height=Inches(height))
