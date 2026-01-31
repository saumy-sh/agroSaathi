import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import uuid
import os

class TTSService:
    def __init__(self, output_dir="temp/outputs"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model_name = "ai4bharat/indic-parler-tts"
        
        print(f"Loading ParlerTTS model from {self.model_name} on {self.device}...")
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.description_tokenizer = AutoTokenizer.from_pretrained(self.model.config.text_encoder._name_or_path)
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_audio(self, text, description=None):
        """
        Generate audio from text using ParlerTTS.
        """
        if not description:
            # Default description for high quality output
            description = "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up."

        input_ids = self.description_tokenizer(description, return_tensors="pt").input_ids.to(self.device)
        prompt_input_ids = self.tokenizer(text, return_tensors="pt").input_ids.to(self.device)

        with torch.no_grad():
            generation = self.model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
        
        audio_arr = generation.cpu().numpy().squeeze()
        
        # Save to file
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        sf.write(filepath, audio_arr, self.model.config.sampling_rate)
        
        return filepath

tts_service = TTSService()
