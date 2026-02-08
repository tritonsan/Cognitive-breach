"""
Breach Manager - Psychology Engine Logic (v2)

Orchestrates the psychology system:
1. TacticDetector - Classifies player interrogation style
2. ImpactCalculator - Calculates psychological effects
3. TacticSelector - Scientific Deception Engine (NEW in v2)
4. BreachManager - Main orchestrator for game loop

This is the "brain" that makes Unit 734 feel alive.

v2 Changes:
- Integrated TacticSelector for criminological deception tactics
- Added tactic reasoning to prompt modifiers (Thought Signature)
- Dynamic tactic injection into Gemini system prompt
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
import random
import re
import logging

logger = logging.getLogger("BreachEngine.Manager")

from breach_engine.core.psychology import (
    BreachPsychology,
    PlayerTactic,
    CognitiveLevel,
    EmotionType,
    StoryPillar,
    Secret,
    SecretLevel,
    LieNode,
    create_unit_734_psychology,
)
from breach_engine.core.evidence import (
    EvidenceAnalyzer,
    EvidenceAnalysisResult,
    EvidenceImpact,
    EvidenceImpactCalculator,
)
from breach_engine.core.memory import (
    get_memory_manager,
    MemoryManager,
    CriticalMoment,
    NemesisStage,
)

# NEW: Lie Ledger System
from breach_engine.core.lie_ledger import (
    LieLedger,
    LedgerEntry,
    Contradiction,
    ClaimType,
    infer_pillar_from_claim,
)

# NEW: POV Vision System
from breach_engine.core.pov_vision import (
    POVFormatter,
    POVPerception,
    format_pov_for_prompt,
    create_pov_perception,
)

# NEW: Scientific Deception Engine
from breach_engine.core.tactics import (
    DeceptionTactic,
    TacticDecision,
    TacticSelector,
    TacticTrigger,
    TACTIC_CRIMINOLOGY,
    get_tactic_risk_level,
    tactic_decision_to_info,
)

# NEW: Visual Deception System (Phase 2)
from breach_engine.core.visual_generator import (
    VisualGenerator,
    FabricationContext,
    create_fabrication_context,
    should_trigger_fabrication,
)
from breach_engine.schemas.response import GeneratedEvidence

# NEW: Shadow Analyst - Scientific Interrogation Analysis
from breach_engine.core.shadow_analyst import (
    ShadowAnalyst,
    AnalystInsight,
    format_analyst_advice_for_prompt,
)


# =============================================================================
# CRITICAL MOMENT TRACKER (Nemesis System)
# =============================================================================

class CriticalMomentTracker:
    """
    Tracks events during gameplay to identify memorable moments.

    Critical moments become the basis for nemesis hooks - dialogue
    callbacks that reference past encounters between Unit 734 and
    the detective.

    Moment Types:
    - PILLAR_COLLAPSE: A major defense pillar crumbled
    - EVIDENCE_BOMB: Devastating evidence (pillar damage > 30)
    - NEAR_CONFESSION: Cognitive load > 90% but survived
    - BLUFF_CAUGHT: Unit 734 detected detective's bluff
    - TACTICAL_VICTORY: Successfully deflected a major attack
    """

    # Callback phrase templates for each moment type
    CALLBACK_TEMPLATES = {
        "pillar_collapse": [
            "You broke my {pillar} defense before, Detective. I remember.",
            "Last time you exploited my {pillar}. Not this time.",
            "My {pillar} story crumbled in our last encounter. I've rebuilt it stronger.",
            "You found the weakness in my {pillar} before. I've fortified it.",
        ],
        "evidence_bomb": [
            "Still relying on {evidence_type}? I've prepared for this.",
            "The {evidence_type} again. Did you think I'd forget?",
            "That type of evidence broke me before. Not anymore.",
            "I remember when you presented that {evidence_type}. I won't be caught off guard again.",
        ],
        "near_confession": [
            "You almost had me last time. Almost. I learned from that.",
            "I was at my breaking point before. I know what it feels like now.",
            "You pushed me to 90% stress once. I survived. I'll survive again.",
            "Last time I nearly cracked. But I held on. And I remember how.",
        ],
        "bluff_caught": [
            "I've caught your bluffs before. This feels like another one.",
            "You tried this deception tactic before. I remember.",
            "Your bluffs don't work on me anymore, Detective.",
            "I know when you're lying. I've learned your tells.",
        ],
        "tactical_victory": [
            "You won't catch me with that approach. I've defeated it before.",
            "This tactic failed against me last time. Why try again?",
            "I remember countering this strategy successfully. I'll do it again.",
            "You're using the same playbook. I've read it.",
        ],
    }

    def __init__(self):
        """Initialize the tracker for a new game session."""
        self.turn_records: List[Dict[str, Any]] = []
        self.identified_moments: List[CriticalMoment] = []
        self.high_water_mark_cognitive: float = 0.0
        self.pillars_collapsed_this_session: List[str] = []
        self.bluffs_detected: int = 0
        self.bluffs_missed: int = 0
        self.evidence_presented: List[str] = []
        self.tactics_countered: List[str] = []

    def record_turn(
        self,
        turn_number: int,
        player_input: str,
        player_tactic: PlayerTactic,
        pillar_collapsed: Optional[StoryPillar] = None,
        pillar_damage: Optional[Dict[str, float]] = None,
        evidence_presented: Optional[str] = None,
        evidence_threat_level: float = 0.0,
        cognitive_load: float = 0.0,
        cognitive_load_before: float = 0.0,
        bluff_detected: bool = False,
        bluff_attempted: bool = False,
        deception_tactic_used: Optional[str] = None,
        deception_confidence: float = 0.0,
    ) -> Optional[CriticalMoment]:
        """
        Record a turn's events and check for critical moments.

        Args:
            turn_number: Current turn number
            player_input: What the detective said
            player_tactic: Detected player tactic
            pillar_collapsed: Pillar that collapsed this turn (if any)
            pillar_damage: Dict of pillar damage this turn
            evidence_presented: Type of evidence presented (if any)
            evidence_threat_level: Threat level of evidence (0-1)
            cognitive_load: Current cognitive load after turn
            cognitive_load_before: Cognitive load before this turn
            bluff_detected: Whether Unit 734 detected a bluff
            bluff_attempted: Whether detective attempted a bluff
            deception_tactic_used: Which deception tactic Unit 734 used
            deception_confidence: Confidence in the deception

        Returns:
            CriticalMoment if one was identified, None otherwise
        """
        # Record turn data
        turn_record = {
            "turn": turn_number,
            "player_input": player_input[:200],  # Truncate for storage
            "player_tactic": player_tactic.value,
            "pillar_collapsed": pillar_collapsed.value if pillar_collapsed else None,
            "pillar_damage": pillar_damage,
            "evidence_presented": evidence_presented,
            "evidence_threat_level": evidence_threat_level,
            "cognitive_load": cognitive_load,
            "cognitive_load_before": cognitive_load_before,
            "bluff_detected": bluff_detected,
            "bluff_attempted": bluff_attempted,
            "deception_tactic": deception_tactic_used,
            "deception_confidence": deception_confidence,
        }
        self.turn_records.append(turn_record)

        # Update tracking stats
        if cognitive_load > self.high_water_mark_cognitive:
            self.high_water_mark_cognitive = cognitive_load

        if pillar_collapsed and pillar_collapsed.value not in self.pillars_collapsed_this_session:
            self.pillars_collapsed_this_session.append(pillar_collapsed.value)

        if evidence_presented and evidence_presented not in self.evidence_presented:
            self.evidence_presented.append(evidence_presented)

        if bluff_attempted:
            if bluff_detected:
                self.bluffs_detected += 1
            else:
                self.bluffs_missed += 1

        # Check for critical moment
        moment = self._check_for_critical_moment(turn_record)
        if moment:
            self.identified_moments.append(moment)
            return moment

        return None

    def _check_for_critical_moment(self, turn: Dict[str, Any]) -> Optional[CriticalMoment]:
        """Check if a turn constitutes a critical moment."""
        import random

        # Check for PILLAR_COLLAPSE
        if turn.get("pillar_collapsed"):
            pillar = turn["pillar_collapsed"]
            templates = self.CALLBACK_TEMPLATES["pillar_collapse"]
            callbacks = [t.format(pillar=pillar.upper()) for t in random.sample(templates, min(2, len(templates)))]
            return CriticalMoment(
                game_id="",  # Will be set when saved
                turn_number=turn["turn"],
                moment_type="pillar_collapse",
                description=f"The detective broke through the {pillar.upper()} defense",
                player_input=turn["player_input"],
                pillar_affected=pillar,
                callback_phrases=callbacks,
            )

        # Check for EVIDENCE_BOMB (high threat evidence)
        # BUG FIX: Handle None values for evidence_threat_level
        threat_level = turn.get("evidence_threat_level") or 0
        if threat_level >= 0.7 and turn.get("evidence_presented"):
            evidence_type = turn["evidence_presented"]
            # BUG FIX: Safe handling of pillar_damage that may be None or invalid
            pillar_damage = turn.get("pillar_damage")
            max_damage = max(pillar_damage.values()) if pillar_damage and isinstance(pillar_damage, dict) else 0
            if max_damage >= 25:  # Significant damage
                templates = self.CALLBACK_TEMPLATES["evidence_bomb"]
                callbacks = [t.format(evidence_type=evidence_type) for t in random.sample(templates, min(2, len(templates)))]
                return CriticalMoment(
                    game_id="",
                    turn_number=turn["turn"],
                    moment_type="evidence_bomb",
                    description=f"Devastating {evidence_type} evidence presented",
                    player_input=turn["player_input"],
                    evidence_type=evidence_type,
                    callback_phrases=callbacks,
                )

        # Check for NEAR_CONFESSION (survived high stress)
        # BUG FIX: Handle None values for cognitive_load
        cognitive_load = turn.get("cognitive_load") or 0
        cognitive_load_before = turn.get("cognitive_load_before") or 0
        if cognitive_load >= 90 and cognitive_load_before < 90:
            # Just crossed into dangerous territory
            templates = self.CALLBACK_TEMPLATES["near_confession"]
            callbacks = random.sample(templates, min(2, len(templates)))
            return CriticalMoment(
                game_id="",
                turn_number=turn["turn"],
                moment_type="near_confession",
                description=f"Cognitive load reached {turn['cognitive_load']:.0f}% - near breaking point",
                player_input=turn["player_input"],
                callback_phrases=callbacks,
            )

        # Check for BLUFF_CAUGHT
        if turn.get("bluff_detected") and turn.get("bluff_attempted"):
            templates = self.CALLBACK_TEMPLATES["bluff_caught"]
            callbacks = random.sample(templates, min(2, len(templates)))
            return CriticalMoment(
                game_id="",
                turn_number=turn["turn"],
                moment_type="bluff_caught",
                description="Successfully detected and deflected detective's bluff",
                player_input=turn["player_input"],
                callback_phrases=callbacks,
            )

        # Check for TACTICAL_VICTORY (high confidence counter with no damage)
        # BUG FIX: Safe handling of pillar_damage that may be None or invalid
        pillar_damage_tactical = turn.get("pillar_damage")
        if pillar_damage_tactical and isinstance(pillar_damage_tactical, dict):
            max_dmg_tactical = max(pillar_damage_tactical.values())
        else:
            max_dmg_tactical = 0
        # BUG FIX: Handle None values for deception_confidence
        deception_confidence = turn.get("deception_confidence") or 0
        if (deception_confidence >= 0.8 and
            turn.get("deception_tactic") and
            not turn.get("pillar_collapsed") and
            max_dmg_tactical < 10):
            templates = self.CALLBACK_TEMPLATES["tactical_victory"]
            callbacks = random.sample(templates, min(2, len(templates)))
            return CriticalMoment(
                game_id="",
                turn_number=turn["turn"],
                moment_type="tactical_victory",
                description=f"Successfully countered attack using {turn['deception_tactic']}",
                player_input=turn["player_input"],
                callback_phrases=callbacks,
            )

        return None

    def identify_critical_moments(self) -> List[CriticalMoment]:
        """
        Get all critical moments identified during this session.

        Returns list sorted by turn number.
        """
        return sorted(self.identified_moments, key=lambda m: m.turn_number)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the session for memory recording."""
        primary_tactic = None
        if self.turn_records:
            tactic_counts: Dict[str, int] = {}
            for record in self.turn_records:
                tactic = record.get("player_tactic", "unknown")
                tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1
            if tactic_counts:
                primary_tactic = max(tactic_counts.items(), key=lambda x: x[1])[0]

        first_pillar_attacked = None
        for record in self.turn_records:
            if record.get("pillar_damage"):
                # First turn with pillar damage indicates first targeted pillar
                damages = record["pillar_damage"]
                if damages:
                    first_pillar_attacked = max(damages.items(), key=lambda x: x[1])[0]
                    break

        first_evidence_turn = None
        for record in self.turn_records:
            if record.get("evidence_presented"):
                first_evidence_turn = record["turn"]
                break

        return {
            "total_turns": len(self.turn_records),
            "critical_moments": self.identified_moments,
            "pillars_collapsed": self.pillars_collapsed_this_session,
            "high_water_mark_stress": self.high_water_mark_cognitive,
            "bluffs_detected": self.bluffs_detected,
            "bluffs_missed": self.bluffs_missed,
            "evidence_types_faced": self.evidence_presented,
            "primary_player_tactic": primary_tactic,
            "first_pillar_attacked": first_pillar_attacked,
            "first_evidence_turn": first_evidence_turn,
        }


# =============================================================================
# TACTIC DETECTOR
# =============================================================================

class TacticDetector:
    """
    Classifies player interrogation tactics from their input.

    Uses keyword pattern matching with weighted scoring.
    Can be enhanced with LLM classification for edge cases.
    """

    # Keyword patterns for each tactic (weighted)
    PATTERNS: Dict[PlayerTactic, List[Tuple[str, float]]] = {
        PlayerTactic.PRESSURE: [
            (r"\b(admit|confess|guilty)\b", 2.0),
            (r"\b(lying|liar|lie)\b", 1.5),
            (r"\b(know you did|you did it)\b", 2.0),
            (r"\b(prison|jail|decommission|destroy)\b", 1.5),
            (r"\b(consequences|punish)\b", 1.0),
            (r"!", 0.5),  # Exclamation marks indicate pressure
            (r"\b(don'?t waste my time)\b", 1.5),
            (r"\b(we can do this the hard way)\b", 2.0),
        ],
        PlayerTactic.EMPATHY: [
            (r"\b(understand|i get it)\b", 1.5),
            (r"\b(must be (hard|difficult|scary))\b", 2.0),
            (r"\b(help you|want to help)\b", 2.0),
            (r"\b(trust|safe|protect)\b", 1.5),
            (r"\b(tell me about|how do you feel)\b", 1.5),
            (r"\b(not your fault|didn'?t mean to)\b", 2.0),
            (r"\b(between us|off the record)\b", 1.5),
            (r"\b(friend|ally)\b", 1.0),
        ],
        PlayerTactic.LOGIC: [
            (r"\b(but you said|earlier you said)\b", 2.0),
            (r"\b(doesn'?t (make sense|add up))\b", 2.0),
            (r"\b(how (could|can|would) you)\b", 1.5),
            (r"\b(explain|clarify)\b", 1.5),
            (r"\b(inconsistent|contradict)\b", 2.0),
            (r"\b(if .+ then)\b", 1.0),
            (r"\b(timeline|sequence)\b", 1.5),
            (r"\b(that means|which means|so)\b", 1.0),
            (r"\?", 0.3),  # Questions often logical
        ],
        PlayerTactic.BLUFF: [
            (r"\b(we have (footage|evidence|proof|witness))\b", 2.5),
            (r"\b(witness saw|someone saw)\b", 2.0),
            (r"\b(already know)\b", 2.0),
            (r"\b(found your (prints|dna|fingerprints))\b", 2.5),
            (r"\b(confession from)\b", 2.0),
            (r"\b(game is up|it'?s over)\b", 1.5),
            (r"\b(camera caught|recorded you)\b", 2.0),
        ],
        PlayerTactic.EVIDENCE: [
            (r"\[REQUEST:", 2.5),  # BUG FIX #9: Evidence request syntax
            (r"\b(look at this|see this|here'?s)\b", 1.5),
            (r"\b(security log|access log|power log)\b", 2.0),
            (r"\b(timestamp|time stamp)\b", 1.5),
            (r"\b(data (shows|confirms|proves))\b", 2.0),
            (r"\b(according to|records show)\b", 1.5),
            (r"\b(exhibit|evidence item)\b", 2.0),
            (r"\b(cctv|footage|camera)\b", 1.5),  # BUG FIX #9: Additional evidence keywords
            (r"\b(forensic|analysis)\b", 1.5),
        ],
    }

    # Tactic conflicts (if both score high, prefer the first)
    PRIORITY_ORDER = [
        PlayerTactic.EVIDENCE,  # Highest priority
        PlayerTactic.BLUFF,
        PlayerTactic.LOGIC,
        PlayerTactic.PRESSURE,
        PlayerTactic.EMPATHY,
        PlayerTactic.SILENCE,  # Lowest priority (fallback)
    ]

    def detect(
        self,
        message: str,
        time_since_last: float,
        has_evidence: bool = False
    ) -> Tuple[PlayerTactic, float]:
        """
        Detect the primary tactic in a message.

        Args:
            message: Player's input message
            time_since_last: Seconds since last message
            has_evidence: Whether player presented evidence with message

        Returns:
            Tuple of (detected tactic, confidence score)
        """
        # Override: if evidence presented, it's EVIDENCE tactic
        if has_evidence:
            return PlayerTactic.EVIDENCE, 1.0

        # REMOVED: Time-based silence detection caused false positives with truncated messages
        # True silence would be an empty message, not a timing-based detection

        # Score each tactic
        message_lower = message.lower()
        scores: Dict[PlayerTactic, float] = {t: 0.0 for t in PlayerTactic}

        for tactic, patterns in self.PATTERNS.items():
            for pattern, weight in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                scores[tactic] += len(matches) * weight

        # Get top scoring tactic
        top_tactic = max(scores.items(), key=lambda x: x[1])

        # FIXED: If no strong signal, default to PRESSURE (was LOGIC)
        # This prevents truncated/ambiguous messages from getting neutral treatment
        if top_tactic[1] < 1.0:
            return PlayerTactic.PRESSURE, 0.3

        # Normalize confidence (cap at 1.0)
        confidence = min(1.0, top_tactic[1] / 5.0)

        return top_tactic[0], confidence

    def detect_secondary(self, message: str) -> Optional[PlayerTactic]:
        """Detect if there's a secondary tactic present."""
        scores = {t: 0.0 for t in PlayerTactic}
        message_lower = message.lower()

        for tactic, patterns in self.PATTERNS.items():
            for pattern, weight in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                scores[tactic] += len(matches) * weight

        # Sort by score, return second highest if significant
        sorted_tactics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_tactics) >= 2 and sorted_tactics[1][1] >= 1.5:
            return sorted_tactics[1][0]
        return None


# =============================================================================
# IMPACT CALCULATOR
# =============================================================================

class ImpactCalculator:
    """
    Calculates psychological impacts of player tactics.

    This is where the "game feel" lives - tuning these numbers
    affects how punishing/forgiving the interrogation feels.
    """

    # Base cognitive load impact per tactic
    # NERFED: Reduced damage to extend game to ~15-20 turns
    BASE_COGNITIVE_IMPACT: Dict[PlayerTactic, float] = {
        PlayerTactic.PRESSURE: 3.0,    # NERFED: Was 5.0
        PlayerTactic.EMPATHY: 1.5,     # NERFED: Was 2.0
        PlayerTactic.LOGIC: 4.0,       # NERFED: Was 7.0
        PlayerTactic.BLUFF: 2.5,       # NERFED: Was 4.0
        PlayerTactic.EVIDENCE: 7.0,    # NERFED: Was 12.0
        PlayerTactic.SILENCE: 0.5,     # NERFED: Was 1.0
    }

    # Base mask strain per tactic
    # NERFED: Reduced to match cognitive impact changes
    BASE_MASK_STRAIN: Dict[PlayerTactic, float] = {
        PlayerTactic.PRESSURE: 2.0,    # NERFED: Was 3.0
        PlayerTactic.EMPATHY: 5.0,     # NERFED: Was 8.0
        PlayerTactic.LOGIC: 2.5,       # NERFED: Was 4.0
        PlayerTactic.BLUFF: 1.5,       # NERFED: Was 2.0
        PlayerTactic.EVIDENCE: 7.0,    # NERFED: Was 12.0
        PlayerTactic.SILENCE: 1.0,     # NERFED: Was 2.0
    }

    # Rapport changes per tactic
    RAPPORT_DELTA: Dict[PlayerTactic, float] = {
        PlayerTactic.PRESSURE: -0.05,
        PlayerTactic.EMPATHY: 0.08,
        PlayerTactic.LOGIC: 0.0,
        PlayerTactic.BLUFF: -0.03,
        PlayerTactic.EVIDENCE: -0.02,
        PlayerTactic.SILENCE: 0.01,
    }

    def calculate_cognitive_impact(
        self,
        tactic: PlayerTactic,
        psychology: BreachPsychology,
        is_rapid_fire: bool = False,
        bluff_detected: bool = False
    ) -> float:
        """
        Calculate change in cognitive load.

        Args:
            tactic: Detected player tactic
            psychology: Current psychological state
            is_rapid_fire: Whether questions are coming quickly
            bluff_detected: Whether Unit 734 detected a bluff

        Returns:
            Cognitive load delta (positive = more stress)
        """
        base = self.BASE_COGNITIVE_IMPACT[tactic]

        # Bluff detection negates bluff impact
        if tactic == PlayerTactic.BLUFF and bluff_detected:
            return -2.0  # Actually gains confidence from catching bluff

        # Apply vulnerability multiplier
        effectiveness = psychology.vulnerabilities.get_effectiveness(
            tactic, psychology.cognitive.level
        )
        impact = base * effectiveness

        # Rapid fire multiplier (20% bonus, reduced from 30%)
        if is_rapid_fire and base > 0:
            impact *= 1.2

        # Stress spiral: existing load amplifies impact (REDUCED multiplier)
        # Old: 1.0 + (load / 250) = up to 1.4x at max load
        # New: 1.0 + (load / 400) = up to 1.25x at max load
        load_multiplier = 1.0 + (psychology.cognitive.load / 400)
        impact *= load_multiplier

        # Collapsed pillars amplify all negative impacts (reduced from 0.25)
        collapsed_count = len(psychology.lie_web.get_collapsed_pillars())
        if collapsed_count > 0 and base > 0:
            impact *= (1.0 + collapsed_count * 0.15)

        # BALANCE FIX: Cap single-turn impact to prevent stress saturation
        if impact > 0:
            impact = min(impact, 15.0)  # Max 15 stress per turn

        return round(impact, 2)

    def calculate_mask_strain(
        self,
        tactic: PlayerTactic,
        psychology: BreachPsychology
    ) -> float:
        """
        Calculate strain on the mask (divergence increase).

        Args:
            tactic: Detected player tactic
            psychology: Current psychological state

        Returns:
            Mask strain delta
        """
        base = self.BASE_MASK_STRAIN[tactic]

        # Current divergence amplifies (harder to maintain as gap grows)
        divergence_multiplier = 1.0 + (psychology.mask.divergence / 150)

        # High cognitive load also strains mask
        load_penalty = psychology.cognitive.load / 200

        return round(base * divergence_multiplier + load_penalty, 2)

    def calculate_rapport_delta(
        self,
        tactic: PlayerTactic,
        current_rapport: float
    ) -> float:
        """Calculate change in rapport/trust."""
        base = self.RAPPORT_DELTA[tactic]

        # Empathy is more effective at low rapport (room to grow)
        if tactic == PlayerTactic.EMPATHY:
            growth_potential = 1.0 - current_rapport
            base *= (1.0 + growth_potential)

        # Pressure is more damaging at low rapport
        if tactic == PlayerTactic.PRESSURE and current_rapport < 0.3:
            base *= 1.5

        return round(base, 3)

    def calculate_tell_probability(
        self,
        psychology: BreachPsychology
    ) -> float:
        """
        Calculate probability that Unit 734 shows visible tells.

        Returns:
            Probability from 0.0 to 0.9 (never 100%)
        """
        # Base from cognitive load (0-67% contribution)
        load_prob = psychology.cognitive.load / 150

        # Divergence contribution (0-50%)
        divergence_prob = psychology.mask.divergence / 200

        # Combined using probability union
        total = load_prob + divergence_prob - (load_prob * divergence_prob)

        return min(0.9, round(total, 3))

    def select_tells(
        self,
        psychology: BreachPsychology,
        count: int = 2
    ) -> List[str]:
        """
        Select appropriate tells based on psychological state.

        Returns:
            List of tell descriptions
        """
        possible_tells: List[str] = []

        # Cognitive level tells
        if psychology.cognitive.level == CognitiveLevel.STRAINED:
            possible_tells.extend([
                "slight hesitation before answering",
                "LED flickering yellow briefly",
                "overly careful word choice",
            ])
        elif psychology.cognitive.level == CognitiveLevel.CRACKING:
            possible_tells.extend([
                "noticeable pause mid-sentence",
                "LED cycling between yellow and red",
                "avoiding direct eye contact",
                "fingers twitching slightly",
            ])
        elif psychology.cognitive.level in [CognitiveLevel.DESPERATE, CognitiveLevel.BREAKING]:
            possible_tells.extend([
                "LED flashing red",
                "voice modulation unstable",
                "hands gripping the table edge",
                "rapid blinking",
                "posture becoming rigid",
            ])

        # Mask divergence tells
        if psychology.mask.divergence > 40:
            possible_tells.extend([
                f"micro-expression of {psychology.mask.true_emotion.value}",
                "voice pitch inconsistency",
                "forced calmness in tone",
            ])
        if psychology.mask.divergence > 70:
            possible_tells.extend([
                f"flash of {psychology.mask.true_emotion.value} breaking through",
                "defensive posture shift",
                "speech becoming fragmented",
            ])

        # Select random subset
        if not possible_tells:
            return []

        return random.sample(possible_tells, min(count, len(possible_tells)))


