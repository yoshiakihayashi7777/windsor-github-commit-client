# GitHub Commit Client

A small Python client for retrieving and normalizing paginated commits from the GitHub REST API.

## Endpoint

```text
https://api.github.com/repos/torvalds/linux/commits
```

## Requirements

- Ubuntu
- Python 3.12+
- `requests`
- `pytest`

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

```bash
python example.py
```

The example fetches three pages with up to 100 commits per page:

```python
client.iter_commits(
    "torvalds",
    "linux",
    pages=3,
    per_page=100,
)
```

Each commit is normalized into:

```python
{
    "sha": "...",
    "author_name": "...",
    "author_email": "...",
    "date": "...",
    "message": "...",
}
```

## Implementation

The client:

- Supports pagination using `page` and `per_page`
- Validates `per_page` from 1 to 100
- Uses an iterator to process commits efficiently
- Uses `requests.Session` for shared headers and authentication
- Applies request timeouts
- Retries network failures with exponential backoff
- Detects genuine GitHub rate-limit responses
- Uses `X-RateLimit-Reset` when available
- Does not retry ordinary `403 Forbidden` responses
- Raises `GitHubClientError` for unsuccessful requests

## Testing

Run:

```bash
python -m pytest -q
```

Expected result:

```text
3 passed
```

Tests cover pagination, normalization, rate-limit retries, and ordinary forbidden responses.

## Manual verification

The client was tested successfully against the live GitHub endpoint and fetched multiple pages of Linux kernel commits.

## Assessment timing

- Start: 30 September 2026, 05:44 PM Europe/Kyiv
- End: 30 September 2026, 06:13 PM Europe/Kyiv
- Duration: 29 minutes

## Git history

The project was developed through incremental commits.

```text
* 7e04011 (HEAD -> main) Add real GitHub API usage example
* 96e43fa Add pagination and rate limit tests
* lc85e23 Initialize project and implement GitHub client
```

## License

This project was created as part of a technical assessment.