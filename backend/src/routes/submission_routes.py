from flask import Blueprint, request, jsonify
import sys
import os

from ..task_manager import TaskManager
from ..utils.logging_config import get_logger

# Add the parent directory to the path to import from openai module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..config.constants import GENERATE_SUBMISSION

# Initialize logger for this module
logger = get_logger(__name__)

submission_bp = Blueprint('submission', __name__)

@submission_bp.route(GENERATE_SUBMISSION, methods=['POST'])
def generate_submission():
    """
    Generate submission content based on topic, objective, and guidelines.
    """
    logger.info("RECIEVED API CALL REQUEST")
    try:
        data = request.get_json()
        
        # Validate required fields
        logger.info(f"DATA: {data}")
        required_fields = ['topic', 'objective', 'guidelines', 'user_id']
        for field in required_fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and data[field].strip() == ''):
                logger.warning(f"Missing or empty required field: {field}")
                return jsonify({
                    'error': f'Missing or empty required field: {field}',
                    'success': False
                }), 400
        
        # Handle submission.
        task_manager_response = TaskManager().handle_submission(data)
        
        return jsonify({
            'success': True,
            'project_id': task_manager_response['project_id'],
            'query_id': task_manager_response['query_id'],
            'youtube': task_manager_response['youtube'],
            'papers': task_manager_response['papers']
        }), 200
    except Exception as e:
        logger.error(f"Exception in generate_submission: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@submission_bp.route(GENERATE_SUBMISSION + "individual_panel/", methods=['POST'])
def generate_submission_individual_panel():
    """
    Generate panel-specific submission content.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        string_fields = ['topic', 'objective', 'guidelines', 'user_special_instructions', 'panel_name', 'user_id']
        for field in string_fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and data[field].strip() == ''):
                return jsonify({
                    'error': f'Missing or empty required field: {field}',
                    'success': False
                }), 400
        
        # Validate ID fields
        id_fields = ['project_id', 'query_id']
        for field in id_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
        
        # handle submission.
        task_manager_response = TaskManager().handle_submission(data)

        return jsonify({
            'success': True,
            'panel_name': task_manager_response['panel_name'],
            'youtube': task_manager_response['youtube'],
            'papers': task_manager_response['papers']
        }), 200
    except Exception as e:
        logger.error(f"Exception in generate_submission: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@submission_bp.route('/api/youtube/<int:youtube_id>', methods=['GET'])
def get_youtube_video(youtube_id):
    """
    Get a single YouTube video by ID.
    """
    try:
        video = TaskManager().handle_get_youtube_video(youtube_id)
        
        if not video:
            return jsonify({
                'error': 'YouTube video not found',
                'success': False
            }), 404
        
        return jsonify({
            'success': True,
            'video': video
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_youtube_video: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@submission_bp.route('/api/papers/<int:paper_id>', methods=['GET'])
def get_paper(paper_id):
    """
    Get a single paper by ID.
    """
    try:
        paper = TaskManager().handle_get_paper(paper_id)
        
        if not paper:
            return jsonify({
                'error': 'Paper not found',
                'success': False
            }), 404
        
        return jsonify({
            'success': True,
            'paper': paper
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_paper: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500