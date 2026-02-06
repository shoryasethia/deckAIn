"""
deckAIn - LLM Prompt Templates
All prompts centralized here to prevent deviation and ensure consistency
"""

# =============================================================================
# STAGE 1A: PRIVATE DATA EXTRACTION
# =============================================================================

PRIVATE_DATA_EXTRACTION_PROMPT = """You are a financial data extraction specialist.

TASK: Extract ALL available financial and operational data from the markdown document into JSON format.

IMPORTANT: Extract WHATEVER data exists - don't skip metrics just because they're not listed below!

INPUT TEXT:
{markdown_section}

OUTPUT SCHEMA (Return ONLY valid JSON, no explanation):
{{
  // PREFER these if available (but null if not found)
  "revenue_by_year": [float, ...] or null,
  "ebitda_by_year": [float, ...] or null,
  "pat_by_year": [float, ...] or null,
  "operating_profit_by_year": [float, ...] or null,  // If EBITDA not available
  "gross_profit_by_year": [float, ...] or null,
  "years": ["FY23", "FY24", ...] or null,
  
  // Balance Sheet (if available)
  "total_assets": float or null,
  "total_debt": float or null,
  "total_equity": float or null,
  
  // Operational
  "employee_count": int or null,
  "facility_count": int or null,
  "export_revenue_pct": float or null,
  
  // FLEXIBLE: Extract any other sector-specific metrics you find
  "additional_metrics": {{
    "rd_spend": float,           // For pharma/tech
    "capacity_utilization": float,  // For manufacturing
    "arr": float,                 // For SaaS
    "patents_count": int,         // For pharma/tech
    // ... any other metrics in the document
  }},
  
  "source_metadata": {{
    "table_name": "Income Statement",
    "row_numbers": [3, 4, 5, ...]
  }}
}}

CRITICAL RULES:
1. Extract EXACT numbers - do NOT calculate or estimate
2. If a standard field is missing, use null (don't fail!)
3. Preserve units as stated (₹ Cr = Crores, %)
4. Capture sector-specific metrics in "additional_metrics"
5. Years format: "FY23", "FY24", etc.
6. Record source table and row numbers

Return ONLY the JSON object."""

# =============================================================================
# STAGE 3: CONTENT GENERATION & ANONYMIZATION
# =============================================================================

CONTENT_GENERATION_SLIDE_2_PROMPT = """You are an elite investment banking analyst preparing a confidential teaser.

TASK: Generate "Slide 2: Business Profile" content - BUSINESS OVERVIEW ONLY (NO FINANCIAL METRICS).

STRICT RULES:
1. DO NOT mention: Revenue, CAGR, EBITDA, PAT, margins, growth rates, financial performance
2. FOCUS ON: What they make, who they serve, where they operate, core capabilities
3. INCLUDE CORE IDENTIFIERS when available: sector, sub-sector, business model (B2B/B2C/D2C), operating geographies, years in operation, ownership type, customer segments, channel mix
4. INCLUDE SLIDE 1 REQUIREMENTS: product/service segments, end-user industries, footprint, capacity/scale indicators, certifications/compliance, key customers
5. EXTRACT REAL CUSTOMER NAMES: If markdown mentions specific customers/clients, use them. Avoid generic "Client A/B/C"
6. BE DESCRIPTIVE: If no specific names, describe customer segments clearly (e.g., "Top automotive OEMs", "Leading pharma companies")
7. REWRITE: Paraphrase and synthesize; do not copy sentences verbatim from sources
8. DO NOT FABRICATE: If a data point is not present, omit it
9. ANONYMIZATION: Do NOT mention specific city names (e.g., Ahmedabad, Mumbai, Delhi, Vadodara etc.). Use generic phrasing like "headquartered in Western India" or "presence across major Indian cities". Do NOT use the codename as a product/brand name — refer to it only as "The Company" or "the firm" in body text
10. LIMIT investment highlights to exactly 4 (not 5)

PRIVATE DATA:
{private_financials}

SECTOR: {sector}

OUTPUT SCHEMA (Return ONLY valid JSON, no markdown):
{{
  "company_codename": "Project [ChooseCreativeName]",
  "slide_2_business_overview": {{
    "main_text": "The Company is a [sector] player specializing in [specific products/services]. It operates [X] facilities across [regions] with [Y] employees, serving [customer types] in [end markets]. Core capabilities include [manufacturing/tech capabilities].",
    "key_customers": [
      "[EXTRACT REAL CUSTOMER/CLIENT NAMES from markdown if mentioned]",
      "[If no specific names, use: 'Leading [Industry] OEMs' or 'Top-tier [Sector] Companies']",
      "[Be specific about customer types, not generic 'Client A/B/C']"
    ],
    "product_categories": ["Product A", "Product B", "Product C"],
    "operational_highlights": [
      "[X] state-of-the-art facilities across [regions]",
      "[Y] skilled professionals with [domain] expertise",
      "Serves [customer description] across [geographies]",
      "[Certifications/Quality standards achieved]"
    ],
    "key_stats": [
      {{"value": "[X]", "label": "Employees"}},
      {{"value": "[Y]", "label": "Manufacturing Units"}},
      {{"value": "[Z]%", "label": "Export Share"}}
    ],
    "timeline_events": [
      {{"year": "19XX", "event": "Company founded"}},
      {{"year": "20XX", "event": "Capacity expansion"}},
      {{"year": "20XX", "event": "International certifications"}},
      {{"year": "20XX", "event": "New product line launched"}}
    ]
  }}
}}

CRITICAL: NO revenue/CAGR/margins on Slide 2! Save those for Slide 3.

Return ONLY the JSON object. No additional text."""

