from flask import Blueprint, request, jsonify
import sys
import os

from ..task_manager import TaskManager
from ..utils.logging_config import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/users/', methods=['POST'])
def create_user():
    """
    Create a new user and return the user_id.
    """
    logger.info("Received create user API call")
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data or not data[field] or data[field].strip() == '':
                logger.warning(f"Missing or empty required field: {field}")
                return jsonify({
                    'error': f'Missing or empty required field: {field}',
                    'success': False
                }), 400
        
        # Sign up/login user
        user = TaskManager().handle_user_signup(data)
        return jsonify({
            'success': True,
            'user_id': user['user_id'],
            'name': user['name'],
            'email': user['email']
        }), 200
    except Exception as e:
        logger.error(f"Exception in create_user: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@user_bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user information by user_id.
    """
    try:
        user = TaskManager().handle_get_user(user_id)
        return jsonify({
            'success': True,
            'user_id': user['user_id'],
            'name': user['name'],
            'email': user['email']
        }), 200
    except Exception as e:
        logger.error(f"Exception in get_user: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@user_bp.route('/api/users/<int:user_id>/projects', methods=['GET'])
def get_user_projects(user_id):
    """
    Get all projects for a user by user_id.
    """
    try:
        projects = TaskManager().handle_user_projects(user_id)
        return jsonify({
            'success': True,
            'projects': projects
        }), 200
    except Exception as e:
        logger.error(f"Exception in get_user_projects: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@user_bp.route('/api/projects/<int:project_id>/complete', methods=['GET'])
def get_complete_project_data(project_id):
    """
    Get complete project data including project, queries, papers, youtube videos, and likes.
    """
    try:
        complete_data = TaskManager().handle_get_complete_project_data(project_id)
        return jsonify({
            'success': True,
            'project': complete_data['project'],
            'queries': complete_data['queries'],
            'papers': complete_data['papers'],
            'youtube_videos': complete_data['youtube_videos'],
            'likes': complete_data['likes']
        }), 200
    except Exception as e:
        logger.error(f"Exception in get_complete_project_data: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500