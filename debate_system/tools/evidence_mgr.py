"""
Evidence Manager Tool.
Manages the collection, storage, and retrieval of debate evidence.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EVIDENCE_MGR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "manage_evidence",
        "description": "管理辩论证据：存储新证据、检索已有证据、列出所有证据。用于系统性管理辩论中收集的事实和数据。",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["store", "retrieve", "list"],
                    "description": "操作类型：store存储证据，retrieve检索证据，list列出全部证据",
                },
                "evidence": {
                    "type": "object",
                    "description": "要存储的证据（仅action=store时需要）",
                    "properties": {
                        "content": {"type": "string", "description": "证据内容"},
                        "source": {"type": "string", "description": "证据来源"},
                        "category": {"type": "string", "description": "证据分类/标签"},
                        "relevance": {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                },
                "query": {
                    "type": "string",
                    "description": "检索关键词（仅action=retrieve时需要）",
                },
            },
            "required": ["action"],
        },
    },
}


class EvidenceStore:
    """In-memory evidence storage with optional persistence."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.evidence_list: List[Dict[str, Any]] = []
        self.persist_dir = persist_dir
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
            self._load()

    def store(
        self,
        content: str,
        source: str = "unknown",
        category: str = "general",
        relevance: str = "medium",
        side: str = "",
    ) -> Dict[str, Any]:
        """Store a piece of evidence."""
        entry = {
            "id": len(self.evidence_list) + 1,
            "content": content,
            "source": source,
            "category": category,
            "relevance": relevance,
            "side": side,
            "timestamp": datetime.now().isoformat(),
        }
        self.evidence_list.append(entry)
        self._save()
        logger.debug(f"Evidence stored: #{entry['id']} [{category}]")
        return {"status": "stored", "evidence_id": entry["id"], "total_count": len(self.evidence_list)}

    def retrieve(self, query: str = "", category: str = "", side: str = "") -> Dict[str, Any]:
        """Search stored evidence."""
        results = self.evidence_list

        if query:
            query_lower = query.lower()
            results = [
                e
                for e in results
                if query_lower in e["content"].lower()
                or query_lower in e["category"].lower()
                or query_lower in e["source"].lower()
            ]
        if category:
            results = [e for e in results if e["category"] == category]
        if side:
            results = [e for e in results if e["side"] == side]

        return {
            "query": query,
            "count": len(results),
            "evidence": results,
        }

    def list_all(self, side: str = "") -> Dict[str, Any]:
        """List all stored evidence."""
        if side:
            filtered = [e for e in self.evidence_list if e["side"] == side]
        else:
            filtered = self.evidence_list

        return {
            "total_count": len(self.evidence_list),
            "filtered_count": len(filtered),
            "evidence": filtered,
            "categories": list(set(e["category"] for e in self.evidence_list)),
        }

    def _save(self):
        if self.persist_dir:
            path = os.path.join(self.persist_dir, "evidence.json")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.evidence_list, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Failed to save evidence: {e}")

    def _load(self):
        if self.persist_dir:
            path = os.path.join(self.persist_dir, "evidence.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.evidence_list = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load evidence: {e}")


# Global evidence store instance
_evidence_store: Optional[EvidenceStore] = None


def get_evidence_store(persist_dir: Optional[str] = None) -> EvidenceStore:
    """Get or create the global evidence store."""
    global _evidence_store
    if _evidence_store is None:
        _evidence_store = EvidenceStore(persist_dir=persist_dir)
    return _evidence_store


def manage_evidence(
    action: str,
    evidence: Optional[Dict[str, Any]] = None,
    query: str = "",
    side: str = "",
) -> Dict[str, Any]:
    """
    Manage debate evidence: store, retrieve, or list.

    Args:
        action: 'store', 'retrieve', or 'list'.
        evidence: Evidence object (for store).
        query: Search query (for retrieve).
        side: Filter by side (for list/retrieve).

    Returns:
        Result dict.
    """
    store = get_evidence_store()

    if action == "store":
        if not evidence:
            return {"error": "存储操作需要提供evidence参数"}
        return store.store(
            content=evidence.get("content", ""),
            source=evidence.get("source", "unknown"),
            category=evidence.get("category", "general"),
            relevance=evidence.get("relevance", "medium"),
            side=side,
        )
    elif action == "retrieve":
        return store.retrieve(query=query, side=side)
    elif action == "list":
        return store.list_all(side=side)
    else:
        return {"error": f"未知操作: {action}"}
