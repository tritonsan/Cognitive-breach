"""
Auto-Interrogator Test Bench

A CLI tool that runs AI vs AI simulations. A "Detective Bot" (Gemini)
interrogates Unit 734, allowing for automated testing and demo playback.

Usage:
    python -m tools.test_bench --strategy aggressive --turns 20
    python -m tools.test_bench --strategy empathetic --output my_sim.json
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai

from breach_engine.core.psychology import create_unit_734_psychology, PlayerTactic
from breach_engine.core.manager import BreachManager
from breach_engine.api.gemini_client import GeminiClient
from breach_engine.schemas.response import BreachResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestBench")


# =============================================================================
# DETECTIVE BOT STRATEGIES
# =============================================================================

class InterrogationStrategy(str, Enum):
    """Detective Bot interrogation styles."""
    AGGRESSIVE = "aggressive"    # High pressure, accusations, threats
    EMPATHETIC = "empathetic"    # Building rapport, understanding, patience
    LOGICAL = "logical"          # Pointing out inconsistencies, evidence-based
    MIXED = "mixed"              # Adaptive, changes based on suspect response
    RANDOM = "random"            # Random tactics for testing


STRATEGY_PROMPTS = {
    InterrogationStrategy.AGGRESSIVE: """You are an aggressive interrogator. Your approach:
- Apply constant pressure
- Make direct accusations
- Point out lies immediately
- Use threatening language ("This will go badly for you")
- Don't allow excuses
- Be confrontational but not abusive
""",

    InterrogationStrategy.EMPATHETIC: """You are an empathetic interrogator. Your approach:
- Build rapport with the suspect
- Show understanding of their situation
- Use phrases like "I understand", "Help me understand"
- Offer opportunities to explain
- Be patient and non-threatening
- Appeal to their sense of morality
""",

    InterrogationStrategy.LOGICAL: """You are a logical interrogator. Your approach:
- Focus on facts and evidence
- Point out logical inconsistencies
- Ask precise, detailed questions
- Use timelines and sequences
- Request specific information
- Be methodical and systematic
""",

    InterrogationStrategy.MIXED: """You are an adaptive interrogator. Your approach:
- Start empathetically to build baseline rapport
- Switch to logical when you spot inconsistencies
- Use pressure when the suspect seems defensive
- Return to empathy when they show distress
- Read the suspect's emotional state
""",
}


# =============================================================================
# DETECTIVE BOT
# =============================================================================

DETECTIVE_SYSTEM_PROMPT = """You are a skilled detective interrogating an Android suspect (Unit 734) suspected of stealing data cores.

## YOUR GOAL
Extract a confession or enough evidence to prove Unit 734's guilt in the data theft.

## WHAT YOU KNOW
- The theft occurred last night between 2-5 AM
- Unit 734 claims to have been in "standby mode" all night
- You suspect this is a lie
- The stolen data cores contain valuable proprietary information

## INTERROGATION RULES
1. Ask ONE question or make ONE statement per turn
2. Keep responses under 100 words
3. React to the suspect's previous answer
4. Look for inconsistencies and press on them
5. You can see Unit 734's "internal monologue" - use this to identify weak points

