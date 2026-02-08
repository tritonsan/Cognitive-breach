"""
Evidence Analyzer - Multimodal Vision System

Uses Gemini Vision to analyze uploaded evidence images and
determine their impact on Unit 734's lie pillars.

This is the "fear" system - images that threaten the cover story
cause massive psychological damage.

Day 15: Added caching for performance optimization.
"""

from __future__ import annotations
import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai
from pydantic import BaseModel, Field

from breach_engine.core.psychology import StoryPillar

logger = logging.getLogger("BreachEngine.EvidenceAnalyzer")


# =============================================================================
# EVIDENCE CACHE
# =============================================================================

class EvidenceCache:
    """
    Simple in-memory cache for evidence analysis results.

    Uses image hash as key to avoid re-analyzing the same image.
    Cache expires after a configurable TTL.
    """

    def __init__(self, max_size: int = 50, ttl_seconds: int = 3600):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of cached results
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def _compute_hash(self, image_data: bytes) -> str:
        """Compute SHA-256 hash of image data."""
        return hashlib.sha256(image_data).hexdigest()[:16]

    def get(self, image_data: bytes) -> Optional[Any]:
        """Get cached result for image data."""
        key = self._compute_hash(image_data)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                logger.debug(f"Cache hit for evidence hash: {key}")
                return result
            else:
                # Expired
                del self._cache[key]
                logger.debug(f"Cache expired for evidence hash: {key}")
        return None

    def set(self, image_data: bytes, result: Any) -> None:
        """Cache analysis result for image data."""
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")

        key = self._compute_hash(image_data)
        self._cache[key] = (result, time.time())
        logger.debug(f"Cached evidence analysis: {key}")

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("Evidence cache cleared")

    @property
    def size(self) -> int:
        """Return current cache size."""
        return len(self._cache)


# Global cache instance
_evidence_cache = EvidenceCache()


# =============================================================================
# EVIDENCE TYPES
# =============================================================================

class EvidenceType(str, Enum):
    """Types of evidence that can be presented."""
    SECURITY_FOOTAGE = "security_footage"     # Timestamps, camera footage
    FORENSIC = "forensic"                      # Fingerprints, DNA, traces
    TOOL = "tool"                              # Screwdrivers, hacking devices
    DATA_STORAGE = "data_storage"              # USB drives, data cores
    DOCUMENT = "document"                      # Logs, records, papers
    LOCATION = "location"                      # Maps, floor plans
    WITNESS = "witness"                        # Photos of witnesses
    OTHER = "other"


# =============================================================================
# EVIDENCE ANALYSIS RESULT
# =============================================================================

class PillarDamage(BaseModel):
    """Damage assessment for a single pillar."""
    pillar: StoryPillar
    severity: float = Field(ge=0.0, le=100.0, description="Damage severity 0-100")
    reason: str = Field(description="Why this evidence damages this pillar")


class DetectedObject(BaseModel):
    """An object detected in the evidence image."""
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    relevance: str = Field(description="Why this object is relevant to the case")


class EvidenceAnalysisResult(BaseModel):
    """Complete analysis result from vision model."""
    # Detection results
    detected_objects: List[DetectedObject] = Field(default_factory=list)
    evidence_type: EvidenceType = Field(default=EvidenceType.OTHER)

    # Pillar damage assessment
    pillar_damage: List[PillarDamage] = Field(default_factory=list)
    total_threat_level: float = Field(
        ge=0.0, le=100.0,
        description="Overall threat to Unit 734's story"
    )

    # Analysis
    analysis_summary: str = Field(description="Brief summary of what was found")
    interrogation_suggestion: str = Field(
        default="",
        description="Suggested question to ask based on this evidence"
    )

    # Metadata
    is_relevant: bool = Field(default=False, description="Is this evidence relevant to the case?")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    def get_most_damaged_pillar(self) -> Optional[PillarDamage]:
        """Get the pillar with highest damage."""
        if not self.pillar_damage:
            return None
        return max(self.pillar_damage, key=lambda p: p.severity)

    def should_collapse_pillar(self, threshold: float = 80.0) -> Optional[StoryPillar]:
        """Check if any pillar should collapse (severity > threshold)."""
        for damage in self.pillar_damage:
            if damage.severity >= threshold:
                return damage.pillar
        return None


