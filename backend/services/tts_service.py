import asyncio
import edge_tts
import os
import uuid
from config import UPLOAD_FOLDER

VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "mr": "mr-IN-AarohiNeural",
    "kn": "kn-IN-SapnaNeural",
    "ta": "ta-IN-PallaviNeural",
}

async def _synthesize(text: str, language: str, output_path: str):
    voice = VOICE_MAP.get(language, "en-IN-NeerjaNeural")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def text_to_speech(text: str, language: str = "en") -> str:
    """Convert text to speech using Edge TTS. Returns path to audio file."""
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(UPLOAD_FOLDER, filename)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_synthesize(text, language, output_path))
    finally:
        loop.close()

    return output_path
