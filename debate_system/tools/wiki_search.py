"""
Wikipedia Search Tool.
Allows agents to retrieve encyclopedic knowledge for debate evidence.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

WIKI_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "wiki_search",
        "description": "搜索维基百科获取客观的百科知识、定义、历史背景和统计数据。适用于获取中立的事实信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要在维基百科搜索的关键词或概念",
                },
                "language": {
                    "type": "string",
                    "description": "语言代码，默认'zh'（中文）",
                    "default": "zh",
                },
            },
            "required": ["query"],
        },
    },
}


def wiki_search(query: str, language: str = "zh") -> Dict[str, Any]:
    """
    Search Wikipedia for information.

    Args:
        query: Search query.
        language: Wikipedia language code.

    Returns:
        Dict with summary, url, and related info.
    """
    try:
        import wikipedia

        wikipedia.set_lang(language)

        # Search for pages
        search_results = wikipedia.search(query, results=3)
        if not search_results:
            return {"query": query, "found": False, "summary": "未找到相关条目。", "url": ""}

        results = []
        for title in search_results[:3]:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                results.append({
                    "title": page.title,
                    "summary": page.summary[:500],
                    "url": page.url,
                })
            except wikipedia.DisambiguationError as e:
                results.append({
                    "title": title,
                    "summary": f"消岐义页面，可能的选项: {e.options[:5]}",
                    "url": "",
                })
            except Exception as e:
                logger.warning(f"Error fetching Wikipedia page '{title}': {e}")
                continue

        logger.info(f"Wiki search for '{query}' found {len(results)} pages")
        return {
            "query": query,
            "found": len(results) > 0,
            "pages": results,
        }
    except ImportError:
        logger.warning("wikipedia not installed, using mock")
        return {
            "query": query,
            "found": False,
            "pages": [],
            "note": "维基百科功能暂时不可用。",
        }
    except Exception as e:
        logger.error(f"Wiki search error: {e}")
        return {"query": query, "found": False, "error": str(e), "pages": []}
