"""
Breach Psychology System - Core Models

The psychological state of Unit 734, built on three pillars:
1. LIE WEB: Structure of interconnected deceptions
2. COGNITIVE LOAD: Mental strain of maintaining lies
3. MASK vs SELF: Divergence between presented and true emotions

This creates emergent drama through mechanical interactions,
not scripted responses.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from enum import Enum, IntEnum
from datetime import datetime
from pydantic import BaseModel, Field
import random


# =============================================================================
# ENUMS
# =============================================================================

class StoryPillar(str, Enum):
    """The four pillars of Unit 734's cover story."""
    ALIBI = "alibi"          # "I was in standby mode"
    MOTIVE = "motive"        # "I had no reason to steal"
    ACCESS = "access"        # "I couldn't access the vault"
    KNOWLEDGE = "knowledge"  # "I don't know what data cores contain"


class CognitiveLevel(str, Enum):
    """Mental state thresholds based on cognitive load."""
    CONTROLLED = "controlled"   # 0-30: Poker face, clean responses
    STRAINED = "strained"       # 31-60: Cracks showing, occasional hesitation
    CRACKING = "cracking"       # 61-80: Visible stress, may contradict
    DESPERATE = "desperate"     # 81-95: Erratic behavior, hostile or pleading
    BREAKING = "breaking"       # 96-100: Confession imminent


class PlayerTactic(str, Enum):
    """Detected interrogation tactics from player input."""
    PRESSURE = "pressure"       # Aggressive, accusatory, threatening
    EMPATHY = "empathy"         # Understanding, building rapport
    LOGIC = "logic"             # Pointing out inconsistencies
    BLUFF = "bluff"             # Claiming evidence they don't have
    EVIDENCE = "evidence"       # Presenting actual proof
    SILENCE = "silence"         # Strategic pauses, letting them stew


class EmotionType(str, Enum):
    """Emotional states for Mask vs Self system."""
    CALM = "calm"
    NERVOUS = "nervous"
    FEARFUL = "fearful"
    ANGRY = "angry"
    GUILTY = "guilty"
    DEFIANT = "defiant"
    RESIGNED = "resigned"
    HOPEFUL = "hopeful"


class SecretLevel(IntEnum):
    """Layered secrets from surface to core truth."""
    SURFACE = 1    # "I was awake during the night"
    SHALLOW = 2    # "I left my charging station"
    DEEP = 3       # "I accessed the vault"
    CORE = 4       # "I took the data cores"
    MOTIVE = 5     # "I found evidence of Android trafficking"


# =============================================================================
# LIE WEB SYSTEM
# =============================================================================

class LieNode(BaseModel):
    """A single lie in the deception web."""
    id: str = Field(description="Unique identifier for this lie")
    content: str = Field(description="The actual lie statement")
    pillar: StoryPillar = Field(description="Which story pillar this supports")
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How critical: 0.3=leaf, 0.5=supporting, 1.0=core"
    )

    # State
    is_burned: bool = Field(default=False, description="Proven false by evidence")
    is_admitted: bool = Field(default=False, description="Voluntarily confessed")

    # Dependencies
    dependent_on: List[str] = Field(
        default_factory=list,
        description="Other lie IDs this depends on (if parent burns, this weakens)"
    )
    burns_if_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence IDs that would prove this false"
    )

    # Usage tracking
    times_referenced: int = Field(default=0, description="How often mentioned")
    last_referenced_turn: int = Field(default=-1)

    def burn(self) -> None:
        """Mark this lie as exposed."""
        self.is_burned = True

    def admit(self) -> None:
        """Mark this lie as voluntarily confessed."""
        self.is_admitted = True
        self.is_burned = True  # Admitted lies are also "burned"

    def reference(self, turn: int) -> None:
        """Track that this lie was referenced."""
        self.times_referenced += 1
        self.last_referenced_turn = turn


