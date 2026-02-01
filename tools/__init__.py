"""
Cognitive Breach - Tools Package

Contains CLI tools for testing and simulation.
"""

from tools.test_bench import (
    DetectiveBot,
    SimulationRunner,
    SimulationTranscript,
    InterrogationStrategy,
)

from tools.auto_interrogator import (
    AutonomousInterrogator,
    AdversarialDetective,
    AdversarialStrategy,
    SessionLog,
    TurnLog,
)

__all__ = [
    # Test Bench
    "DetectiveBot",
    "SimulationRunner",
    "SimulationTranscript",
    "InterrogationStrategy",
    # Auto Interrogator
    "AutonomousInterrogator",
    "AdversarialDetective",
    "AdversarialStrategy",
    "SessionLog",
    "TurnLog",
]
