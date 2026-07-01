"""
Multi-Agent Communication Protocol for Structured Debate System.

Defines the formal message format and MessageBus for inter-agent
communication. This is the central design element for G02's core
challenge: designing a multi-agent communication protocol.

Protocol Rules:
- 立论 (Opening):    正方→all, 反方→all  (broadcast, blind to opponent)
- 质询 (Cross-Exam): 正方→反方(question), 反方→正方(question)  (directed)
- 驳论 (Rebuttal):   正方→反方(rebuttal), 反方→正方(rebuttal)  (directed, must reference)
- 总结 (Closing):    反方→all, 正方→all  (broadcast summary)
- 裁判 (Judgment):   裁判→all(ruling)     (final verdict)
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Message Types and Roles
# ============================================================

class MessageType(str, Enum):
    """Types of messages in the debate protocol."""
    STATEMENT = "statement"       # 立论陈述
    QUESTION = "question"         # 质询提问
    REBUTTAL = "rebuttal"         # 驳论回应
    CLOSING = "closing"           # 总结陈词
    RULING = "ruling"             # 裁判裁决
    ANNOUNCEMENT = "announcement" # 主持人公告


class AgentRole(str, Enum):
    """Agent roles in the debate."""
    PRO = "正方辩手"
    CON = "反方辩手"
    MODERATOR = "主持人"
    JUDGE = "裁判"


# Communication rules: who can send what to whom in each phase
COMMUNICATION_RULES = {
    "opening": {
        AgentRole.PRO: {"receiver": "all", "msg_type": MessageType.STATEMENT},
        AgentRole.CON: {"receiver": "all", "msg_type": MessageType.STATEMENT},
    },
    "cross_examination": {
        AgentRole.PRO: {"receiver": AgentRole.CON, "msg_type": MessageType.QUESTION},
        AgentRole.CON: {"receiver": AgentRole.PRO, "msg_type": MessageType.QUESTION},
    },
    "rebuttal": {
        AgentRole.PRO: {"receiver": AgentRole.CON, "msg_type": MessageType.REBUTTAL},
        AgentRole.CON: {"receiver": AgentRole.PRO, "msg_type": MessageType.REBUTTAL},
    },
    "closing": {
        AgentRole.CON: {"receiver": "all", "msg_type": MessageType.CLOSING},
        AgentRole.PRO: {"receiver": "all", "msg_type": MessageType.CLOSING},
    },
    "judgment": {
        AgentRole.JUDGE: {"receiver": "all", "msg_type": MessageType.RULING},
    },
}


# ============================================================
# Debate Message
# ============================================================

@dataclass
class DebateMessage:
    """
    Formal message structure for inter-agent communication.

    Each message in the debate is a structured object with:
    - Unique ID for traceability
    - Explicit sender/receiver for protocol enforcement
    - References to previous messages for argument chains
    - Evidence used for fact-checking and quality assessment
    """

    msg_id: str
    sender: str              # AgentRole value
    receiver: str            # AgentRole value or "all"
    phase: str               # debate phase name
    msg_type: str            # MessageType value
    content: str             # actual speech content
    round_num: int           # round number within the phase
    references: List[str] = field(default_factory=list)  # referenced msg_ids
    evidence_used: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def create(
        cls,
        sender: str,
        receiver: str,
        phase: str,
        msg_type: str,
        content: str,
        round_num: int = 0,
        references: Optional[List[str]] = None,
        evidence_used: Optional[List[Dict[str, Any]]] = None,
    ) -> "DebateMessage":
        """Factory method to create a DebateMessage with auto-generated ID."""
        return cls(
            msg_id=str(uuid.uuid4())[:8],
            sender=sender,
            receiver=receiver,
            phase=phase,
            msg_type=msg_type,
            content=content,
            round_num=round_num,
            references=references or [],
            evidence_used=evidence_used or [],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "msg_id": self.msg_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "phase": self.phase,
            "msg_type": self.msg_type,
            "content": self.content[:500],  # truncate for storage
            "round_num": self.round_num,
            "ref_count": len(self.references),
            "evidence_count": len(self.evidence_used),
            "timestamp": self.timestamp,
        }


# ============================================================
# MessageBus
# ============================================================

class MessageBus:
    """
    Central message bus for the debate system.

    Responsibilities:
    1. Route messages between agents according to protocol rules
    2. Store all messages for history and retrieval
    3. Provide query interfaces (by sender, phase, round, references)
    4. Maintain message reference chains for argument tracing

    This replaces the implicit state-passing through OrchestratorState
    with an explicit, protocol-enforced communication mechanism.
    """

    def __init__(self):
        self.messages: List[DebateMessage] = []
        self._subscribers: Dict[str, List[Callable]] = {}

    def send(self, message: DebateMessage) -> DebateMessage:
        """
        Send a message through the bus.

        Validates the message against protocol rules, stores it,
        and notifies subscribers.

        Args:
            message: The DebateMessage to send.

        Returns:
            The stored message (with generated ID if new).
        """
        # Validate against protocol rules
        self._validate_message(message)

        # Store
        self.messages.append(message)
        logger.debug(
            f"[MSG {message.msg_id}] {message.sender} → "
            f"{message.receiver} [{message.phase}/{message.msg_type}] "
            f"R{message.round_num}"
        )

        # Notify subscribers
        receiver_key = message.receiver if message.receiver != "all" else "*"
        for subscriber in self._subscribers.get(receiver_key, []):
            try:
                subscriber(message)
            except Exception as e:
                logger.error(f"Subscriber error for {receiver_key}: {e}")

        # Also notify "all" subscribers
        for subscriber in self._subscribers.get("*", []):
            try:
                subscriber(message)
            except Exception as e:
                logger.error(f"Broadcast subscriber error: {e}")

        return message

    def subscribe(self, agent_role: str, callback: Callable[[DebateMessage], None]):
        """
        Subscribe an agent to receive messages addressed to it.

        Args:
            agent_role: The agent role to subscribe as (or "*" for all).
            callback: Function to call when a message arrives.
        """
        if agent_role not in self._subscribers:
            self._subscribers[agent_role] = []
        self._subscribers[agent_role].append(callback)

    def get_messages(
        self,
        sender: Optional[str] = None,
        receiver: Optional[str] = None,
        phase: Optional[str] = None,
        msg_type: Optional[str] = None,
        round_num: Optional[int] = None,
        limit: int = 50,
    ) -> List[DebateMessage]:
        """
        Query messages with filters.

        Args:
            sender: Filter by sender role.
            receiver: Filter by receiver role.
            phase: Filter by debate phase.
            msg_type: Filter by message type.
            round_num: Filter by round number.
            limit: Maximum results to return.

        Returns:
            List of matching DebateMessage objects.
        """
        results = self.messages
        if sender:
            results = [m for m in results if m.sender == sender]
        if receiver:
            results = [m for m in results if m.receiver == receiver or m.receiver == "all"]
        if phase:
            results = [m for m in results if m.phase == phase]
        if msg_type:
            results = [m for m in results if m.msg_type == msg_type]
        if round_num is not None:
            results = [m for m in results if m.round_num == round_num]
        return results[-limit:]

    def get_latest_from(self, sender: str) -> Optional[DebateMessage]:
        """Get the latest message from a specific sender."""
        from_sender = [m for m in self.messages if m.sender == sender]
        return from_sender[-1] if from_sender else None

    def get_reference_chain(self, msg_id: str) -> List[DebateMessage]:
        """
        Trace the reference chain of a message (for argument tracing).

        Args:
            msg_id: The message ID to trace from.

        Returns:
            List of messages in the reference chain, oldest first.
        """
        chain = []
        visited = set()
        current_id = msg_id

        while current_id and current_id not in visited:
            visited.add(current_id)
            msg = self.get_by_id(current_id)
            if msg:
                chain.append(msg)
                # Follow first reference
                current_id = msg.references[0] if msg.references else None
            else:
                break

        return list(reversed(chain))

    def get_by_id(self, msg_id: str) -> Optional[DebateMessage]:
        """Get a message by its ID."""
        for m in self.messages:
            if m.msg_id == msg_id:
                return m
        return None

    def get_phase_summary(self, phase: str) -> str:
        """
        Get a human-readable summary of a phase's messages.

        Args:
            phase: The phase name.

        Returns:
            Formatted string with all messages from the phase.
        """
        phase_msgs = self.get_messages(phase=phase)
        lines = []
        for m in phase_msgs:
            lines.append(f"[{m.sender}→{m.receiver}] ({m.msg_type}): {m.content[:200]}")
        return "\n".join(lines)

    def get_argument_chain_for_judge(self) -> str:
        """
        Build a structured argument chain for the judge to review.
        Groups messages by phase and shows reference links.
        """
        sections = []
        phases = ["opening", "cross_examination", "rebuttal", "closing"]

        for phase in phases:
            msgs = self.get_messages(phase=phase)
            if not msgs:
                continue

            phase_name = {
                "opening": "立论阶段",
                "cross_examination": "质询阶段",
                "rebuttal": "驳论阶段",
                "closing": "总结阶段",
            }.get(phase, phase)

            sections.append(f"\n=== {phase_name} ===")
            for m in msgs:
                ref_str = ""
                if m.references:
                    ref_str = f" [回应: {', '.join(m.references)}]"
                evidence_str = ""
                if m.evidence_used:
                    evidence_str = f" [证据: {len(m.evidence_used)}条]"
                sections.append(
                    f"[R{m.round_num}] {m.sender}: {m.content[:300]}{ref_str}{evidence_str}"
                )

        return "\n".join(sections)

    def clear(self):
        """Clear all messages (for testing/reset)."""
        self.messages.clear()
        self._subscribers.clear()

    def _validate_message(self, message: DebateMessage):
        """
        Validate a message against the communication protocol rules.

        Args:
            message: The message to validate.

        Raises:
            ValueError: If the message violates protocol rules.
        """
        rules = COMMUNICATION_RULES.get(message.phase, {})

        # Find the sender's role
        sender_role = None
        for role in AgentRole:
            if role.value == message.sender:
                sender_role = role
                break

        if sender_role is None:
            logger.warning(f"Unknown sender role: {message.sender}")
            return

        if sender_role not in rules:
            # Moderator announcements are always allowed
            if message.msg_type == MessageType.ANNOUNCEMENT:
                return
            logger.warning(
                f"No protocol rule for {sender_role.value} in phase '{message.phase}'"
            )
            return

        rule = rules[sender_role]
        expected_receiver = rule["receiver"]
        expected_type = rule["msg_type"]

        # Validate receiver
        if isinstance(expected_receiver, AgentRole):
            if message.receiver != expected_receiver.value:
                logger.warning(
                    f"Protocol: expected receiver '{expected_receiver.value}', "
                    f"got '{message.receiver}'"
                )
        elif expected_receiver == "all":
            if message.receiver != "all":
                logger.warning(
                    f"Protocol: expected broadcast ('all'), got '{message.receiver}'"
                )

        # Validate message type
        if message.msg_type != expected_type.value:
            logger.warning(
                f"Protocol: expected msg_type '{expected_type.value}', "
                f"got '{message.msg_type}'"
            )

    @property
    def message_count(self) -> int:
        """Total number of messages."""
        return len(self.messages)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get statistics about the message bus."""
        by_phase = {}
        by_sender = {}
        for m in self.messages:
            by_phase[m.phase] = by_phase.get(m.phase, 0) + 1
            by_sender[m.sender] = by_sender.get(m.sender, 0) + 1
        return {
            "total_messages": len(self.messages),
            "by_phase": by_phase,
            "by_sender": by_sender,
            "reference_chains": sum(1 for m in self.messages if m.references),
        }