# =============================================================================
# EVIDENCE ANALYZER
# =============================================================================

class EvidenceAnalyzer:
    """
    Multimodal evidence analyzer using Gemini Vision.

    Analyzes uploaded images to determine:
    1. What objects/content are in the image
    2. Which lie pillars are threatened
    3. How severely the evidence damages Unit 734's story
    """

    # Evidence analysis prompt
    ANALYSIS_PROMPT = '''You are an evidence analysis AI for an interrogation game.
Analyze this image as if it were evidence in a criminal investigation.

## THE CASE
An Android (Unit 734) is suspected of stealing data cores from a wealthy family's estate.
Unit 734 claims:
- ALIBI: They were docked in "standby/maintenance" from 11 PM to 6 AM (never left the charging alcove)
- MOTIVE: They had no reason to steal (loyal to the family)
- ACCESS: They don't have vault access codes
- KNOWLEDGE: They don't know what the data cores contain

## YOUR TASK
Analyze this image and determine if it contains evidence that threatens any of these claims.

Look for:
1. **Security footage/timestamps** - Would prove Unit 734 was active (threatens ALIBI)
2. **Tools (screwdrivers, hacking devices)** - Would prove capability (threatens ACCESS)
3. **Data storage devices (USB, drives, cores)** - Would prove knowledge (threatens KNOWLEDGE)
4. **Documents/logs** - Could threaten any pillar depending on content
5. **Location evidence** - Floor plans, vault photos, etc. (threatens ACCESS)
6. **Evidence of mistreatment** - Could prove motive (threatens MOTIVE)

## RESPONSE FORMAT
You MUST respond with valid JSON only (no markdown):
{
    "detected_objects": [
        {
            "name": "object name",
            "confidence": 0.0 to 1.0,
            "relevance": "why this matters to the case"
        }
    ],
    "evidence_type": "security_footage" | "forensic" | "tool" | "data_storage" | "document" | "location" | "witness" | "other",
    "pillar_damage": [
        {
            "pillar": "alibi" | "motive" | "access" | "knowledge",
            "severity": 0 to 100,
            "reason": "why this evidence damages this pillar"
        }
    ],
    "total_threat_level": 0 to 100,
    "analysis_summary": "Brief description of what you found and its significance",
    "interrogation_suggestion": "A question the detective could ask based on this evidence",
    "is_relevant": true/false,
    "confidence": 0.0 to 1.0
}

If the image is NOT relevant to the case (random photo, unrelated content), set:
- is_relevant: false
- total_threat_level: 0
- pillar_damage: []

BE DRAMATIC but accurate. This is a game - make the evidence feel impactful!'''

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the evidence analyzer.

        Args:
            api_key: Gemini API key (falls back to env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=self.api_key)

        # Use gemini-3-flash-preview for vision (reasoning + capable)
        # Fallback to 1.5-flash if needed
        try:
            self.model = genai.GenerativeModel("gemini-3-flash-preview")
            self.model_name = "gemini-3-flash-preview"
        except Exception:
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.model_name = "gemini-1.5-flash"

        logger.info(f"EvidenceAnalyzer initialized with model: {self.model_name}")

    def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        use_cache: bool = True
    ) -> EvidenceAnalysisResult:
        """
        Analyze an evidence image.

        Args:
            image_data: Raw image bytes
            mime_type: Image MIME type (image/jpeg, image/png)
            use_cache: Whether to use cached results (default: True)

        Returns:
            EvidenceAnalysisResult with detected objects and pillar damage
        """
        # Check cache first
        if use_cache:
            cached_result = _evidence_cache.get(image_data)
            if cached_result is not None:
                logger.info("Using cached evidence analysis")
                return cached_result

        try:
            # Create image part for Gemini
            image_part = {
                "mime_type": mime_type,
                "data": image_data
            }

            # Generate analysis
            response = self.model.generate_content(
                [self.ANALYSIS_PROMPT, image_part],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
                request_options={"timeout": 30}  # 30 second timeout
            )

            # Parse response
            response_text = response.text.strip()
            logger.debug(f"Vision response: {response_text[:500]}...")

            data = json.loads(response_text)

            # Convert pillar strings to enums
            pillar_damage = []
            for pd in data.get("pillar_damage", []):
                pillar_str = pd.get("pillar", "").lower()
                try:
                    pillar = StoryPillar(pillar_str)
                    pillar_damage.append(PillarDamage(
                        pillar=pillar,
                        severity=pd.get("severity", 0),
                        reason=pd.get("reason", "Unknown")
                    ))
                except ValueError:
                    logger.warning(f"Unknown pillar: {pillar_str}")

            # Convert evidence type
            evidence_type_str = data.get("evidence_type", "other").lower()
            try:
                evidence_type = EvidenceType(evidence_type_str)
            except ValueError:
                evidence_type = EvidenceType.OTHER

            # Build result
            result = EvidenceAnalysisResult(
                detected_objects=[
                    DetectedObject(
                        name=obj.get("name", "Unknown"),
                        confidence=obj.get("confidence", 0.5),
                        relevance=obj.get("relevance", "")
                    )
                    for obj in data.get("detected_objects", [])
                ],
                evidence_type=evidence_type,
                pillar_damage=pillar_damage,
                total_threat_level=data.get("total_threat_level", 0),
                analysis_summary=data.get("analysis_summary", "Analysis unavailable"),
                interrogation_suggestion=data.get("interrogation_suggestion", ""),
                is_relevant=data.get("is_relevant", False),
                confidence=data.get("confidence", 0.5)
            )

            # Cache successful result
            if use_cache:
                _evidence_cache.set(image_data, result)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse vision response: {e}")
            return self._get_fallback_result("Failed to analyze image - invalid response format")

        except Exception as e:
            logger.error(f"Evidence analysis error: {e}")
            return self._get_fallback_result(f"Analysis error: {str(e)}")

    def _get_fallback_result(self, error_message: str) -> EvidenceAnalysisResult:
        """Return a fallback result when analysis fails."""
        return EvidenceAnalysisResult(
            detected_objects=[],
            evidence_type=EvidenceType.OTHER,
            pillar_damage=[],
            total_threat_level=0,
            analysis_summary=error_message,
            interrogation_suggestion="",
            is_relevant=False,
            confidence=0.0
        )

    def analyze_image_file(self, file_path: str) -> EvidenceAnalysisResult:
        """
        Analyze an evidence image from file path.

        Args:
            file_path: Path to image file

        Returns:
            EvidenceAnalysisResult
        """
        import mimetypes

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            mime_type = "image/jpeg"

        # Read file
        with open(file_path, "rb") as f:
            image_data = f.read()

        return self.analyze_image(image_data, mime_type)


