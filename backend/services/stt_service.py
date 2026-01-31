import torch
import soundfile as sf
import nemo.collections.asr as nemo_asr
import librosa
import numpy as np
import os

class STTService:
    def __init__(self, models_dir="models"):
        self.device = "cpu"  # Force CPU as per user code, but can use cuda if available
        self.models_dir = models_dir
        self.models = {}
        self.lang_map = {
            "hi": "indicconformer_stt_hi_hybrid_rnnt_large.nemo",
            "ka": "indicconformer_stt_ka_hybrid_rnnt_large.nemo",
            "mr": "indicconformer_stt_mr_hybrid_rnnt_large.nemo"
        }

    def load_model(self, lang_id):
        if lang_id in self.models:
            return self.models[lang_id]
        
        model_filename = self.lang_map.get(lang_id)
        if not model_filename:
            raise ValueError(f"Language {lang_id} not supported for STT")

        model_path = os.path.join(self.models_dir, model_filename)
        
        # Check if model exists, if not warn (in prod we might auto-download)
        if not os.path.exists(model_path):
            print(f"WARNING: Model file {model_path} not found.")
            # For now, we assume models are present.
        
        print(f"Loading STT model for {lang_id} from {model_path}...")
        try:
            model = nemo_asr.models.EncDecCTCModel.restore_from(restore_path=model_path)
            model.eval()
            model = model.to(self.device)
            # Check if model supports hybrid RNNT/CTC, user code sets decoder explicitly
            if hasattr(model, 'cur_decoder'):
                model.cur_decoder = "rnnt" 
            
            self.models[lang_id] = model
            return model
        except Exception as e:
            print(f"Failed to load STT model: {e}")
            raise e

    def transcribe(self, audio_path, lang_id="hi"):
        """
        Transcribe audio file to text.
        """
        model = self.load_model(lang_id)
        
        # Load and preprocess audio
        wav, rate = librosa.load(audio_path, sr=16000, mono=True)
        wav = wav.astype(np.float32)

        # Run transcription
        # NeMo expects a list of numpy arrays
        try:
            transcription = model.transcribe([wav], batch_size=1, logprobs=False, language_id=lang_id)[0]
            # Depending on return format (single string or list), handle it:
            if isinstance(transcription, list):
                return transcription[0]
            return transcription
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

# Singleton instance for easy import
stt_service = STTService()
