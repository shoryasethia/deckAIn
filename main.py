"""
deckAIn - Main Pipeline
Investment Teaser Generation Pipeline
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.llm_client import GeminiClient
from utils.logger import setup_logger
from extractors.private_data import PrivateDataExtractor
from extractors.public_data import PublicDataScraper
from generators.chart_data import ChartDataGenerator
from generators.content import ContentGenerator
from generators.citations import CitationsBuilder
from assets.image_sourcing import ImageSourcing
from assets.image_compliance import ImageComplianceChecker
from assemblers.slide_builder import SlideBuilder
from assemblers.ppt_template import PPTTemplate
from assemblers.native_charts import NativeChartsCreator
from generators.layout_engine import LayoutEngine
from validators.compliance import ComplianceValidator
from utils.ppt_renderer import PPTRenderer
from validators.groq_reviewer import GroqReviewer
from validators.slide_optimizer import SlideOptimizer
from config.settings import ENABLE_GROQ_REVIEW, USE_LLM_FOR_SLIDES

logger = setup_logger(__name__)

class TeaserPipeline:
    """
    Main pipeline orchestrator for investment teaser generation.
    """
    
    def __init__(self):
        """Initialize pipeline."""
        logger.info("\ndeckAIn - Investment Teaser Generator\n")
        
        # Initialize components
        self.llm = GeminiClient()
        self.private_extractor = PrivateDataExtractor(self.llm)
        self.public_scraper = PublicDataScraper()
        self.chart_generator = ChartDataGenerator()
        self.content_generator = ContentGenerator(self.llm)
        self.citations_builder = CitationsBuilder()
        self.image_sourcing = ImageSourcing()
        self.image_compliance = ImageComplianceChecker()
        
        # Generative Layout Engine (controlled by USE_LLM_FOR_SLIDES flag)
        # Enable in .env with USE_LLM_FOR_SLIDES=true for experimental AI-generated layouts
        if USE_LLM_FOR_SLIDES:
            layout_engine = LayoutEngine(self.llm)
            logger.info("LLM-based slide generation enabled (experimental)")
        else:
            layout_engine = None  # Use reliable fixed templates
            logger.info("Using fixed slide templates")
        
        # Assemblers
        self.ppt_template = PPTTemplate()
        self.charts_creator = NativeChartsCreator()
        self.slide_builder = SlideBuilder(self.ppt_template, layout_engine)
        self.validator = ComplianceValidator()
        self.ppt_renderer = PPTRenderer()
        self.groq_reviewer = GroqReviewer()
        self.slide_optimizer = SlideOptimizer() # Added from original code, was missing in diff
        
        logger.info("All components initialized")
    
    def generate_teaser(
        self,
        markdown_path: str,
        sector: str,
        company_name: str = None
    ) -> dict:
        """
        Generate investment teaser presentation.
        
        Args:
            markdown_path: Path to company OnePager.md
            sector: Business sector (Manufacturing, Pharma, etc.)
            company_name: Optional company name for anonymization checks
        
        Returns:
            Dictionary with output paths and stats
        """
        logger.info(f"\nStarting teaser generation for: {Path(markdown_path).stem}")
        logger.info(f"Sector: {sector}")
        
        # Create company-specific output directory
        from config.settings import OUTPUT_DIR
        run_name = Path(markdown_path).stem
        company_output_dir = OUTPUT_DIR / run_name
        company_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {company_output_dir}")
        
        # Add file handler for this run
        import logging
        from datetime import datetime
        log_file = company_output_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
        logger.info(f"Log file: {log_file}")
        
        # Start timing
        import time
        start_time = time.time()
        
        try:
            # Stage 1A: Extract private data
            financial_data, _ = self.private_extractor.extract_from_markdown(markdown_path)
            
            # Stage 1B: Scrape public data (not needed directly, handled in content gen)
            # public_data = self.public_scraper.scrape_market_context(sector)
            
            # Stage 2: Prepare chart data (sector-aware)
            chart_specs = self.chart_generator.generate_chart_specs(financial_data, sector)
            
            # Stage 3: Generate content
            slide_content, _ = self.content_generator.generate_content(
                financial_data,
                sector,
                company_name,
                markdown_path=markdown_path  # Pass markdown path for direct content extraction
            )
            
            # Stage 4: Build citations
            # Get public data from content generator
            public_data = self.public_scraper.scrape_market_context(sector)
            citations_path = company_output_dir / f"{slide_content.company_codename.replace(' ', '_')}_citations.docx"
            citations_path = self.citations_builder.build_citations_document(
                financial_data,
                public_data,
                slide_content.company_codename,
                output_path=str(citations_path)
            )
            
            # Stage 5: Source images (with business context for better queries)
            # Increased from 3 to 5 images for richer visual presentation
            self.image_sourcing = ImageSourcing(company_output_dir)
            self.image_sourcing.llm = self.llm  # Provide LLM client
            images = self.image_sourcing.source_images(
                sector,
                business_description=slide_content.slide_2_business_overview.main_text,
                products=", ".join(slide_content.slide_2_business_overview.product_categories),
                count=5  # Increased from 3 to 5
            )
            
            # Stage 6: Assemble presentation
            pptx_path = self.slide_builder.build_presentation(
                slide_content,
                financial_data, # Added this
                chart_specs,
                images,
                company_output_dir=company_output_dir,
                sector=sector
            )
            
            # Stage 7: Validate compliance
            # Stage 7: Compliance validation (with sector-specific checks)
            compliance_report = self.validator.validate_presentation(
                pptx_path,
                citations_path,
                company_name,
                sector=sector,
                financial_data=financial_data
            )
            
            # Stage 8: Visual Review & Optimization Loop (Groq Feedback)
            # Controlled by ENABLE_GROQ_REVIEW flag in .env (default: false)
            # WARNING: Groq review can cause issues (deletes KPI cards, overlaps text)
            review_report_path = None
            
            if ENABLE_GROQ_REVIEW and self.ppt_renderer.available and self.groq_reviewer.client:
                logger.info("[>] [8/8] Visual Review & Optimization Loop - START")
                
                # Save BEFORE Groq review starts
                before_review_path = pptx_path.parent / f"{pptx_path.stem}.pptx"
                logger.info(f"Saved BEFORE Groq review: {before_review_path}")
                
                images_dir = company_output_dir / "review_images"
                images_dir.mkdir(exist_ok=True)
                
                # Correct slide indices: 0=Cover, 1=Business Profile, 2=Financials, 3=Highlights, 4=Disclaimer
                # NOTE: Slide 3 (Financials) excluded from review as Groq tends to break chart layouts
                slides_to_review = [
                    (1, "Business Profile"), 
                    # (2, "Financial & Operational"),  # DISABLED - Groq breaks charts
                    (3, "Investment Highlights")
                ]
                
                MAX_ITERATIONS = 2  # Reduced from 3 to minimize over-optimization
                SCORE_THRESHOLD = 8
                
                review_content = ["# Deck Review & Optimization Report", ""]
                optimizer = SlideOptimizer()
                
                for slide_idx, slide_name in slides_to_review:
                    logger.info(f" Reviewing {slide_name} (Slide {slide_idx + 1})...")
                    
                    for iteration in range(MAX_ITERATIONS):
                        # Export current slide state
                        img_path = images_dir / f"slide_{slide_idx + 1}_iter{iteration + 1}.jpg"
                        try:
                            saved_path = self.ppt_renderer.export_slide_as_image(pptx_path, slide_idx, str(img_path))
                        except Exception as e:
                            logger.warning(f"Could not export slide for review (File might be open?): {e}")
                            saved_path = None
                        
                        if not saved_path:
                            logger.warning("Skipping review for this slide due to export failure.")
                            break
                        
                        # Get structured review
                        result = self.groq_reviewer.review_slide_for_fixes(saved_path, slide_name)
                        score = result.get("score", 10)
                        fixes = result.get("fixes", [])
                        
                        logger.info(f"    Iteration {iteration + 1}: Score={score}, Fixes={len(fixes)}")
                        
                        # Log review
                        review_content.append(f"## Slide {slide_idx + 1}: {slide_name} (Iter {iteration + 1})")
                        review_content.append(f"**Score:** {score}/10")
                        if result.get("issues"):
                            for issue in result["issues"][:3]:
                                review_content.append(f"- {issue}")
                        review_content.append("")
                        
                        # Stop if good enough
                        if score >= SCORE_THRESHOLD:
                            logger.info(f"    Score >= {SCORE_THRESHOLD}, stopping optimization")
                            break
                        
                        # Apply fixes
                        if fixes:
                            applied = optimizer.apply_fixes(pptx_path, slide_idx, fixes)
                            if applied:
                                logger.info(f"    Applied {len(fixes)} fixes")
                            else:
                                break  # No fixes applied, stop
                
                review_report_path = company_output_dir / "consultant_review.md"
                with open(review_report_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(review_content))
                
                # Save AFTER Groq review completes
                import shutil
                after_review_path = pptx_path.parent / f"{pptx_path.stem}-after.pptx"
                shutil.copy2(pptx_path, after_review_path)
                logger.info(f"Saved AFTER Groq review: {after_review_path}")
                
                logger.info(f" Review report: {review_report_path}")
                logger.info("[OK] [8/8] Visual Review & Optimization - DONE")
            else:
                logger.info("Skipping visual review (Renderer or API key missing)")
            
            # Get stats
            stats = self.llm.get_stats()
            
            # Summary
            logger.info("\n")
            logger.info("GENERATION COMPLETE")
            logger.info(f"Presentation: {pptx_path}")
            if citations_path:
                logger.info(f"Citations: {citations_path}")
            logger.info(f"Images sourced: {len(images)}")
            logger.info(f"API calls: {stats['total_calls']}")
            logger.info(f"Total tokens: {stats['total_tokens']:,} (In: {stats['total_input_tokens']:,}, Out: {stats['total_output_tokens']:,})")
            
            # Execution duration
            duration = time.time() - start_time
            logger.info(f"Execution time: {duration:.1f}s ({duration/60:.1f}m)")
            
            if compliance_report:
                logger.info(f"Compliance: {compliance_report.overall_score:.1f}%")
                logger.info(f"Status: {'PASSED' if compliance_report.passed else 'FAILED'}")
            
            logger.info("")
            
            # Print image licensing report (Disabled per user request)
            # if images:
            #     logger.info("\n" + self.image_sourcing.get_licensing_report())
            
            return {
                "pptx_path": pptx_path,
                "citations_path": citations_path,
                "images": images,
                "stats": stats,
                "compliance": compliance_report,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"\nPIPELINE FAILED: {e}", exc_info=True)
            return {
                "error": str(e),
                "success": False
            }

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="deckAIn - Investment Teaser Generator")
    parser.add_argument("markdown", help="Path to company OnePager.md file")
    parser.add_argument("--sector", required=True, help="Business sector (Manufacturing, Pharma, Technology, Services)")
    parser.add_argument("--company", help="Company name (for anonymization check)")
    
    args = parser.parse_args()
    
    # Validate inputs
    md_path = Path(args.markdown)
    if not md_path.exists():
        logger.error(f"Markdown file not found: {md_path}")
        sys.exit(1)
    
    valid_sectors = ["Manufacturing", "Pharma", "Technology", "Services", "Logistics", "Healthcare", "Consumer"]
    if args.sector not in valid_sectors:
        logger.warning(f"Unknown sector: {args.sector}. Using anyway...")
    
    # Run pipeline
    pipeline = TeaserPipeline()
    result = pipeline.generate_teaser(
        str(md_path),
        args.sector,
        args.company
    )
    
    if not result["success"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
