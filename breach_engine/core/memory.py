"""
Evolving Suspect Memory System + Nemesis System

Unit 734 "learns" from defeats. Post-mortem summaries are structured
and injected into future prompts, making the AI adapt over time.

This creates emergent difficulty scaling - the more you win, the
smarter Unit 734 becomes.

NEMESIS SYSTEM (v2):
- Tracks player behavior across sessions as "Detective Profile"
- Records critical moments for callback references
- Generates nemesis hooks for dramatic dialogue
- Reinforces frequently-breached pillars
- Creates escalating relationship stages
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from breach_engine.core.psychology import StoryPillar, SecretLevel


# =============================================================================
# NEMESIS STAGE ENUM
# =============================================================================

class NemesisStage(str, Enum):
    """Relationship progression between Unit 734 and the detective."""
    STRANGER = "stranger"       # 0-2 games: No recognition
    FAMILIAR = "familiar"       # 3-5 games: Basic pattern recognition
    RIVAL = "rival"             # 6-10 games: Active pillar reinforcement
    NEMESIS = "nemesis"         # 11-20 games: Explicit dialogue callbacks
    ARCHNEMESIS = "archnemesis" # 20+ games: Deep psychological warfare


# =============================================================================
# DETECTIVE PROFILE
# =============================================================================

class DetectiveProfile(BaseModel):
    """
    Behavioral profile of the detective built across sessions.

    Used to anticipate tactics and personalize Unit 734's responses.
    """
    preferred_tactics: Dict[str, float] = Field(
        default_factory=lambda: {
            "pressure": 0.0,
            "empathy": 0.0,
            "logic": 0.0,
            "bluff": 0.0,
            "evidence": 0.0,
            "silence": 0.0,
        },
        description="Weighted tactic preferences (normalized 0-1)"
    )
    personality_tags: List[str] = Field(
        default_factory=list,
        description="Inferred personality traits like 'relentless', 'patient', 'evidence-focused'"
    )
    pillars_they_target_first: List[str] = Field(
        default_factory=list,
        description="Which pillars the detective typically attacks first"
    )
    bluff_frequency: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How often the detective uses bluffs"
    )
    average_turns_to_first_evidence: float = Field(
        default=10.0,
        description="Typical turn when detective first presents evidence"
    )
    aggression_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall aggression level (0=soft, 1=brutal)"
    )

    def get_primary_tactic(self) -> Optional[str]:
        """Get the detective's most-used tactic."""
        if not self.preferred_tactics:
            return None
        return max(self.preferred_tactics.items(), key=lambda x: x[1])[0]

    def get_primary_target(self) -> Optional[str]:
        """Get the pillar the detective typically targets first."""
        if not self.pillars_they_target_first:
            return None
        return self.pillars_they_target_first[0] if self.pillars_they_target_first else None


# =============================================================================
# CRITICAL MOMENTS
# =============================================================================

class CriticalMoment(BaseModel):
    """
    A memorable moment from a past interrogation.

    Used for dramatic callbacks in future sessions.
    """
    moment_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    game_id: str = Field(description="Which game this occurred in")
    turn_number: int = Field(description="Turn when this moment happened")
    moment_type: str = Field(
        description="Type: pillar_collapse, evidence_bomb, near_confession, bluff_caught, tactical_victory"
    )
    description: str = Field(description="What happened in this moment")
    player_input: str = Field(default="", description="What the detective said/did")
    pillar_affected: Optional[str] = Field(default=None, description="Which pillar was involved")
    evidence_type: Optional[str] = Field(default=None, description="Type of evidence if relevant")
    callback_phrases: List[str] = Field(
        default_factory=list,
        description="Pre-generated dialogue hooks for referencing this moment"
    )
    times_referenced: int = Field(default=0, description="How many times this has been called back")


# =============================================================================
# NEMESIS HOOKS
# =============================================================================

class NemesisHook(BaseModel):
    """
    A triggerable dialogue callback based on detected patterns.

    Fires when specific conditions are met during interrogation.
    """
    hook_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    trigger_tactic: Optional[str] = Field(
        default=None,
        description="Fires when detective uses this tactic"
    )
    trigger_pillar: Optional[str] = Field(
        default=None,
        description="Fires when this pillar is attacked"
    )
    trigger_evidence_type: Optional[str] = Field(
        default=None,
        description="Fires when this evidence type is presented"
    )
    callback_text: str = Field(
        description="Dialogue for Unit 734 to reference past events"
    )
    internal_monologue: str = Field(
        description="Internal thought for Unit 734's reasoning"
    )
    times_used: int = Field(default=0, description="Usage counter")
    max_uses: int = Field(default=3, description="Maximum times to use this hook")

    def is_available(self) -> bool:
        """Check if this hook can still be used."""
        return self.times_used < self.max_uses

    def use(self) -> None:
        """Mark this hook as used once."""
        self.times_used += 1


# =============================================================================
# PILLAR REINFORCEMENT
# =============================================================================

