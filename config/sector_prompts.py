"""
deckAIn - Sector-Specific Prompt Enhancements
Provides sector-specific guidance for LLM content generation
"""

def get_sector_guidance(sector: str) -> str:
    """
    Get sector-specific prompt guidance to append to content generation prompts.
    
    Args:
        sector: Business sector name
    
    Returns:
        Formatted guidance text for LLM prompts
    """
    
    sector_guides = {
        "Pharma": """
SECTOR-SPECIFIC REQUIREMENTS (PHARMACEUTICAL):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - FDA/MHRA/WHO-GMP approvals and certifications
  - API (Active Pharmaceutical Ingredient) portfolio
  - Export markets and regulatory clearances
  - R&D spending and patent portfolio
  - Manufacturing capacity (in metric tons)
  - Product registrations across countries

✓ CERTIFICATIONS TO EMPHASIZE:
  - US FDA, UK MHRA, WHO-GMP, TGA Australia
  - ISO 9001:2015, ISO 14001:2015
  - FSSC 22000, Halal, Kosher, FSSAI

✓ KEY INVESTMENT THEMES:
  - Regulatory moat (FDA approvals are barriers to entry)
  - Export-driven growth (high-margin international markets)
  - API backward integration (cost advantage)
  - Product pipeline and therapeutic areas
  - Quality systems and zero-defect track record

✓ TERMINOLOGY:
  - Products → APIs, formulations, dosage forms
  - Customers → Pharmaceutical companies, hospitals, distributors
  - Facilities → WHO-GMP certified manufacturing units
  - Capacity → Production in metric tons per annum
""",

        "Manufacturing": """
SECTOR-SPECIFIC REQUIREMENTS (MANUFACTURING):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - Production capacity and utilization rates
  - Number of manufacturing facilities
  - Automation level and Industry 4.0 adoption
  - Quality metrics (PPM, rejection rates)
  - OEM customer relationships
  - Export vs domestic revenue mix

✓ CERTIFICATIONS TO EMPHASIZE:
  - IATF 16949 (automotive quality)
  - ISO 9001:2015, ISO 14001, ISO 45001
  - AS9100 (aerospace), NADCAP (special processes)

✓ KEY INVESTMENT THEMES:
  - Capacity utilization and scalability
  - Blue-chip OEM customer base (switching costs)
  - Precision engineering and quality systems
  - Supply chain integration (JIT, vendor consolidation)
  - Import substitution and localization trends

✓ TERMINOLOGY:
  - Products → Components, assemblies, sub-systems
  - Customers → OEMs, Tier-1 suppliers
  - Facilities → Manufacturing plants, production units
  - Capacity → Annual production capacity, utilization %
""",

        "Technology": """
SECTOR-SPECIFIC REQUIREMENTS (TECHNOLOGY):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - ARR (Annual Recurring Revenue) and growth rate
  - Customer retention rate and NRR
  - R&D spending as % of revenue
  - Cloud/SaaS revenue percentage
  - Patents and technology IP
  - Employee skill levels (engineers, data scientists)

✓ CERTIFICATIONS TO EMPHASIZE:
  - ISO 27001 (information security)
  - SOC 2 Type II, GDPR compliance
  - CMMI Level 5, ISO 9001:2015

✓ KEY INVESTMENT THEMES:
  - Recurring revenue model (SaaS economics)
  - Technology IP and patents
  - Customer retention and land-and-expand
  - Scalability (low marginal cost)
  - R&D pipeline and innovation

✓ TERMINOLOGY:
  - Products → Software platforms, SaaS solutions, APIs
  - Customers → Enterprise clients, end-users, subscribers
  - Facilities → Development centers, cloud infrastructure
  - Capacity → User capacity, transaction throughput
""",

        "Services": """
SECTOR-SPECIFIC REQUIREMENTS (SERVICES):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - Revenue per employee
  - Client count and retention rate
  - Employee count and skill levels
  - Project delivery success rate
  - Geographic diversification
  - Top client concentration

✓ CERTIFICATIONS TO EMPHASIZE:
  - ISO 9001:2015, ISO 27001
  - CMMI Level 5, Six Sigma
  - PMP, industry-specific accreditations

✓ KEY INVESTMENT THEMES:
  - Domain expertise and client relationships
  - Employee retention and skill development
  - Project delivery track record
  - Repeat business and upselling
  - Scalability of service model

✓ TERMINOLOGY:
  - Products → Service offerings, consulting solutions
  - Customers → Clients across industries
  - Facilities → Delivery centers, offices
  - Capacity → Headcount, utilization rate
"""
        ,

        "Logistics": """
SECTOR-SPECIFIC REQUIREMENTS (LOGISTICS):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - Fleet size and utilization
  - Ton-km or shipment volume
  - Hub and warehouse count
  - On-time delivery (OTIF)
  - Export/import mix

✓ CERTIFICATIONS TO EMPHASIZE:
  - ISO 9001:2015, ISO 14001:2015
  - AEO (Authorized Economic Operator)
  - GDP (Good Distribution Practices) where relevant

✓ KEY INVESTMENT THEMES:
  - Network density and route optimization
  - High utilization and asset turnover
  - Sticky enterprise contracts
  - Tech-enabled visibility and tracking

✓ TERMINOLOGY:
  - Products → Logistics services, warehousing, last-mile
  - Customers → Shippers, enterprise clients, marketplaces
  - Facilities → Hubs, depots, warehouses
  - Capacity → Fleet size, ton-km, storage area
""",

        "Healthcare": """
SECTOR-SPECIFIC REQUIREMENTS (HEALTHCARE):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - Bed count and occupancy
  - ARPOB/ARPU and payer mix
  - Specialty mix and procedure volumes
  - Accreditation and compliance

✓ CERTIFICATIONS TO EMPHASIZE:
  - NABH, NABL, JCI
  - ISO 9001:2015

✓ KEY INVESTMENT THEMES:
  - High occupancy and case mix
  - Clinical outcomes and reputation
  - Expansion of specialty services
  - Strong insurer relationships

✓ TERMINOLOGY:
  - Products → Clinical services, specialties
  - Customers → Patients, payers, insurers
  - Facilities → Hospitals, clinics
  - Capacity → Beds, ICU beds, occupancy
""",

        "Consumer": """
SECTOR-SPECIFIC REQUIREMENTS (CONSUMER/D2C):
✓ PRIMARY METRICS TO HIGHLIGHT:
  - CAC, LTV, repeat rate
  - AOV and basket size
  - Channel mix and digital traffic
  - Gross margin and contribution margin

✓ CERTIFICATIONS TO EMPHASIZE:
  - FSSAI, GMP, ISO 22000 (for food)
  - ISO 9001:2015

✓ KEY INVESTMENT THEMES:
  - Brand strength and customer loyalty
  - Scalability of digital acquisition
  - Product innovation and portfolio depth
  - Omni-channel growth

✓ TERMINOLOGY:
  - Products → SKUs, product lines
  - Customers → End consumers, repeat buyers
  - Facilities → Fulfillment centers, warehouses
  - Capacity → Orders per day, fulfillment throughput
"""
    }
    
    return sector_guides.get(sector, "")


