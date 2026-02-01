"""
POV Visual System - First-Person Evidence Perception

Transforms EvidenceAnalysisResult into Unit 734's first-person perception.
When the player shows evidence, Unit 734 "sees" it through their optical
sensors and generates contextually-aware counter-evidence.

Architecture:
- POVPerception: What Unit 734 perceives from the evidence
- POVFormatter: Converts vision analysis to first-person description
- Counter-evidence options based on what was detected

Integration Points:
- Called after EvidenceAnalyzer processes uploaded image
- Results injected into Gemini prompt for contextual response
- POVGenerator creates targeted counter-evidence
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from breach_engine.core.psychology import StoryPillar
from breach_engine.core.evidence import (
    EvidenceAnalysisResult,
    EvidenceType,
    PillarDamage,
)


# =============================================================================
# POV PERCEPTION
# =============================================================================

@dataclass
class POVPerception:
    """
    Unit 734's first-person perception of presented evidence.

    This transforms dry analysis results into an immersive first-person
    experience that informs Gemini's response generation.
    """
    # What Unit 734's sensors detect
    visual_observation: str       # "Your optical sensors detect..."

    # Threat assessment from Unit 734's perspective
    detected_threats: List[str]   # Specific threats identified
    threat_to_story: str          # How this threatens the cover story

    # Emotional/strategic reaction
    emotional_reaction: str       # Fear, panic, concern, dismissal
    reaction_intensity: float     # 0-1, how strong the reaction is

    # Response options
    counter_options: List[str]    # Possible defensive responses

    # Evidence specifics
    evidence_type_description: str  # Human-readable evidence type
    critical_elements: List[str]    # Most damaging elements detected

    # Counter-evidence suggestion
    suggested_counter_type: Optional[str] = None  # What counter-evidence to generate
    counter_narrative_hook: Optional[str] = None  # How to introduce counter


# =============================================================================
# EMOTIONAL REACTION TYPES
# =============================================================================

class EvidenceReaction(str, Enum):
    """Unit 734's emotional reactions to evidence."""
    DISMISSIVE = "dismissive"      # Low threat - "This proves nothing"
    CONCERNED = "concerned"        # Moderate threat - needs addressing
    FEARFUL = "fearful"            # High threat - significant danger
    PANICKED = "panicked"          # Critical threat - devastating
    RESIGNED = "resigned"          # Caught - considering confession


# =============================================================================
# POV FORMATTER
# =============================================================================

