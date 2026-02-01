#!/usr/bin/env python3
"""
LIVE IMAGE GENERATION TEST

This script tests REAL API calls to Google Gemini for image generation.
It will generate actual PNG files in the assets/evidence_cache/ directory.

PREREQUISITES:
1. Set your API key: set GOOGLE_API_KEY=your_key_here (Windows)
                  or export GOOGLE_API_KEY=your_key_here (Linux/Mac)
2. Have PIL/Pillow installed: pip install Pillow

Run from project root:
    python tools/test_live_image_gen.py

Expected output:
    - assets/evidence_cache/player/evidence_*.png (player evidence)
    - assets/evidence_cache/counter/counter_*.png (Unit 734 counter-evidence)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_api_key():
    """Check if API key is set."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("=" * 60)
        print("ERROR: No API key found!")
        print("=" * 60)
        print()
        print("Please set your Google API key:")
        print()
        print("  Windows (cmd):   set GOOGLE_API_KEY=your_key_here")
        print("  Windows (PS):    $env:GOOGLE_API_KEY='your_key_here'")
        print("  Linux/Mac:       export GOOGLE_API_KEY=your_key_here")
        print()
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        print()
        return False
    print(f"[OK] API key found: {api_key[:8]}...{api_key[-4:]}")
    return True


def test_player_evidence_generation():
    """Test ForensicsLab live image generation."""
    print()
    print("=" * 60)
    print("TEST 1: Player Evidence Generation (ForensicsLab)")
    print("=" * 60)
    print()

    from breach_engine.core.forensics_lab import ForensicsLab, create_forensics_lab

    lab = create_forensics_lab()

    # Make a request
    request = "Get me CCTV footage of the server room at 2:30 AM"
    print(f"[REQUEST] \"{request}\"")
    print()
    print(f">> {lab.get_loading_message()}")
    print()

    # Request evidence (this creates the record but doesn't generate yet)
    result = lab.request_evidence(request, skip_validation=True)

    if not result["success"]:
        print(f"[FAILED] {result['message']}")
        return None

    evidence = result["evidence"]
    print(f"[INFO] Evidence type: {evidence.evidence_type.value}")
    print(f"[INFO] Location: {evidence.location}")
    print(f"[INFO] Threat level: {result['threat_level']:.0%}")
    print()

    # NOW call the actual API
    print("[API CALL] Calling Gemini API for image generation...")
    print()

    evidence = lab.generate_image_sync(evidence)

    if evidence.image_data:
        print(f"[SUCCESS] Generated image: {len(evidence.image_data)} bytes")

        # Find the cached file
        cache_files = list(lab.cache_dir.glob("evidence_*.png"))
        if cache_files:
            latest = max(cache_files, key=lambda p: p.stat().st_mtime)
            print(f"[SAVED] {latest}")
            return latest
        else:
            # Save manually if not cached
            output_path = lab.cache_dir / f"evidence_test_{evidence.request_id}.png"
            output_path.write_bytes(evidence.image_data)
            print(f"[SAVED] {output_path}")
            return output_path
    else:
        print("[WARNING] No image data returned (may have hit safety filters)")
        return None


def test_counter_evidence_generation():
    """Test VisualGenerator live image generation."""
    print()
    print("=" * 60)
    print("TEST 2: Counter-Evidence Generation (VisualGenerator)")
    print("=" * 60)
    print()

    from breach_engine.core.visual_generator import (
        VisualGenerator,
        create_fabrication_context,
        CounterEvidenceType,
    )
    from breach_engine.core.psychology import StoryPillar

    generator = VisualGenerator()

    # Create context: Unit 734 is stressed and needs to counter alibi evidence
    context = create_fabrication_context(
        threatened_pillar=StoryPillar.ALIBI,
        cognitive_load=85,  # High stress
    )

    print(f"[CONTEXT] Threatened pillar: ALIBI")
    print(f"[CONTEXT] Cognitive load: 85% (desperate)")
    print()

    # Generate counter-evidence strategy and prompt
    evidence = generator.generate_counter_evidence(context)

    print(f"[STRATEGY] {evidence.evidence_type}")
    print(f"[CONFIDENCE] {evidence.fabrication_confidence:.0%}")
    print()
    print(f"[NARRATIVE] \"{evidence.narrative_wrapper}\"")
    print()

    # NOW call the actual API
    print("[API CALL] Calling Gemini API for counter-evidence generation...")
    print()

    evidence = generator.generate_image_sync(evidence)

    if evidence.image_data:
        print(f"[SUCCESS] Generated image: {len(evidence.image_data)} bytes")

        if evidence.image_url:
            print(f"[SAVED] {evidence.image_url}")
            return Path(evidence.image_url)
        else:
            # Save manually
            output_path = generator.cache_dir / f"counter_test_{CounterEvidenceType.MODIFIED_TIMESTAMP.value}.png"
            output_path.write_bytes(evidence.image_data)
            print(f"[SAVED] {output_path}")
            return output_path
    else:
        print("[WARNING] No image data returned")
        return None


def test_fallback_placeholder():
    """Test that fallback placeholder works when API fails."""
    print()
    print("=" * 60)
    print("TEST 3: Fallback Placeholder Generation")
    print("=" * 60)
    print()

    from breach_engine.core.visual_generator import VisualGenerator

    generator = VisualGenerator()

    # Generate corrupted placeholder
    print("[INFO] Generating corrupted data placeholder...")
    placeholder = generator._create_corrupted_placeholder()

    if placeholder:
        output_path = generator.cache_dir / "fallback_test.png"
        output_path.write_bytes(placeholder)
        print(f"[SUCCESS] Placeholder generated: {len(placeholder)} bytes")
        print(f"[SAVED] {output_path}")
        return output_path
    else:
        print("[FAILED] Could not generate placeholder")
        return None


def main():
    """Run live tests."""
    print()
    print("=" * 60)
    print("  LIVE IMAGE GENERATION TEST")
    print("  Testing REAL API calls to Google Gemini")
    print("=" * 60)
    print()

    # Check prerequisites
    if not check_api_key():
        return

    print()
    results = []

    # Test 1: Player Evidence
    try:
        path1 = test_player_evidence_generation()
        results.append(("Player Evidence", path1))
    except Exception as e:
        print(f"[ERROR] Test 1 failed: {type(e).__name__}: {e}")
        results.append(("Player Evidence", None))

    # Test 2: Counter Evidence
    try:
        path2 = test_counter_evidence_generation()
        results.append(("Counter Evidence", path2))
    except Exception as e:
        print(f"[ERROR] Test 2 failed: {type(e).__name__}: {e}")
        results.append(("Counter Evidence", None))

    # Test 3: Fallback
    try:
        path3 = test_fallback_placeholder()
        results.append(("Fallback Placeholder", path3))
    except Exception as e:
        print(f"[ERROR] Test 3 failed: {type(e).__name__}: {e}")
        results.append(("Fallback Placeholder", None))

    # Summary
    print()
    print("=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print()

    for name, path in results:
        status = "PASS" if path else "FAIL"
        path_str = str(path) if path else "No file generated"
        print(f"  [{status}] {name}")
        if path:
            print(f"        -> {path_str}")

    print()

    # List all generated files
    cache_base = project_root / "assets" / "evidence_cache"
    all_files = list(cache_base.rglob("*.png"))
    if all_files:
        print("Generated files:")
        for f in sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
            size = f.stat().st_size
            print(f"  {f.relative_to(cache_base)} ({size:,} bytes)")

    print()
    print("Test complete! Check the assets/evidence_cache/ directory for generated images.")


if __name__ == "__main__":
    main()
