"""
Logical Fallacy Detection Tool.
Analyzes arguments to identify common logical fallacies.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

FALLACY_DETECT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "detect_fallacy",
        "description": "分析一段论证，识别其中可能存在的逻辑谬误。返回谬误类型和解释。",
        "parameters": {
            "type": "object",
            "properties": {
                "argument": {
                    "type": "string",
                    "description": "需要分析的一段论证文本",
                },
                "context": {
                    "type": "string",
                    "description": "该论证所处的辩论上下文",
                },
            },
            "required": ["argument"],
        },
    },
}

# Common logical fallacies and their detection patterns
FALLACIES = [
    {
        "name": "稻草人谬误",
        "en_name": "Straw Man",
        "description": "歪曲对方的观点，使其更容易被攻击",
        "keywords": ["歪曲", "曲解", "夸大对方的", "你说的意思是"],
    },
    {
        "name": "滑坡谬误",
        "en_name": "Slippery Slope",
        "description": "声称一个小的第一步必然导致一系列连锁的负面事件",
        "keywords": ["必然导致", "一旦...就会", "最终会", "一步步走向"],
    },
    {
        "name": "诉诸情感",
        "en_name": "Appeal to Emotion",
        "description": "用情感操控代替理性论证",
        "keywords": ["你难道不觉得", "所有人都认为", "这是不道德的"],
    },
    {
        "name": "虚假二分",
        "en_name": "False Dichotomy",
        "description": "将复杂问题简化为非此即彼的两个选项",
        "keywords": ["只有两种可能", "要么...要么", "非黑即白"],
    },
    {
        "name": "诉诸权威",
        "en_name": "Appeal to Authority",
        "description": "仅凭某权威人物的观点作为论据，而非基于事实和逻辑",
        "keywords": ["某专家说", "权威认为", "名人认为"],
    },
    {
        "name": "以偏概全",
        "en_name": "Hasty Generalization",
        "description": "基于不充分的样本做出广泛结论",
        "keywords": ["所有", "从不", "总是", "无一例外"],
    },
    {
        "name": "循环论证",
        "en_name": "Circular Reasoning",
        "description": "用结论本身来证明结论",
        "keywords": ["因为...所以...因为"],
    },
    {
        "name": "人身攻击",
        "en_name": "Ad Hominem",
        "description": "攻击对方个人而非其论点",
        "keywords": ["你这个人", "你不懂", "你没资格"],
    },
]


def detect_fallacy(argument: str, context: str = "") -> Dict[str, Any]:
    """
    Analyze an argument for logical fallacies.

    Args:
        argument: The argument text to analyze.
        context: Debate context.

    Returns:
        Dict with detected fallacies.
    """
    detected = []

    for fallacy in FALLACIES:
        score = 0
        matched_keywords = []
        for kw in fallacy["keywords"]:
            if kw in argument:
                score += 1
                matched_keywords.append(kw)
        if score > 0:
            detected.append({
                "fallacy_name": fallacy["name"],
                "fallacy_en": fallacy["en_name"],
                "description": fallacy["description"],
                "confidence": min(score / len(fallacy["keywords"]), 1.0),
                "matched_patterns": matched_keywords,
            })

    logger.info(f"Fallacy detection found {len(detected)} potential fallacies")

    return {
        "argument_preview": argument[:200],
        "detected_fallacies": detected,
        "total_found": len(detected),
        "note": (
            "逻辑谬误检测基于关键词匹配，仅供参考。"
            "高得分并不意味着该论证一定包含谬误，请结合上下文判断。"
        ),
    }
