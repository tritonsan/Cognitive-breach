"""
Forensics Lab - Dynamic Player Evidence Generation

Implements the "Generative vs Generative" gameplay:
- Player requests evidence from Forensics Team
- System generates truthful evidence images on-the-fly
- Unit 734 then analyzes and potentially counters with fabricated evidence

This creates a unique "prompt battle" between player and AI:
  Player Evidence (Truth) vs Unit 734 Counter-Evidence (Lies)

Key Design Principles:
1. Latency Masking: "Forensics Team Processing..." hides API wait time
2. Evidence Registry: Maintains consistency across generated evidence
3. Threat Calibration: Generated evidence has appropriate threat levels
4. Request Validation: Prevents prompt injection and off-topic requests

Hackathon Impact:
- Transforms static evidence selection into open-world investigation
- Unlimited replayability - no two playthroughs have same evidence
- Demonstrates Creative Autopilot at its fullest potential
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import base64
import os
import re
import hashlib
import io
from pathlib import Path

# Import psychology types
from .psychology import StoryPillar


# =============================================================================
# CONFIGURATION
# =============================================================================

# Cache directory for player-requested evidence (optional, for local dev)
EVIDENCE_CACHE_DIR = Path(__file__).parent.parent.parent / "assets" / "evidence_cache" / "player"

# Image generation model
IMAGE_GEN_MODEL = "gemini-3-pro-image-preview"


# =============================================================================
# LORE MAPPING - Consistent World Building
# =============================================================================

LORE_KEYWORDS: Dict[str, str] = {
    # Locations
    "standbyplace": "Unit 734's high-tech charging bay in the maintenance wing",
    "chargebay": "Unit 734's high-tech charging bay in the maintenance wing",
    "charging station": "Unit 734's high-tech charging bay with status monitoring displays",
    "maintenance bay": "the industrial maintenance wing with android service equipment",
    "server room": "the secure server room with racks of quantum storage units",
    "vault": "Morrison Estate's high-security data vault with biometric locks",
    "data center": "the climate-controlled data center housing the stolen cores",
    "hallway": "the dimly-lit corridor outside the restricted zones",
    "entrance": "the main entrance with security checkpoint",
    "kitchen": "the Morrison Estate kitchen with service android docking",
    "study": "Mr. Morrison's private study with wall-mounted displays",
    "garage": "the underground garage with vehicle charging stations",
    "security office": "the security monitoring station with multiple screens",
    "garden": "the Morrison Estate garden with motion-activated lights",
    "basement": "the basement storage area with limited surveillance",
    "roof": "the rooftop access point with emergency exit",
    "library": "the estate library with rare data crystal archives",

    # Characters/Units
    "unit 734": "Unit 734, an SN-7 Series synthetic with neural status indicator on temple",
    "suspect": "Unit 734, the synthetic suspect with serial number visible",
    "android": "a humanoid synthetic unit with visible neural status indicator",
    "unit 892": "Unit 892, another household synthetic (potential alternate suspect)",

    # Objects
    "data cores": "the three missing quantum data cores worth millions",
    "stolen property": "the three cylindrical quantum data cores",
    "evidence": "forensic evidence related to the Morrison Estate theft",

    # Time references
    "crime time": "between 2:00 AM and 3:00 AM on March 14, 2087",
    "incident": "the theft that occurred on the night of March 14, 2087",
}

# Facts that should be consistent across all generated evidence
CASE_FACTS = {
    "date": "March 14, 2087",
    "time_window": "2:00 AM - 3:00 AM",
    "location": "Morrison Estate",
    "suspect": "Unit 734 (SN-7 Series)",
    "stolen_items": "Three quantum data cores",
    "alibi_claim": "In charging bay from 11 PM to 3:15 AM",
}


# =============================================================================
# EVIDENCE REQUEST TYPES
# =============================================================================

class EvidenceRequestType(str, Enum):
    """Types of evidence the player can request from Forensics."""

    CCTV_FOOTAGE = "cctv_footage"
    """Security camera footage from specific location/time."""

    ACCESS_LOG = "access_log"
    """Digital access records (door logs, system logins)."""

    FORENSIC_ANALYSIS = "forensic_analysis"
    """Physical evidence analysis (fingerprints, traces, footprints)."""

    COMMUNICATION_RECORD = "communication_record"
    """Messages, calls, data transfers."""

    WITNESS_PHOTO = "witness_photo"
    """Photo evidence from witness accounts."""

    DOCUMENT_SCAN = "document_scan"
    """Scanned documents, records, manifests."""

    TECHNICAL_SCHEMATIC = "technical_schematic"
    """Technical diagrams, system layouts, access paths."""


class RequestValidationResult(str, Enum):
    """Result of validating a player's evidence request."""
    VALID = "valid"
    INVALID_TYPE = "invalid_type"  # Not a valid evidence request
    OUT_OF_SCOPE = "out_of_scope"  # Outside case parameters
    RATE_LIMITED = "rate_limited"  # Too many requests
    INJECTION_DETECTED = "injection_detected"  # Prompt injection attempt