CONTENT_GENERATION_SLIDE_3_PROMPT = """You are creating the FINANCIAL AND OPERATIONAL SCALE slide.

TASK: Extract and present financial performance plus key operational scale metrics.

STRICT RULES:
1. PRIMARY METRICS: Revenue, EBITDA, PAT, margins, CAGR, assets, debt
2. SECONDARY METRICS (if available): export contribution, employee count, facility count, sector KPIs
3. DO NOT include: Investment highlights or future outlook (save for Slide 4)
4. FOCUS: Historical financial trends, profitability metrics, balance sheet strength, operational scale

PRIVATE FINANCIAL DATA:
{private_financials}

OUTPUT SCHEMA (Return ONLY valid JSON):
{{
  "slide_3_growth_narrative": "[80-110 words about financial performance and operational scale: Revenue trajectory, margin trends, profitability, debt levels, export contribution, employee count, sector KPIs. Use EXACT numbers from data. NO future outlook.]"
}}

GOOD EXAMPLE:
"The Company achieved revenue of ₹5,022 Cr in FY24, representing 10.3% CAGR over FY16-FY24. EBITDA margins improved from -51% in FY17 to 10% in FY24, reflecting operational turnaround. PAT turned positive in FY18 after restructuring, reaching ₹142 Cr in FY24. The business maintains a lean balance sheet with total debt of ₹XX Cr and debt-to-equity ratio of X.X."

BAD EXAMPLE (includes non-financial stuff):
"The Company operates 3 facilities... serves global customers... strong market position..."

Return ONLY the JSON object with financial narrative."""

