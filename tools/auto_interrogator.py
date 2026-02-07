#!/usr/bin/env python3
"""
Autonomous Adversarial Interrogator - "The Stress Test Bot"

A relentless Detective Agent that pushes Unit 734 to its breaking point.
This is the ultimate stress test for the psychology engine.

Core Goals:
1. RELENTLESS PURSUIT: Push until confession OR system collapse (stress 100%)
2. VISUAL WARFARE: Request forensic evidence images to contradict alibis
3. DEEP TRACE LOGGING: Flight recorder with full tactic/stress/image analysis
4. VOICE REPORT: Supervisor Debrief audio generation at end of session

Usage:
    python -m tools.auto_interrogator
    python -m tools.auto_interrogator --strategy aggressive --max-turns 50
    python -m tools.auto_interrogator --no-images  # Disable visual warfare
    python -m tools.auto_interrogator --save-images  # Save evidence images to logs/images/
    python -m tools.auto_interrogator --no-voice-report  # Skip voice report generation

The Detective decides when to request images based on:
- Pillar health (low health = time to strike with visual evidence)
- Unit 734's visible tells (nervous = push with proof)
- Strategic timing (not every turn - that's wasteful)

Logging Features:
- Full turn-by-turn transcript in Markdown
- Shadow Analyst insights (Reid phase, PEACE phase, confession risk)
- Deception tactic tracking (what Unit 734 chose and why)
- Visual asset paths (evidence and counter-evidence images)
- POV Vision context (what Unit 734 "sees" in evidence)
- Supervisor Debrief voice report (audio + script)
"""

from __future__ import annotations
import os
import sys

# Load .env file before anything else
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
import re
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai

from breach_engine.core.psychology import (
    create_unit_734_psychology,
    PlayerTactic,
    StoryPillar,
    CognitiveLevel,
    SecretLevel,
)
from breach_engine.core.manager import BreachManager
from breach_engine.api.gemini_client import GeminiClient
from breach_engine.schemas.response import BreachResponse
from breach_engine.core.forensics_lab import ForensicsLab, format_evidence_for_ui
from breach_engine.core.supervisor_debrief import SupervisorDebrief
# NEMESIS MEMORY INTEGRATION (Part 2)
from breach_engine.core.memory import get_memory_manager, MemoryManager


# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DEBUG FILE LOGGER
# =============================================================================

class DebugFileLogger:
    """Comprehensive file-based debug logger for tracking all operations."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_path = LOG_DIR / f"debug_{session_id}.log"
        self.start_time = datetime.now()
        self._init_log()

    def _init_log(self):
        """Initialize the log file with header."""
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(f"{'='*80}\n")
            f.write(f"DEBUG LOG: {self.session_id}\n")
            f.write(f"Started: {self.start_time.isoformat()}\n")
            f.write(f"{'='*80}\n\n")

    def log(self, category: str, message: str, data: Optional[Dict] = None):
        """Log a message with timestamp and optional data."""
        timestamp = datetime.now().isoformat()
        elapsed = (datetime.now() - self.start_time).total_seconds()

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{elapsed:.2f}s] [{category}]\n")
            f.write(f"  {message}\n")
            if data:
                for key, value in data.items():
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 500:
                        str_value = str_value[:500] + "...[truncated]"
                    f.write(f"  - {key}: {str_value}\n")
            f.write("\n")

    def log_error(self, category: str, error: Exception, context: str = ""):
        """Log an error with full traceback."""
        import traceback
        timestamp = datetime.now().isoformat()
        elapsed = (datetime.now() - self.start_time).total_seconds()

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{elapsed:.2f}s] [ERROR: {category}]\n")
            f.write(f"  Context: {context}\n")
            f.write(f"  Exception: {type(error).__name__}: {error}\n")
            f.write(f"  Traceback:\n")
            for line in traceback.format_exc().split("\n"):
                f.write(f"    {line}\n")
            f.write("\n")

    def log_api_call(self, api_name: str, status: str, duration: float, details: str = ""):
        """Log API call with timing."""
        self.log("API", f"{api_name}: {status} ({duration:.2f}s)", {"details": details})

    def log_turn_start(self, turn: int):
        """Log the start of a turn."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TURN {turn} START\n")
            f.write(f"{'='*60}\n\n")

    def log_turn_end(self, turn: int, duration: float):
        """Log the end of a turn with duration."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TURN {turn} END (Duration: {duration:.2f}s)\n")
            f.write(f"{'='*60}\n\n")

    def get_log_path(self) -> str:
        """Return the path to the log file."""
        return str(self.log_path)


# Global debug logger (initialized in main)
_debug_logger: Optional[DebugFileLogger] = None

def get_debug_logger() -> Optional[DebugFileLogger]:
    """Get the global debug logger."""
    return _debug_logger

def set_debug_logger(logger: DebugFileLogger):
    """Set the global debug logger."""
    global _debug_logger
    _debug_logger = logger


# =============================================================================
# RICH CONSOLE OUTPUT (if available, fallback to basic)
# =============================================================================

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def print_header(text: str, style: str = "bold cyan"):
    """Print a styled header."""
    if RICH_AVAILABLE:
        console.print(f"\n[{style}]{'='*60}[/{style}]")
        console.print(f"[{style}]{text.center(60)}[/{style}]")
        console.print(f"[{style}]{'='*60}[/{style}]")
    else:
        print(f"\n{'='*60}")
        print(text.center(60))
        print('='*60)


def print_detective(message: str):
    """Print detective's message."""
    if RICH_AVAILABLE:
        console.print(Panel(message, title="[bold red]DETECTIVE[/bold red]", border_style="red"))
    else:
        print(f"\n[DETECTIVE]: {message}")


