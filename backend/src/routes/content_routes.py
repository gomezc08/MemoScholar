from flask import Blueprint, request, jsonify
import sys
import os

from ..db.db_crud.insert import DBInsert
from ..utils.logging_config import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

youtube_bp = Blueprint('youtube', __name__)

@youtube_bp.route('/api/youtube/', methods=['POST'])
def add_youtube_content():
    """
    Add youtube content to the database.
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
        
    except Exception as e:
        logger.error(f"Exception in add_youtube_content: {str(e)}")
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
        from ..db.db_crud.select_db import DBSelect
        db_select = DBSelect()
        user = db_select.get_user(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email']
            }), 200
        else:
            return jsonify({
                'error': 'User not found',
                'success': False
            }), 404
            
    except Exception as e:
        logger.error(f"Exception in get_user: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
