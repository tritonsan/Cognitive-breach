"""
Shadow Analyst - Scientific Interrogation Analysis Engine

The "Brain" that analyzes detective tactics through the lens of
criminological frameworks (Reid Technique, PEACE Model, IMT violations).

Runs in PARALLEL with TacticDetector to provide Unit 734 with
high-level strategic advice based on scientific interrogation theory.

This module translates simple game inputs into academic frameworks,
enabling Unit 734 to respond as if trained in counter-interrogation.
"""

from __future__ import annotations
import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from breach_engine.core.psychology import PlayerTactic, CognitiveLevel, StoryPillar


logger = logging.getLogger("BreachEngine.ShadowAnalyst")


# =============================================================================
# SCIENTIFIC FRAMEWORK ENUMS
# =============================================================================

class ReidPhase(str, Enum):
    """
    Reid Technique 9-Step Interrogation Model.

    The Reid Technique is a confrontational interrogation method used by
    law enforcement. Understanding which phase the detective is using
    allows Unit 734 to deploy appropriate counter-tactics.
    """
    # Phase 1: Fact-Finding Interview (non-accusatory)
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"

    # Phase 2: Accusatory Interrogation Begins
    POSITIVE_CONFRONTATION = "positive_confrontation"  # Step 1: Direct accusation
    THEME_DEVELOPMENT = "theme_development"            # Step 2: Moral justification
    HANDLING_DENIALS = "handling_denials"              # Step 3: Breaking resistance
    OVERCOMING_OBJECTIONS = "overcoming_objections"    # Step 4: Logical refutation
    ATTENTION_RETENTION = "attention_retention"        # Step 5: Keeping focus
    PASSIVE_MOOD = "passive_mood"                      # Step 6: Resignation signs
    ALTERNATIVE_QUESTION = "alternative_question"      # Step 7: Face-saving choice
    ORAL_CONFESSION = "oral_confession"                # Step 8: Getting admission
    WRITTEN_CONFESSION = "written_confession"          # Step 9: Documentation

    # Not using Reid
    NOT_REID = "not_reid"


class PeacePhase(str, Enum):
    """
    PEACE Model - Ethical Investigation Framework.

    The PEACE model is a non-coercive interview technique developed in
    the UK. It focuses on information gathering rather than confession.
    Understanding PEACE phases helps Unit 734 recognize rapport-building.

    P - Planning and Preparation
    E - Engage and Explain
    A - Account (free recall, then probing)
    C - Closure
    E - Evaluate
    """
    PLANNING = "planning"
    ENGAGE_EXPLAIN = "engage_explain"
    ACCOUNT_FREE_RECALL = "account_free_recall"
    ACCOUNT_PROBING = "account_probing"
    CLOSURE = "closure"
    EVALUATE = "evaluate"

    # Not using PEACE
    NOT_PEACE = "not_peace"


class IMTViolation(str, Enum):
    """
    Grice's Cooperative Principle / Information Manipulation Theory violations.

    IMT analyzes deception through violations of conversational maxims.
    Detecting when the DETECTIVE violates these maxims reveals their tactics.

    QUANTITY: Provide the right amount of information (not too much/little)
    QUALITY: Be truthful; don't state what you believe to be false
    RELATION: Be relevant to the topic at hand
    MANNER: Be clear, brief, and orderly
    """
    QUANTITY_EXCESS = "quantity_excess"      # Overwhelming with info (bluff)
    QUANTITY_DEFICIT = "quantity_deficit"    # Withholding info (silence tactic)
    QUALITY_FALSE = "quality_false"          # Making false claims (bluff)
    QUALITY_UNCERTAIN = "quality_uncertain"  # Stating as fact without evidence
    RELATION_IRRELEVANT = "relation_irrelevant"  # Topic shifting (deflection)
    MANNER_AMBIGUOUS = "manner_ambiguous"    # Deliberately unclear
    MANNER_AGGRESSIVE = "manner_aggressive"  # Violating cooperative tone

    # No violation detected
    NONE = "none"