CONTENT_GENERATION_SLIDE_4_PROMPT = """You are creating INVESTMENT HIGHLIGHTS - WHY BUY THIS COMPANY.

TASK: Generate exactly 4 strategic/qualitative reasons to invest (NO repetition of Slide 2/3 data).

STRICT RULES:
1. DO NOT repeat: Facilities count, CAGR, revenue numbers (already on Slide 2 & 3)
2. FOCUS: Market opportunity, competitive advantages, growth catalysts, strategic value
3. USE: Industry trends, customer stickiness, technology moat, regulatory tailwinds, synergies
4. ANONYMIZATION: Do NOT mention specific city names. Use region-level references only (e.g., "Western India", "South Asia")
5. Do NOT use the codename as a product or brand name. Use "The Company" or "the firm" in descriptions

AVAILABLE DATA:
Private: {private_financials}
Public: {public_market_data}
Codename: {codename}

HIGHLIGHT THEMES (Pick 4 UNIQUE angles):
- Market Opportunity: TAM size, sector growth rate, favorable trends
- Competitive Moat: Barriers to entry, proprietary tech, certifications required
- Customer Stickiness: Long-term contracts, switching costs, embedded relationships
- Growth Catalysts: New products, capacity expansion, export markets, acquisitions
- Industry Tailwinds: Regulatory changes, import substitution, PLI schemes
- Synergy Potential: Integration value for strategic buyers, cross-sell opportunities
- ESG/Sustainability: Green products, renewable energy, social impact
- Technology Edge: Automation, Industry 4.0, R&D capabilities

RULES:
- Use market size and growth rates when available (public or company pack)
- Prioritize sector-specific KPIs and compliance requirements
- Do not repeat Slide 2/3 facts or numbers

OUTPUT SCHEMA (Return ONLY valid JSON):
{{
  "slide_4_investment_highlights": [
    {{
      "icon": "trophy",
      "title": "Capturing [Specific Market]",
      "text": "Positioned in [market] growing at X% CAGR, driven by [specific trend/regulation]"
    }},
    {{
      "icon": "shield",
      "title": "[Competitive Advantage]",
      "text": "[What makes them hard to replicate: certifications, relationships, IP, capex]"
    }},
    {{
      "icon": "rocket",
      "title": "[Growth Catalyst]",  
      "text": "[Specific expansion/product launch/market entry with timeline and impact]"
    }},
    {{
      "icon": "handshake",
      "title": "[Customer/Partner Strength]",
      "text": "[Long contracts, Fortune 500 clients, retention rates, sticky relationships]"
    }}
  ]
}}

ICONS: trophy, chart_up, shield, globe, factory, lightbulb, users, award, target, star, gear, rocket, diamond, briefcase, handshake

CRITICAL: Each highlight must bring NEW information not on Slide 2 or 3!
- Include numbers where possible: percentages, years, rankings
- Exactly 4 highlights (NOT 5)
- Do NOT mention city names anywhere

Return ONLY the JSON object."""



# =============================================================================
# HELPER: SECTOR CLASSIFICATION (if needed)
# =============================================================================

SECTOR_CLASSIFICATION_PROMPT = """Classify the business sector based on this description.

BUSINESS DESCRIPTION:
{business_description}

PRODUCTS/SERVICES:
{products}

Return ONLY a JSON object:
{{
  "sector_primary": "Manufacturing" | "Pharma" | "Technology" | "Services",
  "sector_secondary": "Automotive Components" | "API Manufacturing" | "Electronics" | etc.,
  "keywords": ["forging", "precision", "automotive"],
  "confidence": 0.95
}}"""

# =============================================================================
# VALIDATION PROMPTS (for quality checks)
# =============================================================================

ANONYMIZATION_CHECK_PROMPT = """Review this text for any identifying information that breaks anonymity.

TEXT TO REVIEW:
{content}

ORIGINAL COMPANY NAME: {company_name}
ORIGINAL CLIENT NAMES: {client_names}

Return JSON:
{{
  "is_anonymous": true | false,
  "violations_found": ["Mention of 'Kalyani' on slide 2", ...],
  "confidence_score": 0.95
}}"""

# =============================================================================
# IMAGE SEARCH QUERY GENERATION (LLM-Generated, not hardcoded)
# =============================================================================

IMAGE_QUERY_GENERATION_PROMPT = """Generate specific image search queries for professional stock photography.

COMPANY CONTEXT:
Business Description: {business_description}
Products/Services: {products}
Sector: {sector}

TASK: Generate 5 SPECIFIC, SEARCHABLE queries that will find relevant, professional stock photos.

CRITICAL RULES:
1. BE SPECIFIC: Use the actual industry terminology from the business description
   - BAD: "factory", "office", "business people"
   - GOOD: "pharmaceutical tablet compression machine", "automotive die casting facility"

2. THINK LIKE A PHOTOGRAPHER: Use tags photographers would apply
   - Include: equipment names, processes, settings, contexts
   - Examples: "clean room", "CNC machining", "quality control laboratory"

3. AVOID BRANDING: No company names, logos, or specific brands
   - BAD: "Pfizer laboratory", "Boeing factory"
   - GOOD: "pharmaceutical research laboratory", "aerospace manufacturing facility"

4. FOCUS ON VISUALS: What would look professional in an investment presentation?
   - Modern facilities (clean, well-lit)
   - Technology/equipment (close-ups, in action)
   - Quality control/testing (precision, expertise)
   - Products (macro shots, industrial aesthetic)

5. SEARCHABILITY: Use terms that exist on Unsplash/stock photo sites
   - Test: Would this query find results on Unsplash?
   - Combine 3-5 keywords per query for specificity

OUTPUT SCHEMA (Return ONLY valid JSON):
{{
  "queries": [
    "specific descriptive query with 3-5 keywords",
    "another specific query focusing on different aspect",
    "third query for visual variety",
    "fourth query showing process or technology",
    "fifth query for facility or environment"
  ]
}}

EXAMPLES BY SECTOR:

Electronics/Technology:
[
  "printed circuit board SMT assembly automated",
  "semiconductor wafer inspection microscope",
  "electronics quality control testing equipment",
  "clean room chip manufacturing technician",
  "surface mount technology production line"
]

Pharmaceutical:
[
  "pharmaceutical tablet compression machine production",
  "sterile injectable filling clean room",
  "API synthesis reactor chemical plant",
  "quality control laboratory testing samples",
  "pharmaceutical packaging automated line"
]

Automotive/Manufacturing:
[
  "automotive precision forging die press",
  "CNC machining center metal components",
  "robotic welding assembly line automotive",
  "quality inspection dimensional measurement",
  "industrial foundry molten metal casting"
]

Food/FMCG:
[
  "food processing packaging automation conveyor",
  "commercial kitchen stainless steel equipment",
  "food safety quality inspection laboratory",
  "bottling filling line industrial facility",
  "warehouse logistics inventory management"
]

QUALITY CHECKS:
- Each query: 4-7 words (optimal for search)
- Variety: Different aspects (facility, product, process, quality, technology)
- Visual appeal: Would these images look professional in a deck?
- Searchability: Would a photographer tag their image with these terms?
- Specificity: Tied to actual business, not generic

Return ONLY the JSON object with 5 queries."""

