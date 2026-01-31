from flask import Flask
from flask_cors import CORS
from api.routes import api_bp
from config import Config

def create_app():
    app = Flask(__name__)
    CORS(app) # Enable CORS for all routes (important for frontend integration)
    
    app.config.from_object(Config)

    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def health_check():
        return {"status": "AgroSaathi Backend is running"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
