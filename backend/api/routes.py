import os
import uuid
import json
from flask import Blueprint, request, jsonify, send_file
from config import UPLOAD_FOLDER
from services.stt_service import transcribe_audio
from services.translation_service import translate_text
from services.llm_service import get_llm_response
from services.tts_service import text_to_speech
from services.weather_service import get_weather_data
from services.news_service import get_agriculture_news
from utils.helpers import allowed_file, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS

api = Blueprint("api", __name__)


@api.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint. Accepts text, audio, and/or image.
    Flow: STT -> Translate to EN -> LLM (with image if any) -> Translate back -> TTS
    """
    language = request.form.get("language", "en")
    text = request.form.get("text", "").strip()
    audio_file = request.files.get("audio")
    image_file = request.files.get("image")
    conversation_history = json.loads(request.form.get("conversation_history", "[]"))

    print(f"\n{'='*60}")
    print(f"[REQUEST] Language: {language}")
    print(f"[REQUEST] Text: '{text}'")
    print(f"[REQUEST] Audio: {audio_file.filename if audio_file else 'None'}")
    print(f"[REQUEST] Image: {image_file.filename if image_file else 'None'}")

    image_path = None
    audio_path = None

    try:
        # Save image if provided
        if image_file and image_file.filename:
            ext = image_file.filename.rsplit(".", 1)[-1].lower() if "." in image_file.filename else "jpg"
            image_filename = f"img_{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            image_file.save(image_path)
            print(f"[IMAGE] Saved to {image_path}")

        # Save and transcribe audio if provided
        if audio_file and audio_file.filename:
            ext = audio_file.filename.rsplit(".", 1)[-1].lower() if "." in audio_file.filename else "webm"
            audio_filename = f"audio_{uuid.uuid4().hex}.{ext}"
            audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
            audio_file.save(audio_path)
            print(f"[STT] Transcribing audio...")
            text = transcribe_audio(audio_path, language)
            print(f"[STT] Transcribed: '{text}'")

        if not text:
            print(f"[ERROR] No text or audio provided")
            return jsonify({"error": "No text or audio provided"}), 400

        # Translate user text to English
        print(f"[TRANSLATE] {language} -> en")
        english_text = translate_text(text, language, "en")
        print(f"[TRANSLATE] Result: '{english_text}'")

        # Get LLM response (with image if provided)
        print(f"[LLM] Sending to Gemini (image: {bool(image_path)})...")
        llm_response = get_llm_response(english_text, image_path, conversation_history)
        print(f"[LLM] Response: '{llm_response[:200]}...'")

        # Translate response back to user's language
        print(f"[TRANSLATE] en -> {language}")
        translated_response = translate_text(llm_response, "en", language)
        print(f"[TRANSLATE] Result: '{translated_response[:200]}...'")

        # Generate TTS audio
        print(f"[TTS] Generating audio in '{language}'...")
        tts_path = text_to_speech(translated_response, language)
        tts_filename = os.path.basename(tts_path)
        print(f"[TTS] Saved to {tts_path}")

        print(f"[DONE] Request completed successfully")
        print(f"{'='*60}\n")

        return jsonify({
            "transcribed_text": text,
            "response_text": translated_response,
            "audio_url": f"/api/audio/{tts_filename}",
            "english_user_text": english_text,
            "english_response_text": llm_response,
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up uploaded files
        for path in [audio_path, image_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


@api.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    """Serve generated TTS audio files."""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="audio/mpeg")
    return jsonify({"error": "File not found"}), 404

@api.route("/weather", methods=["GET"])
def get_weather():
    """Endpoint to fetch weather data for farmers."""
    lat = request.args.get("lat", 12.9719)
    lon = request.args.get("lon", 77.5937)
    print(f"[API] Weather request received for lat={lat}, lon={lon}")
    data = get_weather_data(lat, lon)
    if "error" in data:
        return jsonify(data), 500
    return jsonify(data)

@api.route("/news", methods=["GET"])
def get_news():
    """Endpoint to fetch agriculture news."""
    data = get_agriculture_news()
    if "error" in data:
        return jsonify(data), 500
    return jsonify(data)
