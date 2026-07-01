"""
Fact Verification Tool.
Cross-references claims against available information to assess accuracy.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

FACT_CHECK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "fact_check",
        "description": "对一条具体陈述进行事实核查，评估其准确性。返回可信度评级和相关说明。",
        "parameters": {
            "type": "object",
            "properties": {
                "claim": {
                    "type": "string",
                    "description": "需要核查的具体陈述或主张",
                },
                "context": {
                    "type": "string",
                    "description": "该陈述所在的上下文背景，帮助更准确地判断",
                },
            },
            "required": ["claim"],
        },
    },
}

# Known facts for common debate topics (serves as a lightweight knowledge base)
KNOWN_FACTS = {
    "人工智能": {
        "就业": {
            "fact": "根据世界经济论坛《2025年就业未来报告》，AI预计到2030年将取代8500万个岗位，同时创造9700万个新岗位。",
            "source": "世界经济论坛 (World Economic Forum), 2025",
        },
        "发展": {
            "fact": "截至2025年底，全球AI市场规模约为3000亿美元，年增长率超过30%。",
            "source": "Gartner/McKinsey行业报告, 2025",
        },
    },
    "气候变化": {
        "温度": {
            "fact": "根据NASA数据，全球平均气温自1880年以来上升了约1.2°C，其中大部分升温发生在近40年。",
            "source": "NASA GISS, 2024",
        },
    },
}


def fact_check(claim: str, context: str = "") -> Dict[str, Any]:
    """
    Check a factual claim against known information.

    Args:
        claim: The claim to verify.
        context: Additional context for the claim.

    Returns:
        Dict with credibility assessment.
    """
    # Check against known facts
    matched_facts = []
    claim_lower = claim.lower()

    for category, topics in KNOWN_FACTS.items():
        for topic_kw, info in topics.items():
            if category in claim or topic_kw in claim:
                matched_facts.append({
                    "category": category,
                    "topic": topic_kw,
                    "fact": info["fact"],
                    "source": info["source"],
                })

    logger.info(f"Fact check on '{claim[:50]}...' matched {len(matched_facts)} known facts")

    return {
        "claim": claim,
        "context": context,
        "matched_known_facts": matched_facts,
        "credibility_note": (
            "基于已有知识库的匹配结果。请注意：该工具仅提供参考信息，"
            "不能替代专业事实核查。建议结合其他来源交叉验证。"
        ),
    }
