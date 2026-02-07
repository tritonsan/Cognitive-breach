"""Core game logic for BreachEngine."""

from breach_engine.core.psychology import (
    BreachPsychology,
    LieWeb,
    LieNode,
    LiePillar,
    CognitiveState,
    MaskState,
    VulnerabilityProfile,
    Secret,
    StoryPillar,
    CognitiveLevel,
    PlayerTactic,
    EmotionType,
    SecretLevel,
    create_unit_734_psychology,
)

from breach_engine.core.manager import (
    BreachManager,
    TacticDetector,
    ImpactCalculator,
    ProcessedInput,
)

from breach_engine.core.evidence import (
    EvidenceAnalyzer,
    EvidenceAnalysisResult,
    EvidenceImpact,
    EvidenceImpactCalculator,
    EvidenceType,
    PillarDamage,
    DetectedObject,
    get_evidence_analyzer,
)

from breach_engine.core.effects import apply_glitch_effect, get_glitch_css

# NEW: Scientific Deception Engine (Tactics System)
from breach_engine.core.tactics import (
    DeceptionTactic,
    TacticCategory,
    TacticTrigger,
    TacticDecision,
    TacticSelector,
    TACTIC_VS_PLAYER_MATRIX,
    TACTIC_CRIMINOLOGY,
    get_tactic_category,
    get_tactic_risk_level,
    format_tactic_for_display,
    tactic_decision_to_info,
)

# NEW: Visual Deception System (Phase 2)
from breach_engine.core.visual_generator import (
    VisualGenerator,
    CounterEvidenceType,
    FabricationRisk,
    FabricationContext,
    create_fabrication_context,
    should_trigger_fabrication,
    POVGenerator,  # NEW: First-person counter-evidence
)

# NEW: Forensics Lab - Dynamic Player Evidence (Phase 2.5)
from breach_engine.core.forensics_lab import (
    ForensicsLab,
    EvidenceRequestType,
    EvidenceRegistry,
    EvidenceRequestParser,
    GeneratedEvidenceRecord,
    create_forensics_lab,
    format_evidence_for_ui,
)

# NEW: Lie Ledger System - Narrative Consistency Tracking
from breach_engine.core.lie_ledger import (
    LieLedger,
    LedgerEntry,
    Contradiction,
    ClaimType,
    infer_pillar_from_claim,
)

# NEW: POV Vision System - First-Person Evidence Perception
from breach_engine.core.pov_vision import (
    POVFormatter,
    POVPerception,
    EvidenceReaction,
    format_pov_for_prompt,
    create_pov_perception,
)

# NEW: Shadow Analyst - Scientific Interrogation Analysis
from breach_engine.core.shadow_analyst import (
    ShadowAnalyst,
    AnalystInsight,
    ReidPhase,
    PeacePhase,
    IMTViolation,
    AggressionLevel,
    TACTIC_TO_SCIENCE,
    REID_COUNTER_TACTICS,
    format_analyst_advice_for_prompt,
    get_shadow_analyst,
)

# NEW: Supervisor Debrief - Post-Session Audio Analysis
from breach_engine.core.supervisor_debrief import (
    SupervisorDebrief,
    get_supervisor_debrief,
)

__all__ = [
    # Psychology models
    "BreachPsychology",
    "LieWeb",
    "LieNode",
    "LiePillar",
    "CognitiveState",
    "MaskState",
    "VulnerabilityProfile",
    "Secret",
    # Enums
    "StoryPillar",
    "CognitiveLevel",
    "PlayerTactic",
    "EmotionType",
    "SecretLevel",
    # Factory
    "create_unit_734_psychology",
    # Manager
    "BreachManager",
    "TacticDetector",
    "ImpactCalculator",
    "ProcessedInput",
    # Evidence
    "EvidenceAnalyzer",
    "EvidenceAnalysisResult",
    "EvidenceImpact",
    "EvidenceImpactCalculator",
    "EvidenceType",
    "PillarDamage",
    "DetectedObject",
    "get_evidence_analyzer",
    # Effects
    "apply_glitch_effect",
    "get_glitch_css",
    # Tactics (Scientific Deception Engine)
    "DeceptionTactic",
    "TacticCategory",
    "TacticTrigger",
    "TacticDecision",
    "TacticSelector",
    "TACTIC_VS_PLAYER_MATRIX",
    "TACTIC_CRIMINOLOGY",
    "get_tactic_category",
    "get_tactic_risk_level",
    "format_tactic_for_display",
    "tactic_decision_to_info",
    # Visual Deception System (Phase 2)
    "VisualGenerator",
    "CounterEvidenceType",
    "FabricationRisk",
    "FabricationContext",
    "create_fabrication_context",
    "should_trigger_fabrication",
    "POVGenerator",
    # Forensics Lab (Phase 2.5)
    "ForensicsLab",
    "EvidenceRequestType",
    "EvidenceRegistry",
    "EvidenceRequestParser",
    "GeneratedEvidenceRecord",
    "create_forensics_lab",
    "format_evidence_for_ui",
    # Lie Ledger System
    "LieLedger",
    "LedgerEntry",
    "Contradiction",
    "ClaimType",
    "infer_pillar_from_claim",
    # POV Vision System
    "POVFormatter",
    "POVPerception",
    "EvidenceReaction",
    "format_pov_for_prompt",
    "create_pov_perception",
    # Shadow Analyst (Scientific Interrogation Analysis)
    "ShadowAnalyst",
    "AnalystInsight",
    "ReidPhase",
    "PeacePhase",
    "IMTViolation",
    "AggressionLevel",
    "TACTIC_TO_SCIENCE",
    "REID_COUNTER_TACTICS",
    "format_analyst_advice_for_prompt",
    "get_shadow_analyst",
    # Supervisor Debrief (Post-Session Audio Analysis)
    "SupervisorDebrief",
    "get_supervisor_debrief",
]
