"""
Download Bootstrap Icons as PNG for use in PPTX.
"""

import requests
from pathlib import Path

ICONS_DIR = Path(__file__).parent / "icons"
ICONS_DIR.mkdir(exist_ok=True)

# Bootstrap Icons - download SVG and we'll use them as fallback
# For PPTX, we need PNG so we'll use a simple placeholder approach
ICON_URLS = {
    "building": "https://raw.githubusercontent.com/twbs/icons/main/icons/building.svg",
    "bar-chart": "https://raw.githubusercontent.com/twbs/icons/main/icons/bar-chart-fill.svg",
    "trophy": "https://raw.githubusercontent.com/twbs/icons/main/icons/trophy-fill.svg",
    "globe": "https://raw.githubusercontent.com/twbs/icons/main/icons/globe.svg",
    "gear": "https://raw.githubusercontent.com/twbs/icons/main/icons/gear-fill.svg",
    "people": "https://raw.githubusercontent.com/twbs/icons/main/icons/people-fill.svg",
    "graph-up": "https://raw.githubusercontent.com/twbs/icons/main/icons/graph-up-arrow.svg",
    "check-circle": "https://raw.githubusercontent.com/twbs/icons/main/icons/check-circle-fill.svg",
    "cash-coin": "https://raw.githubusercontent.com/twbs/icons/main/icons/cash-coin.svg",
    "shield-check": "https://raw.githubusercontent.com/twbs/icons/main/icons/shield-check.svg",
}

def download_icons():
    """Download icons from Bootstrap Icons repo."""
    for name, url in ICON_URLS.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                svg_path = ICONS_DIR / f"{name}.svg"
                svg_path.write_text(response.text)
                print(f"Downloaded: {name}.svg")
        except Exception as e:
            print(f"Failed: {name} - {e}")

if __name__ == "__main__":
    download_icons()
