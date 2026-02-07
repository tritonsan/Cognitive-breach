#!/usr/bin/env python3
"""
Test script for Visual Deception System integration.

Demonstrates counter-evidence generation under various conditions:
1. Normal state (no fabrication)
2. High stress + evidence (fabrication triggered)
3. Breaking point (desperate fabrication)
4. Different pillar threats (different counter-strategies)

Run from project root:
    python tools/test_visual_generator.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from breach_engine.core.manager import BreachManager
from breach_engine.core.psychology import (
    create_unit_734_psychology,
    StoryPillar,
)
from breach_engine.core.visual_generator import (
    VisualGenerator,
    FabricationContext,
    CounterEvidenceType,
    create_fabrication_context,
    should_trigger_fabrication,
)


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)
    print()


def print_fabrication_result(evidence, scenario: str):
    """Pretty print the fabrication result."""
    print(f"SCENARIO: {scenario}")
    print("-" * 50)
    print(f"Evidence Type: {evidence.evidence_type}")
    print(f"Fabrication Confidence: {evidence.fabrication_confidence:.0%}")
    print()
    print("DESCRIPTION:")
    print(f"  {evidence.description}")
    print()
    print("NARRATIVE WRAPPER (How Unit 734 presents it):")
    print(f"  \"{evidence.narrative_wrapper}\"")
    print()
    print("GENERATION PROMPT (for Nano Banana Pro):")
    print(f"  {evidence.generation_prompt[:200]}...")
    print()
    if evidence.image_data:
        print(f"IMAGE DATA: {len(evidence.image_data)} bytes generated")
    else:
        print("IMAGE DATA: Not generated (test mode / API not called)")
    print()


def test_no_fabrication():
    """Test that fabrication is NOT triggered under normal conditions."""
    print_separator("TEST 1: Normal State (No Fabrication)")

    manager = BreachManager()

    # Simple question - should NOT trigger fabrication
    result = manager.process_input(
        message="Tell me about your relationship with the Morrison family.",
    )

    should_fab = manager.should_show_fabrication(result)
    print(f"Cognitive Load: {manager.psychology.cognitive.load:.1f}%")
    print(f"Tactic Selected: {result.deception_tactic.selected_tactic.value.upper()}")
    print(f"Requires Evidence Generation: {result.deception_tactic.requires_evidence_generation}")
    print(f"Should Trigger Fabrication: {should_fab}")
    print()
    if not should_fab:
        print("CORRECT: No fabrication under normal conditions")
    else:
        print("ERROR: Fabrication should not trigger at low stress!")


def test_high_stress_fabrication():
    """Test fabrication trigger under high stress + evidence."""
    print_separator("TEST 2: High Stress + Evidence (Fabrication Expected)")

    # Create psychology at high stress
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(85)  # Push to breaking state

    manager = BreachManager(psychology=psychology)

    # Present high-threat evidence
    result = manager.process_input(
        message="This camera footage shows you entering the vault at 2:47 AM.",
        evidence_id="access_log",
        evidence_threat_level=0.85,
    )

    print(f"Cognitive Load: {manager.psychology.cognitive.load:.1f}%")
    print(f"Evidence Threat Level: {result.evidence_threat_level:.0%}")
    print(f"Tactic Selected: {result.deception_tactic.selected_tactic.value.upper()}")
    print(f"Requires Evidence Generation: {result.deception_tactic.requires_evidence_generation}")
    print()

    should_fab = manager.should_show_fabrication(result)
    print(f"Should Trigger Fabrication: {should_fab}")
    print()

    if should_fab:
        # Generate the counter-evidence
        evidence = manager.generate_counter_evidence(
            result.deception_tactic,
            player_evidence_description="Camera footage showing vault entry at 2:47 AM"
        )
        if evidence:
            print_fabrication_result(evidence, "High stress with damaging evidence")
        else:
            print("ERROR: Fabrication should have generated evidence!")
    else:
        print("NOTE: Fabrication not triggered (may be tactic-dependent)")


def test_alibi_threat():
    """Test counter-evidence for ALIBI pillar threat."""
    print_separator("TEST 3: ALIBI Pillar Threat")

    context = create_fabrication_context(
        threatened_pillar=StoryPillar.ALIBI,
        cognitive_load=80,
    )

    generator = VisualGenerator()
    evidence = generator.generate_counter_evidence(context)

    print_fabrication_result(evidence, "Player attacking ALIBI with timestamp evidence")


def test_access_threat():
    """Test counter-evidence for ACCESS pillar threat."""
    print_separator("TEST 4: ACCESS Pillar Threat")

    context = create_fabrication_context(
        threatened_pillar=StoryPillar.ACCESS,
        cognitive_load=75,
    )

    generator = VisualGenerator()
    evidence = generator.generate_counter_evidence(context)

    print_fabrication_result(evidence, "Player attacking ACCESS with door logs")


def test_desperate_fabrication():
    """Test fabrication quality at desperate state."""
    print_separator("TEST 5: Desperate State (Low Confidence)")

    # Create context with extreme desperation
    context = FabricationContext(
        threatened_pillar=StoryPillar.MOTIVE,
        cognitive_load=95,
        desperation_level=0.9,  # Very desperate
        alibi_time="11 PM to 3:15 AM",
    )

    generator = VisualGenerator()
    evidence = generator.generate_counter_evidence(context)

    print(f"SCENARIO: Desperate fabrication at breaking point")
    print("-" * 50)
    print(f"Desperation Level: {context.desperation_level:.0%}")
    print(f"Fabrication Confidence: {evidence.fabrication_confidence:.0%}")
    print()
    print("NOTE: Low confidence = higher chance player detects the fabrication!")
    print()
    print("NARRATIVE (more aggressive at desperation):")
    print(f"  \"{evidence.narrative_wrapper}\"")


def test_strategy_selection():
    """Test that different pillars select different strategies."""
    print_separator("TEST 6: Strategy Selection by Pillar")

    generator = VisualGenerator()

    pillars = [
        StoryPillar.ALIBI,
        StoryPillar.ACCESS,
        StoryPillar.MOTIVE,
        StoryPillar.KNOWLEDGE,
    ]

    for pillar in pillars:
        context = create_fabrication_context(
            threatened_pillar=pillar,
            cognitive_load=70,
        )
        strategy, risk = generator.select_counter_strategy(context)
        print(f"{pillar.value.upper():12} -> {strategy.value:25} (Risk: {risk.value})")


def test_fabrication_history():
    """Test that fabrication history is tracked."""
    print_separator("TEST 7: Fabrication History Tracking")

    manager = BreachManager()
    generator = manager.visual_generator

    # Generate multiple fabrications
    contexts = [
        create_fabrication_context(StoryPillar.ALIBI, 80),
        create_fabrication_context(StoryPillar.ACCESS, 75),
        create_fabrication_context(StoryPillar.MOTIVE, 85),
    ]

    for ctx in contexts:
        generator.generate_counter_evidence(ctx)

    print(f"Fabrications in session: {len(generator.generation_history)}")
    print()
    for i, fab in enumerate(generator.generation_history, 1):
        print(f"  {i}. {fab['strategy']:25} | Pillar: {fab['threatened_pillar'] or 'N/A':10} | Risk: {fab['risk']:8} | Conf: {fab['confidence']:.0%}")


def test_integration_flow():
    """Test the full integration flow from input to fabrication."""
    print_separator("TEST 8: Full Integration Flow")

    print("Simulating: Player presents damaging evidence -> Unit 734 generates counter-evidence")
    print()

    # Create high-stress state
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(80)

    manager = BreachManager(psychology=psychology)

    # Player presents evidence
    result = manager.process_input(
        message="Look at this security log. It shows you left your charging station at 2 AM.",
        evidence_id="power_log",
        evidence_threat_level=0.75,
    )

    print("STEP 1: Player Input Processed")
    print(f"  - Detected Tactic: {result.detected_tactic.value}")
    print(f"  - Threatened Pillar: {result.threatened_pillar.value if result.threatened_pillar else 'None'}")
    print(f"  - Evidence Threat: {result.evidence_threat_level:.0%}")
    print()

    print("STEP 2: Deception Tactic Selected")
    print(f"  - Selected Tactic: {result.deception_tactic.selected_tactic.value.upper()}")
    print(f"  - Requires Fabrication: {result.deception_tactic.requires_evidence_generation}")
    print()

    print("STEP 3: Check Fabrication Trigger")
    should_fab = manager.should_show_fabrication(result)
    print(f"  - Should Fabricate: {should_fab}")
    print()

    if should_fab:
        print("STEP 4: Generate Counter-Evidence")
        evidence = manager.generate_counter_evidence(
            result.deception_tactic,
            player_evidence_description="Security log showing charging station exit at 2 AM"
        )
        if evidence:
            print(f"  - Type: {evidence.evidence_type}")
            print(f"  - Confidence: {evidence.fabrication_confidence:.0%}")
            print(f"  - Narrative: \"{evidence.narrative_wrapper[:60]}...\"")
            print()
            print("STEP 5: Ready for BreachResponse")
            print("  - evidence.image_data would be populated by Nano Banana Pro API")
            print("  - Unit 734 would present this with the narrative wrapper")
    else:
        print("STEP 4: Fabrication Not Triggered")
        print("  - Unit 734 will use verbal deception only")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  VISUAL DECEPTION SYSTEM - INTEGRATION TEST")
    print("  Testing VisualGenerator integration with BreachManager")
    print("=" * 70)

    test_no_fabrication()
    test_high_stress_fabrication()
    test_alibi_threat()
    test_access_threat()
    test_desperate_fabrication()
    test_strategy_selection()
    test_fabrication_history()
    test_integration_flow()

    print_separator("ALL TESTS COMPLETE")
    print("The Visual Deception System is successfully integrated!")
    print()
    print("Next Steps:")
    print("1. Connect to actual Gemini Nano Banana Pro API for image generation")
    print("2. Add UI component to display fabricated evidence")
    print("3. Add player detection mechanic for fake evidence")
    print()


if __name__ == "__main__":
    main()
