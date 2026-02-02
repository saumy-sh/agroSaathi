ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "ogg", "webm", "m4a"}

def allowed_file(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed
