from flask import Blueprint, request, jsonify
import sys
import os

from ..generate_content.youtube_generator import YoutubeGenerator
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
        required_fields = ['topic', 'objective', 'guidelines']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
        
        youtube_data = YoutubeGenerator().generate_youtube_videos(data)
        logger.info("SUCCESSFULLY RAN API CALL")
        
        return jsonify({
            'success': True,
            **youtube_data
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
        required_fields = ['topic', 'objective', 'guidelines', 'user_special_instructions', 'panel_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
        
        # TODO: call our function (should be where we call all specific panel AI function).
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500