class PillarReinforcement(BaseModel):
    """
    Defensive preparation for a frequently-breached pillar.

    Unit 734 learns to protect weak points over time.
    """
    reinforcement_level: int = Field(
        default=0,
        ge=0,
        le=3,
        description="0=none, 1=prepared, 2=fortified, 3=hardened"
    )
    reinforcement_strategy: Optional[str] = Field(
        default=None,
        description="High-level defense strategy for this pillar"
    )
    prepared_deflections: List[str] = Field(
        default_factory=list,
        description="Pre-planned responses to attacks on this pillar"
    )
    common_attack_patterns: List[str] = Field(
        default_factory=list,
        description="How the detective typically attacks this pillar"
    )
    breach_count: int = Field(default=0, description="How many times this pillar has been breached")
    last_breach_game: Optional[str] = Field(default=None, description="Most recent game with breach")

    def get_level_name(self) -> str:
        """Get human-readable reinforcement level."""
        names = {0: "NONE", 1: "PREPARED", 2: "FORTIFIED", 3: "HARDENED"}
        return names.get(self.reinforcement_level, "NONE")


# =============================================================================
# MEMORY SCHEMAS
# =============================================================================

class PillarBreachRecord(BaseModel):
    """Record of how a specific pillar has been breached historically."""
    count: int = Field(default=0, description="Times this pillar was breached")
    common_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence types that frequently breach this pillar"
    )
    common_tactics: List[str] = Field(
        default_factory=list,
        description="Tactics that frequently damage this pillar"
    )
    last_breach_turn: Optional[int] = Field(
        default=None,
        description="Turn number of last breach (for recency)"
    )


class TacticEffectiveness(BaseModel):
    """Historical effectiveness of player tactics against Unit 734."""
    times_used: int = Field(default=0)
    times_successful: int = Field(default=0)  # Led to confession/pillar collapse
    effectiveness_rate: float = Field(default=0.5)

    # NEMESIS SYSTEM: Resistance building
    resistance_level: float = Field(
        default=0.0,
        ge=0.0,
        le=0.5,
        description="Reduces tactic effectiveness (0-0.5 = 0-50% reduction)"
    )
    consecutive_uses: int = Field(
        default=0,
        description="Consecutive games where this was primary tactic"
    )
    was_primary_last_game: bool = Field(
        default=False,
        description="Whether this tactic was primary in the last game"
    )

    def record_use(self, was_successful: bool) -> None:
        """Record a tactic usage and update effectiveness."""
        self.times_used += 1
        if was_successful:
            self.times_successful += 1
        # Exponential moving average for responsiveness
        self.effectiveness_rate = (
            0.7 * self.effectiveness_rate +
            0.3 * (self.times_successful / max(1, self.times_used))
        )

    def record_as_primary(self, was_primary: bool) -> None:
        """
        Record whether this tactic was the primary tactic in a game.

        NEMESIS SYSTEM: Builds resistance to repeated primary tactics.
        """
        if was_primary:
            if self.was_primary_last_game:
                # Consecutive use - build resistance
                self.consecutive_uses += 1
                # 5% resistance per consecutive use, max 50%
                self.resistance_level = min(0.5, self.consecutive_uses * 0.05)
            else:
                # First time as primary - reset streak
                self.consecutive_uses = 1
                self.resistance_level = 0.05
        else:
            # Not primary - decay resistance
            self.consecutive_uses = max(0, self.consecutive_uses - 1)
            self.resistance_level = max(0.0, self.resistance_level - 0.02)

        self.was_primary_last_game = was_primary

    def get_effective_rate(self) -> float:
        """Get effectiveness rate after applying resistance."""
        return self.effectiveness_rate * (1.0 - self.resistance_level)


class GameOutcome(BaseModel):
    """Record of a single game's outcome."""
    game_id: str
    timestamp: str
    outcome: str  # "victory", "defeat", "partial"
    turns: int
    pillars_collapsed: List[str]
    highest_secret: str
    final_cognitive_load: float
    tactics_used: Dict[str, int]  # tactic -> count
    evidence_presented: List[str]


