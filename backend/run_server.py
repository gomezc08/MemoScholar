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
from src.routes.like_dislike_routes import like_dislike_bp
from src.routes.user_routes import user_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(submission_bp)
    app.register_blueprint(like_dislike_bp)
    app.register_blueprint(user_bp)
    
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
                'like_dislike': {
                    'POST /like_dislike/': 'Like or dislike submission'
                },
                'user': {
                    'POST /api/users/': 'Create or get user',
                    'GET /api/users/<user_id>': 'Get user by ID'
                },
            }
        })
    
    return app