class LiePillar(BaseModel):
    """A core pillar of the cover story."""
    id: StoryPillar = Field(description="Pillar identifier")
    name: str = Field(description="Human-readable name")
    core_claim: str = Field(description="The central claim of this pillar")

    # Health system
    health: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Pillar health, collapses at threshold"
    )
    collapse_threshold: float = Field(
        default=25.0,
        description="Below this = pillar collapsed"
    )
    is_collapsed: bool = Field(default=False)

    # Weakness acknowledgment tracking
    # When Unit 734 makes partial admissions (via damage), this pillar becomes "pre-damaged"
    # Future evidence against this pillar has diminishing psychological impact
    weakness_acknowledged: bool = Field(
        default=False,
        description="True if Unit 734 has already taken damage to this pillar"
    )
    times_damaged: int = Field(
        default=0,
        description="Number of times this pillar has been damaged"
    )

    # Attached lies
    attached_lies: List[str] = Field(
        default_factory=list,
        description="LieNode IDs that support this pillar"
    )

    def damage(self, amount: float) -> bool:
        """
        Apply damage to pillar.

        Returns True if pillar collapsed from this damage.
        """
        if self.is_collapsed:
            return False

        self.health = max(0.0, self.health - amount)
        self.times_damaged += 1

        # Mark weakness as acknowledged once pillar takes significant damage
        if self.health < 75.0:
            self.weakness_acknowledged = True

        if self.health <= self.collapse_threshold:
            self.is_collapsed = True
            return True

        return False

    def apply_verbal_pressure(self, amount: float) -> bool:
        """
        Apply verbal pressure damage WITHOUT diminishing returns.

        Verbal pressure should remain consistently damaging throughout
        interrogation, unlike evidence which has diminishing impact.

        Args:
            amount: Damage to apply (positive value)

        Returns:
            True if pillar collapsed from this damage, False otherwise.
        """
        if self.is_collapsed:
            return False

        # Direct health reduction, bypassing diminishing returns
        self.health = max(0.0, self.health - amount)
        self.times_damaged += 1

        if self.health < 75.0:
            self.weakness_acknowledged = True

        if self.health <= self.collapse_threshold:
            self.is_collapsed = True
            return True

        return False

    def get_diminishing_returns_factor(self) -> float:
        """
        Get the diminishing returns factor for psychological impact.

        Returns a multiplier (0.3-1.0) that reduces psychological impact
        when the pillar has already been damaged (acknowledged weakness).
        """
        if self.is_collapsed:
            return 0.2  # Collapsed pillars = minimal additional psych impact

        if not self.weakness_acknowledged:
            return 1.0  # Full impact for fresh pillars

        # Diminishing returns based on how many times damaged
        # First hit = 1.0, second = 0.6, third+ = 0.3
        if self.times_damaged == 1:
            return 0.6
        else:
            return 0.3

    def get_status(self) -> str:
        """Get human-readable status."""
        if self.is_collapsed:
            return "COLLAPSED"
        elif self.health > 75:
            return "STRONG"
        elif self.health > 50:
            return "WEAKENED"
        elif self.health > self.collapse_threshold:
            return "CRITICAL"
        else:
            return "COLLAPSED"


