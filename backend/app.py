import sys
import os

# Add backend directory to path so services can import config
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_cors import CORS
from api.routes import api

app = Flask(__name__)
CORS(app)
app.register_blueprint(api, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
