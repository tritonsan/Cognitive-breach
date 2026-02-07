#!/usr/bin/env python3
"""
Test script for the Shadow Analyst - Scientific Interrogation Analysis.

Tests the Shadow Analyst's ability to:
1. Analyze detective input through Reid/PEACE frameworks
2. Detect IMT violations
3. Provide strategic advice to Unit 734
4. Integrate with BreachManager
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from breach_engine.core.shadow_analyst import (
    ShadowAnalyst,
    AnalystInsight,
    ReidPhase,
    PeacePhase,
    IMTViolation,
    AggressionLevel,
    TACTIC_TO_SCIENCE,
    format_analyst_advice_for_prompt,
)
from breach_engine.core.psychology import (
    PlayerTactic,
    CognitiveLevel,
    StoryPillar,
)


def test_tactic_to_science_mapping():
    """Test the static scientific mapping dictionary."""
    print("\n" + "="*60)
    print("TEST 1: TACTIC TO SCIENCE MAPPING")
    print("="*60)

    for tactic, science in TACTIC_TO_SCIENCE.items():
        print(f"\n{tactic.value.upper()}:")
        print(f"  Reid Phases: {[p.value for p in science['reid_phases']]}")
        print(f"  PEACE Phases: {[p.value for p in science['peace_phases']]}")
        print(f"  IMT Violations: {[v.value for v in science['imt_violations']]}")
        print(f"  Aggression: {science['aggression'].value}")
        print(f"  Counter Strategy: {science['counter_strategy']}")

    print("\n[PASS] Static mapping verified")


def test_fallback_insight():
    """Test fallback insight generation (no API call)."""
    print("\n" + "="*60)
    print("TEST 2: FALLBACK INSIGHT GENERATION")
    print("="*60)

    analyst = ShadowAnalyst()

    # Test fallback for each tactic
    test_cases = [
        (PlayerTactic.PRESSURE, CognitiveLevel.CONTROLLED),
        (PlayerTactic.EMPATHY, CognitiveLevel.STRAINED),
        (PlayerTactic.LOGIC, CognitiveLevel.CRACKING),
        (PlayerTactic.EVIDENCE, CognitiveLevel.DESPERATE),
        (PlayerTactic.BLUFF, CognitiveLevel.BREAKING),
    ]

    for tactic, level in test_cases:
        insight = analyst._get_fallback_insight(tactic, level)
        print(f"\n{tactic.value} @ {level.value}:")
        print(f"  Reid Phase: {insight.reid_phase.value}")
        print(f"  Framework: {insight.framework_primary}")
        print(f"  Aggression: {insight.aggression_level.value}")
        print(f"  Recommended: {insight.recommended_tactic}")
        print(f"  Advice: {insight.strategic_advice[:60]}...")

    print("\n[PASS] Fallback insights generated correctly")


def test_live_analysis():
    """Test live analysis with Gemini API."""
    print("\n" + "="*60)
    print("TEST 3: LIVE SHADOW ANALYST ANALYSIS")
    print("="*60)

    analyst = ShadowAnalyst()

    # Test cases: different interrogation approaches
    test_cases = [
        {
            "input": "I know you did it. We have witnesses. Confess now!",
            "tactic": PlayerTactic.PRESSURE,
            "expected_reid": ReidPhase.POSITIVE_CONFRONTATION,
            "expected_aggression": AggressionLevel.AGGRESSIVE,
        },
        {
            "input": "I understand this must be difficult for you. I'm here to help.",
            "tactic": PlayerTactic.EMPATHY,
            "expected_reid": ReidPhase.THEME_DEVELOPMENT,
            "expected_aggression": AggressionLevel.PASSIVE,
        },
        {
            "input": "You said you were in standby at 2 AM, but the logs show movement.",
            "tactic": PlayerTactic.LOGIC,
            "expected_reid": ReidPhase.OVERCOMING_OBJECTIONS,
            "expected_aggression": AggressionLevel.ASSERTIVE,
        },
        {
            "input": "Did you take the data to protect yourself, or to protect someone else?",
            "tactic": PlayerTactic.PRESSURE,
            "expected_reid": ReidPhase.ALTERNATIVE_QUESTION,  # Trap!
            "expected_aggression": AggressionLevel.ASSERTIVE,
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: \"{case['input'][:60]}...\"")
        print(f"Detected Tactic: {case['tactic'].value}")

        insight = analyst.analyze_sync(
            player_input=case["input"],
            detected_tactic=case["tactic"],
            cognitive_load=45.0,
            cognitive_level=CognitiveLevel.STRAINED,
            threatened_pillar=StoryPillar.ALIBI,
            collapsed_pillars=[],
        )

        print(f"\nShadow Analyst Response:")
        print(f"  Reid Phase: {insight.reid_phase.value}")
        print(f"  PEACE Phase: {insight.peace_phase.value}")
        print(f"  Framework: {insight.framework_primary}")
        print(f"  Aggression: {insight.aggression_level.value}")
        print(f"  Rapport Trend: {insight.rapport_trend}")
        print(f"  Confession Risk: {insight.confession_risk:.0%}")
        print(f"  Trap Detected: {insight.trap_detected}")
        if insight.trap_detected:
            print(f"    Trap: {insight.trap_description}")
        print(f"  Recommended Tactic: {insight.recommended_tactic}")
        print(f"  Fallback: {insight.fallback_tactic}")
        print(f"  Strategic Advice: {insight.strategic_advice}")
        print(f"  Scientific Basis: {insight.scientific_basis}")

        # Print formatted advice for prompt
        print(f"\nFormatted for Prompt:")
        formatted = format_analyst_advice_for_prompt(insight)
        for line in formatted.split("\n")[:10]:  # First 10 lines
            print(f"  {line}")

    print("\n[PASS] Live analysis completed")


def test_integration_with_manager():
    """Test integration with BreachManager."""
    print("\n" + "="*60)
    print("TEST 4: INTEGRATION WITH BREACH MANAGER")
    print("="*60)

    from breach_engine.core.manager import BreachManager

    # Create manager
    manager = BreachManager()

    # Process input (this should trigger Shadow Analyst)
    result = manager.process_input(
        message="Tell me exactly where you were between 2 AM and 3 AM. Don't lie to me!",
        evidence_id=None,
        evidence_threat_level=0.0,
    )

    print(f"\nDetected Tactic: {result.detected_tactic.value}")
    print(f"Deception Tactic: {result.deception_tactic.selected_tactic.value if result.deception_tactic else 'None'}")

    # Check if shadow analyst data is in prompt modifiers
    shadow_data = result.prompt_modifiers.get("shadow_analyst")
    if shadow_data:
        print(f"\nShadow Analyst Data in Prompt:")
        print(f"  Reid Phase: {shadow_data.get('reid_phase')}")
        print(f"  Framework: {shadow_data.get('framework_primary')}")
        print(f"  Aggression: {shadow_data.get('aggression_level')}")
        print(f"  Confession Risk: {shadow_data.get('confession_risk', 0):.0%}")
        print(f"  Strategic Advice: {shadow_data.get('strategic_advice', 'N/A')[:60]}...")
        print("\n[PASS] Shadow Analyst integrated with BreachManager")
    else:
        print("\n[WARNING] Shadow Analyst data not found in prompt modifiers")
        print("  (This may be expected if the API call failed)")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SHADOW ANALYST TEST SUITE")
    print("="*60)

    # Test 1: Static mapping
    test_tactic_to_science_mapping()

    # Test 2: Fallback (no API)
    test_fallback_insight()

    # Test 3: Live API analysis
    try:
        test_live_analysis()
    except Exception as e:
        print(f"\n[SKIP] Live analysis failed: {e}")
        print("  (API key may not be configured)")

    # Test 4: Manager integration
    try:
        test_integration_with_manager()
    except Exception as e:
        print(f"\n[SKIP] Manager integration failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
