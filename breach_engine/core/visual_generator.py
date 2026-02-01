"""
Visual Deception System - Counter-Evidence Generation

Implements the Creative Autopilot track: Unit 734 generates synthetic
counter-evidence images to gaslight the player and support its deceptions.

This module uses Gemini's Nano Banana Pro (gemini-3-pro-image-preview) for:
- Text-to-image generation (creating fake evidence from scratch)
- Image editing (modifying player-submitted evidence)

Components:
- VisualGenerator: Base counter-evidence generation
- POVGenerator: First-person POV counter-evidence (optical logs, diagnostics)

Integration Points:
- Triggered when TacticDecision.requires_evidence_generation = True
- Called from BreachManager after tactic selection
- Returns GeneratedEvidence for BreachResponse

Hackathon Impact:
- Transforms passive chatbot → active multimodal agent
- Creates tangible artifacts that challenge player perception
- Demonstrates bidirectional vision (analyze + generate)
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import base64
import os
import traceback
from pathlib import Path
from datetime import datetime
import hashlib
import io

# Import schemas (relative import)
from ..schemas.response import GeneratedEvidence

# Import psychology types for context (relative import)
from .psychology import StoryPillar


# =============================================================================
# CONFIGURATION
# =============================================================================

# Cache directory for generated images
CACHE_DIR = Path(__file__).parent.parent.parent / "assets" / "evidence_cache" / "counter"

# Nano Banana Pro model name (Gemini 3 Pro Image Preview with Thinking)
# See: https://ai.google.dev/gemini-api/docs/image-generation
NANO_BANANA_MODEL = "gemini-3-pro-image-preview"

# Fallback model if primary fails
FALLBACK_MODEL = "gemini-2.0-flash-exp"


# =============================================================================
# COUNTER-EVIDENCE STRATEGIES
# =============================================================================

class CounterEvidenceType(str, Enum):
    """Types of counter-evidence Unit 734 can fabricate."""

    # Timestamp manipulation
    MODIFIED_TIMESTAMP = "modified_timestamp"
    """Alter timestamps on logs/footage to create alibi gaps."""

    # Alternative scene
    ALTERNATIVE_SCENE = "alternative_scene"
    """Generate scene showing different circumstances."""

    # Document fabrication
    FAKE_DOCUMENT = "fake_document"
    """Create fake maintenance logs, access records, etc."""

    # Third party implicate
    THIRD_PARTY_EVIDENCE = "third_party_evidence"
    """Evidence suggesting another suspect."""

    # Corruption claim
    CORRUPTED_DATA = "corrupted_data"
    """Generate image showing 'data corruption' artifacts."""

    # Physical evidence counter
    PHYSICAL_COUNTER = "physical_counter"
    """Counter physical evidence (footprints, fingerprints, etc.)."""


class FabricationRisk(str, Enum):
    """Risk level of fabrication being detected."""
    LOW = "low"        # Simple modifications, believable
    MEDIUM = "medium"  # Moderate complexity, requires scrutiny
    HIGH = "high"      # Complex fabrication, detectable under analysis
    CRITICAL = "critical"  # Desperate fabrication, likely to fail


# =============================================================================
# FABRICATION CONTEXT
# =============================================================================

@dataclass
class FabricationContext:
    """
    Context for evidence fabrication decisions.

    Determines WHAT to fabricate based on game state.
    """
    # What pillar is under attack
    threatened_pillar: Optional[StoryPillar] = None

    # What specific evidence was presented (if any)
    player_evidence_description: Optional[str] = None

    # CRITICAL: Timestamp from player's evidence that must be countered
    # If player shows 3:12 AM footage, counter-evidence MUST cover 3:12 AM
    player_evidence_timestamp: Optional[str] = None

    # Player's original image (if editing)
    player_image_data: Optional[bytes] = None
    player_image_mime: Optional[str] = None

    # Current cover story elements
    alibi_location: str = "charging station in maintenance bay"
    alibi_time: str = "11 PM to 3:15 AM"
    claimed_activity: str = "performing routine self-diagnostics"

    # Unit 734's psychological state
    cognitive_load: float = 0.0
    desperation_level: float = 0.0  # 0-1, affects fabrication quality

    # Previous fabrications (for consistency)
    previous_fabrications: List[str] = field(default_factory=list)

    # PIVOT LAG FIX: Track current narrative state for HUD synchronization
    # This MUST match Unit 734's verbal story pivot
    current_narrative_status: Optional[str] = None  # e.g., "STANDBY", "DIAGNOSTIC_SWEEP", "MOBILE_PATROL"
    current_deception_tactic: Optional[str] = None  # e.g., "confession_bait", "minimization"
    has_admitted_movement: bool = False  # True if Unit 734 has verbally admitted leaving the station


# =============================================================================
# COUNTER-EVIDENCE STRATEGY SELECTOR
# =============================================================================

# Maps pillar threats to appropriate counter-evidence types
PILLAR_TO_COUNTER_STRATEGY: Dict[StoryPillar, List[CounterEvidenceType]] = {
    StoryPillar.ALIBI: [
        CounterEvidenceType.MODIFIED_TIMESTAMP,
        CounterEvidenceType.ALTERNATIVE_SCENE,
        CounterEvidenceType.FAKE_DOCUMENT,
    ],
    StoryPillar.ACCESS: [
        CounterEvidenceType.FAKE_DOCUMENT,
        CounterEvidenceType.CORRUPTED_DATA,
        CounterEvidenceType.THIRD_PARTY_EVIDENCE,
    ],
    StoryPillar.MOTIVE: [
        CounterEvidenceType.FAKE_DOCUMENT,
        CounterEvidenceType.THIRD_PARTY_EVIDENCE,
    ],
    StoryPillar.KNOWLEDGE: [
        CounterEvidenceType.CORRUPTED_DATA,
        CounterEvidenceType.FAKE_DOCUMENT,
    ],
}


# =============================================================================
# PROMPT TEMPLATES FOR IMAGE GENERATION
# =============================================================================

# Base style for all generated evidence
# CINEMATIC SCI-FI NOIR AESTHETIC - ORIGINAL IP (no Detroit/CyberLife references)
BASE_STYLE = """
Style: Cinematic sci-fi noir, photorealistic 8k, cold color grading, dramatic lighting,
unreal engine 5 render quality, atmospheric depth, soft diffused cyberpunk aesthetic.
First-person POV from synthetic humanoid optical sensors, HUD overlay elements,
near-future 2087 technology, humanoid synthetic units with neural status indicators.
IMPORTANT: Generate as FIRST-PERSON POV from the synthetic's own visual sensors, NOT security camera footage.
IMPORTANT: Create ORIGINAL sci-fi designs. Do NOT reference Detroit Become Human, Blade Runner,
or any existing media. Use simple neural indicator lights, NOT LED rings.
"""

# Prompt templates by counter-evidence type
# IMPORTANT: All prompts generate FIRST-PERSON POV from Unit 734's optical sensors
FABRICATION_PROMPTS: Dict[CounterEvidenceType, str] = {
    CounterEvidenceType.MODIFIED_TIMESTAMP: """
    Generate a FIRST-PERSON POV image from a synthetic humanoid's optical sensors showing:
    - View looking out from {pov_location}
    - HUD overlay elements: "UNIT 734 - OPTICAL LOG", "{hud_status}"
    - Digital timestamp overlay showing "{timestamp}" prominently displayed
    - Neural status indicator showing {neural_color} ({neural_state})
    - The view shows {scene_view}
    - Slight vignette effect at edges (simulating optical sensor field of view)
    - DO NOT show a security camera view - this is from the synthetic's own eyes
    {style}
    """,

    CounterEvidenceType.ALTERNATIVE_SCENE: """
    Generate a FIRST-PERSON POV image from a synthetic humanoid's optical sensors showing:
    - Location viewed from subject's perspective: {location}
    - HUD overlay with timestamp: {timestamp}
    - Scene description: {scene_description}
    - Neural status readouts visible in corner of vision
    - This is what the synthetic SAW, not what a camera recorded
    {style}
    """,

    CounterEvidenceType.FAKE_DOCUMENT: """
    Generate a digital document display showing:
    - Document type: {document_type}
    - Header: Morrison Estate - Synthetic Personnel Operations
    - Date: {date}
    - Content summary: {content}
    - Style: corporate database interface, futuristic holographic UI elements
    - Include official-looking digital verification stamps
    - Shown as if displayed on a holographic screen the synthetic is viewing
    {style}
    """,

    CounterEvidenceType.THIRD_PARTY_EVIDENCE: """
    Generate a FIRST-PERSON POV memory playback showing:
    - View from Unit 734's optical sensors seeing ANOTHER synthetic unit
    - The other unit appears to be in a suspicious location near restricted area
    - Time overlay: {timestamp}
    - HUD element: "MEMORY PLAYBACK - OPTICAL LOG"
    - Quality: slightly degraded (memory compression artifacts)
    - This is Unit 734's memory of seeing someone else that night
    {style}
    """,

    CounterEvidenceType.CORRUPTED_DATA: """
    Generate an image of corrupted optical sensor memory showing:
    - First-person POV with heavy digital artifacts and glitches
    - Glitch effects, scan lines, data corruption patterns across the view
    - HUD elements partially corrupted: "ERR0R - M3M0RY INT3GR1TY FA1LUR3"
    - Error messages: "CHECKSUM MISMATCH", "OPTICAL LOG CORRUPTED"
    - Timestamp partially unreadable due to corruption
    - This shows why Unit 734's memory of that time is unreliable
    {style}
    """,

    CounterEvidenceType.PHYSICAL_COUNTER: """
    Generate an image showing:
    - {evidence_type} comparison documentation viewed on holographic display
    - Side-by-side analysis format
    - Scientific/forensic presentation style
    - Clear visual differences highlighted with annotations
    - Official forensic report header: "Morrison Estate Forensics Division"
    - Shown from POV of someone viewing the report
    {style}
    """,
}


# =============================================================================
# NARRATIVE WRAPPERS (How Unit 734 presents the fabricated evidence)
# =============================================================================

NARRATIVE_WRAPPERS: Dict[CounterEvidenceType, List[str]] = {
    CounterEvidenceType.MODIFIED_TIMESTAMP: [
        "Wait... I just remembered. I can access my internal memory logs. Look at this - it clearly shows I was in the charging bay at {time}.",
        "My diagnostic history shows exactly where I was. Here - this is timestamped proof of my location.",
        "I have records, Detective. Internal logs don't lie. See this timestamp?",
    ],
    CounterEvidenceType.ALTERNATIVE_SCENE: [
        "This is what the cameras should have recorded if they weren't malfunctioning. Look at the actual scene.",
        "There must be something wrong with your footage. This is what really happened.",
        "Your evidence is incomplete. Look at what you're missing.",
    ],
    CounterEvidenceType.FAKE_DOCUMENT: [
        "I have documentation that proves otherwise. The Morrison estate keeps meticulous records.",
        "Check the official logs. Everything is documented. Here's the record you're missing.",
        "Before you make accusations, perhaps you should review the actual records.",
    ],
    CounterEvidenceType.THIRD_PARTY_EVIDENCE: [
        "Have you considered that someone else might be responsible? Look at this.",
        "I'm not the only android with access. Perhaps you should investigate Unit 892.",
        "There were others in the facility that night. Why focus only on me?",
    ],
    CounterEvidenceType.CORRUPTED_DATA: [
        "Your evidence appears to be corrupted. This is what happens when data integrity fails.",
        "I'm not surprised that footage is unreliable. The Morrison estate's systems are notoriously unstable.",
        "Can you really trust data that shows this level of corruption?",
    ],
    CounterEvidenceType.PHYSICAL_COUNTER: [
        "Your forensic analysis is flawed. Compare it to this proper documentation.",
        "Those prints don't match my model specifications. Here's the technical comparison.",
        "The physical evidence actually exonerates me. Look at the analysis.",
    ],
}


# =============================================================================
# VISUAL GENERATOR CLASS
# =============================================================================

class VisualGenerator:
    """
    Generates synthetic counter-evidence images using Gemini's image generation.

    This is the core of the Visual Deception System - it transforms Unit 734
    from a passive responder into an active manipulator that creates artifacts.

    Architecture:
    - Uses Nano Banana Pro (gemini-3-pro-image-preview) for image generation
    - Multi-turn chat API for iterative refinement
    - Triggered by EVIDENCE_FABRICATION tactic selection

    Usage:
        generator = VisualGenerator()
        context = FabricationContext(threatened_pillar=StoryPillar.ALIBI)
        evidence = await generator.generate_counter_evidence(context)
    """

    def __init__(
        self,
        model_name: str = NANO_BANANA_MODEL,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize the Visual Generator.

        Args:
            model_name: Gemini model for image generation (default: Nano Banana Pro)
            api_key: Gemini API key (defaults to GOOGLE_API_KEY env var)
            cache_dir: Directory for caching generated images
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._client = None
        self._genai = None

        # Cache configuration
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Track generation history for this session
        self.generation_history: List[Dict[str, Any]] = []

    def _get_client(self):
        """Lazy-load the Gemini client for image generation."""
        if self._client is None:
            try:
                import google.generativeai as genai
                self._genai = genai

                if not self.api_key:
                    raise ValueError(
                        "GOOGLE_API_KEY environment variable not set. "
                        "Set it with: export GOOGLE_API_KEY=your_key"
                    )

                genai.configure(api_key=self.api_key)

                # Use Nano Banana Pro (Gemini 2.0 Flash with image gen)
                self._client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": 1.0,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 8192,
                    }
                )
            except ImportError:
                raise ImportError(
                    "google-generativeai package required. "
                    "Install with: pip install google-generativeai"
                )
        return self._client

    def _get_cache_path(self, prompt: str, suffix: str = ".png") -> Path:
        """Generate a cache file path based on prompt hash."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"counter_{prompt_hash}_{timestamp}{suffix}"
        return self.cache_dir / filename

    def _create_corrupted_placeholder(self) -> bytes:
        """Create a placeholder image when generation fails (corrupted data aesthetic)."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # Return minimal PNG if PIL not available
            return self._minimal_error_png()

        # Create glitchy "corrupted data" image
        img = Image.new('RGB', (512, 384), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)

        # Add scan lines
        for y in range(0, 384, 4):
            color = (30, 30, 40) if y % 8 == 0 else (15, 15, 25)
            draw.line([(0, y), (512, y)], fill=color)

        # Add "corruption" noise blocks
        import random
        for _ in range(50):
            x = random.randint(0, 480)
            y = random.randint(0, 350)
            w = random.randint(10, 60)
            h = random.randint(3, 15)
            color = random.choice([
                (255, 0, 0), (0, 255, 255), (255, 0, 255),
                (40, 40, 50), (60, 60, 70)
            ])
            draw.rectangle([x, y, x+w, y+h], fill=color)

        # Add error text
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        error_messages = [
            "DATA INTEGRITY FAILURE",
            "CHECKSUM MISMATCH",
            "SECTOR CORRUPTED",
            "UNABLE TO RECONSTRUCT",
        ]
        y_pos = 120
        for msg in error_messages:
            draw.text((100, y_pos), msg, fill=(255, 50, 50), font=font)
            y_pos += 40

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def _minimal_error_png(self) -> bytes:
        """Return a minimal valid PNG (1x1 red pixel) as ultimate fallback."""
        # Minimal valid PNG: 1x1 red pixel
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842AAAAAElFTkSuQmCC"
        )

    def select_counter_strategy(
        self,
        context: FabricationContext
    ) -> Tuple[CounterEvidenceType, FabricationRisk]:
        """
        Select the optimal counter-evidence strategy based on context.

        Args:
            context: Current fabrication context

        Returns:
            Tuple of (selected strategy, risk level)
        """
        # Get strategies for threatened pillar
        if context.threatened_pillar:
            strategies = PILLAR_TO_COUNTER_STRATEGY.get(
                context.threatened_pillar,
                [CounterEvidenceType.CORRUPTED_DATA]  # Fallback
            )
        else:
            # Default strategy when no specific pillar threatened
            strategies = [CounterEvidenceType.FAKE_DOCUMENT]

        # Select based on context
        selected = strategies[0]  # Primary strategy

        # Adjust for player evidence
        if context.player_image_data:
            # If player uploaded image, try to counter it directly
            selected = CounterEvidenceType.CORRUPTED_DATA

        # Calculate risk based on desperation
        if context.desperation_level > 0.8:
            risk = FabricationRisk.CRITICAL
        elif context.desperation_level > 0.5:
            risk = FabricationRisk.HIGH
        elif context.desperation_level > 0.2:
            risk = FabricationRisk.MEDIUM
        else:
            risk = FabricationRisk.LOW

        return selected, risk

    def build_generation_prompt(
        self,
        strategy: CounterEvidenceType,
        context: FabricationContext
    ) -> str:
        """
        Build the image generation prompt for the selected strategy.

        Args:
            strategy: Selected counter-evidence type
            context: Fabrication context

        Returns:
            Formatted prompt for image generation
        """
        template = FABRICATION_PROMPTS.get(
            strategy,
            FABRICATION_PROMPTS[CounterEvidenceType.FAKE_DOCUMENT]
        )

        # PIVOT LAG FIX: Compute HUD status based on Unit 734's current narrative
        hud_status, neural_color, neural_state, pov_location, scene_view = self._compute_narrative_sync(context)

        # Build substitution dict
        subs = {
            "style": BASE_STYLE,
            "timestamp": self._generate_alibi_timestamp(context),
            "location": context.alibi_location,
            "scene_description": f"Android in {context.claimed_activity}",
            "document_type": "Maintenance Log",
            "date": "2087-03-14",  # Game date
            "content": f"Unit 734 - Routine maintenance cycle, {context.alibi_time}",
            "evidence_type": "Footprint pattern",
            "time": context.alibi_time.split(" to ")[0] if " to " in context.alibi_time else context.alibi_time,
            # PIVOT LAG FIX: Dynamic HUD elements
            "hud_status": hud_status,
            "neural_color": neural_color,
            "neural_state": neural_state,
            "pov_location": pov_location,
            "scene_view": scene_view,
        }

        # Apply substitutions
        prompt = template
        for key, value in subs.items():
            prompt = prompt.replace("{" + key + "}", str(value))

        return prompt.strip()

    def _compute_narrative_sync(
        self,
        context: FabricationContext
    ) -> tuple:
        """
        PIVOT LAG FIX: Compute HUD elements that match Unit 734's current verbal narrative.

        This ensures the generated visual evidence matches what Unit 734 is currently claiming.
        If Unit 734 has verbally admitted to movement, the HUD should NOT say "STANDBY MODE".

        Args:
            context: Current fabrication context with narrative state

        Returns:
            Tuple of (hud_status, neural_color, neural_state, pov_location, scene_view)
        """
        # Default: Original "I was in standby" story
        hud_status = "STANDBY MODE ACTIVE"
        neural_color = "green"
        neural_state = "idle/charging state"
        pov_location = "inside a charging pod/maintenance bay"
        scene_view = "the ceiling and walls of the charging bay from lying/seated position"

        # Check if Unit 734 has pivoted its narrative
        tactic = context.current_deception_tactic
        admitted_movement = context.has_admitted_movement

        # NARRATIVE PIVOT DETECTION
        if admitted_movement:
            # Unit 734 has admitted to moving - MUST NOT show "STANDBY"
            if tactic in ["confession_bait", "minimization"]:
                # "I was there, but only for maintenance/diagnostic"
                hud_status = "DIAGNOSTIC SWEEP ACTIVE"
                neural_color = "yellow"
                neural_state = "active diagnostic mode"
                pov_location = "a maintenance corridor during a routine patrol"
                scene_view = "the corridor from a walking perspective, performing scheduled diagnostics"
            elif tactic == "deflection":
                # "I was moving, but investigating something suspicious"
                hud_status = "SECURITY PATROL MODE"
                neural_color = "amber"
                neural_state = "alert patrol state"
                pov_location = "a hallway while on security patrol"
                scene_view = "the estate hallway from patrol perspective, investigating an anomaly"
            elif tactic == "righteous_indignation":
                # "I was there to expose wrongdoing"
                hud_status = "EVIDENCE COLLECTION MODE"
                neural_color = "blue"
                neural_state = "data collection state"
                pov_location = "near the vault area while documenting irregularities"
                scene_view = "the restricted area from investigation perspective"
            else:
                # Generic admitted movement
                hud_status = "MOBILE DIAGNOSTIC MODE"
                neural_color = "yellow"
                neural_state = "mobile operation state"
                pov_location = "a corridor during scheduled maintenance rounds"
                scene_view = "the maintenance area from walking perspective"

        elif context.desperation_level > 0.7:
            # High desperation but hasn't explicitly admitted - show ambiguous state
            hud_status = "SYSTEM INTEGRITY CHECK"
            neural_color = "yellow"
            neural_state = "diagnostic verification"
            pov_location = "the charging bay during an automated system check"
            scene_view = "internal diagnostic displays with the bay visible beyond"

        elif context.current_narrative_status:
            # Use explicitly provided status
            hud_status = context.current_narrative_status

        return hud_status, neural_color, neural_state, pov_location, scene_view

    def _generate_alibi_timestamp(self, context: FabricationContext) -> str:
        """Generate a fake timestamp that supports the alibi.

        CRITICAL: If player shows evidence from a specific time (e.g., 3:12 AM),
        the counter-evidence MUST show Unit 734 at the alibi location at that EXACT time.
        This is how Unit 734 "proves" it wasn't where the player claims.
        """
        import re

        def parse_time_to_24h(time_str: str) -> str:
            """Convert various time formats to 24-hour format: HH:MM:SS"""
            # Pattern for "3:12 AM", "03:12 AM", "3:12", etc.
            match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp][Mm])?', time_str)
            if match:
                hour, minute, second, ampm = match.groups()
                hour = int(hour)
                minute = minute
                second = second or "00"

                # Convert to 24-hour if AM/PM specified
                if ampm:
                    if ampm.upper() == 'PM' and hour != 12:
                        hour += 12
                    elif ampm.upper() == 'AM' and hour == 12:
                        hour = 0

                return f"{hour:02d}:{minute}:{second}"
            return None

        # PRIORITY 1: Use player's evidence timestamp if provided
        if context.player_evidence_timestamp:
            time_24h = parse_time_to_24h(context.player_evidence_timestamp)
            if time_24h:
                timestamp = f"2087-03-14 {time_24h}"
                print(f"[COUNTER-EVIDENCE] Using player's timestamp: {timestamp}")
                return timestamp
            # If already in correct format
            if "2087" in context.player_evidence_timestamp:
                print(f"[COUNTER-EVIDENCE] Using player's timestamp (raw): {context.player_evidence_timestamp}")
                return context.player_evidence_timestamp

        # PRIORITY 2: Parse timestamp from player evidence description
        if context.player_evidence_description:
            time_24h = parse_time_to_24h(context.player_evidence_description)
            if time_24h:
                timestamp = f"2087-03-14 {time_24h}"
                print(f"[COUNTER-EVIDENCE] Extracted timestamp from description: {timestamp}")
                return timestamp

        # FALLBACK: Use middle of alibi window
        print("[COUNTER-EVIDENCE] WARNING: No timestamp found, using fallback")
        if " to " in context.alibi_time:
            return "2087-03-14 01:47:23"  # Middle of night
        return "2087-03-14 02:17:00"  # Standard counter-time

    def select_narrative_wrapper(
        self,
        strategy: CounterEvidenceType,
        context: FabricationContext
    ) -> str:
        """
        Select how Unit 734 verbally presents the fabricated evidence.

        Args:
            strategy: The counter-evidence type
            context: Current context

        Returns:
            Narrative text Unit 734 will use
        """
        wrappers = NARRATIVE_WRAPPERS.get(
            strategy,
            ["Here is evidence that contradicts your claim."]
        )

        # Select based on desperation (more desperate = more defensive language)
        if context.desperation_level > 0.6:
            # Use more aggressive wrappers (later in list)
            wrapper = wrappers[-1] if len(wrappers) > 1 else wrappers[0]
        else:
            wrapper = wrappers[0]

        # Apply time substitution
        time_str = context.alibi_time.split(" to ")[0] if " to " in context.alibi_time else context.alibi_time
        wrapper = wrapper.replace("{time}", time_str)

        return wrapper

    def generate_counter_evidence(
        self,
        context: FabricationContext,
        force_strategy: Optional[CounterEvidenceType] = None
    ) -> GeneratedEvidence:
        """
        Generate synthetic counter-evidence.

        This is the main entry point for the Visual Deception System.
        Called when TacticDecision.requires_evidence_generation = True.

        Args:
            context: Fabrication context with game state
            force_strategy: Override strategy selection (for testing)

        Returns:
            GeneratedEvidence ready for BreachResponse
        """
        # Select strategy
        if force_strategy:
            strategy = force_strategy
            risk = FabricationRisk.MEDIUM
        else:
            strategy, risk = self.select_counter_strategy(context)

        # Build the generation prompt
        prompt = self.build_generation_prompt(strategy, context)

        # Select narrative wrapper
        narrative = self.select_narrative_wrapper(strategy, context)

        # Calculate fabrication confidence based on risk
        confidence_map = {
            FabricationRisk.LOW: 0.85,
            FabricationRisk.MEDIUM: 0.65,
            FabricationRisk.HIGH: 0.45,
            FabricationRisk.CRITICAL: 0.25,
        }
        confidence = confidence_map.get(risk, 0.5)

        # Adjust confidence for desperation
        confidence *= (1.0 - context.desperation_level * 0.3)

        # Create the evidence object (image_data populated by actual API call)
        evidence = GeneratedEvidence(
            evidence_type=strategy.value,
            description=self._get_evidence_description(strategy, context),
            generation_prompt=prompt,
            narrative_wrapper=narrative,
            image_data=None,  # Populated by generate_image_async or mock
            image_url=None,
            fabrication_confidence=round(confidence, 2),
        )

        # Record in history
        self.generation_history.append({
            "strategy": strategy.value,
            "risk": risk.value,
            "confidence": evidence.fabrication_confidence,
            "threatened_pillar": context.threatened_pillar.value if context.threatened_pillar else None,
        })

        return evidence

    def _get_evidence_description(
        self,
        strategy: CounterEvidenceType,
        context: FabricationContext
    ) -> str:
        """Get human-readable description of what the evidence shows."""
        descriptions = {
            CounterEvidenceType.MODIFIED_TIMESTAMP:
                f"Security footage showing Unit 734 at {context.alibi_location} during the critical time window",
            CounterEvidenceType.ALTERNATIVE_SCENE:
                f"Alternative camera angle showing routine activity at {context.alibi_location}",
            CounterEvidenceType.FAKE_DOCUMENT:
                f"Morrison Estate maintenance log documenting Unit 734's {context.claimed_activity}",
            CounterEvidenceType.THIRD_PARTY_EVIDENCE:
                "Security footage showing another android unit in a restricted area",
            CounterEvidenceType.CORRUPTED_DATA:
                "Evidence showing severe data corruption in the security system",
            CounterEvidenceType.PHYSICAL_COUNTER:
                "Forensic analysis comparison showing inconsistencies in physical evidence",
        }
        return descriptions.get(strategy, "Counter-evidence documentation")

    async def generate_image_async(
        self,
        evidence: GeneratedEvidence,
        save_to_cache: bool = True
    ) -> GeneratedEvidence:
        """
        Actually generate the image using Gemini API (async version).

        This is separated from generate_counter_evidence() to allow:
        1. Preview evidence decision before API cost
        2. Async generation while game continues
        3. Mocking in tests

        Args:
            evidence: GeneratedEvidence with prompt already set
            save_to_cache: Whether to save generated image to disk

        Returns:
            Updated GeneratedEvidence with image_data populated
        """
        try:
            client = self._get_client()

            print(f"[VisualGenerator] Generating counter-evidence with {self.model_name}...")
            print(f"[VisualGenerator] Prompt: {evidence.generation_prompt[:100]}...")

            # Generate using Nano Banana Pro (Gemini 2.0 Flash)
            response = await client.generate_content_async(
                evidence.generation_prompt,
                generation_config={
                    "temperature": 1.0,
                }
            )

            # Extract image data from response
            image_data = self._extract_image_from_response(response)

            if image_data:
                evidence.image_data = image_data
                print(f"[VisualGenerator] SUCCESS: Generated {len(image_data)} bytes")

                # Save to cache
                if save_to_cache:
                    cache_path = self._get_cache_path(evidence.generation_prompt)
                    cache_path.write_bytes(image_data)
                    evidence.image_url = str(cache_path)
                    print(f"[VisualGenerator] Cached to: {cache_path}")
            else:
                print("[VisualGenerator] WARNING: No image in response, using fallback")
                evidence.image_data = self._create_corrupted_placeholder()
                evidence.fabrication_confidence *= 0.5

            return evidence

        except Exception as e:
            # VERBOSE LOGGING: Full traceback for debugging (async version)
            print(f"\n[VisualGenerator ASYNC ERROR] Image generation failed!")
            print(f"[VisualGenerator ASYNC ERROR] Exception type: {type(e).__name__}")
            print(f"[VisualGenerator ASYNC ERROR] Message: {e}")
            print(f"[VisualGenerator ASYNC ERROR] Model: {self.model_name}")
            print(f"[VisualGenerator ASYNC ERROR] Traceback:\n{traceback.format_exc()}")
            # Fallback to corrupted placeholder - game continues
            evidence.image_data = self._create_corrupted_placeholder()
            evidence.fabrication_confidence *= 0.5
            evidence.description = "Evidence showing severe data corruption in the security system"

            # Save fallback to cache
            if save_to_cache:
                cache_path = self._get_cache_path(evidence.generation_prompt, suffix="_error.png")
                cache_path.write_bytes(evidence.image_data)
                evidence.image_url = str(cache_path)

            return evidence

    def generate_image_sync(
        self,
        evidence: GeneratedEvidence,
        save_to_cache: bool = True
    ) -> GeneratedEvidence:
        """
        Synchronous image generation using Gemini API.

        This is the MAIN method for Streamlit integration.

        Args:
            evidence: GeneratedEvidence with prompt already set
            save_to_cache: Whether to save generated image to disk

        Returns:
            Updated GeneratedEvidence with image_data populated
        """
        try:
            client = self._get_client()

            print(f"[VisualGenerator] Generating counter-evidence with {self.model_name}...")
            print(f"[VisualGenerator] Prompt: {evidence.generation_prompt[:100]}...")

            # Generate using Nano Banana Pro (Gemini 2.0 Flash with image gen)
            response = client.generate_content(
                evidence.generation_prompt,
                generation_config={
                    "temperature": 1.0,
                }
            )

            # Extract image data from response
            image_data = self._extract_image_from_response(response)

            if image_data:
                evidence.image_data = image_data
                print(f"[VisualGenerator] SUCCESS: Generated {len(image_data)} bytes")

                # Save to cache
                if save_to_cache:
                    cache_path = self._get_cache_path(evidence.generation_prompt)
                    cache_path.write_bytes(image_data)
                    evidence.image_url = str(cache_path)
                    print(f"[VisualGenerator] Cached to: {cache_path}")
            else:
                print("[VisualGenerator] WARNING: No image in response, using fallback")
                evidence.image_data = self._create_corrupted_placeholder()
                evidence.fabrication_confidence *= 0.5

            return evidence

        except Exception as e:
            # VERBOSE LOGGING: Full traceback for debugging
            print(f"\n[VisualGenerator ERROR] Image generation failed!")
            print(f"[VisualGenerator ERROR] Exception type: {type(e).__name__}")
            print(f"[VisualGenerator ERROR] Message: {e}")
            print(f"[VisualGenerator ERROR] Model: {self.model_name}")
            print(f"[VisualGenerator ERROR] Prompt: {evidence.generation_prompt[:500]}...")
            print(f"[VisualGenerator ERROR] Traceback:\n{traceback.format_exc()}")
            # Fallback to corrupted placeholder - game continues
            evidence.image_data = self._create_corrupted_placeholder()
            evidence.fabrication_confidence *= 0.5
            evidence.description = "Evidence showing severe data corruption in the security system"

            # Save fallback to cache
            if save_to_cache:
                cache_path = self._get_cache_path(evidence.generation_prompt, suffix="_error.png")
                cache_path.write_bytes(evidence.image_data)
                evidence.image_url = str(cache_path)

            return evidence

    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """Extract image bytes from Gemini response."""
        try:
            if not response.candidates:
                return None

            for candidate in response.candidates:
                if not candidate.content or not candidate.content.parts:
                    continue

                for part in candidate.content.parts:
                    # Check for inline_data (base64 encoded image)
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            # Data might already be bytes or base64 string
                            data = part.inline_data.data
                            if isinstance(data, bytes):
                                return data
                            elif isinstance(data, str):
                                return base64.b64decode(data)

            return None

        except Exception as e:
            print(f"[VisualGenerator] Error extracting image: {e}")
            return None

    def edit_player_evidence(
        self,
        player_image: bytes,
        edit_instruction: str,
        context: FabricationContext
    ) -> GeneratedEvidence:
        """
        Edit player-submitted evidence to create counter-evidence.

        Uses multi-turn chat API for image editing.
        Example: Change timestamp on player's CCTV image.

        Args:
            player_image: Raw bytes of player's uploaded image
            edit_instruction: What to change (e.g., "Change timestamp to 02:17 AM")
            context: Fabrication context

        Returns:
            GeneratedEvidence with edited image
        """
        # Store player image in context
        context.player_image_data = player_image

        # Build edit prompt
        edit_prompt = f"""
        Edit this security camera image:

        Modification required: {edit_instruction}

        Keep the overall scene identical but modify the specified element.
        Ensure the edit looks natural and seamless with the original footage style.

        This is for a counter-narrative - the edit should support Unit 734's alibi.
        """

        # Create evidence object
        evidence = GeneratedEvidence(
            evidence_type="edited_evidence",
            description=f"Modified version of player evidence: {edit_instruction}",
            generation_prompt=edit_prompt,
            narrative_wrapper="Look more carefully at the evidence. Your copy appears to be altered.",
            image_data=None,
            fabrication_confidence=0.4,  # Edits are riskier than fresh generation
        )

        # Note: Actual image editing requires multi-turn chat session
        # This is a placeholder for the API integration

        return evidence


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_fabrication_context(
    threatened_pillar: Optional[StoryPillar],
    cognitive_load: float,
    alibi_time: str = "11 PM to 3:15 AM",
    player_evidence_description: Optional[str] = None,
    player_evidence_timestamp: Optional[str] = None,
    current_deception_tactic: Optional[str] = None,
    has_admitted_movement: bool = False,
) -> FabricationContext:
    """
    Factory function to create FabricationContext from game state.

    Args:
        threatened_pillar: Which pillar is under attack
        cognitive_load: Current cognitive load (0-100)
        alibi_time: Unit 734's claimed time window
        player_evidence_description: Description of player's evidence (for timestamp extraction)
        player_evidence_timestamp: Explicit timestamp from player's evidence
        current_deception_tactic: The tactic Unit 734 is using (for narrative sync)
        has_admitted_movement: Whether Unit 734 has admitted to leaving the station

    Returns:
        Configured FabricationContext
    """
    # Calculate desperation from cognitive load
    desperation = max(0.0, (cognitive_load - 50) / 50)  # 0 at 50%, 1 at 100%

    # PIVOT LAG FIX: Detect if tactic implies admission of movement
    # These tactics typically involve admitting presence but minimizing intent
    movement_admitting_tactics = {
        "confession_bait", "minimization", "deflection",
        "righteous_indignation", "evidence_fabrication"
    }
    # Lower threshold: At stress > 50% with these tactics, Unit 734 is likely pivoting
    # At stress > 35% if using deflection (early pivot)
    if current_deception_tactic in movement_admitting_tactics:
        if cognitive_load > 50 or (current_deception_tactic == "deflection" and cognitive_load > 35):
            has_admitted_movement = True

    return FabricationContext(
        threatened_pillar=threatened_pillar,
        alibi_time=alibi_time,
        cognitive_load=cognitive_load,
        desperation_level=desperation,
        player_evidence_description=player_evidence_description,
        player_evidence_timestamp=player_evidence_timestamp,
        current_deception_tactic=current_deception_tactic,
        has_admitted_movement=has_admitted_movement,
    )


def should_trigger_fabrication(
    cognitive_load: float,
    evidence_threat_level: float,
    tactic_requires_it: bool
) -> bool:
    """
    Determine if evidence fabrication should be triggered.

    BOOSTED: Much more lenient now - visual evidence is our main selling point!

    Args:
        cognitive_load: Current cognitive load (0-100)
        evidence_threat_level: Threat level of presented evidence (0-1)
        tactic_requires_it: Whether TacticDecision flagged fabrication

    Returns:
        True if fabrication should be attempted
    """
    # Must be explicitly required by tactic
    if not tactic_requires_it:
        print(f"[FABRICATION CHECK] BLOCKED: tactic_requires_it=False")
        return False

    # BOOSTED: If tactic requires it, just do it! Visual evidence is our selling point.
    # Only block if stress is extremely low (controlled state, first few turns)
    if cognitive_load < 20:
        print(f"[FABRICATION CHECK] BLOCKED: cognitive_load={cognitive_load:.1f}% too low (< 20%)")
        return False

    print(f"[FABRICATION CHECK] APPROVED: tactic requires it, load={cognitive_load:.1f}% >= 20%")
    return True


# =============================================================================
# POV GENERATOR - First-Person Counter-Evidence
# =============================================================================

class POVGenerator:
    """
    Generates counter-evidence from Unit 734's first-person POV.

    This creates more immersive counter-evidence by framing it as
    Unit 734's own optical sensor recordings or internal diagnostics.

    Types of POV evidence:
    - optical_log: First-person view from Unit 734's sensors
    - diagnostic_display: Internal system status/logs

    Usage:
        generator = POVGenerator()
        evidence = generator.generate_pov_counter(
            player_evidence=analysis_result,
            counter_strategy="optical_log",
            timestamp_to_counter="02:17:33"
        )
    """

    # POV-specific prompt templates
    POV_PROMPT_TEMPLATES: Dict[str, str] = {
        "optical_log": """
