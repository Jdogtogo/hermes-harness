import xml.etree.ElementTree as ET
import json
from research_pipeline.core.request_engine import RequestEngine

class OpenAI_RSS_Fetcher:
    def fetch(self):
        xml_data = RequestEngine.fetch_url("https://openai.com/news/rss.xml")
        root = ET.fromstring(xml_data)
        output = []
        for item in root.find('channel').findall('item')[:2]:
            output.append({
                "source": "OpenAI",
                "title": item.find('title').text,
                "link": item.find('link').text
            })
        return output

class HF_Blog_RSS_Fetcher:
    def fetch(self):
        xml_data = RequestEngine.fetch_url("https://huggingface.co/blog/feed.xml")
        root = ET.fromstring(xml_data)
        output = []
        for item in root.find('channel').findall('item')[:2]:
            output.append({
                "source": "Hugging Face Blog",
                "title": item.find('title').text,
                "link": item.find('link').text
            })
        return output

class GitHub_Releases_Fetcher:
    def fetch(self):
        repos = ["BerriAI/litellm", "ollama/ollama", "stanfordnlp/dspy", "ggml-org/llama.cpp"]
        output = []
        for repo in repos:
            data = json.loads(RequestEngine.fetch_url(f"https://api.github.com/repos/{repo}/releases"))
            if data and isinstance(data, list):
                output.append({
                    "source": "GitHub",
                    "repo": repo,
                    "tag_name": data[0].get('tag_name'),
                    "html_url": data[0].get('html_url')
                })
        return output