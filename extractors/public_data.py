"""
deckAIn - Public Data Scraper
Stage 1B: Scrape public market context from web sources
"""

from typing import List
from ddgs import DDGS

from extractors.schemas import PublicMarketData, PublicDataSource
from config.prompts import get_public_data_queries
from config.settings import ENABLE_WEB_SEARCH
from utils.logger import setup_logger, log_stage

logger = setup_logger(__name__)

class PublicDataScraper:
    """
    Scrape public market context from web sources.
    Uses DuckDuckGo (FREE, no API key required).
    """
    
    def __init__(self):
        """Initialize scraper."""
        logger.info("PublicDataScraper initialized")
    
    def scrape_market_context(self, sector: str) -> PublicMarketData:
        """
        Scrape public market data for a given sector.
        
        Args:
            sector: Business sector (Manufacturing, Pharma, etc.)
        
        Returns:
            PublicMarketData with sources
        """
        log_stage(logger, 1, "Public Data Scraping", "START")
        
        # Web search disabled check
        if not ENABLE_WEB_SEARCH:
            logger.info("[SKIP] Web search disabled in config")
            log_stage(logger, 1, "Public Data Scraping", "SKIP")
            return PublicMarketData()
        
        # Get search queries
        queries = get_public_data_queries(sector)
        logger.info(f"Scraping public data for sector: {sector}")
        logger.debug(f"Search queries: {list(queries.keys())}")
        
        public_data = PublicMarketData()
        
        # Market size data
        public_data.market_size_data = self._search(
            queries["market_size"],
            max_results=3
        )
        logger.info(f"Found {len(public_data.market_size_data)} market size sources")
        
        # Industry trends
        public_data.industry_trends = self._search(
            queries["industry_trends"],
            max_results=3
        )
        logger.info(f"Found {len(public_data.industry_trends)} trend sources")
        
        # Competitive landscape
        public_data.competitive_landscape = self._search(
            queries["competitive_landscape"],
            max_results=2
        )
        logger.info(f"Found {len(public_data.competitive_landscape)} competitive sources")
        
        # Recent news
        public_data.recent_news = self._search(
            queries["recent_news"],
            max_results=2
        )
        logger.info(f"Found {len(public_data.recent_news)} news sources")
        
        total_sources = len(public_data.get_all_sources())
        logger.info(f"Total public sources collected: {total_sources}")
        
        log_stage(logger, 1, "Public Data Scraping", "DONE")
        
        return public_data
    
    def _search(self, query: str, max_results: int = 3) -> List[PublicDataSource]:
        """
        Perform a web search and return structured sources.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of PublicDataSource objects
        """
        sources = []
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                for result in results:
                    source = PublicDataSource(
                        snippet=result.get('body', '')[:500],  # First 500 chars
                        url=result.get('href', ''),
                        title=result.get('title', 'No title')
                    )
                    sources.append(source)
                    logger.debug(f"  - {source.title[:50]}...")
        
        except Exception as e:
            logger.warning(f"Search failed for '{query}': {e}")
        
        return sources
    
    def get_market_summary(self, public_data: PublicMarketData) -> str:
        """
        Create a text summary of public market context for LLM.
        
        Args:
            public_data: Scraped public market data
        
        Returns:
            Formatted text summary
        """
        summary_parts = []
        
        # Market size
        if public_data.market_size_data:
            summary_parts.append("MARKET SIZE & OPPORTUNITY:")
            for source in public_data.market_size_data[:2]:  # Top 2
                summary_parts.append(f"- {source.snippet}")
                summary_parts.append(f"  (Source: {source.url})")
        
        # Trends
        if public_data.industry_trends:
            summary_parts.append("\nINDUSTRY TRENDS:")
            for source in public_data.industry_trends[:2]:
                summary_parts.append(f"- {source.snippet}")
        
        # Competitive
        if public_data.competitive_landscape:
            summary_parts.append("\nCOMPETITIVE LANDSCAPE:")
            for source in public_data.competitive_landscape[:1]:
                summary_parts.append(f"- {source.snippet}")
        
        return "\n".join(summary_parts) if summary_parts else "No public data available."