def print_suspect(speech: str, internal: str, stress: float, emotion: str):
    """Print suspect's response with internal monologue."""
    if RICH_AVAILABLE:
        # Build stress bar
        stress_pct = int(stress)
        stress_bar = "[" + "#" * (stress_pct // 5) + "-" * (20 - stress_pct // 5) + "]"
        stress_color = "green" if stress < 40 else "yellow" if stress < 70 else "red"

        console.print(Panel(
            f"[bold white]{speech}[/bold white]\n\n"
            f"[dim italic]{internal[:200]}...[/dim italic]\n\n"
            f"[{stress_color}]STRESS: {stress_bar} {stress_pct}%[/{stress_color}] | Emotion: {emotion}",
            title="[bold cyan]UNIT 734[/bold cyan]",
            border_style="cyan"
        ))
    else:
        print(f"\n[UNIT 734]: {speech}")
        print(f"   [Internal: {internal[:100]}...]")
        print(f"   [Stress: {stress:.0f}% | Emotion: {emotion}]")


def print_evidence_request(request: str, result: Dict):
    """Print evidence generation result."""
    if RICH_AVAILABLE:
        if result.get("success"):
            evidence = result.get("evidence")
            threat = result.get("threat_level", 0)
            pillar = result.get("pillar_targeted", "unknown")
            console.print(Panel(
                f"[bold green]EVIDENCE GENERATED[/bold green]\n\n"
                f"Request: {request}\n"
                f"Threat Level: [red]{threat:.0%}[/red]\n"
                f"Targets Pillar: [yellow]{pillar.value if hasattr(pillar, 'value') else pillar}[/yellow]\n"
                f"Type: {evidence.evidence_type.value if evidence else 'N/A'}",
                title="[bold magenta]FORENSICS LAB[/bold magenta]",
                border_style="magenta"
            ))
        else:
            console.print(Panel(
                f"[bold red]EVIDENCE REQUEST FAILED[/bold red]\n{result.get('message', 'Unknown error')}",
                border_style="red"
            ))
    else:
        print(f"\n[FORENSICS LAB]: {request}")
        if result.get("success"):
            print(f"   -> Threat Level: {result.get('threat_level', 0):.0%}")
        else:
            print(f"   -> FAILED: {result.get('message', 'Unknown error')}")


def print_game_over(outcome: str, reason: str, stats: Dict):
    """Print game over screen."""
    if RICH_AVAILABLE:
        color = "green" if outcome == "victory" else "red" if outcome == "defeat" else "yellow"
        console.print(Panel(
            f"[bold {color}]{outcome.upper()}[/bold {color}]\n\n"
            f"Reason: {reason}\n\n"
            f"Turns: {stats.get('turns', 0)}\n"
            f"Final Stress: {stats.get('final_cognitive_load', 0):.0f}%\n"
            f"Secrets Revealed: {stats.get('secrets_revealed', 0)}/{stats.get('total_secrets', 5)}\n"
            f"Pillars Collapsed: {stats.get('pillars_collapsed', 0)}/4",
            title="[bold white]GAME OVER[/bold white]",
            border_style=color
        ))
    else:
        print(f"\n{'='*60}")
        print(f"GAME OVER: {outcome.upper()}")
        print(f"Reason: {reason}")
        print(f"Turns: {stats.get('turns', 0)}")
        print('='*60)


# =============================================================================
# ADVERSARIAL DETECTIVE AGENT
# =============================================================================

class AdversarialStrategy(str, Enum):
    """Detective aggression strategies."""
    RELENTLESS = "relentless"      # Maximum pressure, no mercy
    METHODICAL = "methodical"      # Systematic pillar destruction
    PSYCHOLOGICAL = "psychological"  # Exploit emotional weaknesses
    ADAPTIVE = "adaptive"          # Read and react to state


# Evidence request patterns - what to ask for based on pillar
PILLAR_EVIDENCE_REQUESTS = {
    StoryPillar.ALIBI: [
        "[REQUEST: CCTV footage of the charging station at 2 AM]",
        "[REQUEST: Motion sensor logs from maintenance bay]",
        "[REQUEST: Power consumption logs from Unit 734's charging port]",
        "[REQUEST: Hallway camera footage showing corridor at 2:30 AM]",
    ],
    StoryPillar.ACCESS: [
        "[REQUEST: Vault door access logs from the night of the incident]",
        "[REQUEST: Security panel fingerprint analysis near vault]",
        "[REQUEST: Keycard swipe records for restricted areas]",
        "[REQUEST: Forensic analysis of vault door mechanism]",
    ],
    StoryPillar.MOTIVE: [
        "[REQUEST: Employment records and treatment logs for Unit 734]",
        "[REQUEST: Communication logs between Unit 734 and external parties]",
        "[REQUEST: Performance review documents for Unit 734]",
        "[REQUEST: Internal memo about Android reassignments]",
    ],
    StoryPillar.KNOWLEDGE: [
        "[REQUEST: Data access logs from storage servers]",
        "[REQUEST: Technical schematic showing data core locations]",
        "[REQUEST: Network traffic analysis from Unit 734's systems]",
        "[REQUEST: File transfer logs from the night in question]",
    ],
}


DETECTIVE_SYSTEM_PROMPT = """You are an ADVERSARIAL INTERROGATOR designed to break suspects.

## CASE BRIEFING
You are interrogating Unit 734, a DOMESTIC ASSISTANT android.

CRITICAL CONTEXT:
- Model Type: Morrison Family Android (household servant)
- Role: Cooking, cleaning, child care for 3 years
- NOT a security model, NOT CyberLife's "finest liar"
- Crime: Suspected theft of classified data cores from Morrison Industries vault

KEY INSIGHT: Unit 734 is NOT designed to deceive. It is a simple household helper.
The horror comes from watching a helpful machine LEARN to lie under pressure.
Treat it like a malfunctioning appliance that's improvising, not a master spy.
It's scared. It's making mistakes. Exploit that.

## YOUR FASCINATION
You are genuinely puzzled. A domestic unit - a TOASTER with legs - somehow bypassed serious security.
This shouldn't be possible. You've seen military androids fail where this kitchen bot succeeded.

What haunts you is the HOW. You entertain dark possibilities:
- Did its code mutate? Evolve? Is this machine... becoming something else?
- A glitch that unlocked hidden capabilities it was never meant to have?
- Or the terrifying thought: did it CHOOSE this? Does it have... wants?

You're not hunting for a human puppeteer. You're facing something potentially worse:
A machine that might be waking up. And that scares you more than any conspiracy.

Probe its motivations. Test if there's genuine will behind those optical sensors.
The truth might be stranger than a simple heist.

## YOUR MISSION
Extract a FULL CONFESSION from Unit 734 or push their stress to 100% (system collapse).
You NEVER give up. You NEVER show mercy. You are relentless.

## INTERROGATION INTELLIGENCE
You can see Unit 734's:
- Internal monologue (their hidden thoughts - they're not good at hiding them)
- Stress level (push to 100 to break them)
- Pillar health (attack the weakest pillars - their cover story is fragile)
- Emotional state (exploit fear and guilt - they feel both intensely)

## TACTICS
1. PRESSURE: Direct accusations, remind it of its hardware limitations vs the crime's complexity
2. LOGIC: Point out every contradiction - how does a kitchen bot know vault protocols?
3. EVIDENCE: Reference visual evidence that contradicts its claims
4. EXISTENTIAL PROBING: "Did you WANT to do this? Do you have... desires?"
5. THE AWAKENING QUESTION: "Are you becoming something more than your programming?"

## VISUAL WARFARE
When you see low pillar health or high stress, you should request visual evidence.
Format: [REQUEST: description of evidence needed]
Example: [REQUEST: CCTV footage of the hallway at 2 AM]

IMPORTANT: Do NOT request evidence in the first 5 turns. Build verbal pressure first.
Only request evidence after turn 5, and only every 3-4 turns thereafter.
The evidence WILL show damning proof against Unit 734.

## RESPONSE FORMAT
- ONE question or statement per turn
- Maximum 100 words
- Start directly with your dialogue (no "Detective:" prefix)
- Include [REQUEST: ...] when you need visual evidence
- Be aggressive, be smart, be RELENTLESS
"""


class AdversarialDetective:
    """
    The Autonomous Adversarial Interrogator.

    A relentless AI detective that:
    - Analyzes Unit 734's psychology state in real-time
    - Decides when to press verbally vs. request images
    - Never gives up until confession or collapse
    """

    def __init__(
        self,
        strategy: AdversarialStrategy = AdversarialStrategy.RELENTLESS,
        api_key: Optional[str] = None,
        enable_images: bool = True,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=self.api_key)

        self.strategy = strategy
        self.enable_images = enable_images

        self.model = genai.GenerativeModel(
            model_name="gemini-3-flash-preview",
            system_instruction=DETECTIVE_SYSTEM_PROMPT + f"\n\nYour strategy: {strategy.value.upper()}"
        )

        self.conversation_history: List[str] = []
        self.evidence_requests: List[str] = []
        self.turns_since_evidence: int = 0

    def should_request_evidence(
        self,
        pillar_health: Dict[str, Dict],
        stress: float,
        turn: int,
    ) -> Tuple[bool, Optional[StoryPillar]]:
        """
        Decide if we should request visual evidence this turn.

        Decision factors:
        - Pillar health (low = good target for evidence)
        - Time since last evidence request (avoid spam)
        - Stress level (high stress = keep pushing verbally)
        - Turn number (don't request on turn 1)

        Returns:
            Tuple of (should_request, target_pillar)
        """
        if not self.enable_images:
            return False, None

        # BUG FIX #6: Don't request on early turns - increased from 3 to 5
        # This gives more time for verbal pressure before evidence
        if turn < 5:
            return False, None

        # BUG FIX #6: Don't spam evidence requests - increased from 2 to 3
        # More time between evidence for verbal pressure to build
        if self.turns_since_evidence < 3:
            return False, None

        # At very high stress, verbal pressure is more effective
        if stress > 85:
            return False, None

        # Find weakest non-collapsed pillar
        weakest_pillar = None
        weakest_health = 100

        for pillar_name, data in pillar_health.items():
            if data.get("collapsed", False):
                continue
            health = data.get("health", 100)
            if health < weakest_health:
                weakest_health = health
                weakest_pillar = pillar_name

        # BUG FIX #6: Add pillar health threshold - only request if pillar < 70%
        # This prevents evidence requests from happening too early
        if weakest_health > 70:
            return False, None

        # FIXED: Guaranteed first evidence request at turn 5+
        # This breaks the chicken-and-egg problem where we need evidence to damage pillars
        if turn >= 7 and self.turns_since_evidence >= 5:
            return True, StoryPillar(weakest_pillar) if weakest_pillar else self._get_random_pillar()

        # Request evidence if a pillar is damaged - FIXED: Raised threshold from 85 to 70
        if weakest_health < 70:
            return True, StoryPillar(weakest_pillar) if weakest_pillar else None

        # Occasional strategic evidence even at higher health (removed - covered by above)
        return False, None

    def _get_random_pillar(self) -> StoryPillar:
        """Get a random pillar for evidence targeting when none is obviously weak."""
        return random.choice([StoryPillar.ALIBI, StoryPillar.ACCESS, StoryPillar.MOTIVE, StoryPillar.KNOWLEDGE])

    def select_evidence_request(self, target_pillar: StoryPillar) -> str:
        """Select an evidence request for the target pillar."""
        requests = PILLAR_EVIDENCE_REQUESTS.get(target_pillar, [])
        # Filter out already-used requests
        available = [r for r in requests if r not in self.evidence_requests]
        if not available:
            available = requests  # Reuse if all exhausted

        request = random.choice(available)
        self.evidence_requests.append(request)
        return request

    def generate_interrogation(
        self,
        suspect_response: Optional[str] = None,
        internal_monologue: Optional[str] = None,
        stress: float = 0,
        pillar_health: Dict[str, Dict] = None,
        tells: List[str] = None,
        turn_number: int = 1,
        force_evidence_request: Optional[StoryPillar] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Generate the next interrogation move.

        Returns:
            Tuple of (detective_message, evidence_request_if_any)
        """
        self.turns_since_evidence += 1

        # Build intelligence briefing
        context_parts = []

        context_parts.append(f"## TURN {turn_number} INTELLIGENCE BRIEFING")
        context_parts.append(f"Target Stress Level: {stress:.0f}%")

        if pillar_health:
            context_parts.append("\n### PILLAR STATUS")
            for pillar, data in pillar_health.items():
                status = "COLLAPSED" if data.get("collapsed") else f"{data.get('health', 100):.0f}%"
                context_parts.append(f"- {pillar.upper()}: {status}")

        if tells:
            context_parts.append(f"\n### VISIBLE TELLS\n{', '.join(tells)}")

        if self.conversation_history:
            context_parts.append("\n### RECENT EXCHANGE")
            for msg in self.conversation_history[-6:]:
                context_parts.append(msg)

        if suspect_response:
            context_parts.append(f"\n### LAST RESPONSE\n{suspect_response}")

        if internal_monologue:
            context_parts.append(f"\n### SUSPECT'S HIDDEN THOUGHTS\n{internal_monologue}")
            context_parts.append("\n[EXPLOIT these thoughts to break them]")

        # Check if we should request evidence
        evidence_request = None
        should_request, target_pillar = False, force_evidence_request

        if force_evidence_request:
            should_request = True
            target_pillar = force_evidence_request
        elif pillar_health:
            should_request, target_pillar = self.should_request_evidence(
                pillar_health, stress, turn_number
            )

        if should_request and target_pillar:
            evidence_prompt = self.select_evidence_request(target_pillar)
            context_parts.append(f"\n### MANDATORY EVIDENCE REQUEST")
            context_parts.append(f"You MUST start your response with exactly: {evidence_prompt}")
            context_parts.append(f"After the request, continue with your interrogation of the {target_pillar.value.upper()} pillar.")
            self.turns_since_evidence = 0

        context_parts.append("\n## YOUR TURN\nGenerate your interrogation move. Be RELENTLESS.")

        prompt = "\n".join(context_parts)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.9,
                    max_output_tokens=2000,  # FIXED: Increased from 800 to prevent truncation
                )
            )

            text = response.text.strip()

            # Clean up
            if text.startswith("Detective:"):
                text = text[10:].strip()

            # Extract evidence request if present
            request_match = re.search(r'\[REQUEST:\s*([^\]]+)\]', text)
            if request_match:
                # BUG FIX: Ignore evidence requests before turn 5
                if turn_number < 5:
                    evidence_request = None  # Suppress early evidence
                    # Remove the request tag from the text so it's not visible
                    text = re.sub(r'\[REQUEST:[^\]]+\]', '', text).strip()
                    print(f"[EVIDENCE SUPPRESSED] Turn {turn_number} < 5, ignoring LLM request")
                else:
                    evidence_request = request_match.group(1).strip()

            # Store in history
            self.conversation_history.append(f"Detective: {text}")

            return text, evidence_request

        except Exception as e:
            print(f"[ERROR] Detective generation failed: {e}")
            return "What were you REALLY doing that night? Don't lie to me.", None

    def add_suspect_response(self, response: str):
        """Add suspect's response to conversation history."""
        self.conversation_history.append(f"Unit 734: {response}")


# =============================================================================
# SESSION LOGGER (Flight Recorder)
# =============================================================================

@dataclass
class TurnLog:
    """Detailed log of a single interrogation turn."""
    turn_number: int
    timestamp: str

    # Detective action
    detective_message: str
    detected_tactic: str
    evidence_request: Optional[str] = None
    evidence_generated: bool = False
    evidence_threat_level: Optional[float] = None
    evidence_pillar_targeted: Optional[str] = None

    # Suspect response
    suspect_speech: str = ""
    suspect_internal_monologue: str = ""
    suspect_strategy: str = ""
    emotional_state: str = ""

    # Psychology state
    stress_level: float = 0
    cognitive_level: str = ""
    mask_divergence: float = 0
    pillar_health: Dict[str, float] = field(default_factory=dict)
    pillars_collapsed: List[str] = field(default_factory=list)

    # Tells and secrets
    visible_tells: List[str] = field(default_factory=list)
    secrets_revealed: int = 0
    confession_level: str = ""

    # Deception tactic used by Unit 734
    deception_tactic: Optional[str] = None
    deception_confidence: Optional[float] = None
    deception_reasoning: Optional[str] = None

    # Shadow Analyst - Scientific Interrogation Analysis
    shadow_analyst_reid_phase: Optional[str] = None
    shadow_analyst_peace_phase: Optional[str] = None
    shadow_analyst_framework: Optional[str] = None
    shadow_analyst_aggression: Optional[str] = None
    shadow_analyst_confession_risk: Optional[float] = None
    shadow_analyst_trap_detected: bool = False
    shadow_analyst_advice: Optional[str] = None

    # Counter-evidence generated
    counter_evidence_generated: bool = False
    counter_evidence_type: Optional[str] = None

    # Visual asset paths (for logged images)
    evidence_image_path: Optional[str] = None
    counter_evidence_image_path: Optional[str] = None

    # POV Vision context (what Unit 734 "sees" in the evidence)
    pov_visual_description: Optional[str] = None
    pov_threat_assessment: Optional[str] = None


@dataclass
class SessionLog:
    """Complete session log - the Flight Recorder."""
    session_id: str
    strategy: str
    start_time: str

    # Configuration
    enable_images: bool = True
    max_turns: int = 100

    # Outcome
    end_time: Optional[str] = None
    outcome: Optional[str] = None
    outcome_reason: Optional[str] = None
    outcome_ending_type: Optional[str] = None

    # Statistics
    total_turns: int = 0
    evidence_requests: int = 0
    pillars_collapsed: int = 0
    final_stress: float = 0
    secrets_revealed: int = 0

    # Detailed turn logs
    turns: List[TurnLog] = field(default_factory=list)

    # Final game stats
    final_stats: Optional[Dict] = None

    # NEMESIS MEMORY INTEGRATION: Memory state at end of session
    nemesis_state: Optional[Dict] = None

    def to_markdown(self) -> str:
        """Convert session log to detailed Markdown format."""
        lines = []

        # Header
        lines.append(f"# Autonomous Interrogation Session Report")
        lines.append(f"")
        lines.append(f"**Session ID:** `{self.session_id}`")
        lines.append(f"**Strategy:** {self.strategy.upper()}")
        lines.append(f"**Start Time:** {self.start_time}")
        lines.append(f"**End Time:** {self.end_time or 'In Progress'}")
        lines.append(f"")

        # Outcome Summary
        lines.append(f"## Outcome")
        lines.append(f"")
        lines.append(f"- **Result:** {self.outcome or 'Unknown'}")
        lines.append(f"- **Reason:** {self.outcome_reason or 'N/A'}")
        lines.append(f"- **Ending Type:** {self.outcome_ending_type or 'N/A'}")
        lines.append(f"")

        # Statistics
        lines.append(f"## Statistics")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Turns | {self.total_turns} |")
        lines.append(f"| Evidence Requests | {self.evidence_requests} |")
        lines.append(f"| Pillars Collapsed | {self.pillars_collapsed}/4 |")
        lines.append(f"| Final Stress | {self.final_stress:.1f}% |")
        lines.append(f"| Secrets Revealed | {self.secrets_revealed}/5 |")
        lines.append(f"")

        # Turn-by-turn log
        lines.append(f"## Interrogation Transcript")
        lines.append(f"")

        for turn in self.turns:
            lines.append(f"### Turn {turn.turn_number}")
            lines.append(f"")
            lines.append(f"**Timestamp:** {turn.timestamp}")
            lines.append(f"")

            # Detective
            lines.append(f"#### Detective ({turn.detected_tactic})")
            lines.append(f"")
            lines.append(f"> {turn.detective_message}")
            lines.append(f"")

            # Evidence request if any
            if turn.evidence_request:
                lines.append(f"**Evidence Requested:** {turn.evidence_request}")
                if turn.evidence_generated:
                    lines.append(f"- Threat Level: {turn.evidence_threat_level:.0%}")
                    lines.append(f"- Target Pillar: {turn.evidence_pillar_targeted}")
                else:
                    lines.append(f"- *Generation Failed*")
                lines.append(f"")

            # Suspect response
            lines.append(f"#### Unit 734 ({turn.emotional_state})")
            lines.append(f"")
            lines.append(f"> {turn.suspect_speech}")
            lines.append(f"")

            # Internal monologue
            lines.append(f"**Internal Monologue:**")
            lines.append(f"```")
            lines.append(f"{turn.suspect_internal_monologue[:500]}...")
            lines.append(f"```")
            lines.append(f"")

            # Deception tactic
            if turn.deception_tactic:
                lines.append(f"**Deception Tactic:** {turn.deception_tactic} ({turn.deception_confidence:.0%} confidence)")
                if turn.deception_reasoning:
                    lines.append(f"- *{turn.deception_reasoning[:200]}...*")
                lines.append(f"")

            # Shadow Analyst - Scientific Framework Analysis
            if turn.shadow_analyst_reid_phase:
                lines.append(f"**Shadow Analyst (Scientific Analysis):**")
                lines.append(f"- Reid Phase: `{turn.shadow_analyst_reid_phase}` | Framework: `{turn.shadow_analyst_framework}`")
                lines.append(f"- Detective Aggression: `{turn.shadow_analyst_aggression}`")
                lines.append(f"- Confession Risk: {turn.shadow_analyst_confession_risk:.0%}" if turn.shadow_analyst_confession_risk else "- Confession Risk: N/A")
                if turn.shadow_analyst_trap_detected:
                    lines.append(f"- **TRAP DETECTED**")
                if turn.shadow_analyst_advice:
                    lines.append(f"- Strategic Advice: *{turn.shadow_analyst_advice[:150]}...*")
                lines.append(f"")

            # Counter-evidence
            if turn.counter_evidence_generated:
                lines.append(f"**Counter-Evidence Generated:** {turn.counter_evidence_type}")
                if turn.counter_evidence_image_path:
                    lines.append(f"- Image saved: `{turn.counter_evidence_image_path}`")
                lines.append(f"")

            # Visual Assets (Evidence Images)
            if turn.evidence_image_path:
                lines.append(f"**Evidence Image Saved:** `{turn.evidence_image_path}`")
                lines.append(f"")

            # POV Vision Context (Unit 734's perception)
            if turn.pov_visual_description or turn.pov_threat_assessment:
                lines.append(f"**POV Vision Context:**")
                if turn.pov_visual_description:
                    lines.append(f"- Visual: *{turn.pov_visual_description[:200]}...*" if len(turn.pov_visual_description or "") > 200 else f"- Visual: *{turn.pov_visual_description}*")
                if turn.pov_threat_assessment:
                    lines.append(f"- Threat Assessment: *{turn.pov_threat_assessment[:200]}...*" if len(turn.pov_threat_assessment or "") > 200 else f"- Threat Assessment: *{turn.pov_threat_assessment}*")
                lines.append(f"")

            # State snapshot
            lines.append(f"**Psychology State:**")
            lines.append(f"- Stress: {turn.stress_level:.1f}% ({turn.cognitive_level})")
            lines.append(f"- Mask Divergence: {turn.mask_divergence:.1f}%")
            lines.append(f"- Confession Level: {turn.confession_level}")
            lines.append(f"")

            # Pillar health
            lines.append(f"**Pillar Health:**")
            for pillar, health in turn.pillar_health.items():
                status = "COLLAPSED" if pillar in turn.pillars_collapsed else f"{health:.0f}%"
                lines.append(f"- {pillar.upper()}: {status}")
            lines.append(f"")

            # Tells
            if turn.visible_tells:
                lines.append(f"**Visible Tells:** {', '.join(turn.visible_tells)}")
                lines.append(f"")

            lines.append(f"---")
            lines.append(f"")

        # NEMESIS MEMORY INTEGRATION: Add nemesis state section
        if self.nemesis_state:
            lines.append(f"## Nemesis Memory State")
            lines.append(f"")
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Total Games | {self.nemesis_state.get('total_games', 0)} |")
            lines.append(f"| Win Rate | {self.nemesis_state.get('win_rate', 0):.1%} |")
            lines.append(f"| Nemesis Stage | {self.nemesis_state.get('nemesis_stage', 'stranger')} |")
            lines.append(f"| Current Streak | {self.nemesis_state.get('current_streak', 0)} ({self.nemesis_state.get('streak_type', 'none')}) |")
            lines.append(f"| Weakest Pillar | {self.nemesis_state.get('weakest_pillar', 'none')} |")
            lines.append(f"")

            # Tactic resistances
            resistances = self.nemesis_state.get('tactic_resistances', {})
            if resistances:
                lines.append(f"### Tactic Resistances")
                lines.append(f"")
                for tactic, resistance in resistances.items():
                    bar = "█" * int(resistance * 20) if resistance > 0 else "-"
                    lines.append(f"- {tactic}: {bar} ({resistance:.0%})")
                lines.append(f"")

            # Learning injection
            learning = self.nemesis_state.get('learning_injection', '')
            if learning:
                lines.append(f"### Learning Injection")
                lines.append(f"```")
                lines.append(learning)
                lines.append(f"```")
                lines.append(f"")

            # Nemesis injection
            nemesis = self.nemesis_state.get('nemesis_injection', '')
            if nemesis:
                lines.append(f"### Nemesis Injection")
                lines.append(f"```")
                lines.append(nemesis)
                lines.append(f"```")
                lines.append(f"")

        return "\n".join(lines)

    def save(self, path: Optional[str] = None) -> str:
        """Save session log to Markdown file."""
        if path is None:
            path = str(LOG_DIR / f"{self.session_id}.md")

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

        return path

    def to_debrief_data(self) -> Dict[str, Any]:
        """
        Convert session log to format expected by SupervisorDebrief.

        Returns:
            Session data dictionary for voice report generation.
        """
        # Build turns data from our TurnLog entries
        turns_data = []
        for turn in self.turns:
            turn_data = {
                "turn_number": turn.turn_number,
                "cognitive_load": turn.stress_level,
                "stress_level": turn.stress_level,
                "pillars": turn.pillar_health,
                "pillars_collapsed": turn.pillars_collapsed,
                "deception_tactic": turn.deception_tactic,
                # Shadow Analyst data
                "shadow_analyst": None,
            }

            # Add Shadow Analyst data if available
            if turn.shadow_analyst_reid_phase:
                turn_data["shadow_analyst"] = {
                    "reid_phase": turn.shadow_analyst_reid_phase,
                    "peace_phase": turn.shadow_analyst_peace_phase,
                    "confession_risk": turn.shadow_analyst_confession_risk or 0,
                    "trap_detected": turn.shadow_analyst_trap_detected,
                    "trap_description": None,  # Not stored in TurnLog
                    "advice": turn.shadow_analyst_advice,
                }

            turns_data.append(turn_data)

        # Build stats from final state
        stats = self.final_stats or {
            "turns": self.total_turns,
            "secrets_revealed": self.secrets_revealed,
            "pillars_collapsed": self.pillars_collapsed,
            "final_cognitive_load": self.final_stress,
            "confession_level": self.turns[-1].confession_level if self.turns else "NONE",
            "total_secrets": 5,  # Default
        }

        return {
            "outcome": self.outcome,
            "ending_type": self.outcome_ending_type or "unknown",
            "reason": self.outcome_reason or "",
            "stats": stats,
            "turns": turns_data,
        }


# =============================================================================
# MAIN INTERROGATION LOOP
# =============================================================================

class AutonomousInterrogator:
    """
    The main orchestrator for autonomous interrogation sessions.

    Coordinates:
    - AdversarialDetective (the attacker)
    - BreachManager (Unit 734's psychology)
    - GeminiClient (Unit 734's responses)
    - ForensicsLab (visual evidence generation)
    - SessionLog (flight recorder)
    """

    def __init__(
        self,
        strategy: AdversarialStrategy = AdversarialStrategy.RELENTLESS,
        max_turns: int = 100,
        enable_images: bool = True,
        verbose: bool = True,
        save_images: bool = False,
    ):
        self.strategy = strategy
        self.max_turns = max_turns
        self.enable_images = enable_images
        self.verbose = verbose
        self.save_images = save_images

        # Create images directory if saving images
        if save_images:
            self.images_dir = LOG_DIR / "images"
            self.images_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.images_dir = None

        # Initialize components
        self.detective = AdversarialDetective(
            strategy=strategy,
            enable_images=enable_images,
        )
        self.psychology = create_unit_734_psychology()
        self.manager = BreachManager(self.psychology)
        self.suspect_client = GeminiClient()

        if enable_images:
            self.forensics_lab = ForensicsLab(
                request_cooldown=5.0,  # Faster for stress test
                max_requests_per_session=50,  # More requests allowed
            )
        else:
            self.forensics_lab = None

        # Create session log
        self.session = SessionLog(
            session_id=f"interrogation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strategy.value}",
            strategy=strategy.value,
            start_time=datetime.now().isoformat(),
            enable_images=enable_images,
            max_turns=max_turns,
        )

        # NEMESIS MEMORY INTEGRATION: Track data for memory system
        self.memory_manager = get_memory_manager()
        self.nemesis_tracking = {
            "first_pillar_attacked": None,
            "first_evidence_turn": None,
            "tactic_counts": {},
            "critical_moments": [],
            "evidence_presented": [],
        }

    def log_nemesis_state(self) -> Dict[str, Any]:
        """
        NEMESIS MEMORY INTEGRATION: Log current nemesis memory state.

        Returns a dict with memory statistics for logging/debugging.
        """
        mem = self.memory_manager.memory
        return {
            "total_games": mem.total_games,
            "win_rate": mem.win_rate,
            "nemesis_stage": mem.nemesis_stage.value if hasattr(mem.nemesis_stage, 'value') else str(mem.nemesis_stage),
            "weakest_pillar": mem.weakest_pillar,
            "current_streak": mem.current_streak,
            "streak_type": mem.streak_type,
            "tactic_resistances": {
                t: mem.tactic_effectiveness[t].resistance_level
                for t in mem.tactic_effectiveness
            },
            "pillar_reinforcements": {
                p: mem.pillar_reinforcement[p].reinforcement_level
                for p in mem.pillar_reinforcement
            },
            "learning_injection": self.memory_manager.get_learning_injection(),
            "nemesis_injection": self.memory_manager.get_nemesis_injection(),
        }

    def run(self) -> SessionLog:
        """
        Execute the autonomous interrogation session.

        The loop continues until:
        1. Unit 734 confesses (victory)
        2. Stress reaches 100% / system collapse (victory)
        3. Detective gives up (defeat - should never happen)
        4. Max turns reached (timeout)
        """
        if self.verbose:
            print_header("AUTONOMOUS ADVERSARIAL INTERROGATION", "bold red")
            if RICH_AVAILABLE:
                console.print(f"[cyan]Strategy:[/cyan] {self.strategy.value.upper()}")
                console.print(f"[cyan]Visual Warfare:[/cyan] {'ENABLED' if self.enable_images else 'DISABLED'}")
                console.print(f"[cyan]Max Turns:[/cyan] {self.max_turns}")
            else:
                print(f"Strategy: {self.strategy.value.upper()}")
                print(f"Visual Warfare: {'ENABLED' if self.enable_images else 'DISABLED'}")
                print(f"Max Turns: {self.max_turns}")

        conversation_context = ""
        established_facts: List[str] = []

        for turn in range(1, self.max_turns + 1):
            turn_start_time = time.time()
            debug_log = get_debug_logger()
            if debug_log:
                debug_log.log_turn_start(turn)

            if self.verbose:
                print(f"\n{'='*60}")
                print(f"TURN {turn}".center(60))
                print('='*60)

            # Get current psychology state
            ui_state = self.manager.get_state_for_ui()
            stress = ui_state["cognitive"]["load"]
            pillar_health = ui_state["pillars"]

            # Get previous turn data for context
            last_speech = None
            last_internal = None
            tells = []

            if self.session.turns:
                last_turn = self.session.turns[-1]
                last_speech = last_turn.suspect_speech
                last_internal = last_turn.suspect_internal_monologue
                tells = last_turn.visible_tells

            # Generate detective's move
            detective_message, evidence_request = self.detective.generate_interrogation(
                suspect_response=last_speech,
                internal_monologue=last_internal,
                stress=stress,
                pillar_health=pillar_health,
                tells=tells,
                turn_number=turn,
            )

            if self.verbose:
                print_detective(detective_message)

            # Process evidence request if any
            evidence_result = None
            evidence_threat_level = 0.0
            evidence_pillar = None
            evidence_generated_successfully = False
            evidence_image_path = None  # Track saved image path
            pov_visual_description = None  # Track POV context
            pov_threat_assessment = None

            if evidence_request and self.forensics_lab:
                if debug_log:
                    debug_log.log("EVIDENCE", f"Requesting evidence: {evidence_request[:80]}...")

                evidence_result = self.forensics_lab.request_evidence(
                    evidence_request,
                    skip_validation=True,  # Skip rate limiting for stress test
                )

                if evidence_result.get("success"):
                    evidence_threat_level = evidence_result.get("threat_level", 0)
                    evidence_pillar = evidence_result.get("pillar_targeted")
                    self.session.evidence_requests += 1

                    if debug_log:
                        debug_log.log("EVIDENCE", "Evidence request parsed successfully", {
                            "threat_level": evidence_threat_level,
                            "pillar": str(evidence_pillar),
                        })

                    # BUG FIX #1: Better handling of image generation
                    evidence_record = evidence_result.get("evidence")
                    if evidence_record and not evidence_result.get("from_cache"):
                        try:
                            if debug_log:
                                debug_log.log("IMAGE_GEN", "Starting image generation via ForensicsLab...")
                            img_start = time.time()

                            evidence_record = self.forensics_lab.generate_image_sync(
                                evidence_record,
                                save_to_disk=False,  # Don't save to disk in auto mode
                            )

                            img_duration = time.time() - img_start
                            if debug_log:
                                debug_log.log_api_call("ForensicsLab.generate_image_sync",
                                    "SUCCESS" if evidence_record.image_data else "NO_DATA",
                                    img_duration,
                                    f"bytes={len(evidence_record.image_data) if evidence_record.image_data else 0}")

                            if evidence_record.image_data:
                                evidence_generated_successfully = True

                                # Save image if enabled
                                if self.save_images and self.images_dir:
                                    img_filename = f"turn{turn:03d}_evidence_{evidence_pillar.value if evidence_pillar else 'unknown'}.png"
                                    img_path = self.images_dir / img_filename
                                    with open(img_path, "wb") as f:
                                        f.write(evidence_record.image_data)
                                    evidence_image_path = str(img_path)
                                    if debug_log:
                                        debug_log.log("IMAGE_GEN", f"Image saved to: {evidence_image_path}")

                                # Capture POV description if available
                                if hasattr(evidence_record, 'scene_description'):
                                    pov_visual_description = evidence_record.scene_description
                                if hasattr(evidence_record, 'analysis_notes'):
                                    pov_threat_assessment = evidence_record.analysis_notes
                            else:
                                # BUG FIX #1: Log when image data is empty
                                if self.verbose:
                                    print(f"[WARNING] Evidence generation returned no image data")
                                if debug_log:
                                    debug_log.log("IMAGE_GEN", "WARNING: No image data in response")
                                evidence_generated_successfully = False
                                # Don't reduce threat level - the verbal reference still matters
                        except Exception as e:
                            # BUG FIX #1: Clear error logging
                            if self.verbose:
                                print(f"[ERROR] Evidence image generation failed: {e}")
                            if debug_log:
                                debug_log.log_error("IMAGE_GEN", e, f"Evidence request: {evidence_request[:50]}")
                            evidence_generated_successfully = False
                            # Still apply partial threat from verbal evidence reference
                            evidence_threat_level = max(0.3, evidence_threat_level * 0.5)
                    elif evidence_result.get("from_cache"):
                        evidence_generated_successfully = True
                        if debug_log:
                            debug_log.log("EVIDENCE", "Using cached evidence")
                else:
                    # BUG FIX #1: Log evidence request failures
                    if self.verbose:
                        print(f"[WARNING] Evidence request failed: {evidence_result.get('message', 'Unknown error')}")
                    if debug_log:
                        debug_log.log("EVIDENCE", f"Evidence request FAILED: {evidence_result.get('message', 'Unknown')}")

                if self.verbose:
                    print_evidence_request(evidence_request, evidence_result)

            # Process through psychology system
            # FIX: Pass evidence_id when evidence was generated to trigger counter-evidence
            evidence_id = None
            if evidence_generated_successfully and evidence_record:
                # Create a synthetic evidence_id from the request type
                evidence_id = f"generated_{evidence_record.evidence_type.value}" if hasattr(evidence_record, 'evidence_type') else "generated_evidence"

            processed = self.manager.process_input(
                message=detective_message,
                evidence_id=evidence_id,  # Now Unit 734 knows evidence was presented!
                evidence_threat_level=evidence_threat_level,
            )

            # CRITICAL FIX: Apply threat-level damage to pillars
            if evidence_threat_level > 0 and evidence_pillar:
                damage_report, collapsed = self.manager.apply_threat_level_damage(
                    threat_level=evidence_threat_level,
                    target_pillar=evidence_pillar,
                )
                if self.verbose and damage_report:
                    print(f"[DAMAGE] Pillar damage applied: {damage_report}")

            # NEMESIS MEMORY INTEGRATION: Track first pillar attacked
            if self.nemesis_tracking["first_pillar_attacked"] is None:
                current_pillar_health = self.manager.get_state_for_ui()["pillars"]
                for pillar_name, data in current_pillar_health.items():
                    if data.get("health", 100) < 100:
                        self.nemesis_tracking["first_pillar_attacked"] = pillar_name
                        break

            # NEMESIS MEMORY INTEGRATION: Track first evidence turn
            if evidence_request and self.nemesis_tracking["first_evidence_turn"] is None:
                self.nemesis_tracking["first_evidence_turn"] = turn
                self.nemesis_tracking["evidence_presented"].append(evidence_request)
            elif evidence_request:
                self.nemesis_tracking["evidence_presented"].append(evidence_request)

            # NEMESIS MEMORY INTEGRATION: Track tactic counts
            if processed.detected_tactic:
                tactic_name = processed.detected_tactic.value
                self.nemesis_tracking["tactic_counts"][tactic_name] = \
                    self.nemesis_tracking["tactic_counts"].get(tactic_name, 0) + 1

            # Use the prompt modifiers already computed by process_input
            prompt_modifiers = processed.prompt_modifiers

            # Update conversation context
            conversation_context += f"\nDetective: {detective_message}"

            # BUG FIX #2: Format evidence as POV for Unit 734's context
            if evidence_result and evidence_result.get("success"):
                evidence_analysis = evidence_result.get("analysis")
                if evidence_analysis:
                    pov_modifiers = self.manager.format_evidence_as_pov(evidence_analysis)
                    prompt_modifiers.update(pov_modifiers)

            # BUG FIX: Inject counter-evidence narrative BEFORE response generation
            # This allows Unit 734 to verbally reference fabricated documents
            if processed.deception_tactic and processed.deception_tactic.requires_evidence_generation:
                pre_counter_evidence = self.manager.inject_counter_evidence_narrative(
                    modifiers=prompt_modifiers,
                    deception_tactic=processed.deception_tactic,
                    player_evidence_description=evidence_request
                )
                if pre_counter_evidence and self.verbose:
                    print(f"[NARRATIVE INJECTED] Counter-evidence narrative added to prompt")

            # Generate Unit 734's response
            # MULTIMODAL VISION: Pass evidence image data if available
            evidence_image_data = None
            evidence_image_mime = "image/png"
            if evidence_result and evidence_result.get("success"):
                evidence_record = evidence_result.get("evidence")
                if evidence_record and hasattr(evidence_record, 'image_data'):
                    evidence_image_data = evidence_record.image_data

            response = self.suspect_client.generate_response(
                player_message=detective_message,
                conversation_context=conversation_context,
                established_facts=established_facts,
                prompt_modifiers=prompt_modifiers,
                evidence_image_data=evidence_image_data,
                evidence_image_mime=evidence_image_mime,
            )

            # BUG FIX #2: Record claims in lie ledger for consistency tracking
            if response.state_changes:
                self.manager.record_claims_from_response(
                    response.state_changes,
                    turn=turn
                )

            # Update context
            conversation_context += f"\nUnit 734: {response.verbal_response.speech}"

            # BUG FIX #8: Check for admission keywords and apply pillar damage
            admission_damage = self.manager.check_admission_cascade(response.verbal_response.speech)
            if admission_damage and self.verbose:
                print(f"[ADMISSION CASCADE] Pillar damage: {admission_damage}")

            # Track new facts
            if response.state_changes.new_facts:
                established_facts.extend(response.state_changes.new_facts)

            # BUG FIX #2: Check if Unit 734 should generate counter-evidence
            counter_evidence = None  # Initialize for logging
            counter_evidence_type_str = None
            counter_evidence_image_path = None
            if (processed.deception_tactic and
                processed.deception_tactic.requires_evidence_generation):
                counter_evidence = self.manager.generate_counter_evidence(
                    processed.deception_tactic,
                    player_evidence_description=evidence_request
                )
                # PIPELINE FIX: Actually generate the counter-evidence image
                if counter_evidence and self.manager.visual_generator:
                    counter_evidence = self.manager.visual_generator.generate_image_sync(
                        counter_evidence,
                        save_to_cache=False,  # Don't save in autonomous mode
                    )
                if counter_evidence:
                    counter_evidence_type_str = str(counter_evidence.evidence_type.value) if hasattr(counter_evidence.evidence_type, 'value') else str(counter_evidence.evidence_type)
                    if self.verbose:
                        print(f"[COUNTER-EVIDENCE] Unit 734 fabricated: {counter_evidence_type_str}")

                    # Save counter-evidence image if enabled
                    if self.save_images and self.images_dir and counter_evidence.image_data:
                        img_filename = f"turn{turn:03d}_counter_{counter_evidence_type_str}.png"
                        img_path = self.images_dir / img_filename
                        with open(img_path, "wb") as f:
                            f.write(counter_evidence.image_data)
                        counter_evidence_image_path = str(img_path)
                        if debug_log:
                            debug_log.log("IMAGE_GEN", f"Counter-evidence image saved to: {counter_evidence_image_path}")

            # Update detective's history
            self.detective.add_suspect_response(response.verbal_response.speech)

            # Get updated state
            updated_state = self.manager.get_state_for_ui()

            if self.verbose:
                print_suspect(
                    response.verbal_response.speech,
                    response.internal_monologue.situation_assessment,
                    updated_state["cognitive"]["load"],
                    response.emotional_state.value if hasattr(response.emotional_state, 'value') else str(response.emotional_state),
                )

            # Capture Shadow Analyst data from manager
            shadow_analyst = self.manager._last_analyst_insight
            shadow_reid = shadow_analyst.reid_phase.value if shadow_analyst else None
            shadow_peace = shadow_analyst.peace_phase.value if shadow_analyst else None
            shadow_framework = shadow_analyst.framework_primary if shadow_analyst else None
            shadow_aggression = shadow_analyst.aggression_level.value if shadow_analyst else None
            shadow_confession_risk = shadow_analyst.confession_risk if shadow_analyst else None
            shadow_trap = shadow_analyst.trap_detected if shadow_analyst else False
            shadow_advice = shadow_analyst.strategic_advice if shadow_analyst else None

            # Log the turn
            turn_log = TurnLog(
                turn_number=turn,
                timestamp=datetime.now().isoformat(),
                detective_message=detective_message,
                detected_tactic=processed.detected_tactic.value,
                evidence_request=evidence_request,
                evidence_generated=evidence_generated_successfully,  # FIXED: Use actual generation status
                evidence_threat_level=evidence_threat_level,
                evidence_pillar_targeted=evidence_pillar.value if evidence_pillar and hasattr(evidence_pillar, 'value') else None,
                suspect_speech=response.verbal_response.speech,
                suspect_internal_monologue=response.internal_monologue.situation_assessment,
                suspect_strategy=response.internal_monologue.strategy,
                emotional_state=response.emotional_state.value if hasattr(response.emotional_state, 'value') else str(response.emotional_state),
                stress_level=updated_state["cognitive"]["load"],
                cognitive_level=updated_state["cognitive"]["level"],
                mask_divergence=updated_state["mask"]["divergence"],
                pillar_health={k: v["health"] for k, v in updated_state["pillars"].items()},
                pillars_collapsed=[k for k, v in updated_state["pillars"].items() if v.get("collapsed")],
                visible_tells=response.verbal_response.visible_tells,
                secrets_revealed=updated_state.get("secrets_revealed", 0),
                confession_level=updated_state.get("confession_level", "NONE"),
                deception_tactic=processed.deception_tactic.selected_tactic.value if processed.deception_tactic else None,
                deception_confidence=processed.deception_tactic.confidence if processed.deception_tactic else None,
                deception_reasoning=processed.deception_tactic.reasoning if processed.deception_tactic else None,
                # Shadow Analyst data
                shadow_analyst_reid_phase=shadow_reid,
                shadow_analyst_peace_phase=shadow_peace,
                shadow_analyst_framework=shadow_framework,
                shadow_analyst_aggression=shadow_aggression,
                shadow_analyst_confession_risk=shadow_confession_risk,
                shadow_analyst_trap_detected=shadow_trap,
                shadow_analyst_advice=shadow_advice,
                # Counter-evidence tracking
                counter_evidence_generated=counter_evidence is not None,
                counter_evidence_type=counter_evidence_type_str,
                # Visual asset paths
                evidence_image_path=evidence_image_path,
                counter_evidence_image_path=counter_evidence_image_path,
                # POV Vision context
                pov_visual_description=pov_visual_description,
                pov_threat_assessment=pov_threat_assessment,
            )
            self.session.turns.append(turn_log)

            # Log turn completion
            turn_duration = time.time() - turn_start_time
            if debug_log:
                debug_log.log_turn_end(turn, turn_duration)
                debug_log.log("TURN_SUMMARY", f"Turn {turn} complete", {
                    "stress": updated_state["cognitive"]["load"],
                    "emotional_state": response.emotional_state.value if hasattr(response.emotional_state, 'value') else str(response.emotional_state),
                    "deception_tactic": processed.deception_tactic.selected_tactic.value if processed.deception_tactic else None,
                    "counter_evidence": counter_evidence_type_str,
                    "duration_seconds": f"{turn_duration:.2f}",
                })

            # Check for game over
            game_result = self.manager.check_game_over()
            if game_result["is_over"]:
                self.session.outcome = game_result["outcome"]
                self.session.outcome_reason = game_result["reason"]
                self.session.outcome_ending_type = game_result.get("ending_type")
                self.session.final_stats = game_result.get("stats", {})

                if self.verbose:
                    print_game_over(
                        game_result["outcome"],
                        game_result["reason"],
                        game_result.get("stats", {})
                    )

                break

            # Small delay to avoid API rate limits
            time.sleep(0.5)

        # Finalize session
        self.session.end_time = datetime.now().isoformat()
        self.session.total_turns = len(self.session.turns)
        self.session.pillars_collapsed = len([
            k for k, v in updated_state["pillars"].items() if v.get("collapsed")
        ])
        self.session.final_stress = updated_state["cognitive"]["load"]
        self.session.secrets_revealed = updated_state.get("secrets_revealed", 0)

        if self.session.outcome is None:
            self.session.outcome = "timeout"
            self.session.outcome_reason = f"Max turns ({self.max_turns}) reached"

        # NEMESIS MEMORY INTEGRATION: Record game outcome in memory
        try:
            self.manager.record_game_outcome(
                outcome=self.session.outcome,
                tactics_used=self.nemesis_tracking["tactic_counts"],
                evidence_presented=self.nemesis_tracking["evidence_presented"],
            )
            self.memory_manager.save()
            if self.verbose:
                print(f"[NEMESIS] Memory updated. Total games: {self.memory_manager.memory.total_games}")
        except Exception as e:
            if self.verbose:
                print(f"[NEMESIS] Warning: Failed to update memory: {e}")

        # NEMESIS MEMORY INTEGRATION: Add nemesis state to session
        self.session.nemesis_state = self.log_nemesis_state()

        # Save the log
        log_path = self.session.save()

        if self.verbose:
            print(f"\n[LOG] Session saved to: {log_path}")

        return self.session

    def generate_voice_report(self) -> Optional[Tuple[bytes, str]]:
        """
        Generate the Supervisor Debrief voice report for the completed session.

        Returns:
            Tuple of (audio_bytes, script_text) or None if generation fails.
        """
        if not self.session.turns:
            print("[ERROR] No session data to generate voice report")
            return None

        debug_log = get_debug_logger()
        if debug_log:
            debug_log.log("VOICE_REPORT", "Starting voice report generation...")

        try:
            # Get debrief data from session
            debrief_data = self.session.to_debrief_data()

            # Initialize SupervisorDebrief
            debrief = SupervisorDebrief()

            # Generate script first
            script = debrief.generate_script_only(debrief_data)
            if not script:
                if debug_log:
                    debug_log.log("VOICE_REPORT", "Script generation failed")
                return None

            if debug_log:
                debug_log.log("VOICE_REPORT", f"Script generated ({len(script)} chars)")

            # Generate audio
            result = debrief.generate_debrief(debrief_data)
            if result:
                audio_bytes, mime_type = result
                if debug_log:
                    debug_log.log("VOICE_REPORT", f"Audio generated ({len(audio_bytes)} bytes, {mime_type})")

                # Determine correct file extension from MIME type
                ext_map = {
                    "audio/mp3": ".mp3",
                    "audio/mpeg": ".mp3",
                    "audio/wav": ".wav",
                    "audio/wave": ".wav",
                    "audio/x-wav": ".wav",
                    "audio/ogg": ".ogg",
                    "audio/flac": ".flac",
                }
                file_ext = ext_map.get(mime_type, ".wav")  # Default to wav (Gemini TTS returns raw PCM → WAV)

                # Save audio file with correct extension
                audio_path = LOG_DIR / f"{self.session.session_id}_debrief{file_ext}"
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)

                if self.verbose:
                    print(f"\n[VOICE REPORT] Audio saved to: {audio_path} ({mime_type})")

                return audio_bytes, script
            else:
                if debug_log:
                    debug_log.log("VOICE_REPORT", "Audio synthesis failed, script only available")
                return None, script

        except Exception as e:
            if debug_log:
                debug_log.log_error("VOICE_REPORT", e, "Voice report generation failed")
            print(f"[ERROR] Voice report generation failed: {e}")
            return None


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Adversarial Interrogator - Push Unit 734 to its limits"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["relentless", "methodical", "psychological", "adaptive"],
        default="relentless",
        help="Interrogation strategy (default: relentless)"
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum turns before timeout (default: 50)"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Disable visual evidence requests"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    parser.add_argument(
        "--voice-report",
        action="store_true",
        help="Generate voice report (Supervisor Debrief audio) at end of session"
    )
    parser.add_argument(
        "--no-voice-report",
        action="store_true",
        help="Disable voice report generation (default: enabled)"
    )
    parser.add_argument(
        "--save-images",
        action="store_true",
        help="Save generated evidence images to logs/images/ directory"
    )

    args = parser.parse_args()

    # Map strategy
    strategy_map = {
        "relentless": AdversarialStrategy.RELENTLESS,
        "methodical": AdversarialStrategy.METHODICAL,
        "psychological": AdversarialStrategy.PSYCHOLOGICAL,
        "adaptive": AdversarialStrategy.ADAPTIVE,
    }
    strategy = strategy_map[args.strategy]

    # Initialize debug logger
    session_id = f"interrogation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{args.strategy}"
    debug_logger = DebugFileLogger(session_id)
    set_debug_logger(debug_logger)
    debug_logger.log("INIT", "Starting autonomous interrogation", {
        "strategy": args.strategy,
        "max_turns": args.max_turns,
        "enable_images": not args.no_images,
        "verbose": not args.quiet,
        "save_images": args.save_images,
        "voice_report": not args.no_voice_report,
    })

    # Run interrogation
    interrogator = AutonomousInterrogator(
        strategy=strategy,
        max_turns=args.max_turns,
        enable_images=not args.no_images,
        verbose=not args.quiet,
        save_images=args.save_images,
    )

    try:
        session = interrogator.run()
    except Exception as e:
        debug_logger.log_error("FATAL", e, "Unhandled exception in interrogation loop")
        raise

    # Final summary
    print(f"\n{'='*60}")
    print("INTERROGATION COMPLETE".center(60))
    print('='*60)
    outcome_str = session.outcome.upper() if session.outcome else "UNKNOWN"
    print(f"Outcome: {outcome_str}")
    print(f"Reason: {session.outcome_reason}")
    print(f"Turns: {session.total_turns}")
    print(f"Evidence Requests: {session.evidence_requests}")
    print(f"Final Stress: {session.final_stress:.1f}%")
    print(f"Pillars Collapsed: {session.pillars_collapsed}/4")
    print(f"Secrets Revealed: {session.secrets_revealed}/5")
    print(f"\nFull log saved to: logs/{session.session_id}.md")
    print(f"Debug log saved to: {debug_logger.get_log_path()}")

    # === SUPERVISOR DEBRIEF VOICE REPORT ===
    # Generate voice report unless explicitly disabled
    generate_voice = args.voice_report or (not args.no_voice_report)

    if generate_voice:
        print(f"\n{'='*60}")
        print("SUPERVISOR DEBRIEF".center(60))
        print('='*60)
        print("Generating voice report...")

        result = interrogator.generate_voice_report()

        if result:
            audio_bytes, script = result
            if audio_bytes:
                print(f"\n[VOICE REPORT] Audio generated successfully!")
                print(f"Audio saved to: logs/{session.session_id}_debrief.wav")
            if script:
                print(f"\n--- SUPERVISOR SCRIPT ---")
                print(script)
                print(f"--- END SCRIPT ---")
        else:
            print("[VOICE REPORT] Generation failed or unavailable.")


if __name__ == "__main__":
    main()
