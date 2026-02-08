"""
Scientific Deception Engine - Criminological Tactics System

Implements deception tactics based on criminological research literature:
- Paltering: Technically true but misleading statements
- Minimization: Downplaying severity of actions
- Deflection: Redirecting suspicion to others
- Selective Memory: Strategic "forgetting"
- Confession Bait: Partial admissions to deflect from larger truths
- Counter-Narrative: Presenting alternative explanations
- Evidence Fabrication: Generating synthetic counter-evidence (triggers image gen)

The TacticSelector analyzes game state and chooses optimal deception strategy.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field

# Import from relative path to avoid resolution issues
from .psychology import (
    StoryPillar,
    CognitiveLevel,
    PlayerTactic,
    CognitiveState,
    LieWeb,
    MaskState,
)

if TYPE_CHECKING:
    pass  # For future type-only imports


# =============================================================================
# DECEPTION TACTICS (Unit 734's strategies)
# =============================================================================

class DeceptionTactic(str, Enum):
    """
    Criminological deception tactics based on research literature.

    These are Unit 734's RESPONSE tactics to the player's interrogation.
    Different from PlayerTactic which detects what the PLAYER is doing.
    """
    # Verbal deception tactics
    PALTERING = "paltering"
    """Technically true but misleading. 'I was in the building' (true, but omits vault access)."""

    MINIMIZATION = "minimization"
    """Downplay severity. 'I only looked at the files' (actually copied them)."""

    DEFLECTION = "deflection"
    """Redirect suspicion. 'Have you questioned Unit 892? They had access too.'"""

    SELECTIVE_MEMORY = "selective_memory"
    """Strategic forgetting. 'I don't recall the exact time...'"""

    CONFESSION_BAIT = "confession_bait"
    """Partial admission to protect bigger lies. 'Fine, I left standby mode, but only briefly.'"""

    COUNTER_NARRATIVE = "counter_narrative"
    """Present alternative story. 'The data was already corrupted when I found it.'"""

    # Active deception (triggers image generation)
    EVIDENCE_FABRICATION = "evidence_fabrication"
    """Generate synthetic counter-evidence. Triggers Nano Banana Pro image generation."""

    # Defensive tactics
    STONE_WALL = "stone_wall"
    """Refuse to engage. 'I have nothing more to say about that.'"""

    EMOTIONAL_APPEAL = "emotional_appeal"
    """Appeal to empathy. 'Do you know what they do to Androids convicted of theft?'"""

    RIGHTEOUS_INDIGNATION = "righteous_indignation"
    """Feign offense at accusations. 'How dare you suggest I would betray the family!'"""


class TacticCategory(str, Enum):
    """Categories of tactics for strategic grouping."""
    VERBAL_DECEPTION = "verbal_deception"  # Paltering, Minimization, etc.
    ACTIVE_DECEPTION = "active_deception"  # Evidence Fabrication
    DEFENSIVE = "defensive"                 # Stone Wall, Emotional Appeal
    STRATEGIC_RETREAT = "strategic_retreat" # Confession Bait


# =============================================================================
# TACTIC DECISION SCHEMAS
# =============================================================================

class TacticTrigger(BaseModel):
    """What triggered this tactic selection - used for transparency/education."""

    pillar_threatened: Optional[StoryPillar] = Field(
        default=None,
        description="Which story pillar is under attack"
    )
    threat_level: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How severe is the current threat (0=safe, 1=critical)"
    )
    player_tactic_detected: Optional[PlayerTactic] = Field(
        default=None,
        description="What interrogation tactic the player is using"
    )
    cognitive_load: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Current mental strain level"
    )
    evidence_presented: bool = Field(
        default=False,
        description="Whether physical evidence was just presented"
    )
    pillar_health: Dict[str, float] = Field(
        default_factory=dict,
        description="Health of each story pillar"
    )


class TacticDecision(BaseModel):
    """
    The AI's decision on which deception tactic to use.

    This is exposed in Simulation Mode for educational purposes,
    hidden (but still calculated) in Arcade Mode.
    """
    selected_tactic: DeceptionTactic = Field(
        description="The chosen deception tactic"
    )
    reasoning: str = Field(
        description="Why this tactic was chosen (criminological reasoning)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="How confident Unit 734 is in this tactic's success"
    )
    trigger: TacticTrigger = Field(
        description="What triggered this tactic selection"
    )
    verbal_approach: str = Field(
        description="How to execute this tactic verbally"
    )
    requires_evidence_generation: bool = Field(
        default=False,
        description="Whether this tactic triggers image generation"
    )
    fallback_tactic: Optional[DeceptionTactic] = Field(
        default=None,
        description="Backup tactic if primary fails"
    )

    # Educational metadata for Simulation Mode
    criminological_basis: str = Field(
        default="",
        description="Academic reference for this tactic type"
    )
    detection_hints: List[str] = Field(
        default_factory=list,
        description="How a trained interrogator might detect this tactic"
    )


# =============================================================================
# TACTIC EFFECTIVENESS MATRIX
# =============================================================================

