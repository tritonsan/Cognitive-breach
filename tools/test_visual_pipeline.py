#!/usr/bin/env python3
"""
Test script for end-to-end visual pipeline verification.

Verifies:
1. Detective generates evidence image via ForensicsLab
2. Image bytes are passed to Gemini via generate_response()
3. Unit 734 can "see" the image (multimodal vision)
4. Unit 734 can generate counter-evidence if needed

Run from project root:
    python tools/test_visual_pipeline.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Suppress verbose logs during test
os.environ.setdefault("BREACH_LOG_LEVEL", "WARNING")

from breach_engine.core.manager import BreachManager
from breach_engine.core.psychology import create_unit_734_psychology, StoryPillar
from breach_engine.core.forensics_lab import create_forensics_lab
from breach_engine.api.gemini_client import GeminiClient


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_status(label: str, status: bool, details: str = ""):
    """Print a status line."""
    icon = "[PASS]" if status else "[FAIL]"
    print(f"  {icon} {label}")
    if details:
        print(f"      -> {details}")


def test_evidence_image_generation():
    """Test Step 1: Generate evidence image from ForensicsLab."""
    print_header("STEP 1: GENERATE PLAYER EVIDENCE IMAGE")

    lab = create_forensics_lab()

    # Request CCTV evidence targeting ALIBI pillar
    request = "Get me security camera footage of the vault at 2:30 AM"
    print(f"Player Request: \"{request}\"")
    print(f">> {lab.get_loading_message()}\n")

    result = lab.request_evidence(request)

    if not result["success"]:
        print_status("Evidence Request", False, result.get("message", "Unknown error"))
        return None, None, None

    evidence = result["evidence"]
    print_status("Evidence Generated", True, f"Type: {evidence.evidence_type.value}")
    print_status("Pillar Targeted", True, f"{result['pillar_targeted'].value.upper()}")
    print_status("Threat Level", True, f"{result['threat_level']:.0%}")

    # Now generate the actual image
    print("\n  Generating image via Imagen API...")

    psychology = create_unit_734_psychology()
    manager = BreachManager(psychology=psychology)

    if not manager.visual_generator:
        print_status("Visual Generator", False, "Not initialized")
        return None, None, None

    # Generate the image
    evidence_with_image = manager.visual_generator.generate_image_sync(
        evidence,
        save_to_cache=False
    )

    if evidence_with_image.image_data:
        print_status("Image Generated", True, f"{len(evidence_with_image.image_data)} bytes")
        return evidence_with_image, result["threat_level"], result["pillar_targeted"]
    else:
        print_status("Image Generated", False, "No image_data returned")
        return None, None, None


def test_unit734_sees_image(evidence, threat_level: float, pillar: StoryPillar):
    """Test Step 2: Verify Unit 734 can see the image via multimodal."""
    print_header("STEP 2: UNIT 734 MULTIMODAL VISION TEST")

    # Initialize fresh systems
    psychology = create_unit_734_psychology()
    psychology.cognitive.add_load(50)  # Some initial stress

    manager = BreachManager(psychology=psychology)
    gemini_client = GeminiClient()

    print(f"  Evidence Type: {evidence.evidence_type.value}")
    print(f"  Image Size: {len(evidence.image_data)} bytes")
    print(f"  Threat Level: {threat_level:.0%}")
    print(f"  Target Pillar: {pillar.value.upper()}")
    print()

    # Process input to get prompt modifiers (simulating app.py flow)
    player_message = "Look at this security footage. It shows someone at the vault at 2:30 AM. Explain yourself."

    processed = manager.process_input(
        message=player_message,
        evidence_id="test_cctv_vault",
        evidence_threat_level=threat_level,
    )

    print_status("Input Processed", True, f"Tactic: {processed.detected_tactic.value}")
    print_status("Deception Selected", True, f"{processed.deception_tactic.selected_tactic.value}")

    # Build prompt modifiers (simulating evidence impact)
    prompt_modifiers = processed.prompt_modifiers.copy()

    # Generate response WITH the image (multimodal call)
    print("\n  Calling Gemini with image (multimodal)...")

    try:
        response = gemini_client.generate_response(
            player_message=player_message,
            conversation_context="Detective is interrogating Unit 734 about a security breach.",
            established_facts=["Unit 734 claims to have been in standby mode"],
            prompt_modifiers=prompt_modifiers,
            evidence_image_data=evidence.image_data,  # THE IMAGE BYTES
            evidence_image_mime="image/png",
        )

        print_status("Gemini Response", True, "BreachResponse received")

        # Check if Unit 734's response acknowledges the image
        speech = response.verbal_response.speech.lower()
        monologue = response.internal_monologue.situation_assessment.lower()

        # Look for visual references in response
        visual_keywords = ["footage", "camera", "image", "see", "shows", "video",
                          "recording", "frame", "timestamp", "visual", "picture"]

        speech_refs = [kw for kw in visual_keywords if kw in speech]
        monologue_refs = [kw for kw in visual_keywords if kw in monologue]

        print()
        print("  UNIT 734 RESPONSE ANALYSIS:")
        print(f"  Speech (excerpt): \"{response.verbal_response.speech[:150]}...\"")
        print(f"  Visual refs in speech: {speech_refs if speech_refs else 'None detected'}")
        print(f"  Visual refs in monologue: {monologue_refs if monologue_refs else 'None detected'}")
        print(f"  Emotional State: {response.emotional_state}")
        print(f"  Threat Assessment: {response.internal_monologue.threat_level:.0%}")

        # Determine if Unit 734 "saw" the image
        saw_image = len(speech_refs) > 0 or len(monologue_refs) > 0
        print_status("Unit 734 Acknowledged Image", saw_image)

        return response, processed, manager

    except Exception as e:
        print_status("Gemini Response", False, str(e))
        return None, processed, manager


def test_counter_evidence_generation(processed, manager):
    """Test Step 3: Counter-evidence generation if triggered."""
    print_header("STEP 3: COUNTER-EVIDENCE GENERATION TEST")

    # Check if Unit 734 should fabricate
    should_fab = manager.should_show_fabrication(processed)
    requires_fab = processed.deception_tactic.requires_evidence_generation

    print(f"  Should Fabricate (manager): {should_fab}")
    print(f"  Tactic Requires Fabrication: {requires_fab}")
    print(f"  Selected Tactic: {processed.deception_tactic.selected_tactic.value}")
    print()

    if not (should_fab or requires_fab):
        print("  Fabrication not triggered - forcing test anyway...")

    # Generate counter-evidence
    if not manager.visual_generator:
        print_status("Visual Generator", False, "Not initialized")
        return None

    # Use the manager's generate_counter_evidence method
    counter_evidence = manager.generate_counter_evidence(
        processed.deception_tactic,
        player_evidence_description="Security footage of vault at 2:30 AM"
    )

    if not counter_evidence:
        print_status("Counter-Evidence Metadata", False, "None generated")
        return None

    print_status("Counter-Evidence Metadata", True, f"Type: {counter_evidence.evidence_type}")
    print(f"      -> Narrative: \"{counter_evidence.narrative_wrapper[:80]}...\"")

    # Now generate the actual image (this is what we fixed in auto_interrogator.py)
    print("\n  Generating counter-evidence image...")

    counter_evidence = manager.visual_generator.generate_image_sync(
        counter_evidence,
        save_to_cache=False
    )

    if counter_evidence.image_data:
        print_status("Counter-Evidence Image", True, f"{len(counter_evidence.image_data)} bytes")
        # Detection risk may not be set on all evidence types
        if hasattr(counter_evidence, 'detection_risk') and counter_evidence.detection_risk is not None:
            print(f"      -> Detection Risk: {counter_evidence.detection_risk:.0%}")
        return counter_evidence
    else:
        print_status("Counter-Evidence Image", False, "No image_data returned")
        return None


def test_full_pipeline():
    """Run the complete visual pipeline test."""
    print("\n" + "=" * 70)
    print("  COGNITIVE BREACH: VISUAL PIPELINE END-TO-END TEST")
    print("=" * 70)
    print()
    print("This test verifies:")
    print("  1. ForensicsLab generates evidence images")
    print("  2. Unit 734 receives images via Gemini multimodal API")
    print("  3. Unit 734's response acknowledges the visual evidence")
    print("  4. Counter-evidence generation produces actual images")
    print()

    # Step 1: Generate player evidence
    evidence, threat_level, pillar = test_evidence_image_generation()

    if not evidence:
        print("\n[FAIL] PIPELINE TEST FAILED: Could not generate evidence image")
        return False

    # Step 2: Test Unit 734 multimodal vision
    response, processed, manager = test_unit734_sees_image(evidence, threat_level, pillar)

    if not response:
        print("\n[FAIL] PIPELINE TEST FAILED: Could not get Unit 734 response")
        return False

    # Step 3: Test counter-evidence generation
    counter_evidence = test_counter_evidence_generation(processed, manager)

    # Summary
    print_header("PIPELINE TEST SUMMARY")

    print_status("Evidence Image Generated", evidence is not None and evidence.image_data is not None)
    print_status("Multimodal API Called", response is not None)
    print_status("Unit 734 Response Valid", response is not None)
    print_status("Counter-Evidence Generated", counter_evidence is not None and counter_evidence.image_data is not None)

    all_passed = (
        evidence is not None and evidence.image_data is not None and
        response is not None and
        counter_evidence is not None and counter_evidence.image_data is not None
    )

    print()
    if all_passed:
        print("[SUCCESS] VISUAL PIPELINE: ALL TESTS PASSED")
        print("   Unit 734 can see player evidence and generate counter-evidence.")
    else:
        print("[WARNING] VISUAL PIPELINE: SOME TESTS FAILED")
        print("   Check the output above for details.")

    return all_passed


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
