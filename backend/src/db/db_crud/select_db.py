import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBSelect:
    def __init__(self):
        self.connector = Connector()
    
    def get_user(self, user_id):
        """Get a single user by ID"""
        self.connector.open_connection()
        try:
            query = "SELECT user_id, name, email FROM users WHERE user_id = %s"
            self.connector.cursor.execute(query, (user_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'name': result[1],
                    'email': result[2]
                }
            return None
        except Exception as e:
            print(f"get_user error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_user_by_email(self, email):
        """Get a user by email"""
        self.connector.open_connection()
        try:
            query = "SELECT user_id, name, email FROM users WHERE email = %s"
            self.connector.cursor.execute(query, (email,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'name': result[1],
                    'email': result[2]
                }
            return None
        except Exception as e:
            print(f"get_user_by_email error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_all_users(self):
        """Get all users"""
        self.connector.open_connection()
        try:
            query = "SELECT user_id, name, email FROM users ORDER BY user_id"
            self.connector.cursor.execute(query)
            results = self.connector.cursor.fetchall()
            return [
                {
                    'user_id': row[0],
                    'name': row[1],
                    'email': row[2]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_all_users error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_user_projects(self, user_id):
        """Get all projects for a user"""
        self.connector.open_connection()
        try:
            query = """
                SELECT project_id, user_id, topic, objective, guidelines 
                FROM project 
                WHERE user_id = %s 
                ORDER BY project_id
            """
            self.connector.cursor.execute(query, (user_id,))
            results = self.connector.cursor.fetchall()
            return [
                {
                    'project_id': row[0],
                    'user_id': row[1],
                    'topic': row[2],
                    'objective': row[3],
                    'guidelines': row[4]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_user_projects error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_project(self, project_id):
        """Get a single project by ID"""
        self.connector.open_connection()
        try:
            query = """
                SELECT project_id, user_id, topic, objective, guidelines 
                FROM project 
                WHERE project_id = %s
            """
            self.connector.cursor.execute(query, (project_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'project_id': result[0],
                    'user_id': result[1],
                    'topic': result[2],
                    'objective': result[3],
                    'guidelines': result[4]
                }
            return None
        except Exception as e:
            print(f"get_project error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_all_projects(self):
        """Get all projects"""
        self.connector.open_connection()
        try:
            query = """
                SELECT project_id, user_id, topic, objective, guidelines 
                FROM project 
                ORDER BY project_id
            """
            self.connector.cursor.execute(query)
            results = self.connector.cursor.fetchall()
            return [
                {
                    'project_id': row[0],
                    'user_id': row[1],
                    'topic': row[2],
                    'objective': row[3],
                    'guidelines': row[4]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_all_projects error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_project_queries(self, project_id):
        """Get all queries for a project"""
        self.connector.open_connection()
        try:
            query = """
                SELECT query_id, project_id, queries_text, special_instructions 
                FROM queries 
                WHERE project_id = %s 
                ORDER BY query_id
            """
            self.connector.cursor.execute(query, (project_id,))
            results = self.connector.cursor.fetchall()
            return [
                {
                    'query_id': row[0],
                    'project_id': row[1],
                    'queries_text': row[2],
                    'special_instructions': row[3]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_project_queries error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_query(self, query_id):
        """Get a single query by ID"""
        self.connector.open_connection()
        try:
            query = """
                SELECT query_id, project_id, queries_text, special_instructions 
                FROM queries 
                WHERE query_id = %s
            """
            self.connector.cursor.execute(query, (query_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'query_id': result[0],
                    'project_id': result[1],
                    'queries_text': result[2],
                    'special_instructions': result[3]
                }
            return None
        except Exception as e:
            print(f"get_query error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_project_papers(self, project_id):
        """Get all papers for a project"""
        self.connector.open_connection()
        try:
            query = """
                SELECT paper_id, project_id, query_id, paper_title, paper_summary, 
                       published_year, pdf_link 
                FROM papers 
                WHERE project_id = %s 
                ORDER BY paper_id
            """
            self.connector.cursor.execute(query, (project_id,))
            results = self.connector.cursor.fetchall()
            return [
                {
                    'paper_id': row[0],
                    'project_id': row[1],
                    'query_id': row[2],
                    'paper_title': row[3],
                    'paper_summary': row[4],
                    'published_year': row[5],
                    'pdf_link': row[6]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_project_papers error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_paper(self, paper_id):
        """Get a single paper by ID"""
        self.connector.open_connection()
        try:
            query = """
                SELECT paper_id, project_id, query_id, paper_title, paper_summary, 
                       published_year, pdf_link 
                FROM papers 
                WHERE paper_id = %s
            """
            self.connector.cursor.execute(query, (paper_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'paper_id': result[0],
                    'project_id': result[1],
                    'query_id': result[2],
                    'paper_title': result[3],
                    'paper_summary': result[4],
                    'published_year': result[5],
                    'pdf_link': result[6]
                }
            return None
        except Exception as e:
            print(f"get_paper error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_paper_with_authors(self, paper_id):
        """Get a paper with all its authors"""
        self.connector.open_connection()
        try:
            # Get paper info
            paper_query = """
                SELECT p.paper_id, p.project_id, p.query_id, p.paper_title, 
                       p.paper_summary, p.published_year, p.pdf_link 
                FROM papers p 
                WHERE p.paper_id = %s
            """
            self.connector.cursor.execute(paper_query, (paper_id,))
            paper_result = self.connector.cursor.fetchone()
            
            if not paper_result:
                return None
            
            # Get authors for this paper
            authors_query = """
                SELECT a.author_id, a.name 
                FROM authors a 
                JOIN paperauthors pa ON a.author_id = pa.author_id 
                WHERE pa.paper_id = %s 
                ORDER BY a.name
            """
            self.connector.cursor.execute(authors_query, (paper_id,))
            author_results = self.connector.cursor.fetchall()
            
            authors = [
                {
                    'author_id': row[0],
                    'name': row[1]
                }
                for row in author_results
            ]
            
            return {
                'paper_id': paper_result[0],
                'project_id': paper_result[1],
                'query_id': paper_result[2],
                'paper_title': paper_result[3],
                'paper_summary': paper_result[4],
                'published_year': paper_result[5],
                'pdf_link': paper_result[6],
                'authors': authors
            }
        except Exception as e:
            print(f"get_paper_with_authors error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_project_youtube_videos(self, project_id):
        """Get all YouTube videos for a project"""
        self.connector.open_connection()
        try:
            query = """
                SELECT youtube_id, project_id, query_id, video_title, video_description, 
                       video_duration, video_url, video_views, video_likes 
                FROM youtube 
                WHERE project_id = %s 
                ORDER BY youtube_id
            """
            self.connector.cursor.execute(query, (project_id,))
            results = self.connector.cursor.fetchall()
            return [
                {
                    'youtube_id': row[0],
                    'project_id': row[1],
                    'query_id': row[2],
                    'video_title': row[3],
                    'video_description': row[4],
                    'video_duration': str(row[5]) if row[5] else None,  # Convert TIME to string
                    'video_url': row[6],
                    'video_views': row[7],
                    'video_likes': row[8]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_project_youtube_videos error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_youtube_video(self, youtube_id):
        """Get a single YouTube video by ID"""
        self.connector.open_connection()
        try:
            query = """
                SELECT youtube_id, project_id, query_id, video_title, video_description, 
                       video_duration, video_url, video_views, video_likes 
                FROM youtube 
                WHERE youtube_id = %s
            """
            self.connector.cursor.execute(query, (youtube_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'youtube_id': result[0],
                    'project_id': result[1],
                    'query_id': result[2],
                    'video_title': result[3],
                    'video_description': result[4],
                    'video_duration': str(result[5]) if result[5] else None,
                    'video_url': result[6],
                    'video_views': result[7],
                    'video_likes': result[8]
                }
            return None
        except Exception as e:
            print(f"get_youtube_video error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_author(self, author_id):
        """Get a single author by ID"""
        self.connector.open_connection()
        try:
            query = "SELECT author_id, name FROM authors WHERE author_id = %s"
            self.connector.cursor.execute(query, (author_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'author_id': result[0],
                    'name': result[1]
                }
            return None
        except Exception as e:
            print(f"get_author error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_all_authors(self):
        """Get all authors"""
        self.connector.open_connection()
        try:
            query = "SELECT author_id, name FROM authors ORDER BY name"
            self.connector.cursor.execute(query)
            results = self.connector.cursor.fetchall()
            return [
                {
                    'author_id': row[0],
                    'name': row[1]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_all_authors error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_likes_for_project(self, project_id):
        """Get all likes for a project"""
        self.connector.open_connection()
        try:
            query = """
                SELECT liked_disliked_id, project_id, target_type, target_id, isLiked 
                FROM likes 
                WHERE project_id = %s 
                ORDER BY liked_disliked_id
            """
            self.connector.cursor.execute(query, (project_id,))
            results = self.connector.cursor.fetchall()
            return [
                {
                    'liked_disliked_id': row[0],
                    'project_id': row[1],
                    'target_type': row[2],
                    'target_id': row[3],
                    'isLiked': row[4]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_likes_for_project error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_likes_for_item(self, project_id, target_type, target_id):
        """Get likes for a specific item (paper or youtube video)"""
        self.connector.open_connection()
        try:
            query = """
                SELECT liked_disliked_id, project_id, target_type, target_id, isLiked 
                FROM likes 
                WHERE project_id = %s AND target_type = %s AND target_id = %s
            """
            self.connector.cursor.execute(query, (project_id, target_type, target_id))
            results = self.connector.cursor.fetchall()
            return [
                {
                    'liked_disliked_id': row[0],
                    'project_id': row[1],
                    'target_type': row[2],
                    'target_id': row[3],
                    'isLiked': row[4]
                }
                for row in results
            ]
        except Exception as e:
            print(f"get_likes_for_item error: {e}")
            return []
        finally:
            self.connector.close_connection()
    
    def get_like(self, liked_disliked_id):
        """Get a single like by ID"""
        self.connector.open_connection()
        try:
            query = """
                SELECT liked_disliked_id, project_id, target_type, target_id, isLiked 
                FROM likes 
                WHERE liked_disliked_id = %s
            """
            self.connector.cursor.execute(query, (liked_disliked_id,))
            result = self.connector.cursor.fetchone()
            if result:
                return {
                    'liked_disliked_id': result[0],
                    'project_id': result[1],
                    'target_type': result[2],
                    'target_id': result[3],
                    'isLiked': result[4]
                }
            return None
        except Exception as e:
            print(f"get_like error: {e}")
            return None
        finally:
            self.connector.close_connection()
    
    def get_complete_project_data(self, project_id):
        """Get complete project data including all related entities"""
        self.connector.open_connection()
        try:
            # Get project info
            project = self.get_project(project_id)
            if not project:
                return None
            
            # Get related data
            queries = self.get_project_queries(project_id)
            papers = self.get_project_papers(project_id)
            youtube_videos = self.get_project_youtube_videos(project_id)
            likes = self.get_likes_for_project(project_id)
            
            # Get authors for each paper
            papers_with_authors = []
            for paper in papers:
                paper_with_authors = self.get_paper_with_authors(paper['paper_id'])
                papers_with_authors.append(paper_with_authors)
            
            return {
                'project': project,
                'queries': queries,
                'papers': papers_with_authors,
                'youtube_videos': youtube_videos,
                'likes': likes
            }
        except Exception as e:
            print(f"get_complete_project_data error: {e}")
            return None
        finally:
            self.connector.close_connection()


if __name__ == '__main__':
    db_select = DBSelect()
    
    print("🧪 Testing DBSelect operations...")
    print("=" * 50)
    
    # Test 1: Get all users
    print("\n1. Testing get_all_users()...")
    users = db_select.get_all_users()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  - {user['name']} ({user['email']}) - ID: {user['user_id']}")
    
    # Test 2: Get user by ID (if users exist)
    if users:
        print(f"\n2. Testing get_user(user_id={users[0]['user_id']})...")
        user = db_select.get_user(users[0]['user_id'])
        if user:
            print(f"  Found user: {user['name']} ({user['email']})")
        else:
            print("  No user found")
    
    # Test 3: Get all projects
    print("\n3. Testing get_all_projects()...")
    projects = db_select.get_all_projects()
    print(f"Found {len(projects)} projects:")
    for project in projects:
        print(f"  - {project['topic']} (User ID: {project['user_id']}) - Project ID: {project['project_id']}")
    
    # Test 4: Get project by ID (if projects exist)
    if projects:
        project_id = projects[0]['project_id']
        print(f"\n4. Testing get_project(project_id={project_id})...")
        project = db_select.get_project(project_id)
        if project:
            print(f"  Found project: {project['topic']}")
            print(f"  Objective: {project['objective'][:100]}...")
        
        # Test 5: Get project queries
        print(f"\n5. Testing get_project_queries(project_id={project_id})...")
        queries = db_select.get_project_queries(project_id)
        print(f"Found {len(queries)} queries:")
        for query in queries:
            print(f"  - {query['queries_text'][:50]}...")
        
        # Test 6: Get project papers
        print(f"\n6. Testing get_project_papers(project_id={project_id})...")
        papers = db_select.get_project_papers(project_id)
        print(f"Found {len(papers)} papers:")
        for paper in papers:
            print(f"  - {paper['paper_title'][:50]}...")
        
        # Test 7: Get project YouTube videos
        print(f"\n7. Testing get_project_youtube_videos(project_id={project_id})...")
        youtube_videos = db_select.get_project_youtube_videos(project_id)
        print(f"Found {len(youtube_videos)} YouTube videos:")
        for video in youtube_videos:
            print(f"  - {video['video_title'][:50]}...")
        
        # Test 8: Get project likes
        print(f"\n8. Testing get_likes_for_project(project_id={project_id})...")
        likes = db_select.get_likes_for_project(project_id)
        print(f"Found {len(likes)} likes:")
        for like in likes:
            status = "👍 Liked" if like['isLiked'] else "👎 Disliked"
            print(f"  - {like['target_type']} ID {like['target_id']}: {status}")
        
        # Test 9: Get complete project data
        print(f"\n9. Testing get_complete_project_data(project_id={project_id})...")
        complete_data = db_select.get_complete_project_data(project_id)
        if complete_data:
            print(f"  Project: {complete_data['project']['topic']}")
            print(f"  Queries: {len(complete_data['queries'])}")
            print(f"  Papers: {len(complete_data['papers'])}")
            print(f"  YouTube videos: {len(complete_data['youtube_videos'])}")
            print(f"  Likes: {len(complete_data['likes'])}")
        
        # Test 10: Get paper with authors (if papers exist)
        if papers:
            paper_id = papers[0]['paper_id']
            print(f"\n10. Testing get_paper_with_authors(paper_id={paper_id})...")
            paper_with_authors = db_select.get_paper_with_authors(paper_id)
            if paper_with_authors:
                print(f"  Paper: {paper_with_authors['paper_title']}")
                print(f"  Authors: {len(paper_with_authors['authors'])}")
                for author in paper_with_authors['authors']:
                    print(f"    - {author['name']}")
    
    # Test 11: Get all authors
    print("\n11. Testing get_all_authors()...")
    authors = db_select.get_all_authors()
    print(f"Found {len(authors)} authors:")
    for author in authors:
        print(f"  - {author['name']} (ID: {author['author_id']})")
    
    print("\n✅ All tests completed! Check the output above for results.")
    print("=" * 50)