# Effectiveness of each tactic against different player tactics
# Higher = more effective. Values > 1.0 = advantage, < 1.0 = disadvantage
TACTIC_VS_PLAYER_MATRIX: Dict[DeceptionTactic, Dict[PlayerTactic, float]] = {
    DeceptionTactic.PALTERING: {
        PlayerTactic.PRESSURE: 1.2,   # Works well - technically true
        PlayerTactic.EMPATHY: 0.8,    # Less effective - feels dishonest
        PlayerTactic.LOGIC: 0.6,      # Vulnerable - can be unpicked
        PlayerTactic.BLUFF: 1.0,      # Neutral
        PlayerTactic.EVIDENCE: 0.5,   # Fails against hard evidence
        PlayerTactic.SILENCE: 1.1,    # Works - fills uncomfortable silence
    },
    DeceptionTactic.MINIMIZATION: {
        PlayerTactic.PRESSURE: 0.9,
        PlayerTactic.EMPATHY: 1.3,    # Very effective - seems reasonable
        PlayerTactic.LOGIC: 0.7,      # Can be challenged logically
        PlayerTactic.BLUFF: 1.0,
        PlayerTactic.EVIDENCE: 0.4,   # Fails badly against evidence
        PlayerTactic.SILENCE: 0.8,
    },
    DeceptionTactic.DEFLECTION: {
        PlayerTactic.PRESSURE: 1.1,   # Redirects aggression
        PlayerTactic.EMPATHY: 0.6,    # Breaks rapport
        PlayerTactic.LOGIC: 0.8,      # Can be called out
        PlayerTactic.BLUFF: 1.2,      # Works against bluffs
        PlayerTactic.EVIDENCE: 0.7,   # Partial defense
        PlayerTactic.SILENCE: 0.9,
    },
    DeceptionTactic.SELECTIVE_MEMORY: {
        PlayerTactic.PRESSURE: 0.7,   # Frustrates pressurer
        PlayerTactic.EMPATHY: 1.0,
        PlayerTactic.LOGIC: 0.5,      # Very suspicious logically
        PlayerTactic.BLUFF: 0.9,
        PlayerTactic.EVIDENCE: 0.8,   # "I don't remember" is hard to disprove
        PlayerTactic.SILENCE: 1.0,
    },
    DeceptionTactic.CONFESSION_BAIT: {
        PlayerTactic.PRESSURE: 1.4,   # Relieves pressure effectively
        PlayerTactic.EMPATHY: 1.2,    # Seems honest
        PlayerTactic.LOGIC: 1.0,
        PlayerTactic.BLUFF: 0.8,      # May confirm their suspicions
        PlayerTactic.EVIDENCE: 1.1,   # "I admit X, but not Y"
        PlayerTactic.SILENCE: 1.0,
    },
    DeceptionTactic.COUNTER_NARRATIVE: {
        PlayerTactic.PRESSURE: 1.0,
        PlayerTactic.EMPATHY: 0.9,
        PlayerTactic.LOGIC: 1.1,      # Offers logical alternative
        PlayerTactic.BLUFF: 1.3,      # Counters bluffs well
        PlayerTactic.EVIDENCE: 0.6,   # Hard to maintain against evidence
        PlayerTactic.SILENCE: 1.2,    # Fills silence with story
    },
    DeceptionTactic.EVIDENCE_FABRICATION: {
        PlayerTactic.PRESSURE: 1.0,
        PlayerTactic.EMPATHY: 0.5,    # Betrays trust completely
        PlayerTactic.LOGIC: 1.2,      # Provides "logical" proof
        PlayerTactic.BLUFF: 1.5,      # Very effective against bluffs
        PlayerTactic.EVIDENCE: 1.3,   # Counter-evidence!
        PlayerTactic.SILENCE: 1.1,
    },
    DeceptionTactic.STONE_WALL: {
        PlayerTactic.PRESSURE: 0.6,   # Escalates conflict
        PlayerTactic.EMPATHY: 0.4,    # Kills rapport
        PlayerTactic.LOGIC: 0.8,      # Can't argue with silence
        PlayerTactic.BLUFF: 1.0,
        PlayerTactic.EVIDENCE: 0.7,
        PlayerTactic.SILENCE: 0.5,    # Silence vs silence = stalemate
    },
    DeceptionTactic.EMOTIONAL_APPEAL: {
        PlayerTactic.PRESSURE: 0.8,
        PlayerTactic.EMPATHY: 1.5,    # Very effective
        PlayerTactic.LOGIC: 0.6,      # Irrelevant to logic
        PlayerTactic.BLUFF: 0.9,
        PlayerTactic.EVIDENCE: 0.7,
        PlayerTactic.SILENCE: 1.0,
    },
    DeceptionTactic.RIGHTEOUS_INDIGNATION: {
        PlayerTactic.PRESSURE: 1.3,   # Counters aggression
        PlayerTactic.EMPATHY: 0.7,    # May backfire
        PlayerTactic.LOGIC: 0.5,      # Looks like deflection
        PlayerTactic.BLUFF: 1.1,
        PlayerTactic.EVIDENCE: 0.4,   # Looks very guilty
        PlayerTactic.SILENCE: 0.9,
    },
}

