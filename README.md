# deckAIn

> Automated investment teaser generation from company data — editable PowerPoint decks with native charts, anonymization, and full source citations.

<p align="center">
  <img src="assets/kelp_logo.png" alt="Kelp Branding" height="60" style="background-color: #1a1a2e; padding: 10px 20px; border-radius: 8px;" />
</p>

---

## Overview

deckAIn reads a markdown OnePager with company financials and produces a **5-slide investment teaser** in under 3 minutes. The output is a fully editable `.pptx` with real Excel-backed charts, professional Kelp branding, and a companion citations document that traces every data point back to its source.

### Key Capabilities

| Capability | Description |
|---|---|
| **Native Charts** | Excel-backed bar/line charts via `python-pptx` — click to edit in PowerPoint |
| **Adaptive Extraction** | Works with whatever financial data exists; missing EBITDA or PAT won't break the pipeline |
| **Multi-Sector Intelligence** | Pharma, Manufacturing, Technology, Services, Logistics, Healthcare, Consumer |
| **Auto-Anonymization** | Company names replaced with codenames; verified across all slides |
| **Public Data Fusion** | DuckDuckGo search for market context, trends, and competitive landscape |
| **Image Sourcing** | Unsplash API with compliance checks (logo/text detection via OCR) |
| **Citations** | Every claim maps to a markdown line or web URL in a `.docx` audit trail |
| **Compliance Validation** | Automated checks for chart editability, anonymization, branding, and slide count |

---

## Sample Output

The pipeline generates presentations like this:

| Cover | Business Overview | Financials | Investment Highlights | Disclaimer |
|:---:|:---:|:---:|:---:|:---:|
| Slide 1 | Slide 2 | Slide 3 | Slide 4 | Slide 5 |

Output files per run:
```
output/CompanyName-OnePager/
├── Project_Codename_Investment_Teaser.pptx   # 5-slide presentation
├── Project_Codename_citations.docx           # Source audit trail
├── images/                                    # Sourced photos
└── run_YYYYMMDD_HHMMSS.log                   # Execution log
```

---

## Prerequisites

- **Python 3.10+**
- **Google Gemini API key** (required — free tier is sufficient)
- **Unsplash API key** (optional — improves image quality; DuckDuckGo is the fallback)
- **Groq API key** (optional — enables experimental visual review)

---

## Setup

```bash
cd deckain

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate          # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure API keys
copy .env.example .env               # Windows
# cp .env.example .env               # macOS / Linux
# Then edit .env and add your GOOGLE_API_KEY
```

---

## Usage

```bash
python main.py <markdown_path> --sector <sector> --company <name>
```

| Argument | Required | Description |
|---|---|---|
| `markdown_path` | Yes | Path to the company OnePager `.md` file |
| `--sector` | Yes | Industry — one of: `Pharma`, `Manufacturing`, `Technology`, `Services`, `Logistics`, `Healthcare`, `Consumer` |
| `--company` | No | Original company name (used to verify anonymization) |

### Examples

```bash
# Pharma company
python main.py "..\Company Data\pharma-ind-swift\Ind Swift-OnePager.md" --sector Pharma --company "Ind Swift"

# Logistics company
python main.py "..\Company Data\logistics-gati\Gati-OnePager.md" --sector Logistics --company "gati"

# Technology company
python main.py "..\Company Data\technology-ksolves\Ksolves-OnePager.md" --sector Technology --company "ksolves"

# Entertainment / Services
python main.py "..\Company Data\entertainment-connplex\Connplex Cinemas-OnePager.md" --sector Services --company "connplex"

# Batch generation (all companies)
python batch_generate.py
```

---

## Pipeline Architecture

```
                    ┌─────────────────────────────────────┐
                    │         Company OnePager.md         │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
     │  1. Financial   │  │  2. Chart Spec   │  │  5. Image       │
     │     Extraction  │  │     Generation   │  │     Sourcing    │
     │  (Gemini API)   │  │  (Sector-aware)  │  │  (Unsplash/DDG) │
     └───────┬─────────┘  └───────┬──────────┘  └───────┬─────────┘
             │                    │                     │
             ▼                    │                     │
     ┌─────────────────┐          │                     │
     │  3. Content     │          │                     │
     │     Generation  │◄─────────┘                     │
     │  (Gemini API)   │                                │
     └───────┬─────────┘                                │
             │                                          │
             ▼                                          │
     ┌─────────────────┐                                │
     │  4. Citations   │                                │
     │     Builder     │                                │
     └───────┬─────────┘                                │
             │                                          │
             └───────────────┬──────────────────────────┘
                             ▼
                   ┌──────────────────┐
                   │  6. PPT Assembly │
                   │  (python-pptx)   │
                   └───────┬──────────┘
                           ▼
                   ┌──────────────────┐
                   │  7. Compliance   │
                   │     Validation   │
                   └───────┬──────────┘
                           ▼
                   ┌──────────────────┐
                   │   .pptx + .docx  │
                   └──────────────────┘
```

**7 stages** execute sequentially:

