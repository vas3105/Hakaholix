import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from gtts import gTTS
import numpy as np
import logging
from pathlib import Path
from scipy import signal
from starlette.background import BackgroundTask

logger = logging.getLogger(_name_)

class VoiceService:
    """Handles voice-to-text (Whisper) and text-to-speech (gTTS)."""

    def _init_(self, whisper_model: str = "openai/whisper-tiny"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts_lang = "en"  # Default language

        # Initialize Whisper (speech-to-text)
        logger.info(f"Loading Whisper model: {whisper_model}")
        self.whisper_processor = WhisperProcessor.from_pretrained(whisper_model)
        self.whisper_model = WhisperForConditionalGeneration.from_pretrained(whisper_model)
        self.whisper_model.to(self.device)
        logger.info("VoiceService initialized (Whisper + gTTS)")

    # -------------------- Speech-to-Text --------------------
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Convert speech to text using Whisper."""
        try:
            if sample_rate != 16000:
                audio_data = self._resample_audio(audio_data, sample_rate, 16000)

            input_features = self.whisper_processor(
                audio_data, sampling_rate=16000, return_tensors="pt"
            ).input_features.to(self.device)

            predicted_ids = self.whisper_model.generate(input_features)
            transcription = self.whisper_processor.batch_decode(
                predicted_ids, skip_special_tokens=True
            )[0]

            logger.info(f"Transcribed: {transcription}")
            return transcription
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    # -------------------- Text-to-Speech --------------------
    def synthesize_speech(self, text: str, output_path: Path) -> Path:
    # Convert text to speech using gTTS (Google Text-to-Speech)
        try:
            tts = gTTS(text=text, lang=self.tts_lang)
            tts.save(str(output_path))
            logger.info(f"Generated speech: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise


    # -------------------- Helper --------------------
    def _resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        if orig_sr == target_sr:
            return audio
        duration = audio.shape[0] / orig_sr
        num_samples = int(duration * target_sr)
        return signal.resample(audio, num_samples)


class StreamingVoiceService:
    """Handles real-time streaming voice interaction."""

    def _init_(self, voice_service: VoiceService):
        self.voice_service = voice_service
        self.audio_buffer = []
        self.is_recording = False

    async def start_recording(self):
        self.is_recording = True
        self.audio_buffer = []
        logger.info("Started recording")

    async def process_audio_chunk(self, audio_chunk: bytes):
        if self.is_recording:
            self.audio_buffer.append(audio_chunk)

    async def stop_recording(self) -> str:
        self.is_recording = False
        if not self.audio_buffer:
            return ""

        audio_data = np.frombuffer(b"".join(self.audio_buffer), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0  # normalize

        transcription = self.voice_service.transcribe_audio(audio_data)
        self.audio_buffer = []
        return transcription
