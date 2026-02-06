"""
deckAIn - Data Schemas
Pydantic models for validation and type safety
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

# =============================================================================
# STAGE 1: EXTRACTION SCHEMAS
# =============================================================================

class SourceMetadata(BaseModel):
    """Metadata about data source for citations."""
    table_name: str = Field(..., description="Name of source table")
    row_numbers: List[Union[int, str]] = Field(default_factory=list, description="Row indices or section names in source")
    source_file: str = Field(..., description="Source file path")
    extraction_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class FinancialData(BaseModel):
    """
    Flexible financial data schema - adapts to whatever data is available.
    NOT all fields are required - extract what exists!
    """
    
    # Core Income Statement (prefer these if available)
    revenue_by_year: Optional[List[float]] = Field(None, description="Revenue in ₹ Crores")
    ebitda_by_year: Optional[List[float]] = Field(None, description="EBITDA in ₹ Crores")
    pat_by_year: Optional[List[float]] = Field(None, description="PAT/Net Profit in ₹ Crores")
    years: Optional[List[str]] = Field(None, description="Fiscal years (FY23, FY24, etc.)")
    
    # Alternative P&L metrics (if EBITDA not available)
    operating_profit_by_year: Optional[List[float]] = Field(None, description="Operating profit")
    gross_profit_by_year: Optional[List[float]] = Field(None, description="Gross profit")
    
    # Balance Sheet
    total_assets: Optional[float] = Field(None, description="Total assets in ₹ Crores")
    total_debt: Optional[float] = Field(None, description="Total debt in ₹ Crores")
    total_equity: Optional[float] = Field(None, description="Total equity in ₹ Crores")
    
    # Operational Metrics (sector-agnostic)
    employee_count: Optional[int] = Field(None, description="Number of employees")
    facility_count: Optional[int] = Field(None, description="Number of facilities")
    export_revenue_pct: Optional[float] = Field(None, description="Export revenue percentage")
    
    # Sector-specific metrics (extracted if found - flexible!)
    additional_metrics: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Any other sector-specific metrics (R&D spend, capacity utilization, etc.)"
    )
    
    # Calculated Metrics (will be computed by Python, not LLM)
    revenue_cagr: Optional[float] = Field(None, description="Revenue CAGR %")
    ebitda_margin_latest: Optional[float] = Field(None, description="Latest EBITDA margin %")
    ebitda_margin_avg: Optional[float] = Field(None, description="Average EBITDA margin %")
    
    # Source tracking
    source_metadata: Optional[SourceMetadata] = None
    
    @validator('years')
    def validate_years_format(cls, v):
        """Ensure years are in correct format."""
        for year in v:
            if not (year.startswith("FY") or year.startswith("FY20") or year.startswith("FY21")):
                raise ValueError(f"Invalid year format: {year}. Expected FY23, FY24, etc.")
        return v
    
    @validator('export_revenue_pct')
    def validate_export_percentage(cls, v):
        """Ensure export percentage is valid (0-100)."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError(f"Percentage must be between 0 and 100, got {v}")
        return v
        
    @validator('ebitda_margin_latest', 'ebitda_margin_avg')
    def validate_margin_percentages(cls, v):
        """Ensure margins are realistic (-100 to 100)."""
        if v is not None and (v < -100 or v > 100):
             # Allow negative margins, but cap at realistic bounds
            raise ValueError(f"Margin must be between -100 and 100, got {v}")
        return v

class PublicDataSource(BaseModel):
    """Single public data source with citation info."""
    snippet: str = Field(..., description="Text snippet")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Article/page title")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class PublicMarketData(BaseModel):
    """Public market context from web sources."""
    market_size_data: List[PublicDataSource] = Field(default_factory=list)
    industry_trends: List[PublicDataSource] = Field(default_factory=list)
    competitive_landscape: List[PublicDataSource] = Field(default_factory=list)
    recent_news: List[PublicDataSource] = Field(default_factory=list)
    
    def get_all_sources(self) -> List[PublicDataSource]:
        """Get all sources for citation document."""
        return (
            self.market_size_data +
            self.industry_trends +
            self.competitive_landscape +
            self.recent_news
        )

# =============================================================================
# STAGE 2: CHART DATA SCHEMAS
# =============================================================================

class ChartSeries(BaseModel):
    """Single data series for a chart."""
    name: str = Field(..., description="Series name (e.g., 'Revenue')")
    values: List[float] = Field(..., description="Data values")
    color: str = Field(..., description="Hex color code")
    
    @validator('color')
    def validate_hex_color(cls, v):
        """Ensure color is valid hex."""
        if not v.startswith('#') or len(v) != 7:
            raise ValueError(f"Color must be hex format #RRGGBB, got {v}")
        return v