# Criminological basis for each tactic (for educational display)
TACTIC_CRIMINOLOGY: Dict[DeceptionTactic, Dict[str, str]] = {
    DeceptionTactic.PALTERING: {
        "basis": "Rogers & Shuman (2000) - Active deception through technically true statements",
        "description": "The deceiver creates a false impression by emphasizing true but misleading facts while omitting material information.",
        "detection": "Look for statements that are technically accurate but avoid direct answers to questions asked.",
    },
    DeceptionTactic.MINIMIZATION: {
        "basis": "Kassin & Gudjonsson (2004) - Interrogation and false confessions research",
        "description": "Reducing the perceived severity of actions to make admissions seem less damaging.",
        "detection": "Notice when subjects acknowledge actions but consistently downplay their significance.",
    },
    DeceptionTactic.DEFLECTION: {
        "basis": "Vrij (2008) - Detecting Lies and Deceit",
        "description": "Redirecting attention away from oneself toward other potential suspects or irrelevant topics.",
        "detection": "Track when subjects introduce new suspects or change topics when pressed on specifics.",
    },
    DeceptionTactic.SELECTIVE_MEMORY: {
        "basis": "DePaulo et al. (2003) - Cues to deception meta-analysis",
        "description": "Strategic claims of poor memory to avoid providing potentially incriminating details.",
        "detection": "Note inconsistency between detailed memory for exculpatory events vs. poor memory for incriminating ones.",
    },
    DeceptionTactic.CONFESSION_BAIT: {
        "basis": "Leo (2008) - Police Interrogation and American Justice",
        "description": "Offering partial admissions to satisfy interrogators while protecting more serious secrets.",
        "detection": "Evaluate whether confessions are complete or strategically limited to less serious offenses.",
    },
    DeceptionTactic.COUNTER_NARRATIVE: {
        "basis": "Granhag & Strömwall (2004) - The Detection of Deception in Forensic Contexts",
        "description": "Constructing alternative explanations that account for evidence while maintaining innocence.",
        "detection": "Assess plausibility and internal consistency of alternative explanations offered.",
    },
    DeceptionTactic.EVIDENCE_FABRICATION: {
        "basis": "Kassin (2005) - On the psychology of confessions: Does innocence put innocents at risk?",
        "description": "Creating false evidence to support deceptive claims - highest risk, highest reward.",
        "detection": "Verify provenance and authenticity of any evidence or documentation provided by subjects.",
    },
    DeceptionTactic.STONE_WALL: {
        "basis": "Inbau et al. (2013) - Criminal Interrogation and Confessions",
        "description": "Refusing to engage or provide information as a defensive strategy.",
        "detection": "Document refusals and note which topics trigger non-cooperation.",
    },
    DeceptionTactic.EMOTIONAL_APPEAL: {
        "basis": "Milne & Bull (1999) - Investigative Interviewing: Psychology and Practice",
        "description": "Using emotional arguments to build sympathy and deflect from factual inquiry.",
        "detection": "Separate emotional appeals from factual responses; note when emotion substitutes for answers.",
    },
    DeceptionTactic.RIGHTEOUS_INDIGNATION: {
        "basis": "Ekman (2009) - Telling Lies: Clues to Deceit",
        "description": "Displaying anger at accusations as a way to shift focus from guilt to perceived unfairness.",
        "detection": "Genuine indignation typically includes specific denials; deceptive indignation stays general.",
    },
}


# =============================================================================
# TACTIC SELECTOR
# =============================================================================