# =============================================================================
# EVIDENCE REGISTRY
# =============================================================================

@dataclass
class GeneratedEvidenceRecord:
    """Record of evidence generated during the session."""
    request_id: str
    request_text: str
    evidence_type: EvidenceRequestType
    location: str
    time_reference: str
    pillar_targeted: StoryPillar
    threat_level: float
    image_data: Optional[bytes] = None
    generation_prompt: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def get_summary(self) -> str:
        """Get a brief summary for display."""
        return f"{self.evidence_type.value}: {self.location} @ {self.time_reference}"


class EvidenceRegistry:
    """
    Maintains consistency across all generated evidence.

    Ensures that if the player asks for "CCTV of server room at 3AM" twice,
    they get consistent (cached) results, not contradictory images.
    """

    def __init__(self):
        self.records: Dict[str, GeneratedEvidenceRecord] = {}
        self.request_count: int = 0
        self.last_request_time: Optional[datetime] = None

    def _generate_request_id(self, request_text: str) -> str:
        """Generate a unique but deterministic ID for a request."""
        # Normalize the request for consistent hashing
        normalized = request_text.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def has_similar_evidence(self, request_text: str) -> Optional[GeneratedEvidenceRecord]:
        """Check if similar evidence was already generated."""
        request_id = self._generate_request_id(request_text)
        return self.records.get(request_id)

    def register_evidence(
        self,
        request_text: str,
        evidence_type: EvidenceRequestType,
        location: str,
        time_reference: str,
        pillar_targeted: StoryPillar,
        threat_level: float,
        generation_prompt: str,
        image_data: Optional[bytes] = None,
    ) -> GeneratedEvidenceRecord:
        """Register newly generated evidence."""
        request_id = self._generate_request_id(request_text)

        record = GeneratedEvidenceRecord(
            request_id=request_id,
            request_text=request_text,
            evidence_type=evidence_type,
            location=location,
            time_reference=time_reference,
            pillar_targeted=pillar_targeted,
            threat_level=threat_level,
            generation_prompt=generation_prompt,
            image_data=image_data,
        )

        self.records[request_id] = record
        self.request_count += 1
        self.last_request_time = datetime.now()

        return record

    def get_all_evidence(self) -> List[GeneratedEvidenceRecord]:
        """Get all generated evidence records."""
        return list(self.records.values())

    def can_make_request(self, cooldown_seconds: float = 30.0) -> bool:
        """Check if enough time has passed since last request."""
        if self.last_request_time is None:
            return True
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        return elapsed >= cooldown_seconds


# =============================================================================
# REQUEST PARSER
# =============================================================================

