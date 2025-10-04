from flask import Blueprint, request, jsonify
import sys
import os

from ..db.db_crud.insert import DBInsert
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
        
        # Check if user already exists by email first
        from ..db.db_crud.select_db import DBSelect
        db_select = DBSelect()
        existing_user = db_select.get_user_by_email(data['email'].strip().lower())
        
        if existing_user:
            # User already exists, return existing user info
            logger.info(f"User already exists with ID: {existing_user['user_id']}")
            return jsonify({
                'success': True,
                'user_id': existing_user['user_id'],
                'name': existing_user['name'],
                'email': existing_user['email']
            }), 200
        
        # Create new user
        db_insert = DBInsert()
        user_id = db_insert.create_user(data['name'].strip(), data['email'].strip().lower())
        
        if user_id:
            logger.info(f"Successfully created user with ID: {user_id}")
            return jsonify({
                'success': True,
                'user_id': user_id,
                'name': data['name'].strip(),
                'email': data['email'].strip().lower()
            }), 200
        else:
            logger.error("User creation failed")
            return jsonify({
                'error': 'User creation failed',
                'success': False
            }), 500
            
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