# =============================================================================
# EVIDENCE IMPACT CALCULATOR
# =============================================================================

@dataclass
class EvidenceImpact:
    """Calculated impact of evidence on psychology."""
    cognitive_load_spike: float
    mask_divergence_spike: float
    pillars_damaged: Dict[StoryPillar, float]  # pillar -> damage amount
    pillars_collapsed: List[StoryPillar]
    secrets_triggered: List[str]  # Secret IDs that should be revealed
    analysis_result: EvidenceAnalysisResult


class EvidenceImpactCalculator:
    """
    Calculates the psychological impact of evidence.

    Converts vision analysis results into game mechanics:
    - Cognitive load spikes
    - Mask breaks
    - Pillar damage/collapse
    - Secret reveals

    Features DIMINISHING RETURNS: Evidence against pillars that have
    already been damaged (acknowledged weakness) has reduced psychological
    impact - Unit 734 has already "taken the hit" mentally.
    """

    # Base cognitive load spike for evidence
    BASE_COGNITIVE_SPIKE = 25.0

    # Mask divergence spike
    BASE_MASK_SPIKE = 30.0

    # Pillar collapse threshold
    COLLAPSE_THRESHOLD = 80.0

    def calculate_impact(
        self,
        analysis: EvidenceAnalysisResult,
        current_pillar_health: Dict[StoryPillar, float],
        pillar_diminishing_factors: Optional[Dict[StoryPillar, float]] = None
    ) -> EvidenceImpact:
        """
        Calculate the psychological impact of evidence.

        Args:
            analysis: Vision analysis result
            current_pillar_health: Current health of each pillar
            pillar_diminishing_factors: Optional dict of pillar -> factor (0.0-1.0)
                                       for reducing psychological impact on
                                       already-damaged pillars

        Returns:
            EvidenceImpact with all calculated effects
        """
        if not analysis.is_relevant:
            return EvidenceImpact(
                cognitive_load_spike=0,
                mask_divergence_spike=0,
                pillars_damaged={},
                pillars_collapsed=[],
                secrets_triggered=[],
                analysis_result=analysis
            )

        # Default to no diminishing returns if not provided
        diminishing_factors = pillar_diminishing_factors or {}

        # Calculate base cognitive spike based on threat level
        threat_multiplier = analysis.total_threat_level / 100
        base_cognitive_spike = self.BASE_COGNITIVE_SPIKE * threat_multiplier

        # High-threat evidence causes bigger spike
        if analysis.total_threat_level > 70:
            base_cognitive_spike *= 1.5

        # Calculate base mask spike
        base_mask_spike = self.BASE_MASK_SPIKE * threat_multiplier

        # Track actual psychological impact (may be reduced by diminishing returns)
        total_cognitive_spike = 0.0
        total_mask_spike = 0.0

        # Process pillar damage with diminishing returns
        pillars_damaged = {}
        pillars_collapsed = []

        for damage in analysis.pillar_damage:
            pillar = damage.pillar
            severity = damage.severity

            # Get diminishing returns factor for this pillar
            # 1.0 = full impact (fresh pillar), 0.3 = minimal impact (already admitted)
            dr_factor = diminishing_factors.get(pillar, 1.0)

            # Calculate actual damage to pillar (full damage regardless of DR)
            damage_amount = severity * 0.5  # Severity 100 = 50 damage
            pillars_damaged[pillar] = damage_amount

            # Calculate PSYCHOLOGICAL impact (affected by diminishing returns)
            # This is the key fix: evidence confirming known weakness hurts less
            pillar_cognitive_contribution = (base_cognitive_spike * (severity / 100)) * dr_factor
            pillar_mask_contribution = (base_mask_spike * (severity / 100)) * dr_factor

            total_cognitive_spike += pillar_cognitive_contribution
            total_mask_spike += pillar_mask_contribution

            # Check for collapse
            current_health = current_pillar_health.get(pillar, 100)
            new_health = current_health - damage_amount

            if new_health <= 25 or severity >= self.COLLAPSE_THRESHOLD:
                pillars_collapsed.append(pillar)
                # Pillar collapse = massive psychological impact (NOT reduced by DR)
                # Collapse is always traumatic, even if weakness was acknowledged
                total_cognitive_spike += 20
                total_mask_spike = 100  # Complete mask break

        # If no pillar-specific damage, use base values
        if not analysis.pillar_damage:
            total_cognitive_spike = base_cognitive_spike
            total_mask_spike = base_mask_spike

        # Determine secrets triggered by pillar collapses
        secrets_triggered = []
        for pillar in pillars_collapsed:
            # Map pillars to secret IDs
            pillar_to_secret = {
                StoryPillar.ALIBI: "secret_left_station",
                StoryPillar.ACCESS: "secret_vault_access",
                StoryPillar.MOTIVE: "secret_motive",
                StoryPillar.KNOWLEDGE: "secret_took_cores",
            }
            if pillar in pillar_to_secret:
                secrets_triggered.append(pillar_to_secret[pillar])

        return EvidenceImpact(
            cognitive_load_spike=min(total_cognitive_spike, 50),  # Cap at 50
            mask_divergence_spike=min(total_mask_spike, 100),
            pillars_damaged=pillars_damaged,
            pillars_collapsed=pillars_collapsed,
            secrets_triggered=secrets_triggered,
            analysis_result=analysis
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_evidence_analyzer() -> EvidenceAnalyzer:
    """Get a configured EvidenceAnalyzer instance."""
    return EvidenceAnalyzer()