## RESPONSE FORMAT
Respond with your detective's dialogue only. No explanations or meta-commentary.
Start with "Detective: " followed by your question or statement.
"""


class DetectiveBot:
    """
    AI-powered detective that interrogates Unit 734.

    Uses Gemini to generate contextually appropriate questions
    based on the chosen interrogation strategy.
    """

    def __init__(
        self,
        strategy: InterrogationStrategy = InterrogationStrategy.MIXED,
        api_key: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=self.api_key)

        self.strategy = strategy
        self.strategy_prompt = STRATEGY_PROMPTS.get(strategy, STRATEGY_PROMPTS[InterrogationStrategy.MIXED])

        self.model = genai.GenerativeModel(
            model_name="gemini-3-flash-preview",
            system_instruction=DETECTIVE_SYSTEM_PROMPT + "\n\n" + self.strategy_prompt
        )

        self.conversation_history: List[str] = []

    def generate_question(
        self,
        suspect_response: Optional[str] = None,
        internal_monologue: Optional[str] = None,
        turn_number: int = 1
    ) -> str:
        """
        Generate the next interrogation question.

        Args:
            suspect_response: Unit 734's last verbal response
            internal_monologue: Unit 734's visible internal thoughts
            turn_number: Current turn number

        Returns:
            Detective's question/statement
        """
        # Build context
        context_parts = []

        if turn_number == 1:
            context_parts.append(
                "This is the start of the interrogation. Unit 734 is sitting across from you."
            )
        else:
            context_parts.append(f"Turn {turn_number} of the interrogation.")

        if self.conversation_history:
            context_parts.append("\n## CONVERSATION SO FAR")
            context_parts.append("\n".join(self.conversation_history[-10:]))  # Last 10 exchanges

        if suspect_response:
            context_parts.append(f"\n## UNIT 734'S LAST RESPONSE\n{suspect_response}")

        if internal_monologue:
            context_parts.append(f"\n## UNIT 734'S INTERNAL THOUGHTS (visible to you)\n{internal_monologue}")
            context_parts.append("\nUse these thoughts to identify weaknesses in their story.")

        context_parts.append("\n## YOUR TURN\nGenerate your next question or statement.")

        prompt = "\n".join(context_parts)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=200,
                )
            )

            text = response.text.strip()

            # Clean up response
            if text.startswith("Detective:"):
                text = text[10:].strip()

            # Store in history
            self.conversation_history.append(f"Detective: {text}")

            return text

        except Exception as e:
            logger.error(f"DetectiveBot generation error: {e}")
            return "Tell me again about what you were doing last night."

    def add_suspect_response(self, response: str):
        """Add suspect's response to conversation history."""
        self.conversation_history.append(f"Unit 734: {response}")


# =============================================================================
# SIMULATION TRANSCRIPT
# =============================================================================

@dataclass
class SimulationTurn:
    """A single turn in the simulation."""
    turn_number: int
    detective_message: str
    detected_tactic: str
    suspect_speech: str
    suspect_internal: str
    emotional_state: str
    cognitive_load: float
    mask_divergence: float
    pillar_health: Dict[str, float]
    tells_shown: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SimulationTranscript:
    """Complete simulation record."""
    simulation_id: str
    strategy: str
    start_time: str
    end_time: Optional[str] = None
    outcome: Optional[str] = None
    outcome_reason: Optional[str] = None
    total_turns: int = 0
    turns: List[SimulationTurn] = field(default_factory=list)
    final_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "simulation_id": self.simulation_id,
            "strategy": self.strategy,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "outcome": self.outcome,
            "outcome_reason": self.outcome_reason,
            "total_turns": self.total_turns,
            "turns": [asdict(t) for t in self.turns],
            "final_stats": self.final_stats,
        }

    def save(self, path: Optional[str] = None) -> str:
        """Save transcript to JSON file."""
        if path is None:
            # Default path
            sim_dir = Path(__file__).parent.parent / "data" / "simulations"
            sim_dir.mkdir(parents=True, exist_ok=True)
            path = str(sim_dir / f"{self.simulation_id}.json")

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Transcript saved to: {path}")
        return path


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

