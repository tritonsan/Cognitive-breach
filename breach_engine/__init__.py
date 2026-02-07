"""
Cognitive Breach - BreachEngine

Core game engine for the AI interrogation game.
Handles Unit 734's reasoning, lie tracking, and response generation.
"""

from breach_engine.schemas.response import (
    BreachResponse,
    InternalMonologue,
    VerbalResponse,
    StateChanges,
    LieConsistencyCheck,
    EmotionalState,
)
from breach_engine.schemas.state import GameState, SuspectState

__version__ = "0.1.0"
__all__ = [
    "BreachResponse",
    "InternalMonologue",
    "VerbalResponse",
    "StateChanges",
    "LieConsistencyCheck",
    "EmotionalState",
    "GameState",
    "SuspectState",
]
