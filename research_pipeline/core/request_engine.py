import urllib.request
import json

class RequestEngine:
    @staticmethod
    def fetch_url(url):
        headers = {'User-Agent': 'Hermes-Research-Pipeline-Agent'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read()