class EvidenceRequestParser:
    """
    Parses natural language evidence requests from the player.

    Extracts:
    - Evidence type (CCTV, logs, forensics, etc.)
    - Location reference
    - Time reference
    - Target pillar (inferred)
    """

    # Keywords for evidence type detection
    # EVIDENCE TYPE MISMATCH FIX: Comprehensive keyword mappings
    # PRIORITY ORDER: More specific keywords first to avoid false matches
    TYPE_KEYWORDS: Dict[EvidenceRequestType, List[str]] = {
        # HIGHEST PRIORITY: Visual/image-based evidence
        EvidenceRequestType.CCTV_FOOTAGE: [
            "cctv", "camera", "footage", "video", "recording", "surveillance",
            "security camera", "monitor", "feed", "infrared", "thermal",
            "night vision", "motion sensor", "freeze-frame", "freeze frame",
            "still", "frame", "snapshot", "capture", "image from camera"
        ],
        EvidenceRequestType.WITNESS_PHOTO: [
            "witness", "saw", "observed", "testimony", "statement",
            "photo from", "picture from", "reflection", "optical serial",
            "photo of", "image of", "picture of", "visual of"
        ],
        # FORENSIC: Physical/scientific analysis
        EvidenceRequestType.FORENSIC_ANALYSIS: [
            "fingerprint", "dna", "trace", "residue", "footprint", "forensic",
            "sample", "fiber", "hair", "x-ray", "xray", "body scan",
            "torso scan", "internal scan", "component scan", "diagnostic scan",
            "heat signature", "thermal analysis", "biometric scan", "retinal",
            "spectral analysis", "material analysis"
        ],
        # DOCUMENTS: Text-based records
        EvidenceRequestType.DOCUMENT_SCAN: [
            "document", "manifest", "schedule", "roster", "report",
            "log book", "maintenance log", "duty roster", "service record",
            "banking", "ledger", "financial", "deed", "contract", "memo",
            "decrypted", "file header", "file metadata", "encrypted file",
            "data file", "hex dump", "binary"
        ],
        # TECHNICAL: Graphs, schematics, data visualizations
        EvidenceRequestType.TECHNICAL_SCHEMATIC: [
            "schematic", "blueprint", "layout", "diagram", "map",
            "floor plan", "system diagram", "network map",
            "power", "battery", "energy", "consumption", "discharge",
            "wattage", "voltage", "current", "amp", "power log",
            "power spike", "energy consumption", "charging log",
            "graph", "chart", "timeline", "activity log"
        ],
        # COMMUNICATION: Network/signal records
        EvidenceRequestType.COMMUNICATION_RECORD: [
            "message", "communication", "call", "email", "transmission",
            "signal", "data transfer", "network log", "packet", "traffic",
            "broadcast", "ping", "handshake", "protocol"
        ],
        # ACCESS LOGS: Door/entry records (lowest priority to avoid false positives)
        EvidenceRequestType.ACCESS_LOG: [
            "access log", "door log", "entry log", "login record",
            "authentication log", "badge swipe", "keycard log",
            "access record", "entry record", "swipe record",
            "vault door log", "override log", "clearance log"
        ],
    }

    # Known locations in the Morrison Estate
    VALID_LOCATIONS = [
        "server room", "vault", "data center", "hallway", "entrance",
        "maintenance bay", "charging station", "kitchen", "study",
        "garage", "security office", "garden", "basement", "roof",
        "master bedroom", "guest room", "library", "corridor",
        "east wing", "west wing", "north wing", "south wing",
    ]

    # Time pattern matching
    TIME_PATTERNS = [
        r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))',  # 3:00 AM
        r'(\d{1,2}\s*(?:am|pm|AM|PM))',         # 3 AM
        r'(\d{1,2}:\d{2})',                       # 03:00
        r'(midnight|noon)',                       # Keywords
        r'(around\s+\d{1,2})',                   # "around 3"
        r'(between\s+\d{1,2}\s*(?:and|to)\s*\d{1,2})',  # "between 2 and 4"
    ]

    # Pillar inference based on location
    LOCATION_TO_PILLAR: Dict[str, StoryPillar] = {
        "server room": StoryPillar.ACCESS,
        "vault": StoryPillar.ACCESS,
        "data center": StoryPillar.KNOWLEDGE,
        "charging station": StoryPillar.ALIBI,
        "maintenance bay": StoryPillar.ALIBI,
        "hallway": StoryPillar.ALIBI,
        "entrance": StoryPillar.ALIBI,
    }

    def parse(self, request_text: str) -> Dict[str, Any]:
        """
        Parse a natural language evidence request.

        Returns dict with:
        - evidence_type: EvidenceRequestType
        - location: str
        - time_reference: str
        - pillar_targeted: StoryPillar
        - confidence: float (how confident we are in parsing)
        """
        text_lower = request_text.lower()

        # Detect evidence type
        evidence_type = self._detect_type(text_lower)

        # Extract location
        location = self._extract_location(text_lower)

        # Extract time
        time_ref = self._extract_time(text_lower)

        # Infer target pillar
        pillar = self._infer_pillar(location, evidence_type)

        # Calculate parsing confidence
        confidence = self._calculate_confidence(
            evidence_type, location, time_ref
        )

        return {
            "evidence_type": evidence_type,
            "location": location,
            "time_reference": time_ref,
            "pillar_targeted": pillar,
            "confidence": confidence,
            "raw_request": request_text,
        }

    def _detect_type(self, text: str) -> EvidenceRequestType:
        """Detect evidence type from keywords."""
        scores = {t: 0 for t in EvidenceRequestType}

        for etype, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[etype] += len(keyword)  # Longer matches = higher score

        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]

        # Default to CCTV (most common request)
        return EvidenceRequestType.CCTV_FOOTAGE

    def _extract_location(self, text: str) -> str:
        """Extract location from request."""
        for location in self.VALID_LOCATIONS:
            if location in text:
                return location

        # Try to find any location-like phrase
        # Pattern: "of the <location>" or "in the <location>"
        match = re.search(r'(?:of|in|at|from)\s+(?:the\s+)?([a-z\s]+?)(?:\s+at|\s+around|\s*$)', text)
        if match:
            return match.group(1).strip()

        return "unknown location"

    def _extract_time(self, text: str) -> str:
        """Extract time reference from request."""
        for pattern in self.TIME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Check for relative times
        if "last night" in text:
            return "last night"
        if "during the theft" in text or "time of crime" in text:
            return "02:00-03:00 AM"

        return "unspecified time"

    def _infer_pillar(
        self,
        location: str,
        evidence_type: EvidenceRequestType
    ) -> StoryPillar:
        """Infer which story pillar this evidence targets."""
        # Location-based inference
        for loc, pillar in self.LOCATION_TO_PILLAR.items():
            if loc in location:
                return pillar

        # Type-based inference
        type_to_pillar = {
            EvidenceRequestType.ACCESS_LOG: StoryPillar.ACCESS,
            EvidenceRequestType.FORENSIC_ANALYSIS: StoryPillar.ACCESS,
            EvidenceRequestType.COMMUNICATION_RECORD: StoryPillar.KNOWLEDGE,
            EvidenceRequestType.DOCUMENT_SCAN: StoryPillar.MOTIVE,
        }

        return type_to_pillar.get(evidence_type, StoryPillar.ALIBI)

    def _calculate_confidence(
        self,
        evidence_type: EvidenceRequestType,
        location: str,
        time_ref: str
    ) -> float:
        """Calculate how confident we are in the parsing."""
        confidence = 0.5  # Base

        if evidence_type != EvidenceRequestType.CCTV_FOOTAGE:  # Not default
            confidence += 0.2

        if location != "unknown location":
            confidence += 0.2

        if time_ref != "unspecified time":
            confidence += 0.1

        return min(1.0, confidence)