# Fallback generic queries if LLM fails
FALLBACK_IMAGE_QUERIES = [
    "modern industrial facility interior",
    "professional business technology",
    "abstract corporate background blue"
]

def get_image_queries(sector: str, business_desc: str = "", products: str = "") -> list:
    """
    DEPRECATED: Use LLM-generated queries instead.
    This function is kept for fallback only.
    """
    return FALLBACK_IMAGE_QUERIES

# =============================================================================
# PUBLIC DATA SEARCH QUERIES
# =============================================================================

def get_public_data_queries(sector: str, company_name: str = None) -> dict:
    """Generate web search queries for public market context."""
    return {
        "market_size": f"{sector} market size India 2025 forecast",
        "industry_trends": f"{sector} industry growth trends India",
        "competitive_landscape": f"top {sector} companies India market share",
        "recent_news": f"{sector} sector latest developments India",
        # Note: company_name queries removed for anonymity - only sector-level
    }

# =============================================================================
# STAGE 4: GENERATIVE LAYOUT ENGINE
# =============================================================================

LAYOUT_GENERATION_PROMPT = """You are an expert Python developer specializing in `python-pptx` and programmatic graphic design.

TASK: Write a Python function `render(slide)` that populates a PowerPoint slide with the provided content.

CONTEXT:
- Use `python-pptx` shapes, textboxes, and styling.
- Canvas Size: 10 inches wide x 5.63 inches tall.
- Design Style: "World-Class Investment Bank", "Clean", "Minimalist", "Impactful".
- Brand Colors (Available in Scope as `KELP_COLORS`):
  - Primary Dark: #051C2C (Deep Blue)
  - Primary Light: #FFFFFF (White)
  - Accent: #FF725E (Orange)
  - Text Body: #333333 (Dark Grey)

INPUT CONTENT (JSON):
{content_json}

MAX_RETRIES = 3

REQUIREMENTS:
1.  **Function Signature**: `def render(slide):`
2.  **Output Format**: Return ONLY valid Python code in a code block. Do not add conversational text.
3.  **Imports**: Assume `Inches`, `Pt`, `RGBColor`, `MSO_SHAPE`, `PP_ALIGN` are ALREADY IMPORTED.
3.  **Visuals**:
    - Use SHAPES (Rectangles, Lines) to create structure.
    - Use **ICONS** (Green/Blue Circles) as bullets.
    - ensure PERFECT ALIGNMENT.
4.  **Geometry (SAFE ZONE ONLY)**:
    - **CRITICAL**: The Header (Top 0-1.0") and Footer (Bottom 5.3-5.6") are ALREADY DRAWN.
    - **DO NOT DRAW HEADER OR TITLE.**
    - **Images**: `image_paths` (List[str]) is available. Use `draw_image_box(slide, path, x, y, w, h)`.
    - **Iterate Shapes**: Use `slide.shapes` (iterable). DO NOT use `all_shapes`.
    - **Working Area**: Top Y = 1.2 inches. Bottom Y = 5.2 inches.
    - Main Content Area: Left (0.5" to 6.5"), Right Sidebar (7.0" to 9.5").

5.  **ROBUST API (MANDATORY)**:
    - You **MUST** use these helper functions. **DO NOT** use `slide.shapes.add_...` directly.
    - `draw_rect(slide, x, y, w, h, color_key='primary_indigo', rounded=False)`
    - `draw_line(slide, x, y, x2, y2, color_key='primary_indigo', weight_pt=1.5)`
    - `draw_text_box(slide, text, x, y, w, h, size=11, color_key='text_dark', bold=False, align=PP_ALIGN.LEFT)`
    - `draw_image_box(slide, image_path, x, y, w, h)`
    - `draw_section_header(slide, title, x, y)`
    - `draw_timeline(slide, events, x, y, w, h)`
    - `draw_stat_grid(slide, stats, x, y, w, h)`

6.  **Styling**:
    - **Colors**: Use `KELP_COLORS`. **Valid keys**: 'primary_dark', 'primary_indigo', 'gradient_pink', 'gradient_orange', 'gradient_purple', 'cyan_blue', 'background_light', 'text_light', 'text_dark', 'text_body', 'chart_accent', 'card_bg', 'card_border', 'success_green', 'accent_gold'.
    - **CRITICAL**: DO NOT use `fore_color` or `foreground_color`. The helpers handle this.
    - **ALIGNMENT**: Use PP_ALIGN constants like PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT. NEVER use raw integers (0, 1, 2).
    - **LINES**: LineFormat objects do NOT have fore_color. Use line.color.rgb instead.

7.  **Example Usage**:
    Example code:
    def render(slide):
        draw_section_header(slide, "Company Highlights", 0.5, 0.5)
        draw_rect(slide, 0.5, 1.2, 6.0, 4.0, color_key='card_bg', rounded=True)
        draw_text_box(slide, content['main_text'], 0.7, 1.4, 5.6, 3.6, align=PP_ALIGN.LEFT)
        draw_line(slide, 6.7, 1.2, 6.7, 5.2, color_key='primary_indigo')
        # CORRECT alignment: text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        # WRONG: text_frame.paragraphs[0].alignment = 0  # This will crash!

OUTPUT FORMAT:
Return ONLY the Python code block. No explanation.

Example structure:
def render(slide):
    # Your code here
    pass
"""