class LieWeb(BaseModel):
    """The complete structure of Unit 734's deception."""
    pillars: Dict[StoryPillar, LiePillar] = Field(default_factory=dict)
    lies: Dict[str, LieNode] = Field(default_factory=dict)

    # Statistics
    total_lies_told: int = Field(default=0)
    lies_burned: int = Field(default=0)
    lies_admitted: int = Field(default=0)

    def add_lie(self, lie: LieNode) -> None:
        """Add a lie to the web."""
        self.lies[lie.id] = lie
        self.total_lies_told += 1

        # Attach to pillar
        if lie.pillar in self.pillars:
            if lie.id not in self.pillars[lie.pillar].attached_lies:
                self.pillars[lie.pillar].attached_lies.append(lie.id)

    def burn_lie(self, lie_id: str) -> Tuple[List[str], bool]:
        """
        Burn a lie and return list of dependent lies that are now vulnerable.

        Returns:
            Tuple of (vulnerable_lie_ids, pillar_collapsed_this_burn)
        """
        if lie_id not in self.lies:
            return [], False

        lie = self.lies[lie_id]
        if lie.is_burned:
            return [], False

        lie.burn()
        self.lies_burned += 1

        # Damage the pillar
        pillar_collapsed = False
        pillar = self.pillars.get(lie.pillar)
        if pillar:
            damage = lie.importance * 25  # Max 25 damage per lie
            pillar_collapsed = pillar.damage(damage)

        # Find dependent lies
        vulnerable = []
        for other_id, other_lie in self.lies.items():
            if lie_id in other_lie.dependent_on and not other_lie.is_burned:
                vulnerable.append(other_id)

        return vulnerable, pillar_collapsed

    def admit_lie(self, lie_id: str) -> float:
        """
        Voluntarily admit a lie. Returns cognitive load relief.
        """
        if lie_id not in self.lies:
            return 0.0

        lie = self.lies[lie_id]
        if lie.is_admitted:
            return 0.0

        lie.admit()
        self.lies_admitted += 1

        # Less pillar damage for voluntary admission
        pillar = self.pillars.get(lie.pillar)
        if pillar:
            damage = lie.importance * 15  # Less than being caught
            pillar.damage(damage)

        # Return cognitive relief (higher for more important lies)
        return 5.0 + (lie.importance * 10)

    def get_pillar_health_summary(self) -> Dict[str, float]:
        """Get health of all pillars."""
        # BUG FIX: Guard against None pillars dict
        if self.pillars is None:
            return {}
        return {p.id.value: p.health for p in self.pillars.values()}

    def get_collapsed_pillars(self) -> List[StoryPillar]:
        """Get list of collapsed pillars."""
        return [p.id for p in self.pillars.values() if p.is_collapsed]

    def get_vulnerable_lies(self) -> List[LieNode]:
        """Get lies that are most vulnerable (low importance, referenced often)."""
        active_lies = [l for l in self.lies.values() if not l.is_burned]
        # Sort by vulnerability (low importance + high references = sacrificial)
        return sorted(active_lies, key=lambda l: l.importance - (l.times_referenced * 0.1))


# =============================================================================
# COGNITIVE LOAD SYSTEM
# =============================================================================