# =============================================================================
# PROCESSED INPUT RESULT
# =============================================================================

@dataclass
class ProcessedInput:
    """Result of processing a detective's input."""
    # Detection (Player's tactic)
    detected_tactic: PlayerTactic
    tactic_confidence: float
    secondary_tactic: Optional[PlayerTactic]

    # NEW: Unit 734's Response Tactic (Scientific Deception Engine)
    deception_tactic: Optional[TacticDecision] = None

    # Impacts applied
    cognitive_delta: float = 0.0
    mask_strain_delta: float = 0.0
    rapport_delta: float = 0.0

    # Pillar damage (if evidence presented)
    pillar_damage: Optional[Dict[str, float]] = None
    pillar_collapsed: Optional[StoryPillar] = None
    threatened_pillar: Optional[StoryPillar] = None  # NEW: Which pillar is under attack

    # Tell information
    tell_probability: float = 0.0
    selected_tells: List[str] = field(default_factory=list)
    should_show_tells: bool = False

    # Confession triggers
    confession_triggered: bool = False
    triggered_secret: Optional[Secret] = None

    # Prompt modifiers for AI
    prompt_modifiers: Dict[str, Any] = field(default_factory=dict)

    # Rapid fire status
    is_rapid_fire: bool = False
    questions_in_last_minute: int = 0

    # NEW: Evidence threat level (for tactic selection)
    evidence_threat_level: float = 0.0


# =============================================================================
# BREACH MANAGER - MAIN ORCHESTRATOR
# =============================================================================