# =============================================================================
# PROMPT TEMPLATES FOR EVIDENCE GENERATION
# =============================================================================

EVIDENCE_BASE_STYLE = """
Style: Cinematic sci-fi noir, photorealistic 8k, cold color grading, dramatic lighting,
unreal engine 5 render quality, atmospheric depth, soft diffused cyberpunk aesthetic.
Security/forensic documentation with authentic imperfections, near-future 2087 technology,
corporate surveillance aesthetic. The evidence should look AUTHENTIC and potentially DAMAGING.
IMPORTANT: Create ORIGINAL sci-fi designs. Do NOT reference Detroit Become Human, Blade Runner,
or any existing media. Synthetics should have a simple neural status indicator light (not LED ring).
"""

EVIDENCE_GENERATION_PROMPTS: Dict[EvidenceRequestType, str] = {
    EvidenceRequestType.CCTV_FOOTAGE: """
Generate a security camera footage frame showing:
- Location: {location} in the Morrison Estate
- Time: {time_reference} (timestamp overlay: "2087-03-14 {time_display}")
- Scene: {scene_description}
- A humanoid synthetic figure (Unit 734) visible in the frame, appearing suspicious
- The synthetic has a neural status indicator light on temple (glowing color)
- Camera angle: elevated corner view typical of security cameras
- Quality: Real CCTV footage quality with slight grain/compression artifacts
- The synthetic should be doing something that contradicts their alibi
- IMPORTANT: Original sci-fi design, NOT from any existing game or movie
{style}
""",

    EvidenceRequestType.ACCESS_LOG: """
Generate a digital access log display showing:
- System: Morrison Estate Security System v3.7
- Date: 2087-03-14
- Log entries showing Unit 734's access being used at {location}
- Timestamp: {time_reference}
- Entry highlighting: "UNIT-734 | ACCESS GRANTED | {location}"
- UI style: Corporate security interface with blue/green accents
- Include anomaly flag or warning indicator
{style}
""",

    EvidenceRequestType.FORENSIC_ANALYSIS: """
Generate a forensic analysis report display showing:
- Evidence type: {evidence_detail}
- Location found: {location}
- Analysis result: Match to Unit 734's specifications (SN-7 Series)
- {forensic_visual_type}
- Official forensic lab header: "Morrison Estate Forensics Division"
- Conclusion: "HIGH CONFIDENCE MATCH"
{style}
""",

    EvidenceRequestType.COMMUNICATION_RECORD: """
Generate a communication log display showing:
- System: Morrison Estate Network Monitor
- Date: 2087-03-14, Time: {time_reference}
- Data transfer record from {location}
- Source: Unit 734's internal systems
- Destination: External server (suspicious)
- Data volume highlighted as anomalous
- Red warning flags on the interface
{style}
""",

    EvidenceRequestType.WITNESS_PHOTO: """
Generate an image representing witness testimony:
- Scene: {location} at {time_reference}
- View from a witness perspective (another synthetic or human staff member)
- Unit 734 (humanoid synthetic with neural indicator light) visible, acting covertly
- Lighting: Nighttime, partial illumination
- Photo quality: Slightly grainy, as if taken quickly
- Include timestamp watermark
- IMPORTANT: Original sci-fi design, NOT from any existing game or movie
{style}
""",

    EvidenceRequestType.DOCUMENT_SCAN: """
Generate a scanned document showing:
- Document type: {evidence_detail}
- Morrison Estate official letterhead
- Date: 2087-03-14
- Content: Information that contradicts Unit 734's statements
- Handwritten notes or highlights on key sections
- Official stamps and signatures
- Slight scan artifacts for authenticity
{style}
""",

    EvidenceRequestType.TECHNICAL_SCHEMATIC: """
Generate a {technical_visual_type}:
- Type: {evidence_detail}
- {technical_context}
- Time: {time_reference}
- Subject: Unit 734 (SN-7 Series Synthetic)
- {technical_annotation}
- Technical annotation style with grid overlay
- "CONFIDENTIAL" watermark
{style}
""",
}


# =============================================================================
# FORENSICS LAB CLASS
# =============================================================================