def get_sector_examples(sector: str) -> str:
    """
    Get sector-specific examples for better content generation.
    
    Args:
        sector: Business sector name
    
    Returns:
        Example content for the sector
    """
    
    examples = {
        "Pharma": """
PHARMA EXAMPLE (Good Business Overview):
"The Company is a leading pharmaceutical manufacturer specializing in Active Pharmaceutical Ingredients (APIs) and formulations across cardiovascular, anti-diabetic, and pain management segments. It operates 3 WHO-GMP certified manufacturing facilities across Western and Southern India with 850+ employees, serving pharmaceutical companies and hospitals across 25+ countries. Core capabilities include API synthesis, sterile injectable manufacturing, and regulatory compliance with US FDA, UK MHRA, and TGA Australia approvals."

PHARMA EXAMPLE (Good Key Stats):
- Employees: 850+
- WHO-GMP Facilities: 3
- Export Revenue: 65%
- FDA-Approved Products: 12
""",

        "Manufacturing": """
MANUFACTURING EXAMPLE (Good Business Overview):
"The Company is a precision forging and machining specialist serving the automotive and industrial equipment sectors. It operates 5 IATF 16949-certified manufacturing facilities across North and West India with 1,200+ employees, supplying tier-1 components to leading domestic and global OEMs. Core capabilities include hot/cold forging, CNC machining, and heat treatment with Industry 4.0 automation integration."

MANUFACTURING EXAMPLE (Good Key Stats):
- Employees: 1,200+
- Manufacturing Units: 5
- Capacity Utilization: 82%
- Export Revenue: 40%
""",

        "Technology": """
TECHNOLOGY EXAMPLE (Good Business Overview):
"The Company is an enterprise software provider specializing in cloud-based supply chain management and logistics optimization platforms. With 500+ software engineers across 3 development centers, it serves Fortune 500 clients in retail, FMCG, and e-commerce sectors globally. Core capabilities include AI/ML-driven route optimization, real-time tracking, and predictive analytics on a microservices-based SaaS architecture."

TECHNOLOGY EXAMPLE (Good Key Stats):
- Engineers: 500+
- ARR: $12M
- Customer Retention: 95%
- Cloud Revenue: 80%
""",

        "Services": """
SERVICES EXAMPLE (Good Business Overview):
"The Company is a specialized consulting firm providing supply chain transformation and operations excellence services to manufacturing and retail clients. With 400+ consultants across 6 delivery centers in India and Southeast Asia, it serves multinational corporations and mid-market enterprises. Core capabilities include process re-engineering, digital transformation, and Lean Six Sigma implementation with proven client ROI of 15-30%."

SERVICES EXAMPLE (Good Key Stats):
- Consultants: 400+
- Client Retention: 92%
- Revenue per Employee: $80K
- Repeat Business: 75%
"""
  ,

  "Logistics": """
LOGISTICS EXAMPLE (Good Business Overview):
"The Company is an integrated logistics provider with pan-India coverage across road transport and warehousing. It operates a fleet of 1,200+ vehicles and 80+ hubs/depots, serving enterprise clients across retail, automotive, and industrial segments. Core capabilities include multimodal transportation, last-mile delivery, and tech-enabled tracking with high on-time performance."

LOGISTICS EXAMPLE (Good Key Stats):
- Fleet Size: 1,200+
- Hubs/Depots: 80+
- Utilization: 85%
- On-time Delivery: 95%
""",

  "Healthcare": """
HEALTHCARE EXAMPLE (Good Business Overview):
"The Company is a multi-specialty hospital chain with a strong presence in cardiac, oncology, and orthopedics. It operates 450 beds across 4 hospitals with 70% average occupancy, serving insured and self-pay patients. Core capabilities include advanced diagnostics, critical care, and high-complexity procedures with NABH accreditation."

HEALTHCARE EXAMPLE (Good Key Stats):
- Beds: 450
- Occupancy: 70%
- ARPOB: INR 28,000
- Specialty Mix: 3 core specialties
""",

  "Consumer": """
CONSUMER/D2C EXAMPLE (Good Business Overview):
"The Company is a digital-first consumer brand focused on premium personal care products. It sells through its D2C website and leading marketplaces, supported by data-driven marketing and high repeat purchase behavior. Core capabilities include in-house product development, influencer-led acquisition, and fast fulfillment."

CONSUMER/D2C EXAMPLE (Good Key Stats):
- CAC: INR 450
- LTV: INR 2,800
- Repeat Rate: 45%
- AOV: INR 1,200
"""
    }
    
    return examples.get(sector, "")
