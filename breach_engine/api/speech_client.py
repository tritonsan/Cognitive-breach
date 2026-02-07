"""
Google Speech-to-Text integration for voice input.

Uses Gemini's audio capabilities for transcription, with SpeechRecognition
library as a fallback option.

Created for hackathon multimodal INPUT feature (complements image OUTPUT).
"""

from __future__ import annotations
import os
import io
import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("BreachEngine.SpeechClient")


class TranscriptionResult(BaseModel):
    """Result from voice transcription."""
    transcript: str = Field(description="The transcribed text")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    duration_seconds: float = Field(ge=0.0, description="Audio duration in seconds")
    error: Optional[str] = Field(default=None, description="Error message if transcription failed")


class SpeechClient:
    """
    Google Speech-to-Text integration for voice input.

    Attempts transcription via Gemini's audio capabilities first,
    falls back to SpeechRecognition library if needed.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the speech client.

        Args:
            api_key: Gemini API key (falls back to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._gemini_model = None
        self._speech_recognizer = None

        # Initialize Gemini for audio transcription
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # Use Gemini 3 Flash for fast transcription (matches main GeminiClient)
                self._gemini_model = genai.GenerativeModel("gemini-3-flash-preview")
                logger.info("SpeechClient initialized with Gemini audio support")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini for audio: {e}")

        # Initialize SpeechRecognition as fallback
        try:
            import speech_recognition as sr
            self._speech_recognizer = sr.Recognizer()
            logger.info("SpeechRecognition fallback initialized")
        except ImportError:
            logger.info("SpeechRecognition not installed - Gemini-only mode")

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav"
    ) -> TranscriptionResult:
        """
        Convert audio to text.

        Args:
            audio_bytes: Raw audio data from st.audio_input()
            mime_type: Audio format (audio/wav, audio/webm, etc.)

        Returns:
            TranscriptionResult with transcript and confidence
        """
        # Estimate duration (rough calculation)
        # WAV: ~176KB per second at 44.1kHz 16-bit stereo
        # WebM: much more compressed
        estimated_duration = len(audio_bytes) / 176000 if "wav" in mime_type else len(audio_bytes) / 20000

        # Try Gemini first (primary method)
        if self._gemini_model:
            result = self._transcribe_with_gemini(audio_bytes, mime_type, estimated_duration)
            if result.error is None:
                return result
            logger.warning(f"Gemini transcription failed: {result.error}, trying fallback")

        # Fallback to SpeechRecognition
        if self._speech_recognizer:
            result = self._transcribe_with_speech_recognition(audio_bytes, mime_type, estimated_duration)
            if result.error is None:
                return result

        # Both methods failed
        return TranscriptionResult(
            transcript="",
            confidence=0.0,
            duration_seconds=estimated_duration,
            error="Transcription failed - please try again or type your message"
        )

    def _transcribe_with_gemini(
        self,
        audio_bytes: bytes,
        mime_type: str,
        duration: float
    ) -> TranscriptionResult:
        """Transcribe using Gemini's audio understanding."""
        import base64

        try:
            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Build multimodal content with audio
            content = [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": audio_b64,
                    }
                },
                "Transcribe this audio exactly as spoken. Return ONLY the spoken words, nothing else. If the audio is silent or unintelligible, respond with '[SILENT]'."
            ]

            response = self._gemini_model.generate_content(
                content,
                generation_config={
                    "temperature": 0.0,  # Deterministic for transcription
                    "max_output_tokens": 500,
                }
            )

            transcript = response.text.strip()

            # Handle silent/empty recordings
            if transcript == "[SILENT]" or not transcript:
                return TranscriptionResult(
                    transcript="",
                    confidence=0.0,
                    duration_seconds=duration,
                    error="No speech detected in recording"
                )

            logger.info(f"Gemini transcription: '{transcript[:50]}...'")

            return TranscriptionResult(
                transcript=transcript,
                confidence=0.9,  # Gemini doesn't provide confidence, assume high
                duration_seconds=duration,
                error=None
            )

        except Exception as e:
            logger.error(f"Gemini transcription error: {e}")
            return TranscriptionResult(
                transcript="",
                confidence=0.0,
                duration_seconds=duration,
                error=str(e)
            )

    def _transcribe_with_speech_recognition(
        self,
        audio_bytes: bytes,
        mime_type: str,
        duration: float
    ) -> TranscriptionResult:
        """Fallback transcription using SpeechRecognition library."""
        try:
            import speech_recognition as sr

            # SpeechRecognition works best with WAV format
            audio_file = io.BytesIO(audio_bytes)

            with sr.AudioFile(audio_file) as source:
                audio_data = self._speech_recognizer.record(source)

            # Use Google's free speech recognition API
            transcript = self._speech_recognizer.recognize_google(audio_data)

            logger.info(f"SpeechRecognition result: '{transcript[:50]}...'")

            return TranscriptionResult(
                transcript=transcript,
                confidence=0.85,  # Google API doesn't provide confidence
                duration_seconds=duration,
                error=None
            )

        except sr.UnknownValueError:
            return TranscriptionResult(
                transcript="",
                confidence=0.0,
                duration_seconds=duration,
                error="Could not understand audio - try speaking more clearly"
            )
        except sr.RequestError as e:
            logger.error(f"SpeechRecognition API error: {e}")
            return TranscriptionResult(
                transcript="",
                confidence=0.0,
                duration_seconds=duration,
                error=f"Speech recognition service error: {e}"
            )
        except Exception as e:
            logger.error(f"SpeechRecognition error: {e}")
            return TranscriptionResult(
                transcript="",
                confidence=0.0,
                duration_seconds=duration,
                error=str(e)
            )

    def is_available(self) -> bool:
        """Check if speech transcription is available."""
        return self._gemini_model is not None or self._speech_recognizer is not None


def create_speech_client() -> SpeechClient:
    """Factory function to create a SpeechClient instance."""
    return SpeechClient()
