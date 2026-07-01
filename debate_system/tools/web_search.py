"""
Web Search Tool using DuckDuckGo.
Allows agents to search the web for evidence and facts.
"""

import logging
import warnings
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Tool schema for LLM function calling
WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "搜索互联网获取与辩题相关的信息、数据、案例和专家观点。用于查找支持论据的事实和数据。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，应精确描述要查找的内容",
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回结果的最大数量，默认5",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        Dict with 'results' list and 'query' info.
    """
    # Try new package name first, fall back to old one
    DDGS = None
    try:
        from ddgs import DDGS  # new package name
    except ImportError:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                from duckduckgo_search import DDGS  # old package name
        except ImportError:
            pass

    if DDGS is None:
        logger.warning("DuckDuckGo search not available, using mock search")
        return _mock_search(query, max_results)

    try:
        results = []
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))
            for r in search_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

        return {
            "query": query,
            "total_results": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"query": query, "error": str(e), "results": []}


def _mock_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Fallback mock search for when DuckDuckGo is unavailable."""
    return {
        "query": query,
        "total_results": 0,
        "results": [],
        "note": "搜索功能暂时不可用（duckduckgo-search未安装），请基于已有知识进行辩论。",
    }
