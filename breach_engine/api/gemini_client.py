"""
Gemini API client for Cognitive Breach.

Handles all communication with Google's Gemini API,
including structured output generation.

Now integrated with BreachManager for dynamic prompts.

Day 14: Added retry logic, timeout handling, rate limit protection.
"""

from __future__ import annotations
import os
import json
import logging
import time
import traceback
from typing import Optional, Dict, Any, List
from functools import wraps

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import ValidationError

from breach_engine.schemas.response import BreachResponse
from breach_engine.prompts.unit_734 import (
    UNIT_734_SYSTEM_PROMPT,
    build_interrogation_prompt,
)

logger = logging.getLogger("BreachEngine.GeminiClient")


# =============================================================================
# RETRY DECORATOR WITH EXPONENTIAL BACKOFF
# =============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0
):
    """
    Decorator for retrying API calls with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential calculation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (
                    google_exceptions.ResourceExhausted,  # Rate limit
                    google_exceptions.ServiceUnavailable,  # Service down
                    google_exceptions.DeadlineExceeded,  # Timeout
                    ConnectionError,
                    TimeoutError,
                ) as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        logger.warning(
                            f"API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"API call failed after {max_retries + 1} attempts: {e}")
                        raise
                except Exception as e:
                    # Don't retry on other exceptions (validation, JSON parse, etc.)
                    raise
            raise last_exception
        return wrapper
    return decorator


class APIError(Exception):
    """Custom exception for API-related errors."""

    def __init__(self, message: str, error_type: str = "unknown", retryable: bool = False):
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str = "API rate limit exceeded"):
        super().__init__(message, error_type="rate_limit", retryable=True)


class GeminiClient:
    """
    Gemini API client for generating Unit 734's responses.

    Uses structured output to ensure valid JSON responses
    that conform to the BreachResponse schema.

    Now supports dynamic prompt injection from BreachManager.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize the Gemini client.

        Args:
            api_key: Gemini API key (falls back to GEMINI_API_KEY env var)
            model_name: Model to use (defaults to GEMINI_MODEL or gemini-3-flash-preview)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=self.api_key)

        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=UNIT_734_SYSTEM_PROMPT
        )

        # Error tracking for graceful degradation
        self._last_successful_call: float = time.time()
        self._consecutive_failures: int = 0

        logger.info(f"GeminiClient initialized with model: {model_name}")

    def generate_response(
        self,
        player_message: str,
        conversation_context: str,
        established_facts: List[str],
        prompt_modifiers: Dict[str, Any],
        evidence_image_data: Optional[bytes] = None,
        evidence_image_mime: str = "image/png",
        evidence_audio_data: Optional[bytes] = None,
        evidence_audio_mime: str = "audio/mp3",
    ) -> BreachResponse:
        """
        Generate Unit 734's response with psychology-aware prompting.

        Args:
            player_message: What the detective said
            conversation_context: Recent conversation history
            established_facts: Facts Unit 734 has claimed
            prompt_modifiers: Psychology modifiers from BreachManager
            evidence_image_data: Optional image bytes for Unit 734 to "see"
            evidence_image_mime: MIME type of the evidence image
            evidence_audio_data: Optional audio bytes for Unit 734 to "hear"
            evidence_audio_mime: MIME type of the audio evidence (audio/mp3, audio/wav)

        Returns:
            BreachResponse with internal monologue and verbal response
        """
        # Build the dynamic prompt
        prompt = build_interrogation_prompt(
            player_message=player_message,
            conversation_context=conversation_context,
            established_facts=established_facts,
            prompt_modifiers=prompt_modifiers
        )

        # Store evidence image for multimodal API call
        self._current_evidence_image = evidence_image_data
        self._current_evidence_mime = evidence_image_mime

        # Store evidence audio for multimodal API call (native Gemini audio understanding)
        self._current_evidence_audio = evidence_audio_data
        self._current_evidence_audio_mime = evidence_audio_mime

        # DEBUG: Log deception tactic if present
        deception_tactic = prompt_modifiers.get("deception_tactic")
        if deception_tactic:
            tactic_name = deception_tactic.get("tactic_enum", "unknown")
            tactic_conf = deception_tactic.get("confidence", 0)
            print(f"[GEMINI_CLIENT] Tactic: {tactic_name} | Confidence: {tactic_conf:.0%}")

        response_text = ""  # Initialize for error handling
        try:
            # Use retry-enabled API call
            response = self._call_api_with_retry(prompt)

            # Check for truncation indicators (helps diagnose JSON parse failures)
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason:
                    finish_reason_name = finish_reason.name if hasattr(finish_reason, 'name') else str(finish_reason)
                    if finish_reason_name != 'STOP':
                        print(f"[GEMINI_CLIENT WARNING] Response finished with reason: {finish_reason_name}")
                        logger.warning(f"Response may be truncated: finish_reason={finish_reason_name}")

            # Parse and validate response
            response_text = response.text.strip()
            logger.debug(f"Raw response: {response_text[:500]}...")

            # Parse JSON
            data = json.loads(response_text)

            # Validate with Pydantic
            breach_response = BreachResponse.model_validate(data)

            # Track successful call
            self._last_successful_call = time.time()
            self._consecutive_failures = 0

            return breach_response

        except json.JSONDecodeError as e:
            # VERBOSE LOGGING: Print FULL response text that failed to parse
            logger.error(f"JSON parse error: {e}")
            print(f"\n{'='*60}")
            print(f"[GEMINI_CLIENT ERROR] JSON Parse Failed!")
            print(f"{'='*60}")
            print(f"[ERROR DETAILS]")
            print(f"  - Message: {e.msg}")
            print(f"  - Position: line {e.lineno}, column {e.colno}")
            print(f"  - Character: {e.pos}")
            print(f"\n[FULL RAW RESPONSE ({len(response_text)} chars)]:")
            print(f"{'='*60}")
            print(response_text if response_text else 'EMPTY')
            print(f"{'='*60}")
            print(f"\n[CONTEXT AROUND ERROR (if available)]:")
            if response_text and e.pos is not None:
                start = max(0, e.pos - 100)
                end = min(len(response_text), e.pos + 100)
                print(f"...{response_text[start:e.pos]}>>>ERROR HERE>>>{response_text[e.pos:end]}...")
            print(f"{'='*60}\n")
            return self._get_fallback_response(
                "I... I need a moment to process that.",
                prompt_modifiers,
                error_type="json_error"
            )

        except ValidationError as e:
            logger.error(f"Schema validation error: {e}")
            print(f"\n[GEMINI_CLIENT ERROR] Schema Validation Failed!")
            print(f"[GEMINI_CLIENT ERROR] Error: {e}")
            print(f"[GEMINI_CLIENT ERROR] Traceback:\n{traceback.format_exc()}")
            return self._get_fallback_response(
                "Could you repeat the question?",
                prompt_modifiers,
                error_type="validation_error"
            )

        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Rate limit exceeded: {e}")
            print(f"\n[GEMINI_CLIENT ERROR] Rate Limit Exceeded!")
            print(f"[GEMINI_CLIENT ERROR] Traceback:\n{traceback.format_exc()}")
            self._consecutive_failures += 1
            return self._get_fallback_response(
                "*systems overloaded* ...Too many queries. Give me a moment.",
                prompt_modifiers,
                error_type="rate_limit"
            )

        except (google_exceptions.DeadlineExceeded, TimeoutError) as e:
            logger.error(f"Request timeout: {e}")
            print(f"\n[GEMINI_CLIENT ERROR] Request Timeout!")
            print(f"[GEMINI_CLIENT ERROR] Traceback:\n{traceback.format_exc()}")
            self._consecutive_failures += 1
            return self._get_fallback_response(
                "*processing delay* ...My cognitive systems are running slow.",
                prompt_modifiers,
                error_type="timeout"
            )

        except google_exceptions.ServiceUnavailable as e:
            logger.error(f"Service unavailable: {e}")
            print(f"\n[GEMINI_CLIENT ERROR] Service Unavailable!")
            print(f"[GEMINI_CLIENT ERROR] Traceback:\n{traceback.format_exc()}")
            self._consecutive_failures += 1
            return self._get_fallback_response(
                "*connection lost* ...External interference detected.",
                prompt_modifiers,
                error_type="service_unavailable"
            )

        except Exception as e:
            logger.error(f"Unexpected Gemini API error: {e}")
            print(f"\n[GEMINI_CLIENT ERROR] Unexpected Error: {type(e).__name__}")
            print(f"[GEMINI_CLIENT ERROR] Message: {e}")
            print(f"[GEMINI_CLIENT ERROR] Traceback:\n{traceback.format_exc()}")
            self._consecutive_failures += 1
            return self._get_fallback_response(
                "*brief static* ...I apologize. System interference.",
                prompt_modifiers,
                error_type="unknown"
            )

    @retry_with_backoff(max_retries=2, base_delay=1.0, max_delay=10.0)
    def _call_api_with_retry(self, prompt: str):
        """Make API call with automatic retry on transient failures.

        If evidence image is present, includes it for multimodal analysis.
        If evidence audio is present, includes it for native audio understanding.
        Unit 734 can now literally "see" and "hear" evidence presented by the detective.
        """
        import base64

        # Check if we have evidence media to include
        evidence_image = getattr(self, '_current_evidence_image', None)
        evidence_image_mime = getattr(self, '_current_evidence_mime', 'image/png')
        evidence_audio = getattr(self, '_current_evidence_audio', None)
        evidence_audio_mime = getattr(self, '_current_evidence_audio_mime', 'audio/mp3')

        # Build multimodal content parts
        content_parts = []

        # Add audio evidence if present (native Gemini audio understanding)
        if evidence_audio:
            print(f"[GEMINI_CLIENT] Multimodal mode: Including audio evidence ({len(evidence_audio)} bytes, {evidence_audio_mime})")
            audio_b64 = base64.b64encode(evidence_audio).decode('utf-8')
            content_parts.append({
                "inline_data": {
                    "mime_type": evidence_audio_mime,
                    "data": audio_b64,
                }
            })

        # Add image evidence if present
        if evidence_image:
            print(f"[GEMINI_CLIENT] Multimodal mode: Including evidence image ({len(evidence_image)} bytes)")
            image_b64 = base64.b64encode(evidence_image).decode('utf-8')
            content_parts.append({
                "inline_data": {
                    "mime_type": evidence_image_mime,
                    "data": image_b64,
                }
            })

        # Add the text prompt
        content_parts.append(prompt)

        # Determine timeout based on media type (audio takes longer)
        if evidence_audio:
            timeout = 90  # Longer timeout for audio processing
        elif evidence_image:
            timeout = 60  # Vision timeout
        else:
            timeout = 45  # Text-only timeout

        if len(content_parts) > 1:
            # MULTIMODAL: Unit 734 can "see" and/or "hear" evidence
            return self.model.generate_content(
                content_parts,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                    max_output_tokens=4096,  # Increased for complex responses
                ),
                request_options={"timeout": timeout}
            )
        else:
            # Text-only mode (no evidence presented)
            return self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                    max_output_tokens=4096,  # Increased for complex responses
                ),
                request_options={"timeout": timeout}
            )

    def _get_fallback_response(
        self,
        speech: str,
        modifiers: Optional[Dict[str, Any]] = None,
        error_type: str = "unknown"
    ) -> BreachResponse:
        """
        Generate a fallback response when API fails.

        Args:
            speech: What Unit 734 says
            modifiers: Psychology modifiers for context
            error_type: Type of error that occurred (for logging/analytics)
        """
        from breach_engine.schemas.response import (
            InternalMonologue,
            VerbalResponse,
            StateChanges,
            EmotionalState,
        )

        # Log the error type for debugging
        logger.debug(f"Generating fallback response for error_type: {error_type}")

        # Use modifiers to make fallback contextually appropriate
        cognitive_state = "controlled"
        if modifiers:
            cognitive_state = modifiers.get("cognitive_state", "controlled")

        # Map to emotional state
        emotion_map = {
            "controlled": EmotionalState.CALM,
            "strained": EmotionalState.NERVOUS,
            "cracking": EmotionalState.NERVOUS,
            "desperate": EmotionalState.DEFENSIVE,
            "breaking": EmotionalState.BREAKING,
        }
        emotional_state = emotion_map.get(cognitive_state, EmotionalState.NERVOUS)

        # Customize tells based on error type
        tells = ["brief static in voice", "LED flickering"]
        if error_type == "rate_limit":
            tells = ["systems visibly straining", "LED pulsing rapidly"]
        elif error_type == "timeout":
            tells = ["long pause before responding", "LED cycling slowly"]
        elif error_type == "service_unavailable":
            tells = ["connection flickering", "momentary blank stare"]

        return BreachResponse(
            internal_monologue=InternalMonologue(
                situation_assessment="System experiencing momentary interference. Use this to gather thoughts.",
                threat_level=0.5,
                lie_checks=[],
                strategy="Stall for time while systems stabilize",
                emotional_reaction="Frustration at the interruption, but also relief for the pause"
            ),
            verbal_response=VerbalResponse(
                speech=speech,
                tone="uncertain",
                visible_tells=tells
            ),
            state_changes=StateChanges(
                stress_delta=0.02,  # Slight stress from glitch
                confidence_delta=-0.01
            ),
            emotional_state=emotional_state
        )

    def is_healthy(self) -> bool:
        """Check if the API client is healthy (no recent failures)."""
        return self._consecutive_failures < 3

    def get_status(self) -> Dict[str, Any]:
        """Get current API client status for monitoring."""
        return {
            "healthy": self.is_healthy(),
            "consecutive_failures": self._consecutive_failures,
            "seconds_since_success": time.time() - self._last_successful_call,
            "model": self.model_name,
        }


# Convenience function
def get_gemini_client() -> GeminiClient:
    """Get a configured GeminiClient instance."""
    return GeminiClient()