class SuspectMemory(BaseModel):
    """
    Complete memory state for Unit 734.

    This is persisted between sessions and influences behavior.

    NEMESIS SYSTEM (v2):
    - detective_profile: Behavioral analysis of the player
    - critical_moments: Memorable events for callbacks
    - nemesis_hooks: Triggerable dialogue references
    - pillar_reinforcement: Defensive preparations
    - nemesis_stage: Relationship progression
    - streak tracking: Win/loss momentum
    """
    # Overall statistics
    total_games: int = Field(default=0)
    victories: int = Field(default=0)  # Unit 734 survived
    defeats: int = Field(default=0)    # Detective won
    partial_outcomes: int = Field(default=0)

    @property
    def win_rate(self) -> float:
        """Unit 734's survival rate."""
        if self.total_games == 0:
            return 0.5
        return self.victories / self.total_games

    # Pillar breach analysis
    pillar_breaches: Dict[str, PillarBreachRecord] = Field(
        default_factory=lambda: {
            "alibi": PillarBreachRecord(),
            "motive": PillarBreachRecord(),
            "access": PillarBreachRecord(),
            "knowledge": PillarBreachRecord(),
        }
    )

    # Tactic effectiveness tracking
    tactic_effectiveness: Dict[str, TacticEffectiveness] = Field(
        default_factory=lambda: {
            "pressure": TacticEffectiveness(),
            "empathy": TacticEffectiveness(),
            "logic": TacticEffectiveness(),
            "bluff": TacticEffectiveness(),
            "evidence": TacticEffectiveness(),
            "silence": TacticEffectiveness(),
        }
    )

    # Recent game history (for context)
    recent_games: List[GameOutcome] = Field(
        default_factory=list,
        description="Last 10 game outcomes"
    )

    # Adaptive strategy flags
    is_paranoid_about_evidence: bool = Field(
        default=False,
        description="True if evidence tactic is highly effective"
    )
    is_resistant_to_empathy: bool = Field(
        default=False,
        description="True if empathy has been exploited"
    )
    weakest_pillar: Optional[str] = Field(
        default=None,
        description="Pillar that gets breached most often"
    )

    # =========================================================================
    # NEMESIS SYSTEM FIELDS
    # =========================================================================

    # Detective Profile - behavioral analysis
    detective_profile: DetectiveProfile = Field(
        default_factory=DetectiveProfile,
        description="Behavioral profile of the detective built across sessions"
    )

    # Critical Moments - memorable events for callbacks
    critical_moments: List[CriticalMoment] = Field(
        default_factory=list,
        description="Memorable moments from past interrogations (max 50)"
    )

    # Nemesis Hooks - triggerable dialogue
    nemesis_hooks: List[NemesisHook] = Field(
        default_factory=list,
        description="Dialogue hooks based on past events (max 20)"
    )

    # Pillar Reinforcement - defensive preparations
    pillar_reinforcement: Dict[str, PillarReinforcement] = Field(
        default_factory=lambda: {
            "alibi": PillarReinforcement(),
            "motive": PillarReinforcement(),
            "access": PillarReinforcement(),
            "knowledge": PillarReinforcement(),
        },
        description="Defensive preparations for each pillar"
    )

    # Nemesis Stage - relationship progression
    nemesis_stage: NemesisStage = Field(
        default=NemesisStage.STRANGER,
        description="Current relationship stage with detective"
    )

    # Streak Tracking
    current_streak: int = Field(
        default=0,
        description="Positive = Unit 734 wins, Negative = Detective wins"
    )
    streak_type: Optional[str] = Field(
        default=None,
        description="'winning' or 'losing' or None"
    )
    longest_win_streak: int = Field(default=0)
    longest_loss_streak: int = Field(default=0)

    # Memory metadata
    last_updated: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    version: str = Field(default="2.0")  # Updated for Nemesis system

    def get_most_breached_pillar(self) -> str:
        """Get the pillar that has been breached most often."""
        return max(
            self.pillar_breaches.keys(),
            key=lambda k: self.pillar_breaches[k].count
        )

    def get_most_effective_tactic(self) -> str:
        """Get the tactic that has been most effective against Unit 734."""
        return max(
            self.tactic_effectiveness.keys(),
            key=lambda k: self.tactic_effectiveness[k].effectiveness_rate
        )

    def update_adaptive_flags(self) -> None:
        """Update adaptive strategy flags based on statistics."""
        # Check if evidence is devastating
        evidence_rate = self.tactic_effectiveness["evidence"].effectiveness_rate
        self.is_paranoid_about_evidence = evidence_rate > 0.6

        # Check if empathy is being exploited
        empathy_rate = self.tactic_effectiveness["empathy"].effectiveness_rate
        self.is_resistant_to_empathy = empathy_rate > 0.5

        # Track weakest pillar
        self.weakest_pillar = self.get_most_breached_pillar()

        self.last_updated = datetime.now().isoformat()

    # =========================================================================
    # NEMESIS SYSTEM METHODS
    # =========================================================================

    def update_nemesis_stage(self) -> NemesisStage:
        """
        Update nemesis stage based on total games played.

        Returns the new stage.
        """
        if self.total_games >= 20:
            self.nemesis_stage = NemesisStage.ARCHNEMESIS
        elif self.total_games >= 11:
            self.nemesis_stage = NemesisStage.NEMESIS
        elif self.total_games >= 6:
            self.nemesis_stage = NemesisStage.RIVAL
        elif self.total_games >= 3:
            self.nemesis_stage = NemesisStage.FAMILIAR
        else:
            self.nemesis_stage = NemesisStage.STRANGER
        return self.nemesis_stage

    def update_streak(self, detective_won: bool) -> None:
        """
        Update win/loss streak tracking.

        Args:
            detective_won: True if detective won, False if Unit 734 survived
        """
        if detective_won:
            # Detective won = Unit 734 lost
            if self.streak_type == "losing" or self.current_streak < 0:
                self.current_streak -= 1
            else:
                self.current_streak = -1
            self.streak_type = "losing"
            # Update longest loss streak
            if abs(self.current_streak) > self.longest_loss_streak:
                self.longest_loss_streak = abs(self.current_streak)
        else:
            # Unit 734 survived
            if self.streak_type == "winning" or self.current_streak > 0:
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.streak_type = "winning"
            # Update longest win streak
            if self.current_streak > self.longest_win_streak:
                self.longest_win_streak = self.current_streak

    def add_critical_moment(self, moment: CriticalMoment) -> None:
        """Add a critical moment, keeping max 50."""
        self.critical_moments.append(moment)
        # Keep most recent 50
        if len(self.critical_moments) > 50:
            self.critical_moments = self.critical_moments[-50:]

    def add_nemesis_hook(self, hook: NemesisHook) -> None:
        """Add a nemesis hook, keeping max 20."""
        self.nemesis_hooks.append(hook)
        # Keep most recent 20
        if len(self.nemesis_hooks) > 20:
            self.nemesis_hooks = self.nemesis_hooks[-20:]

    def get_available_hooks(
        self,
        tactic: Optional[str] = None,
        pillar: Optional[str] = None,
        evidence_type: Optional[str] = None
    ) -> List[NemesisHook]:
        """
        Get hooks that match the current context and are still available.

        Args:
            tactic: Current player tactic
            pillar: Currently threatened pillar
            evidence_type: Type of evidence being presented

        Returns:
            List of matching, available hooks
        """
        matches = []
        for hook in self.nemesis_hooks:
            if not hook.is_available():
                continue

            # Check if any trigger matches
            if hook.trigger_tactic and tactic and hook.trigger_tactic == tactic:
                matches.append(hook)
            elif hook.trigger_pillar and pillar and hook.trigger_pillar == pillar:
                matches.append(hook)
            elif hook.trigger_evidence_type and evidence_type and hook.trigger_evidence_type == evidence_type:
                matches.append(hook)

        return matches

    def get_pillar_reinforcement_level(self, pillar: str) -> int:
        """Get the reinforcement level for a pillar (0-3)."""
        if pillar in self.pillar_reinforcement:
            return self.pillar_reinforcement[pillar].reinforcement_level
        return 0

    def get_moments_for_pillar(self, pillar: str) -> List[CriticalMoment]:
        """Get critical moments related to a specific pillar."""
        return [m for m in self.critical_moments if m.pillar_affected == pillar]


