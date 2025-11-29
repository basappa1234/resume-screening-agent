# Vercel serverless function entry point
import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import the Flask app with error handling
try:
    from backend.app import app
    application = app
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
    # Create a simple fallback app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Application is starting up..."
    
    application = app