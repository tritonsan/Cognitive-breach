"""Pydantic schemas for BreachEngine."""

from breach_engine.schemas.response import (
    BreachResponse,
    InternalMonologue,
    VerbalResponse,
    StateChanges,
    LieConsistencyCheck,
    EmotionalState,
    # NEW: Scientific Deception Engine
    TacticInfo,
    # NEW: Visual Deception System
    GeneratedEvidence,
)
from breach_engine.schemas.state import GameState, SuspectState

__all__ = [
    "BreachResponse",
    "InternalMonologue",
    "VerbalResponse",
    "StateChanges",
    "LieConsistencyCheck",
    "EmotionalState",
    "GameState",
    "SuspectState",
    # NEW: Tactics
    "TacticInfo",
    # NEW: Visual Deception
    "GeneratedEvidence",
]