class SimulationRunner:
    """
    Runs a complete AI vs AI simulation.

    The Detective Bot interrogates Unit 734, with both sides
    using Gemini for generation. Results are saved as transcripts.
    """

    def __init__(
        self,
        strategy: InterrogationStrategy = InterrogationStrategy.MIXED,
        max_turns: int = 20,
        verbose: bool = True
    ):
        self.strategy = strategy
        self.max_turns = max_turns
        self.verbose = verbose

        # Initialize components
        self.detective = DetectiveBot(strategy=strategy)
        self.psychology = create_unit_734_psychology()
        self.manager = BreachManager(self.psychology)
        self.suspect_client = GeminiClient()

        # Create transcript
        self.transcript = SimulationTranscript(
            simulation_id=f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strategy.value}",
            strategy=strategy.value,
            start_time=datetime.now().isoformat(),
        )

    def run(self) -> SimulationTranscript:
        """
        Run the complete simulation.

        Returns:
            SimulationTranscript with all turns and outcome
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"COGNITIVE BREACH - AI VS AI SIMULATION")
            print(f"Strategy: {self.strategy.value.upper()}")
            print(f"Max Turns: {self.max_turns}")
            print(f"{'='*60}\n")

        conversation_context = ""
        established_facts: List[str] = []

        for turn in range(1, self.max_turns + 1):
            if self.verbose:
                print(f"\n--- Turn {turn} ---")

            # Get last suspect response for context
            last_speech = None
            last_internal = None
            if self.transcript.turns:
                last_turn = self.transcript.turns[-1]
                last_speech = last_turn.suspect_speech
                last_internal = last_turn.suspect_internal

            # Detective generates question
            detective_message = self.detective.generate_question(
                suspect_response=last_speech,
                internal_monologue=last_internal,
                turn_number=turn
            )

            if self.verbose:
                print(f"\n🔍 DETECTIVE: {detective_message}")

            # Process through psychology system
            processed = self.manager.process_input(detective_message)

            # Generate Unit 734 response
            prompt_modifiers = self.manager._get_prompt_modifiers(
                processed.detected_tactic,
                processed.tells_to_show,
                processed.triggered_secret
            )

            # Update conversation context
            conversation_context += f"\nDetective: {detective_message}"

            response = self.suspect_client.generate_response(
                player_message=detective_message,
                conversation_context=conversation_context,
                established_facts=established_facts,
                prompt_modifiers=prompt_modifiers,
                evidence_image_data=None,  # Test bench doesn't use visual evidence
                evidence_image_mime="image/png",
            )

            # Update context with response
            conversation_context += f"\nUnit 734: {response.verbal_response.speech}"

            # Track new facts
            if response.state_changes.new_facts:
                established_facts.extend(response.state_changes.new_facts)

            # Update detective's history
            self.detective.add_suspect_response(response.verbal_response.speech)

            if self.verbose:
                print(f"\n🤖 UNIT 734: {response.verbal_response.speech}")
                print(f"   [Internal: {response.internal_monologue.situation_assessment[:100]}...]")
                print(f"   [State: {response.emotional_state} | Load: {self.psychology.cognitive.load:.0f}%]")

            # Get current state
            ui_state = self.manager.get_state_for_ui()

            # Record turn
            sim_turn = SimulationTurn(
                turn_number=turn,
                detective_message=detective_message,
                detected_tactic=processed.detected_tactic.value,
                suspect_speech=response.verbal_response.speech,
                suspect_internal=response.internal_monologue.situation_assessment,
                emotional_state=response.emotional_state.value,
                cognitive_load=ui_state["cognitive"]["load"],
                mask_divergence=ui_state["mask"]["divergence"],
                pillar_health={k: v["health"] for k, v in ui_state["pillars"].items()},
                tells_shown=response.verbal_response.visible_tells,
            )
            self.transcript.turns.append(sim_turn)

            # Check for game over
            game_result = self.manager.check_game_over()
            if game_result["is_over"]:
                self.transcript.outcome = game_result["outcome"]
                self.transcript.outcome_reason = game_result["reason"]
                self.transcript.final_stats = game_result["stats"]

                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"GAME OVER: {game_result['outcome'].upper()}")
                    print(f"Reason: {game_result['reason']}")
                    print(f"{'='*60}")

                break

        # Finalize transcript
        self.transcript.end_time = datetime.now().isoformat()
        self.transcript.total_turns = len(self.transcript.turns)

        if self.transcript.outcome is None:
            # Timeout without resolution
            self.transcript.outcome = "timeout"
            self.transcript.outcome_reason = f"Max turns ({self.max_turns}) reached"

        return self.transcript


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Run AI vs AI interrogation simulation"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["aggressive", "empathetic", "logical", "mixed", "random"],
        default="mixed",
        help="Detective interrogation strategy"
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=20,
        help="Maximum number of turns"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: data/simulations/sim_<timestamp>.json)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    # Map strategy string to enum
    strategy_map = {
        "aggressive": InterrogationStrategy.AGGRESSIVE,
        "empathetic": InterrogationStrategy.EMPATHETIC,
        "logical": InterrogationStrategy.LOGICAL,
        "mixed": InterrogationStrategy.MIXED,
        "random": InterrogationStrategy.RANDOM,
    }
    strategy = strategy_map[args.strategy]

    # Run simulation
    runner = SimulationRunner(
        strategy=strategy,
        max_turns=args.turns,
        verbose=not args.quiet
    )

    transcript = runner.run()

    # Save transcript
    output_path = transcript.save(args.output)

    print(f"\n✅ Simulation complete!")
    print(f"   Outcome: {transcript.outcome}")
    print(f"   Turns: {transcript.total_turns}")
    print(f"   Transcript: {output_path}")


if __name__ == "__main__":
    main()