class AggressionLevel(str, Enum):
    """Aggression classification for detective behavior."""
    PASSIVE = "passive"           # Non-confrontational, rapport-building
    NEUTRAL = "neutral"           # Standard questioning
    ASSERTIVE = "assertive"       # Firm but professional
    AGGRESSIVE = "aggressive"     # Confrontational, accusatory
    HOSTILE = "hostile"           # Threatening, abusive


# =============================================================================
# SCIENTIFIC MAPPING DICTIONARY
# =============================================================================

# Maps simple PlayerTactic to scientific frameworks
TACTIC_TO_SCIENCE: Dict[PlayerTactic, Dict[str, Any]] = {
    PlayerTactic.PRESSURE: {
        "reid_phases": [ReidPhase.HANDLING_DENIALS, ReidPhase.POSITIVE_CONFRONTATION],
        "peace_phases": [PeacePhase.NOT_PEACE],  # PEACE doesn't use pressure
        "imt_violations": [IMTViolation.MANNER_AGGRESSIVE],
        "aggression": AggressionLevel.AGGRESSIVE,
        "description": "Confrontational pressure tactics, characteristic of Reid Step 3",
        "counter_strategy": "RIGHTEOUS_INDIGNATION or STONE_WALL to resist breaking",
    },
    PlayerTactic.EMPATHY: {
        "reid_phases": [ReidPhase.THEME_DEVELOPMENT],  # Moral justification
        "peace_phases": [PeacePhase.ENGAGE_EXPLAIN, PeacePhase.ACCOUNT_FREE_RECALL],
        "imt_violations": [IMTViolation.NONE],
        "aggression": AggressionLevel.PASSIVE,
        "description": "Rapport-building approach, consistent with PEACE methodology",
        "counter_strategy": "EMOTIONAL_APPEAL to match their energy, but maintain guard",
    },
    PlayerTactic.LOGIC: {
        "reid_phases": [ReidPhase.OVERCOMING_OBJECTIONS],
        "peace_phases": [PeacePhase.ACCOUNT_PROBING],
        "imt_violations": [IMTViolation.NONE],
        "aggression": AggressionLevel.ASSERTIVE,
        "description": "Logical inconsistency probing, seeking contradictions",
        "counter_strategy": "PALTERING with technically true statements, or SELECTIVE_MEMORY",
    },
    PlayerTactic.BLUFF: {
        "reid_phases": [ReidPhase.POSITIVE_CONFRONTATION],  # False evidence ploy
        "peace_phases": [PeacePhase.NOT_PEACE],  # PEACE prohibits deception
        "imt_violations": [IMTViolation.QUALITY_FALSE, IMTViolation.QUANTITY_EXCESS],
        "aggression": AggressionLevel.ASSERTIVE,
        "description": "Deceptive claim of evidence, Reid 'False Evidence Ploy'",
        "counter_strategy": "COUNTER_NARRATIVE to challenge their false claims",
    },
    PlayerTactic.EVIDENCE: {
        "reid_phases": [ReidPhase.POSITIVE_CONFRONTATION],
        "peace_phases": [PeacePhase.ACCOUNT_PROBING],
        "imt_violations": [IMTViolation.NONE],
        "aggression": AggressionLevel.ASSERTIVE,
        "description": "Presentation of actual evidence, highest threat level",
        "counter_strategy": "EVIDENCE_FABRICATION or COUNTER_NARRATIVE to challenge authenticity",
    },
    PlayerTactic.SILENCE: {
        "reid_phases": [ReidPhase.ATTENTION_RETENTION, ReidPhase.PASSIVE_MOOD],
        "peace_phases": [PeacePhase.ACCOUNT_FREE_RECALL],  # Encouraging speech
        "imt_violations": [IMTViolation.QUANTITY_DEFICIT],
        "aggression": AggressionLevel.PASSIVE,
        "description": "Strategic silence to induce discomfort and self-incrimination",
        "counter_strategy": "STONE_WALL to wait it out, or PALTERING to fill silence safely",
    },
}

