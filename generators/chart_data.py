"""
deckAIn - Chart Data Generator
Stage 2: Prepare chart specifications for native PPTX charts
NO matplotlib - only data structures for python-pptx
"""

from typing import Dict, List, Optional
from extractors.schemas import FinancialData, ChartSpec, ChartSeries
from config.settings import KELP_COLORS
from config.sector_config import get_sector_config
from utils.logger import setup_logger, log_stage

logger = setup_logger(__name__)

class ChartDataGenerator:
    """
    Prepare chart data specifications for native PPTX charts.
    NO image generation - just JSON structures.
    """
    
    def __init__(self):
        """Initialize chart generator."""
        logger.info("ChartDataGenerator initialized")
    
    def generate_chart_specs(self, financial_data: FinancialData, sector: str = None) -> Dict[str, ChartSpec]:
        """
        Generate chart specifications from financial data.
        
        Args:
            financial_data: Validated financial data
            sector: Business sector for sector-specific chart selection
        
        Returns:
            Dictionary of chart specifications
        """
        log_stage(logger, 2, "Chart Data Preparation", "START")
        
        # Get sector-specific preferences
        if sector:
            try:
                sector_config = get_sector_config(sector)
                logger.info(f"Using sector-specific chart configuration for {sector}")
                preferred_charts = sector_config.chart_types
            except ValueError:
                logger.warning(f"Unknown sector {sector}, using default charts")
                preferred_charts = ["revenue_trend", "margin_expansion"]
        else:
            preferred_charts = ["revenue_trend", "margin_expansion"]
        
        chart_specs = {}
        
        # Chart 1: Revenue, EBITDA, PAT trend (clustered columns)
        # Using _create_financial_chart (renamed from trends) and handling None
        fin_chart = self._create_financial_chart(financial_data)
        if fin_chart:
            chart_specs["financial_trends"] = fin_chart
            logger.info(" Created financial trends chart spec")
        else:
            logger.warning(" Skipped financial trends chart (insufficient data)")
            
        # Chart 2: Margin Evolution
        if (financial_data.years and 
            financial_data.revenue_by_year and 
            financial_data.ebitda_by_year and
            len(financial_data.revenue_by_year) >= 3):
            
            margin_chart = self._create_margin_chart(financial_data)
            if margin_chart:
                chart_specs["margin_evolution"] = margin_chart
                logger.info(" Created margin evolution chart spec")
        else:
            logger.warning(" Insufficient data for margin evolution chart")
        
        log_stage(logger, 2, "Chart Data Preparation", "DONE")
        logger.info(f"Generated {len(chart_specs)} chart specifications")
        
        return chart_specs
 
    def _create_financial_chart(self, data: FinancialData) -> Optional[ChartSpec]:
        """
        Create specification for revenue/EBITDA/PAT chart.
        """
        # Nil-check: If years or data is missing, we can't build a chart
        if not data.years or not data.revenue_by_year:
            logger.warning("Insufficient data for financial trends chart")
            return None
            
        # --- DATA SLICING (Premium Fix) ---
        # Limit to last 7 years max to prevent overcrowding
        MAX_YEARS = 7
        years = data.years
        rev = data.revenue_by_year
        ebitda = data.ebitda_by_year
        pat = data.pat_by_year
        
        if len(years) > MAX_YEARS:
            # Take the LAST N years (assuming sorted chronological)
            years = years[-MAX_YEARS:]
            rev = rev[-MAX_YEARS:] if rev else []
            ebitda = ebitda[-MAX_YEARS:] if ebitda else []
            pat = pat[-MAX_YEARS:] if pat else []
            logger.info(f"Sliced financial data to last {MAX_YEARS} years for readability")

        series = []
        
        # 1. Revenue (Columns) - Blue
        if rev:
             series.append(ChartSeries(
                 name="Revenue ($Mn)",
                 values=rev,
                 color=KELP_COLORS["primary_dark"] # Dark Blue
             ))
        
        # 2. EBITDA (Columns? Or Line?) - Usually Revenue + EBITDA are clustered columns
        if ebitda:
            series.append(ChartSeries(
                name="EBITDA ($Mn)",
                values=ebitda,
                color=KELP_COLORS["cyan_blue"] # Cyan
            ))
            
        # 3. PAT (Columns) - Purple
        if pat:
            series.append(ChartSeries(
                name="PAT ($Mn)",
                values=pat,
                color=KELP_COLORS["gradient_pink"] # Pink
            ))
            
        if not series:
            return None
            
        chart_spec = ChartSpec(
            chart_type="COLUMN_CLUSTERED",
            categories=years,
            series=series,
            data_labels=True,
            legend_position="BOTTOM",
            y_axis_title="Amount ($Mn)",
            x_axis_title="Fiscal Year"
        )
        
        logger.debug(f"Financial trends chart: {len(series)} series, {len(years)} periods")
        
        return chart_spec
 
    def _create_margin_chart(self, data: FinancialData) -> Optional[ChartSpec]:
        """
        Create specification for EBITDA margin evolution chart.
        """
        # Nil-check
        if not data.years or not data.revenue_by_year or not data.ebitda_by_year:
            logger.warning("Insufficient data for margin chart")
            return None

        # Calculate margins for each year
        margins = []
        for rev, ebitda in zip(data.revenue_by_year, data.ebitda_by_year):
            if rev > 0:
                margin = (ebitda / rev) * 100
                margins.append(round(margin, 1))
            else:
                margins.append(0)
        
        series = [
            ChartSeries(
                name="EBITDA Margin %",
                values=margins,
                color=KELP_COLORS["gradient_pink"] # Pink
            )
        ]
        
        chart_spec = ChartSpec(
            chart_type="LINE",
            categories=data.years,
            series=series,
            data_labels=True,
            legend_position="BOTTOM",
            y_axis_title="Margin %",
            x_axis_title="Fiscal Year"
        )
        
        logger.debug(f"Margin chart: {len(margins)} data points")
        
        return chart_spec
