"""
deckAIn - Investment Teaser Generator
Configuration and settings management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")
OUTPUT_DIR.mkdir(exist_ok=True)

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")  # User must set in .env
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Default to 90b vision (11b preview decommissioned) - verify on Groq console
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# Feature Flags
ENABLE_GROQ_REVIEW = os.getenv("ENABLE_GROQ_REVIEW", "false").lower() == "true"
USE_LLM_FOR_SLIDES = os.getenv("USE_LLM_FOR_SLIDES", "false").lower() == "true"

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
if not GEMINI_MODEL:
    raise ValueError("GEMINI_MODEL not found in environment variables. Set in .env (e.g., gemini-2.0-flash-exp)")

# Kelp Brand Colors (per Problem Statement Attachment A)
KELP_COLORS = {
    # Primary (Covers/Overlays) - Dark Indigo/Violet
    "primary_dark": "#1A237E",       # Dark Indigo (title bars, headers)
    "primary_indigo": "#303F9F",     # Slightly lighter indigo for accents
    # Secondary (Accents) - Pink-to-Orange Gradient & Cyan
    "gradient_pink": "#FF4B91",      # Pink (gradient start)
    "gradient_orange": "#FF7A3D",    # Orange (gradient end)
    "gradient_purple": "#8B5CF6",    # Purple for variety
    "cyan_blue": "#00D4FF",          # Cyan Blue (icons/accents)
    # Background
    "background_light": "#FFFFFF",   # White (content slides)
    # Text
    "text_light": "#FFFFFF",         # White text (on dark)
    "text_dark": "#333333",          # Dark grey (on light backgrounds)
    "text_body": "#4A5568",          # Medium grey body text
    # Charts & Cards
    "chart_accent": "#5C6BC0",       # Indigo accent for charts
    "card_bg": "#F8FAFC",            # Subtle off-white for cards
    "card_border": "#E2E8F0",        # Light border for cards
    "success_green": "#10B981",      # For positive metrics
    "accent_gold": "#F59E0B",        # Gold accent
}

# Footer text (exact as per spec)
KELP_FOOTER_TEXT = "Strictly Private & Confidential – Prepared by Kelp M&A Team"

# Typography
KELP_FONT_HEAD = "Arial"  # Or "Aptos" if available
KELP_FONT_BODY = "Arial"

# Feature flags
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
ENABLE_CITATIONS = os.getenv("ENABLE_CITATIONS", "true").lower() == "true"
ENABLE_COMPLIANCE_CHECKS = os.getenv("ENABLE_COMPLIANCE_CHECKS", "true").lower() == "true"

# Performance settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "120"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security settings
SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "30"))
ALLOWED_IMPORTS = os.getenv("ALLOWED_IMPORTS", "pandas,numpy,re,json,datetime").split(",")

# Validation
assert KELP_COLORS["primary_dark"].startswith("#"), "Colors must be hex format"
assert MAX_RETRIES > 0, "MAX_RETRIES must be positive"
assert API_TIMEOUT > 0, "API_TIMEOUT must be positive"
