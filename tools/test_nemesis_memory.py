"""
Nemesis Memory Test Harness

Runs multiple interrogation sessions in succession to verify
Unit 734 remembers and adapts to previous defeats.

Usage:
    python -m tools.test_nemesis_memory --sessions 3 --strategy relentless
    python -m tools.test_nemesis_memory --sessions 5 --no-reset
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file before other imports
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from tools.auto_interrogator import (
    AutonomousInterrogator,
    AdversarialStrategy,
)
from breach_engine.core.memory import get_memory_manager, MemoryManager


def run_nemesis_test(
    num_sessions: int = 3,
    strategy: AdversarialStrategy = AdversarialStrategy.RELENTLESS,
    reset_memory: bool = True,
    max_turns: int = 30,
    verbose: bool = True,
) -> List[Dict]:
    """
    Run multiple sessions and track memory evolution.

    Args:
        num_sessions: How many games to play
        strategy: Which adversarial strategy
        reset_memory: Whether to clear memory before starting
        max_turns: Maximum turns per session
        verbose: Whether to print progress

    Returns:
        List of session summaries with memory state
    """
    memory_path = Path("data/memory.json")

    # Optionally reset memory
    if reset_memory and memory_path.exists():
        backup_path = memory_path.with_suffix(".backup.json")
        shutil.copy(memory_path, backup_path)
        memory_path.unlink()
        if verbose:
            print(f"[NEMESIS TEST] Memory reset. Backup at {backup_path}")

    results = []

    for session_num in range(1, num_sessions + 1):
        if verbose:
            print(f"\n{'='*60}")
            print(f"SESSION {session_num}/{num_sessions}")
            print(f"{'='*60}")

        # Get pre-session memory state
        # Force reload by creating new manager
        mm = MemoryManager()
        pre_state = {
            "total_games": mm.memory.total_games,
            "nemesis_stage": mm.memory.nemesis_stage.value if hasattr(mm.memory.nemesis_stage, 'value') else str(mm.memory.nemesis_stage),
            "win_rate": mm.memory.win_rate,
            "weakest_pillar": mm.memory.weakest_pillar,
            "learning_injection": mm.get_learning_injection(),
        }

        if verbose:
            print(f"\n[PRE-SESSION MEMORY]")
            print(f"  Total games: {pre_state['total_games']}")
            print(f"  Stage: {pre_state['nemesis_stage']}")
            print(f"  Win rate: {pre_state['win_rate']:.1%}")
            if pre_state['learning_injection']:
                print(f"  Learning injection preview:")
                print(f"    {pre_state['learning_injection'][:100]}...")

        # Run interrogation
        try:
            interrogator = AutonomousInterrogator(
                strategy=strategy,
                max_turns=max_turns,
                enable_images=True,
                verbose=verbose,
                save_images=False,
            )

            session = interrogator.run()

            outcome = session.outcome or "unknown"
            turns = session.total_turns

        except Exception as e:
            print(f"[ERROR] Session {session_num} failed: {e}")
            outcome = "error"
            turns = 0

        # Get post-session memory state (force reload)
        mm = MemoryManager()
        post_state = {
            "total_games": mm.memory.total_games,
            "nemesis_stage": mm.memory.nemesis_stage.value if hasattr(mm.memory.nemesis_stage, 'value') else str(mm.memory.nemesis_stage),
            "win_rate": mm.memory.win_rate,
            "weakest_pillar": mm.memory.weakest_pillar,
            "current_streak": mm.memory.current_streak,
            "streak_type": mm.memory.streak_type,
            "learning_injection": mm.get_learning_injection(),
            "nemesis_injection": mm.get_nemesis_injection(),
            "tactic_resistances": {
                t: mm.memory.tactic_effectiveness[t].resistance_level
                for t in mm.memory.tactic_effectiveness
            },
            "pillar_reinforcements": {
                p: mm.memory.pillar_reinforcement[p].reinforcement_level
                for p in mm.memory.pillar_reinforcement
            },
        }

        results.append({
            "session": session_num,
            "outcome": outcome,
            "turns": turns,
            "pre_memory": pre_state,
            "post_memory": post_state,
            "memory_changed": pre_state["learning_injection"] != post_state["learning_injection"],
            "games_incremented": post_state["total_games"] > pre_state["total_games"],
        })

        # Print memory evolution
        if verbose:
            print(f"\n[MEMORY EVOLUTION]")
            print(f"  Games: {pre_state['total_games']} → {post_state['total_games']}")
            print(f"  Stage: {pre_state['nemesis_stage']} → {post_state['nemesis_stage']}")
            print(f"  Streak: {post_state['current_streak']} ({post_state['streak_type'] or 'none'})")
            if post_state["tactic_resistances"]:
                print(f"  Tactic Resistances:")
                for tactic, resistance in post_state["tactic_resistances"].items():
                    if resistance > 0:
                        print(f"    {tactic}: {resistance:.0%}")
            if post_state["learning_injection"]:
                print(f"  Learning Injection:")
                print(f"    {post_state['learning_injection'][:200]}...")

    # Final summary
    if verbose:
        print(f"\n{'='*60}")
        print("NEMESIS MEMORY TEST COMPLETE")
        print(f"{'='*60}")
        print(f"\n{'Session':<10} {'Outcome':<12} {'Turns':<8} {'Memory Changed':<15} {'Games Inc'}")
        print("-" * 60)
        for r in results:
            print(f"{r['session']:<10} {r['outcome']:<12} {r['turns']:<8} "
                  f"{'YES' if r['memory_changed'] else 'NO':<15} "
                  f"{'YES' if r['games_incremented'] else 'NO'}")

        # Check verification criteria
        print(f"\n[VERIFICATION CHECKLIST]")

        # Session 1: No learning injection (fresh start)
        if results and results[0]["pre_memory"]["learning_injection"] == "":
            print("✓ Session 1: No learning injection (fresh start)")
        else:
            print("✗ Session 1: Expected no learning injection")

        # Session 2+: Learning injection appears
        if len(results) > 1 and results[1]["post_memory"]["learning_injection"]:
            print("✓ Session 2+: Learning injection appears")
        elif len(results) > 1:
            print("✗ Session 2+: Expected learning injection after first defeat")

        # Memory file exists
        if memory_path.exists():
            print("✓ Memory file saved to disk")
        else:
            print("✗ Memory file not saved")

        # Games count incremented
        if all(r["games_incremented"] for r in results):
            print("✓ All games properly incremented total_games")
        else:
            print("✗ Some games did not increment total_games")

    return results


def print_memory_analysis(memory_path: str = "data/memory.json") -> None:
    """
    Print detailed analysis of current memory state.

    Args:
        memory_path: Path to memory file
    """
    path = Path(memory_path)
    if not path.exists():
        print(f"[ERROR] Memory file not found: {memory_path}")
        return

    with open(path, "r") as f:
        data = json.load(f)

    print(f"\n{'='*60}")
    print("NEMESIS MEMORY ANALYSIS")
    print(f"{'='*60}")

    print(f"\n[OVERVIEW]")
    print(f"  Total Games: {data.get('total_games', 0)}")
    print(f"  Victories (Unit 734 survived): {data.get('victories', 0)}")
    print(f"  Defeats (Detective won): {data.get('defeats', 0)}")
    print(f"  Nemesis Stage: {data.get('nemesis_stage', 'stranger')}")

    print(f"\n[PILLAR BREACHES]")
    breaches = data.get('pillar_breaches', {})
    for pillar, breach_data in breaches.items():
        count = breach_data.get('count', 0)
        print(f"  {pillar.upper()}: {count} breaches")

    print(f"\n[TACTIC EFFECTIVENESS]")
    tactics = data.get('tactic_effectiveness', {})
    for tactic, tactic_data in tactics.items():
        rate = tactic_data.get('effectiveness_rate', 0.5)
        resistance = tactic_data.get('resistance_level', 0)
        print(f"  {tactic}: {rate:.0%} effective, {resistance:.0%} resistance")

    print(f"\n[DETECTIVE PROFILE]")
    profile = data.get('detective_profile', {})
    print(f"  Aggression: {profile.get('aggression_score', 0.5):.0%}")
    print(f"  Bluff Frequency: {profile.get('bluff_frequency', 0):.0%}")
    print(f"  Primary Target: {profile.get('pillars_they_target_first', [])}")

    print(f"\n[CRITICAL MOMENTS]")
    moments = data.get('critical_moments', [])
    print(f"  Total recorded: {len(moments)}")
    for moment in moments[-3:]:  # Show last 3
        print(f"    - {moment.get('moment_type', 'unknown')}: {moment.get('description', '')[:50]}...")

    print(f"\n[NEMESIS HOOKS]")
    hooks = data.get('nemesis_hooks', [])
    print(f"  Total hooks: {len(hooks)}")
    for hook in hooks[-3:]:  # Show last 3
        print(f"    - Trigger: {hook.get('trigger_tactic') or hook.get('trigger_pillar') or 'general'}")
        print(f"      \"{hook.get('callback_text', '')[:60]}...\"")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Nemesis Memory Test Harness - Test Unit 734's learning system"
    )
    parser.add_argument(
        "--sessions",
        type=int,
        default=3,
        help="Number of sessions to run (default: 3)"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="relentless",
        choices=["relentless", "methodical", "psychological", "adaptive"],
        help="Adversarial strategy to use (default: relentless)"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't reset memory before starting"
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Maximum turns per session (default: 30)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Just analyze existing memory file (don't run sessions)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )

    args = parser.parse_args()

    if args.analyze:
        print_memory_analysis()
    else:
        strategy_map = {
            "relentless": AdversarialStrategy.RELENTLESS,
            "methodical": AdversarialStrategy.METHODICAL,
            "psychological": AdversarialStrategy.PSYCHOLOGICAL,
            "adaptive": AdversarialStrategy.ADAPTIVE,
        }

        results = run_nemesis_test(
            num_sessions=args.sessions,
            strategy=strategy_map[args.strategy],
            reset_memory=not args.no_reset,
            max_turns=args.max_turns,
            verbose=not args.quiet,
        )

        # Save results summary
        results_path = Path("logs") / f"nemesis_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n[RESULTS] Test results saved to: {results_path}")
