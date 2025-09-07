from flask import Blueprint, request, jsonify
import sys
import os

# Add the parent directory to the path to import from openai module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..config.constants import ACCEPT_OR_REJECT

accept_or_reject_bp = Blueprint('accept_or_reject', __name__)

@accept_or_reject_bp.route(ACCEPT_OR_REJECT, methods=['POST'])
def accept_or_reject():
    """
    Provides ability to recognize whether the submission is accepted or rejected.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["panel_name", "panel_name_content_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
    
        # TODO: call our function (should be where we build KG + update DB).
        return jsonify({
            'success': True,
            'data': data
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500