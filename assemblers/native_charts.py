"""
deckAIn - Native Charts Creator
Create editable PPTX charts using python-pptx (NO matplotlib)
"""

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_MARK
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from extractors.schemas import ChartSpec
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NativeChartsCreator:
    """
    Create native editable charts in PPTX with premium styling.
    CRITICAL: These are real Excel-backed charts, not images.
    """
    
    def __init__(self):
        """Initialize native charts creator."""
        logger.info("NativeChartsCreator initialized")
    
    def add_chart_to_slide(
        self,
        slide,
        chart_spec: ChartSpec,
        x: float = 1.0,
        y: float = 2.0,
        width: float = 8.0,
        height: float = 4.5
    ):
        """
        Add a native chart to a slide with premium styling.
        """
        logger.debug(f"Adding {chart_spec.chart_type} chart to slide")
        
        # Prepare chart data
        chart_data = CategoryChartData()
        chart_data.categories = chart_spec.categories
        
        # Add all series
        for series in chart_spec.series:
            # Defensive: skip empty series or filter out None
            clean_values = [v if v is not None else 0 for v in series.values]
            if not any(clean_values):
                logger.warning(f"Skipping series '{series.name}' - all values zero or None")
                continue
            chart_data.add_series(series.name, clean_values)
        
        # Determine chart type
        chart_type_map = {
            "COLUMN_CLUSTERED": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "LINE": XL_CHART_TYPE.LINE,
            "BAR_CLUSTERED": XL_CHART_TYPE.BAR_CLUSTERED,
            "PIE": XL_CHART_TYPE.PIE
        }
        
        chart_type = chart_type_map.get(chart_spec.chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED)
        
        # Add chart to slide
        x_pos, y_pos = Inches(x), Inches(y)
        cx, cy = Inches(width), Inches(height)
        
        try:
            graphic_frame = slide.shapes.add_chart(
                chart_type,
                x_pos, y_pos, cx, cy,
                chart_data
            )
            chart = graphic_frame.chart
            
            # apply global style
            self._style_chart(chart, chart_spec)
        except Exception as e:
            logger.error(f"Failed to add chart to slide: {e}")
            return None
        
        logger.info(f"Added native {chart_spec.chart_type} chart")
        
        return chart
    
    def _style_chart(self, chart, chart_spec: ChartSpec):
        """
        Apply premium styling to chart (fonts, colors, number formats).
        """
        # Set font for entire chart area first (defaults)
        try:
            chart.font.name = 'Arial'
            chart.font.size = Pt(9)
            chart.font.color.rgb = RGBColor(74, 85, 104)  # Slate grey
        except:
            pass
        
        # Legend styling
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False  # Prevent chart shrinking
        chart.legend.font.size = Pt(9)

        # ---------------------------
        # Axis Styling
        # ---------------------------
        try:
            # Value Axis (Y-axis for Column/Line)
            val_axis = chart.value_axis
            val_axis.has_major_gridlines = True
            val_axis.major_gridlines.format.line.width = Pt(0.5)
            val_axis.major_gridlines.format.line.color.rgb = RGBColor(226, 232, 240)  # faint grey
            
            val_axis.has_minor_gridlines = False
            val_axis.tick_labels.font.size = Pt(8)
            val_axis.tick_labels.font.color.rgb = RGBColor(100, 116, 139)
            
            # Format numbers to be concise (e.g. 2k)
            # "0" = integer, "0.0" = 1 decimal, "#,##0" = standard
            # We want to avoid huge numbers.
             # Setting number format is tricky via python-pptx directly for all cases, 
            # but general format usually works.
            val_axis.tick_labels.number_format = '#,##0' 
            
            # Category Axis (X-axis for Column/Line)
            cat_axis = chart.category_axis
            cat_axis.tick_labels.font.size = Pt(8)
            cat_axis.tick_labels.font.bold = False
            cat_axis.has_major_gridlines = False
            cat_axis.major_tick_mark = XL_TICK_MARK.NONE
            
        except Exception as e:
            logger.debug(f"Axis styling partial failure: {e}")

        # ---------------------------
        # Data Labels
        # ---------------------------
        if chart_spec.data_labels:
            plot = chart.plots[0]
            plot.has_data_labels = True
            
            # Apply to collection
            dls = plot.data_labels
            dls.font.size = Pt(8)
            dls.font.bold = True
            dls.font.color.rgb = RGBColor(51, 65, 85) # Dark slate
            dls.position = None # Let PowerPoint decide best placement
            
            # Try specific number format for labels if possible
            try:
                dls.number_format = '#,##0'
            except:
                pass
        
        # ---------------------------
        # Series Colors & Widths
        # ---------------------------
        for idx, series_spec in enumerate(chart_spec.series):
            if idx < len(chart.series):
                series = chart.series[idx]
                
                # Colors
                hex_color = series_spec.color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                
                series.format.fill.solid()
                series.format.fill.fore_color.rgb = RGBColor(*rgb)
                
                # If Line chart, smooth line and add markers
                if chart_spec.chart_type == "LINE":
                    series.format.line.width = Pt(2.5)
                    series.format.line.color.rgb = RGBColor(*rgb)
                    series.smooth = True  # Smooth curve
                
                # Gap width for column charts (make bars fatter)
                if chart_spec.chart_type == "COLUMN_CLUSTERED":
                    try:
                        chart.plots[0].gap_width = 150 # 150% gap width is standard/clean
                    except:
                        pass
        
        # ---------------------------
        # Titles (Remove if redundant to save space)
        # ---------------------------
        if chart.value_axis:
            chart.value_axis.has_title = False # Save space
        if chart.category_axis:
            chart.category_axis.has_title = False # Save space

        logger.debug("Premium chart styling applied")