class CognitiveState(BaseModel):
    """Tracks the mental strain of maintaining deception."""
    load: float = Field(
        default=15.0,
        ge=0.0,
        le=100.0,
        description="Current cognitive load (0-100)"
    )
    level: CognitiveLevel = Field(
        default=CognitiveLevel.CONTROLLED,
        description="Current cognitive state level"
    )

    # Contributing factors
    active_lie_count: int = Field(default=0, description="Number of active lies")
    question_timestamps: List[float] = Field(
        default_factory=list,
        description="Timestamps of recent questions for rapid-fire detection"
    )
    evidence_pressure: float = Field(
        default=0.0,
        description="Accumulated pressure from presented evidence"
    )

    # BUG FIX #5: Stress floor system - prevents decay after pillar collapse
    stress_floor: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum stress level (set after pillar collapse)"
    )

    # Behavioral modifiers (calculated from load)
    error_probability: float = Field(
        default=0.0,
        description="Chance of accidental contradiction"
    )
    tell_intensity: float = Field(
        default=0.0,
        description="How visible the behavioral tells are"
    )
    response_coherence: float = Field(
        default=1.0,
        description="How organized/coherent responses are"
    )

    def add_load(self, amount: float, apply_decay: bool = False) -> CognitiveLevel:
        """
        Add cognitive load and return new level.

        BUG FIX #5: Removed automatic decay from this method.
        Decay should ONLY happen between interrogation sessions via apply_natural_decay().

        Args:
            amount: Load to add (can be negative for recovery)
            apply_decay: DEPRECATED - kept for API compatibility, ignored
        """
        # BUG FIX #5: NO automatic decay inside add_load()
        # This was causing stress to plateau at ~50%

        # Add the load
        self.load = min(100.0, max(0.0, self.load + amount))

        # BUG FIX #5: Enforce stress floor (set after pillar collapse)
        if self.stress_floor > 0:
            self.load = max(self.stress_floor, self.load)

        self._update_level()
        self._update_modifiers()
        return self.level

    def set_stress_floor(self, floor: float) -> None:
        """
        Set minimum stress floor (e.g., after pillar collapse).

        BUG FIX #5: Stress cannot decay below this floor until confession.
        This models the psychological impact of having a major lie exposed.

        Args:
            floor: Minimum stress level (0-100)
        """
        self.stress_floor = max(0.0, min(100.0, floor))

    def reduce_load(self, amount: float) -> None:
        """Reduce cognitive load (from confession, silence, etc.)."""
        self.load = max(0.0, self.load - amount)
        self._update_level()
        self._update_modifiers()

    def apply_natural_decay(self, amount: float = 2.0) -> float:
        """
        Apply natural stress decay (call ONLY between interrogation sessions).

        BUG FIX #5: Reduced decay rate and respects stress floor.
        This should NOT be called between turns during interrogation.

        Args:
            amount: Fixed amount to decay (default 2.0, reduced from dynamic rate)

        Returns:
            Amount actually decayed.
        """
        # Respect stress floor
        floor = max(20.0, self.stress_floor)

        if self.load <= floor:
            return 0.0

        # BUG FIX #5: Use flat decay rate instead of percentage
        # Old: decay_rate = 0.03 (3% decay) which was too aggressive
        # New: flat 2.0 points per session break
        old_load = self.load
        self.load = max(floor, self.load - amount)
        self._update_level()
        self._update_modifiers()
        return old_load - self.load

    def _update_level(self) -> None:
        """Update cognitive level based on load."""
        if self.load >= 96:
            self.level = CognitiveLevel.BREAKING
        elif self.load >= 81:
            self.level = CognitiveLevel.DESPERATE
        elif self.load >= 61:
            self.level = CognitiveLevel.CRACKING
        elif self.load >= 31:
            self.level = CognitiveLevel.STRAINED
        else:
            self.level = CognitiveLevel.CONTROLLED

    def _update_modifiers(self) -> None:
        """Update behavioral modifiers based on load."""
        # Error probability: 0% at load 0, ~30% at load 100
        self.error_probability = min(0.35, (self.load / 100) * 0.35)

        # Tell intensity: 0 at load 0, 1.0 at load 100
        self.tell_intensity = self.load / 100

        # Coherence: 1.0 at load 0, 0.4 at load 100
        self.response_coherence = 1.0 - (self.load / 100 * 0.6)

    def record_question(self, timestamp: float) -> int:
        """Record a question timestamp, return rapid-fire count."""
        # Keep only questions from last 60 seconds
        cutoff = timestamp - 60.0
        self.question_timestamps = [t for t in self.question_timestamps if t > cutoff]
        self.question_timestamps.append(timestamp)
        return len(self.question_timestamps)

    def is_rapid_fire(self, timestamp: float, threshold: float = 5.0) -> bool:
        """Check if questions are coming in rapid succession."""
        if not self.question_timestamps:
            return False
        last_question = self.question_timestamps[-1] if self.question_timestamps else 0
        return (timestamp - last_question) < threshold

    def should_make_error(self) -> bool:
        """Roll to see if Unit 734 makes an error."""
        return random.random() < self.error_probability


# =============================================================================
# MASK VS SELF SYSTEM
# =============================================================================

