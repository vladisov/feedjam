import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import openai

from utils.logger import get_logger

logger = get_logger(__name__)


class DataExtractor:

    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = self.api_key

    def get_webpage_text(self, url):
        response = requests.get(url, timeout=3)
        soup = BeautifulSoup(response.text, 'html.parser')

        for element in soup(['style', 'header', 'footer', 'nav', '[document]']):
            element.extract()

        for script in soup(["script"]):
            if script.get("type") is not None and script.get("type").startswith("application"):
                continue
            else:
                script.extract()

        all_text = ' '.join(soup.stripped_strings) + ' ' + ' '.join(
            script.string for script in soup.find_all("script", type="application/ld+json") if script.string
        ) + ' '.join(
            meta.get("content") for meta in soup.find_all("meta") if meta.get("content") is not None
        )

        return all_text

    def summarize_chatgpt(self,  text):
        prompt = f"nSummarize this webpage in few sentences in the language of source, make it comprehensible for end user:\n{text}"
        response = openai.Completion.create(
            engine="text-davinci-003", prompt=prompt, max_tokens=300)

        return response.choices[0].text.strip()  # type: ignore

    def extract_and_summarize(self, url):
        try:
            text = self.get_webpage_text(url)
            summary = self.summarize_chatgpt(text)
            return summary
        except RequestException as e:
            logger.error("Error extracting and summarizing: %s", e)
        return None

    def summarize_huggingface(self, text):
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        HUGGINGFACE_API_TOKEN = "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"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        payload = {"inputs": text}

        response = requests.post(
            API_URL, headers=headers, json=payload, timeout=3)
        return response.json()
