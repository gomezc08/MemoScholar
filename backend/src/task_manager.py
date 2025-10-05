from src.generate_content.youtube_generator import YoutubeGenerator
from src.generate_content.paper_generator import PaperGenerator
from src.db.db_crud.insert import DBInsert
from src.db.db_crud.select_db import DBSelect
from src.utils.logging_config import get_logger
from src.db.db_crud.change import DBChange

class TaskManager:
    def __init__(self):
        self.db_insert = DBInsert()
        self.db_select = DBSelect()
        self.youtube_generator = YoutubeGenerator()
        self.paper_generator = PaperGenerator()
        self.logger = get_logger(__name__)

    def handle_submission(self, data):
        """
        Handle submission based on panel type.
        Returns structured response with generated content IDs.
        """
        panel_name = data.get('panel_name', 'Generic')
        result = {
            'success': True,
            'panel_name': panel_name,
            'papers': [],
            'youtube': []
        }
        
        try:
            # Always create project and query for new submissions
            if panel_name == 'Generic':
                project_id = self._handle_project_task(data)
                query_id = self._handle_default_query_task(data, project_id)
                result['project_id'] = project_id
                result['query_id'] = query_id
            else:
                # For panel-specific submissions, use provided project/query IDs
                project_id = data['project_id']
                query_id = data['query_id']
                
                # Validate that the project and query exist
                if not project_id or not query_id:
                    raise ValueError("Project ID and Query ID are required for panel-specific submissions")
            
            # Handle content generation based on panel type
            if panel_name in ['Generic', 'Papers']:
                papers = self._handle_paper_task(data, project_id, query_id)
                result['papers'] = papers or []
            
            if panel_name in ['Generic', 'YouTube']:
                youtube_videos = self._handle_youtube_task(data, project_id, query_id)
                result['youtube'] = youtube_videos or []
                
        except Exception as e:
            self.logger.error(f"Error in handle_submission: {str(e)}")
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def handle_like_dislike(self, data):
        """
        Create a new like/dislike record in the database.
        Returns like ID or raises exception on failure.
        """
        try:
            # Validate required fields
            required_fields = ['project_id', 'target_type', 'target_id', 'isLiked']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate target_type
            if data['target_type'] not in ['youtube', 'paper']:
                raise ValueError("target_type must be either 'youtube' or 'paper'")
            
            # Validate boolean isLiked
            if not isinstance(data['isLiked'], bool):
                raise ValueError("isLiked must be a boolean value")
            
            # Create the like/dislike record
            like_id = self.db_insert.create_like(
                project_id=data['project_id'],
                target_type=data['target_type'],
                target_id=data['target_id'],
                isLiked=data['isLiked']
            )
            
            if like_id is None:
                error_msg = "Failed to create like/dislike record in database"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self.logger.info(f"Successfully created like/dislike record with ID {like_id}")
            return like_id
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_like_dislike: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_like_dislike: {str(e)}")
            raise RuntimeError(f"Failed to create like/dislike record: {str(e)}")
    
    def handle_like_dislike_update(self, data):
        """
        Update an existing like/dislike record in the database.
        Toggles the isLiked status for the given record.
        """
        try:
            # Validate required fields
            if 'liked_disliked_id' not in data:
                raise ValueError("Missing required field: liked_disliked_id")
            
            # Validate liked_disliked_id is a positive integer
            try:
                liked_disliked_id = int(data['liked_disliked_id'])
                if liked_disliked_id <= 0:
                    raise ValueError("liked_disliked_id must be a positive integer")
            except (ValueError, TypeError):
                raise ValueError("liked_disliked_id must be a positive integer")
            
            # Update the like/dislike record
            success = DBChange().update_like(liked_disliked_id)
            
            if not success:
                error_msg = f"Failed to update like/dislike record with ID {liked_disliked_id}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self.logger.info(f"Successfully updated like/dislike record with ID {liked_disliked_id}")
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_like_dislike_update: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_like_dislike_update: {str(e)}")
            raise RuntimeError(f"Failed to update like/dislike record: {str(e)}")
    
    def handle_user_creation(self, data):
        """
        Create a new user in the database.
        Returns user ID or raises exception on failure.
        """
        
        existing_user = self.db_select.get_user_by_email(data['email'].strip().lower())
        
        if existing_user:
            # User already exists, return existing user info
            self.logger.info(f"User already exists with ID: {existing_user['user_id']}")
            return {
                'success': True,
                'user_id': existing_user['user_id'],
                'name': existing_user['name'],
                'email': existing_user['email']
            }
        
        # Create new user
        user_id = self.db_insert.create_user(data['name'].strip(), data['email'].strip().lower())
        
        if user_id:
            self.logger.info(f"Successfully created user with ID: {user_id}")
            return {
                'success': True,
                'user_id': user_id,
                'name': data['name'].strip(),
                'email': data['email'].strip().lower()
            }
        else:
            self.logger.error("User creation failed")
            return {
                'error': 'User creation failed',
                'success': False
            }
    
    def _handle_project_task(self, data):
        """
        Create a new project in the database.
        Returns project ID or raises exception on failure.
        """
        project_id = self.db_insert.create_project(
            data['user_id'], 
            data['topic'], 
            data['objective'], 
            data['guidelines']
        )
        
        if project_id is None:
            error_msg = "Failed to create project"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        self.logger.info(f"Created project with ID: {project_id}")
        return project_id
    
    def _handle_default_query_task(self, data, project_id):
        """
        Create a default query for the project.
        Returns query ID or raises exception on failure.
        """
        query_text = f"{data['topic']}; {data['objective']}"
        query_id = self.db_insert.create_query(project_id, query_text)
        
        if query_id is None:
            error_msg = "Failed to create query"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.logger.info(f"Created query with ID: {query_id}")
        return query_id
            
    def _handle_paper_task(self, data, project_id, query_id):
        paper_data = self.paper_generator.generate_paper(data)
        papers = paper_data.get('papers', [])
        papers_with_ids = []
        
        for paper in papers:
            # Extract authors from paper data
            authors_list = paper.get('authors', [])
            
            # Create paper with authors
            paper_id = self.db_insert.create_paper_with_authors(
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
                self.logger.info(f"Created paper with ID {paper_id}: {paper.get('title', 'Unknown')}")
            else:
                self.logger.warning(f"Failed to create paper: {paper.get('title', 'Unknown')}")
        
        
        self.logger.info(f"SUCCESSFULLY RAN API CALL - Created project ID: {project_id}")
        self.logger.info(f"Returning {len(papers_with_ids)} papers with IDs")
        return papers_with_ids  
    
    def _handle_youtube_task(self, data, project_id, query_id):
        """
        Generate YouTube videos and insert them into the database.
        Returns list of videos with their database IDs.
        """
        # Generate YouTube videos
        youtube_data = self.youtube_generator.generate_youtube_videos(data)
        youtube_videos = youtube_data.get('youtube', [])
        youtube_with_ids = []
        
        for video in youtube_videos:
            youtube_id = self.db_insert.create_youtube(
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
                self.logger.info(f"Created YouTube video with ID {youtube_id}: {video.get('video_title', 'Unknown')}")
            else:
                self.logger.warning(f"Failed to create YouTube video: {video.get('video_title', 'Unknown')}")
        
        self.logger.info(f"Successfully processed {len(youtube_with_ids)} YouTube videos")
        return youtube_with_ids