class ChartSpec(BaseModel):
    """Specification for a native PPTX chart."""
    chart_type: str = Field(..., description="Chart type (COLUMN_CLUSTERED, etc.)")
    categories: List[str] = Field(..., description="X-axis categories")
    series: List[ChartSeries] = Field(..., description="Data series")
    data_labels: bool = Field(True, description="Show data labels")
    legend_position: str = Field("BOTTOM", description="Legend position")
    y_axis_title: str = Field("", description="Y-axis title")
    x_axis_title: str = Field("", description="X-axis title")

# =============================================================================
# STAGE 3: CONTENT SCHEMAS
# =============================================================================

class BusinessOverview(BaseModel):
    """Structured content for Business Profile slide."""
    main_text: str = Field(..., description="High-level summary paragraph")
    key_customers: List[str] = Field(..., description="List of 3-5 key customers")
    product_categories: List[str] = Field(..., description="List of 4-6 product groups")
    
    # New Smart Components
    timeline_events: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="Key history events [{'year': '2010', 'event': 'Founded'}, ...]"
    )
    key_stats: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Key statistics [{'label': 'Employees', 'value': '500+'}, ...]"
    )
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    operational_highlights: List[str] = Field(default_factory=list, description="Key facts")

class InvestmentHighlight(BaseModel):
    """Single investment highlight point."""
    icon: str = Field(..., description="Icon name (trophy, factory, globe, chart_up, shield)")
    title: str = Field(..., description="Highlight title (3-5 words)")
    text: str = Field(..., description="Highlight description (30-50 words)")
    
    @validator('icon')
    def validate_icon(cls, v):
        """Ensure icon is from allowed list."""
        allowed = [
            "trophy", "factory", "globe", "chart_up", "shield", 
            "lightbulb", "users", "award", "target", "star",
            "gear", "rocket", "diamond", "briefcase", "handshake"
        ]
        if v not in allowed:
            raise ValueError(f"Icon must be one of {allowed}, got {v}")
        return v

class SlideContent(BaseModel):
    """Complete slide content for the presentation."""
    company_codename: Optional[str] = Field("Project Velocity", description="Anonymized project name")
    slide_2_business_overview: Optional[BusinessOverview] = Field(None)
    slide_3_growth_narrative: Optional[str] = Field("Growth narrative unavailable due to data limitations.", description="Growth story")
    slide_4_investment_highlights: Optional[List[InvestmentHighlight]] = Field(default_factory=list, description="Highlights")
    anonymization_map: Optional[Dict[str, str]] = Field(default_factory=dict, description="Mapping")
    
    @validator('company_codename')
    def validate_codename(cls, v):
        """Ensure codename starts with 'Project'."""
        if not v.startswith("Project "):
            raise ValueError("Codename must start with 'Project '")
        return v

# =============================================================================
# STAGE 4: CITATION SCHEMAS
# =============================================================================

class Citation(BaseModel):
    """Single citation entry."""
    claim: str = Field(..., description="The claim or data point")
    value: Optional[Any] = Field(None, description="Numeric value if applicable")
    source_type: str = Field(..., description="'private_document' or 'public_web'")
    source_details: Dict[str, Any] = Field(..., description="File path / URL / etc.")
    
    @validator('source_type')
    def validate_source_type(cls, v):
        """Ensure source type is valid."""
        if v not in ["private_document", "public_web"]:
            raise ValueError("source_type must be 'private_document' or 'public_web'")
        return v

# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class ComplianceCheckResult(BaseModel):
    """Result of a compliance check."""
    check_name: str
    passed: bool
    details: str = ""
    severity: str = "info"  # info, warning, critical
    
    @validator('severity')
    def validate_severity(cls, v):
        """Ensure severity is valid."""
        if v not in ["info", "warning", "critical"]:
            raise ValueError("severity must be info/warning/critical")
        return v

class ComplianceReport(BaseModel):
    """Overall compliance validation report."""
    checks: List[ComplianceCheckResult] = Field(default_factory=list)
    overall_score: float = Field(0.0, description="Percentage score")
    passed: bool = Field(False, description="Whether all critical checks passed")
    
    def add_check(self, name: str, passed: bool, details: str = "", severity: str = "info"):
        """Add a compliance check result."""
        self.checks.append(ComplianceCheckResult(
            check_name=name,
            passed=passed,
            details=details,
            severity=severity
        ))
    
    def calculate_score(self):
        """Calculate overall compliance score."""
        if not self.checks:
            self.overall_score = 0.0
            self.passed = False
            return
        
        # Critical checks must all pass
        critical_checks = [c for c in self.checks if c.severity == "critical"]
        if any(not c.passed for c in critical_checks):
            self.passed = False
            self.overall_score = 0.0
            return
        
        # Calculate percentage
        passed_count = sum(1 for c in self.checks if c.passed)
        self.overall_score = (passed_count / len(self.checks)) * 100
        self.passed = self.overall_score >= 80  # Need 80%+ to pass
