from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are AgroSaathi, an expert agricultural AI assistant. You help Indian farmers with:
- Crop disease identification and treatment
- Farming best practices and techniques
- Soil health and fertilizer recommendations
- Weather-related farming advice
- Market information and crop selection
- Pest management solutions

Be concise, practical, and give actionable advice. If an image is provided, analyze it for crop/plant health issues."""

def get_llm_response(text: str, image_path: str = None, conversation_history: list = None) -> str:
    """Get response from Gemini API, optionally with an image and conversation history."""
    Content = genai.types.Content
    Part = genai.types.Part

    contents = [
        Content(role="user", parts=[Part.from_text(text=SYSTEM_PROMPT)]),
        Content(role="model", parts=[Part.from_text(text="Understood. I am AgroSaathi, ready to help with agricultural advice.")]),
    ]

    # Add conversation history
    if conversation_history:
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(Content(role=role, parts=[Part.from_text(text=msg["content"])]))

    # Build current user message parts
    current_parts = []
    if image_path:
        import mimetypes
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        with open(image_path, "rb") as f:
            image_data = f.read()
        current_parts.append(Part.from_bytes(data=image_data, mime_type=mime_type))
    current_parts.append(Part.from_text(text=text))

    contents.append(Content(role="user", parts=current_parts))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
    )
    return response.text
