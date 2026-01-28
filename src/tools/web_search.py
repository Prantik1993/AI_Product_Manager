"""Enhanced web search with retry logic, caching, and metrics.

Provides robust web search functionality using Tavily API with:
- Automatic retry with exponential backoff
- Result caching to reduce API calls
- Metrics tracking for monitoring
- Graceful error handling
"""

from tavily import TavilyClient
from typing import Optional

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.core.retry import retry_with_backoff
from src.core.exceptions import ExternalServiceError
from src.cache.cache import cached
from src.monitoring.metrics import increment_counter, track_execution_time

logger = get_logger(__name__)


@cached(ttl=settings.CACHE_TTL if settings.ENABLE_CACHE else 0, key_prefix="web_search")
@retry_with_backoff(
    max_retries=settings.MAX_RETRIES,
    initial_delay=settings.RETRY_INITIAL_DELAY,
    backoff_factor=settings.RETRY_BACKOFF_FACTOR,
    exceptions=(Exception,),
)
@track_execution_time("web_search")
def perform_web_search(
    query: str,
    max_results: Optional[int] = None,
    search_depth: str = "advanced"
) -> str:
    """
    Searches the web using Tavily API with retry and caching.

    Args:
        query: Search query string
        max_results: Maximum number of results (default: from settings)
        search_depth: Search depth ('basic' or 'advanced')

    Returns:
        Formatted search results as a string

    Raises:
        ExternalServiceError: If search fails after retries
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("Search disabled: No API key found")
        increment_counter("web_search_disabled", 1.0)
        return "Search functionality is disabled (Missing API Key)."

    max_results = max_results or settings.MAX_SEARCH_RESULTS

    try:
        logger.info(
            "Performing web search",
            extra={
                "extra_fields": {
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                }
            },
        )

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        # Perform search with configured parameters
        response = client.search(
            query,
            search_depth=search_depth,
            max_results=max_results
        )

        # Parse and format results
        results = []
        for idx, result in enumerate(response.get('results', []), 1):
            title = result.get('title', 'No Title')
            content = result.get('content', 'No Content')
            url = result.get('url', '#')
            score = result.get('score', 0.0)

            results.append(
                f"[{idx}] {title}\n"
                f"URL: {url}\n"
                f"Relevance: {score:.2f}\n"
                f"Summary: {content}\n"
            )

        if not results:
            logger.warning(f"No search results found for query: {query}")
            increment_counter("web_search_no_results", 1.0)
            return "No search results found."

        formatted_results = "\n---\n".join(results)

        logger.info(
            f"Web search completed successfully",
            extra={
                "extra_fields": {
                    "query": query,
                    "results_count": len(results),
                }
            },
        )
        increment_counter("web_search_success", 1.0)

        return formatted_results

    except Exception as e:
        logger.error(
            f"Tavily search failed: {e}",
            extra={
                "extra_fields": {
                    "query": query,
                    "error": str(e),
                }
            },
        )
        increment_counter("web_search_error", 1.0)
        raise ExternalServiceError("Tavily", f"Search failed: {str(e)}")


def search_with_fallback(query: str, fallback_message: str = "Search unavailable") -> str:
    """
    Perform web search with fallback message on failure.

    Args:
        query: Search query
        fallback_message: Message to return if search fails

    Returns:
        Search results or fallback message
    """
    try:
        return perform_web_search(query)
    except Exception as e:
        logger.warning(f"Search failed, using fallback: {e}")
        return fallback_message