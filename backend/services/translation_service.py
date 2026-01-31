import torch
from IndicTransToolkit import IndicProcessor
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class TranslationService:
    def __init__(self):
        self.device = "cpu"  # Force CPU as per requests, but switch to cuda if available
        
        # Load English -> Indic Model
        self.en_indic_model_name = "ai4bharat/indictrans2-en-indic-dist-200M"
        self.en_tokenizer = AutoTokenizer.from_pretrained(self.en_indic_model_name, trust_remote_code=True)
        self.en_indic_model = AutoModelForSeq2SeqLM.from_pretrained(self.en_indic_model_name, trust_remote_code=True).to(self.device)
        self.ip_indic = IndicProcessor(inference=True)

        # Load Indic -> English Model
        self.indic_en_model_name = "ai4bharat/indictrans2-indic-en-dist-200M"
        self.indic_tokenizer = AutoTokenizer.from_pretrained(self.indic_en_model_name, trust_remote_code=True)
        self.indic_en_model = AutoModelForSeq2SeqLM.from_pretrained(self.indic_en_model_name, trust_remote_code=True).to(self.device)
        self.ip_en = IndicProcessor(inference=True)

        self.lang_codes = {
            "english": "eng_Latn",   
            "hindi": "hin_Deva",
            "kannada": "kan_Knda",
            "marathi": "mar_Deva",
            "tamil": "tam_Taml" 
        }

    def translate_to_en(self, text, spoken_lang):
        """
        Translate Indic text to English.
        """
        if spoken_lang not in self.lang_codes:
            print(f"Language {spoken_lang} not supported")
            return text 

        print(f"Translating to English: {text} ({spoken_lang})")
        
        sentences = [text]
        
        batch = self.ip_en.preprocess_batch(
            sentences, 
            src_lang=self.lang_codes[spoken_lang], 
            tgt_lang=self.lang_codes["english"], 
            visualize=False
        )
        
        batch = self.indic_tokenizer(
            batch, 
            padding="longest", 
            truncation=True, 
            max_length=256, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.inference_mode():
            outputs = self.indic_en_model.generate(
                **batch, 
                num_beams=5, 
                num_return_sequences=1, 
                max_length=256,
                use_cache=False
            ).to(self.device)
        
        outputs = self.indic_tokenizer.batch_decode(outputs, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        outputs = self.ip_en.postprocess_batch(outputs, self.lang_codes["english"])
        return outputs[0]

    def translate_to_indic(self, text, target_lang):
        """
        Translate English text to Indic language.
        """
        if target_lang not in self.lang_codes:
             print(f"Language {target_lang} not supported")
             return text

        print(f"Translating to {target_lang}: {text}")
        
        sentences = [text]
        
        batch = self.ip_indic.preprocess_batch(
            sentences, 
            src_lang=self.lang_codes["english"], 
            tgt_lang=self.lang_codes[target_lang], 
            visualize=False
        )
        
        batch = self.en_tokenizer(
            batch, 
            padding="longest", 
            truncation=True, 
            max_length=256, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.inference_mode():
            outputs = self.en_indic_model.generate(
                **batch, 
                num_beams=5, 
                num_return_sequences=1, 
                max_length=256,
                use_cache=False
            )
        
        outputs = self.en_tokenizer.batch_decode(outputs, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        outputs = self.ip_indic.postprocess_batch(outputs, self.lang_codes[target_lang])
        return outputs[0]

# Singleton
translation_service = TranslationService()