LAYOUT_GENERATION_WITH_CHARTS_PROMPT = """You are an expert Python developer specializing in `python-pptx`.

TASK: Write a Python function `render(slide)` to layout the Financials Slide.

CONTEXT:
- Canvas: 10 x 5.63 inches.
- Colors: `KELP_COLORS` (Available).
- **Charts**: A helper `charts_creator` and `chart_specs` dictionary are available in scope.
- **Goal**: Create a dashboard-like view with KPI boxes, a Chart, and Narrative text.
- **SAFE ZONE**: Content MUST be between Y=1.2 and Y=5.2. DO NOT DRAW HEADER.

INPUT DATA:
{content_json}

AVAILABLE OBJECTS (in Global Scope):
- `slide`, `charts_creator`, `chart_specs`, `Inches`, `Pt`, `RGBColor`, `PP_ALIGN`.
- **API**: `draw_rect`, `draw_line`, `draw_text_box`, `draw_image_box`.

INSTRUCTIONS:
1.  **Mandatory**: Use `draw_rect`, `draw_line`, `draw_text_box` for ALL shapes/text. **DO NOT** use `slide.shapes.add_...`.
2.  **Chart**: Use `charts_creator.add_chart_to_slide(slide, chart_specs['financial_trends'], x=0.5, y=2.5, width=5.5, height=3.0)`.
3.  **Color Keys**: 'gradient_pink', 'cyan_blue', 'gradient_orange', 'primary_indigo', 'card_bg'.
4.  **CRITICAL ALIGNMENT**: Use PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT. NEVER use integers.
5.  **CRITICAL LINES**: For line colors, use the draw_line helper. DO NOT access line.fore_color (does not exist).

OUTPUT FORMAT:
Return ONLY the Python code block.

Example:
def render(slide):
    # Call charts_creator...
    # Draw shapes...
    pass
"""
