from tavily import TavilyClient
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("tool.web_search")

def perform_web_search(query: str) -> str:
    """
    Searches the web using Tavily API.
    Handles errors gracefully.
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("Search disabled: No API key found.")
        return "Search functionality is disabled (Missing API Key)."

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # 'advanced' depth is better for research
        response = client.search(query, search_depth="advanced", max_results=3)
        
        results = []
        for result in response.get('results', []):
            title = result.get('title', 'No Title')
            content = result.get('content', 'No Content')
            url = result.get('url', '#')
            results.append(f"Source: {title} ({url})\nSummary: {content}\n")
            
        return "\n---\n".join(results)
        
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return f"Error performing search: {str(e)}"