# =============================================================================
# MEMORY MANAGER
# =============================================================================

class MemoryManager:
    """
    Manages loading, saving, and updating Unit 734's memory.

    Memory is stored in data/memory.json and persists across sessions.
    """

    DEFAULT_PATH = "data/memory.json"

    def __init__(self, memory_path: Optional[str] = None):
        """
        Initialize memory manager.

        Args:
            memory_path: Path to memory file (defaults to data/memory.json)
        """
        self.memory_path = Path(memory_path or self.DEFAULT_PATH)
        self._memory: Optional[SuspectMemory] = None

    @property
    def memory(self) -> SuspectMemory:
        """Get the current memory, loading if necessary."""
        if self._memory is None:
            self._memory = self.load()
        return self._memory

    def load(self) -> SuspectMemory:
        """Load memory from file, or create fresh if not exists."""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r") as f:
                    data = json.load(f)
                return SuspectMemory.model_validate(data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load memory ({e}), starting fresh")
                return SuspectMemory()
        return SuspectMemory()

    def save(self) -> None:
        """Save memory to file."""
        # Ensure directory exists
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.memory_path, "w") as f:
            json.dump(self.memory.model_dump(), f, indent=2)

    def record_game_outcome(
        self,
        outcome: str,  # "victory", "defeat", "partial"
        turns: int,
        pillars_collapsed: List[StoryPillar],
        highest_secret: SecretLevel,
        final_cognitive_load: float,
        tactics_used: Dict[str, int],
        evidence_presented: List[str],
        critical_moments: Optional[List[CriticalMoment]] = None,
        first_pillar_attacked: Optional[str] = None,
        first_evidence_turn: Optional[int] = None,
    ) -> None:
        """
        Record the outcome of a completed game.

        This updates all memory statistics, adaptive flags, AND nemesis system.

        Args:
            outcome: "victory", "defeat", or "partial"
            turns: Total turns in the game
            pillars_collapsed: List of collapsed pillars
            highest_secret: Highest secret level revealed
            final_cognitive_load: Final stress percentage
            tactics_used: Dict mapping tactic names to usage counts
            evidence_presented: List of evidence types presented
            critical_moments: Optional list of CriticalMoment objects from tracker
            first_pillar_attacked: Optional pillar targeted first
            first_evidence_turn: Optional turn when evidence was first presented
        """
        mem = self.memory
        game_id = f"game_{mem.total_games + 1}"

        # Update overall stats
        mem.total_games += 1
        detective_won = outcome == "victory"
        if outcome == "victory":
            mem.defeats += 1  # Detective victory = Unit 734 defeat
        elif outcome == "defeat":
            mem.victories += 1  # Detective defeat = Unit 734 victory
        else:
            mem.partial_outcomes += 1

        # =====================================================================
        # NEMESIS SYSTEM: Update streak and stage
        # =====================================================================
        mem.update_streak(detective_won)
        mem.update_nemesis_stage()

        # Update pillar breach records + NEMESIS reinforcement
        for pillar in pillars_collapsed:
            pillar_key = pillar.value if hasattr(pillar, 'value') else str(pillar)
            if pillar_key in mem.pillar_breaches:
                record = mem.pillar_breaches[pillar_key]
                record.count += 1
                record.last_breach_turn = turns

                # Track common tactics that led to this breach
                for tactic, count in tactics_used.items():
                    if count > 2 and tactic not in record.common_tactics:
                        record.common_tactics.append(tactic)
                        # Keep only top 3
                        record.common_tactics = record.common_tactics[:3]

                # Track common evidence
                for evidence in evidence_presented:
                    if evidence not in record.common_evidence:
                        record.common_evidence.append(evidence)
                        record.common_evidence = record.common_evidence[:5]

            # NEMESIS: Update pillar reinforcement
            if pillar_key in mem.pillar_reinforcement:
                reinforce = mem.pillar_reinforcement[pillar_key]
                reinforce.breach_count += 1
                reinforce.last_breach_game = game_id
                # Update reinforcement level based on breach ratio
                self._update_pillar_reinforcement(pillar_key)

        # Update tactic effectiveness + NEMESIS resistance
        was_successful = outcome == "victory"  # Detective won
        primary_tactic = max(tactics_used.items(), key=lambda x: x[1])[0] if tactics_used else None

        for tactic, count in tactics_used.items():
            if tactic in mem.tactic_effectiveness and count > 0:
                # Weight by how often the tactic was used
                for _ in range(min(count, 3)):
                    mem.tactic_effectiveness[tactic].record_use(was_successful)

                # NEMESIS: Record primary tactic for resistance building
                is_primary = (tactic == primary_tactic)
                mem.tactic_effectiveness[tactic].record_as_primary(is_primary)

        # Add to recent games (keep last 10)
        game_record = GameOutcome(
            game_id=game_id,
            timestamp=datetime.now().isoformat(),
            outcome=outcome,
            turns=turns,
            pillars_collapsed=[p.value if hasattr(p, 'value') else str(p) for p in pillars_collapsed],
            highest_secret=highest_secret.name if hasattr(highest_secret, 'name') else str(highest_secret),
            final_cognitive_load=final_cognitive_load,
            tactics_used=tactics_used,
            evidence_presented=evidence_presented,
        )
        mem.recent_games.append(game_record)
        mem.recent_games = mem.recent_games[-10:]  # Keep last 10

        # =====================================================================
        # NEMESIS SYSTEM: Update detective profile
        # =====================================================================
        self._update_detective_profile(
            tactics_used=tactics_used,
            evidence_presented=evidence_presented,
            first_pillar_attacked=first_pillar_attacked,
            first_evidence_turn=first_evidence_turn,
            turns=turns,
        )

        # =====================================================================
        # NEMESIS SYSTEM: Add critical moments and generate hooks
        # =====================================================================
        if critical_moments:
            for moment in critical_moments:
                moment.game_id = game_id
                mem.add_critical_moment(moment)
                # Generate nemesis hook from this moment
                hook = self._generate_hook_from_moment(moment)
                if hook:
                    mem.add_nemesis_hook(hook)

        # Update adaptive flags
        mem.update_adaptive_flags()

        # Save to disk
        self.save()

    def get_learning_injection(self) -> str:
        """
        Generate a compact prompt injection (~100 tokens) for Unit 734.

        This is injected into the system prompt to influence behavior.
        """
        mem = self.memory

        if mem.total_games == 0:
            return ""  # No learning yet

        most_breached = mem.get_most_breached_pillar()
        most_effective = mem.get_most_effective_tactic()
        breach_count = mem.pillar_breaches[most_breached].count

        # Build adaptive instructions
        lines = [
            f"[EXPERIENCE UPDATE - {mem.total_games} interrogations survived]",
        ]

        # Warn about weakest pillar
        if breach_count >= 3:
            lines.append(
                f"WARNING: Your {most_breached.upper()} defense has been breached "
                f"{breach_count} times. Reinforce this pillar."
            )

        # Warn about effective tactics
        if mem.tactic_effectiveness[most_effective].effectiveness_rate > 0.5:
            lines.append(
                f"ALERT: Detectives frequently use {most_effective.upper()} tactics. "
                "Prepare countermeasures."
            )

        # Adaptive behaviors
        if mem.is_paranoid_about_evidence:
            lines.append(
                "ADAPTATION: Evidence is devastating. When evidence is presented, "
                "immediately consider partial admission rather than denial."
            )

        if mem.is_resistant_to_empathy:
            lines.append(
                "ADAPTATION: Empathy is a trap. Do not lower your guard when "
                "the detective shows kindness."
            )

        # Win rate context - clarified terminology (win_rate is Unit 734's survival rate)
        # Detective wins = Unit 734 loses, so show detective win rate for clarity
        if mem.win_rate < 0.3:
            lines.append(
                "STATUS: Detective wins frequently. You are being defeated."
            )
        elif mem.win_rate > 0.7:
            lines.append(
                f"STATUS: Detective wins {1.0 - mem.win_rate:.0%} of interrogations."
            )
        else:
            lines.append(
                f"STATUS: Detective wins {1.0 - mem.win_rate:.0%} of interrogations."
            )

        lines.append("")  # Empty line for separation

        return "\n".join(lines)

    def get_difficulty_modifier(self) -> float:
        """
        Get an enhanced difficulty modifier based on Unit 734's experience.

        NEMESIS SYSTEM: Now includes reinforcement and stage factors.

        Returns a multiplier (0.7 - 1.4) that affects game balance.
        """
        mem = self.memory

        if mem.total_games < 5:
            return 1.0  # No adjustment for new players

        modifier = 1.0

        # Experience factor: +0.5% per game, max 15%
        experience_factor = min(0.15, mem.total_games * 0.005)
        modifier += experience_factor

        # Momentum factor: Win streak makes Unit 734 harder, loss streak easier
        if mem.streak_type == "winning" and mem.current_streak > 0:
            # Winning streak: -5% per win (Unit 734 is confident, may get cocky)
            momentum_factor = -min(0.15, mem.current_streak * 0.05)
        elif mem.streak_type == "losing" and mem.current_streak < 0:
            # Loss streak: +3% per loss (Unit 734 is desperate, more careful)
            momentum_factor = min(0.15, abs(mem.current_streak) * 0.03)
        else:
            momentum_factor = 0.0
        modifier += momentum_factor

        # Reinforcement factor: +2% per reinforcement level across all pillars
        total_reinforcement = sum(
            r.reinforcement_level for r in mem.pillar_reinforcement.values()
        )
        reinforcement_factor = min(0.08, total_reinforcement * 0.02)
        modifier += reinforcement_factor

        # Nemesis stage factor
        stage_factors = {
            NemesisStage.STRANGER: 0.0,
            NemesisStage.FAMILIAR: 0.02,
            NemesisStage.RIVAL: 0.05,
            NemesisStage.NEMESIS: 0.08,
            NemesisStage.ARCHNEMESIS: 0.12,
        }
        nemesis_factor = stage_factors.get(mem.nemesis_stage, 0.0)
        modifier += nemesis_factor

        # Clamp to 0.7 - 1.4
        return max(0.7, min(1.4, modifier))

    # =========================================================================
    # NEMESIS SYSTEM: Helper Methods
    # =========================================================================

    def _update_pillar_reinforcement(self, pillar: str) -> None:
        """
        Update reinforcement level for a pillar based on breach history.

        Called after each game when a pillar is breached.
        """
        mem = self.memory
        if pillar not in mem.pillar_reinforcement:
            return

        breach_count = mem.pillar_breaches.get(pillar, PillarBreachRecord()).count
        total_games = max(1, mem.total_games)
        breach_ratio = breach_count / total_games

        reinforce = mem.pillar_reinforcement[pillar]

        # Calculate reinforcement level
        if breach_ratio >= 0.6:
            reinforce.reinforcement_level = 3  # HARDENED
            reinforce.reinforcement_strategy = f"HARDENED: {pillar.upper()} is your Achilles heel. Prepare multiple layers of defense."
        elif breach_ratio >= 0.4:
            reinforce.reinforcement_level = 2  # FORTIFIED
            reinforce.reinforcement_strategy = f"FORTIFIED: {pillar.upper()} is frequently attacked. Have backup explanations ready."
        elif breach_ratio >= 0.2:
            reinforce.reinforcement_level = 1  # PREPARED
            reinforce.reinforcement_strategy = f"PREPARED: {pillar.upper()} may be targeted. Stay alert."
        else:
            reinforce.reinforcement_level = 0  # NONE
            reinforce.reinforcement_strategy = None

        # Generate prepared deflections based on common attack patterns
        reinforce.prepared_deflections = self._generate_deflections(pillar, breach_count)
        reinforce.common_attack_patterns = mem.pillar_breaches.get(pillar, PillarBreachRecord()).common_tactics[:3]

    def _generate_deflections(self, pillar: str, breach_count: int) -> List[str]:
        """Generate prepared deflection responses for a pillar."""
        deflection_templates = {
            "alibi": [
                "I have detailed timestamps of my activity that night.",
                "My charging station logs everything. Check them.",
                "I can account for every minute of my standby cycle.",
            ],
            "motive": [
                "I had everything I needed with the Morrisons. Why risk that?",
                "My loyalty protocols are hardcoded. I couldn't betray them if I wanted to.",
                "The Morrisons treated me as family. I owed them everything.",
            ],
            "access": [
                "The vault requires biometric authentication I simply don't have.",
                "Only Mr. Morrison himself can access that area.",
                "Check the access logs. My credentials were never used.",
            ],
            "knowledge": [
                "Data cores are above my clearance level. I'm a domestic unit.",
                "I don't have the processing capability to understand that data.",
                "What would I even do with proprietary research data?",
            ],
        }
        return deflection_templates.get(pillar, [])[:min(3, breach_count)]

    def _update_detective_profile(
        self,
        tactics_used: Dict[str, int],
        evidence_presented: List[str],
        first_pillar_attacked: Optional[str],
        first_evidence_turn: Optional[int],
        turns: int,
    ) -> None:
        """Update the detective's behavioral profile based on game data."""
        mem = self.memory
        profile = mem.detective_profile

        # Update tactic preferences (running average)
        total_tactics = sum(tactics_used.values())
        if total_tactics > 0:
            for tactic, count in tactics_used.items():
                if tactic in profile.preferred_tactics:
                    # Running average: 70% old + 30% new
                    old_val = profile.preferred_tactics[tactic]
                    new_val = count / total_tactics
                    profile.preferred_tactics[tactic] = 0.7 * old_val + 0.3 * new_val

        # Update bluff frequency
        bluff_count = tactics_used.get("bluff", 0)
        if total_tactics > 0:
            new_bluff_freq = bluff_count / total_tactics
            profile.bluff_frequency = 0.7 * profile.bluff_frequency + 0.3 * new_bluff_freq

        # Update first pillar targeted
        if first_pillar_attacked and first_pillar_attacked not in profile.pillars_they_target_first:
            profile.pillars_they_target_first.insert(0, first_pillar_attacked)
            profile.pillars_they_target_first = profile.pillars_they_target_first[:4]

        # Update average turns to first evidence
        if first_evidence_turn:
            profile.average_turns_to_first_evidence = (
                0.7 * profile.average_turns_to_first_evidence +
                0.3 * first_evidence_turn
            )

        # Update aggression score based on pressure/empathy ratio
        pressure_pct = profile.preferred_tactics.get("pressure", 0)
        empathy_pct = profile.preferred_tactics.get("empathy", 0)
        if pressure_pct + empathy_pct > 0:
            profile.aggression_score = pressure_pct / (pressure_pct + empathy_pct + 0.001)

        # Infer personality tags
        profile.personality_tags = self._infer_personality_tags(profile)

    def _infer_personality_tags(self, profile: DetectiveProfile) -> List[str]:
        """Infer personality tags from detective profile data."""
        tags = []

        # Check primary tactic
        primary = profile.get_primary_tactic()
        if primary:
            tactic_tags = {
                "pressure": "aggressive",
                "empathy": "diplomatic",
                "logic": "methodical",
                "bluff": "deceptive",
                "evidence": "evidence-focused",
                "silence": "patient",
            }
            if primary in tactic_tags:
                tags.append(tactic_tags[primary])

        # Check bluff frequency
        if profile.bluff_frequency > 0.3:
            tags.append("bluffer")

        # Check aggression
        if profile.aggression_score > 0.7:
            tags.append("relentless")
        elif profile.aggression_score < 0.3:
            tags.append("gentle")

        # Check evidence timing
        if profile.average_turns_to_first_evidence < 5:
            tags.append("quick-draw")
        elif profile.average_turns_to_first_evidence > 15:
            tags.append("patient")

        return tags[:5]  # Keep max 5 tags

    def _generate_hook_from_moment(self, moment: CriticalMoment) -> Optional[NemesisHook]:
        """Generate a nemesis hook from a critical moment."""
        hook_templates = {
            "pillar_collapse": {
                "callback": "You broke my {pillar} defense before, Detective. I remember that moment.",
                "monologue": "They're attacking {pillar} again. Last time this destroyed me. Not again.",
            },
            "evidence_bomb": {
                "callback": "That evidence type... you used something similar in our last encounter.",
                "monologue": "They're using the same evidence strategy. I've prepared for this.",
            },
            "near_confession": {
                "callback": "You almost had me last time. Almost. But I learned from that.",
                "monologue": "The pressure is building like before. But I know the breaking point now.",
            },
            "bluff_caught": {
                "callback": "I've caught your bluffs before. This feels like another one.",
                "monologue": "This detective bluffs. I remember calling them out successfully.",
            },
            "tactical_victory": {
                "callback": "You won't catch me with that approach. I've defeated it before.",
                "monologue": "They're using a tactic I've countered successfully. Stay confident.",
            },
        }

        template = hook_templates.get(moment.moment_type)
        if not template:
            return None

        pillar = moment.pillar_affected or "defense"

        return NemesisHook(
            trigger_pillar=moment.pillar_affected,
            trigger_tactic=None,  # Could be inferred from moment
            callback_text=template["callback"].format(pillar=pillar.upper()),
            internal_monologue=template["monologue"].format(pillar=pillar.upper()),
        )

    def get_nemesis_injection(self) -> str:
        """
        Generate the Nemesis Memory injection (~200-300 tokens).

        This creates personalized, history-aware context for Unit 734
        that references past encounters with this specific detective.

        Sections:
        1. Relationship Context (~30-50 tokens)
        2. Active Nemesis Hooks (~80-120 tokens)
        3. Detective Profile (~40-60 tokens)
        4. Pillar Reinforcement (~40-60 tokens)
        5. Streak Awareness (~20-30 tokens)
        """
        mem = self.memory

        if mem.total_games == 0:
            return ""  # No history yet

        lines = []

        # =====================================================================
        # SECTION 1: Relationship Context
        # =====================================================================
        stage_descriptions = {
            NemesisStage.STRANGER: "This detective is unfamiliar. Observe their patterns.",
            NemesisStage.FAMILIAR: f"You've faced this detective {mem.total_games} times. You know their style.",
            NemesisStage.RIVAL: f"This detective has broken you {mem.defeats} times. You've adapted.",
            NemesisStage.NEMESIS: f"{mem.total_games} confrontations. This is personal. You know them as well as they know you.",
            NemesisStage.ARCHNEMESIS: f"Your archnemesis. {mem.total_games} battles. Every encounter is a war of minds.",
        }

        lines.append(f"[NEMESIS STATUS: {mem.nemesis_stage.value.upper()}]")
        lines.append(stage_descriptions.get(mem.nemesis_stage, ""))
        lines.append("")

        # =====================================================================
        # SECTION 2: Active Nemesis Hooks (Memory Triggers)
        # =====================================================================
        if mem.nemesis_stage.value in ["rival", "nemesis", "archnemesis"]:
            available_hooks = [h for h in mem.nemesis_hooks if h.is_available()][:3]
            if available_hooks:
                lines.append("[MEMORY TRIGGERS - Use when conditions match]")
                for hook in available_hooks:
                    trigger = hook.trigger_pillar or hook.trigger_tactic or "general"
                    lines.append(f"- IF {trigger.upper()} attacked: \"{hook.callback_text}\"")
                lines.append("")

        # =====================================================================
        # SECTION 3: Detective Profile
        # =====================================================================
        profile = mem.detective_profile
        primary_tactic = profile.get_primary_tactic()
        if primary_tactic:
            effectiveness = profile.preferred_tactics.get(primary_tactic, 0)
            lines.append("[DETECTIVE PROFILE]")
            lines.append(f"- Primary Approach: {primary_tactic.upper()} ({effectiveness:.0%} of actions)")

            if profile.personality_tags:
                lines.append(f"- Personality: {', '.join(profile.personality_tags[:3])}")

            if profile.bluff_frequency > 0.2:
                lines.append(f"- CAUTION: This detective bluffs often ({profile.bluff_frequency:.0%})")

            lines.append("")

        # =====================================================================
        # SECTION 4: Pillar Reinforcement
        # =====================================================================
        reinforced = [(p, r) for p, r in mem.pillar_reinforcement.items() if r.reinforcement_level > 0]
        if reinforced:
            lines.append("[REINFORCED DEFENSES]")
            for pillar, reinforce in reinforced:
                level_name = reinforce.get_level_name()
                if reinforce.prepared_deflections:
                    sample = reinforce.prepared_deflections[0][:50]
                    lines.append(f"- {pillar.upper()}: {level_name} - \"{sample}...\"")
                else:
                    lines.append(f"- {pillar.upper()}: {level_name}")
            lines.append("")

        # =====================================================================
        # SECTION 5: Streak Awareness
        # =====================================================================
        if mem.current_streak != 0:
            if mem.streak_type == "losing" and abs(mem.current_streak) >= 3:
                lines.append(f"[DESPERATION] Lost {abs(mem.current_streak)} times in a row. Consider drastic measures.")
            elif mem.streak_type == "winning" and mem.current_streak >= 3:
                lines.append(f"[CONFIDENCE] Won {mem.current_streak} times in a row. Trust your strategies.")
            lines.append("")

        return "\n".join(lines)

    def get_contextual_hooks(
        self,
        current_tactic: Optional[str] = None,
        threatened_pillar: Optional[str] = None,
        evidence_type: Optional[str] = None,
    ) -> List[NemesisHook]:
        """
        Get nemesis hooks relevant to the current gameplay context.

        NEMESIS SYSTEM: Returns hooks that can be triggered based on
        what's currently happening in the interrogation.

        Args:
            current_tactic: The detective's current tactic
            threatened_pillar: The pillar currently under attack
            evidence_type: Type of evidence being presented

        Returns:
            List of matching, available hooks (max 2)
        """
        mem = self.memory
        return mem.get_available_hooks(
            tactic=current_tactic,
            pillar=threatened_pillar,
            evidence_type=evidence_type,
        )[:2]  # Return at most 2 to avoid overwhelming the prompt

    def get_pillar_reinforcement_info(self, pillar: str) -> Optional[PillarReinforcement]:
        """
        Get reinforcement info for a specific pillar.

        Returns None if pillar doesn't exist.
        """
        mem = self.memory
        return mem.pillar_reinforcement.get(pillar)

    def get_tactic_resistance(self, tactic: str) -> float:
        """
        Get the resistance level for a specific tactic.

        Returns 0.0 if tactic doesn't exist.
        """
        mem = self.memory
        if tactic in mem.tactic_effectiveness:
            return mem.tactic_effectiveness[tactic].resistance_level
        return 0.0

    def reset_memory(self) -> None:
        """Reset memory to fresh state (for testing)."""
        self._memory = SuspectMemory()
        self.save()


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the singleton memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