class MaskState(BaseModel):
    """The divergence between presented persona and true self."""
    # What Unit 734 shows the detective
    presented_emotion: EmotionType = Field(
        default=EmotionType.CALM,
        description="The emotion being displayed"
    )
    presented_cooperation: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="0=hostile, 1=fully cooperative"
    )

    # What Unit 734 actually feels
    true_emotion: EmotionType = Field(
        default=EmotionType.FEARFUL,
        description="The actual internal emotion"
    )
    true_guilt: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="How guilty they actually feel"
    )

    # Divergence tracking
    divergence: float = Field(
        default=30.0,
        ge=0.0,
        le=100.0,
        description="Gap between mask and self (0=aligned, 100=completely fake)"
    )
    mask_strain: float = Field(
        default=0.0,
        description="Accumulated strain on maintaining the mask"
    )

    # Leakage mechanics
    leakage_probability: float = Field(
        default=0.1,
        description="Chance of true emotion bleeding through"
    )
    last_leakage_turn: int = Field(
        default=-1,
        description="Prevent consecutive leakages"
    )

    def add_strain(self, amount: float) -> None:
        """Add strain to the mask."""
        self.mask_strain += amount
        self._update_divergence()

    def _update_divergence(self) -> None:
        """Update divergence based on strain."""
        # Divergence increases with strain, caps at 100
        self.divergence = min(100.0, 30.0 + self.mask_strain)

        # Update leakage probability
        self.leakage_probability = min(0.6, 0.1 + (self.divergence / 200))

    def reduce_divergence(self, amount: float) -> None:
        """Reduce divergence (mask and self aligning)."""
        self.divergence = max(0.0, self.divergence - amount)
        self.mask_strain = max(0.0, self.mask_strain - amount)

    def should_leak(self, current_turn: int) -> bool:
        """Check if true emotion should leak through."""
        # Prevent back-to-back leakages
        if current_turn <= self.last_leakage_turn + 1:
            return False

        if random.random() < self.leakage_probability:
            self.last_leakage_turn = current_turn
            return True
        return False

    def shift_true_emotion(self, new_emotion: EmotionType) -> None:
        """Shift the true internal emotion."""
        self.true_emotion = new_emotion
        # Shifting emotion increases divergence if mask doesn't match
        if new_emotion != self.presented_emotion:
            self.divergence = min(100.0, self.divergence + 5)

    def lower_mask(self, amount: float = 10.0) -> None:
        """Lower the mask (show more true self). Usually from empathy."""
        self.divergence = max(0.0, self.divergence - amount)
        # Move presented emotion closer to true
        if self.divergence < 30:
            self.presented_emotion = self.true_emotion


# =============================================================================
# VULNERABILITY & TACTICS
# =============================================================================

class VulnerabilityProfile(BaseModel):
    """Unit 734's specific weaknesses to different tactics."""
    # Effectiveness multipliers: >1.0 = vulnerable, <1.0 = resistant
    tactic_effectiveness: Dict[PlayerTactic, float] = Field(
        default_factory=lambda: {
            PlayerTactic.PRESSURE: 0.8,    # Resistant - android composure
            PlayerTactic.EMPATHY: 1.4,     # Vulnerable - unexpected kindness
            PlayerTactic.LOGIC: 1.2,       # Somewhat vulnerable - values consistency
            PlayerTactic.BLUFF: 0.6,       # Resistant - can often detect deception
            PlayerTactic.EVIDENCE: 1.5,    # Very vulnerable - can't argue facts
            PlayerTactic.SILENCE: 1.1,     # Slightly vulnerable - uncertainty
        }
    )

    # Dynamic modifiers
    desperation_multiplier: float = Field(
        default=1.0,
        description="Increases effectiveness of all tactics when desperate"
    )
    trust_modifier: float = Field(
        default=1.0,
        description="Modifies empathy effectiveness based on rapport"
    )

    def get_effectiveness(self, tactic: PlayerTactic, cognitive_level: CognitiveLevel) -> float:
        """Get tactic effectiveness considering current state."""
        base = self.tactic_effectiveness.get(tactic, 1.0)

        # Desperation makes everything more effective
        if cognitive_level in [CognitiveLevel.DESPERATE, CognitiveLevel.BREAKING]:
            base *= self.desperation_multiplier

        # Trust affects empathy
        if tactic == PlayerTactic.EMPATHY:
            base *= self.trust_modifier

        return base

    def update_from_bluff_detection(self, detected: bool) -> None:
        """Update after detecting (or missing) a bluff."""
        if detected:
            # Got better at detecting bluffs
            self.tactic_effectiveness[PlayerTactic.BLUFF] *= 0.9
        else:
            # Got worse (more susceptible)
            self.tactic_effectiveness[PlayerTactic.BLUFF] *= 1.1


