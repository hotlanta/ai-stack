# =============================================================================
# DeerFlow — SearXNG Search Tool Wrapper
#
# Drop this file at:
#   deer-flow/backend/src/community/searxng/tools.py
#
# Then in config.yaml set:
#   tools:
#     - name: web_search
#       group: web
#       use: src.community.searxng.tools:web_search_tool
#
# And in .env set:
#   SEARXNG_URL=http://host.docker.internal:8080
# =============================================================================

import os
import requests
from langchain_core.tools import tool


SEARXNG_URL = os.getenv("SEARXNG_URL", "http://host.docker.internal:8080")
DEFAULT_MAX_RESULTS = int(os.getenv("SEARXNG_MAX_RESULTS", "5"))
REQUEST_TIMEOUT = int(os.getenv("SEARXNG_TIMEOUT", "10"))


@tool
def web_search_tool(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> str:
    """Search the web using a local SearXNG instance.

    Args:
        query:       The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        Formatted string of search results with title, URL, and snippet.
        Returns an error message string if SearXNG is unreachable.
    """
    params = {
        "q": query,
        "format": "json",
        "engines": "google,duckduckgo,bing",
        "language": "en",
        "safesearch": "0",
    }

    try:
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        return (
            f"[SearXNG unavailable] Could not connect to {SEARXNG_URL}. "
            "Check that SearXNG is running and SEARXNG_URL is correct in .env."
        )
    except requests.exceptions.Timeout:
        return (
            f"[SearXNG timeout] Request to {SEARXNG_URL} timed out after "
            f"{REQUEST_TIMEOUT}s. SearXNG may be overloaded."
        )
    except requests.exceptions.HTTPError as e:
        return f"[SearXNG HTTP error] {e}"

    try:
        data = response.json()
    except ValueError:
        return "[SearXNG error] Response was not valid JSON. Check SearXNG settings.yml has 'json' in formats."

    results = data.get("results", [])

    if not results:
        return f"[SearXNG] No results found for query: '{query}'"

    formatted = []
    for r in results[:max_results]:
        title   = r.get("title", "No title").strip()
        url     = r.get("url", "").strip()
        snippet = r.get("content", "No snippet available").strip()
        formatted.append(f"**{title}**\n{url}\n{snippet}")

    return "\n\n".join(formatted)
