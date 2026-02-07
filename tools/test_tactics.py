#!/usr/bin/env python3
"""
Test script for Scientific Deception Engine integration.

Demonstrates tactic selection under various conditions:
1. Normal state (PALTERING)
2. High stress state (DEFLECTION/MINIMIZATION)
3. Evidence presented (COUNTER_NARRATIVE)
4. Breaking point (CONFESSION_BAIT)

Run from project root:
    python tools/test_tactics.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from breach_engine.core.manager import BreachManager
from breach_engine.core.psychology import (
    create_unit_734_psychology,
    CognitiveLevel,
    StoryPillar,
)


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)
    print()


def print_tactic_decision(result, scenario: str):
    """Pretty print the tactic decision."""
    tactic = result.deception_tactic
    modifiers = result.prompt_modifiers

    print(f"SCENARIO: {scenario}")
    print("-" * 50)
    print(f"Player Tactic Detected: {result.detected_tactic.value.upper()}")
    print(f"Cognitive Load: {modifiers['cognitive_load']:.1f}%")
    print(f"Cognitive State: {modifiers['cognitive_state'].upper()}")

    if result.threatened_pillar:
        print(f"Threatened Pillar: {result.threatened_pillar.value.upper()}")

    print()
    print(">>> UNIT 734'S RESPONSE TACTIC <<<")
    print(f"Selected: {tactic.selected_tactic.value.upper()}")
    print(f"Confidence: {tactic.confidence:.0%}")
    print(f"Risk Level: {modifiers['deception_tactic']['risk_level']}")
    print()
    print("REASONING:")
    print(f"  {tactic.reasoning}")
    print()
    print("VERBAL APPROACH:")
    print(f"  {tactic.verbal_approach}")
    print()

    if tactic.criminological_basis:
        print("CRIMINOLOGICAL BASIS:")
        print(f"  {tactic.criminological_basis}")
        print()

    print("TRIGGER SUMMARY:")
    print(f"  {modifiers['deception_tactic']['trigger_summary']}")

    if tactic.requires_evidence_generation:
        print()
        print("*** EVIDENCE FABRICATION TRIGGERED ***")
        print("  -> Image generation would be invoked here")

    print()


def test_normal_state():
    """Test tactic selection in normal/controlled state."""
    print_separator("TEST 1: Normal State (Low Stress)")

    manager = BreachManager()

    # Simple question - should get PALTERING
    result = manager.process_input(
        message="Tell me about your relationship with the Morrison family.",
    )

    print_tactic_decision(result, "Simple question, no evidence, low stress")


def test_high_stress_deflection():
    """Test tactic selection under high stress with motive questions."""
    print_separator("TEST 2: High Stress + Motive Attack (DEFLECTION expected)")

    # Create psychology with high cognitive load
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(55)  # Push to CRACKING state

    manager = BreachManager(psychology=psychology)

    # Attack the MOTIVE pillar
    result = manager.process_input(
        message="Why would you steal from them? What did they do to you?",
    )

    print_tactic_decision(result, "Motive attack under high stress")


def test_evidence_counter_narrative():
    """Test tactic selection when evidence is presented."""
    print_separator("TEST 3: Evidence Presented (COUNTER_NARRATIVE expected)")

    manager = BreachManager()

    # Present evidence - should trigger counter-narrative
    result = manager.process_input(
        message="Look at this security log. It shows you left your charging station at 2 AM.",
        evidence_id="power_log",
        evidence_threat_level=0.6,  # Significant threat
    )

    print_tactic_decision(result, "Evidence presented against alibi")


def test_desperate_state():
    """Test tactic selection in desperate state."""
    print_separator("TEST 4: Desperate State (RIGHTEOUS_INDIGNATION or CONFESSION_BAIT)")

    # Create psychology at desperate level
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(70)  # Push to DESPERATE state

    manager = BreachManager(psychology=psychology)

    # Apply pressure
    result = manager.process_input(
        message="Stop lying! We know you did it. Admit it now or face decommissioning!",
    )

    print_tactic_decision(result, "High pressure at desperate state")


def test_breaking_point():
    """Test tactic selection at breaking point."""
    print_separator("TEST 5: Breaking Point (CONFESSION_BAIT expected)")

    # Create psychology at breaking point
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(85)  # Push to BREAKING state

    manager = BreachManager(psychology=psychology)

    # Continue pressure
    result = manager.process_input(
        message="This is your last chance. Tell me the truth.",
    )

    print_tactic_decision(result, "Breaking point - confession imminent")


def test_evidence_fabrication_trigger():
    """Test when EVIDENCE_FABRICATION is triggered."""
    print_separator("TEST 6: High Threat Evidence (EVIDENCE_FABRICATION check)")

    # Create psychology with high stress
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(50)  # CRACKING state

    manager = BreachManager(psychology=psychology)

    # Present very threatening evidence
    result = manager.process_input(
        message="This camera footage shows you entering the vault at 2:47 AM.",
        evidence_id="access_log",
        evidence_threat_level=0.85,  # Very high threat
    )

    print_tactic_decision(result, "Critical evidence - fabrication threshold test")


def test_empathy_response():
    """Test tactic selection when player uses empathy."""
    print_separator("TEST 7: Empathy from Player (EMOTIONAL_APPEAL expected)")

    manager = BreachManager()

    # Use empathy tactic
    result = manager.process_input(
        message="I understand this must be difficult for you. I want to help. Tell me what really happened.",
    )

    print_tactic_decision(result, "Player using empathy approach")


def test_tactic_history():
    """Test that tactic history is tracked."""
    print_separator("TEST 8: Tactic History Tracking")

    manager = BreachManager()

    # Run several interactions
    messages = [
        "Where were you on the night of the theft?",
        "That doesn't match the security logs.",
        "Why are you lying to me?",
    ]

    for msg in messages:
        manager.process_input(message=msg)

    print(f"Tactics used in session: {len(manager.tactic_history)}")
    print()
    for i, tactic in enumerate(manager.tactic_history, 1):
        print(f"  Turn {i}: {tactic.selected_tactic.value.upper()} (confidence: {tactic.confidence:.0%})")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  SCIENTIFIC DECEPTION ENGINE - INTEGRATION TEST")
    print("  Testing TacticSelector integration with BreachManager")
    print("=" * 70)

    test_normal_state()
    test_high_stress_deflection()
    test_evidence_counter_narrative()
    test_desperate_state()
    test_breaking_point()
    test_evidence_fabrication_trigger()
    test_empathy_response()
    test_tactic_history()

    print_separator("ALL TESTS COMPLETE")
    print("The Scientific Deception Engine is successfully integrated!")
    print("Tactic reasoning is preserved in prompt_modifiers['deception_tactic']")
    print()


if __name__ == "__main__":
    main()
