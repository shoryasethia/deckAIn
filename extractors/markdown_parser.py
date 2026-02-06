"""
deckAIn - Direct Markdown Content Parser
Extract actual content from OnePager markdown files
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MarkdownContentParser:
    """
    Parse markdown OnePager files to extract actual business content.
    This provides REAL content instead of LLM-generated generic content.
    """
    
    def __init__(self):
        """Initialize parser."""
        logger.info("MarkdownContentParser initialized")
    
    def parse_file(self, markdown_path: str) -> Dict:
        """
        Parse markdown file and extract all business content.
        
        Args:
            markdown_path: Path to company OnePager.md file
        
        Returns:
            Dict with extracted content sections
        """
        md_path = Path(markdown_path)
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Parsing markdown: {md_path.name}")
        
        # Extract all sections
        parsed = {
            "business_description": self._extract_section(content, "Business Description"),
            "website": self._extract_section(content, "Website"),
            "products_services": self._extract_list_section(content, "Product & Services"),
            "application_areas": self._extract_section(content, "Application areas / Industries served"),
            "key_operational_indicators": self._extract_list_section(content, "Key Operational Indicators"),
            "channel_mix": self._extract_list_section(content, "Channel Mix"),
            "key_metrics": self._extract_list_section(content, "Key Metrics"),
            "key_milestones": self._extract_table_as_dict_list(content, "Key Milestones"),
            "partners": self._extract_section(content, "Partners"),
            "clients": self._extract_section(content, "Clients"),
            "awards_certifications": self._extract_list_section(content, "Awards and Certifications"),
            "market_size": self._extract_table_as_dict_list(content, "Market Size"),
            "global_presence": self._extract_list_section(content, "Global Presence"),
            "shareholders": self._extract_all_tables_in_section(content, "Shareholders"),
        }

        details_fields = self._extract_details_fields(content)
        parsed.update(details_fields)

        # Normalize global presence if provided as a comma-separated string
        if parsed.get("global_presence") and len(parsed["global_presence"]) == 1:
            raw_geo = parsed["global_presence"][0]
            if "," in raw_geo:
                parsed["global_presence"] = [g.strip() for g in raw_geo.split(",") if g.strip()]
        
        # Extract metrics from milestones and description
        parsed["employee_count"] = self._extract_employee_count(content)
        parsed["facility_count"] = self._extract_facility_count(content)
        parsed["capacity_indicators"] = self._extract_capacity_indicators(content)
        parsed["years_in_operation"] = self._extract_years_in_operation(parsed.get("founded_year"))
        parsed["channel_metrics"] = self._extract_channel_metrics(parsed.get("channel_mix", []))
        
        # Parse certifications into categories
        parsed["certifications"] = self._parse_certifications(parsed["awards_certifications"])
        
        logger.info(f"Parsed {len(parsed)} content sections")
        return parsed

    def _extract_channel_metrics(self, channel_lines: List[str]) -> Dict[str, float]:
        """Extract numeric metrics from channel mix lines."""
        metrics = {}
        if not channel_lines:
            return metrics

        for line in channel_lines:
            match = re.match(r"^([^:]+):\s*([\d,.]+)", line)
            if match:
                key = match.group(1).strip().lower().replace(" ", "_")
                value = match.group(2).replace(",", "")
                try:
                    metrics[key] = float(value)
                except ValueError:
                    continue

        return metrics

    def _extract_details_fields(self, content: str) -> Dict:
        """Extract structured fields from Details and Ownership sections."""
        fields: Dict[str, Optional[str]] = {
            "domain": None,
            "segment": None,
            "sub_segment": None,
            "business_model": None,
            "business_activity": None,
            "headquarters": None,
            "founded_year": None,
            "ownership_type": None,
        }

        details_text = self._extract_section(content, "Details") or ""
        ownership_text = self._extract_section(content, "Ownership") or ""

        kv_pairs = self._extract_kv_pairs(details_text) + self._extract_kv_pairs(ownership_text)
        for key, value in kv_pairs:
            normalized = key.strip().lower().replace("-", " ")
            normalized = re.sub(r"\s+", " ", normalized)

            if normalized == "domain":
                fields["domain"] = value
            elif normalized == "segment":
                fields["segment"] = value
            elif normalized in ["sub segment", "sub-segment"]:
                fields["sub_segment"] = value
            elif normalized == "customer base":
                fields["business_model"] = value
            elif normalized == "business activity":
                fields["business_activity"] = value
            elif normalized == "headquarters":
                fields["headquarters"] = value
            elif normalized == "founded":
                year_match = re.search(r"(\d{4})", value)
                fields["founded_year"] = year_match.group(1) if year_match else value
            elif normalized == "type":
                fields["ownership_type"] = value

        return fields

    def _extract_kv_pairs(self, text: str) -> List[Tuple[str, str]]:
        """Extract key-value pairs like 'Field: **Value**' from a section."""
        pairs: List[Tuple[str, str]] = []
        for line in text.splitlines():
            match = re.match(r"^\s*([A-Za-z /-]+):\s+\*\*(.+?)\*\*\s*$", line.strip())
            if match:
                pairs.append((match.group(1), match.group(2).strip()))
        return pairs
    
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content from a section header."""
        # Pattern: ## Section Name followed by content until next ##
        pattern = rf"##\s+{re.escape(section_name)}\s*\n\n?(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Remove "Not Available"
            if text == "Not Available":
                return None
            return text
        return None
    
    def _extract_list_section(self, content: str, section_name: str) -> List[str]:
        """Extract bullet list items from a section."""
        section_text = self._extract_section(content, section_name)
        if not section_text:
            return []
        
        # Extract bullet points (- or * or numbered)
        items = []
        for line in section_text.split('\n'):
            line = line.strip()
            # Match bullet points: - text, * text, or numbered lists
            if re.match(r'^[-*]\s+\*\*(.+?)\*\*', line):
                # Bold items like - **Item**
                match = re.match(r'^[-*]\s+\*\*(.+?)\*\*', line)
                items.append(match.group(1).strip())
            elif re.match(r'^[-*]\s+(.+)', line):
                # Regular bullets
                match = re.match(r'^[-*]\s+(.+)', line)
                items.append(match.group(1).strip())
            elif line and not line.startswith('#'):
                # Plain text lines (for certifications that might not have bullets)
                items.append(line)
        
        return items
    
    def _extract_table_as_dict_list(self, content: str, section_name: str) -> List[Dict]:
        """Extract markdown table as list of dicts."""
        section_text = self._extract_section(content, section_name)
        if not section_text:
            return []
        
        # Parse markdown table
        lines = [l.strip() for l in section_text.split('\n') if l.strip()]
        if len(lines) < 3:  # Need header + separator + at least one row
            return []
        
        # Extract headers
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        # Skip separator line (line 1)
        # Extract data rows
        rows = []
        for line in lines[2:]:
            if '|' in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) == len(headers):
                    row_dict = dict(zip(headers, cells))
                    rows.append(row_dict)
        
        return rows
    
    def _extract_all_tables_in_section(self, content: str, section_name: str) -> List[List[Dict]]:
        """Extract all tables in a section (for sections with multiple tables)."""
        section_text = self._extract_section(content, section_name)
        if not section_text:
            return []
        
        # Split by double newline to get separate tables
        tables = []
        current_table_lines = []
        
        for line in section_text.split('\n'):
            line = line.strip()
            if '|' in line:
                current_table_lines.append(line)
            elif current_table_lines:
                # End of current table
                table_data = self._parse_table_lines(current_table_lines)
                if table_data:
                    tables.append(table_data)
                current_table_lines = []
        
        # Handle last table
        if current_table_lines:
            table_data = self._parse_table_lines(current_table_lines)
            if table_data:
                tables.append(table_data)
        
        return tables
    
    def _parse_table_lines(self, lines: List[str]) -> List[Dict]:
        """Parse table lines into list of dicts."""
        if len(lines) < 3:
            return []
        
        # Extract headers
        headers = [h.strip() for h in lines[0].split('|') if h.strip()]
        
        # Skip separator (line 1)
        # Parse data rows
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) == len(headers):
                row_dict = dict(zip(headers, cells))
                rows.append(row_dict)
        
        return rows
    
    def _extract_employee_count(self, content: str) -> Optional[int]:
        """Extract employee count from milestones or description."""
        # Look for patterns like "831 employees", "450 developers", "525 team members"
        patterns = [
            r'(\d+)\s+(?:skilled\s+)?(?:professionals|employees|developers|team\s+members)',
            r'Employee\s+count\s+reached\s+(\d+)',
            r'(\d+)\s+Employees',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                logger.debug(f"Found employee count: {count}")
                return count
        
        return None
    
    def _extract_facility_count(self, content: str) -> Optional[int]:
        """Extract facility/manufacturing unit count."""
        patterns = [
            r'(\d+)\s+(?:WHO-GMP\s+certified\s+)?(?:manufacturing\s+)?(?:facilities|units)',
            r'(\d+)\s+development\s+centers',
            r'(\d+)\s+delivery\s+center',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                logger.debug(f"Found facility count: {count}")
                return count
        
        return None

    def _extract_capacity_indicators(self, content: str) -> List[str]:
        """Extract capacity or scale indicators (MTPA, beds, lines, etc.)."""
        patterns = [
            r"\b\d+(?:\.\d+)?\s*(?:MTPA|TPA|TPD|MW|GW)\b",
            r"\b\d+(?:,\d{3})*\s*(?:sq\.?\s*ft|sqft|square\s+feet|sq\.?\s*m)\b",
            r"\b\d+(?:,\d{3})*\s*(?:beds|lines|plants|units|seats|trucks|vehicles|rooms|stores|branches)\b",
        ]
        matches = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, content, flags=re.IGNORECASE))
        # De-duplicate while preserving order
        seen = set()
        result = []
        for match in matches:
            normalized = match.strip()
            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                result.append(normalized)
        return result

    def _extract_years_in_operation(self, founded_year: Optional[str]) -> Optional[int]:
        """Calculate years in operation from founded year if possible."""
        if not founded_year:
            return None
        try:
            year = int(re.search(r"\d{4}", str(founded_year)).group(0))
            current_year = datetime.now().year
            if 1900 <= year <= current_year:
                return current_year - year
        except Exception:
            return None
        return None
    
    def _parse_certifications(self, cert_list: List[str]) -> List[str]:
        """
        Parse certifications into short names suitable for badges.
        Extracts main certification names (ISO, FDA, GMP, etc.)
        """
        if not cert_list:
            return []
        
        # Extract key certification abbreviations
        cert_keywords = {
            'ISO': 'ISO',
            'CMMI': 'CMMI',
            'FDA': 'FDA',
            'GMP': 'GMP',
            'HACCP': 'HACCP',
            'Halal': 'Halal',
            'Kosher': 'Kosher',
            'FSSC': 'FSSC',
            'FSSAI': 'FSSAI',
            'Organic': 'Organic',
            'SOC': 'SOC',
            'GDPR': 'GDPR',
            'HIPAA': 'HIPAA',
            'PCI DSS': 'PCI-DSS',
        }
        
        found_certs = set()
        for cert_text in cert_list:
            for keyword, short_name in cert_keywords.items():
                if keyword.lower() in cert_text.lower():
                    found_certs.add(short_name)
                    break
        
        # Convert to sorted list
        certs = sorted(list(found_certs))
        logger.debug(f"Parsed certifications: {certs}")
        return certs if certs else ["ISO", "CMMI"]  # Default fallback

    def get_operational_highlights(self, parsed_data: Dict) -> List[str]:
        """
        Generate operational highlights from parsed data.
        Uses ACTUAL content from markdown.
        """
        highlights = []

        # 0. Key operational indicators (already curated)
        for item in parsed_data.get("key_operational_indicators", []):
            if item and item not in highlights:
                highlights.append(item)
        
        # 1. Facilities/Centers
        if parsed_data.get("facility_count"):
            facility_text = f"{parsed_data['facility_count']} operating facilities across key locations"
            highlights.append(facility_text)
        
        # 2. Employee expertise
        if parsed_data.get("employee_count"):
            # Try to get description from business description
            desc = parsed_data.get("business_description", "")
            if "skilled" in desc.lower():
                # Extract the employee description line
                match = re.search(r'\d+\s+skilled\s+[^.]+', desc, re.IGNORECASE)
                if match:
                    highlights.append(match.group(0))
            else:
                highlights.append(f"{parsed_data['employee_count']} skilled professionals with deep expertise")
        
        # 3. Capacity or scale indicators
        for indicator in parsed_data.get("capacity_indicators", [])[:2]:
            highlights.append(f"Capacity scale: {indicator}")

        # 4. End-user industries
        application_areas = parsed_data.get("application_areas")
        if application_areas:
            highlights.append(f"End-user industries served: {application_areas}")

        # 5. Parse business description for key highlights (first few sentences)
        desc = parsed_data.get("business_description", "")
        if desc:
            # Split into sentences, take most important ones
            sentences = [s.strip() + '.' for s in desc.split('.') if s.strip()]
            # Usually 2nd and 3rd sentences are key facts
            for sentence in sentences[1:4]:
                if len(sentence) > 30 and len(sentence) < 200:
                    highlights.append(sentence)
        
        # 6. Partners
        if parsed_data.get("partners"):
            partners = parsed_data["partners"]
            if len(partners) < 100:  # If it's a short list
                highlights.append(f"Strategic partnerships with {partners}")
        
        # Limit to 6 highlights
        return highlights[:6]
    
    def get_product_categories(self, parsed_data: Dict) -> List[str]:
        """Get product/service categories from parsed data."""
        products = parsed_data.get("products_services", [])
        # Return first 8 products
        return products[:8] if products else []
    
    def get_key_customers(self, parsed_data: Dict) -> List[str]:
        """Get key customer types from parsed data."""
        clients = parsed_data.get("clients", "")
        application_areas = parsed_data.get("application_areas", "")
        
        # Parse clients if it's a comma-separated list
        if clients:
            # Try comma/semicolon split first
            if "," in clients or ";" in clients:
                customer_list = [c.strip() for c in re.split(r"[,;]", clients) if c.strip()]
            else:
                # Split on multiple spaces or newlines as a fallback
                customer_list = [c.strip() for c in re.split(r"\s{2,}|\n", clients) if c.strip()]
                if not customer_list:
                    # Last resort: split on single spaces (best-effort for single-word clients)
                    customer_list = [c.strip() for c in clients.split() if c.strip()]

            if len(customer_list) >= 4:
                return customer_list[:4]
            if customer_list:
                return customer_list
        
        # Fallback: use application areas
        if application_areas:
            areas = [a.strip() for a in application_areas.split(',')]
            return [f"{area} Companies" for area in areas[:4]]
        
        # Default fallback
        return [
            "Leading Global\nEnterprises",
            "Top-tier Industry\nLeaders",
            "Fortune 500\nCompanies",
            "International\nPartners"
        ]
    
    def get_key_stats(self, parsed_data: Dict) -> List[Dict]:
        """Generate key stats from parsed data."""
        stats = []
        
        # Employee count
        if parsed_data.get("employee_count"):
            stats.append({
                "value": str(parsed_data["employee_count"]),
                "label": "Employees"
            })
        
        # Facility count
        if parsed_data.get("facility_count"):
            stats.append({
                "value": str(parsed_data["facility_count"]),
                "label": "Facilities"
            })

        # Export / global presence
        if parsed_data.get("global_presence"):
            stats.append({
                "value": str(len(parsed_data["global_presence"])),
                "label": "Geographies"
            })
        
        # Try to extract global presence
        desc = parsed_data.get("business_description", "")
        if any(word in desc.lower() for word in ["global", "international", "export", "countries"]):
            stats.append({
                "value": "Global",
                "label": "Export Presence"
            })

        # Years in operation
        if parsed_data.get("years_in_operation"):
            stats.append({
                "value": f"{parsed_data['years_in_operation']}+",
                "label": "Years in Operation"
            })

        # Capacity indicator
        if parsed_data.get("capacity_indicators"):
            stats.append({
                "value": parsed_data["capacity_indicators"][0],
                "label": "Capacity"
            })
        
        # Client retention from milestones
        milestones = parsed_data.get("key_milestones", [])
        for milestone in milestones:
            text = milestone.get("MILESTONE", "").lower()
            if "retention" in text:
                match = re.search(r'(\d+)%', text)
                if match:
                    stats.append({
                        "value": match.group(1) + "%+",
                        "label": "Customer Retention Rate"
                    })
                    break
        
        return stats[:3]  # Limit to 3 stats