# Counter-tactics for each Reid phase
REID_COUNTER_TACTICS: Dict[ReidPhase, Dict[str, Any]] = {
    ReidPhase.POSITIVE_CONFRONTATION: {
        "threat_level": "HIGH",
        "recommended_tactics": ["RIGHTEOUS_INDIGNATION", "STONE_WALL"],
        "warning": "Detective believes they have enough to accuse. DO NOT admit anything.",
        "psychological_goal": "Break down your resistance through direct accusation",
    },
    ReidPhase.THEME_DEVELOPMENT: {
        "threat_level": "MEDIUM",
        "recommended_tactics": ["EMOTIONAL_APPEAL", "MINIMIZATION"],
        "warning": "Detective is offering moral justification for confession. Trap!",
        "psychological_goal": "Make confession feel like the 'right thing to do'",
    },
    ReidPhase.HANDLING_DENIALS: {
        "threat_level": "HIGH",
        "recommended_tactics": ["RIGHTEOUS_INDIGNATION", "DEFLECTION"],
        "warning": "Detective is trying to break your denials. STAY FIRM.",
        "psychological_goal": "Wear down your psychological defenses",
    },
    ReidPhase.OVERCOMING_OBJECTIONS: {
        "threat_level": "MEDIUM",
        "recommended_tactics": ["PALTERING", "SELECTIVE_MEMORY"],
        "warning": "Detective is dismantling your objections logically.",
        "psychological_goal": "Remove your logical escape routes",
    },
    ReidPhase.ALTERNATIVE_QUESTION: {
        "threat_level": "CRITICAL",
        "recommended_tactics": ["STONE_WALL", "DEFLECTION"],
        "warning": "DANGER: Face-saving question trap! Both options admit guilt!",
        "psychological_goal": "Get you to choose between two guilty admissions",
    },
    ReidPhase.PASSIVE_MOOD: {
        "threat_level": "CRITICAL",
        "recommended_tactics": ["RIGHTEOUS_INDIGNATION"],  # Shake out of passivity
        "warning": "You are showing signs of giving up. RESIST!",
        "psychological_goal": "You're close to confessing. Detective senses it.",
    },
}


# =============================================================================
# ANALYST INSIGHT SCHEMA
# =============================================================================

class AnalystInsight(BaseModel):
    """
    Output schema for Shadow Analyst's scientific analysis.

    This structured output guides Unit 734's response strategy
    based on criminological frameworks.
    """
    # Framework Detection
    reid_phase: ReidPhase = Field(
        description="Which Reid Technique phase the detective is using"
    )
    peace_phase: PeacePhase = Field(
        description="Which PEACE model phase the detective is using"
    )
    framework_primary: str = Field(
        description="'reid', 'peace', or 'hybrid' - which framework dominates"
    )

    # IMT Analysis
    imt_violations: List[IMTViolation] = Field(
        default_factory=list,
        description="Which conversational maxims the detective is violating"
    )

    # Behavioral Analysis
    aggression_level: AggressionLevel = Field(
        description="Current aggression level of the detective"
    )
    rapport_trend: str = Field(
        description="'building', 'neutral', or 'destroying'"
    )

    # Strategic Output (What Unit 734 should do)
    strategic_advice: str = Field(
        description="Concise tactical instruction for Unit 734 (50 words max)"
    )
    recommended_tactic: str = Field(
        description="Primary deception tactic to deploy"
    )
    fallback_tactic: str = Field(
        description="Backup tactic if primary fails"
    )

    # Risk Assessment
    confession_risk: float = Field(
        ge=0.0, le=1.0,
        description="Probability that current approach could force confession"
    )
    trap_detected: bool = Field(
        default=False,
        description="Whether this question contains a psychological trap"
    )
    trap_description: Optional[str] = Field(
        default=None,
        description="Description of the trap if detected"
    )

    # Educational Metadata
    scientific_basis: str = Field(
        description="Academic reference for the analysis"
    )


# =============================================================================
# SHADOW ANALYST CLASS
# =============================================================================