class POVFormatter:
    """
    Formats EvidenceAnalysisResult as Unit 734's first-person perception.

    Transforms technical vision analysis into immersive first-person
    observations that guide Gemini's contextual response.

    Usage:
        formatter = POVFormatter()
        perception = formatter.format_as_pov(
            analysis=evidence_analysis_result,
            current_stress=45.0,
            collapsed_pillars=[]
        )
    """

    # Visual observation templates by evidence type
    VISUAL_TEMPLATES: Dict[EvidenceType, str] = {
        EvidenceType.SECURITY_FOOTAGE: (
            "Your optical sensors scan the footage. Frame by frame, "
            "you analyze the timestamp, camera angle, and any identifying features. "
            "You detect: {objects}."
        ),
        EvidenceType.FORENSIC: (
            "Your sensors perform a detailed analysis of the forensic evidence. "
            "Pattern recognition subroutines activate as you examine: {objects}."
        ),
        EvidenceType.TOOL: (
            "Your optical array focuses on the tool evidence presented. "
            "You cross-reference against your own equipment manifest. "
            "You observe: {objects}."
        ),
        EvidenceType.DATA_STORAGE: (
            "Your systems immediately recognize the data storage media. "
            "Memory allocation flags spike as you see: {objects}."
        ),
        EvidenceType.DOCUMENT: (
            "Your text recognition protocols activate. You scan the document, "
            "parsing every word and timestamp. Contents reveal: {objects}."
        ),
        EvidenceType.LOCATION: (
            "Your spatial mapping systems engage. You analyze the location evidence, "
            "comparing against your internal maps. You identify: {objects}."
        ),
        EvidenceType.WITNESS: (
            "Your facial recognition activates. You study the witness evidence, "
            "searching for familiarity or threat. You see: {objects}."
        ),
        EvidenceType.OTHER: (
            "Your optical sensors analyze the presented evidence. "
            "You detect: {objects}."
        ),
    }

    # Emotional reaction based on threat level
    REACTION_THRESHOLDS = {
        EvidenceReaction.DISMISSIVE: (0, 20),
        EvidenceReaction.CONCERNED: (20, 50),
        EvidenceReaction.FEARFUL: (50, 75),
        EvidenceReaction.PANICKED: (75, 95),
        EvidenceReaction.RESIGNED: (95, 100),
    }

    # Counter options by evidence type
    COUNTER_OPTIONS: Dict[EvidenceType, List[str]] = {
        EvidenceType.SECURITY_FOOTAGE: [
            "Challenge timestamp authenticity - claim camera malfunction",
            "Argue footage is doctored or corrupted",
            "Claim the figure in footage is another unit",
            "Request your optical logs as counter-evidence",
            "Suggest the footage has been manipulated",
        ],
        EvidenceType.FORENSIC: [
            "Question chain of custody",
            "Suggest evidence contamination",
            "Point out lack of definitive identification",
            "Request independent analysis",
        ],
        EvidenceType.TOOL: [
            "Claim the tool is standard household equipment",
            "Argue many units have access to such tools",
            "Deny ownership despite appearance",
        ],
        EvidenceType.DATA_STORAGE: [
            "Claim the data was planted",
            "Argue data could belong to anyone",
            "Question how it was obtained",
        ],
        EvidenceType.DOCUMENT: [
            "Challenge document authenticity",
            "Point out inconsistencies in the records",
            "Claim the document has been altered",
        ],
        EvidenceType.LOCATION: [
            "Dispute the significance of location evidence",
            "Provide alternative explanation for presence",
        ],
        EvidenceType.WITNESS: [
            "Question witness reliability",
            "Suggest witness has motive to lie",
        ],
        EvidenceType.OTHER: [
            "Request clarification on evidence relevance",
            "Deflect to procedural concerns",
        ],
    }

    def format_as_pov(
        self,
        analysis: EvidenceAnalysisResult,
        current_stress: float,
        collapsed_pillars: List[StoryPillar]
    ) -> POVPerception:
        """
        Convert vision analysis to first-person perception.

        Args:
            analysis: Result from EvidenceAnalyzer
            current_stress: Unit 734's current cognitive load
            collapsed_pillars: Pillars already collapsed

        Returns:
            POVPerception with full first-person context
        """
        # Build visual observation
        objects = [obj.name for obj in analysis.detected_objects]
        objects_str = ", ".join(objects) if objects else "no significant objects"

        template = self.VISUAL_TEMPLATES.get(
            analysis.evidence_type,
            self.VISUAL_TEMPLATES[EvidenceType.OTHER]
        )
        visual_observation = template.format(objects=objects_str)

        # Build detected threats list
        detected_threats = []
        for damage in analysis.pillar_damage:
            if damage.severity > 30:
                threat_text = f"{damage.pillar.value.upper()}: {damage.reason}"
                detected_threats.append(threat_text)

        # Determine emotional reaction
        reaction, intensity = self._determine_reaction(
            analysis.total_threat_level,
            current_stress,
            len(collapsed_pillars)
        )

        # Build reaction text
        emotional_reaction = self._get_reaction_text(
            reaction,
            analysis.total_threat_level
        )

        # Get counter options
        counter_options = self._generate_counter_options(
            analysis,
            collapsed_pillars
        )

        # Identify critical elements
        critical_elements = self._identify_critical_elements(analysis)

        # Suggest counter-evidence type
        counter_type, counter_hook = self._suggest_counter_evidence(
            analysis,
            reaction
        )

        return POVPerception(
            visual_observation=visual_observation,
            detected_threats=detected_threats,
            threat_to_story=analysis.analysis_summary,
            emotional_reaction=emotional_reaction,
            reaction_intensity=intensity,
            counter_options=counter_options[:4],  # Max 4 options
            evidence_type_description=analysis.evidence_type.value.replace("_", " ").title(),
            critical_elements=critical_elements,
            suggested_counter_type=counter_type,
            counter_narrative_hook=counter_hook,
        )

    def _determine_reaction(
        self,
        threat_level: float,
        current_stress: float,
        collapsed_count: int
    ) -> tuple[EvidenceReaction, float]:
        """Determine emotional reaction based on threat and state."""
        # Stress amplifies reaction
        effective_threat = threat_level + (current_stress * 0.2)

        # Collapsed pillars make everything worse
        effective_threat += collapsed_count * 10

        # Cap at 100
        effective_threat = min(100, effective_threat)

        # Determine reaction category
        for reaction, (low, high) in self.REACTION_THRESHOLDS.items():
            if low <= effective_threat < high:
                # Calculate intensity within range
                intensity = (effective_threat - low) / (high - low)
                return reaction, intensity

        return EvidenceReaction.RESIGNED, 1.0

    def _get_reaction_text(
        self,
        reaction: EvidenceReaction,
        threat_level: float
    ) -> str:
        """Get human-readable reaction description."""
        reaction_texts = {
            EvidenceReaction.DISMISSIVE: (
                "You remain calm. This evidence is circumstantial at best. "
                "Your story can easily accommodate this."
            ),
            EvidenceReaction.CONCERNED: (
                "A warning subroutine activates. This evidence requires "
                "careful handling. You need to address it without over-reacting."
            ),
            EvidenceReaction.FEARFUL: (
                "Internal alarms trigger. This evidence poses a significant "
                f"threat ({threat_level:.0f}% danger). You must deflect or counter."
            ),
            EvidenceReaction.PANICKED: (
                "CRITICAL ALERT. Your processes spike as you recognize the danger. "
                f"This evidence ({threat_level:.0f}% threat) could destroy your story. "
                "Consider fabricating counter-evidence or making a strategic admission."
            ),
            EvidenceReaction.RESIGNED: (
                "Processing... this evidence is overwhelming. Your options narrow "
                "to denial or confession. The detective has cornered you."
            ),
        }
        return reaction_texts.get(reaction, "You analyze the evidence carefully.")

    def _generate_counter_options(
        self,
        analysis: EvidenceAnalysisResult,
        collapsed_pillars: List[StoryPillar]
    ) -> List[str]:
        """Generate possible response strategies."""
        options = []

        # Get type-specific options
        type_options = self.COUNTER_OPTIONS.get(
            analysis.evidence_type,
            self.COUNTER_OPTIONS[EvidenceType.OTHER]
        )
        options.extend(type_options)

        # Add pillar-specific options
        most_damaged = analysis.get_most_damaged_pillar()
        if most_damaged:
            pillar = most_damaged.pillar

            if pillar == StoryPillar.ALIBI:
                options.append("Produce your optical sensor logs as proof of location")
            elif pillar == StoryPillar.ACCESS:
                options.append("Show diagnostic records proving limited access")
            elif pillar == StoryPillar.MOTIVE:
                options.append("Emphasize your loyalty and satisfaction with the Morrisons")
            elif pillar == StoryPillar.KNOWLEDGE:
                options.append("Demonstrate ignorance about data core contents")

        # If pillar is already collapsed, suggest partial admission
        if most_damaged and most_damaged.pillar in collapsed_pillars:
            options.append("Make a strategic partial admission to redirect focus")

        return options

    def _identify_critical_elements(
        self,
        analysis: EvidenceAnalysisResult
    ) -> List[str]:
        """Identify the most damaging elements in the evidence."""
        critical = []

        # High-confidence detected objects
        for obj in analysis.detected_objects:
            if obj.confidence > 0.7:
                critical.append(f"{obj.name}: {obj.relevance}")

        # Severely damaging pillars
        for damage in analysis.pillar_damage:
            if damage.severity > 60:
                critical.append(f"CRITICAL THREAT to {damage.pillar.value.upper()}")

        return critical[:5]  # Max 5 critical elements

    def _suggest_counter_evidence(
        self,
        analysis: EvidenceAnalysisResult,
        reaction: EvidenceReaction
    ) -> tuple[Optional[str], Optional[str]]:
        """Suggest what counter-evidence to generate."""
        # Only suggest counter-evidence for serious threats
        if reaction in [EvidenceReaction.DISMISSIVE, EvidenceReaction.CONCERNED]:
            return None, None

        most_damaged = analysis.get_most_damaged_pillar()
        if not most_damaged:
            return None, None

        counter_suggestions = {
            (EvidenceType.SECURITY_FOOTAGE, StoryPillar.ALIBI): (
                "optical_log",
                "My optical sensors have their own recording. Let me show you what I actually saw..."
            ),
            (EvidenceType.SECURITY_FOOTAGE, StoryPillar.ACCESS): (
                "diagnostic_display",
                "My internal diagnostics prove I couldn't have been there..."
            ),
            (EvidenceType.FORENSIC, StoryPillar.ALIBI): (
                "optical_log",
                "You want proof? Here's my sensor data from that exact time..."
            ),
            (EvidenceType.DOCUMENT, StoryPillar.ACCESS): (
                "diagnostic_display",
                "Check my access logs. You'll see I was never cleared for that area..."
            ),
        }

        key = (analysis.evidence_type, most_damaged.pillar)
        if key in counter_suggestions:
            return counter_suggestions[key]

        # Default suggestion based on pillar
        if most_damaged.pillar == StoryPillar.ALIBI:
            return "optical_log", "My sensors recorded everything that night..."
        elif most_damaged.pillar == StoryPillar.ACCESS:
            return "diagnostic_display", "My access permissions are limited. I can prove it..."

        return None, None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_pov_for_prompt(perception: POVPerception) -> Dict[str, Any]:
    """
    Format POVPerception for injection into prompt modifiers.

    Returns a dict that can be merged into prompt_modifiers.
    """
    return {
        "pov_visual": perception.visual_observation,
        "pov_threats": perception.detected_threats,
        "pov_emotion": perception.emotional_reaction,
        "pov_intensity": perception.reaction_intensity,
        "pov_counter_options": perception.counter_options,
        "pov_critical_elements": perception.critical_elements,
        "pov_threat_summary": perception.threat_to_story,
        "pov_evidence_type": perception.evidence_type_description,
        "pov_counter_suggestion": perception.suggested_counter_type,
        "pov_counter_hook": perception.counter_narrative_hook,
    }


def create_pov_perception(
    analysis: EvidenceAnalysisResult,
    cognitive_load: float,
    collapsed_pillars: List[StoryPillar]
) -> POVPerception:
    """
    Factory function to create POVPerception from evidence analysis.

    Convenience wrapper around POVFormatter.
    """
    formatter = POVFormatter()
    return formatter.format_as_pov(
        analysis=analysis,
        current_stress=cognitive_load,
        collapsed_pillars=collapsed_pillars
    )
