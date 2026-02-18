"""Web search tool using Tavily API with retry and caching."""

from typing import Optional

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.core.retry import retry_with_backoff
from src.core.exceptions import ExternalServiceError
from src.cache.cache import cached

logger = get_logger(__name__)


@cached(ttl=settings.CACHE_TTL if settings.ENABLE_CACHE else 0, key_prefix="web_search")
@retry_with_backoff(
    max_retries=settings.MAX_RETRIES,
    initial_delay=settings.RETRY_INITIAL_DELAY,
    backoff_factor=settings.RETRY_BACKOFF_FACTOR,
    exceptions=(Exception,),
)
def perform_web_search(
    query: str,
    max_results: Optional[int] = None,
    search_depth: str = "advanced",
) -> str:
    """
    Search the web using Tavily API.

    Returns formatted results as a plain string.
    IMPORTANT: Caller is responsible for placing this in HumanMessage — never SystemMessage.

    Raises:
        ExternalServiceError: If search fails after all retries.
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set — search disabled")
        return "Web search disabled (missing API key)."

    from tavily import TavilyClient

    max_results = max_results or settings.MAX_SEARCH_RESULTS
    client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    logger.info(
        "Web search executing",
        extra={"extra_fields": {"query": query, "max_results": max_results}},
    )

    try:
        response = client.search(query, search_depth=search_depth, max_results=max_results)
    except Exception as e:
        raise ExternalServiceError("Tavily", f"Search request failed: {e}")

    results = response.get("results", [])
    if not results:
        logger.warning(f"No results for query: {query}")
        return "No web search results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] {r.get('title', 'No Title')}\n"
            f"URL: {r.get('url', '')}\n"
            f"Score: {r.get('score', 0):.2f}\n"
            f"Content: {r.get('content', '')}\n"
        )

    logger.info(f"Web search complete: {len(results)} results")
    return "\n---\n".join(lines)


def search_with_fallback(query: str, fallback: str = "Search unavailable.") -> str:
    """Perform web search, returning fallback string on any failure."""
    try:
        return perform_web_search(query)
    except Exception as e:
        logger.warning(f"Search failed, using fallback: {e}")
        return fallback
