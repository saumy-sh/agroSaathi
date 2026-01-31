from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from config import Config
from services.stt_service import stt_service
from services.translation_service import translation_service
from services.image_service import MobileNetV2Predictor
from services.rag_service import rag_service
from services.llm_service import llm_service
from services.tts_service import tts_service

api_bp = Blueprint('api', __name__)

# Initialize Image Service (Model path assumed relative or absolute per user setup)
IMAGE_MODEL_PATH = os.path.join(Config.MODELS_DIR, "best_finetuned_model.pth")
if os.path.exists(IMAGE_MODEL_PATH):
    image_predictor = MobileNetV2Predictor(model_path=IMAGE_MODEL_PATH)
else:
    print(f"WARNING: Image model not found at {IMAGE_MODEL_PATH}")
    image_predictor = None

@api_bp.route('/chat', methods=['POST'])
def chat():
    try:
        # 1. Parse Inputs
        language = request.form.get('language', 'en') # e.g., 'hi', 'mr', 'ka'
        audio_file = request.files.get('audio')
        image_file = request.files.get('image')
        text_input = request.form.get('text') # Optional fallback input
        
        user_query_indic = ""
        
        # 2. Handle Audio Input (STT)
        if audio_file:
            filename = secure_filename(audio_file.filename)
            audio_path = os.path.join(Config.TEMP_UPLOAD_DIR, filename)
            audio_file.save(audio_path)
            
            # STT: Audio -> Indic Text
            user_query_indic = stt_service.transcribe(audio_path, lang_id=language)
        elif text_input:
            user_query_indic = text_input
        else:
            return jsonify({"error": "No audio or text input provided"}), 400

        # 3. Handle Image Input (Classification)
        disease_info = "No image provided."
        disease_class = None
        if image_file and image_predictor:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(Config.TEMP_UPLOAD_DIR, filename)
            image_file.save(image_path)
            
            # Predict
            result = image_predictor.predict_single_image(image_path)
            if 'error' not in result:
                disease_class = result['predicted_class']
                confidence = result['confidence']
                disease_info = f"Detected Class: {disease_class} (Confidence: {confidence:.2f})"
            else:
                disease_info = f"Error analyzing image: {result['error']}"

        # 4. Translation (Indic -> English)
        if language != 'en':
            user_query_eng = translation_service.translate_to_en(user_query_indic, spoken_lang=language)
        else:
            user_query_eng = user_query_indic

        # 5. RAG Retrieval
        # Combine user query with disease class for better context search
        search_query = f"{user_query_eng} {disease_class if disease_class else ''}"
        rag_context = rag_service.search(search_query)

        # 6. LLM Reasoning
        llm_response_eng = llm_service.generate_response(
            context=rag_context,
            disease_info=disease_info,
            user_query=user_query_eng
        )

        # 7. Translation (English -> Indic)
        if language != 'en':
            llm_response_indic = translation_service.translate_to_indic(llm_response_eng, target_lang=language)
        else:
            llm_response_indic = llm_response_eng

        # 8. TTS (Indic Text -> Audio)
        # Using a fixed description for now, can be made dynamic if needed
        audio_output_path = tts_service.generate_audio(llm_response_indic)
        audio_filename = os.path.basename(audio_output_path)
        audio_url = f"/api/audio/{audio_filename}"

        return jsonify({
            "user_query_transcribed": user_query_indic,
            "user_query_english": user_query_eng,
            "disease_detected": disease_class,
            "context_retrieved": True if rag_context else False,
            "response_text": llm_response_indic,
            "audio_url": audio_url
        })

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(Config.TEMP_OUTPUT_DIR, filename)
