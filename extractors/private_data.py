"""
deckAIn - Private Data Extractor
Stage 1A: Extract financial data from markdown/PDF using LLM
"""

import re
from pathlib import Path
from typing import Optional, Tuple

from extractors.schemas import FinancialData, SourceMetadata
from extractors.markdown_parser import MarkdownContentParser
from config.prompts import PRIVATE_DATA_EXTRACTION_PROMPT
from utils.llm_client import GeminiClient
from utils.logger import setup_logger, log_stage

logger = setup_logger(__name__)

class PrivateDataExtractor:
    """
    Extract financial data from private company documents.
    Uses LLM for direct JSON extraction (NO code generation).
    """
    
    def __init__(self, llm_client: GeminiClient):
        """
        Initialize extractor.
        
        Args:
            llm_client: Configured Gemini client
        """
        self.llm = llm_client
        self.markdown_parser = MarkdownContentParser()
        logger.info("PrivateDataExtractor initialized")
    
    def extract_from_markdown(self, markdown_path: str) -> Tuple[FinancialData, dict]:
        """
        Extract structured financial data from markdown file.
        
        Args:
            markdown_path: Path to company OnePager.md file
        
        Returns:
            Tuple of (validated Financial Data, raw LLM response)
        
        Raises:
            FileNotFoundError: If markdown file doesn't exist
            ValueError: If extraction fails or validation fails
        """
        log_stage(logger, 1, "Private Data Extraction", "START")
        
        # Read markdown file
        md_path = Path(markdown_path)
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        logger.info(f"Read markdown file: {md_path.name} ({len(markdown_content)} chars)")
        
        # Upload file to Gemini File API (more efficient than sending as text)
        logger.info("Uploading markdown to Gemini File API...")
        uploaded_file = self.llm.upload_file(
            file_path=str(md_path),
            display_name=f"{md_path.stem}_financial_data"
        )
        
        # Parse markdown for fallback operational metrics
        parsed_markdown = None
        try:
            parsed_markdown = self.markdown_parser.parse_file(markdown_path)
        except Exception as e:
            logger.warning(f"Markdown parsing failed for fallback metrics: {e}")

        # Build prompt that references the uploaded file
        prompt = """You are a financial data extraction specialist.

TASK: Extract structured financial and operational data from the uploaded markdown document into JSON format.

Focus on these sections:
- Income Statement (Revenue, EBITDA, PAT by year)
- Balance Sheet (Assets, Debt, Equity)
- Key Metrics (Employees, Facilities, Export %, sector KPIs)

OUTPUT SCHEMA (Return ONLY valid JSON, no explanation):
{
    "revenue_by_year": [float, float, ...] or null,
    "ebitda_by_year": [float, float, ...] or null,
    "pat_by_year": [float, float, ...] or null,
    "years": ["FY23", "FY24", "FY25", ...] or null,
    "total_assets": float or null,
    "total_debt": float or null,
    "total_equity": float or null,
    "employee_count": int or null,
    "facility_count": int or null,
    "export_revenue_pct": float or null,
    "additional_metrics": {
        "capacity_utilization": float or null,
        "rd_spend": float or null,
        "arr": float or null,
        "fleet_size": float or null,
        "bed_count": float or null,
        "cac": float or null,
        "ltv": float or null
    },
    "source_metadata": {
        "table_name": "Income Statement",
        "row_numbers": [3, 4, 5, ...]
    }
}

CRITICAL RULES:
1. Extract EXACT numbers from tables - do NOT calculate or estimate
2. If a value is missing, use null
3. Preserve units (₹ Cr means Crores, % is percentage)
4. Record which table and row numbers you extracted from
5. Years format: "FY23", "FY24", etc.
6. If a sector KPI exists, place it in additional_metrics

Return ONLY the JSON object."""
        
        # Call LLM with uploaded file
        logger.info("Calling LLM for financial data extraction (using File API)...")
        # Generate JSON with file (using File API for efficiency)
        raw_data = self.llm.generate_json_with_file(
            prompt=prompt,
            file_ref=uploaded_file  # Pass file object, not URI
        )
        
        # Robustness: Handle list response (common with some models)
        if isinstance(raw_data, list):
            if raw_data:
                logger.warning("LLM returned a list instead of a dict. Using first element.")
                raw_data = raw_data[0]
            else:
                 logger.error("LLM returned an empty list.")
                 return None, None
        
        logger.debug(f"LLM returned: {list(raw_data.keys())}")
        
        # Add source metadata
        raw_data['source_metadata'] = {
            "table_name": raw_data.get("source_metadata", {}).get("table_name", "Unknown"),
            "row_numbers": raw_data.get("source_metadata", {}).get("row_numbers", []),
            "source_file": str(md_path),
            "extraction_timestamp": ""  # Will be auto-filled by Pydantic
        }

        # Fill missing operational metrics from parsed markdown
        if parsed_markdown:
            if raw_data.get("employee_count") is None and parsed_markdown.get("employee_count"):
                raw_data["employee_count"] = parsed_markdown.get("employee_count")
            if raw_data.get("facility_count") is None and parsed_markdown.get("facility_count"):
                raw_data["facility_count"] = parsed_markdown.get("facility_count")

            additional_metrics = raw_data.get("additional_metrics") or {}
            channel_metrics = parsed_markdown.get("channel_metrics") or {}
            for key, value in channel_metrics.items():
                additional_metrics.setdefault(key, value)

            clients = parsed_markdown.get("clients")
            if clients:
                if "," in clients:
                    client_list = [c.strip() for c in clients.split(",") if c.strip()]
                else:
                    client_list = [c.strip() for c in clients.split() if c.strip()]
                if client_list:
                    additional_metrics.setdefault("client_count", len(client_list))

            raw_data["additional_metrics"] = additional_metrics
        
        # Validate with Pydantic
        try:
            financial_data = FinancialData(**raw_data)
            logger.info("Financial data validated successfully")
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise ValueError(f"Financial data validation failed: {e}")
        
        # Calculate derived metrics (Python, NOT LLM)
        financial_data = self._calculate_metrics(financial_data)
        
        log_stage(logger, 1, "Private Data Extraction", "DONE")
        
        return financial_data, raw_data
    
    def _extract_financial_section(self, markdown: str) -> str:
        """
        Extract financial tables section from markdown.
        
        Args:
            markdown: Full markdown content
        
        Returns:
            Financial section text
        """
        # Find tables with financial keywords
        patterns = [
            r'## Income Statement.*?(?=##|\Z)',
            r'## Balance Sheet.*?(?=##|\Z)',
            r'## Financial.*?(?=##|\Z)',
            r'## Key.*?Metrics.*?(?=##|\Z)'
        ]
        
        sections = []
        for pattern in patterns:
            matches = re.findall(pattern, markdown, re.DOTALL | re.IGNORECASE)
            sections.extend(matches)
        
        if sections:
            return "\n\n".join(sections)
        
        return ""
    
    def _calculate_metrics(self, data: FinancialData) -> FinancialData:
        """
        Calculate derived financial metrics using Python (100% accurate).
        
        Args:
            data: Financial data with base numbers
        
        Returns:
            Updated financial data with calculated metrics
        """
        logger.debug("Calculating derived metrics...")
        
        # Revenue CAGR
        if len(data.revenue_by_year) >= 2:
            years = len(data.revenue_by_year)
            start = data.revenue_by_year[0]
            end = data.revenue_by_year[-1]
            
            if start > 0:
                cagr = ((end / start) ** (1 / (years - 1)) - 1) * 100
                data.revenue_cagr = round(cagr, 1)
                logger.debug(f"Revenue CAGR: {data.revenue_cagr}%")
        
        # EBITDA margins
        if data.revenue_by_year and data.ebitda_by_year:
            # Latest margin
            if data.revenue_by_year[-1] > 0:
                latest_margin = (data.ebitda_by_year[-1] / data.revenue_by_year[-1]) * 100
                data.ebitda_margin_latest = round(latest_margin, 1)
                logger.debug(f"Latest EBITDA margin: {data.ebitda_margin_latest}%")
            
            # Average margin
            margins = []
            for rev, ebitda in zip(data.revenue_by_year, data.ebitda_by_year):
                if rev > 0:
                    margins.append((ebitda / rev) * 100)
            
            if margins:
                data.ebitda_margin_avg = round(sum(margins) / len(margins), 1)
                logger.debug(f"Average EBITDA margin: {data.ebitda_margin_avg}%")
        
        logger.info("Calculated metrics: CAGR, margins")

        # Revenue per employee (services KPI) if possible
        if data.revenue_by_year and data.employee_count and data.employee_count > 0:
            latest_rev = data.revenue_by_year[-1]
            revenue_per_employee = latest_rev / data.employee_count
            data.additional_metrics = data.additional_metrics or {}
            if "revenue_per_employee" not in data.additional_metrics:
                data.additional_metrics["revenue_per_employee"] = round(revenue_per_employee, 2)
        
        return data
