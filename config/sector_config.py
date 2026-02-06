"""
deckAIn - Sector-Specific Configuration
Defines metrics, KPIs, and presentation logic per industry sector
"""

from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class SectorMetrics:
    """Defines sector-specific metrics and presentation requirements."""
    name: str
    primary_kpis: List[str]  # Must-have metrics for this sector
    optional_kpis: List[str]  # Nice-to-have metrics
    chart_types: List[str]  # Preferred chart visualizations
    certifications: List[str]  # Common certifications for this sector
    key_strengths: List[str]  # What to highlight in investment case
    terminology: Dict[str, str]  # Sector-specific terms

# =============================================================================
# SECTOR DEFINITIONS
# =============================================================================

PHARMA_METRICS = SectorMetrics(
    name="Pharma",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat",
        "rd_spend",
        "facility_count",
        "export_revenue_pct"
    ],
    optional_kpis=[
        "patents_count",
        "api_portfolio_count",
        "product_registrations",
        "clinical_trials",
        "compliance_certifications"
    ],
    chart_types=["revenue_trend", "margin_expansion", "export_mix"],
    certifications=[
        "US FDA",
        "UK MHRA", 
        "WHO GMP",
        "ISO 9001:2015",
        "ISO 14001:2015",
        "FSSC 22000",
        "Halal",
        "Kosher",
        "FSSAI"
    ],
    key_strengths=[
        "FDA approvals and regulatory compliance",
        "API manufacturing capabilities",
        "Export market penetration",
        "R&D pipeline and patent portfolio",
        "Quality certifications (GMP, ISO)"
    ],
    terminology={
        "products": "APIs and formulations",
        "customers": "pharmaceutical companies and healthcare providers",
        "facilities": "WHO-GMP certified manufacturing units",
        "capacity": "production capacity in metric tons",
        "quality": "regulatory compliance and certifications"
    }
)

MANUFACTURING_METRICS = SectorMetrics(
    name="Manufacturing",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat",
        "facility_count",
        "capacity_utilization",
        "employee_count"
    ],
    optional_kpis=[
        "production_capacity",
        "automation_level",
        "quality_metrics",
        "export_revenue_pct",
        "customer_concentration"
    ],
    chart_types=["revenue_trend", "capacity_utilization", "export_domestic_mix"],
    certifications=[
        "ISO 9001:2015",
        "IATF 16949",
        "ISO 14001:2015",
        "ISO 45001",
        "AS9100",
        "NADCAP"
    ],
    key_strengths=[
        "Production capacity and utilization",
        "Automation and Industry 4.0 adoption",
        "Blue-chip customer relationships",
        "Quality certifications (IATF, ISO)",
        "Supply chain integration"
    ],
    terminology={
        "products": "manufactured components and assemblies",
        "customers": "OEMs and tier-1 suppliers",
        "facilities": "manufacturing plants and production units",
        "capacity": "annual production capacity",
        "quality": "quality systems and defect rates"
    }
)

TECHNOLOGY_METRICS = SectorMetrics(
    name="Technology",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat",
        "arr",  # Annual Recurring Revenue
        "employee_count",
        "rd_spend"
    ],
    optional_kpis=[
        "customer_retention_rate",
        "net_revenue_retention",
        "patents_count",
        "cloud_revenue_pct",
        "international_revenue_pct"
    ],
    chart_types=["revenue_growth", "arr_trend", "customer_acquisition"],
    certifications=[
        "ISO 27001",
        "SOC 2 Type II",
        "GDPR Compliant",
        "ISO 9001:2015",
        "CMMI Level 5"
    ],
    key_strengths=[
        "Recurring revenue model (SaaS/ARR)",
        "Technology IP and patents",
        "Customer retention and NRR",
        "R&D capabilities and innovation",
        "Scalability and cloud infrastructure"
    ],
    terminology={
        "products": "software solutions and technology platforms",
        "customers": "enterprise clients and end-users",
        "facilities": "development centers and data centers",
        "capacity": "user capacity and transaction volume",
        "quality": "uptime, security, and performance metrics"
    }
)

SERVICES_METRICS = SectorMetrics(
    name="Services",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat"
    ],
    optional_kpis=[
        "employee_count",
        "client_count",
        "revenue_per_employee",
        "customer_retention_rate",
        "project_delivery_success_rate",
        "international_revenue_pct",
        "top_client_concentration"
    ],
    chart_types=["revenue_trend", "client_growth", "margin_trend"],
    certifications=[
        "ISO 9001:2015",
        "ISO 27001",
        "CMMI Level 5",
        "Six Sigma",
        "PMP"
    ],
    key_strengths=[
        "Domain expertise and client relationships",
        "Employee skill levels and retention",
        "Project delivery track record",
        "Geographic diversification",
        "Scalability of service model"
    ],
    terminology={
        "products": "service offerings and solutions",
        "customers": "clients across industries",
        "facilities": "delivery centers and offices",
        "capacity": "headcount and utilization rate",
        "quality": "client satisfaction and delivery excellence"
    }
)

