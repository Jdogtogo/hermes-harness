# Integrated Runner Audit Report

**Timestamp:** 2026-06-10T13:20:14.306850Z

## Summary
- Raw items fetched: 18
- Items after deduplication: 18
- Duplicates removed: 0

## Deduplication Method
- Primary key: `link` or `html_url` (canonical URL)
- Fallback key: `source` + `title` + `published` (if available)

## Sources Included
- OpenAI RSS
- Hugging Face Blog RSS
- GitHub Releases API (approved 4 repos)

## Processing Notes
- Manual command-line execution only.
- Read-only source access.
- No automation, scheduling, or persistence added.
- No credentials, API keys, or secrets used.
