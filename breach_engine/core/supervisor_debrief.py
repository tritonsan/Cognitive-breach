"""
Supervisor Debrief System - Post-Interrogation Audio Analysis

Generates cold, analytical audio debriefs using:
1. Gemini for script generation (analysis of session data)
2. Gemini 2.5 TTS for audio synthesis

The Supervisor is an ominous, data-driven AI that evaluates
interrogation performance with clinical precision.
"""

from __future__ import annotations
import os
import io
import base64
import wave
import logging
from typing import Optional, Dict, Any, List, Tuple

# Try importing the new google-genai SDK first (for TTS support)
try:
    from google import genai as genai_new
    from google.genai import types as genai_types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False
    genai_new = None
    genai_types = None

# Legacy SDK for script generation
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger("BreachEngine.SupervisorDebrief")


class SupervisorDebrief:
    """
    Cold, analytical AI supervisor that generates post-interrogation audio debriefs.
    Uses Gemini for script generation + Gemini 2.5 TTS for audio synthesis.
    """

    # Models
    SCRIPT_MODEL = "gemini-3-flash-preview"  # Script generation
    TTS_MODEL = "gemini-2.5-flash-preview-tts"  # Audio synthesis

    # Supervisor Persona
    PERSONA = """You are THE SUPERVISOR - a cold, analytical AI that evaluates
interrogation performance. Your tone is:
- Precise and data-driven
- Slightly ominous but professional
- Like a high-level AI evaluating a subordinate algorithm
- No warmth, no encouragement - pure objective analysis

You speak in short, clipped sentences. You reference specific data points.
You are never impressed. You are never disappointed. You simply... evaluate."""

    # Script generation prompt template
    SCRIPT_PROMPT = '''THE SUPERVISOR DEBRIEF PROTOCOL

{persona}

Generate a 30-45 second audio debrief script (80-120 words) for text-to-speech.

SESSION DATA:
- Outcome: {outcome}
- Ending Type: {ending_type}
- Reason: {reason}

STATISTICS:
- Total Turns: {turns}
- Secrets Revealed: {secrets_revealed}
- Pillars Collapsed: {pillars_collapsed}/4
- Final Cognitive Load: {final_cognitive_load:.1f}%
- Confession Level: {confession_level}

TURN-BY-TURN ANALYSIS:
{turn_analysis}

YOUR SCRIPT MUST CONTAIN ALL FOUR SECTIONS IN ORDER:

SECTION 1 - THE VERDICT:
State "Interrogation result: [SUCCESSFUL/FAILED/INCONCLUSIVE]" and reference the ending type.

SECTION 2 - THE TURNING POINT:
Identify the critical turn where the outcome was determined. Reference specific data: stress levels, pillar collapses, Reid phase, or confession risk percentages from the turn analysis above.

SECTION 3 - EFFICIENCY RATING:
State "Efficiency rating: {efficiency:.0f} percent" then deliver assessment based on score:
- Below 40%: "Suboptimal. Significant room for improvement."
- 40-60%: "Acceptable. Marginal performance detected."
- 60-80%: "Efficient. Within expected parameters."
- Above 80%: "Optimal. Performance noted for future reference."

SECTION 4 - CLOSING:
End with ONE ominous line. Examples:
- "The suspect's data patterns have been archived."
- "Your methods are now part of the permanent record."
- "The subject's resistance profile has been updated."

CRITICAL REQUIREMENTS:
- You MUST write ALL FOUR sections. Do not stop early.
- Total length: 80-120 words (approximately 400-600 characters)
- Output ONLY the spoken script text. No headers, labels, or formatting.
- Short, punchy sentences for TTS clarity.
- Clinical, data-driven tone. No praise or encouragement.

BEGIN SCRIPT:
'''

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Supervisor Debrief system.

        Args:
            api_key: Gemini API key (falls back to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=self.api_key)

        # Script generation model
        self.script_model = genai.GenerativeModel(
            model_name=self.SCRIPT_MODEL,
            system_instruction=self.PERSONA
        )

        # TTS model
        self.tts_model = genai.GenerativeModel(self.TTS_MODEL)

        logger.info(f"SupervisorDebrief initialized with {self.SCRIPT_MODEL} + {self.TTS_MODEL}")

    def generate_debrief(self, session_data: Dict[str, Any]) -> Optional[Tuple[bytes, str]]:
        """
        Generate audio debrief from session data.

        Args:
            session_data: Dictionary containing:
                - outcome: "victory" | "defeat" | "partial"
                - ending_type: str
                - reason: str
                - stats: dict with turns, secrets_revealed, etc.
                - turns: list of turn snapshots

        Returns:
            Tuple of (audio_bytes, mime_type) or None if generation fails.
            mime_type is typically 'audio/mp3' or 'audio/wav'.
        """
        try:
            # Step 1: Generate the script
            script = self._generate_script(session_data)
            if not script:
                logger.error("Script generation failed")
                return None

            logger.info(f"Generated script ({len(script)} chars)")

            # Step 2: Synthesize audio
            result = self._synthesize_audio(script)
            if not result:
                logger.error("Audio synthesis failed")
                return None

            audio_bytes, mime_type = result
            logger.info(f"Generated audio ({len(audio_bytes)} bytes, {mime_type})")
            return audio_bytes, mime_type

        except Exception as e:
            logger.error(f"Debrief generation failed: {e}")
            return None

    # Minimum acceptable script length (characters)
    # 80 words minimum * ~5 chars/word = 400 chars
    MIN_SCRIPT_LENGTH = 350

    def _generate_script(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate the debrief script using Gemini.

        Args:
            session_data: Session data dictionary

        Returns:
            Script text or None if generation fails
        """
        try:
            # Extract stats
            stats = session_data.get("stats", {})
            turns_data = session_data.get("turns", [])

            # Calculate efficiency
            efficiency = self._calculate_efficiency(stats)

            # Build turn analysis string
            turn_analysis = self._format_turn_analysis(turns_data)

            # Build the prompt
            prompt = self.SCRIPT_PROMPT.format(
                persona=self.PERSONA,
                outcome=session_data.get("outcome", "unknown").upper(),
                ending_type=session_data.get("ending_type", "unknown"),
                reason=session_data.get("reason", "No reason provided"),
                turns=stats.get("turns", 0),
                secrets_revealed=stats.get("secrets_revealed", 0),
                pillars_collapsed=stats.get("pillars_collapsed", 0),
                final_cognitive_load=stats.get("final_cognitive_load", 0),
                confession_level=stats.get("confession_level", "NONE"),
                turn_analysis=turn_analysis,
                efficiency=efficiency,
            )

            # Generate script with retry logic for truncation
            max_attempts = 3
            for attempt in range(max_attempts):
                response = self.script_model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7 + (attempt * 0.1),  # Slightly increase temp on retry
                        max_output_tokens=1000,  # Increased from 500
                    ),
                    request_options={"timeout": 45}
                )

                script = response.text.strip()
                script_length = len(script)

                logger.info(f"Script attempt {attempt + 1}: {script_length} chars")

                # Validate script length
                if script_length >= self.MIN_SCRIPT_LENGTH:
                    logger.info(f"Script accepted: {script_length} chars, ~{len(script.split())} words")
                    return script

                # Script too short - log and retry
                logger.warning(
                    f"Script too short ({script_length} chars < {self.MIN_SCRIPT_LENGTH}). "
                    f"Attempt {attempt + 1}/{max_attempts}. Content: {script[:100]}..."
                )

            # All attempts failed - return best effort with warning
            logger.error(f"Script generation failed to meet minimum length after {max_attempts} attempts")
            # Return the last script anyway rather than failing completely
            return script

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"Script generation rate limited: {e}")
            return None
        except Exception as e:
            logger.error(f"Script generation error: {e}")
            return None

    def _synthesize_audio(self, script: str) -> Optional[Tuple[bytes, str]]:
        """
        Convert script to audio using Gemini TTS.

        Args:
            script: The script text to synthesize

        Returns:
            Tuple of (audio_bytes, mime_type) or None if synthesis fails.
            mime_type is typically 'audio/mp3' or 'audio/wav'.
        """
        # Try new SDK first (has proper TTS support)
        if NEW_SDK_AVAILABLE and genai_new and genai_types:
            try:
                return self._synthesize_audio_new_sdk(script)
            except Exception as e:
                logger.warning(f"New SDK TTS failed, trying legacy: {e}")

        # Fallback to legacy SDK approach (returns None - legacy doesn't support TTS)
        return self._synthesize_audio_legacy(script)

    def _synthesize_audio_new_sdk(self, script: str) -> Optional[Tuple[bytes, str]]:
        """
        TTS synthesis using the new google-genai SDK.

        Gemini TTS returns raw PCM audio data (not encoded MP3/WAV).
        We must wrap it in a proper WAV container for playback.

        PCM format from Gemini TTS:
        - Sample rate: 24000 Hz
        - Channels: 1 (mono)
        - Sample width: 2 bytes (16-bit)

        Args:
            script: The script text to synthesize

        Returns:
            Tuple of (wav_bytes, mime_type) or None if synthesis fails
        """
        try:
            # Create client with API key
            client = genai_new.Client(api_key=self.api_key)

            # Generate audio using the TTS-specific API
            response = client.models.generate_content(
                model=self.TTS_MODEL,
                contents=script,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=genai_types.SpeechConfig(
                        voice_config=genai_types.VoiceConfig(
                            prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                                voice_name="Kore"  # Cold, analytical voice
                            )
                        )
                    )
                )
            )

            # Extract audio data from response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Check for inline_data with audio
                    if hasattr(part, 'inline_data') and part.inline_data:
                        inline_data = part.inline_data
                        pcm_data = inline_data.data

                        # Data might be base64 encoded or raw bytes
                        if isinstance(pcm_data, str):
                            pcm_data = base64.b64decode(pcm_data)

                        logger.info(f"TTS returned {len(pcm_data)} bytes of raw PCM data")

                        # Convert raw PCM to WAV format
                        wav_bytes = self._pcm_to_wav(pcm_data)
                        logger.info(f"Converted to WAV: {len(wav_bytes)} bytes")

                        return wav_bytes, "audio/wav"

            logger.warning("No audio data found in new SDK TTS response")
            return None

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"TTS rate limited: {e}")
            return None
        except Exception as e:
            logger.error(f"New SDK TTS synthesis error: {e}")
            raise  # Re-raise to trigger fallback

    def _pcm_to_wav(
        self,
        pcm_data: bytes,
        channels: int = 1,
        sample_rate: int = 24000,
        sample_width: int = 2
    ) -> bytes:
        """
        Convert raw PCM audio data to WAV format.

        Gemini TTS outputs raw PCM data that needs a WAV header for playback.

        Args:
            pcm_data: Raw PCM audio bytes
            channels: Number of audio channels (default: 1 = mono)
            sample_rate: Sample rate in Hz (default: 24000)
            sample_width: Bytes per sample (default: 2 = 16-bit)

        Returns:
            Complete WAV file as bytes
        """
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)

        wav_buffer.seek(0)
        return wav_buffer.read()

    def _synthesize_audio_legacy(self, script: str) -> Optional[bytes]:
        """
        Legacy TTS synthesis fallback.

        NOTE: The legacy google-generativeai SDK does NOT support audio modalities.
        TTS requires the new google-genai SDK with response_modalities=["AUDIO"].

        Args:
            script: The script text to synthesize

        Returns:
            None - legacy SDK cannot generate audio
        """
        logger.warning(
            "Legacy SDK (google-generativeai) does not support TTS audio generation. "
            "Install google-genai>=1.0.0 for voice report functionality: "
            "pip install google-genai"
        )
        return None

    def _calculate_efficiency(self, stats: Dict[str, Any]) -> float:
        """
        Calculate interrogation efficiency (0-100%).

        Formula:
        - Pillars collapsed: 25 points each (max 100)
        - Secrets revealed: 10 points each (max 50)
        - Turn penalty: -2 points per turn over 5

        Args:
            stats: Game statistics dictionary

        Returns:
            Efficiency percentage (0-100)
        """
        pillars_collapsed = stats.get("pillars_collapsed", 0)
        secrets_revealed = stats.get("secrets_revealed", 0)
        turns = stats.get("turns", 0)

        pillar_score = pillars_collapsed * 25  # 0-100
        secret_score = secrets_revealed * 10   # 0-50
        turn_penalty = max(0, (turns - 5) * 2)  # 0-50+

        raw_score = pillar_score + secret_score - turn_penalty
        return max(0, min(100, raw_score))

    def _format_turn_analysis(self, turns_data: List[Dict[str, Any]]) -> str:
        """
        Format turn-by-turn data for the script prompt.

        Args:
            turns_data: List of turn snapshots

        Returns:
            Formatted string for prompt injection
        """
        if not turns_data:
            return "No detailed turn data available."

        lines = []
        for turn in turns_data[-10:]:  # Last 10 turns max
            turn_num = turn.get("turn_number", turn.get("turn", "?"))
            stress = turn.get("cognitive_load", turn.get("stress_level", 0))

            line = f"Turn {turn_num}: Stress={stress:.0f}%"

            # Add pillar info if available
            pillars_collapsed = turn.get("pillars_collapsed", [])
            if pillars_collapsed:
                line += f", Collapsed=[{', '.join(pillars_collapsed)}]"

            # Add Shadow Analyst data if available
            shadow = turn.get("shadow_analyst")
            if shadow:
                reid_phase = shadow.get("reid_phase", "unknown")
                confession_risk = shadow.get("confession_risk", 0)
                trap_detected = shadow.get("trap_detected", False)

                line += f", Reid={reid_phase}, ConfessionRisk={confession_risk:.0%}"
                if trap_detected:
                    line += ", TRAP DETECTED"

            # Add deception tactic if available
            tactic = turn.get("deception_tactic")
            if tactic:
                line += f", Tactic={tactic}"

            lines.append(line)

        return "\n".join(lines)

    def generate_script_only(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate only the script without audio synthesis.
        Useful for testing or text-only fallback.

        Args:
            session_data: Session data dictionary

        Returns:
            Script text or None
        """
        return self._generate_script(session_data)


def get_supervisor_debrief() -> SupervisorDebrief:
    """Factory function to get a configured SupervisorDebrief instance."""
    return SupervisorDebrief()
