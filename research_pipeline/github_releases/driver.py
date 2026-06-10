import urllib.request
import json
import os

def fetch_github_releases(repo):
    # Use the GitHub API for releases
    url = f"https://api.github.com/repos/{repo}/releases"
    # User-Agent is required by GitHub API
    headers = {'User-Agent': 'Hermes-Research-Pipeline-Agent'}
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req) as response:
        # Check rate limits if needed, but for 4 repos it's negligible
        data = json.loads(response.read().decode())
    
    output = []
    # Take latest 2 releases for sample
    for release in data[:2]:
        output.append({
            "repo": repo,
            "tag_name": release.get('tag_name'),
            "published_at": release.get('published_at'),
            "html_url": release.get('html_url')
        })
    return output

if __name__ == "__main__":
    repos = ["BerriAI/litellm", "ollama/ollama", "stanfordnlp/dspy", "ggml-org/llama.cpp"]
    all_data = []
    
    for repo in repos:
        try:
            all_data.extend(fetch_github_releases(repo))
        except Exception as e:
            print(f"Error fetching {repo}: {e}")
            
    output_dir = "/home/jfroh/hermes/harness/research_pipeline/github_releases"
    output_file = os.path.join(output_dir, "sample_output.json")
    
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)
        
    print(f"Sample data written to: {output_file}")