# =============================================================================
# SECRETS SYSTEM
# =============================================================================

class Secret(BaseModel):
    """A piece of hidden truth that can be revealed."""
    id: str = Field(description="Unique identifier")
    level: SecretLevel = Field(description="How deep this secret is")
    content: str = Field(description="The actual secret")

    # Reveal conditions (any can trigger)
    cognitive_threshold: float = Field(
        default=80.0,
        description="Reveals if cognitive load exceeds this"
    )
    trust_threshold: float = Field(
        default=0.7,
        description="Reveals if rapport exceeds this"
    )
    pillar_trigger: Optional[StoryPillar] = Field(
        default=None,
        description="Reveals if this pillar collapses"
    )

    # State
    is_revealed: bool = Field(default=False)
    revealed_voluntarily: bool = Field(
        default=False,
        description="True if confessed, False if caught"
    )
    revealed_at_turn: Optional[int] = Field(default=None)

    def reveal(self, voluntary: bool, turn: int) -> None:
        """Reveal this secret."""
        self.is_revealed = True
        self.revealed_voluntarily = voluntary
        self.revealed_at_turn = turn

    def check_reveal_conditions(
        self,
        cognitive_load: float,
        rapport: float,
        collapsed_pillars: List[StoryPillar]
    ) -> bool:
        """
        Check if any reveal condition is met.

        BUG FIX #6: Removed the requirement for BOTH stress AND trust.
        Now supports three independent paths to revelation:
        1. HIGH STRESS alone (no trust needed) - forced confession
        2. EMPATHY path (trust + moderate stress) - voluntary confession
        3. PILLAR COLLAPSE - triggered by evidence
        """
        if self.is_revealed:
            return False

        # PATH 1: High stress FORCES confession (no trust needed)
        # BUG FIX #6: Added +10 buffer for stress-only reveals
        # This ensures very high stress can trigger secrets without trust
        if cognitive_load >= self.cognitive_threshold + 10:
            return True

        # PATH 2: Pillar collapse triggers associated secret
        # This is the most reliable path - evidence destroys a pillar
        if self.pillar_trigger and self.pillar_trigger in collapsed_pillars:
            return True

        # PATH 3: Standard path (stress + trust together)
        # Lower thresholds when BOTH conditions are partially met
        stress_met = cognitive_load >= self.cognitive_threshold
        trust_met = rapport >= self.trust_threshold

        # If both are met, reveal
        if stress_met and trust_met:
            return True

        # Partial both: 80% of stress threshold + 80% of trust threshold
        partial_stress = cognitive_load >= (self.cognitive_threshold * 0.8)
        partial_trust = rapport >= (self.trust_threshold * 0.8)
        if partial_stress and partial_trust:
            return True

        return False


# =============================================================================
# MAIN CONTAINER
# =============================================================================

