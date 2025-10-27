from src.generate_content.youtube_generator import YoutubeGenerator
from src.generate_content.paper_generator import PaperGenerator
from src.db.db_crud.insert import DBInsert
from src.db.db_crud.select_db import DBSelect
from src.utils.logging_config import get_logger
from src.db.db_crud.change import DBChange
from src.generate_content.create_query import CreateQuery
from src.text_embedding.embedding import Embedding

class TaskManager:
    def __init__(self):
        self.db_insert = DBInsert()
        self.db_select = DBSelect()
        self.youtube_generator = YoutubeGenerator()
        self.paper_generator = PaperGenerator()
        self.create_query = CreateQuery()
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
                self.logger.info("Handling Generic panel submission")
                project_id = self._handle_project_task(data)
                query_id = self._handle_default_query_task(data, project_id)
                result['project_id'] = project_id
                result['query_id'] = query_id
            else:
                # For panel-specific submissions, use provided project/query IDs
                self.logger.info(f"Handling panel-specific submission: {panel_name}")
                project_id = data['project_id']
                self.logger.info(f"Using project_id: {project_id}")
                query_id = self._handle_query_task(data, project_id)
                self.logger.info(f"Generated query_id: {query_id}")
                
                # Validate that the project exists
                if project_id is None:
                    raise ValueError("Project ID is required for panel-specific submissions")
                
                # If query_id is 0 or None, create a default query
                if query_id is None or query_id == 0:
                    self.logger.info("Creating default query as backup")
                    query_id = self._handle_default_query_task(data, project_id)
            
            self.logger.info(f"here is the project id: {project_id}")
            
            # Handle content generation based on panel type
            if panel_name in ['Generic', 'YouTube']:
                self.logger.info("Generating YouTube videos")
                youtube_videos = self._handle_youtube_task(data, project_id, query_id)
                result['youtube'] = youtube_videos or []
                
            if panel_name in ['Generic', 'Papers']:
                self.logger.info("Generating papers")
                papers = self._handle_paper_task(data, project_id, query_id)
                result['papers'] = papers or []
            
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
    
    def handle_user_signup(self, data):
        """
        Create a new user in the database.
        Returns user data or raises exception on failure.
        """
        try:
            # Validate required fields
            required_fields = ['name', 'email']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if user already exists
            existing_user = self.db_select.get_user_by_email(data['email'].strip().lower())
            
            if existing_user:
                # User already exists, return existing user info
                self.logger.info(f"User already exists with ID: {existing_user['user_id']}")
                return {
                    'user_id': existing_user['user_id'],
                    'name': existing_user['name'],
                    'email': existing_user['email']
                }
            
            # Create new user
            user_id = self.db_insert.create_user(data['name'].strip(), data['email'].strip().lower())
            
            if user_id is None:
                raise RuntimeError("Failed to create user in database")
            
            self.logger.info(f"Successfully created user with ID: {user_id}")
            return {
                'user_id': user_id,
                'name': data['name'].strip(),
                'email': data['email'].strip().lower()
            }
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_user_signup: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_user_signup: {str(e)}")
            raise RuntimeError(f"Failed to handle user signup: {str(e)}")
    
    def handle_user_login(self, data):
        """
        Login a user by email.
        Returns user data or raises exception on failure.
        """
        try:
            # Validate required fields
            if 'email' not in data:
                raise ValueError("Missing required field: email")
            
            # Get user by email
            user = self.db_select.get_user_by_email(data['email'].strip().lower())
            
            if not user:
                raise ValueError("User not found with this email")
            
            self.logger.info(f"User login successful for ID: {user['user_id']}")
            return {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email']
            }
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_user_login: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_user_login: {str(e)}")
            raise RuntimeError(f"Failed to handle user login: {str(e)}")
    
    def handle_get_user(self, user_id):
        """
        Get user information by user_id.
        Returns user data or raises exception on failure.
        """
        try:
            # Validate user_id
            if not user_id or user_id <= 0:
                raise ValueError("Invalid user_id provided")
            
            # Get user by user_id
            user = self.db_select.get_user(user_id)
            
            if not user:
                raise ValueError("User not found with this ID")
            
            self.logger.info(f"Retrieved user with ID: {user['user_id']}")
            return {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email']
            }
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_get_user: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_get_user: {str(e)}")
            raise RuntimeError(f"Failed to get user: {str(e)}")
    
    def handle_user_projects(self, user_id):
        """
        Get all projects for a user by user_id.
        Returns list of projects or raises exception on failure.
        """
        try:
            # Validate user_id
            if not user_id or user_id <= 0:
                raise ValueError("Invalid user_id provided")
            
            # Get projects for user
            projects = self.db_select.get_user_projects(user_id)
            
            if projects is None:
                raise RuntimeError("Failed to retrieve projects from database")
            
            self.logger.info(f"Retrieved {len(projects)} projects for user ID: {user_id}")
            return projects
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_user_projects: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_user_projects: {str(e)}")
            raise RuntimeError(f"Failed to get user projects: {str(e)}")

    def handle_get_likes_for_project(self, project_id):
        """
        Get all likes for a project by project_id.
        Returns list of likes or raises exception on failure.
        """
        try:
            # Validate project_id
            if not project_id or project_id <= 0:
                raise ValueError("Invalid project_id provided")
            
            # Get likes for project
            likes = self.db_select.get_likes_for_project(project_id)
            
            if likes is None:
                raise RuntimeError("Failed to retrieve likes from database")
            
            self.logger.info(f"Retrieved {len(likes)} likes for project ID: {project_id}")
            return likes
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_get_likes_for_project: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_get_likes_for_project: {str(e)}")
            raise RuntimeError(f"Failed to get likes for project: {str(e)}")

    def handle_get_complete_project_data(self, project_id):
        """
        Get complete project data including project, queries, papers, youtube videos, and likes.
        Returns complete project data or raises exception on failure.
        """
        try:
            # Validate project_id
            if not project_id or project_id <= 0:
                raise ValueError("Invalid project_id provided")
            
            # Get complete project data
            complete_data = self.db_select.get_complete_project_data(project_id)
            
            if complete_data is None:
                raise RuntimeError("Failed to retrieve project data from database")
            
            self.logger.info(f"Retrieved complete data for project ID: {project_id}")
            return complete_data
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_get_complete_project_data: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_get_complete_project_data: {str(e)}")
            raise RuntimeError(f"Failed to get complete project data: {str(e)}")

    def handle_get_youtube_video(self, youtube_id):
        """
        Get a single YouTube video by ID.
        Returns video data or None if not found.
        """
        try:
            # Validate youtube_id
            if not youtube_id or youtube_id <= 0:
                raise ValueError("Invalid youtube_id provided")
            
            # Get YouTube video by ID
            video = self.db_select.get_youtube_video(youtube_id)
            
            if not video:
                self.logger.info(f"YouTube video not found with ID: {youtube_id}")
                return None
            
            self.logger.info(f"Retrieved YouTube video with ID: {youtube_id}")
            return video
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_get_youtube_video: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_get_youtube_video: {str(e)}")
            raise RuntimeError(f"Failed to get YouTube video: {str(e)}")

    def handle_get_youtube_video_from_recs(self, rec_id):
        """
        Get a single YouTube video from youtube_current_recs by rec_id.
        Returns video data or None if not found.
        """
        try:
            # Validate rec_id
            if not rec_id or rec_id <= 0:
                raise ValueError("Invalid rec_id provided")
            
            # Get YouTube video from recs by rec_id
            video = self.db_select.get_youtube_video_from_youtube_current_recs(rec_id)
            
            if not video:
                self.logger.info(f"YouTube video not found in current recs with rec_id: {rec_id}")
                return None
            
            self.logger.info(f"Retrieved YouTube video from recs with rec_id: {rec_id}")
            return video
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_get_youtube_video_from_recs: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_get_youtube_video_from_recs: {str(e)}")
            raise RuntimeError(f"Failed to get YouTube video from recs: {str(e)}")

    def handle_get_paper(self, paper_id):
        """
        Get a single paper by ID.
        Returns paper data or None if not found.
        """
        try:
            # Validate paper_id
            if not paper_id or paper_id <= 0:
                raise ValueError("Invalid paper_id provided")
            
            # Get paper by ID
            paper = self.db_select.get_paper(paper_id)
            
            if not paper:
                self.logger.info(f"Paper not found with ID: {paper_id}")
                return None
            
            self.logger.info(f"Retrieved paper with ID: {paper_id}")
            return paper
            
        except ValueError as e:
            self.logger.error(f"Validation error in handle_get_paper: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_get_paper: {str(e)}")
            raise RuntimeError(f"Failed to get paper: {str(e)}")

    
    def _handle_project_task(self, data):
        """
        Create a new project in the database.
        Returns project ID or raises exception on failure.
        """
        # create embedding for the project.
        embedding_text = f"{data['topic']}; {data['objective']}; {data['guidelines']}"
        embedding = Embedding().embed_text(embedding_text)
        self.logger.info(f"Embedding type: {type(embedding)}")
        project_id = self.db_insert.create_project(
            data['user_id'], 
            data['topic'], 
            data['objective'], 
            data['guidelines'],
            embedding
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
    
    def _handle_query_task(self, data, project_id):
        query_response = self.create_query.generate_paper_query(data)
        
        # Check if the response is successful and extract content
        if not query_response or not query_response.get('success', False):
            error_msg = "Failed to generate query"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        query_text = query_response['content']
        query_id = self.db_insert.create_query(project_id, query_text)
        
        if query_id is None:
            error_msg = "Failed to create query"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        self.logger.info(f"Created query with ID: {query_id}")
        return query_id
            
    def _handle_paper_task(self, data, project_id, query_id):
        self.logger.info(f"Starting paper task for project_id: {project_id}, query_id: {query_id}")
        query_result = self.db_select.get_query(query_id)
        if not query_result:
            error_msg = f"Query not found with ID: {query_id}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        self.logger.info(f"Retrieved query result: {query_result}")
        paper_data = self.paper_generator.generate_paper(data, query_result)
        self.logger.info(f"Generated paper data: {type(paper_data)}")
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
        # add project id to data.
        data['project_id'] = project_id
        # Generate YouTube videos
        self.logger.info(f"Starting YouTube task for project_id: {project_id}, query_id: {query_id}")
        query_result = self.db_select.get_query(query_id)
        if not query_result:
            error_msg = f"Query not found with ID: {query_id}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        self.logger.info(f"Retrieved query result: {query_result}")
        query_text = query_result['queries_text']
        self.logger.info(f"Extracted query text: {query_text}")
        youtube_data = self.youtube_generator.generate_youtube_videos(data, query_result)
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