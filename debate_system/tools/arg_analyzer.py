"""
Argument Structure Analyzer Tool.
Analyzes the structure and quality of debate arguments.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

ARG_ANALYZER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_argument",
        "description": "分析一段辩论论证的结构和质量，包括论点清晰度、论据支持度、逻辑完整性等维度。",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "需要分析的论证文本",
                },
                "role": {
                    "type": "string",
                    "enum": ["正方", "反方", "裁判"],
                    "description": "论证者的角色",
                },
            },
            "required": ["text"],
        },
    },
}


def analyze_argument(text: str, role: str = "unknown") -> Dict[str, Any]:
    """
    Analyze the structure and quality of an argument.

    Args:
        text: The argument text to analyze.
        role: The role of the arguer.

    Returns:
        Dict with analysis results.
    """
    # Structural analysis
    sentences = [s.strip() for s in text.replace("！", "。").replace("？", "。").split("。") if s.strip()]
    word_count = len(text)

    # Detect argument components
    has_claim = any(kw in text for kw in ["我认为", "主张", "观点是", "立场是", "认为", "应该", "必须"])
    has_evidence = any(kw in text for kw in ["根据", "数据", "研究表明", "调查", "统计", "案例", "例如", "比如"])
    has_reasoning = any(kw in text for kw in ["因为", "所以", "因此", "由此可见", "这意味着", "说明"])
    has_rebuttal = any(kw in text for kw in ["但是", "然而", "反对", "驳斥", "不同意", "错误"])

    # Quality metrics
    structure_score = sum([has_claim, has_evidence, has_reasoning, has_rebuttal]) / 4.0

    logger.info(
        f"Argument analysis: {word_count} chars, structure_score={structure_score:.2f}"
    )

    return {
        "word_count": word_count,
        "sentence_count": len(sentences),
        "structure": {
            "has_claim": has_claim,
            "has_evidence": has_evidence,
            "has_reasoning": has_reasoning,
            "has_rebuttal": has_rebuttal,
        },
        "structure_score": round(structure_score, 2),
        "role": role,
        "assessment": _get_assessment(structure_score),
    }


def _get_assessment(score: float) -> str:
    if score >= 0.75:
        return "论证结构完整，包含论点、论据和推理。"
    elif score >= 0.5:
        return "论证结构基本完整，但可在某些维度加强。"
    elif score >= 0.25:
        return "论证结构不够完整，建议增加论据或逻辑推理。"
    else:
        return "论证结构薄弱，缺乏清晰论点或论据支持。"