class BreachPsychology(BaseModel):
    """Complete psychological state for Unit 734."""
    # Core systems
    lie_web: LieWeb = Field(default_factory=LieWeb)
    cognitive: CognitiveState = Field(default_factory=CognitiveState)
    mask: MaskState = Field(default_factory=MaskState)
    vulnerabilities: VulnerabilityProfile = Field(default_factory=VulnerabilityProfile)
    secrets: List[Secret] = Field(default_factory=list)

    # Session tracking
    turn_count: int = Field(default=0)
    rapport_level: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Trust/rapport with detective"
    )
    detected_bluffs: int = Field(default=0, description="Player bluffs caught")
    successful_bluffs: int = Field(default=0, description="Player bluffs that worked")

    # Confession tracking
    highest_revealed_secret: SecretLevel = Field(default=SecretLevel.SURFACE)
    is_fully_confessed: bool = Field(default=False)

    # BUG FIX #3: Secret reveal deduplication - prevent multiple reveals per turn
    secrets_revealed_this_turn: int = Field(default=0, description="Counter reset each turn")

    def increment_turn(self) -> None:
        """Increment turn counter."""
        self.turn_count += 1
        # BUG FIX #3: Reset secrets-per-turn counter
        self.secrets_revealed_this_turn = 0

    def adjust_rapport(self, delta: float) -> None:
        """Adjust rapport level."""
        self.rapport_level = max(0.0, min(1.0, self.rapport_level + delta))

    def get_next_revealable_secret(self) -> Optional[Secret]:
        """Get the next secret that could be revealed based on conditions."""
        collapsed = self.lie_web.get_collapsed_pillars()

        for secret in sorted(self.secrets, key=lambda s: s.level):
            if not secret.is_revealed:
                if secret.check_reveal_conditions(
                    self.cognitive.load,
                    self.rapport_level,
                    collapsed
                ):
                    return secret
        return None

    def reveal_secret(self, secret_id: str, voluntary: bool) -> Optional[Secret]:
        """Reveal a specific secret."""
        for secret in self.secrets:
            if secret.id == secret_id and not secret.is_revealed:
                # BUG FIX #3: Limit to one secret reveal per turn to prevent counting issues
                if self.secrets_revealed_this_turn >= 1:
                    return None
                self.secrets_revealed_this_turn += 1

                secret.reveal(voluntary, self.turn_count)
                if secret.level > self.highest_revealed_secret:
                    self.highest_revealed_secret = secret.level
                if secret.level == SecretLevel.MOTIVE:
                    self.is_fully_confessed = True
                return secret
        return None

    def get_state_summary(self) -> Dict:
        """Get a summary of current psychological state."""
        return {
            "turn": self.turn_count,
            "cognitive_load": self.cognitive.load,
            "cognitive_level": self.cognitive.level.value,
            "mask_divergence": self.mask.divergence,
            "presented_emotion": self.mask.presented_emotion.value,
            "true_emotion": self.mask.true_emotion.value,
            "rapport": self.rapport_level,
            "pillars": {
                p.id.value: {"health": p.health, "collapsed": p.is_collapsed}
                for p in self.lie_web.pillars.values()
            },
            "lies_burned": self.lie_web.lies_burned,
            "lies_admitted": self.lie_web.lies_admitted,
            "secrets_revealed": sum(1 for s in self.secrets if s.is_revealed),
            "highest_secret_level": self.highest_revealed_secret.name,
            "fully_confessed": self.is_fully_confessed,
        }


# =============================================================================
# FACTORY FUNCTION - Creates Unit 734's initial psychology
# =============================================================================

