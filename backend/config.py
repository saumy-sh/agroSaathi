import os

class Config:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    MODELS_DIR = os.path.join(os.getcwd(), "backend", "models")
    TEMP_UPLOAD_DIR = os.path.join(os.getcwd(), "backend", "temp", "uploads")
    TEMP_OUTPUT_DIR = os.path.join(os.getcwd(), "backend", "temp", "outputs")
    VECTOR_DB_DIR = os.path.join(os.getcwd(), "backend", "data", "vector_store")
    
    # Ensure dirs exist
    os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
    os.makedirs(TEMP_OUTPUT_DIR, exist_ok=True)
