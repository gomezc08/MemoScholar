from flask import Blueprint, request, jsonify
import sys
import os

# Add the parent directory to the path to import from openai module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..db.db_crud.insert import DBInsert
from ..config.constants import ACCEPT_OR_REJECT

accept_or_reject_bp = Blueprint('accept_or_reject', __name__)

@accept_or_reject_bp.route(ACCEPT_OR_REJECT, methods=['POST'])
def accept_or_reject():
    """
    Provides ability to recognize whether the submission is accepted or rejected.
    Creates a like/dislike record in the database.
    """
    try:
        data = request.get_json()
        
        # Validate required fields for create_like function
        required_fields = ["project_id", "target_type", "target_id", "isLiked"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
        
        # Validate target_type is either 'youtube' or 'paper'
        if data['target_type'] not in ['youtube', 'paper']:
            return jsonify({
                'error': 'target_type must be either "youtube" or "paper"',
                'success': False
            }), 400
        
        # Validate isLiked is boolean
        if not isinstance(data['isLiked'], bool):
            return jsonify({
                'error': 'isLiked must be a boolean value',
                'success': False
            }), 400
        
        # Create the like/dislike record
        like_id = DBInsert().create_like(
            project_id=data['project_id'],
            target_type=data['target_type'],
            target_id=data['target_id'],
            isLiked=data['isLiked']
        )
        
        if like_id is None:
            return jsonify({
                'error': 'Failed to create like/dislike record',
                'success': False
            }), 500
        
        return jsonify({
            'success': True,
            'like_id': like_id,
            'message': f'Successfully {"liked" if data["isLiked"] else "disliked"} {data["target_type"]} item'
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500