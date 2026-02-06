"""
deckAIn - Image Sourcing
Stage 5: Source license-safe images from Unsplash and DuckDuckGo
"""

import requests
from pathlib import Path
import time
from PIL import Image
import io
from typing import List, Dict, Optional

from ddgs import DDGS

from assets.image_compliance import ImageComplianceChecker
from config.prompts import IMAGE_QUERY_GENERATION_PROMPT, FALLBACK_IMAGE_QUERIES
from config.settings import UNSPLASH_ACCESS_KEY, OUTPUT_DIR
from utils.logger import setup_logger, log_stage
from utils.llm_client import GeminiClient

logger = setup_logger(__name__)

class ImageSourcing:
  """
  Source license-safe stock photos for presentation.
  Uses Unsplash API (preferred) and DuckDuckGo fallback.
  """
  
  def __init__(self, company_output_dir: Path = None):
      """
      Initialize image sourcing.
      
      Args:
      company_output_dir: Company-specific output directory for images
      """
      self.llm = None # Will be set by main pipeline
      self.compliance_checker = ImageComplianceChecker()
      self.company_output_dir = company_output_dir or OUTPUT_DIR
      self.images_dir = self.company_output_dir / "images"
      self.sourced_images = []
      self.licensing_info = {}
      logger.info("ImageSourcing initialized")
  
  def source_images(
      self,
      sector: str,
      business_description: str = "",
      products: str = "",
      count: int = 3
      ) -> Dict[str, Dict]:
      """
      Source images for a company.
      
      Args:
      sector: Business sector
      business_description: Actual business description
      products: Products/services offered
      count: Number of images to source
      
      Returns:
      Dictionary mapping image type to {path, license, source}
      """
      log_stage(logger, 5, "Image Sourcing", "START")
      
      # Generate context-specific queries using LLM
      if self.llm and business_description:
          queries = self._generate_image_queries(sector, business_description, products)
      else:
          logger.warning("No LLM client or business context - using fallback queries")
          queries = FALLBACK_IMAGE_QUERIES
      
      logger.info(f"Sourcing {count} images with queries: {queries[:count]}")
      
      images = {}
      
      for idx, query in enumerate(queries[:count]):
          logger.info(f"Searching for: '{query}'")
          
          # Try Unsplash first (if API key available)
          if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_access_key_here":
              image_data = self._source_from_unsplash(query, idx)
              if image_data:
                  images[f"image_{idx + 1}"] = image_data
                  continue
          
          # Fallback to DuckDuckGo
          image_data = self._source_from_duckduckgo(query, idx)
          if image_data:
              images[f"image_{idx + 1}"] = image_data
      
      log_stage(logger, 5, "Image Sourcing", "DONE")
      logger.info(f" Sourced {len(images)} images")
      
      return images
  
  def _generate_image_queries(
      self,
      sector: str,
      business_description: str,
      products: str
      ) -> List[str]:
      """
      Generate relevant image search queries using LLM with enhanced sector intelligence.
      Uses actual product/service names and business specifics for highly targeted queries.
      
      Args:
      sector: Business sector
      business_description: Company business description
      products: Products/services
      
      Returns:
      List of search queries
      """
      try:
          # Enhanced prompt with explicit product extraction
          enhanced_prompt = IMAGE_QUERY_GENERATION_PROMPT.format(
              sector=sector,
              business_description=business_description[:500], # Limit length
              products=products[:500] if products else "Various products/services"
          )
          
          # Add sector-specific context to improve query quality
          sector_hints = {
              "Pharma": "\nFOCUS: APIs, formulations, clean rooms, tablet compression, sterile filling, quality labs",
              "Manufacturing": "\nFOCUS: CNC machining, forging presses, die casting, welding, quality inspection",
              "Technology": "\nFOCUS: developers at work, agile boards, cloud infrastructure, code visualization, modern offices",
              "Services": "\nFOCUS: professional teams, client meetings, service delivery, documentation, consulting"
          }
          
          if sector in sector_hints:
              enhanced_prompt += sector_hints[sector]
          
          logger.info("Calling LLM for intelligent image query generation...")
          response = self.llm.generate_json(enhanced_prompt)
          
          queries = response.get("queries", FALLBACK_IMAGE_QUERIES)
          
          # Ensure we have diverse queries by validating uniqueness
          if len(queries) < 5:
              logger.warning(f"Only got {len(queries)} queries, padding with fallbacks")
              queries.extend(FALLBACK_IMAGE_QUERIES[:5-len(queries)])
          
          # Add slide-specific variants: some wide (for slide 2 bottom), some square (for slide 3/4)
          logger.info(f"[OK] Generated {len(queries)} sector-specific image queries")
          logger.debug(f"Queries: {queries}")
          
          return queries
      
      except Exception as e:
          logger.warning(f"LLM query generation failed: {e}. Using sector fallbacks.")
          return self._get_sector_fallback_queries(sector)
  
  def _get_sector_fallback_queries(self, sector: str) -> List[str]:
      """
      Get intelligent fallback queries based on sector when LLM fails.
      
      Args:
      sector: Business sector
      
      Returns:
      List of sector-specific fallback queries
      """
      sector_queries = {
          "Pharma": [
              "pharmaceutical tablet manufacturing clean room",
              "API synthesis chemical reactor plant",
              "quality control laboratory testing samples",
              "sterile injectable filling production line",
              "pharmaceutical packaging automated equipment"
          ],
          "Manufacturing": [
              "precision CNC machining metal components",
              "industrial forging die press facility",
              "robotic welding assembly line automotive",
              "quality inspection dimensional measurement",
              "modern factory floor production line"
          ],
          "Technology": [
              "software developers coding modern office",
              "agile scrum board team collaboration",
              "cloud server data center infrastructure",
              "software development workspace monitors",
              "technology startup office workspace"
          ],
          "Services": [
              "professional business team meeting",
              "consulting presentation business strategy",
              "customer service support team office",
              "business analytics dashboard screen",
              "corporate office interior modern workspace"
          ]
      }
      
      queries = sector_queries.get(sector, FALLBACK_IMAGE_QUERIES)
      logger.info(f"Using {sector} sector fallback queries")
      return queries
  
  def _source_from_unsplash(self, query: str, index: int) -> Optional[Dict]:
      """
      Source image from Unsplash API (license-safe).
      
      Args:
      query: Search query
      index: Image index
      
      Returns:
      Image data dictionary or None
      """
      try:
          url = "https://api.unsplash.com/photos/random"
          params = {
              "query": query,
              "client_id": UNSPLASH_ACCESS_KEY,
              "orientation": "landscape"
          }
          
          response = requests.get(url, params=params, timeout=10)
          response.raise_for_status()
          
          data = response.json()
          
          # Download image
          image_url = data['urls']['regular']
          download_path = self.images_dir / f"unsplash_{index + 1}.jpg"
          download_path.parent.mkdir(parents=True, exist_ok=True)
          
          img_response = requests.get(image_url, timeout=15)
          img_response.raise_for_status()
          
          with open(download_path, 'wb') as f:
              f.write(img_response.content)
          
          logger.info(f" Downloaded from Unsplash: {download_path.name}")
          
          # Compliance check
          is_compliant, sanitized_path, issues = self.compliance_checker.check_and_sanitize(str(download_path))
          
          # Record licensing
          license_info = {
              "path": sanitized_path if sanitized_path else str(download_path),
              "source": "Unsplash",
              "license": "Unsplash License (Free to use)",
              "photographer": data['user']['name'],
              "url": data['links']['html'],
              "compliance_status": "compliant" if is_compliant else issues,
              "query": query
          }
          
          self.licensing_info[f"image_{index + 1}"] = license_info
          
          return license_info
      
      except Exception as e:
          logger.warning(f"Unsplash sourcing failed: {e}")
          return None
  
  def _source_from_duckduckgo(self, query: str, index: int) -> Optional[Dict]:
      """
      Source image from DuckDuckGo (fallback).
      
      Args:
      query: Search query
      index: Image index
      
      Returns:
      Image data dictionary or None
      """
      try:
          with DDGS() as ddgs:
              results = list(ddgs.images(
                  query,
                  region="wt-wt",
                  safesearch="on",
                  size="Medium",
                  max_results=5
              ))
              
              if not results:
                  logger.warning(f"No images found for query: {query}")
                  return None
              
              # Try first result
              for result in results:
                  try:
                      image_url = result['image']
                      
                      # Download
                      download_path = self.images_dir / f"ddg_{index + 1}.jpg"
                      download_path.parent.mkdir(parents=True, exist_ok=True)
                      
                      img_response = requests.get(image_url, timeout=10)
                      img_response.raise_for_status()
                      
                      with open(download_path, 'wb') as f:
                          f.write(img_response.content)
                      
                      logger.info(f" Downloaded from DuckDuckGo: {download_path.name}")
                      
                      # Compliance check
                      is_compliant, sanitized_path, issues = self.compliance_checker.check_and_sanitize(str(download_path))
                      
                      # If not compliant and has text, try next result
                      if not is_compliant and "Text" in issues:
                          logger.debug(f"Skipping image with text, trying next...")
                          continue
                      
                      # Record licensing
                      license_info = {
                          "path": sanitized_path if sanitized_path else str(download_path),
                          "source": "DuckDuckGo",
                          "license": "Unknown - verify manually",
                          "source_url": result.get('url', ''),
                          "compliance_status": "compliant" if is_compliant else issues,
                          "query": query
                      }
                      
                      self.licensing_info[f"image_{index + 1}"] = license_info
                      
                      return license_info
                  
                  except Exception as e:
                      logger.debug(f"Failed to download image: {e}")
                      continue
              
              logger.warning(f"All images failed for query: {query}")
              return None
      
      except Exception as e:
          logger.warning(f"DuckDuckGo sourcing failed: {e}")
          return None
  
  def get_licensing_report(self) -> str:
      """
      Generate licensing and compliance report.
      
      Returns:
      Formatted report string
      """
      report_lines = ["IMAGE LICENSING REPORT", "=" * 50, ""]
      
      for img_id, info in self.licensing_info.items():
          report_lines.append(f"{img_id.upper()}:")
          report_lines.append(f" Source: {info['source']}")
          report_lines.append(f" License: {info['license']}")
          report_lines.append(f" Compliance: {info['compliance_status']}")
          report_lines.append(f" Query: {info['query']}")
          report_lines.append("")
      
      return "\n".join(report_lines)
