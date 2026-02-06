"""
Batch Generate Investment Teasers for Multiple Companies
Run this to process all companies in the Company Data folder
"""

import sys
from pathlib import Path
from main import DeckAInPipeline
from utils.logger import setup_logger

logger = setup_logger(__name__)

def batch_generate():
    """Process all company one-pagers in Company Data directory"""
    
    # Company data directory
    company_data_dir = Path(__file__).parent.parent / "Company Data"
    
    if not company_data_dir.exists():
        logger.error(f"Company Data directory not found: {company_data_dir}")
        return
    
    # Find all company folders
    company_folders = [f for f in company_data_dir.iterdir() if f.is_dir()]
    
    logger.info(f"Found {len(company_folders)} company folders")
    logger.info("="*80)
    
    results = []
    
    for idx, company_folder in enumerate(company_folders, 1):
        # Find the OnePager markdown file
        onepager_files = list(company_folder.glob("*-OnePager.md"))
        
        if not onepager_files:
            logger.warning(f"[{idx}/{len(company_folders)}] No OnePager found in {company_folder.name}, skipping...")
            continue
        
        onepager_path = onepager_files[0]
        
        # Infer sector from folder name
        sector_map = {
            "technology": "Technology",
            "automotive": "Automotive",
            "pharma": "Pharma",
            "logistics": "Logistics",
            "electronics": "Electronics",
            "entertainment": "Entertainment",
            "manufacturing": "Manufacturing"
        }
        
        sector = "Default"
        for key, value in sector_map.items():
            if key in company_folder.name.lower():
                sector = value
                break
        
        logger.info(f"\n[{idx}/{len(company_folders)}] Processing: {company_folder.name}")
        logger.info(f"  File: {onepager_path.name}")
        logger.info(f"  Sector: {sector}")
        logger.info("-"*80)
        
        try:
            # Initialize pipeline
            pipeline = DeckAInPipeline()
            
            # Run generation
            output_path = pipeline.run(
                company_file=str(onepager_path),
                sector=sector
            )
            
            results.append({
                "company": company_folder.name,
                "status": "SUCCESS",
                "output": output_path
            })
            
            logger.info(f"[OK] SUCCESS: {output_path}")
            
        except Exception as e:
            logger.error(f"[FAIL] FAILED: {company_folder.name} - {str(e)}")
            results.append({
                "company": company_folder.name,
                "status": "FAILED",
                "error": str(e)
            })
    
    # Summary Report
    logger.info("\n" + "="*80)
    logger.info("BATCH GENERATION SUMMARY")
    logger.info("="*80)
    
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    
    logger.info(f"Total Processed: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info("\n[OK] Successful Generations:")
        for r in successful:
            logger.info(f"  - {r['company']}")
    
    if failed:
        logger.info("\n[FAIL] Failed Generations:")
        for r in failed:
            logger.info(f"  - {r['company']}: {r.get('error', 'Unknown error')}")
    
    logger.info("="*80)

if __name__ == "__main__":
    batch_generate()