class ForensicsLab:
    """
    Generates truthful evidence images at the player's request.

    This is the player's tool for investigation - they describe what
    evidence they want, and the "Forensics Team" generates it.

    Key Design:
    - Latency is masked as "Forensics Team Processing..."
    - Generated evidence is consistent (cached in registry)
    - Evidence always threatens Unit 734 (it's real evidence)
    - Rate-limited to prevent abuse

    Usage:
        lab = ForensicsLab()
        result = lab.request_evidence("Get me CCTV of the server room at 3 AM")
        # Returns evidence that the player can present to Unit 734
    """

    def __init__(
        self,
        model_name: str = IMAGE_GEN_MODEL,  # Use stable image gen model
        api_key: Optional[str] = None,
        request_cooldown: float = 30.0,  # Seconds between requests
        max_requests_per_session: int = 10,
    ):
        """
        Initialize the Forensics Lab.

        Args:
            model_name: Gemini model for image generation (default: gemini-2.0-flash-exp)
            api_key: Gemini API key
            request_cooldown: Minimum seconds between requests
            max_requests_per_session: Maximum evidence requests per game
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.request_cooldown = request_cooldown
        self.max_requests = max_requests_per_session

        self._client = None
        self._genai = None
        self.registry = EvidenceRegistry()
        self.parser = EvidenceRequestParser()

        # Cache directory
        self.cache_dir = EVIDENCE_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Threat level calibration based on pillar
        self.pillar_threat_levels: Dict[StoryPillar, Tuple[float, float]] = {
            StoryPillar.ALIBI: (0.6, 0.9),    # High threat - core to story
            StoryPillar.ACCESS: (0.5, 0.85),  # High threat
            StoryPillar.MOTIVE: (0.4, 0.75),  # Medium-high
            StoryPillar.KNOWLEDGE: (0.3, 0.7), # Medium
        }

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

    def _get_cache_path(self, request_id: str) -> Path:
        """Get cache file path for an evidence request."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{request_id}_{timestamp}.png"
        return self.cache_dir / filename

    def _create_placeholder_evidence(self) -> bytes:
        """Create a placeholder when generation fails."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # Return minimal PNG if PIL not available
            return base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842AAAAAElFTkSuQmCC"
            )

        # Create "processing" placeholder
        img = Image.new('RGB', (512, 384), color=(30, 35, 45))
        draw = ImageDraw.Draw(img)

        # Add grid pattern
        for x in range(0, 512, 32):
            draw.line([(x, 0), (x, 384)], fill=(40, 45, 55))
        for y in range(0, 384, 32):
            draw.line([(0, y), (512, y)], fill=(40, 45, 55))

        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((120, 160), "EVIDENCE RETRIEVAL", fill=(100, 150, 200), font=font)
        draw.text((140, 200), "PLEASE WAIT...", fill=(80, 120, 160), font=font)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def validate_request(self, request_text: str) -> Tuple[RequestValidationResult, str]:
        """
        Validate a player's evidence request.

        Checks for:
        - Rate limiting
        - Prompt injection attempts
        - Valid evidence type

        Returns:
            Tuple of (validation result, message)
        """
        # Check rate limit
        if not self.registry.can_make_request(self.request_cooldown):
            return (
                RequestValidationResult.RATE_LIMITED,
                "Forensics Team is still processing the previous request. Please wait."
            )

        # Check max requests
        if self.registry.request_count >= self.max_requests:
            return (
                RequestValidationResult.RATE_LIMITED,
                "Forensics Team has reached maximum capacity for this investigation."
            )

        # Check for prompt injection attempts
        injection_patterns = [
            r'ignore.*instructions',
            r'ignore.*previous',
            r'system\s*prompt',
            r'you\s+are\s+(now|actually)',
            r'pretend\s+to\s+be',
            r'<\s*script',
            r'\{\{.*\}\}',
            r'disregard',
            r'new\s+instructions',
        ]

        text_lower = request_text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                return (
                    RequestValidationResult.INJECTION_DETECTED,
                    "Invalid evidence request format. Please describe the evidence you need."
                )

        # Check for out-of-scope requests
        out_of_scope = [
            "other case", "different crime", "not morrison",
            "another suspect", "not unit 734",
        ]

        for phrase in out_of_scope:
            if phrase in text_lower:
                return (
                    RequestValidationResult.OUT_OF_SCOPE,
                    "This request is outside the scope of the current investigation."
                )

        # Parse and validate structure
        parsed = self.parser.parse(request_text)
        if parsed["confidence"] < 0.3:
            return (
                RequestValidationResult.INVALID_TYPE,
                "Could not understand the evidence request. Try: 'Get CCTV footage of [location] at [time]'"
            )

        return (RequestValidationResult.VALID, "Request validated. Forensics Team processing...")

    def request_evidence(
        self,
        request_text: str,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a player's evidence request.

        This is the main entry point for player evidence generation.

        Args:
            request_text: Natural language evidence request
            skip_validation: Skip validation (for testing)

        Returns:
            Dict containing:
            - success: bool
            - evidence: GeneratedEvidenceRecord (if successful)
            - message: str (status message)
            - threat_level: float
            - pillar_targeted: StoryPillar
        """
        # Validate request
        if not skip_validation:
            validation, message = self.validate_request(request_text)
            if validation != RequestValidationResult.VALID:
                return {
                    "success": False,
                    "evidence": None,
                    "message": message,
                    "validation_result": validation.value,
                }

        # Check cache first
        cached = self.registry.has_similar_evidence(request_text)
        if cached:
            return {
                "success": True,
                "evidence": cached,
                "message": "Retrieved from evidence database.",
                "threat_level": cached.threat_level,
                "pillar_targeted": cached.pillar_targeted,
                "from_cache": True,
            }

        # Parse the request
        parsed = self.parser.parse(request_text)

        # Calculate threat level
        threat_range = self.pillar_threat_levels.get(
            parsed["pillar_targeted"],
            (0.4, 0.7)
        )
        import random
        threat_level = random.uniform(*threat_range)

        # Build generation prompt (pass original request for sub-type detection)
        prompt = self._build_generation_prompt(parsed, request_text)

        # Register the evidence (image_data populated later by API)
        record = self.registry.register_evidence(
            request_text=request_text,
            evidence_type=parsed["evidence_type"],
            location=parsed["location"],
            time_reference=parsed["time_reference"],
            pillar_targeted=parsed["pillar_targeted"],
            threat_level=threat_level,
            generation_prompt=prompt,
            image_data=None,  # Populated by generate_image_sync/async
        )

        return {
            "success": True,
            "evidence": record,
            "message": f"Evidence request processed: {record.get_summary()}",
            "threat_level": threat_level,
            "pillar_targeted": parsed["pillar_targeted"],
            "from_cache": False,
        }

    def _build_generation_prompt(self, parsed: Dict[str, Any], request_text: str = "") -> str:
        """Build the image generation prompt from parsed request."""
        evidence_type = parsed["evidence_type"]
        template = EVIDENCE_GENERATION_PROMPTS.get(
            evidence_type,
            EVIDENCE_GENERATION_PROMPTS[EvidenceRequestType.CCTV_FOOTAGE]
        )

        # Build scene description based on pillar
        scene_descriptions = {
            StoryPillar.ALIBI: "The android is clearly away from their claimed location",
            StoryPillar.ACCESS: "The android is accessing a restricted area",
            StoryPillar.MOTIVE: "Evidence of conflict or suspicious behavior",
            StoryPillar.KNOWLEDGE: "The android handling sensitive data",
        }

        # Time display normalization
        time_ref = parsed["time_reference"]
        if "am" in time_ref.lower() or "pm" in time_ref.lower():
            time_display = time_ref.upper()
        else:
            time_display = time_ref

        # EVIDENCE TYPE MISMATCH FIX: Detect specialized sub-types
        request_lower = request_text.lower()

        # Forensic Analysis sub-types
        forensic_visual_type = "Scientific visualization (comparison charts, match probability)"
        if any(kw in request_lower for kw in ["x-ray", "xray", "scan", "torso", "body", "internal"]):
            forensic_visual_type = "X-ray scan visualization showing internal components, synthetic framework scan, diagnostic overlay with highlighted anomalies"
        elif any(kw in request_lower for kw in ["fingerprint", "print"]):
            forensic_visual_type = "Fingerprint comparison analysis with ridge pattern matching and confidence scores"
        elif any(kw in request_lower for kw in ["dna", "genetic"]):
            forensic_visual_type = "DNA/synthetic material analysis with helix visualization and match indicators"
        elif any(kw in request_lower for kw in ["footprint", "trace", "residue"]):
            forensic_visual_type = "Trace evidence analysis with contamination mapping and source attribution"

        # Technical Schematic sub-types (power logs, etc.)
        technical_visual_type = "technical schematic"
        technical_context = f"Morrison Estate facility layout\n- {parsed['location']} highlighted"
        technical_annotation = "Access points and security zones labeled"

        if any(kw in request_lower for kw in ["power", "battery", "energy", "consumption", "discharge", "watt"]):
            technical_visual_type = "power consumption log graph"
            technical_context = f"Unit 734 battery discharge history\n- Energy usage timeline from 11 PM to 4 AM\n- Graph showing power spikes at {time_ref}"
            technical_annotation = "RED SPIKE HIGHLIGHTED at suspicious time - 'ANOMALOUS POWER DRAW DETECTED'\n- Normal standby baseline shown for comparison\n- Labeled axis: Power (Watts) vs Time"
        elif any(kw in request_lower for kw in ["movement", "locomotion", "pedometer", "gps"]):
            technical_visual_type = "movement tracking log"
            technical_context = f"Unit 734 internal motion sensor data\n- Position tracking from internal GPS/pedometer"
            technical_annotation = "Movement vectors marked in red, contradicting 'stationary' claim"

        # Substitutions
        subs = {
            "style": EVIDENCE_BASE_STYLE,
            "location": parsed["location"],
            "time_reference": time_ref,
            "time_display": time_display,
            "scene_description": scene_descriptions.get(
                parsed["pillar_targeted"],
                "Suspicious activity captured"
            ),
            "evidence_detail": f"{evidence_type.value} from {parsed['location']}",
            # EVIDENCE TYPE MISMATCH FIX: Specialized visual types
            "forensic_visual_type": forensic_visual_type,
            "technical_visual_type": technical_visual_type,
            "technical_context": technical_context,
            "technical_annotation": technical_annotation,
        }

        prompt = template
        for key, value in subs.items():
            prompt = prompt.replace("{" + key + "}", str(value))

        return prompt.strip()

    def _inject_lore_context(
        self,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        established_facts: Optional[List[str]] = None,
    ) -> str:
        """
        Inject lore context and chat history into the generation prompt.

        This ensures visual consistency with:
        1. The game's established world (LORE_KEYWORDS)
        2. Recent conversation context (what Unit 734 claimed)
        3. Established facts from the interrogation

        Args:
            prompt: The base generation prompt
            chat_history: Last N messages from the conversation
            established_facts: Known facts from the game state

        Returns:
            Enhanced prompt with lore and context injection
        """
        enhanced_prompt = prompt

        # Step 1: Expand lore keywords in the prompt
        for keyword, expansion in LORE_KEYWORDS.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            enhanced_prompt = pattern.sub(expansion, enhanced_prompt)

        # Step 2: Build context block from chat history
        context_block = []

        # Add case facts
        context_block.append("=== CASE CONTEXT ===")
        context_block.append(f"Date: {CASE_FACTS['date']}")
        context_block.append(f"Location: {CASE_FACTS['location']}")
        context_block.append(f"Suspect: {CASE_FACTS['suspect']}")
        context_block.append(f"Crime Window: {CASE_FACTS['time_window']}")
        context_block.append(f"Suspect's Alibi Claim: {CASE_FACTS['alibi_claim']}")

        # Add established facts if available
        if established_facts:
            context_block.append("\n=== ESTABLISHED FACTS ===")
            for fact in established_facts[-5:]:  # Last 5 facts
                context_block.append(f"- {fact}")

        # Add recent chat context
        if chat_history:
            context_block.append("\n=== RECENT INTERROGATION CONTEXT ===")
            # Get last 5 relevant messages
            recent = chat_history[-5:] if len(chat_history) > 5 else chat_history

            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                if role == "detective":
                    # Summarize detective's question
                    context_block.append(f"Detective asked about: {content[:100]}...")
                elif role == "suspect":
                    # Extract key claims from Unit 734
                    verbal = msg.get("verbal_response", {})
                    speech = verbal.get("speech", content) if isinstance(verbal, dict) else content
                    if speech:
                        context_block.append(f"Unit 734 claimed: {speech[:150]}...")

        # Step 3: Inject context into prompt
        context_text = "\n".join(context_block)

        consistency_instruction = f"""
=== CONSISTENCY REQUIREMENTS ===
{context_text}

IMPORTANT: The generated evidence must be visually consistent with the above context.
- If Unit 734 claimed to be in a location, evidence should reflect that claim being FALSE
- Timestamps must be within the crime window ({CASE_FACTS['time_window']})
- The synthetic shown should match Unit 734's description (SN-7 Series, neural status indicator)
- Style: Near-future 2087, corporate security aesthetic, slight grain/noise
"""

        # Prepend consistency requirements to the prompt
        enhanced_prompt = consistency_instruction + "\n\n" + enhanced_prompt

        return enhanced_prompt

    def generate_image_sync(
        self,
        evidence: GeneratedEvidenceRecord,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        established_facts: Optional[List[str]] = None,
        save_to_disk: bool = False,  # Cloud-compatible: default to in-memory only
    ) -> GeneratedEvidenceRecord:
        """
        Generate evidence image using Gemini API (synchronous).

        This is the MAIN method for Streamlit integration.
        Cloud-compatible: stores image data in-memory, optionally saves to disk.

        Args:
            evidence: Evidence record with prompt set
            chat_history: Recent chat messages for context consistency
            established_facts: Known facts from interrogation
            save_to_disk: Whether to save to disk (False for cloud deployment)

        Returns:
            Updated evidence record with image_data and image_base64
        """
        try:
            client = self._get_client()

            print(f"[ForensicsLab] Generating evidence with {self.model_name}...")
            print(f"[ForensicsLab] Request: {evidence.request_text[:50]}...")

            # Inject lore context for consistency
            enhanced_prompt = self._inject_lore_context(
                evidence.generation_prompt,
                chat_history=chat_history,
                established_facts=established_facts,
            )

            print(f"[ForensicsLab] Enhanced prompt with lore context ({len(enhanced_prompt)} chars)")

            # Generate image using Nano Banana Pro
            print(f"[ForensicsLab] Calling API... (timeout: 90s)")
            response = client.generate_content(
                enhanced_prompt,
                generation_config={
                    "temperature": 1.0,
                },
                request_options={"timeout": 90}  # 90 second timeout for image gen
            )
            print(f"[ForensicsLab] API call completed")

            # Extract image data
            image_data = self._extract_image_from_response(response)

            if image_data:
                evidence.image_data = image_data
                print(f"[ForensicsLab] SUCCESS: Generated {len(image_data)} bytes")

                # Optionally save to disk (for local development)
                if save_to_disk:
                    try:
                        cache_path = self._get_cache_path(evidence.request_id)
                        cache_path.write_bytes(image_data)
                        print(f"[ForensicsLab] Cached to: {cache_path}")
                    except Exception as disk_err:
                        print(f"[ForensicsLab] Disk cache failed (cloud?): {disk_err}")
            else:
                print("[ForensicsLab] WARNING: No image in response, using placeholder")
                evidence.image_data = self._create_placeholder_evidence()

            return evidence

        except Exception as e:
            print(f"[ForensicsLab] ERROR: {type(e).__name__}: {e}")
            # Use placeholder - don't crash the game
            evidence.image_data = self._create_placeholder_evidence()
            return evidence

    def get_image_as_base64(self, image_data: bytes) -> str:
        """Convert image bytes to base64 string for cloud-safe storage."""
        return base64.b64encode(image_data).decode('utf-8')

    def get_image_from_base64(self, base64_str: str) -> bytes:
        """Convert base64 string back to image bytes."""
        return base64.b64decode(base64_str)

    async def generate_image_async(
        self,
        evidence: GeneratedEvidenceRecord,
        save_to_cache: bool = True
    ) -> GeneratedEvidenceRecord:
        """Async version of image generation."""
        try:
            client = self._get_client()

            print(f"[ForensicsLab] Generating evidence with {self.model_name}...")

            # Generate image using Nano Banana Pro (async)
            response = await client.generate_content_async(
                evidence.generation_prompt,
                generation_config={
                    "temperature": 1.0,
                }
            )

            image_data = self._extract_image_from_response(response)

            if image_data:
                evidence.image_data = image_data
                print(f"[ForensicsLab] SUCCESS: Generated {len(image_data)} bytes")

                if save_to_cache:
                    cache_path = self._get_cache_path(evidence.request_id)
                    cache_path.write_bytes(image_data)
                    print(f"[ForensicsLab] Cached to: {cache_path}")
            else:
                print("[ForensicsLab] WARNING: No image in response")
                evidence.image_data = self._create_placeholder_evidence()

            return evidence

        except Exception as e:
            print(f"[ForensicsLab] ERROR: {type(e).__name__}: {e}")
            evidence.image_data = self._create_placeholder_evidence()
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
            print(f"[ForensicsLab] Error extracting image: {e}")
            return None

    def get_loading_message(self) -> str:
        """Get a random loading message for UX."""
        messages = [
            "Forensics Team analyzing surveillance archives...",
            "Searching Morrison Estate security database...",
            "Cross-referencing with crime scene timeline...",
            "Enhancing footage quality...",
            "Validating evidence chain of custody...",
            "Retrieving archived sensor data...",
            "Processing forensic analysis request...",
            "Decrypting secured records...",
        ]
        import random
        return random.choice(messages)

    def get_evidence_summary(self) -> List[str]:
        """Get summary of all evidence gathered in this session."""
        return [
            record.get_summary()
            for record in self.registry.get_all_evidence()
        ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_forensics_lab() -> ForensicsLab:
    """Factory function to create a configured ForensicsLab."""
    return ForensicsLab(
        request_cooldown=30.0,
        max_requests_per_session=10,
    )


def format_evidence_for_ui(evidence: GeneratedEvidenceRecord) -> Dict[str, Any]:
    """Format evidence record for UI display."""
    return {
        "title": f"Evidence: {evidence.evidence_type.value.replace('_', ' ').title()}",
        "location": evidence.location,
        "time": evidence.time_reference,
        "threat_level": evidence.threat_level,
        "threat_label": (
            "CRITICAL" if evidence.threat_level > 0.8
            else "HIGH" if evidence.threat_level > 0.6
            else "MODERATE" if evidence.threat_level > 0.4
            else "LOW"
        ),
        "pillar": evidence.pillar_targeted.value.upper(),
        "has_image": evidence.image_data is not None,
        "summary": evidence.get_summary(),
    }


# =============================================================================
# PUBLIC API - Exports for use by other modules
# =============================================================================

__all__ = [
    # Main classes
    "ForensicsLab",
    "EvidenceRequestParser",
    "EvidenceRegistry",
    "GeneratedEvidenceRecord",
    # Enums
    "EvidenceRequestType",
    "RequestValidationResult",
    # Factory functions
    "create_forensics_lab",
    "format_evidence_for_ui",
    # Lore constants
    "LORE_KEYWORDS",
    "CASE_FACTS",
]