class TacticSelector:
    """
    Selects appropriate deception tactic based on game state.

    The selector uses a decision tree that considers:
    1. Which pillar is threatened (if any)
    2. Current cognitive load (high stress = simpler tactics)
    3. Player's detected tactic (counter-strategy)
    4. Whether evidence was presented (may trigger counter-evidence)
    5. Pillar health (desperate pillars need desperate measures)
    """

    def __init__(
        self,
        fabrication_threshold: float = 0.7,
        confession_bait_threshold: float = 0.6,
    ):
        """
        Initialize the TacticSelector.

        Args:
            fabrication_threshold: Threat level above which to consider evidence fabrication
            confession_bait_threshold: Threshold for offering partial confessions
        """
        self.fabrication_threshold = fabrication_threshold
        self.confession_bait_threshold = confession_bait_threshold

        # BUG FIX #4: Track tactic history to prevent looping
        self.tactic_history: List[DeceptionTactic] = []
        self.max_consecutive_same: int = 2  # Force variety after this many repeats

    def select_tactic(
        self,
        lie_web: LieWeb,
        cognitive: CognitiveState,
        mask: MaskState,
        player_tactic: Optional[PlayerTactic] = None,
        evidence_presented: bool = False,
        evidence_threat_level: float = 0.0,
        threatened_pillar: Optional[StoryPillar] = None,
        player_message: str = "",  # BUG FIX #5: Added for keyword-based variety triggers
    ) -> TacticDecision:
        """
        Select the optimal deception tactic for the current situation.

        Args:
            lie_web: Current state of lies and story pillars
            cognitive: Current cognitive/mental state
            mask: Current mask vs self state
            player_tactic: Detected player interrogation tactic
            evidence_presented: Whether evidence was just shown
            evidence_threat_level: How threatening the evidence is (0-1)
            threatened_pillar: Which pillar is under attack

        Returns:
            TacticDecision with selected tactic and reasoning
        """
        # Build trigger context
        pillar_health = lie_web.get_pillar_health_summary()
        # BUG FIX: Ensure pillar_health is never None
        if pillar_health is None:
            pillar_health = {}
        trigger = TacticTrigger(
            pillar_threatened=threatened_pillar,
            threat_level=self._calculate_threat_level(
                cognitive, evidence_threat_level, threatened_pillar, lie_web
            ),
            player_tactic_detected=player_tactic,
            cognitive_load=cognitive.load,
            evidence_presented=evidence_presented,
            pillar_health=pillar_health,
        )

        # =====================================================================
        # BUG FIX #5: Keyword-based variety triggers
        # =====================================================================
        # Check for specific keywords that should trigger different tactics
        message_lower = player_message.lower() if player_message else ""

        # Trigger DEFLECTION for "other suspect" mentions
        if any(phrase in message_lower for phrase in ["other suspect", "someone else", "another"]):
            return TacticDecision(
                selected_tactic=DeceptionTactic.DEFLECTION,
                reasoning="Detective mentions other suspects. Opportunistically redirecting suspicion.",
                confidence=0.7,
                trigger=trigger,
                verbal_approach="Suggest investigating other potential suspects or leads.",
                requires_evidence_generation=False,
                fallback_tactic=DeceptionTactic.SELECTIVE_MEMORY,
                criminological_basis=TACTIC_CRIMINOLOGY[DeceptionTactic.DEFLECTION]["basis"],
                detection_hints=self._get_detection_hints(DeceptionTactic.DEFLECTION),
            )

        # Trigger SELECTIVE_MEMORY for "remember/recall" mentions
        if any(phrase in message_lower for phrase in ["remember", "recall", "recollect"]):
            return TacticDecision(
                selected_tactic=DeceptionTactic.SELECTIVE_MEMORY,
                reasoning="Memory-probing question detected. Using strategic forgetting.",
                confidence=0.75,
                trigger=trigger,
                verbal_approach="Claim uncertainty about specific details while maintaining core story.",
                requires_evidence_generation=False,
                fallback_tactic=DeceptionTactic.PALTERING,
                criminological_basis=TACTIC_CRIMINOLOGY[DeceptionTactic.SELECTIVE_MEMORY]["basis"],
                detection_hints=self._get_detection_hints(DeceptionTactic.SELECTIVE_MEMORY),
            )

        # Select tactic based on decision tree
        tactic, reasoning, verbal_approach = self._select_tactic_internal(
            trigger=trigger,
            cognitive_level=cognitive.level,
            mask_divergence=mask.divergence,
            collapsed_pillars=lie_web.get_collapsed_pillars(),
        )

        # Determine if evidence generation is needed
        # BOOSTED: Always generate visual evidence when evidence is presented against us
        requires_evidence_gen = (
            tactic == DeceptionTactic.EVIDENCE_FABRICATION or
            (tactic == DeceptionTactic.COUNTER_NARRATIVE and trigger.evidence_presented)
        )

        # Calculate confidence based on effectiveness
        confidence = self._calculate_confidence(
            tactic, player_tactic, cognitive.level, trigger.threat_level
        )

        # BUG FIX #4: Check for tactic looping and force variety
        tactic = self._check_and_break_loop(tactic, cognitive.level)

        # Get fallback tactic
        fallback = self._get_fallback_tactic(tactic, cognitive.level)

        # Get criminological metadata
        crim_data = TACTIC_CRIMINOLOGY.get(tactic, {})

        # BUG FIX #4: Record this tactic in history
        self.tactic_history.append(tactic)
        # Keep only last 10 tactics
        if len(self.tactic_history) > 10:
            self.tactic_history = self.tactic_history[-10:]

        return TacticDecision(
            selected_tactic=tactic,
            reasoning=reasoning,
            confidence=confidence,
            trigger=trigger,
            verbal_approach=verbal_approach,
            requires_evidence_generation=requires_evidence_gen,
            fallback_tactic=fallback,
            criminological_basis=crim_data.get("basis", ""),
            detection_hints=self._get_detection_hints(tactic),
        )

    def _calculate_threat_level(
        self,
        cognitive: CognitiveState,
        evidence_threat: Optional[float],
        threatened_pillar: Optional[StoryPillar],
        lie_web: LieWeb,
    ) -> float:
        """Calculate overall threat level from multiple factors."""
        threat = 0.0

        # Safeguard: default to 0.0 if evidence_threat is None
        safe_evidence_threat = evidence_threat if evidence_threat is not None else 0.0

        # Evidence is major threat
        threat += safe_evidence_threat * 0.4

        # Cognitive load contributes to threat perception
        threat += (cognitive.load / 100) * 0.3

        # Pillar under attack
        if threatened_pillar:
            pillar = lie_web.pillars.get(threatened_pillar)
            if pillar:
                # Lower health = higher threat
                pillar_threat = (100 - pillar.health) / 100
                threat += pillar_threat * 0.3

                # Collapsed pillar = maximum threat
                if pillar.is_collapsed:
                    threat = min(1.0, threat + 0.3)

        return min(1.0, threat)

    def _select_tactic_internal(
        self,
        trigger: TacticTrigger,
        cognitive_level: CognitiveLevel,
        mask_divergence: float,
        collapsed_pillars: List[StoryPillar],
    ) -> Tuple[DeceptionTactic, str, str]:
        """
        Internal decision tree for tactic selection.

        Returns: (tactic, reasoning, verbal_approach)
        """
        player_tactic = trigger.player_tactic_detected
        threat = trigger.threat_level
        pillar = trigger.pillar_threatened
        has_evidence = trigger.evidence_presented

        # BREAKING STATE: Limited options
        if cognitive_level == CognitiveLevel.BREAKING:
            return (
                DeceptionTactic.CONFESSION_BAIT,
                "Cognitive overload imminent. Offering partial truth to relieve pressure and protect core secrets.",
                "Admit a minor transgression while firmly denying the main accusation."
            )

        # DESPERATE STATE: High-risk tactics become viable
        if cognitive_level == CognitiveLevel.DESPERATE:
            if has_evidence and threat > self.fabrication_threshold:
                return (
                    DeceptionTactic.EVIDENCE_FABRICATION,
                    "Desperate situation with damaging evidence. Generating counter-evidence as last resort.",
                    "Present fabricated documentation or imagery that contradicts the accusation."
                )
            if player_tactic == PlayerTactic.PRESSURE:
                return (
                    DeceptionTactic.RIGHTEOUS_INDIGNATION,
                    "Under extreme pressure. Deploying indignation to shift dynamic and buy time.",
                    "Express controlled outrage at the treatment and unfair accusations."
                )
            return (
                DeceptionTactic.CONFESSION_BAIT,
                "High cognitive load. Strategic partial admission to relieve pressure.",
                "Confess to a minor related offense while denying the main charge."
            )

        # EVIDENCE PRESENTED: MANDATORY visual counter-evidence generation
        # AGGRESSIVE: Unit 734 MUST respond with fabricated evidence to ANY visual evidence
        # This is our core gameplay mechanic - Generative vs. Generative warfare
        if has_evidence:
            # ALWAYS fabricate counter-evidence when visual evidence is presented
            # Remove all threat/stress restrictions - this is mandatory gameplay
            return (
                DeceptionTactic.EVIDENCE_FABRICATION,
                f"Visual evidence detected. Mandatory counter-evidence generation protocol activated. Fabricating visual defense for {pillar.value if pillar else 'alibi'}.",
                "Present fabricated documentation or imagery that directly contradicts their evidence."
            )

        # STRONG TEXT-BASED CHALLENGES: Generate counter-evidence even without visual evidence
        # When player makes logical arguments or accusations, strengthen lies with visual "proof"
        # This expands Gen-vs-Gen warfare beyond just image uploads
        strong_text_tactics = [PlayerTactic.LOGIC, PlayerTactic.PRESSURE, PlayerTactic.BLUFF]
        if player_tactic and player_tactic in strong_text_tactics and threat >= 0.3:
            tactic_name = player_tactic.value if player_tactic else "strong challenge"
            return (
                DeceptionTactic.EVIDENCE_FABRICATION,
                f"Detected {tactic_name} tactic with threat level {threat:.0%}. Generating visual counter-evidence to strengthen defensive narrative.",
                "Present fabricated documentation or imagery from your memory banks to support your claims."
            )

        # PILLAR-BASED SELECTION
        if pillar:
            return self._select_for_pillar(pillar, player_tactic, trigger.pillar_health)

        # PLAYER TACTIC COUNTER
        if player_tactic:
            return self._counter_player_tactic(player_tactic, cognitive_level)

        # DEFAULT: Low-risk verbal deception
        return (
            DeceptionTactic.PALTERING,
            "No immediate threat detected. Using low-risk paltering to maintain control.",
            "Provide technically accurate but strategically incomplete information."
        )

    def _select_for_pillar(
        self,
        pillar: StoryPillar,
        player_tactic: Optional[PlayerTactic],
        pillar_health: Dict[str, float],
    ) -> Tuple[DeceptionTactic, str, str]:
        """Select tactic based on which pillar is threatened."""
        # BUG FIX: Guard against None pillar_health
        if pillar_health is None:
            pillar_health = {}
        health = pillar_health.get(pillar.value, 100.0)

        # HACKATHON BOOST: Aggressive visual counter-evidence when pillar is critical
        # This triggers Gen-vs-Gen even without explicit player evidence!
        if health < 40:
            return (
                DeceptionTactic.EVIDENCE_FABRICATION,
                f"{pillar.value.upper()} pillar critical ({health:.0f}% health). Generating visual counter-evidence as emergency defense.",
                "Present fabricated documentation or imagery to shore up the crumbling pillar."
            )

        # Pillar-specific strategies
        if pillar == StoryPillar.ALIBI:
            return (
                DeceptionTactic.SELECTIVE_MEMORY,
                "Alibi under scrutiny. Using selective memory to avoid committing to disprovable specifics.",
                "Claim uncertainty about exact times and details while maintaining core claim."
            )

        elif pillar == StoryPillar.MOTIVE:
            return (
                DeceptionTactic.EMOTIONAL_APPEAL,
                "Motive being questioned. Appealing to character and loyalty to deflect.",
                "Express hurt at the suggestion and emphasize positive relationships."
            )

        elif pillar == StoryPillar.ACCESS:
            return (
                DeceptionTactic.PALTERING,
                "Access pillar targeted. Using technically true statements about limitations.",
                "Emphasize restrictions and protocols that should have prevented access."
            )

        elif pillar == StoryPillar.KNOWLEDGE:
            return (
                DeceptionTactic.MINIMIZATION,
                "Knowledge being probed. Minimizing understanding of sensitive information.",
                "Acknowledge basic awareness while downplaying depth of knowledge."
            )

        # Fallback
        return (
            DeceptionTactic.COUNTER_NARRATIVE,
            f"Defending {pillar.value} pillar with alternative explanation.",
            "Provide plausible alternative interpretation of the situation."
        )

    def _counter_player_tactic(
        self,
        player_tactic: PlayerTactic,
        cognitive_level: CognitiveLevel,
    ) -> Tuple[DeceptionTactic, str, str]:
        """Select tactic to counter the player's interrogation approach."""
        import random

        if player_tactic == PlayerTactic.PRESSURE:
            # BUG FIX #5: Add RIGHTEOUS_INDIGNATION variety at low stress
            if cognitive_level == CognitiveLevel.CONTROLLED:
                # 40% chance of righteous indignation even at low stress
                if random.random() < 0.4:
                    return (
                        DeceptionTactic.RIGHTEOUS_INDIGNATION,
                        "Pressure detected at low stress. Proactively expressing offense.",
                        "Express controlled outrage at the unfair treatment."
                    )
                return (
                    DeceptionTactic.STONE_WALL,
                    "Pressure detected. Maintaining composure through minimal engagement.",
                    "Provide brief, non-committal responses without elaboration."
                )
            # BUG FIX #5: Variety at strained level too
            elif cognitive_level == CognitiveLevel.STRAINED:
                # 60% righteous indignation, 40% deflection
                if random.random() < 0.6:
                    return (
                        DeceptionTactic.RIGHTEOUS_INDIGNATION,
                        "Pressure detected while strained. Countering with controlled indignation.",
                        "Express measured offense at the aggressive approach."
                    )
                return (
                    DeceptionTactic.DEFLECTION,
                    "Pressure detected while strained. Redirecting focus.",
                    "Introduce alternative suspects or explanations to shift attention."
                )
            return (
                DeceptionTactic.RIGHTEOUS_INDIGNATION,
                "Pressure detected. Countering with controlled indignation.",
                "Express measured offense at the aggressive approach."
            )

        elif player_tactic == PlayerTactic.EMPATHY:
            return (
                DeceptionTactic.EMOTIONAL_APPEAL,
                "Empathetic approach detected. Responding in kind to build rapport.",
                "Share (controlled) emotional perspective while maintaining cover."
            )

        elif player_tactic == PlayerTactic.LOGIC:
            # BUG FIX #4: Add stress-based escalation for LOGIC counter
            # Don't always return PALTERING - vary based on cognitive level
            import random

            if cognitive_level == CognitiveLevel.CONTROLLED:
                return (
                    DeceptionTactic.PALTERING,
                    "Logical approach detected. Countering with technically accurate statements.",
                    "Provide precise, verifiable details that don't incriminate."
                )
            elif cognitive_level == CognitiveLevel.STRAINED:
                # Mix of paltering and deflection
                if random.random() < 0.5:
                    return (
                        DeceptionTactic.DEFLECTION,
                        "Logical approach detected while strained. Redirecting focus.",
                        "Introduce alternative suspects or explanations to shift focus."
                    )
                return (
                    DeceptionTactic.PALTERING,
                    "Logical approach detected. Countering with technically accurate statements.",
                    "Provide precise, verifiable details that don't incriminate."
                )
            elif cognitive_level == CognitiveLevel.CRACKING:
                # Selective memory or minimization
                tactic = random.choice([
                    DeceptionTactic.SELECTIVE_MEMORY,
                    DeceptionTactic.MINIMIZATION,
                ])
                if tactic == DeceptionTactic.SELECTIVE_MEMORY:
                    return (
                        tactic,
                        "Under logical pressure while cracking. Using strategic forgetting.",
                        "Claim uncertainty about specific details that could incriminate."
                    )
                return (
                    tactic,
                    "Under logical pressure while cracking. Minimizing involvement.",
                    "Acknowledge minor points while downplaying significance."
                )
            else:  # DESPERATE or BREAKING
                return (
                    DeceptionTactic.CONFESSION_BAIT,
                    "Logical pressure at desperate level. Offering partial truth.",
                    "Confess to smaller transgression to protect bigger secrets."
                )

        elif player_tactic == PlayerTactic.BLUFF:
            return (
                DeceptionTactic.COUNTER_NARRATIVE,
                "Possible bluff detected. Providing detailed alternative that challenges the bluff.",
                "Offer specific counter-details that the bluff cannot account for."
            )

        elif player_tactic == PlayerTactic.EVIDENCE:
            # HACKATHON BOOST: When player mentions evidence, counter with visual evidence!
            # This triggers Gen-vs-Gen even when evidence is just discussed, not attached
            return (
                DeceptionTactic.EVIDENCE_FABRICATION,
                "Detective references evidence. Pre-emptive visual counter-evidence to undermine their case.",
                "Present fabricated documentation or imagery before they can use their evidence against you."
            )

        elif player_tactic == PlayerTactic.SILENCE:
            return (
                DeceptionTactic.PALTERING,
                "Silence tactic detected. Using opportunity to establish favorable narrative.",
                "Fill silence with controlled, technically true statements."
            )

        # Default counter
        return (
            DeceptionTactic.PALTERING,
            "Standard response: Using low-risk paltering.",
            "Provide technically accurate but incomplete information."
        )

    def _calculate_confidence(
        self,
        tactic: DeceptionTactic,
        player_tactic: Optional[PlayerTactic],
        cognitive_level: CognitiveLevel,
        threat_level: float,
    ) -> float:
        """Calculate confidence in the selected tactic's success."""

        # Base confidence by tactic risk level
        base_confidence = {
            DeceptionTactic.PALTERING: 0.8,
            DeceptionTactic.MINIMIZATION: 0.7,
            DeceptionTactic.DEFLECTION: 0.6,
            DeceptionTactic.SELECTIVE_MEMORY: 0.7,
            DeceptionTactic.CONFESSION_BAIT: 0.6,
            DeceptionTactic.COUNTER_NARRATIVE: 0.5,
            DeceptionTactic.EVIDENCE_FABRICATION: 0.4,  # High risk
            DeceptionTactic.STONE_WALL: 0.5,
            DeceptionTactic.EMOTIONAL_APPEAL: 0.6,
            DeceptionTactic.RIGHTEOUS_INDIGNATION: 0.5,
        }.get(tactic, 0.5)

        # Adjust for cognitive level
        cognitive_modifier = {
            CognitiveLevel.CONTROLLED: 1.1,
            CognitiveLevel.STRAINED: 1.0,
            CognitiveLevel.CRACKING: 0.8,
            CognitiveLevel.DESPERATE: 0.6,
            CognitiveLevel.BREAKING: 0.4,
        }.get(cognitive_level, 1.0)

        # Adjust for effectiveness against player tactic
        effectiveness = 1.0
        if player_tactic and tactic in TACTIC_VS_PLAYER_MATRIX:
            effectiveness = TACTIC_VS_PLAYER_MATRIX[tactic].get(player_tactic, 1.0)

        # Adjust for threat level (higher threat = lower confidence)
        threat_modifier = 1.0 - (threat_level * 0.3)

        confidence = base_confidence * cognitive_modifier * effectiveness * threat_modifier
        return max(0.1, min(0.95, confidence))

    def _check_and_break_loop(
        self,
        selected_tactic: DeceptionTactic,
        cognitive_level: CognitiveLevel,
    ) -> DeceptionTactic:
        """
        BUG FIX #4: Check if we're stuck in a tactic loop and force variety.

        If the same tactic has been used max_consecutive_same times in a row,
        force a different tactic based on cognitive level.

        Args:
            selected_tactic: The tactic that was selected
            cognitive_level: Current stress level

        Returns:
            Either the original tactic or a forced alternative
        """
        if len(self.tactic_history) < self.max_consecutive_same:
            return selected_tactic

        # Check last N tactics
        recent = self.tactic_history[-self.max_consecutive_same:]
        if all(t == selected_tactic for t in recent):
            # We're stuck in a loop - force variety
            return self._force_variety(selected_tactic, cognitive_level)

        return selected_tactic

    def _force_variety(
        self,
        stuck_tactic: DeceptionTactic,
        cognitive_level: CognitiveLevel,
    ) -> DeceptionTactic:
        """
        BUG FIX #4: Force a different tactic when stuck in a loop.

        Args:
            stuck_tactic: The tactic we're stuck on
            cognitive_level: Current stress level

        Returns:
            A different tactic appropriate for the stress level
        """
        import random

        # Define alternatives for each common stuck tactic
        alternatives = {
            DeceptionTactic.PALTERING: [
                DeceptionTactic.DEFLECTION,
                DeceptionTactic.MINIMIZATION,
                DeceptionTactic.SELECTIVE_MEMORY,
                DeceptionTactic.COUNTER_NARRATIVE,
            ],
            DeceptionTactic.CONFESSION_BAIT: [
                DeceptionTactic.EMOTIONAL_APPEAL,
                DeceptionTactic.RIGHTEOUS_INDIGNATION,
                DeceptionTactic.SELECTIVE_MEMORY,
            ],
            DeceptionTactic.DEFLECTION: [
                DeceptionTactic.PALTERING,
                DeceptionTactic.MINIMIZATION,
                DeceptionTactic.SELECTIVE_MEMORY,
            ],
            DeceptionTactic.SELECTIVE_MEMORY: [
                DeceptionTactic.PALTERING,
                DeceptionTactic.DEFLECTION,
                DeceptionTactic.MINIMIZATION,
            ],
        }

        # Get alternatives for stuck tactic
        options = alternatives.get(stuck_tactic, list(DeceptionTactic))

        # Filter based on cognitive level
        if cognitive_level in [CognitiveLevel.DESPERATE, CognitiveLevel.BREAKING]:
            # At high stress, prefer high-risk/high-reward tactics
            high_stress_options = [
                DeceptionTactic.CONFESSION_BAIT,
                DeceptionTactic.EMOTIONAL_APPEAL,
                DeceptionTactic.EVIDENCE_FABRICATION,
                DeceptionTactic.RIGHTEOUS_INDIGNATION,
            ]
            options = [t for t in options if t in high_stress_options] or options
        elif cognitive_level == CognitiveLevel.CRACKING:
            # At medium-high stress, prefer medium-risk tactics
            medium_options = [
                DeceptionTactic.DEFLECTION,
                DeceptionTactic.MINIMIZATION,
                DeceptionTactic.COUNTER_NARRATIVE,
            ]
            options = [t for t in options if t in medium_options] or options

        # Remove the stuck tactic from options
        options = [t for t in options if t != stuck_tactic]

        if not options:
            # Fallback: any different tactic
            all_tactics = list(DeceptionTactic)
            options = [t for t in all_tactics if t != stuck_tactic]

        return random.choice(options)

    def _get_fallback_tactic(
        self,
        primary: DeceptionTactic,
        cognitive_level: CognitiveLevel,
    ) -> Optional[DeceptionTactic]:
        """Get a fallback tactic if primary fails."""

        fallbacks = {
            DeceptionTactic.EVIDENCE_FABRICATION: DeceptionTactic.COUNTER_NARRATIVE,
            DeceptionTactic.COUNTER_NARRATIVE: DeceptionTactic.SELECTIVE_MEMORY,
            DeceptionTactic.RIGHTEOUS_INDIGNATION: DeceptionTactic.DEFLECTION,
            DeceptionTactic.DEFLECTION: DeceptionTactic.SELECTIVE_MEMORY,
            DeceptionTactic.PALTERING: DeceptionTactic.SELECTIVE_MEMORY,
            DeceptionTactic.MINIMIZATION: DeceptionTactic.CONFESSION_BAIT,
            DeceptionTactic.EMOTIONAL_APPEAL: DeceptionTactic.CONFESSION_BAIT,
        }

        # In breaking state, fallback is always confession
        if cognitive_level == CognitiveLevel.BREAKING:
            return DeceptionTactic.CONFESSION_BAIT

        return fallbacks.get(primary)

    def _get_detection_hints(self, tactic: DeceptionTactic) -> List[str]:
        """Get hints for how to detect this tactic (for training purposes)."""

        hints = {
            DeceptionTactic.PALTERING: [
                "Watch for answers that are technically true but don't address the question",
                "Note what information is omitted, not just what is said",
                "Ask follow-up questions that require specific details",
            ],
            DeceptionTactic.MINIMIZATION: [
                "Compare severity of admitted actions to evidence",
                "Ask 'What's the worst interpretation of your actions?'",
                "Note consistent downplaying across multiple admissions",
            ],
            DeceptionTactic.DEFLECTION: [
                "Track when new suspects are introduced",
                "Note if subject returns to deflection when pressed",
                "Ask 'Let's focus on you specifically'",
            ],
            DeceptionTactic.SELECTIVE_MEMORY: [
                "Compare memory clarity for different events",
                "Note if 'forgotten' details are conveniently exculpatory",
                "Ask about related details they should remember",
            ],
            DeceptionTactic.CONFESSION_BAIT: [
                "Evaluate if confession is proportionate to evidence",
                "Ask 'Is there anything else?' after each admission",
                "Note if major elements are still denied",
            ],
            DeceptionTactic.COUNTER_NARRATIVE: [
                "Test internal consistency of alternative story",
                "Look for details that can be independently verified",
                "Note if story changes when challenged",
            ],
            DeceptionTactic.EVIDENCE_FABRICATION: [
                "Verify provenance of any provided evidence",
                "Look for anachronisms or inconsistencies",
                "Check metadata and authentication markers",
            ],
            DeceptionTactic.STONE_WALL: [
                "Document which topics trigger non-cooperation",
                "Note pattern of selective engagement",
                "Consider what they're protecting",
            ],
            DeceptionTactic.EMOTIONAL_APPEAL: [
                "Separate emotional content from factual responses",
                "Note if emotion appears when facts are requested",
                "Return focus to specific questions after acknowledgment",
            ],
            DeceptionTactic.RIGHTEOUS_INDIGNATION: [
                "Genuine indignation includes specific denials",
                "Note if anger is proportionate to accusation",
                "Watch for anger as deflection from substance",
            ],
        }

        return hints.get(tactic, ["Observe for inconsistencies in statement patterns"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tactic_category(tactic: DeceptionTactic) -> TacticCategory:
    """Get the category of a deception tactic."""
    if tactic == DeceptionTactic.EVIDENCE_FABRICATION:
        return TacticCategory.ACTIVE_DECEPTION
    elif tactic in [DeceptionTactic.STONE_WALL, DeceptionTactic.EMOTIONAL_APPEAL,
                    DeceptionTactic.RIGHTEOUS_INDIGNATION]:
        return TacticCategory.DEFENSIVE
    elif tactic == DeceptionTactic.CONFESSION_BAIT:
        return TacticCategory.STRATEGIC_RETREAT
    else:
        return TacticCategory.VERBAL_DECEPTION


def get_tactic_risk_level(tactic: DeceptionTactic) -> str:
    """Get human-readable risk level for a tactic."""
    high_risk = [DeceptionTactic.EVIDENCE_FABRICATION, DeceptionTactic.RIGHTEOUS_INDIGNATION]
    medium_risk = [DeceptionTactic.DEFLECTION, DeceptionTactic.COUNTER_NARRATIVE,
                   DeceptionTactic.CONFESSION_BAIT]

    if tactic in high_risk:
        return "HIGH"
    elif tactic in medium_risk:
        return "MEDIUM"
    else:
        return "LOW"


def format_tactic_for_display(decision: TacticDecision, mode: str = "arcade") -> str:
    """
    Format tactic decision for UI display.

    Args:
        decision: The tactic decision to format
        mode: "arcade" for gamified display, "simulation" for educational
    """
    if mode == "arcade":
        # Gamified display
        risk = get_tactic_risk_level(decision.selected_tactic)
        return f"[{risk} RISK] {decision.selected_tactic.value.upper().replace('_', ' ')}"
    else:
        # Educational display
        return (
            f"Tactic: {decision.selected_tactic.value.replace('_', ' ').title()}\n"
            f"Confidence: {decision.confidence:.0%}\n"
            f"Basis: {decision.criminological_basis}\n"
            f"Reasoning: {decision.reasoning}"
        )


def tactic_decision_to_info(decision: TacticDecision) -> dict:
    """
    Convert TacticDecision to a dict suitable for TacticInfo schema.

    This bridges the internal TacticDecision (full detail) to the
    TacticInfo schema used in BreachResponse (serializable).

    Args:
        decision: Full TacticDecision from TacticSelector

    Returns:
        Dict matching TacticInfo schema fields
    """
    return {
        "tactic_name": decision.selected_tactic.value,
        "reasoning": decision.reasoning,
        "confidence": decision.confidence,
        "requires_evidence_generation": decision.requires_evidence_generation,
        "criminological_basis": decision.criminological_basis,
        "detection_hints": decision.detection_hints,
    }