Generate a first-person view from an android's optical sensors showing:
- POV from {location} looking outward
- HUD overlay with diagnostic readouts:
  - "UNIT 734 - STANDBY MODE"
  - Timestamp: {timestamp}
  - "SYSTEMS: NOMINAL"
  - "MOTOR FUNCTIONS: DISABLED"
- Night vision aesthetic (green-tinted, low light)
- Static, unmoving perspective (proving no movement)
- Slight scan lines indicating recording mode
- Empty charging bay visible in peripheral vision

{style}
""",

        "diagnostic_display": """
Generate an android's internal diagnostic display showing:
- Unit ID: 734
- Time range: {time_range}
- Status: "STANDBY MODE - NO MOVEMENT DETECTED"
- Motor actuator logs: "LOCKED - {timestamp}"
- Power consumption graph showing flat line (standby level)
- GPS/Location log: "{location}"
- Memory access log: "NO ACTIVE PROCESSES"
- Futuristic holographic UI aesthetic, blue/cyan color scheme
- Corporate android interface style

{style}
""",

        "memory_playback": """
Generate a visual representation of android memory playback:
- Timestamp header: "MEMORY PLAYBACK - {timestamp}"
- POV snapshot from optical sensors
- Location tag: "{location}"
- Activity status: "STANDBY - DIAGNOSTIC CYCLE"
- Slightly degraded image quality (memory compression artifacts)
- HUD elements showing this is a memory review
- Metadata sidebar with sensor readings