| Stage | Module | What it does |
|:---:|---|---|
| 1 | `extractors/private_data.py` | Uploads markdown to Gemini File API; extracts financials into a flexible Pydantic schema |
| 2 | `generators/chart_data.py` | Builds native chart specs (revenue trend, margin, sector-specific) |
| 3 | `generators/content.py` | Generates slide text, merges private + public data, applies anonymization |
| 4 | `generators/citations.py` | Creates `.docx` linking every claim to markdown lines or web URLs |
| 5 | `assets/image_sourcing.py` | LLM-generated search queries → Unsplash/DuckDuckGo → OCR compliance check |
| 6 | `assemblers/slide_builder.py` | Assembles branded slides with sector-aware layout variants |
| 7 | `validators/compliance.py` | Chart editability, anonymization, branding, citation, and slide count checks |

---

## Project Structure

```
deckain/
├── main.py                     # CLI entry point
├── batch_generate.py           # Run all companies at once
├── requirements.txt            # Python dependencies
├── .env.example                # Template for API keys
│
├── config/                     # Configuration
│   ├── settings.py             # Loads .env, defines paths and colors
│   ├── prompts.py              # LLM prompt templates
│   ├── sector_config.py        # Per-sector KPIs, certs, terminology
│   └── sector_prompts.py       # Sector-specific prompt augmentation
│
├── extractors/                 # Stage 1: Data extraction
│   ├── private_data.py         # Gemini-based financial extraction
│   ├── public_data.py          # DuckDuckGo web scraping
│   ├── markdown_parser.py      # Markdown section parser
│   └── schemas.py              # Pydantic models for all stages
│
├── generators/                 # Stages 2-4: Content creation
│   ├── chart_data.py           # Native chart specifications
│   ├── content.py              # Slide text generation
│   ├── citations.py            # Source documentation builder
│   └── layout_engine.py        # Experimental generative layouts
│
├── assets/                     # Stage 5: Images and icons
│   ├── image_sourcing.py       # Unsplash + DuckDuckGo image search
│   ├── image_compliance.py     # OCR-based logo/text detection
│   ├── icon_helper.py          # SVG → PNG icon management
│   ├── pillow_icons.py         # Pillow-generated icons and cert badges
│   └── icons/                  # Cached SVG/PNG icons
│
├── assemblers/                 # Stage 6: PowerPoint assembly
│   ├── slide_builder.py        # Builds all 5 slides
│   ├── ppt_template.py         # Kelp-branded template (header/footer)
│   ├── native_charts.py        # Excel-backed chart creation
│   └── components.py           # Reusable visual components
│
├── validators/                 # Stage 7: Quality assurance
│   ├── compliance.py           # Automated compliance scoring
│   ├── groq_reviewer.py        # LLM-based visual review (optional)
│   ├── slide_optimizer.py      # Layout adjustments
│   └── visual_reviewer.py      # Slide rendering for review
│
├── utils/                      # Shared utilities
│   ├── llm_client.py           # Gemini API wrapper with retries
│   ├── logger.py               # Structured logging
│   ├── checkpoint.py           # Pipeline checkpoint/resume
│   └── ppt_renderer.py         # Slide → image rendering
│
└── output/                     # Generated presentations
```

---

## Configuration

All settings live in `.env` (copy from `.env.example`):

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3-flash-preview

# Optional — improves image quality
UNSPLASH_ACCESS_KEY=your_unsplash_key

# Optional — visual feedback loop
GROQ_API_KEY=your_groq_key
GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct

# Feature flags
ENABLE_WEB_SEARCH=true
ENABLE_CITATIONS=true
ENABLE_COMPLIANCE_CHECKS=true
ENABLE_GROQ_REVIEW=false
USE_LLM_FOR_SLIDES=false
```

---

## Sector Intelligence

Each sector customizes KPIs, certifications, image queries, and slide terminology:

| Sector | Key Metrics | Certifications | Focus Areas |
|---|---|---|---|
| **Pharma** | ANDA count, R&D spend, export % | WHO-GMP, US FDA, CEP | API portfolio, therapeutic areas, regulatory filings |
| **Manufacturing** | Capacity utilization, facility count | IATF 16949, ISO 9001 | Production lines, quality, automotive/industrial |
| **Technology** | Developer count, ARR, client retention | ISO 27001, CMMI | SaaS metrics, tech stack, platform capabilities |
| **Services** | Client count, geographic reach | ISO 9001, CMMI | Service breadth, customer relationships |
| **Logistics** | Fleet size, ton-km, hub count | ISO 14001, AEO | Network density, utilization, tracking |
| **Healthcare** | Bed count, patient volume | NABH, JCI | Clinical specialties, outcomes |
| **Consumer** | SKU count, D2C %, repeat rate | FSSAI, BIS | Brand portfolio, distribution reach |

---

## Performance

| Metric | Typical Value |
|---|---|
| End-to-end time | 60–120 seconds |
| Gemini API calls | 5–6 per teaser |
| Token usage | 30,000–50,000 total |
| Cost | Free tier sufficient (1,500 req/day) |
| Output | 5 slides + citations `.docx` |

---

## Design Decisions

| Choice | Rationale |
|---|---|
| **Gemini + File API** | Upload markdown once, reuse across prompts — saves tokens |
| **python-pptx** | Creates real PowerPoint objects; charts stay editable |
| **Pydantic schemas** | Type-safe validation with flexible optional fields |
| **DuckDuckGo** | Free web search, no API key required |
| **Unsplash** | License-clear professional photography |
| **Sector configs** | Single source of truth for industry-specific behavior |

---

## License

MIT

---

*Built for the Kelp M&A automation challenge (AI-ML GC IIT Bombay) — Jan - Feb 2026.*
