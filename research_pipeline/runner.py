import json
import os
from datetime import datetime

def deduplicate_items(items):
    seen = set()
    deduped = []
    for item in items:
        # Use link/html_url as primary key, fallback to others
        key = item.get('link') or item.get('html_url') or f"{item.get('source')}_{item.get('title')}_{item.get('published')}"
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped

def main():
    # Fetch existing samples from the 3 previous drivers
    samples = []
    sources = ['openai_rss', 'huggingface_blog', 'github_releases']
    for source in sources:
        path = f"/home/jfroh/hermes/harness/research_pipeline/{source}/sample_output.json"
        with open(path, 'r') as f:
            data = json.load(f)
            for item in data:
                item['source'] = source
                samples.append(item)
    
    raw_count = len(samples)
    deduped = deduplicate_items(samples)
    removed = raw_count - len(deduped)
    
    output_dir = "/home/jfroh/hermes/harness/research_pipeline/data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Write combined output
    combined_path = os.path.join(output_dir, "combined_output.json")
    with open(combined_path, 'w') as f:
        json.dump(deduped, f, indent=2)
    
    # Write audit report
    audit_path = os.path.join(output_dir, "audit_report.md")
    with open(audit_path, 'w') as f:
        f.write(f"# Integrated Runner Audit Report\n\n")
        f.write(f"**Timestamp:** {datetime.utcnow().isoformat()}Z\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Raw items fetched: {raw_count}\n")
        f.write(f"- Items after deduplication: {len(deduped)}\n")
        f.write(f"- Duplicates removed: {removed}\n\n")
        f.write(f"## Deduplication Method\n")
        f.write(f"- Primary key: `link` or `html_url` (canonical URL)\n")
        f.write(f"- Fallback key: `source` + `title` + `published` (if available)\n\n")
        f.write(f"## Sources Included\n")
        f.write(f"- OpenAI RSS\n")
        f.write(f"- Hugging Face Blog RSS\n")
        f.write(f"- GitHub Releases API (approved 4 repos)\n\n")
        f.write(f"## Processing Notes\n")
        f.write(f"- Manual command-line execution only.\n")
        f.write(f"- Read-only source access.\n")
        f.write(f"- No automation, scheduling, or persistence added.\n")
        f.write(f"- No credentials, API keys, or secrets used.\n")
    
    print(f"Pipeline run complete. Results: {len(deduped)} items.")
    print(f"Raw: {raw_count}, Deduped: {len(deduped)}, Removed: {removed}")

if __name__ == "__main__":
    main()
