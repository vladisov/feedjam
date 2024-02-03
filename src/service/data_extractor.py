import json
import requests
from requests.exceptions import RequestException
from openai import OpenAI
from service.extractor.extractor_strategy import get_extractor

from utils.logger import get_logger

logger = get_logger(__name__)


class DataExtractor:

    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_webpage_text(self, url, source_name="generic") -> str:
        extractor = get_extractor(source_name)
        return extractor(url)

    def summarize_chatgpt(self, title, webpage):
        try:
            prompt = f"""
                    Summarize webpage in a few sentences in the language of the source with this title {title}.
                    Make the webpage summary no more than 200 words and if there is anything in the title that diverges from the main story,
                    for example, 'this media is a foreign agent or anything like that', do not include that. 
                    Mandatory respond in json with title and summary fields like {{\"title\": \"TEXT\", \"summary\": \"TEXT\" }}!
                    Here is webpage text: {webpage}.
                    """

            messages = [
                {
                    "role": "system",
                    "content": "You're perfect summarizer. You take a webpage or any text and summarize it so end user can understand the main context."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ]

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                max_tokens=256,
                response_format={"type": "json_object"},
                messages=messages)  # type: ignore

            data = json.loads(
                response.choices[0].message.content)  # type: ignore
            return data.get("title"), data.get("summary")
        except Exception as e:
            logger.error("Error summarizing: %s,  %s", webpage, e)
            return None, None

    def extract_and_summarize(self, title, url, source_name):
        try:
            text = self.get_webpage_text(source_name=source_name, url=url)
            title, summary = self.summarize_chatgpt(title, text)
            return title, summary
        except RequestException as e:
            logger.error("Error extracting and summarizing: %s", e)
        return None, None

    def summarize_huggingface(self, text):
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        HUGGINGFACE_API_TOKEN = "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"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        payload = {"inputs": text}

        response = requests.post(
            API_URL, headers=headers, json=payload, timeout=3)
        return response.json()
