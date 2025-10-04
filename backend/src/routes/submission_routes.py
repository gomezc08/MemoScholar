from flask import Blueprint, request, jsonify
import sys
import os

from ..generate_content.youtube_generator import YoutubeGenerator
from ..generate_content.paper_generator import PaperGenerator
from ..utils.logging_config import get_logger
from ..db.db_crud.insert import DBInsert

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
        
        youtube_data = YoutubeGenerator().generate_youtube_videos(data)
        paper_data = PaperGenerator().generate_paper(data)
        
        # Create project and check if it was successful
        project_id = DBInsert().create_project(data['user_id'], data['topic'], data['objective'], data['guidelines'])
        if project_id is None:
            logger.error("Failed to create project")
            return jsonify({
                'error': 'Failed to create project',
                'success': False
            }), 500
        
        # Create query.
        query_id = DBInsert().create_query(project_id, data['topic'] + ";" + data['objective'])
        if query_id is None:
            logger.error("Failed to create query")
            return jsonify({
                'error': 'Failed to create query',
                'success': False
            }), 500
        
        # Update youtube and paper tables.
        # Handle YouTube videos - insert each video individually
        youtube_videos = youtube_data.get('youtube', [])
        youtube_with_ids = []
        db_insert = DBInsert()
        
        for video in youtube_videos:
            youtube_id = db_insert.create_youtube(
                project_id, 
                query_id, 
                video.get('video_title', ''), 
                video.get('video_description', ''), 
                video.get('video_duration', ''), 
                video.get('video_url', ''), 
                video.get('video_views', 0), 
                video.get('video_likes', 0)
            )
            
            if youtube_id:
                # Add database ID to the video data
                video_with_id = video.copy()
                video_with_id['youtube_id'] = youtube_id
                youtube_with_ids.append(video_with_id)
                logger.info(f"Created YouTube video with ID {youtube_id}: {video.get('video_title', 'Unknown')}")
            else:
                logger.warning(f"Failed to create YouTube video: {video.get('video_title', 'Unknown')}")
        
        # Handle papers - insert each paper individually with authors
        papers = paper_data.get('papers', [])
        papers_with_ids = []
        
        for paper in papers:
            # Extract authors from paper data
            authors_list = paper.get('authors', [])
            
            # Create paper with authors
            paper_id = db_insert.create_paper_with_authors(
                project_id, 
                query_id, 
                paper.get('title', ''), 
                paper.get('summary', ''), 
                paper.get('year', 2024), 
                paper.get('pdf_link', ''),
                authors_list
            )
            
            if paper_id:
                # Add database ID to the paper data
                paper_with_id = paper.copy()
                paper_with_id['paper_id'] = paper_id
                papers_with_ids.append(paper_with_id)
                logger.info(f"Created paper with ID {paper_id}: {paper.get('title', 'Unknown')}")
            else:
                logger.warning(f"Failed to create paper: {paper.get('title', 'Unknown')}")
        
        
        logger.info(f"SUCCESSFULLY RAN API CALL - Created project ID: {project_id}")
        logger.info(f"Returning {len(youtube_with_ids)} YouTube videos with IDs")
        logger.info(f"Returning {len(papers_with_ids)} papers with IDs")
        if youtube_with_ids:
            logger.info(f"First YouTube video: {youtube_with_ids[0]}")
        if papers_with_ids:
            logger.info(f"First paper: {papers_with_ids[0]}")
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'youtube': youtube_with_ids,
            'papers': papers_with_ids
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
        required_fields = ['topic', 'objective', 'guidelines', 'user_special_instructions', 'panel_name', 'user_id']
        for field in required_fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and data[field].strip() == ''):
                return jsonify({
                    'error': f'Missing or empty required field: {field}',
                    'success': False
                }), 400
        
        # Create project first (this will be idempotent if project already exists)
        db_insert = DBInsert()
        
        if data['panel_name'] == 'Papers':
            paper_data = PaperGenerator().generate_paper(data)
            
            # Create project with user_id
            db_insert.create_project(
                user_id=data['user_id'],
                topic=data['topic'],
                objective=data['objective'],
                guidelines=data['guidelines']
            )
            
            return jsonify({
                'success': True,
                'panel_name': data['panel_name'],
                'papers': paper_data.get('papers', [])
            }), 200
        elif data['panel_name'] == 'YouTube':
            youtube_data = YoutubeGenerator().generate_youtube_videos(data)
            
            # Create project with user_id
            db_insert.create_project(
                user_id=data['user_id'],
                topic=data['topic'],
                objective=data['objective'],
                guidelines=data['guidelines']
            )
            
            return jsonify({
                'success': True,
                'panel_name': data['panel_name'],
                'youtube': youtube_data.get('youtube', [])
            }), 200
    except Exception as e:
        logger.error(f"Exception in generate_submission: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500