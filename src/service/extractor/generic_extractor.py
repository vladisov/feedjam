import re

import requests
from bs4 import BeautifulSoup


def extract_generic(url: str) -> str:
    try:
        response = requests.get(url, timeout=3)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()

        # Extract content from <script> tags if needed
        script_content = ""
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                script_content += script.string + " "

        # Focus on main content area
        main_content = (
            soup.find("main") or soup.find("article") or soup.find("div", class_="content")
        )
        if not main_content:
            main_content = soup  # Fallback to the entire soup if specific main content not found

        # Extract and concatenate text from all visible elements
        texts = []
        for element in main_content.find_all(text=True):  # type: ignore
            if element.parent.name not in ["style", "script", "[document]", "head", "title"]:
                texts.append(element.strip())

        article_text = " ".join(texts)

        # Remove any residual scripts or non-text content
        cleaned_article_text = re.sub(r"\s+", " ", article_text)

        return script_content + cleaned_article_text
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return ""
    except Exception as e:
        print(f"Error extracting content: {e}")
        return ""
