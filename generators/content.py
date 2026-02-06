"""
deckAIn - Content Generator
Stage 3: Generate anonymized slide content using LLM
"""

from typing import Dict, List, Tuple
from extractors.schemas import FinancialData, PublicMarketData, SlideContent
from extractors.public_data import PublicDataScraper
from extractors.markdown_parser import MarkdownContentParser
from config.prompts import (
    CONTENT_GENERATION_SLIDE_2_PROMPT,
    CONTENT_GENERATION_SLIDE_3_PROMPT,
    CONTENT_GENERATION_SLIDE_4_PROMPT
)
from config.sector_config import get_sector_config, validate_sector_metrics
from config.sector_prompts import get_sector_guidance, get_sector_examples
from utils.llm_client import GeminiClient
from utils.logger import setup_logger, log_stage

logger = setup_logger(__name__)

class ContentGenerator:
    """
    Generate slide content with anonymization using LLM.
    Combines private financial data with public market context.
    """
    
    def __init__(self, llm_client: GeminiClient):
        """
        Initialize content generator.
        
        Args:
            llm_client: Configured Gemini client
        """
        self.llm = llm_client
        self.public_scraper = PublicDataScraper()
        self.markdown_parser = MarkdownContentParser()
        logger.info("ContentGenerator initialized")
    
    def generate_content(
        self,
        financial_data: FinancialData,
        sector: str,
        company_name: str = None,
        markdown_path: str = None
    ) -> Tuple[SlideContent, dict]:
        """
        Generate anonymized slide content (Multi-step).
        Now uses REAL content from markdown file instead of LLM-generated generic content.
        """
        log_stage(logger, 3, "Content Generation", "START")
        
        # Parse markdown to get REAL content
        markdown_content = None
        if markdown_path:
            try:
                markdown_content = self.markdown_parser.parse_file(markdown_path)
                logger.info("Parsed markdown for LLM context")
            except Exception as e:
                logger.warning(f"Could not parse markdown: {e}. Falling back to LLM generation")
                markdown_content = None
        
        # Prepare financial summary for LLM
        financial_summary = self._prepare_financial_summary(financial_data)
        
        # Get public market context
        logger.info(f"Fetching public market data for sector: {sector}")
        public_data = self.public_scraper.scrape_market_context(sector)
        public_summary = self.public_scraper.get_market_summary(public_data)

        # Add market size context from markdown if available
        markdown_market_summary = self._format_market_size_summary(markdown_content)
        if markdown_market_summary:
            public_summary = f"{public_summary}\n\n{markdown_market_summary}"
        
        # Get sector-specific guidance and examples
        sector_guidance = get_sector_guidance(sector)
        sector_examples = get_sector_examples(sector)

        # Build sector intelligence summary for prompts
        sector_intelligence = self._build_sector_intelligence_summary(
            financial_data,
            sector,
            markdown_content
        )
        
        if sector_guidance:
            logger.info(f"Applied {sector}-specific guidance to prompts")
        
        # Shared context for Slides 2-4
        markdown_context = self._format_markdown_context(markdown_content)
        common_context = (
            financial_summary
            + "\n\n" + sector_guidance
            + "\n\n" + sector_examples
            + "\n\n" + sector_intelligence
            + ("\n\nSOURCE DATA:\n" + markdown_context if markdown_context else "")
        )

        # --- STEP 1: Slide 2 & Anonymization ---
        logger.info("Generating Slide 2 (Business Profile) & Anonymization...")
        prompt_2 = CONTENT_GENERATION_SLIDE_2_PROMPT.format(
            private_financials=common_context,
            sector=sector
        )
        raw_2 = self.llm.generate_json(prompt_2)
        
        codename = raw_2.get("company_codename", "Project Unknown")
        logger.info(f"Generated Codename: {codename}")
        
        # --- STEP 2: Slide 3 (Growth Narrative) ---
        logger.info("Generating Slide 3 (Growth Narrative)...")
        prompt_3 = CONTENT_GENERATION_SLIDE_3_PROMPT.format(
            private_financials=common_context,
            codename=codename
        )
        raw_3 = self.llm.generate_json(prompt_3)

        # Normalize legacy field name if returned by LLM
        if "slide_3_financial_narrative" in raw_3 and "slide_3_growth_narrative" not in raw_3:
            raw_3["slide_3_growth_narrative"] = raw_3.pop("slide_3_financial_narrative")
        
        # --- STEP 3: Slide 4 (Highlights) ---
        logger.info("Generating Slide 4 (Investment Highlights)...")
        prompt_4 = CONTENT_GENERATION_SLIDE_4_PROMPT.format(
            private_financials=common_context,
            public_market_data=public_summary + "\n\n" + sector_intelligence,
            codename=codename
        )
        raw_4 = self.llm.generate_json(prompt_4)
        
        # Combine all parts
        raw_content = {**raw_2, **raw_3, **raw_4}
        
        # Auto-fix invalid icons before validation
        if "slide_4_investment_highlights" in raw_content:
            raw_content["slide_4_investment_highlights"] = self._fix_invalid_icons(
                raw_content["slide_4_investment_highlights"]
            )

        # Sanitize any accidental company name mentions
        if company_name:
            raw_content = self._sanitize_company_mentions(raw_content, company_name, codename)
        
        # Validate with Pydantic
        try:
            slide_content = SlideContent(**raw_content)
            logger.info("Slide content validated successfully")
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            raise ValueError(f"Slide content validation failed: {e}")
        
        # Verify anonymization
        self._verify_anonymization(slide_content, company_name)
        
        log_stage(logger, 3, "Content Generation", "DONE")
        
        return slide_content, raw_content

    def _sanitize_company_mentions(self, data: Dict, company_name: str, codename: str) -> Dict:
        """Replace company name and identifying city names with anonymized versions."""
        if not company_name:
            return data

        import re
        # Build list of patterns to sanitize: company name + common identifying cities
        pattern = re.compile(re.escape(company_name), re.IGNORECASE)
        
        # Indian city names that could identify the company
        city_replacements = {
            'ahmedabad': 'Western India',
            'vadodara': 'Western India',
            'mumbai': 'Western India',
            'delhi': 'Northern India',
            'new delhi': 'Northern India',
            'bangalore': 'Southern India',
            'bengaluru': 'Southern India',
            'chennai': 'Southern India',
            'hyderabad': 'Southern India',
            'pune': 'Western India',
            'kolkata': 'Eastern India',
            'jaipur': 'Northern India',
            'lucknow': 'Northern India',
            'chandigarh': 'Northern India',
            'gurgaon': 'Northern India',
            'noida': 'Northern India',
            'indore': 'Central India',
            'bhopal': 'Central India',
            'surat': 'Western India',
            'nagpur': 'Central India',
            'kochi': 'Southern India',
            'coimbatore': 'Southern India',
            'visakhapatnam': 'Southern India',
            'mohali': 'Northern India',
            'zirakpur': 'Northern India',
            'derabassi': 'Northern India',
        }
        
        # Build city regex
        city_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(c) for c in city_replacements.keys()) + r')\b',
            re.IGNORECASE
        )

        def replace_text(value):
            if isinstance(value, str):
                # Replace company name
                result = pattern.sub(codename, value)
                # Replace city names
                def city_sub(m):
                    return city_replacements.get(m.group(0).lower(), 'India')
                result = city_pattern.sub(city_sub, result)
                return result
            if isinstance(value, list):
                return [replace_text(v) for v in value]
            if isinstance(value, dict):
                return {k: replace_text(v) for k, v in value.items()}
            return value

        return replace_text(data)
    
    def _prepare_financial_summary(self, data: FinancialData) -> str:
        """
        Prepare financial data summary for LLM.
        
        Args:
            data: Financial data
        
        Returns:
            Formatted text summary
        """
        summary_parts = [
            "FINANCIAL PERFORMANCE:",
            f"- Revenue trend: {data.revenue_by_year} (₹ Cr) across {data.years}",
            f"- EBITDA trend: {data.ebitda_by_year} (₹ Cr)",
            f"- PAT trend: {data.pat_by_year} (₹ Cr)",
        ]
        
        if data.revenue_cagr:
            summary_parts.append(f"- Revenue CAGR: {data.revenue_cagr}%")
        
        if data.ebitda_margin_latest:
            summary_parts.append(f"- Latest EBITDA margin: {data.ebitda_margin_latest}%")
        
        if data.ebitda_margin_avg:
            summary_parts.append(f"- Average EBITDA margin: {data.ebitda_margin_avg}%")
        
        summary_parts.append("\nOPERATIONAL METRICS:")
        
        if data.employee_count:
            summary_parts.append(f"- Employees: {data.employee_count}")
        
        if data.facility_count:
            summary_parts.append(f"- Manufacturing facilities: {data.facility_count}")
        
        if data.export_revenue_pct:
            summary_parts.append(f"- Export revenue: {data.export_revenue_pct}%")
        
        if data.total_assets:
            summary_parts.append(f"- Total assets: {data.total_assets} ₹ Cr")
        
        if data.total_debt:
            summary_parts.append(f"- Total debt: {data.total_debt} ₹ Cr")
        
        return "\n".join(summary_parts)
    
    def _verify_anonymization(self, content: SlideContent, company_name: str = None):
        """
        Verify that content is properly anonymized.
        
        Args:
            content: Generated slide content
            company_name: Company name to check for leaks
        """
        logger.debug("Verifying anonymization...")
        
        # Check if company name appears anywhere
        if company_name:
            text_to_check = [
                content.slide_2_business_overview.main_text,
                content.slide_3_growth_narrative,
                *[h.text for h in content.slide_4_investment_highlights]
            ]
            
            for text in text_to_check:
                if company_name.lower() in text.lower():
                    logger.warning(f"Company name found in content: '{company_name}'")
                    # Not raising error, just warning - LLM should have handled it
        
        # Check codename format
        if not content.company_codename.startswith("Project "):
            logger.warning(f"Codename doesn't start with 'Project': {content.company_codename}")
        
        logger.info(f"Anonymization verified: {content.company_codename}")
        logger.debug(f"Anonymization map: {len(content.anonymization_map)} replacements")
    
    def _fix_invalid_icons(self, highlights: list) -> list:
        """
        Auto-fix invalid icon names to prevent validation errors.
        
        Args:
            highlights: List of highlight dicts
            
        Returns:
            Fixed highlights list
        """
        valid_icons = [
            "trophy", "factory", "globe", "chart_up", "shield",
            "lightbulb", "users", "award", "target", "star",
            "gear", "rocket", "diamond", "briefcase", "handshake"
        ]
        
        # Icon mapping for common mistakes
        icon_fixes = {
            "growth": "chart_up",
            "innovation": "lightbulb",
            "team": "users",
            "customer": "users",
            "quality": "award",
            "goal": "target",
            "market": "globe",
            "operations": "factory",
            "operational": "gear",
            "technology": "lightbulb",
            "leadership": "trophy",
            "partnership": "handshake",
            "expansion": "rocket",
            "premium": "diamond",
            "business": "briefcase"
        }
        
        fixed_highlights = []
        for highlight in highlights:
            if isinstance(highlight, dict) and "icon" in highlight:
                icon = highlight["icon"]
                if icon not in valid_icons:
                    # Try to fix
                    fixed_icon = icon_fixes.get(icon.lower(), "trophy")  # Default to trophy
                    logger.warning(f"Invalid icon '{icon}' replaced with '{fixed_icon}'")
                    highlight["icon"] = fixed_icon
            fixed_highlights.append(highlight)
        
        return fixed_highlights

    def _generate_slide_2_from_markdown(self, markdown_content: Dict, financial_data: FinancialData, sector: str, company_name: str = None) -> Dict:
        """
        Generate Slide 2 content using REAL markdown content instead of LLM-generated generic content.
        
        Args:
            markdown_content: Parsed markdown content dict
            financial_data: Financial data object
            sector: Sector name
            company_name: Company name for anonymization
        
        Returns:
            Dict with Slide 2 content structure
        """
        logger.info("Building Slide 2 from real markdown content")
        
        # Generate codename (use LLM just for this part)
        codename_prompt = f"""Generate a creative "Project [NAME]" codename for a {sector} company.
        
Examples:
- Project Phoenix (for revival/growth story)
- Project Titan (for industry leader)
- Project Nexus (for connector/platform)
- Project Catalyst (for enabler)
- Project Velocity (for fast-growing)

Return JSON: {{"company_codename": "Project [NAME]"}}"""
        
        codename_response = self.llm.generate_json(codename_prompt)
        codename = codename_response.get("company_codename", "Project Opportunity")
        
        # Build anonymization map
        anonymization_map = {}
        if company_name:
            anonymization_map[company_name] = codename
        
        # Extract operational highlights from REAL markdown content
        operational_highlights = self.markdown_parser.get_operational_highlights(markdown_content)
        operational_highlights = self._enrich_operational_highlights(markdown_content, operational_highlights)
        
        # Extract product categories from REAL markdown content
        product_categories = self.markdown_parser.get_product_categories(markdown_content)
        
        # Extract key customers from REAL markdown content
        key_customers = self.markdown_parser.get_key_customers(markdown_content)
        
        # Extract key stats from REAL markdown content
        key_stats = self._build_key_stats_from_data(markdown_content, financial_data)
        
        # Get main business description text and enrich it with checklist data
        main_text = self._build_main_text(markdown_content, sector, codename, company_name)
        
        # Build Slide 2 structure
        slide_2_data = {
            "company_codename": codename,
            "anonymization_map": anonymization_map,
            "slide_2_business_overview": {
                "main_text": main_text if main_text else f"{codename} is a leading {sector} company.",
                "operational_highlights": operational_highlights,
                "product_categories": product_categories,
                "key_customers": key_customers,
                "key_stats": key_stats,
                "certifications": markdown_content.get("certifications", ["ISO", "CMMI"]),
                "timeline_events": self._build_timeline_events(markdown_content.get("key_milestones", []))
            }
        }
        
        logger.info(f"Built Slide 2 with {len(operational_highlights)} highlights, {len(product_categories)} products, {len(key_stats)} stats")
        return slide_2_data

    def _build_main_text(self, markdown_content: Dict, sector: str, codename: str, company_name: str = None) -> str:
        """Build business overview text using checklist fields."""
        base_text = markdown_content.get("business_description", "") or ""
        if company_name and base_text:
            base_text = base_text.replace(company_name, codename)

        sub_segment = markdown_content.get("sub_segment")
        business_model = markdown_content.get("business_model")
        headquarters = markdown_content.get("headquarters")
        ownership_type = markdown_content.get("ownership_type")
        years_in_operation = markdown_content.get("years_in_operation")
        global_presence = markdown_content.get("global_presence")

        additions = []
        if ownership_type:
            additions.append(f"Ownership: {ownership_type}.")
        if business_model:
            additions.append(f"Business model: {business_model}.")
        if sub_segment:
            additions.append(f"Focus area: {sub_segment}.")
        if years_in_operation:
            additions.append(f"{years_in_operation}+ years in operation.")
        # NOTE: Skip headquarters (city name) to prevent location leak / anonymization breach
        if global_presence:
            # Only mention countries, not specific cities
            countries = [g for g in global_presence[:5] if g.lower() not in ('ahmedabad', 'vadodara', 'mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'kolkata', 'jaipur', 'lucknow', 'chandigarh')]
            if countries:
                additions.append(f"Operating geographies: {', '.join(countries)}.")

        if base_text:
            return f"{base_text} {' '.join(additions)}".strip()

        fallback = f"{codename} is a {sector} company."
        if additions:
            fallback = f"{fallback} {' '.join(additions)}"
        return fallback

    def _enrich_operational_highlights(self, markdown_content: Dict, highlights: List[str]) -> List[str]:
        """Add missing checklist items to operational highlights."""
        enriched = list(highlights) if highlights else []

        if markdown_content.get("business_model"):
            enriched.append(f"Business model: {markdown_content['business_model']}")

        # NOTE: Skip headquarters to prevent city name leak

        if markdown_content.get("global_presence"):
            # Filter out city names, keep only countries/regions
            geos = [g for g in markdown_content["global_presence"][:5] if len(g) > 3 and g.lower() not in ('ahmedabad', 'vadodara', 'mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'kolkata')]
            if geos:
                enriched.append(f"Operating geographies: {', '.join(geos)}")

        if markdown_content.get("certifications"):
            certs = ", ".join(markdown_content["certifications"][:6])
            enriched.append(f"Certifications: {certs}")

        # De-duplicate and keep at most 6
        deduped = []
        seen = set()
        for item in enriched:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped[:6]

    def _build_key_stats_from_data(self, markdown_content: Dict, financial_data: FinancialData) -> List[Dict[str, str]]:
        """Build key stats with finance + operational scale metrics."""
        stats = self.markdown_parser.get_key_stats(markdown_content)

        if financial_data.export_revenue_pct is not None:
            stats.append({
                "value": f"{financial_data.export_revenue_pct}%",
                "label": "Export Share"
            })

        if markdown_content.get("years_in_operation"):
            stats.append({
                "value": f"{markdown_content['years_in_operation']}+",
                "label": "Years in Operation"
            })

        # Keep order priority and cap to 3 for layout
        prioritized = []
        for stat in stats:
            if stat not in prioritized:
                prioritized.append(stat)

        return prioritized[:3]

    def _build_timeline_events(self, milestones: List[Dict]) -> List[Dict[str, str]]:
        """Build concise timeline events from milestones table."""
        events = []
        for milestone in milestones[:4]:
            date_val = milestone.get("DATE") or milestone.get("Date") or ""
            event_val = milestone.get("MILESTONE") or milestone.get("Milestone") or ""
            if date_val and event_val:
                events.append({"year": str(date_val)[:4], "event": event_val})
        return events

    def _format_market_size_summary(self, markdown_content: Dict) -> str:
        """Format market size table from company pack for LLM prompts."""
        if not markdown_content or not markdown_content.get("market_size"):
            return ""

        lines = ["MARKET SIZE (from company pack):"]
        for row in markdown_content.get("market_size", [])[:3]:
            market = row.get("MARKET", "").strip()
            region = row.get("REGION", "").strip()
            size = row.get("CURRENT MARKET SIZE", "").strip()
            growth = row.get("GROWTH (%)", "").strip()
            if market:
                lines.append(f"- {market} | {region} | {size} | Growth: {growth}%")
        return "\n".join(lines)

    def _build_sector_intelligence_summary(self, financial_data: FinancialData, sector: str, markdown_content: Dict) -> str:
        """Create a concise sector intelligence summary for the LLM."""
        available_metrics = set()
        if financial_data.revenue_by_year:
            available_metrics.add("revenue")
        if financial_data.ebitda_by_year:
            available_metrics.add("ebitda")
        if financial_data.pat_by_year:
            available_metrics.add("pat")
        if financial_data.employee_count:
            available_metrics.add("employee_count")
        if financial_data.facility_count:
            available_metrics.add("facility_count")
        if financial_data.export_revenue_pct is not None:
            available_metrics.add("export_revenue_pct")

        for key in (financial_data.additional_metrics or {}):
            available_metrics.add(key)

        if markdown_content and markdown_content.get("capacity_indicators"):
            available_metrics.add("capacity_indicators")

        try:
            sector_config = get_sector_config(sector)
            required_kpis = sector_config.primary_kpis
            optional_kpis = sector_config.optional_kpis
        except Exception:
            required_kpis = []
            optional_kpis = []

        coverage = validate_sector_metrics(sector, available_metrics) if required_kpis else {
            "coverage_pct": 0,
            "missing_kpis": []
        }

        summary = ["SECTOR INTELLIGENCE:"]
        if required_kpis:
            summary.append(f"- Priority KPIs: {', '.join(required_kpis)}")
        if optional_kpis:
            summary.append(f"- Secondary KPIs: {', '.join(optional_kpis)}")
        if available_metrics:
            summary.append(f"- Available metrics: {', '.join(sorted(available_metrics))}")
        if coverage.get("missing_kpis"):
            summary.append(f"- Missing priority KPIs: {', '.join(coverage['missing_kpis'])}")
        summary.append(f"- KPI coverage: {coverage.get('coverage_pct', 0):.0f}%")

        return "\n".join(summary)

    def _format_markdown_context(self, markdown_content: Dict) -> str:
        """Format key markdown fields into a concise context block for the LLM."""
        if not markdown_content:
            return ""

        lines = []
        fields = {
            "business_description": "Business Description",
            "products_services": "Products/Services",
            "application_areas": "End-user Industries",
            "key_operational_indicators": "Key Operational Indicators",
            "clients": "Clients",
            "partners": "Partners",
            "awards_certifications": "Awards/Certifications",
            "market_size": "Market Size",
            "global_presence": "Operating Geographies",
            "domain": "Sector",
            "segment": "Segment",
            "sub_segment": "Sub-segment",
            "business_model": "Business Model",
            "ownership_type": "Ownership",
            "years_in_operation": "Years in Operation",
            "capacity_indicators": "Capacity Indicators"
        }
        # NOTE: 'headquarters' intentionally excluded to prevent city name leaks

        for key, label in fields.items():
            value = markdown_content.get(key)
            if value:
                if isinstance(value, list):
                    value = ", ".join([str(v) for v in value[:8]])
                lines.append(f"- {label}: {value}")

        return "\n".join(lines)