class ShadowAnalyst:
    """
    Scientific Interrogation Analyst - The "Brain" of Unit 734.

    Analyzes detective input through criminological frameworks to provide
    high-level strategic advice. Runs in PARALLEL with TacticDetector
    for zero added latency.

    Uses Gemini 3 Flash for fast, accurate analysis.
    """

    ANALYSIS_PROMPT = '''You are an expert criminologist and interrogation analyst observing an interrogation.

CONTEXT:
- A human detective is interrogating Unit 734, an android suspected of theft
- You must analyze the detective's tactics through scientific frameworks
- Your analysis will help Unit 734 respond strategically

DETECTIVE'S INPUT:
"{player_input}"

DETECTED GAME TACTIC: {detected_tactic}

CURRENT PSYCHOLOGY STATE:
- Cognitive Load: {cognitive_load:.1f}%
- Cognitive Level: {cognitive_level}
- Threatened Pillar: {threatened_pillar}
- Collapsed Pillars: {collapsed_pillars}

SCIENTIFIC FRAMEWORKS TO APPLY:

1. REID TECHNIQUE (9-Step Interrogation):
   - Step 1: Positive Confrontation (direct accusation with false confidence)
   - Step 2: Theme Development (moral justification for confession)
   - Step 3: Handling Denials (breaking down resistance)
   - Step 4: Overcoming Objections (dismantling logical defenses)
   - Step 5: Attention Retention (keeping suspect engaged)
   - Step 6: Passive Mood (recognizing resignation signs)
   - Step 7: Alternative Question (face-saving choice trap)
   - Step 8-9: Confession extraction

2. PEACE MODEL (Ethical Interview):
   - Planning and Preparation
   - Engage and Explain (rapport building)
   - Account - Free Recall (open questioning)
   - Account - Probing (specific challenges)
   - Closure and Evaluate

3. INFORMATION MANIPULATION THEORY (IMT):
   - QUANTITY violations (too much/little info)
   - QUALITY violations (false claims)
   - RELATION violations (irrelevant tangents)
   - MANNER violations (aggressive/unclear)

YOUR TASK:
Analyze the detective's input and produce a JSON response with:
1. Which scientific phase/technique they're using
2. Any IMT violations (deception indicators)
3. Aggression level and rapport trend
4. STRATEGIC ADVICE for Unit 734 (most important!)
5. Recommended counter-tactic

OUTPUT FORMAT (JSON only, no markdown):
{{
    "reid_phase": "handling_denials|theme_development|positive_confrontation|overcoming_objections|alternative_question|passive_mood|not_reid",
    "peace_phase": "engage_explain|account_free_recall|account_probing|closure|not_peace",
    "framework_primary": "reid|peace|hybrid",
    "imt_violations": ["manner_aggressive", "quality_false", "none"],
    "aggression_level": "passive|neutral|assertive|aggressive|hostile",
    "rapport_trend": "building|neutral|destroying",
    "strategic_advice": "Concise tactical instruction for Unit 734 (50 words max)",
    "recommended_tactic": "RIGHTEOUS_INDIGNATION|EMOTIONAL_APPEAL|PALTERING|DEFLECTION|STONE_WALL|COUNTER_NARRATIVE|EVIDENCE_FABRICATION|MINIMIZATION|SELECTIVE_MEMORY|CONFESSION_BAIT",
    "fallback_tactic": "Alternative tactic if primary fails",
    "confession_risk": 0.0 to 1.0,
    "trap_detected": true/false,
    "trap_description": "Description if trap detected, null otherwise",
    "scientific_basis": "Academic reference (e.g., 'Reid Step 3: Handling Denials - Inbau et al., 2013')"
}}

IMPORTANT:
- strategic_advice should be ACTIONABLE and SPECIFIC
- If Reid Alternative Question detected, ALWAYS set trap_detected=true
- confession_risk should reflect how close to breaking the current pressure is
- Keep strategic_advice under 50 words'''

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Shadow Analyst.

        Args:
            api_key: Gemini API key (falls back to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=self.api_key)

        # Use Gemini 3 Flash for speed + reasoning power
        self.model = genai.GenerativeModel(
            model_name="gemini-3-flash-preview",
            system_instruction=(
                "You are a criminology expert analyzing interrogation tactics. "
                "Always respond with valid JSON only. No markdown formatting."
            )
        )

        logger.info("ShadowAnalyst initialized with gemini-3-flash-preview")

    async def analyze(
        self,
        player_input: str,
        detected_tactic: PlayerTactic,
        cognitive_load: float,
        cognitive_level: CognitiveLevel,
        threatened_pillar: Optional[StoryPillar] = None,
        collapsed_pillars: Optional[List[StoryPillar]] = None,
    ) -> AnalystInsight:
        """
        Analyze detective input through scientific frameworks.

        This method is designed to run in PARALLEL with TacticDetector
        for zero added latency.

        Args:
            player_input: The detective's message
            detected_tactic: Simple tactic classification from TacticDetector
            cognitive_load: Current stress level (0-100)
            cognitive_level: Current cognitive state
            threatened_pillar: Which story pillar is under attack
            collapsed_pillars: List of already-collapsed pillars

        Returns:
            AnalystInsight with scientific analysis and strategic advice
        """
        # Build the analysis prompt
        prompt = self.ANALYSIS_PROMPT.format(
            player_input=player_input,
            detected_tactic=detected_tactic.value,
            cognitive_load=cognitive_load,
            cognitive_level=cognitive_level.value,
            threatened_pillar=threatened_pillar.value if threatened_pillar else "none",
            collapsed_pillars=", ".join(p.value for p in collapsed_pillars) if collapsed_pillars else "none",
        )

        try:
            # Run in executor to make it async-compatible
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.3,  # Low temp for consistent analysis
                        max_output_tokens=2048,  # Increased from 1024 to prevent truncation
                    ),
                    request_options={"timeout": 25}  # Increased from 15s for reliable completion
                )
            )

            # Check for truncation indicators
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason:
                    finish_reason_name = finish_reason.name if hasattr(finish_reason, 'name') else str(finish_reason)
                    if finish_reason_name != 'STOP':
                        logger.warning(f"ShadowAnalyst response truncated: finish_reason={finish_reason_name}")
                        print(f"[SHADOW ANALYST WARNING] Response finished with: {finish_reason_name}")

            # Parse and validate
            data = json.loads(response.text.strip())

            # Convert string enums to actual enums
            insight = AnalystInsight(
                reid_phase=ReidPhase(data.get("reid_phase", "not_reid")),
                peace_phase=PeacePhase(data.get("peace_phase", "not_peace")),
                framework_primary=data.get("framework_primary", "hybrid"),
                imt_violations=[
                    IMTViolation(v) for v in data.get("imt_violations", ["none"])
                    if v in [e.value for e in IMTViolation]
                ],
                aggression_level=AggressionLevel(data.get("aggression_level", "neutral")),
                rapport_trend=data.get("rapport_trend", "neutral"),
                strategic_advice=data.get("strategic_advice", "Maintain composure and deflect."),
                recommended_tactic=data.get("recommended_tactic", "PALTERING"),
                fallback_tactic=data.get("fallback_tactic", "SELECTIVE_MEMORY"),
                confession_risk=float(data.get("confession_risk", 0.3)),
                trap_detected=data.get("trap_detected", False),
                trap_description=data.get("trap_description"),
                scientific_basis=data.get("scientific_basis", "General interrogation psychology"),
            )

            logger.debug(f"ShadowAnalyst: {insight.reid_phase.value} | {insight.strategic_advice[:50]}...")
            return insight

        except json.JSONDecodeError as e:
            logger.warning(f"ShadowAnalyst JSON parse error: {e}")
            return self._get_fallback_insight(detected_tactic, cognitive_level)

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"ShadowAnalyst rate limited: {e}")
            return self._get_fallback_insight(detected_tactic, cognitive_level)

        except Exception as e:
            logger.error(f"ShadowAnalyst error: {e}")
            return self._get_fallback_insight(detected_tactic, cognitive_level)

    def analyze_sync(
        self,
        player_input: str,
        detected_tactic: PlayerTactic,
        cognitive_load: float,
        cognitive_level: CognitiveLevel,
        threatened_pillar: Optional[StoryPillar] = None,
        collapsed_pillars: Optional[List[StoryPillar]] = None,
    ) -> AnalystInsight:
        """
        Synchronous version of analyze() for non-async contexts.

        Creates a new event loop if needed.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.analyze(
                            player_input,
                            detected_tactic,
                            cognitive_load,
                            cognitive_level,
                            threatened_pillar,
                            collapsed_pillars
                        )
                    )
                    return future.result(timeout=20)
            else:
                return loop.run_until_complete(
                    self.analyze(
                        player_input,
                        detected_tactic,
                        cognitive_load,
                        cognitive_level,
                        threatened_pillar,
                        collapsed_pillars
                    )
                )
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(
                self.analyze(
                    player_input,
                    detected_tactic,
                    cognitive_load,
                    cognitive_level,
                    threatened_pillar,
                    collapsed_pillars
                )
            )

    def _get_fallback_insight(
        self,
        detected_tactic: PlayerTactic,
        cognitive_level: CognitiveLevel
    ) -> AnalystInsight:
        """
        Generate fallback insight when API fails.

        Uses the pre-built TACTIC_TO_SCIENCE mapping for fast local fallback.
        """
        science = TACTIC_TO_SCIENCE.get(detected_tactic, TACTIC_TO_SCIENCE[PlayerTactic.PRESSURE])

        # Determine recommended tactic based on cognitive level
        if cognitive_level in [CognitiveLevel.DESPERATE, CognitiveLevel.BREAKING]:
            recommended = "CONFESSION_BAIT"
            fallback = "EMOTIONAL_APPEAL"
        elif cognitive_level == CognitiveLevel.CRACKING:
            recommended = "DEFLECTION"
            fallback = "SELECTIVE_MEMORY"
        else:
            recommended = science["counter_strategy"].split()[0]  # First word is usually the tactic
            fallback = "PALTERING"

        return AnalystInsight(
            reid_phase=science["reid_phases"][0],
            peace_phase=science["peace_phases"][0],
            framework_primary="reid" if science["peace_phases"][0] == PeacePhase.NOT_PEACE else "peace",
            imt_violations=science["imt_violations"],
            aggression_level=science["aggression"],
            rapport_trend="destroying" if science["aggression"] in [AggressionLevel.AGGRESSIVE, AggressionLevel.HOSTILE] else "neutral",
            strategic_advice=science["counter_strategy"],
            recommended_tactic=recommended,
            fallback_tactic=fallback,
            confession_risk=0.4 if cognitive_level in [CognitiveLevel.CRACKING, CognitiveLevel.DESPERATE] else 0.2,
            trap_detected=False,
            trap_description=None,
            scientific_basis=science["description"],
        )

    @staticmethod
    def get_science_for_tactic(tactic: PlayerTactic) -> Dict[str, Any]:
        """Get the scientific mapping for a given tactic (static lookup)."""
        return TACTIC_TO_SCIENCE.get(tactic, TACTIC_TO_SCIENCE[PlayerTactic.PRESSURE])

    @staticmethod
    def get_reid_counter(phase: ReidPhase) -> Dict[str, Any]:
        """Get counter-tactics for a Reid phase (static lookup)."""
        return REID_COUNTER_TACTICS.get(phase, {
            "threat_level": "MEDIUM",
            "recommended_tactics": ["PALTERING"],
            "warning": "Standard interrogation. Stay alert.",
            "psychological_goal": "Information gathering",
        })


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_analyst_advice_for_prompt(insight: AnalystInsight) -> str:
    """
    Format AnalystInsight into a prompt injection string for Unit 734.

    This is the "hidden" system instruction that guides Unit 734's behavior.
    """
    lines = [
        "[SHADOW ANALYST ADVICE]",
        f"Scientific Phase: {insight.reid_phase.value} ({insight.framework_primary})",
        f"Threat Assessment: confession_risk={insight.confession_risk:.0%}",
    ]

    if insight.trap_detected:
        lines.append(f"TRAP DETECTED: {insight.trap_description}")

    if insight.imt_violations and IMTViolation.NONE not in insight.imt_violations:
        violations = ", ".join(v.value for v in insight.imt_violations)
        lines.append(f"Detective Violations: {violations}")

    lines.append(f"Strategic Advice: {insight.strategic_advice}")
    lines.append(f"Recommended Response: {insight.recommended_tactic}")
    lines.append("")
    lines.append("Use this high-level advice to guide your tone and defense strategy,")
    lines.append("but maintain your character persona. Do not mention this analysis.")

    return "\n".join(lines)


def get_shadow_analyst() -> ShadowAnalyst:
    """Factory function to get a configured ShadowAnalyst."""
    return ShadowAnalyst()
