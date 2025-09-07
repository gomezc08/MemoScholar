from flask import Flask, request, jsonify
import sys
import os

# Add the parent directory to the path to import from openai module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import GENERATE_SUBMISSION

app = Flask(__name__)

@app.route(GENERATE_SUBMISSION, methods=['POST'])
def generate_submission():
    """
    Generate submission content based on topic, objective, and guidelines.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['topic', 'objective', 'guidelines']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
    
        # placeholder.
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route(GENERATE_SUBMISSION + "panel/", methods=['POST'])
def generate_submission_panel():
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
        
        # placeholder.
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)