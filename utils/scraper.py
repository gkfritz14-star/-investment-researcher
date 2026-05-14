"""
Web scraping utilities for extracting raw page content from plan/fund websites.
"""

import requests
from bs4 import BeautifulSoup
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_page(url: str, timeout: int = 15) -> dict:
    """
    Fetch a URL and return cleaned text + metadata.
    Returns dict with keys: url, title, raw_text, error
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, footer, scripts, styles
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else url

        # Get main content area if available
        main = soup.find("main") or soup.find(id="main") or soup.find(class_="content") or soup.body
        raw_text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

        # Collapse excessive whitespace
        raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
        raw_text = re.sub(r" {2,}", " ", raw_text)

        # Truncate to avoid hitting context limits (keep first ~8000 chars)
        if len(raw_text) > 8000:
            raw_text = raw_text[:8000] + "\n\n[... content truncated ...]"

        return {
            "url": url,
            "title": title_text,
            "raw_text": raw_text,
            "error": None,
        }

    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "title": "",
            "raw_text": "",
            "error": str(e),
        }


def baseline_extract_names(raw_text: str) -> list[str]:
    """
    BASELINE METHOD: Simple heuristic name extraction without AI.
    Looks for capitalized word pairs (FirstName LastName patterns).
    This is what we compare the AI approach against.
    """
    # Pattern: Two or more capitalized words in a row (simple name heuristic)
    pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
    candidates = re.findall(pattern, raw_text)

    # Filter out common non-name phrases
    stop_phrases = {
        "Investment Committee", "Board Of", "Annual Report", "Chief Investment",
        "Managing Director", "Vice President", "New York", "United States",
        "Executive Director", "Portfolio Manager", "Asset Management",
        "Private Equity", "Fixed Income", "Real Estate", "Fund Manager",
        "Senior Vice", "Executive Vice", "General Counsel", "Chief Financial",
        "Chief Executive", "Investment Officer", "Investment Manager",
    }

    seen = set()
    names = []
    for c in candidates:
        c = c.strip()
        if c not in stop_phrases and c not in seen and len(c.split()) >= 2:
            seen.add(c)
            names.append(c)

    return names[:20]  # cap at 20
