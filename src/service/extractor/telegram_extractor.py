import requests
from bs4 import BeautifulSoup


def extract_telegram(url: str) -> str:
    response = requests.get(url, timeout=3)
    soup = BeautifulSoup(response.text, "html.parser")

    channel_info = {}
    messages = []

    # Extracting channel information
    channel_title = soup.find("div", class_="tgme_channel_info_header_title")
    if channel_title:
        channel_info["title"] = channel_title.get_text(strip=True)

    channel_description = soup.find("div", class_="tgme_channel_info_description")
    if channel_description:
        channel_info["description"] = channel_description.get_text(strip=True)

    channel_counters = soup.find_all("div", class_="tgme_channel_info_counter")
    for counter in channel_counters:
        counter_type = counter.find("span", class_="counter_type").get_text(strip=True)
        counter_value = counter.find("span", class_="counter_value").get_text(strip=True)
        channel_info[counter_type] = counter_value

    # Extracting messages
    for message in soup.find_all("div", class_="tgme_widget_message"):
        message_content = message.find("div", class_="tgme_widget_message_text")
        if message_content:
            message_text = message_content.get_text(strip=True)
            messages.append(message_text)

    # Assemble extracted data
    extracted_data = {"channel_info": channel_info, "messages": messages}

    return str(extracted_data)
