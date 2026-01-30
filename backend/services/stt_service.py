import os
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def transcribe_audio(audio_path: str, language: str = "en") -> str:
    """Transcribe audio using Groq Whisper API."""
    lang_map = {"en": "en", "hi": "hi", "mr": "mr", "kn": "kn", "ta": "ta"}
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model="whisper-large-v3",
            language=lang_map.get(language, "en"),
            response_format="text",
        )
    return transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
