"""
Game state schemas for Cognitive Breach.

Tracks the interrogation state, suspect state, and conversation history.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SuspectState(BaseModel):
    """Unit 734's current psychological state."""
    stress: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Current stress level (0=calm, 1=breaking)"
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in maintaining cover (0=shattered, 1=confident)"
    )
    hostility: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Hostility toward detective (0=cooperative, 1=hostile)"
    )
    trust: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Trust in detective (affects confession likelihood)"
    )

    def update(self, stress_delta: float = 0, confidence_delta: float = 0) -> None:
        """Update state with deltas, clamping to valid range."""
        self.stress = max(0.0, min(1.0, self.stress + stress_delta))
        self.confidence = max(0.0, min(1.0, self.confidence + confidence_delta))

    def is_breaking(self) -> bool:
        """Check if suspect is close to breaking."""
        return self.stress > 0.8 or self.confidence < 0.2


class ConversationTurn(BaseModel):
    """A single turn in the interrogation."""
    role: str = Field(description="'detective' or 'suspect'")
    content: str = Field(description="What was said")
    internal_monologue: Optional[str] = Field(
        default=None,
        description="Unit 734's internal thoughts (only for suspect turns)"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class GameState(BaseModel):
    """Complete game state for an interrogation session."""

    # Session info
    session_id: str = Field(default="")
    case_id: str = Field(default="case_001")
    started_at: datetime = Field(default_factory=datetime.now)

    # Suspect state
    suspect_state: SuspectState = Field(default_factory=SuspectState)

    # Conversation history
    conversation: List[ConversationTurn] = Field(default_factory=list)

    # Lie tracking
    established_facts: List[str] = Field(
        default_factory=list,
        description="Facts Unit 734 has claimed as true"
    )
    established_lies: List[str] = Field(
        default_factory=list,
        description="Lies Unit 734 has told"
    )
    contradictions_found: List[str] = Field(
        default_factory=list,
        description="Contradictions the detective has caught"
    )

    # Evidence
    evidence_presented: List[str] = Field(
        default_factory=list,
        description="Evidence shown to suspect"
    )

    # Game progress
    confession_level: int = Field(
        default=0,
        ge=0,
        le=5,
        description="How much has been confessed (0=nothing, 5=full confession)"
    )

    def add_detective_message(self, content: str) -> None:
        """Add a detective's message to conversation."""
        self.conversation.append(ConversationTurn(
            role="detective",
            content=content
        ))

    def add_suspect_response(
        self,
        content: str,
        internal_monologue: Optional[str] = None
    ) -> None:
        """Add Unit 734's response to conversation."""
        self.conversation.append(ConversationTurn(
            role="suspect",
            content=content,
            internal_monologue=internal_monologue
        ))

    def get_conversation_context(self, max_turns: int = 10) -> str:
        """Get recent conversation as context string."""
        recent = self.conversation[-max_turns:]
        lines = []
        for turn in recent:
            role = "Detective" if turn.role == "detective" else "Unit 734"
            lines.append(f"{role}: {turn.content}")
        return "\n".join(lines)

    def get_facts_context(self) -> str:
        """Get established facts as context string."""
        if not self.established_facts:
            return "No facts established yet."
        return "Established facts:\n- " + "\n- ".join(self.established_facts)
