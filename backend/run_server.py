#!/usr/bin/env python3
"""
MemoScholar Flask Application Server
Main entry point that registers all route blueprints and runs the Flask server.
"""

import os
import sys
from flask import Flask, jsonify
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import blueprints
from src.routes.submission_routes import submission_bp
from src.routes.accept_or_reject_routes import accept_or_reject_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(submission_bp)
    app.register_blueprint(accept_or_reject_bp)
    
    # Add a root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information."""
        return jsonify({
            'message': 'MemoScholar API Server',
            'version': '1.0.0',
            'endpoints': {
                'submission': {
                    'POST /generate_submission/': 'Generate submission content',
                    'POST /generate_submission/individual_panel/': 'Generate panel-specific content'
                },
                'accept_reject': {
                    'POST /accept_or_reject/': 'Accept or reject submission'
                },
            }
        })
    
    return app

if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
        
    # Create and run the Flask app
    app = create_app()
    print("Starting MemoScholar Flask Application...")
    app.run(debug=True, host='0.0.0.0', port=5000)