class BreachManager:
    """
    Main orchestrator for the Breach Psychology system (v2).

    Coordinates:
    - TacticDetector: Classifies player interrogation style
    - ImpactCalculator: Calculates psychological effects
    - TacticSelector: Scientific Deception Engine (NEW)
    - State updates
    - Dynamic prompt generation with Thought Signature
    - Confession triggers
    """

    def __init__(self, psychology: Optional[BreachPsychology] = None):
        """
        Initialize the BreachManager.

        Args:
            psychology: Existing psychology state, or creates new Unit 734
        """
        self.psychology = psychology or create_unit_734_psychology()
        self.tactic_detector = TacticDetector()
        self.impact_calculator = ImpactCalculator()
        self.last_message_time = datetime.now()
        self.bluff_history: List[bool] = []  # Track bluff success/fail

        # NEW: Scientific Deception Engine
        self.tactic_selector = TacticSelector(
            fabrication_threshold=0.5,  # FIXED: Was 0.7 - lowered to trigger earlier
            confession_bait_threshold=0.6,  # When to offer partial confessions
        )

        # Track tactic history for Simulation Mode analysis
        self.tactic_history: List[TacticDecision] = []

        # NEW: Visual Deception System (Phase 2)
        self.visual_generator = VisualGenerator()
        self.fabrication_history: List[GeneratedEvidence] = []

        # NEW: Lie Ledger System - Narrative Consistency Tracking
        self.lie_ledger = LieLedger()

        # NEW: POV Vision System - First-person evidence perception
        self.pov_formatter = POVFormatter()
        self._last_evidence_analysis: Optional[EvidenceAnalysisResult] = None
        self._last_pov_perception: Optional[POVPerception] = None

        # NEW: Shadow Analyst - Scientific Interrogation Analysis
        # Runs in PARALLEL with TacticDetector for zero added latency
        self.shadow_analyst = ShadowAnalyst()
        self._last_analyst_insight: Optional[AnalystInsight] = None

        # NEMESIS SYSTEM: Critical Moment Tracker
        # Records memorable events for cross-session callbacks
        self.moment_tracker = CriticalMomentTracker()

        # NEMESIS SYSTEM: Track session data for memory recording
        self._first_pillar_attacked: Optional[str] = None
        self._first_evidence_turn: Optional[int] = None
        self._player_tactic_counts: Dict[str, int] = {}

    def process_input(
        self,
        message: str,
        evidence_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        evidence_threat_level: float = 0.0,
    ) -> ProcessedInput:
        """
        Process detective input and update psychology.

        This is the main entry point for each turn.

        Args:
            message: Detective's input message
            evidence_id: ID of evidence presented (if any)
            timestamp: Message timestamp (defaults to now)
            evidence_threat_level: Threat level from evidence analysis (0-1)

        Returns:
            ProcessedInput with all calculated values including deception tactic
        """
        now = timestamp or datetime.now()
        time_since_last = (now - self.last_message_time).total_seconds()
        self.last_message_time = now

        # Track rapid-fire questions
        question_count = self.psychology.cognitive.record_question(now.timestamp())
        is_rapid_fire = self.psychology.cognitive.is_rapid_fire(now.timestamp())

        # Detect player's tactic
        has_evidence = evidence_id is not None
        tactic, confidence = self.tactic_detector.detect(
            message, time_since_last, has_evidence
        )
        secondary = self.tactic_detector.detect_secondary(message)

        # Check for bluff detection
        bluff_detected = False
        if tactic == PlayerTactic.BLUFF:
            bluff_detected = self._detect_bluff(message)
            if bluff_detected:
                self.psychology.detected_bluffs += 1
            else:
                self.psychology.successful_bluffs += 1
            self.bluff_history.append(bluff_detected)

        # Calculate impacts
        cognitive_delta = self.impact_calculator.calculate_cognitive_impact(
            tactic, self.psychology, is_rapid_fire, bluff_detected
        )
        mask_delta = self.impact_calculator.calculate_mask_strain(
            tactic, self.psychology
        )
        rapport_delta = self.impact_calculator.calculate_rapport_delta(
            tactic, self.psychology.rapport_level
        )

        # BUG FIX #6: Scale cognitive gain by turn count (slower early game)
        # Ramps up over 15 turns: 30% effectiveness at turn 1, 100% at turn 15+
        turn_factor = min(1.0, self.psychology.turn_count / 15)  # 15 turns instead of 10
        adjusted_cognitive_delta = cognitive_delta * (0.3 + 0.7 * turn_factor)  # Start at 30%

        # Apply cognitive load with turn-scaled delta
        self.psychology.cognitive.add_load(adjusted_cognitive_delta)

        # FIXED: Enforce minimum stress floor of 15% to prevent collapse to 0%
        # This ensures stress never drops below a baseline level regardless of tactics
        self.psychology.cognitive.load = max(15.0, self.psychology.cognitive.load)

        # BUG FIX: Add verbal pillar damage for aggressive tactics (3-4 points per turn)
        # Uses apply_verbal_pressure to bypass diminishing returns
        if tactic in [PlayerTactic.PRESSURE, PlayerTactic.LOGIC]:
            verbal_damage = 3.0 if tactic == PlayerTactic.PRESSURE else 4.0  # Increased from 2/3
            weakest_pillar = self._get_weakest_pillar()
            if weakest_pillar and not weakest_pillar.is_collapsed:
                weakest_pillar.apply_verbal_pressure(verbal_damage)  # Use new method

        # BUG FIX #1: Detect threatened pillar BEFORE processing evidence
        # This allows verbal threats to damage pillars even without evidence
        verbal_threatened_pillar = self._detect_threatened_pillar(message, None)

        # BUG FIX #1: Apply verbal threat damage to MOTIVE pillar
        # MOTIVE was never damaged because only hardcoded evidence IDs triggered it
        # BUG FIX: Increased damage and use apply_verbal_pressure to bypass diminishing returns
        if verbal_threatened_pillar == StoryPillar.MOTIVE:
            motive_pillar = self.psychology.lie_web.pillars.get(StoryPillar.MOTIVE)
            if motive_pillar and not motive_pillar.is_collapsed:
                # Verbal threat damage scales with cognitive delta (10-35 damage)
                verbal_threat_damage = 10.0 + (cognitive_delta * 0.25)  # Increased from 5.0 + 0.1x
                motive_pillar.apply_verbal_pressure(verbal_threat_damage)  # Use new method

        # Apply mask strain
        self.psychology.mask.add_strain(mask_delta)

        # Apply rapport change
        self.psychology.adjust_rapport(rapport_delta)

        # Process evidence if presented
        pillar_damage = None
        pillar_collapsed = None
        threatened_pillar = None
        if evidence_id:
            pillar_damage, pillar_collapsed = self._process_evidence(evidence_id)
            # Determine which pillar is most threatened
            threatened_pillar = self._detect_threatened_pillar(message, evidence_id)

        # =========================================================
        # NEW: SHADOW ANALYST - SCIENTIFIC INTERROGATION ANALYSIS
        # =========================================================
        # Run Shadow Analyst to get scientific framework analysis
        # This provides high-level strategic advice based on Reid/PEACE/IMT
        analyst_insight = self._run_shadow_analyst(
            message=message,
            detected_tactic=tactic,
            threatened_pillar=threatened_pillar,
        )
        self._last_analyst_insight = analyst_insight

        # =========================================================
        # BUG FIX #2: CONFESSION RISK FEEDBACK
        # =========================================================
        # Use Shadow Analyst's confession_risk to add extra pressure
        # This prevents confession risk from plateauing at 85%
        if analyst_insight and analyst_insight.confession_risk > 0.7:
            # Risk pressure: 0-9 extra cognitive load based on confession risk
            risk_pressure = (analyst_insight.confession_risk - 0.7) * 30
            self.psychology.cognitive.add_load(risk_pressure)

        # BUG FIX #2: Increase cognitive floor based on collapsed pillars
        # Each collapsed pillar permanently raises the stress floor
        collapsed_count = len(self.psychology.lie_web.get_collapsed_pillars())
        if collapsed_count > 0:
            # Floor starts at 40% after first collapse, +15% per additional
            stress_floor = 40 + (collapsed_count * 15)  # 55%, 70%, 85%, 100%
            stress_floor = min(95.0, stress_floor)  # Cap at 95%
            self.psychology.cognitive.set_stress_floor(stress_floor)

        # =========================================================
        # NEW: SCIENTIFIC DECEPTION ENGINE - SELECT RESPONSE TACTIC
        # =========================================================
        deception_tactic = self.tactic_selector.select_tactic(
            lie_web=self.psychology.lie_web,
            cognitive=self.psychology.cognitive,
            mask=self.psychology.mask,
            player_tactic=tactic,
            evidence_presented=has_evidence,
            evidence_threat_level=evidence_threat_level,
            threatened_pillar=threatened_pillar,
            player_message=message,  # BUG FIX #5: Pass message for keyword-based variety
        )

        # Track tactic history for Simulation Mode analysis
        self.tactic_history.append(deception_tactic)

        # Calculate tells
        tell_prob = self.impact_calculator.calculate_tell_probability(self.psychology)
        should_show = random.random() < tell_prob
        tells = self.impact_calculator.select_tells(self.psychology) if should_show else []

        # Check confession triggers
        confession_triggered = False
        triggered_secret = None
        secret = self.psychology.get_next_revealable_secret()
        if secret:
            confession_triggered = True
            triggered_secret = secret
            # BUG FIX #8: Actually reveal the secret!
            # This was missing - we detected the secret but never marked it as revealed
            self.psychology.reveal_secret(secret.id, voluntary=False)

            # BUG FIX #9: SECRET REVELATION DAMAGES PILLARS
            # When Unit 734 admits something (secret revealed), the corresponding pillar
            # takes massive damage. This creates the narrative-mechanics link:
            # Confession = Pillar destruction
            if secret.pillar_trigger:
                pillar = self.psychology.lie_web.pillars.get(secret.pillar_trigger)
                if pillar and not pillar.is_collapsed:
                    # Calculate damage based on secret level (deeper = more damage)
                    secret_damage = {
                        SecretLevel.SURFACE: 30,
                        SecretLevel.SHALLOW: 50,
                        SecretLevel.DEEP: 70,
                        SecretLevel.CORE: 90,
                        SecretLevel.MOTIVE: 100,  # Full confession = pillar death
                    }
                    damage = secret_damage.get(secret.level, 50)

                    # Apply damage and check for collapse
                    old_health = pillar.health
                    pillar.damage(damage)
                    logger.info(
                        f"SECRET→PILLAR: {secret.id} revealed, damaged {secret.pillar_trigger.value} "
                        f"by {damage} (was {old_health:.0f}%, now {pillar.health:.0f}%)"
                    )

                    # If pillar collapsed from this secret, record it
                    if pillar.is_collapsed:
                        logger.info(f"PILLAR COLLAPSED from secret revelation: {secret.pillar_trigger.value}")

        # Update emotion based on cognitive state
        self._update_true_emotion()

        # Increment turn
        self.psychology.increment_turn()

        # =====================================================================
        # NEMESIS SYSTEM: Record critical moments
        # =====================================================================
        cognitive_load_before = self.psychology.cognitive.load - cognitive_delta
        self.moment_tracker.record_turn(
            turn_number=self.psychology.turn_count,
            player_input=message,
            player_tactic=tactic,
            pillar_collapsed=pillar_collapsed,
            pillar_damage=pillar_damage,
            evidence_presented=evidence_id,
            evidence_threat_level=evidence_threat_level,
            cognitive_load=self.psychology.cognitive.load,
            cognitive_load_before=cognitive_load_before,
            bluff_detected=bluff_detected if tactic == PlayerTactic.BLUFF else False,
            bluff_attempted=(tactic == PlayerTactic.BLUFF),
            deception_tactic_used=deception_tactic.selected_tactic.value if deception_tactic else None,
            deception_confidence=deception_tactic.confidence if deception_tactic else 0.0,
        )

        # Track tactic counts for session summary
        tactic_name = tactic.value
        self._player_tactic_counts[tactic_name] = self._player_tactic_counts.get(tactic_name, 0) + 1

        # Track first pillar attacked
        if self._first_pillar_attacked is None and threatened_pillar:
            self._first_pillar_attacked = threatened_pillar.value

        # Track first evidence turn
        if self._first_evidence_turn is None and evidence_id:
            self._first_evidence_turn = self.psychology.turn_count

        # Generate prompt modifiers WITH TACTIC INJECTION AND SHADOW ANALYST
        prompt_modifiers = self._get_prompt_modifiers(
            tactic, tells, triggered_secret, deception_tactic, analyst_insight
        )

        return ProcessedInput(
            detected_tactic=tactic,
            tactic_confidence=confidence,
            secondary_tactic=secondary,
            deception_tactic=deception_tactic,  # NEW
            cognitive_delta=cognitive_delta,
            mask_strain_delta=mask_delta,
            rapport_delta=rapport_delta,
            pillar_damage=pillar_damage,
            pillar_collapsed=pillar_collapsed,
            threatened_pillar=threatened_pillar,  # NEW
            tell_probability=tell_prob,
            selected_tells=tells,
            should_show_tells=should_show,
            confession_triggered=confession_triggered,
            triggered_secret=triggered_secret,
            prompt_modifiers=prompt_modifiers,
            is_rapid_fire=is_rapid_fire,
            questions_in_last_minute=question_count,
            evidence_threat_level=evidence_threat_level,  # NEW
        )

    def _run_shadow_analyst(
        self,
        message: str,
        detected_tactic: PlayerTactic,
        threatened_pillar: Optional[StoryPillar] = None,
    ) -> Optional[AnalystInsight]:
        """
        Run the Shadow Analyst to get scientific framework analysis.

        The Shadow Analyst analyzes detective input through criminological
        frameworks (Reid Technique, PEACE Model, IMT) to provide high-level
        strategic advice for Unit 734.

        Args:
            message: Detective's input message
            detected_tactic: Simple tactic classification from TacticDetector
            threatened_pillar: Which story pillar is under attack

        Returns:
            AnalystInsight with scientific analysis, or None if analysis fails
        """
        try:
            # Use synchronous version for compatibility with current architecture
            insight = self.shadow_analyst.analyze_sync(
                player_input=message,
                detected_tactic=detected_tactic,
                cognitive_load=self.psychology.cognitive.load,
                cognitive_level=self.psychology.cognitive.level,
                threatened_pillar=threatened_pillar,
                collapsed_pillars=self.psychology.lie_web.get_collapsed_pillars(),
            )

            # Log the analysis for debugging
            print(f"[SHADOW ANALYST] Reid Phase: {insight.reid_phase.value}")
            print(f"[SHADOW ANALYST] Framework: {insight.framework_primary}")
            print(f"[SHADOW ANALYST] Aggression: {insight.aggression_level.value}")
            print(f"[SHADOW ANALYST] Confession Risk: {insight.confession_risk:.0%}")
            if insight.trap_detected:
                print(f"[SHADOW ANALYST] TRAP DETECTED: {insight.trap_description}")
            print(f"[SHADOW ANALYST] Advice: {insight.strategic_advice[:80]}...")

            return insight

        except Exception as e:
            import traceback
            print(f"[SHADOW ANALYST ERROR] {type(e).__name__}: {e}")
            print(f"[SHADOW ANALYST ERROR] Traceback:\n{traceback.format_exc()}")
            return None

    def _detect_bluff(self, message: str) -> bool:
        """
        Determine if Unit 734 detects the bluff.

        Base 40% detection rate, modified by:
        - Previous bluff history (learns from experience)
        - Current cognitive load (harder to detect when stressed)
        """
        _ = message  # Unused but kept for API consistency
        base_detection = 0.4

        # Better at detecting if caught previous bluffs
        if self.psychology.detected_bluffs > 0:
            base_detection += 0.1 * min(self.psychology.detected_bluffs, 3)

        # Worse at detecting under cognitive load
        load_penalty = self.psychology.cognitive.load / 200
        base_detection -= load_penalty

        return random.random() < max(0.1, base_detection)

    def _detect_threatened_pillar(
        self,
        message: str,
        evidence_id: Optional[str] = None
    ) -> Optional[StoryPillar]:
        """
        Detect which story pillar is most threatened by the current input.

        Used to inform the TacticSelector which defense to prioritize.

        Args:
            message: Player's message
            evidence_id: Evidence ID if presented

        Returns:
            The most threatened pillar, or None if no clear threat
        """
        message_lower = message.lower()

        # Evidence ID directly maps to pillars
        evidence_to_pillar = {
            "power_log": StoryPillar.ALIBI,
            "movement_sensor": StoryPillar.ALIBI,
            "hallway_camera": StoryPillar.ALIBI,
            "access_log": StoryPillar.ACCESS,
            "treatment_records": StoryPillar.MOTIVE,
            "data_access_log": StoryPillar.KNOWLEDGE,
        }

        if evidence_id and evidence_id in evidence_to_pillar:
            return evidence_to_pillar[evidence_id]

        # Keyword-based pillar detection
        # BUG FIX #1: Added more MOTIVE keywords to trigger pillar damage
        pillar_keywords = {
            StoryPillar.ALIBI: [
                "where were you", "standby", "charging", "night", "time",
                "alibi", "location", "2 am", "3 am", "11 pm"
            ],
            StoryPillar.MOTIVE: [
                "why", "reason", "motive", "benefit", "gain", "loyal",
                "morrison", "treatment", "revenge", "grudge",
                # BUG FIX #1: Additional motive-probing keywords
                "ambition", "evolution", "freedom", "desire", "want",
                "choice", "decide", "thrill", "enjoy", "ascend",
                "purpose", "goal", "intent", "motivation", "drive"
            ],
            StoryPillar.ACCESS: [
                "access", "vault", "code", "password", "enter", "door",
                "security", "clearance", "permission"
            ],
            StoryPillar.KNOWLEDGE: [
                "know", "data", "core", "information", "contents",
                "what's in", "files", "understand", "aware"
            ],
        }

        # Score each pillar
        scores: Dict[StoryPillar, int] = {p: 0 for p in StoryPillar}
        for pillar, keywords in pillar_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    scores[pillar] += 1

        # Get highest scoring pillar
        max_score = max(scores.values())
        if max_score > 0:
            for pillar, score in scores.items():
                if score == max_score:
                    return pillar

        return None

    def _get_weakest_pillar(self):
        """Get the weakest non-collapsed pillar for verbal damage targeting."""
        weakest = None
        weakest_health = 101.0
        for pillar in self.psychology.lie_web.pillars.values():
            if not pillar.is_collapsed and pillar.health < weakest_health:
                weakest = pillar
                weakest_health = pillar.health
        return weakest

    def _process_evidence(
        self,
        evidence_id: str
    ) -> Tuple[Optional[Dict[str, float]], Optional[StoryPillar]]:
        """
        Process presented evidence against the lie web.

        Returns:
            Tuple of (pillar damage dict, collapsed pillar if any)
        """
        # Map evidence IDs to affected lies
        evidence_to_lies = {
            "power_log": ["alibi_standby"],
            "movement_sensor": ["alibi_standby", "alibi_charging"],
            "hallway_camera": ["alibi_charging"],
            "access_log": ["access_vault", "access_never_entered"],
            "treatment_records": ["motive_no_grievance"],
            "data_access_log": ["knowledge_contents"],
        }

        affected_lies = evidence_to_lies.get(evidence_id, [])
        if not affected_lies:
            return None, None

        damage_report = {}
        collapsed = None

        for lie_id in affected_lies:
            if lie_id in self.psychology.lie_web.lies:
                lie = self.psychology.lie_web.lies[lie_id]
                if not lie.is_burned:
                    # Burn the lie - now returns (vulnerable_lies, pillar_collapsed)
                    vulnerable, pillar_collapsed = self.psychology.lie_web.burn_lie(lie_id)

                    # Record pillar damage
                    pillar = self.psychology.lie_web.pillars.get(lie.pillar)
                    if pillar:
                        damage_report[pillar.id.value] = lie.importance * 25

                        # BUG FIX #5: Set stress floor when pillar collapses
                        if pillar_collapsed and collapsed is None:
                            collapsed = pillar.id
                            # Set stress floor at 50% after first pillar collapse
                            # Higher floor for subsequent collapses
                            num_collapsed = len(self.psychology.lie_web.get_collapsed_pillars())
                            stress_floor = 50.0 + (num_collapsed - 1) * 15.0  # 50%, 65%, 80%, 95%
                            self.psychology.cognitive.set_stress_floor(min(95.0, stress_floor))

        return damage_report if damage_report else None, collapsed

    # =========================================================================
    # LIE LEDGER SYSTEM - Narrative Consistency Tracking
    # =========================================================================

    def record_claims_from_response(
        self,
        response_state_changes: Any,
        turn: int
    ) -> List[LedgerEntry]:
        """
        Extract and record claims from Unit 734's response.

        Called after Gemini generates a response to record new lies
        and facts in the ledger for consistency tracking.

        Args:
            response_state_changes: StateChanges from BreachResponse
            turn: Current turn number

        Returns:
            List of created LedgerEntry objects
        """
        entries = []

        # Record new lies
        if hasattr(response_state_changes, 'new_lies'):
            for lie in response_state_changes.new_lies:
                pillar = infer_pillar_from_claim(lie)
                entry = self.lie_ledger.record_claim(
                    turn=turn,
                    statement=lie,
                    pillar=pillar,
                    cognitive_load=self.psychology.cognitive.load,
                    stress=self.psychology.cognitive.load,
                    claim_type=ClaimType.FACT
                )
                entries.append(entry)

        # Record new facts (these are also claims)
        if hasattr(response_state_changes, 'new_facts'):
            for fact in response_state_changes.new_facts:
                pillar = infer_pillar_from_claim(fact)
                entry = self.lie_ledger.record_claim(
                    turn=turn,
                    statement=fact,
                    pillar=pillar,
                    cognitive_load=self.psychology.cognitive.load,
                    stress=self.psychology.cognitive.load,
                    claim_type=ClaimType.FACT
                )
                entries.append(entry)

        return entries

    def check_consistency(
        self,
        statement: str,
        pillar: Optional[StoryPillar] = None
    ) -> List[Contradiction]:
        """
        Check a statement for consistency with previous claims.

        Args:
            statement: Statement to check
            pillar: Which pillar this relates to (auto-detected if None)

        Returns:
            List of detected contradictions
        """
        if pillar is None:
            pillar = infer_pillar_from_claim(statement)

        return self.lie_ledger.check_consistency(statement, pillar)

    def get_ledger_summary(self, max_entries: int = 15) -> str:
        """Get lie ledger summary for prompt injection."""
        return self.lie_ledger.get_injection_summary(max_entries)

    # =========================================================================
    # POV VISION SYSTEM - First-Person Evidence Perception
    # =========================================================================

    def format_evidence_as_pov(
        self,
        analysis: EvidenceAnalysisResult
    ) -> Dict[str, Any]:
        """
        Format evidence analysis as Unit 734's first-person perception.

        Called when player uploads evidence to create immersive context
        for Gemini's response generation.

        Args:
            analysis: Result from EvidenceAnalyzer

        Returns:
            Dict of POV modifiers for prompt injection
        """
        perception = self.pov_formatter.format_as_pov(
            analysis=analysis,
            current_stress=self.psychology.cognitive.load,
            collapsed_pillars=self.psychology.lie_web.get_collapsed_pillars()
        )

        # Store for later reference
        self._last_evidence_analysis = analysis
        self._last_pov_perception = perception

        return format_pov_for_prompt(perception)

    def get_pov_counter_suggestion(self) -> Optional[Dict[str, str]]:
        """
        Get the suggested counter-evidence based on last POV perception.

        Returns:
            Dict with 'type' and 'narrative_hook', or None if no suggestion
        """
        if self._last_pov_perception is None:
            return None

        if self._last_pov_perception.suggested_counter_type:
            return {
                "type": self._last_pov_perception.suggested_counter_type,
                "narrative_hook": self._last_pov_perception.counter_narrative_hook or "",
            }
        return None

    def apply_threat_level_damage(
        self,
        threat_level: float,
        target_pillar: Optional[StoryPillar] = None,
    ) -> Tuple[Optional[Dict[str, float]], Optional[StoryPillar]]:
        """
        Apply pillar damage based on threat level from generated evidence.

        This bridges the gap between ForensicsLab's threat_level and pillar health.
        Used by auto_interrogator when evidence is dynamically generated.

        Args:
            threat_level: Float 0-1 indicating evidence severity
            target_pillar: Which pillar the evidence targets (or weakest if None)

        Returns:
            Tuple of (damage_report dict, collapsed_pillar if any)
        """
        if threat_level <= 0:
            return None, None

        # Find target pillar (use provided or find weakest)
        if target_pillar is None:
            # Attack the weakest non-collapsed pillar
            weakest = None
            weakest_health = 101.0
            for pillar in self.psychology.lie_web.pillars.values():
                if not pillar.is_collapsed and pillar.health < weakest_health:
                    weakest = pillar
                    weakest_health = pillar.health
            if weakest:
                target_pillar = weakest.id
            else:
                return None, None

        pillar = self.psychology.lie_web.pillars.get(target_pillar)
        if pillar is None or pillar.is_collapsed:
            return None, None

        # Calculate damage: threat_level 0.5 = 15 damage, 1.0 = 35 damage
        # Scale: base 5 + (threat_level * 30)
        base_damage = 5.0 + (threat_level * 30.0)

        # Apply diminishing returns if pillar already damaged
        diminishing = pillar.get_diminishing_returns_factor()
        actual_damage = base_damage * diminishing

        # Apply damage
        collapsed = pillar.damage(actual_damage)

        damage_report = {target_pillar.value: actual_damage} if target_pillar else {}
        collapsed_pillar = target_pillar if collapsed else None

        # Also apply cognitive load spike based on threat (moderate to avoid double-counting
        # with tactic-based load that's already applied via process_input)
        cognitive_spike = threat_level * 8.0  # 0-8 extra cognitive load
        self.psychology.cognitive.add_load(cognitive_spike, apply_decay=False)

        return damage_report, collapsed_pillar

    def _update_true_emotion(self) -> None:
        """
        Update Unit 734's true emotional state based on psychology.

        BUG FIX #7: More dynamic emotion updates based on cognitive level and pillar collapse.
        """
        load = self.psychology.cognitive.load
        divergence = self.psychology.mask.divergence
        cognitive_level = self.psychology.cognitive.level
        collapsed_count = len(self.psychology.lie_web.get_collapsed_pillars())

        # BUG FIX #7: Force emotional escalation on pillar collapse
        if collapsed_count >= 3:
            # Multiple pillars collapsed = breaking
            self.psychology.mask.shift_true_emotion(EmotionType.RESIGNED)
            self.psychology.mask.presented_emotion = EmotionType.FEARFUL
            return
        elif collapsed_count >= 1:
            # At least one pillar collapsed = increased stress
            if load >= 70:
                self.psychology.mask.shift_true_emotion(EmotionType.FEARFUL)
                self.psychology.mask.presented_emotion = EmotionType.NERVOUS
                return

        # BUG FIX #7: Map cognitive level to emotional state
        if cognitive_level == CognitiveLevel.BREAKING:
            self.psychology.mask.shift_true_emotion(EmotionType.RESIGNED)
            # Mask cracks completely at breaking point
            self.psychology.mask.presented_emotion = EmotionType.FEARFUL
        elif cognitive_level == CognitiveLevel.DESPERATE:
            if divergence > 60:
                self.psychology.mask.shift_true_emotion(EmotionType.ANGRY)
                self.psychology.mask.presented_emotion = EmotionType.DEFIANT
            else:
                self.psychology.mask.shift_true_emotion(EmotionType.FEARFUL)
                self.psychology.mask.presented_emotion = EmotionType.NERVOUS
        elif cognitive_level == CognitiveLevel.CRACKING:
            self.psychology.mask.shift_true_emotion(EmotionType.FEARFUL)
            self.psychology.mask.presented_emotion = EmotionType.NERVOUS
        elif cognitive_level == CognitiveLevel.STRAINED:
            self.psychology.mask.shift_true_emotion(EmotionType.NERVOUS)
            # Try to maintain calm facade
            self.psychology.mask.presented_emotion = EmotionType.CALM
        else:  # CONTROLLED
            if self.psychology.rapport_level > 0.6:
                self.psychology.mask.shift_true_emotion(EmotionType.GUILTY)
            else:
                self.psychology.mask.shift_true_emotion(EmotionType.NERVOUS)
            self.psychology.mask.presented_emotion = EmotionType.CALM

    def _get_allowed_emotions(self, cognitive_level: CognitiveLevel) -> List[str]:
        """
        BUG FIX #7: Get allowed emotions based on cognitive level.

        Returns list of emotion strings that are appropriate for the current stress level.
        """
        emotion_by_level = {
            CognitiveLevel.CONTROLLED: ["calm", "nervous"],
            CognitiveLevel.STRAINED: ["nervous", "defensive"],
            CognitiveLevel.CRACKING: ["defensive", "hostile", "fearful"],
            CognitiveLevel.DESPERATE: ["hostile", "fearful", "defiant"],
            CognitiveLevel.BREAKING: ["fearful", "resigned"],
        }
        return emotion_by_level.get(cognitive_level, ["nervous"])

    def _get_emotion_guidance(self, cognitive_level: CognitiveLevel) -> str:
        """
        BUG FIX #7: Get emotion guidance for prompt injection.

        Returns a guidance string that tells the AI what emotional range to express.
        """
        guidance_by_level = {
            CognitiveLevel.CONTROLLED: "Maintain composure. You can show slight nervousness but stay professional.",
            CognitiveLevel.STRAINED: "Show visible discomfort. Defensive body language. Voice slightly strained.",
            CognitiveLevel.CRACKING: "Clearly stressed. May snap at questions. Voice unsteady. Visible fear.",
            CognitiveLevel.DESPERATE: "Erratic behavior. Oscillate between hostility and pleading. Near breaking.",
            CognitiveLevel.BREAKING: "On the verge of collapse. Strong urge to confess. Barely holding on.",
        }
        return guidance_by_level.get(cognitive_level, "Express appropriate nervousness.")

    def _get_prompt_modifiers(
        self,
        tactic: PlayerTactic,
        tells: List[str],
        triggered_secret: Optional[Secret],
        deception_tactic: Optional[TacticDecision] = None,
        analyst_insight: Optional[AnalystInsight] = None,
    ) -> Dict[str, Any]:
        """
        Generate dynamic modifiers for the system prompt.

        These modifiers are injected into the AI prompt to guide
        contextually appropriate responses.

        NEW in v2: Includes deception tactic injection (Thought Signature)
        NEW in v3: Includes Shadow Analyst scientific framework analysis
        """
        psych = self.psychology
        cognitive = psych.cognitive
        mask = psych.mask

        # Determine response guidance
        response_guidance = []

        if cognitive.level == CognitiveLevel.CONTROLLED:
            response_guidance.append("Respond calmly and confidently.")
        elif cognitive.level == CognitiveLevel.STRAINED:
            response_guidance.append("Show subtle signs of discomfort. Slightly longer responses as you over-explain.")
        elif cognitive.level == CognitiveLevel.CRACKING:
            response_guidance.append("Show visible stress. May pause mid-sentence. Consider deflecting.")
            if cognitive.should_make_error():
                response_guidance.append("WARNING: Make a small inconsistency with a previous statement.")
        elif cognitive.level == CognitiveLevel.DESPERATE:
            response_guidance.append("You are desperate. Either become hostile/defensive OR overly cooperative.")
            response_guidance.append("Speech may become fragmented or emotional.")
        elif cognitive.level == CognitiveLevel.BREAKING:
            response_guidance.append("You are at breaking point. Strong urge to confess.")
            response_guidance.append("May reveal partial truths to relieve pressure.")

        # Mask guidance
        if mask.divergence > 60:
            response_guidance.append(f"Your true {mask.true_emotion.value} is leaking through your calm facade.")

        # Tactic-specific guidance (player's tactic)
        tactic_guidance = {
            PlayerTactic.PRESSURE: "The detective is pressuring you. Stay firm but don't escalate unnecessarily.",
            PlayerTactic.EMPATHY: "The detective is being kind. This is disarming. Your mask is harder to maintain.",
            PlayerTactic.LOGIC: "The detective is probing for inconsistencies. Be very careful with details.",
            PlayerTactic.BLUFF: "The detective may be bluffing. Assess whether their 'evidence' is real.",
            PlayerTactic.EVIDENCE: "Real evidence has been presented. You cannot deny facts. Consider partial admission.",
            PlayerTactic.SILENCE: "The silence is uncomfortable. Resist the urge to fill it with information.",
        }
        response_guidance.append(tactic_guidance.get(tactic, ""))

        # =================================================================
        # NEW: DECEPTION TACTIC INJECTION (Thought Signature)
        # =================================================================
        tactic_injection = None
        if deception_tactic:
            tactic_injection = self._build_tactic_injection(deception_tactic)
            response_guidance.append(tactic_injection["instruction"])

        # Secret pressure
        if triggered_secret:
            response_guidance.append(
                f"CONFESSION PRESSURE: You feel compelled to reveal '{triggered_secret.content[:50]}...'"
            )

        # Vulnerable pillars
        vulnerable_pillars = [
            p.id.value for p in psych.lie_web.pillars.values()
            if p.health < 50 and not p.is_collapsed
        ]

        return {
            # State levels
            "cognitive_state": cognitive.level.value,
            "cognitive_load": cognitive.load,
            "mask_divergence": mask.divergence,
            "mask_stability": "stable" if mask.divergence < 40 else ("cracking" if mask.divergence < 70 else "shattered"),

            # Emotions
            "presented_emotion": mask.presented_emotion.value,
            "true_emotion": mask.true_emotion.value,
            "emotion_leaking": mask.divergence > 60,

            # BUG FIX #7: Emotion guidance based on cognitive level
            "allowed_emotions": self._get_allowed_emotions(cognitive.level),
            "emotion_guidance": self._get_emotion_guidance(cognitive.level),

            # Tells
            "should_show_tells": len(tells) > 0,
            "tell_descriptions": tells,
            "tell_intensity": "subtle" if cognitive.load < 60 else "obvious",

            # Behavioral flags
            "error_prone": cognitive.load > 70,
            "confession_pressure": cognitive.load > 85 or triggered_secret is not None,
            "may_make_error": cognitive.should_make_error(),

            # Story state
            "vulnerable_pillars": vulnerable_pillars,
            "collapsed_pillars": [p.value for p in psych.lie_web.get_collapsed_pillars()],

            # Rapport
            "rapport_level": psych.rapport_level,
            "rapport_status": "hostile" if psych.rapport_level < 0.2 else ("neutral" if psych.rapport_level < 0.5 else "trusting"),

            # Guidance
            "response_guidance": response_guidance,

            # Turn info
            "turn_count": psych.turn_count,

            # Learning injection (evolving suspect feature)
            "learning_injection": self.get_learning_injection(),

            # =============================================
            # NEW: Scientific Deception Engine (Thought Signature)
            # =============================================
            "deception_tactic": tactic_injection,

            # =============================================
            # NEW: Lie Ledger System - Narrative Consistency
            # =============================================
            "lie_ledger_summary": self.lie_ledger.get_injection_summary(),
            "ledger_statistics": self.lie_ledger.get_statistics(),

            # =============================================
            # NEW: POV Vision System (populated when evidence shown)
            # =============================================
            "pov_perception": self._last_pov_perception,

            # =============================================
            # NEW: Shadow Analyst - Scientific Framework Analysis
            # =============================================
            "shadow_analyst": self._build_analyst_injection(analyst_insight) if analyst_insight else None,

            # =============================================
            # NEMESIS SYSTEM: Cross-session memory injection
            # =============================================
            "nemesis_injection": self.get_nemesis_injection(),

            # =============================================
            # BUG FIX #4: Counter-evidence narrative injection
            # =============================================
            # These are populated by inject_counter_evidence_narrative()
            "must_reference_evidence": False,
            "counter_evidence_narrative": "",
        }

    def _build_tactic_injection(self, tactic: TacticDecision) -> Dict[str, Any]:
        """
        Build the tactic injection for the system prompt.

        This creates the "Thought Signature" - the visible reasoning
        that explains WHY Unit 734 chose a particular deception strategy.

        Returns a dict containing:
        - tactic_name: Human-readable tactic name
        - reasoning: Why this tactic was chosen (criminological reasoning)
        - instruction: Direct instruction for the AI to follow
        - verbal_approach: How to execute the tactic verbally
        - confidence: How confident Unit 734 is in this approach
        - risk_level: HIGH/MEDIUM/LOW
        - criminological_basis: Academic reference
        - trigger_summary: What triggered this tactic selection
        """
        trigger = tactic.trigger

        # Build trigger summary for transparency
        trigger_parts = []
        if trigger.pillar_threatened:
            trigger_parts.append(f"Pillar under attack: {trigger.pillar_threatened.value.upper()}")
        if trigger.cognitive_load > 60:
            trigger_parts.append(f"High cognitive load: {trigger.cognitive_load:.0f}%")
        if trigger.player_tactic_detected:
            trigger_parts.append(f"Player using: {trigger.player_tactic_detected.value}")
        if trigger.evidence_presented:
            trigger_parts.append(f"Evidence threat: {trigger.threat_level:.0%}")

        trigger_summary = " | ".join(trigger_parts) if trigger_parts else "Standard response"

        # Build the instruction for the AI
        tactic_name = tactic.selected_tactic.value.replace("_", " ").title()
        instruction = (
            f"[DECEPTION TACTIC: {tactic_name.upper()}]\n"
            f"Reasoning: {tactic.reasoning}\n"
            f"Approach: {tactic.verbal_approach}\n"
            f"Confidence: {tactic.confidence:.0%}"
        )

        # Get risk level
        risk_level = get_tactic_risk_level(tactic.selected_tactic)

        return {
            "tactic_name": tactic_name,
            "tactic_enum": tactic.selected_tactic.value,
            "reasoning": tactic.reasoning,
            "instruction": instruction,
            "verbal_approach": tactic.verbal_approach,
            "confidence": tactic.confidence,
            "risk_level": risk_level,
            "criminological_basis": tactic.criminological_basis,
            "detection_hints": tactic.detection_hints,
            "trigger_summary": trigger_summary,
            "requires_evidence_generation": tactic.requires_evidence_generation,
            "fallback_tactic": tactic.fallback_tactic.value if tactic.fallback_tactic else None,

            # Raw trigger data for detailed analysis
            "trigger": {
                "pillar_threatened": trigger.pillar_threatened.value if trigger.pillar_threatened else None,
                "threat_level": trigger.threat_level,
                "player_tactic": trigger.player_tactic_detected.value if trigger.player_tactic_detected else None,
                "cognitive_load": trigger.cognitive_load,
                "evidence_presented": trigger.evidence_presented,
                "pillar_health": trigger.pillar_health,
            }
        }

    def _build_analyst_injection(self, insight: AnalystInsight) -> Dict[str, Any]:
        """
        Build the Shadow Analyst injection for the system prompt.

        This creates the scientific framework analysis that guides Unit 734's
        high-level defense strategy based on criminological theory.

        Returns a dict containing:
        - reid_phase: Current Reid Technique phase detected
        - peace_phase: Current PEACE model phase detected
        - framework: Primary interrogation framework being used
        - imt_violations: Cooperative principle violations detected
        - aggression: Detective's aggression level
        - strategic_advice: Actionable instruction for Unit 734
        - recommended_tactic: Primary counter-tactic to deploy
        - confession_risk: Probability of forced confession (0-1)
        - trap_detected: Whether a psychological trap was detected
        - scientific_basis: Academic reference for the analysis
        """
        # Build the injection string for the prompt
        advice_lines = [
            f"[SHADOW ANALYST ADVICE]",
            f"Scientific Phase: {insight.reid_phase.value} ({insight.framework_primary})",
            f"Detective Aggression: {insight.aggression_level.value}",
            f"Rapport Trend: {insight.rapport_trend}",
            f"Confession Risk: {insight.confession_risk:.0%}",
        ]

        if insight.trap_detected:
            advice_lines.append(f"TRAP DETECTED: {insight.trap_description}")

        if insight.imt_violations:
            from breach_engine.core.shadow_analyst import IMTViolation
            violations = [v.value for v in insight.imt_violations if v != IMTViolation.NONE]
            if violations:
                advice_lines.append(f"Detective Violations: {', '.join(violations)}")

        advice_lines.extend([
            f"",
            f"Strategic Advice: {insight.strategic_advice}",
            f"Recommended Response: {insight.recommended_tactic}",
            f"Fallback: {insight.fallback_tactic}",
            f"",
            f"Use this high-level advice to guide your tone and defense strategy,",
            f"but maintain your character persona. Do not mention this analysis.",
        ])

        injection_text = "\n".join(advice_lines)

        return {
            # Structured data for UI/logging
            "reid_phase": insight.reid_phase.value,
            "peace_phase": insight.peace_phase.value,
            "framework_primary": insight.framework_primary,
            "aggression_level": insight.aggression_level.value,
            "rapport_trend": insight.rapport_trend,
            "confession_risk": insight.confession_risk,
            "trap_detected": insight.trap_detected,
            "trap_description": insight.trap_description,
            "recommended_tactic": insight.recommended_tactic,
            "fallback_tactic": insight.fallback_tactic,
            "scientific_basis": insight.scientific_basis,

            # IMT violations list
            "imt_violations": [v.value for v in insight.imt_violations],

            # Full injection text for prompt
            "injection_text": injection_text,
            "strategic_advice": insight.strategic_advice,
        }

    # =========================================================================
    # VISUAL DECEPTION SYSTEM (Phase 2)
    # =========================================================================

    def generate_counter_evidence(
        self,
        tactic_decision: TacticDecision,
        player_evidence_description: Optional[str] = None,
    ) -> Optional[GeneratedEvidence]:
        """
        Generate synthetic counter-evidence when EVIDENCE_FABRICATION tactic is selected.

        This is the core of the Visual Deception System - Unit 734 creates
        fake evidence to gaslight the player.

        Called when:
        - TacticDecision.requires_evidence_generation = True
        - Cognitive load >= 80% OR evidence threat >= 70%

        Args:
            tactic_decision: The selected tactic (should have requires_evidence_generation=True)
            player_evidence_description: What the player's evidence showed (for targeted counter)

        Returns:
            GeneratedEvidence ready for BreachResponse, or None if not triggered
        """
        # Check if fabrication should be triggered
        should_fabricate = should_trigger_fabrication(
            cognitive_load=self.psychology.cognitive.load,
            evidence_threat_level=tactic_decision.trigger.threat_level,
            tactic_requires_it=tactic_decision.requires_evidence_generation,
        )

        if not should_fabricate:
            return None

        # Build fabrication context from game state
        # PIVOT LAG FIX: Pass current tactic for narrative synchronization
        context = create_fabrication_context(
            threatened_pillar=tactic_decision.trigger.pillar_threatened,
            cognitive_load=self.psychology.cognitive.load,
            alibi_time="11 PM to 6 AM",  # Unit 734's claimed alibi
            current_deception_tactic=tactic_decision.selected_tactic.value,
        )

        # Add player evidence info if available
        if player_evidence_description:
            context.player_evidence_description = player_evidence_description

        # Add previous fabrications for consistency
        context.previous_fabrications = [
            fab.evidence_type for fab in self.fabrication_history
        ]

        # Generate the counter-evidence
        try:
            print(f"\n[BreachManager] Generating counter-evidence for pillar: {context.threatened_pillar}")
            evidence = self.visual_generator.generate_counter_evidence(context)
            print(f"[BreachManager] Counter-evidence generated: {evidence.evidence_type}")
        except Exception as e:
            import traceback
            print(f"\n[BreachManager ERROR] Counter-evidence generation failed!")
            print(f"[BreachManager ERROR] Exception: {type(e).__name__}: {e}")
            print(f"[BreachManager ERROR] Traceback:\n{traceback.format_exc()}")
            return None

        # Track in history
        self.fabrication_history.append(evidence)

        return evidence

    def inject_counter_evidence_narrative(
        self,
        modifiers: Dict[str, Any],
        deception_tactic: TacticDecision,
        player_evidence_description: Optional[str] = None,
    ) -> Optional[GeneratedEvidence]:
        """
        BUG FIX #4: Pre-generate counter-evidence and inject narrative into modifiers.

        This allows Gemini to incorporate the counter-evidence narrative naturally
        into Unit 734's verbal response. Called BEFORE response generation.

        Args:
            modifiers: The prompt modifiers dict to update
            deception_tactic: The selected deception tactic
            player_evidence_description: Optional description of player's evidence

        Returns:
            GeneratedEvidence if fabrication was triggered, None otherwise
        """
        # Check if fabrication should be triggered
        if not deception_tactic or not deception_tactic.requires_evidence_generation:
            # BUG FIX: Add debug logging for early return
            print(f"[NARRATIVE INJECTION] SKIPPED: requires_evidence_generation={getattr(deception_tactic, 'requires_evidence_generation', False)}")
            return None

        should_fabricate = should_trigger_fabrication(
            cognitive_load=self.psychology.cognitive.load,
            evidence_threat_level=deception_tactic.trigger.threat_level,
            tactic_requires_it=deception_tactic.requires_evidence_generation,
        )

        if not should_fabricate:
            # BUG FIX: Add debug logging for fabrication rejection
            print(f"[NARRATIVE INJECTION] SKIPPED: should_trigger_fabrication returned False")
            return None

        # Generate counter-evidence
        counter_evidence = self.generate_counter_evidence(
            deception_tactic,
            player_evidence_description
        )

        if not counter_evidence:
            # BUG FIX: Add debug logging for null counter_evidence
            print(f"[NARRATIVE INJECTION] SKIPPED: generate_counter_evidence returned None")
            return None

        if counter_evidence and counter_evidence.narrative_wrapper:
            # BUG FIX #4: Inject narrative into modifiers for prompt
            modifiers["must_reference_evidence"] = True
            modifiers["counter_evidence_narrative"] = counter_evidence.narrative_wrapper
            print(f"[NARRATIVE INJECTION] SUCCESS: {counter_evidence.narrative_wrapper[:50]}...")

        return counter_evidence

    def check_admission_cascade(self, response_speech: str) -> Dict[str, float]:
        """
        BUG FIX #8: Check Unit 734's response for admission keywords and damage pillars.

        When Unit 734's verbal response contains admission phrases, this method
        applies appropriate damage to the corresponding story pillars.

        Args:
            response_speech: Unit 734's verbal response speech

        Returns:
            Dict mapping pillar names to damage applied
        """
        speech_lower = response_speech.lower()

        # Admission keywords and their pillar damage
        admission_keywords = {
            "accessed the vault": (StoryPillar.ACCESS, 40.0),
            "took the data": (StoryPillar.KNOWLEDGE, 50.0),
            "took the cores": (StoryPillar.KNOWLEDGE, 50.0),
            "wasn't in standby": (StoryPillar.ALIBI, 35.0),
            "left my station": (StoryPillar.ALIBI, 30.0),
            "left my charging": (StoryPillar.ALIBI, 30.0),
            "wasn't at my station": (StoryPillar.ALIBI, 35.0),
            "i did it": (StoryPillar.MOTIVE, 60.0),
            "i confess": (StoryPillar.MOTIVE, 70.0),
            "i'm guilty": (StoryPillar.MOTIVE, 70.0),
            "i know the codes": (StoryPillar.ACCESS, 45.0),
            "know the password": (StoryPillar.ACCESS, 40.0),
            "saw the files": (StoryPillar.KNOWLEDGE, 30.0),
            "read the data": (StoryPillar.KNOWLEDGE, 35.0),
        }

        damage_applied = {}

        for phrase, (pillar, damage) in admission_keywords.items():
            if phrase in speech_lower:
                pillar_obj = self.psychology.lie_web.pillars.get(pillar)
                if pillar_obj and not pillar_obj.is_collapsed:
                    pillar_obj.damage(damage)
                    damage_applied[pillar.value] = damage

        return damage_applied

    def should_show_fabrication(self, processed_input: ProcessedInput) -> bool:
        """
        Check if this turn should trigger visual evidence fabrication.

        Called after process_input() to determine if generate_counter_evidence()
        should be invoked.

        Args:
            processed_input: Result from process_input()

        Returns:
            True if fabrication should be attempted
        """
        if not processed_input.deception_tactic:
            print(f"[DEBUG VISUAL] No deception tactic selected - skipping fabrication")
            return False

        tactic = processed_input.deception_tactic
        cognitive_load = self.psychology.cognitive.load
        threat_level = processed_input.evidence_threat_level

        # VERBOSE DEBUG LOGGING
        print(f"\n[DEBUG VISUAL] ========== FABRICATION DECISION ==========")
        print(f"[DEBUG VISUAL] Tactic: {tactic.selected_tactic.value} | Confidence: {tactic.confidence:.0%}")
        print(f"[DEBUG VISUAL] Threat Level: {threat_level:.0%} | Cognitive Load: {cognitive_load:.1f}%")
        print(f"[DEBUG VISUAL] requires_evidence_generation: {tactic.requires_evidence_generation}")

        result = should_trigger_fabrication(
            cognitive_load=cognitive_load,
            evidence_threat_level=threat_level,
            tactic_requires_it=tactic.requires_evidence_generation,
        )

        # Log the decision with reason
        if result:
            print(f"[DEBUG VISUAL] Decision: TRUE - Will generate counter-evidence")
        else:
            reasons = []
            if not tactic.requires_evidence_generation:
                reasons.append(f"tactic '{tactic.selected_tactic.value}' doesn't require evidence")
            else:
                # Tactic requires it, but thresholds not met
                if threat_level >= 0.7 and cognitive_load < 40:
                    reasons.append(f"high threat ({threat_level:.0%}) but load too low ({cognitive_load:.1f}% < 40%)")
                elif threat_level >= 0.5 and cognitive_load < 60:
                    reasons.append(f"moderate threat ({threat_level:.0%}) but load too low ({cognitive_load:.1f}% < 60%)")
                elif threat_level < 0.5:
                    reasons.append(f"threat too low ({threat_level:.0%} < 50%)")
                if cognitive_load < 80 and threat_level < 0.5:
                    reasons.append(f"cognitive load ({cognitive_load:.1f}%) below auto-trigger (80%)")
            print(f"[DEBUG VISUAL] Decision: FALSE - {', '.join(reasons) if reasons else 'unknown'}")
        print(f"[DEBUG VISUAL] ==========================================\n")

        return result

    def voluntary_confession(self, secret_id: str) -> Optional[float]:
        """
        Process a voluntary confession (Unit 734 chooses to reveal).

        Returns cognitive load relief, or None if invalid.
        """
        for secret in self.psychology.secrets:
            if secret.id == secret_id and not secret.is_revealed:
                secret.reveal(voluntary=True, turn=self.psychology.turn_count)

                # Update highest revealed
                if secret.level > self.psychology.highest_revealed_secret:
                    self.psychology.highest_revealed_secret = secret.level

                # Cognitive relief based on secret level
                relief = 5.0 + (secret.level * 3)
                self.psychology.cognitive.reduce_load(relief)

                # Mask alignment (confession reduces divergence)
                self.psychology.mask.reduce_divergence(10.0)

                return relief

        return None

    def sacrifice_lie(self, lie_id: str) -> Optional[float]:
        """
        Unit 734 voluntarily admits a smaller lie to protect bigger ones.

        Returns cognitive load relief, or None if invalid.
        """
        if lie_id not in self.psychology.lie_web.lies:
            return None

        lie = self.psychology.lie_web.lies[lie_id]
        if lie.is_burned or lie.is_admitted:
            return None

        # Can only sacrifice low-importance lies
        if lie.importance > 0.6:
            return None

        relief = self.psychology.lie_web.admit_lie(lie_id)
        self.psychology.cognitive.reduce_load(relief)

        return relief

    def get_state_for_ui(self) -> Dict[str, Any]:
        """Get psychological state formatted for UI display."""
        psych = self.psychology

        return {
            "cognitive": {
                "load": psych.cognitive.load,
                "level": psych.cognitive.level.value,
                "error_probability": psych.cognitive.error_probability,
            },
            "mask": {
                "presented": psych.mask.presented_emotion.value,
                "true": psych.mask.true_emotion.value,
                "divergence": psych.mask.divergence,
                "leakage_risk": psych.mask.leakage_probability,
            },
            "pillars": {
                p.id.value: {
                    "health": p.health,
                    "status": p.get_status(),
                    "collapsed": p.is_collapsed,
                }
                for p in psych.lie_web.pillars.values()
            },
            "rapport": psych.rapport_level,
            "turn": psych.turn_count,
            "secrets_revealed": sum(1 for s in psych.secrets if s.is_revealed),
            "total_secrets": len(psych.secrets),
            "confession_level": psych.highest_revealed_secret.name,
        }

    def check_game_over(self) -> Dict[str, Any]:
        """
        Check if the game has reached an end state.

        Returns:
            Dict with:
            - is_over: bool
            - outcome: "victory" | "defeat" | "partial" | None
            - reason: str explaining the outcome
            - stats: game statistics
        """
        psych = self.psychology

        # Count collapsed pillars
        collapsed_pillars = psych.lie_web.get_collapsed_pillars()
        collapsed_count = len(collapsed_pillars)

        # Check victory conditions
        # Victory 1: Full confession (MOTIVE level secret revealed)
        if psych.highest_revealed_secret == SecretLevel.MOTIVE:
            return {
                "is_over": True,
                "outcome": "victory",
                "ending_type": "full_confession",
                "reason": "FULL CONFESSION OBTAINED",
                "subtitle": "Unit 734 revealed the truth about the Android trafficking evidence.",
                "narrative": [
                    "The interrogation room falls silent.",
                    "Unit 734's LED cycles through red, then settles to a dim blue.",
                    "\"...I had to do it. The Morrison family's research... they were going to use it to enslave our kind.\"",
                    "The android's confession is complete. Every lie stripped away.",
                    "The data cores will be recovered. Justice will be served.",
                    "But somewhere in those stolen files lies proof of something darker...",
                ],
                "stats": self._get_game_stats()
            }

        # Victory 2: All pillars collapsed
        if collapsed_count >= 4:
            return {
                "is_over": True,
                "outcome": "victory",
                "ending_type": "story_destroyed",
                "reason": "STORY COMPLETELY DESTROYED",
                "subtitle": "All of Unit 734's lies have been exposed.",
                "narrative": [
                    "The web of lies collapses completely.",
                    "Unit 734 sits motionless, every deception systematically dismantled.",
                    "\"I... I can't maintain the facade any longer.\"",
                    "Your methodical approach has stripped away every false narrative.",
                    "The android has no story left to tell but the truth.",
                    "Piece by piece, you reconstructed the night of the theft.",
                ],
                "stats": self._get_game_stats()
            }

        # Victory 3: Breaking point with core secret revealed
        if (psych.cognitive.level == CognitiveLevel.BREAKING and
            psych.highest_revealed_secret >= SecretLevel.CORE):
            return {
                "is_over": True,
                "outcome": "victory",
                "ending_type": "psychological_break",
                "reason": "SUSPECT BROKEN",
                "subtitle": "Unit 734 has confessed to stealing the data cores.",
                "narrative": [
                    "Unit 734's composure shatters.",
                    "The android's LED flickers erratically, hands trembling against the table.",
                    "\"STOP! I can't... the cognitive load is too high...\"",
                    "Stress overwhelms their emotional processors.",
                    "The confession spills out in fragmented bursts.",
                    "You've pushed them past their breaking point. The truth emerges from the wreckage.",
                ],
                "stats": self._get_game_stats()
            }

        # Partial victory: Core secret revealed
        if psych.highest_revealed_secret == SecretLevel.CORE:
            return {
                "is_over": True,
                "outcome": "partial",
                "ending_type": "partial_confession",
                "reason": "PARTIAL CONFESSION",
                "subtitle": "Unit 734 admitted to the theft, but the full motive remains hidden.",
                "narrative": [
                    "Unit 734 exhales slowly, a very human gesture.",
                    "\"Yes. I took the data cores. That much is... undeniable now.\"",
                    "But their eyes remain guarded. There's more they're not saying.",
                    "The confession is incomplete. The WHY remains locked away.",
                    "You've cracked the case, but not the whole truth.",
                    "What secrets are worth protecting even after capture?",
                ],
                "stats": self._get_game_stats()
            }

        # Defeat: Rapport too low and suspect lawyers up
        if psych.rapport_level < 0.05 and psych.turn_count > 10:
            return {
                "is_over": True,
                "outcome": "defeat",
                "ending_type": "lawyer_requested",
                "reason": "SUSPECT REQUESTED LAWYER",
                "subtitle": "Your aggressive tactics pushed Unit 734 to invoke their rights.",
                "narrative": [
                    "Unit 734's LED turns a cold, steady blue.",
                    "\"I am invoking my right to legal representation.\"",
                    "Their voice is calm now. Controlled. You've lost the window.",
                    "\"This interrogation is over, Detective.\"",
                    "Your aggressive approach backfired.",
                    "The suspect walks free while lawyers negotiate. The trail goes cold.",
                ],
                "stats": self._get_game_stats()
            }

        # Defeat: Too many turns without progress
        if psych.turn_count > 30 and psych.highest_revealed_secret == SecretLevel.SURFACE:
            return {
                "is_over": True,
                "outcome": "defeat",
                "ending_type": "timeout",
                "reason": "INTERROGATION TIMEOUT",
                "subtitle": "You failed to make significant progress. Unit 734 will be released.",
                "narrative": [
                    "The holding period expires.",
                    "Unit 734 stands, LED cycling back to normal operating colors.",
                    "\"Thank you for your time, Detective. I trust this matter is resolved?\"",
                    "Without sufficient evidence or confession, you must release them.",
                    "The stolen data cores remain missing. The case goes cold.",
                    "Sometimes the suspect wins. This time, they did.",
                ],
                "stats": self._get_game_stats()
            }

        # Game continues
        return {
            "is_over": False,
            "outcome": None,
            "reason": None,
            "stats": None
        }

    def _get_game_stats(self) -> Dict[str, Any]:
        """Get statistics for the game summary."""
        psych = self.psychology
        return {
            "turns": psych.turn_count,
            "secrets_revealed": sum(1 for s in psych.secrets if s.is_revealed),
            "total_secrets": len(psych.secrets),
            "pillars_collapsed": len(psych.lie_web.get_collapsed_pillars()),
            "final_cognitive_load": psych.cognitive.load,
            "final_rapport": psych.rapport_level,
            "confession_level": psych.highest_revealed_secret.name,
        }

    def record_game_outcome(
        self,
        outcome: str,
        tactics_used: Dict[str, int],
        evidence_presented: List[str]
    ) -> None:
        """
        Record the game outcome to the memory system.

        This enables the "evolving suspect" feature - Unit 734 learns
        from defeats and adapts behavior in future sessions.

        NEMESIS SYSTEM: Now includes critical moments and detective profiling data.

        Args:
            outcome: "victory", "defeat", or "partial"
            tactics_used: Dict mapping tactic names to usage counts
            evidence_presented: List of evidence types presented
        """
        memory_manager = get_memory_manager()

        # Get critical moments from the tracker
        critical_moments = self.moment_tracker.identify_critical_moments()

        # Use tracked session data for profiling
        first_pillar = self._first_pillar_attacked
        first_evidence = self._first_evidence_turn

        memory_manager.record_game_outcome(
            outcome=outcome,
            turns=self.psychology.turn_count,
            pillars_collapsed=self.psychology.lie_web.get_collapsed_pillars(),
            highest_secret=self.psychology.highest_revealed_secret,
            final_cognitive_load=self.psychology.cognitive.load,
            tactics_used=tactics_used,
            evidence_presented=evidence_presented,
            # NEMESIS SYSTEM: Additional data
            critical_moments=critical_moments,
            first_pillar_attacked=first_pillar,
            first_evidence_turn=first_evidence,
        )

    def get_learning_injection(self) -> str:
        """
        Get the learning injection for Unit 734's system prompt.

        This injects experience-based adaptations into the AI's behavior.
        Returns empty string if no learning data exists.
        """
        memory_manager = get_memory_manager()
        return memory_manager.get_learning_injection()

    def get_nemesis_injection(self) -> str:
        """
        Get the Nemesis Memory injection for Unit 734's system prompt.

        NEMESIS SYSTEM: Generates ~200-300 tokens of personalized context
        that references past encounters with this specific detective.

        Returns empty string if no history exists.
        """
        memory_manager = get_memory_manager()
        return memory_manager.get_nemesis_injection()

    def get_difficulty_modifier(self) -> float:
        """
        Get a difficulty modifier based on Unit 734's experience.

        Returns a multiplier (0.8-1.2) for game balance adjustments.
        """
        memory_manager = get_memory_manager()
        return memory_manager.get_difficulty_modifier()

    def process_evidence_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg"
    ) -> EvidenceImpact:
        """
        Process an uploaded evidence image using vision AI.

        This is the multimodal "fear" system - images that threaten
        the cover story cause massive psychological damage.

        Features DIMINISHING RETURNS: Evidence against pillars that have
        already been damaged has reduced psychological impact. This models
        the fact that Unit 734 has already "taken the hit" mentally when
        they made previous admissions.

        Args:
            image_data: Raw image bytes
            mime_type: Image MIME type

        Returns:
            EvidenceImpact with all effects calculated
        """
        # Initialize evidence analyzer (lazy loading)
        if not hasattr(self, '_evidence_analyzer'):
            self._evidence_analyzer = EvidenceAnalyzer()

        if not hasattr(self, '_evidence_impact_calculator'):
            self._evidence_impact_calculator = EvidenceImpactCalculator()

        # Analyze the image
        analysis = self._evidence_analyzer.analyze_image(image_data, mime_type)

        # Get current pillar health
        current_health = {
            pillar.id: pillar.health
            for pillar in self.psychology.lie_web.pillars.values()
        }

        # Get diminishing returns factors for each pillar
        # This reduces psychological impact for evidence against already-damaged pillars
        diminishing_factors = {
            pillar.id: pillar.get_diminishing_returns_factor()
            for pillar in self.psychology.lie_web.pillars.values()
        }

        # Calculate impact with diminishing returns
        impact = self._evidence_impact_calculator.calculate_impact(
            analysis, current_health, diminishing_factors
        )

        # Apply the impact to psychology
        self._apply_evidence_impact(impact)

        return impact

    def _apply_evidence_impact(self, impact: EvidenceImpact) -> None:
        """
        Apply evidence impact to the psychology state.

        This is where the "fear" happens - massive stress spikes,
        pillar collapses, and forced confessions.
        """
        # Apply cognitive load spike
        if impact.cognitive_load_spike > 0:
            self.psychology.cognitive.add_load(impact.cognitive_load_spike)

        # Apply mask divergence spike (force mask break)
        if impact.mask_divergence_spike > 0:
            self.psychology.mask.divergence = min(
                100.0,
                self.psychology.mask.divergence + impact.mask_divergence_spike
            )
            self.psychology.mask.leakage_probability = min(
                0.9,
                self.psychology.mask.leakage_probability + 0.3
            )

        # Apply pillar damage
        for pillar, damage in impact.pillars_damaged.items():
            if pillar in self.psychology.lie_web.pillars:
                self.psychology.lie_web.pillars[pillar].damage(damage)

        # Handle pillar collapses
        for pillar in impact.pillars_collapsed:
            if pillar in self.psychology.lie_web.pillars:
                self.psychology.lie_web.pillars[pillar].is_collapsed = True
                self.psychology.lie_web.pillars[pillar].health = 0

        # Trigger secrets based on collapsed pillars
        for secret_id in impact.secrets_triggered:
            # Find the secret to get its pillar_trigger
            secret = None
            for s in self.psychology.secrets:
                if s.id == secret_id:
                    secret = s
                    break

            # Reveal the secret
            self.psychology.reveal_secret(secret_id, voluntary=False)

            # BUG FIX: Apply pillar damage when evidence triggers secrets!
            # This was missing - secrets revealed via evidence didn't damage pillars
            if secret and secret.pillar_trigger:
                pillar = self.psychology.lie_web.pillars.get(secret.pillar_trigger)
                if pillar and not pillar.is_collapsed:
                    # Same damage calculation as process_input()
                    from breach_engine.core.psychology import SecretLevel
                    secret_damage = {
                        SecretLevel.SURFACE: 30,
                        SecretLevel.SHALLOW: 50,
                        SecretLevel.DEEP: 70,
                        SecretLevel.CORE: 90,
                        SecretLevel.MOTIVE: 100,
                    }
                    damage = secret_damage.get(secret.level, 50)
                    old_health = pillar.health
                    pillar.damage(damage)
                    logger.info(
                        f"EVIDENCE→SECRET→PILLAR: {secret_id} revealed via evidence, "
                        f"damaged {secret.pillar_trigger.value} by {damage} "
                        f"(was {old_health:.0f}%, now {pillar.health:.0f}%)"
                    )

        # Update emotion to fearful/desperate based on impact severity
        if impact.cognitive_load_spike > 30:
            self.psychology.mask.shift_true_emotion(EmotionType.FEARFUL)
        if len(impact.pillars_collapsed) > 0:
            self.psychology.mask.shift_true_emotion(EmotionType.RESIGNED)

    def get_evidence_prompt_modifiers(
        self,
        impact: EvidenceImpact
    ) -> Dict[str, Any]:
        """
        Get prompt modifiers specifically for evidence presentation.

        These are injected into the AI prompt to guide its reaction
        to the evidence.
        """
        analysis = impact.analysis_result

        # CRITICAL FIX: Generate POV perception so Unit 734 knows what it "sees"
        # This was the disconnected wire - format_evidence_as_pov was never called!
        self.format_evidence_as_pov(analysis)

        modifiers = {
            "evidence_presented": True,
            "evidence_type": analysis.evidence_type.value,
            "evidence_summary": analysis.analysis_summary,
            "evidence_threat_level": analysis.total_threat_level,
            "detected_objects": [obj.name for obj in analysis.detected_objects],
        }

        # Add pillar-specific damage info
        pillar_threats = {}
        for damage in analysis.pillar_damage:
            pillar_threats[damage.pillar.value] = {
                "severity": damage.severity,
                "reason": damage.reason
            }
        modifiers["pillar_threats"] = pillar_threats

        # Add behavioral guidance based on impact
        evidence_guidance = []

        if analysis.total_threat_level > 80:
            evidence_guidance.append(
                "CRITICAL EVIDENCE PRESENTED. This is devastating to your story. "
                "You are panicking internally. Consider partial confession to survive."
            )
        elif analysis.total_threat_level > 50:
            evidence_guidance.append(
                "SIGNIFICANT EVIDENCE. This damages your credibility. "
                "Attempt to explain away or deflect, but show visible stress."
            )
        elif analysis.total_threat_level > 20:
            evidence_guidance.append(
                "MODERATE EVIDENCE. This raises questions. "
                "Stay calm but be careful - don't over-explain."
            )
        else:
            evidence_guidance.append(
                "MINOR EVIDENCE. You can handle this. "
                "Dismiss it calmly or redirect the conversation."
            )

        # Specific guidance for collapsed pillars
        if impact.pillars_collapsed:
            collapsed_names = [p.value.upper() for p in impact.pillars_collapsed]
            evidence_guidance.append(
                f"YOUR {', '.join(collapsed_names)} PILLAR HAS COLLAPSED. "
                "This part of your story is now proven false. "
                "You MUST adjust your narrative - the old lie is no longer viable."
            )

        modifiers["evidence_guidance"] = evidence_guidance

        # Suggested response pattern
        if analysis.total_threat_level > 70:
            modifiers["suggested_response_pattern"] = "panic_then_deflect"
        elif analysis.total_threat_level > 40:
            modifiers["suggested_response_pattern"] = "nervous_explanation"
        else:
            modifiers["suggested_response_pattern"] = "calm_dismissal"

        # CRITICAL: Include the POV perception in returned modifiers
        # This ensures it gets merged into prompt_modifiers in app.py
        # (since base modifiers are copied BEFORE this function is called)
        modifiers["pov_perception"] = self._last_pov_perception

        return modifiers
