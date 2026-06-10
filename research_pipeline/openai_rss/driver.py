import urllib.request
import xml.etree.ElementTree as ET
import json
import os

def fetch_openai_rss():
    feed_url = "https://openai.com/news/rss.xml"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    req = urllib.request.Request(feed_url, headers=headers)
    
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
    
    root = ET.fromstring(xml_data)
    channel = root.find('channel')
    
    output_data = []
    # Find items under channel; ensure channel is found before searching items
    if channel is not None:
        for item in channel.findall('item')[:5]:
            title = item.find('title').text if item.find('title') is not None else "N/A"
            link = item.find('link').text if item.find('link') is not None else "N/A"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
            output_data.append({
                "title": title,
                "link": link,
                "published": pub_date
            })
    
    return output_data

if __name__ == "__main__":
    try:
        data = fetch_openai_rss()
        output_dir = "/home/jfroh/hermes/harness/research_pipeline/openai_rss"
        output_file = os.path.join(output_dir, "sample_output.json")
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Sample data written to: {output_file}")
    except Exception as e:
        print(f"Error fetching RSS: {e}")