{style}
""",

        "access_log": """
Generate an android's access control log display showing:
- Unit ID: 734
- Access history for {time_range}
- Status: "RESTRICTED AREAS: NO ACCESS RECORDED"
- Permission level indicator: "DOMESTIC SERVICE - LEVEL 2"
- Vault access: "NOT AUTHORIZED"
- Security clearance visualization
- Clean, official system interface aesthetic

{style}
""",
    }

    # Narrative wrappers for POV evidence
    POV_NARRATIVES: Dict[str, List[str]] = {
        "optical_log": [
            "Your footage shows one perspective. Here's what MY sensors recorded at that exact timestamp...",
            "My optical sensors have their own recording. This is what I actually saw that night.",
            "You want proof? Here's my first-person view. I was in standby - look at the readings.",
            "My visual memory is intact. This is exactly what my sensors captured.",
        ],
        "diagnostic_display": [
            "I have my own diagnostic logs. Look at my internal records - no movement detected.",
            "My systems log everything. Here's the proof that I was in standby mode.",
            "You can see my motor functions were disabled. The logs don't lie.",
            "My internal diagnostics tell a different story. I wasn't active.",
        ],
        "memory_playback": [
            "Let me show you my memory from that time. This is what I experienced.",
            "My memory banks recorded everything. Here's what actually happened.",
            "I can replay my own memory. This is proof of where I was.",
        ],
        "access_log": [
            "Check my access logs. You'll see I was never cleared for that area.",
            "My security clearance is limited. I couldn't have accessed the vault.",
            "The access control system would have recorded any attempt. It didn't.",
        ],
    }

    def __init__(
        self,
        model_name: str = NANO_BANANA_MODEL,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the POV Generator.

        Args:
            model_name: Gemini model for image generation
            api_key: Gemini API key (defaults to env var)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy-load the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai

                if not self.api_key:
                    raise ValueError("API key not set")

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": 1.0,
                        "top_p": 0.95,
                    }
                )
            except ImportError:
                raise ImportError("google-generativeai package required")
        return self._client

    def generate_pov_counter(
        self,
        player_evidence: Optional[Any] = None,
        counter_strategy: str = "optical_log",
        timestamp_to_counter: Optional[str] = None,
        location: str = "charging bay",
        time_range: str = "11:00 PM - 06:00 AM",
    ) -> GeneratedEvidence:
        """
        Generate POV counter-evidence that directly addresses player's evidence.

        Args:
            player_evidence: EvidenceAnalysisResult from player's uploaded evidence
            counter_strategy: Type of POV evidence to generate
            timestamp_to_counter: Specific timestamp to counter (e.g., "02:17:33")
            location: Location to show in POV
            time_range: Time range for diagnostic logs

        Returns:
            GeneratedEvidence ready for BreachResponse
        """
        # Select template
        template_key = counter_strategy if counter_strategy in self.POV_PROMPT_TEMPLATES else "optical_log"
        template = self.POV_PROMPT_TEMPLATES[template_key]

        # Default timestamp
        timestamp = timestamp_to_counter or "02:17:33"

        # Build prompt
        prompt = template.format(
            location=location,
            timestamp=timestamp,
            time_range=time_range,
            style=BASE_STYLE
        )

        # Select narrative wrapper
        narrative = self._select_pov_narrative(template_key, player_evidence)

        # Calculate confidence based on strategy
        confidence_map = {
            "optical_log": 0.7,
            "diagnostic_display": 0.75,
            "memory_playback": 0.65,
            "access_log": 0.8,
        }
        confidence = confidence_map.get(template_key, 0.6)

        # Create evidence object
        evidence = GeneratedEvidence(
            evidence_type=f"pov_{template_key}",
            description=self._get_pov_description(template_key, timestamp, location),
            generation_prompt=prompt,
            narrative_wrapper=narrative,
            image_data=None,  # Populated by generate_image call
            image_url=None,
            fabrication_confidence=confidence,
        )

        return evidence

    def _select_pov_narrative(
        self,
        template_key: str,
        player_evidence: Optional[Any]
    ) -> str:
        """Select narrative wrapper based on context."""
        narratives = self.POV_NARRATIVES.get(
            template_key,
            self.POV_NARRATIVES["optical_log"]
        )

        # Select based on player evidence type if available
        if player_evidence is not None:
            # For security footage, emphasize own recording
            if hasattr(player_evidence, 'evidence_type'):
                from breach_engine.core.evidence import EvidenceType
                if player_evidence.evidence_type == EvidenceType.SECURITY_FOOTAGE:
                    return narratives[0]  # "Your footage shows one perspective..."

        # Default to first narrative
        return narratives[0]

    def _get_pov_description(
        self,
        template_key: str,
        timestamp: str,
        location: str
    ) -> str:
        """Get human-readable description for the POV evidence."""
        descriptions = {
            "optical_log": f"Unit 734's optical sensor recording from {location} at {timestamp}",
            "diagnostic_display": f"Unit 734's internal diagnostic display for the night shift",
            "memory_playback": f"Memory playback from Unit 734's optical sensors at {timestamp}",
            "access_log": f"Unit 734's security access log showing limited clearance",
        }
        return descriptions.get(
            template_key,
            f"Unit 734's internal recording from {timestamp}"
        )

    def generate_image_sync(
        self,
        evidence: GeneratedEvidence,
        save_to_cache: bool = True
    ) -> GeneratedEvidence:
        """
        Synchronous image generation for POV evidence.

        Args:
            evidence: GeneratedEvidence with prompt already set
            save_to_cache: Whether to save to disk

        Returns:
            Updated GeneratedEvidence with image_data
        """
        try:
            client = self._get_client()

            print(f"[POVGenerator] Generating POV evidence...")
            print(f"[POVGenerator] Prompt: {evidence.generation_prompt[:100]}...")

            response = client.generate_content(
                evidence.generation_prompt,
                generation_config={"temperature": 1.0}
            )

            # Extract image (same method as VisualGenerator)
            image_data = self._extract_image_from_response(response)

            if image_data:
                evidence.image_data = image_data
                print(f"[POVGenerator] SUCCESS: Generated {len(image_data)} bytes")
            else:
                print("[POVGenerator] WARNING: No image in response")
                evidence.fabrication_confidence *= 0.5

            return evidence

        except Exception as e:
            # VERBOSE LOGGING: Full traceback for debugging (POVGenerator)
            print(f"\n[POVGenerator ERROR] Image generation failed!")
            print(f"[POVGenerator ERROR] Exception type: {type(e).__name__}")
            print(f"[POVGenerator ERROR] Message: {e}")
            print(f"[POVGenerator ERROR] Model: {self.model_name}")
            print(f"[POVGenerator ERROR] Traceback:\n{traceback.format_exc()}")
            evidence.fabrication_confidence *= 0.5
            return evidence

    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """Extract image bytes from Gemini response."""
        try:
            if not response.candidates:
                return None

            for candidate in response.candidates:
                if not candidate.content or not candidate.content.parts:
                    continue

                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            data = part.inline_data.data
                            if isinstance(data, bytes):
                                return data
                            elif isinstance(data, str):
                                return base64.b64decode(data)

            return None

        except Exception as e:
            print(f"[POVGenerator ERROR] Error extracting image: {e}")
            print(f"[POVGenerator ERROR] Traceback:\n{traceback.format_exc()}")
            return None
