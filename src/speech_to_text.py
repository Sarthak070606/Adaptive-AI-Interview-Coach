"""Speech-to-text using Groq Whisper."""
import os
import tempfile
from pathlib import Path
from src.llm_client import get_client


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribe audio bytes using Groq Whisper.
    audio_bytes: raw bytes from Streamlit audio_input or file uploader
    """
    if not audio_bytes:
        return ""

    client = get_client()

    # Write to a temporary file because Groq client expects a file-like object
    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(filename, f),
                model="whisper-large-v3",
                response_format="text",
                language="en"
            )
        # API may return str or object depending on version
        if isinstance(transcription, str):
            return transcription.strip()
        return getattr(transcription, "text", str(transcription)).strip()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