LOGISTICS_METRICS = SectorMetrics(
    name="Logistics",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat",
        "fleet_size",
        "ton_km",
        "utilization",
        "hub_count"
    ],
    optional_kpis=[
        "on_time_delivery",
        "warehouse_area",
        "export_revenue_pct",
        "customer_concentration"
    ],
    chart_types=["revenue_trend", "utilization", "fleet_growth"],
    certifications=[
        "ISO 9001:2015",
        "ISO 14001:2015",
        "AEO",
        "GDP"
    ],
    key_strengths=[
        "Network density and route optimization",
        "High utilization and asset turnover",
        "Sticky enterprise contracts",
        "Tech-enabled visibility and tracking"
    ],
    terminology={
        "products": "logistics services and warehousing",
        "customers": "enterprise shippers and marketplaces",
        "facilities": "hubs, depots, and warehouses",
        "capacity": "fleet size and ton-km",
        "quality": "on-time delivery and damage rates"
    }
)

HEALTHCARE_METRICS = SectorMetrics(
    name="Healthcare",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat",
        "bed_count",
        "occupancy_rate",
        "arpo_b",
        "payer_mix"
    ],
    optional_kpis=[
        "specialty_mix",
        "procedure_volume",
        "nabh_accreditation"
    ],
    chart_types=["revenue_trend", "occupancy", "margin_trend"],
    certifications=[
        "NABH",
        "NABL",
        "JCI",
        "ISO 9001:2015"
    ],
    key_strengths=[
        "High occupancy and case mix",
        "Clinical outcomes and reputation",
        "Expansion of specialty services",
        "Strong insurer relationships"
    ],
    terminology={
        "products": "clinical services and specialties",
        "customers": "patients and payers",
        "facilities": "hospitals and clinics",
        "capacity": "beds and occupancy",
        "quality": "clinical outcomes and accreditation"
    }
)

CONSUMER_METRICS = SectorMetrics(
    name="Consumer",
    primary_kpis=[
        "revenue",
        "ebitda",
        "pat",
        "cac",
        "ltv",
        "repeat_rate",
        "aov"
    ],
    optional_kpis=[
        "channel_mix",
        "digital_traffic",
        "gross_margin"
    ],
    chart_types=["revenue_trend", "cohort_retention", "channel_mix"],
    certifications=[
        "FSSAI",
        "GMP",
        "ISO 22000",
        "ISO 9001:2015"
    ],
    key_strengths=[
        "Brand strength and customer loyalty",
        "Scalable digital acquisition",
        "Product innovation and portfolio depth",
        "Omni-channel growth"
    ],
    terminology={
        "products": "SKUs and product lines",
        "customers": "end consumers and repeat buyers",
        "facilities": "fulfillment centers and warehouses",
        "capacity": "orders per day and throughput",
        "quality": "customer ratings and repeat rate"
    }
)

# Sector registry
SECTOR_REGISTRY: Dict[str, SectorMetrics] = {
    "Pharma": PHARMA_METRICS,
    "Manufacturing": MANUFACTURING_METRICS,
    "Technology": TECHNOLOGY_METRICS,
    "Services": SERVICES_METRICS,
    "Logistics": LOGISTICS_METRICS,
    "Healthcare": HEALTHCARE_METRICS,
    "Consumer": CONSUMER_METRICS
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_sector_config(sector: str) -> SectorMetrics:
    """
    Get sector-specific configuration.
    
    Args:
        sector: Sector name (case-insensitive)
    
    Returns:
        SectorMetrics configuration
    
    Raises:
        ValueError: If sector not found
    """
    # Case-insensitive lookup
    for key, config in SECTOR_REGISTRY.items():
        if key.lower() == sector.lower():
            return config
    
    # Default fallback
    raise ValueError(
        f"Unknown sector: {sector}. "
        f"Valid sectors: {', '.join(SECTOR_REGISTRY.keys())}"
    )

def get_required_kpis(sector: str) -> Set[str]:
    """Get list of required KPIs for a sector."""
    config = get_sector_config(sector)
    return set(config.primary_kpis)

def get_sector_certifications(sector: str) -> List[str]:
    """Get common certifications for a sector."""
    config = get_sector_config(sector)
    return config.certifications

def get_sector_terminology(sector: str, term: str) -> str:
    """
    Get sector-specific terminology.
    
    Args:
        sector: Sector name
        term: Term to translate (e.g., 'products', 'customers')
    
    Returns:
        Sector-specific term or original if not found
    """
    config = get_sector_config(sector)
    return config.terminology.get(term, term)

def validate_sector_metrics(sector: str, available_metrics: Set[str]) -> Dict[str, any]:
    """
    Validate that required sector metrics are present.
    
    Args:
        sector: Sector name
        available_metrics: Set of metric names present in data
    
    Returns:
        Dict with validation results
    """
    config = get_sector_config(sector)
    required = set(config.primary_kpis)
    available = set(available_metrics)
    
    missing = required - available
    present = required & available
    coverage = len(present) / len(required) if required else 1.0
    
    return {
        "sector": sector,
        "required_kpis": list(required),
        "present_kpis": list(present),
        "missing_kpis": list(missing),
        "coverage_pct": coverage * 100,
        "is_compliant": coverage >= 0.6  # At least 60% of required metrics
    }