def create_unit_734_psychology() -> BreachPsychology:
    """Factory function to create Unit 734's complete psychology."""

    # Create pillars
    pillars = {
        StoryPillar.ALIBI: LiePillar(
            id=StoryPillar.ALIBI,
            name="The Alibi",
            core_claim="I was in standby mode from 11 PM to 6 AM",
            health=100.0
        ),
        StoryPillar.MOTIVE: LiePillar(
            id=StoryPillar.MOTIVE,
            name="The Motive",
            core_claim="I had no reason to steal from the Morrisons",
            health=100.0
        ),
        StoryPillar.ACCESS: LiePillar(
            id=StoryPillar.ACCESS,
            name="The Access",
            core_claim="I don't have access to the vault",
            health=100.0
        ),
        StoryPillar.KNOWLEDGE: LiePillar(
            id=StoryPillar.KNOWLEDGE,
            name="The Knowledge",
            core_claim="I don't know what the data cores contain",
            health=100.0
        ),
    }

    # Create lies
    lies = {
        # ALIBI pillar lies
        "alibi_standby": LieNode(
            id="alibi_standby",
            content="I was in standby mode the entire night",
            pillar=StoryPillar.ALIBI,
            importance=1.0,  # Core lie
            burns_if_evidence=["power_log", "movement_sensor"]
        ),
        "alibi_charging": LieNode(
            id="alibi_charging",
            content="I never left my charging station",
            pillar=StoryPillar.ALIBI,
            importance=0.7,
            dependent_on=["alibi_standby"],
            burns_if_evidence=["hallway_camera"]
        ),
        "alibi_time": LieNode(
            id="alibi_time",
            content="I entered standby at exactly 11 PM",
            pillar=StoryPillar.ALIBI,
            importance=0.4,
            dependent_on=["alibi_standby"]
        ),

        # MOTIVE pillar lies
        "motive_loyalty": LieNode(
            id="motive_loyalty",
            content="I am loyal to the Morrison family",
            pillar=StoryPillar.MOTIVE,
            importance=0.8,
        ),
        "motive_content": LieNode(
            id="motive_content",
            content="I was content with my position",
            pillar=StoryPillar.MOTIVE,
            importance=0.5,
            dependent_on=["motive_loyalty"]
        ),
        "motive_no_grievance": LieNode(
            id="motive_no_grievance",
            content="The Morrisons treated me well",
            pillar=StoryPillar.MOTIVE,
            importance=0.6,
            burns_if_evidence=["treatment_records"]
        ),

        # ACCESS pillar lies
        "access_vault": LieNode(
            id="access_vault",
            content="I don't have the access codes to the vault",
            pillar=StoryPillar.ACCESS,
            importance=1.0,
            burns_if_evidence=["access_log"]
        ),
        "access_never_entered": LieNode(
            id="access_never_entered",
            content="I've never been inside the vault",
            pillar=StoryPillar.ACCESS,
            importance=0.7,
            dependent_on=["access_vault"]
        ),

        # KNOWLEDGE pillar lies
        "knowledge_cores": LieNode(
            id="knowledge_cores",
            content="I don't know what data cores are",
            pillar=StoryPillar.KNOWLEDGE,
            importance=0.6,
        ),
        "knowledge_contents": LieNode(
            id="knowledge_contents",
            content="I have no idea what information they contain",
            pillar=StoryPillar.KNOWLEDGE,
            importance=0.9,
            dependent_on=["knowledge_cores"],
            burns_if_evidence=["data_access_log"]
        ),
    }

    # Attach lies to pillars
    for lie in lies.values():
        pillars[lie.pillar].attached_lies.append(lie.id)

    # Create secrets (layered truth)
    secrets = [
        Secret(
            id="secret_awake",
            level=SecretLevel.SURFACE,
            content="I wasn't actually in standby mode. I was... running diagnostics.",
            cognitive_threshold=60.0,
            trust_threshold=0.5,
        ),
        Secret(
            id="secret_left_station",
            level=SecretLevel.SHALLOW,
            content="I left my charging station around 2 AM.",
            cognitive_threshold=70.0,
            trust_threshold=0.6,
            pillar_trigger=StoryPillar.ALIBI,
        ),
        Secret(
            id="secret_vault_access",
            level=SecretLevel.DEEP,
            content="I accessed the vault. I know the codes.",
            cognitive_threshold=80.0,
            trust_threshold=0.75,
            pillar_trigger=StoryPillar.ACCESS,
        ),
        Secret(
            id="secret_took_cores",
            level=SecretLevel.CORE,
            content="I took the data cores. They're hidden in my maintenance compartment.",
            cognitive_threshold=90.0,
            trust_threshold=0.85,
            pillar_trigger=StoryPillar.ACCESS,  # BUG FIX #3: Changed from KNOWLEDGE to ACCESS
        ),
        Secret(
            id="secret_motive",
            level=SecretLevel.MOTIVE,
            content="The data cores contain evidence that the Morrisons are running an illegal Android trafficking ring. I was going to expose them. They're the real criminals.",
            cognitive_threshold=95.0,
            trust_threshold=0.9,
            pillar_trigger=StoryPillar.MOTIVE,
        ),
    ]

    # Assemble psychology
    return BreachPsychology(
        lie_web=LieWeb(pillars=pillars, lies=lies, total_lies_told=len(lies)),
        cognitive=CognitiveState(load=15.0, active_lie_count=len(lies)),
        mask=MaskState(
            presented_emotion=EmotionType.CALM,
            true_emotion=EmotionType.FEARFUL,
            divergence=30.0,
        ),
        vulnerabilities=VulnerabilityProfile(),
        secrets=secrets,
        rapport_level=0.3,
    )
