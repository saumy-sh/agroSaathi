from deep_translator import GoogleTranslator

def translate_text(text: str, src_lang: str, dest_lang: str) -> str:
    """Translate text between languages using Google Translate."""
    if src_lang == dest_lang:
        return text
    try:
        result = GoogleTranslator(source=src_lang, target=dest_lang).translate(text)
        return result
    except Exception as e:
        print(f"Translation error: {e}")
        return text
