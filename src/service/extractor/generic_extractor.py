import re

import requests
from bs4 import BeautifulSoup

from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; FeedJam/1.0; +https://feedjam.app)'
}

MAX_CONTENT_LENGTH = 5000


def extract_generic(url: str) -> str:
    """Extract main text content from a URL."""
    try:
        response = requests.get(url, timeout=5, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()

        main_content = (
            soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup
        )

        texts = [
            element.strip()
            for element in main_content.find_all(text=True)  # type: ignore
            if element.parent.name not in ["style", "script", "[document]", "head", "title"]
        ]

        article_text = " ".join(texts)
        cleaned_text = re.sub(r"\s+", " ", article_text).strip()

        return cleaned_text[:MAX_CONTENT_LENGTH]
    except requests.RequestException as e:
        logger.warning(f"Request error fetching {url}: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Error extracting content from {url}: {e}")
        return ""
