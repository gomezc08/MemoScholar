import os
import sys
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBInsert:
    def __init__(self):
        self.connector = Connector()
        self.manage_connection = True  # Set to False to skip opening/closing connections

    def create_user(self, name, email):
        if self.manage_connection:
            self.connector.open_connection()
        try:
            query = "INSERT INTO users (name, email) VALUES (%s, %s)"
            values = (name, email)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the user_id of the created user
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_user error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_project(self, user_id, topic, objective, guidelines):
        """Create project (embedding stored separately). user_id is REQUIRED by schema."""
        self.connector.open_connection()
        try:
            query = "INSERT INTO project (user_id, topic, objective, guidelines) VALUES (%s, %s, %s, %s)"
            values = (user_id, topic, objective, guidelines)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the project_id of the created project
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_project error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_project_embedding(self, project_id, embedding):
        """Insert embedding into project_embeddings for a project."""
        if self.manage_connection:
            self.connector.open_connection()
        try:
            # Convert embedding to JSON string if it's a list or array
            if embedding is None:
                return None
            if isinstance(embedding, list):
                embedding_str = json.dumps(embedding)
            elif hasattr(embedding, '__iter__'):
                embedding_str = json.dumps(list(embedding))
            else:
                embedding_str = str(embedding)

            query = "INSERT INTO project_embeddings (project_id, embedding) VALUES (%s, STRING_TO_VECTOR(%s))"
            values = (project_id, embedding_str)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_project_embedding error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_query(self, project_id, queries_text, special_instructions=None):
        self.connector.open_connection()
        try:
            query = "INSERT INTO queries (project_id, queries_text, special_instructions) VALUES (%s, %s, %s)"
            values = (project_id, queries_text, special_instructions if special_instructions else None)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the query_id of the created query
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_query error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_paper(self, project_id, query_id, paper_title, paper_summary, published_year, pdf_link):
        self.connector.open_connection()
        try:
            query = """
                INSERT INTO papers (project_id, paper_title, paper_summary, published_year, pdf_link, query_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (project_id, paper_title, paper_summary, published_year, pdf_link, query_id)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the paper_id of the created paper
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_paper error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_author(self, name):
        self.connector.open_connection()
        try:
            query = "INSERT INTO authors (name) VALUES (%s)"
            values = (name,)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the author_id of the created author
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_author error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def get_or_create_author(self, name):
        """
        Get existing author by name, or create new one if doesn't exist.
        Returns author_id or None if failed.
        """
        if not name or name.strip() == '':
            return None
            
        self.connector.open_connection()
        try:
            # First, try to find existing author
            query = "SELECT author_id FROM authors WHERE name = %s"
            self.connector.cursor.execute(query, (name.strip(),))
            result = self.connector.cursor.fetchone()
            
            if result:
                return result[0]  # Return existing author_id
            else:
                # Author doesn't exist, create new one
                return self.create_author(name.strip())
        except Exception as e:
            print("get_or_create_author error:", e)
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def add_paper_author(self, paper_id, author_id):
        self.connector.open_connection()
        try:
            query = "INSERT INTO paperauthors (paper_id, author_id) VALUES (%s, %s)"
            values = (paper_id, author_id)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the paper_author_id of the created paper_author
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("add_paper_author error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_paper_with_authors(self, project_id, query_id, paper_title, paper_summary, published_year, pdf_link, authors_list):
        """
        Create a paper and link it with its authors.
        Returns paper_id if successful, None if failed.
        """
        # First create the paper
        paper_id = self.create_paper(project_id, query_id, paper_title, paper_summary, published_year, pdf_link)
        
        if paper_id is None:
            return None
        
        # Then handle authors
        if authors_list and isinstance(authors_list, list):
            for author_name in authors_list:
                if author_name and author_name.strip():
                    author_id = self.get_or_create_author(author_name.strip())
                    if author_id:
                        self.add_paper_author(paper_id, author_id)
        
        return paper_id

    def create_youtube(self, project_id, query_id, video_title, video_description, video_duration, video_url,
                       video_views=0, video_likes=0):
        self.connector.open_connection()
        try:
            query = """
                INSERT INTO youtube (
                    project_id, query_id, video_title, video_description,
                    video_duration, video_url, video_views, video_likes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (project_id, query_id, video_title, video_description,
                      video_duration, video_url, video_views, video_likes)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the youtube_id of the created youtube
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_youtube error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_youtube_project_embedding(self, project_id, embedding):
        """Insert per-project YouTube embedding into youtube_embeddings."""
        if self.manage_connection:
            self.connector.open_connection()
        try:
            if embedding is None:
                return None
            if isinstance(embedding, list):
                embedding_str = json.dumps(embedding)
            elif hasattr(embedding, '__iter__'):
                embedding_str = json.dumps(list(embedding))
            else:
                embedding_str = str(embedding)

            query = "INSERT INTO youtube_embeddings (project_id, embedding) VALUES (%s, STRING_TO_VECTOR(%s))"
            values = (project_id, embedding_str)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_youtube_project_embedding error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def upsert_youtube_video_embedding(self, youtube_id, embedding):
        """Insert or update cached embedding for a YouTube video."""
        if self.manage_connection:
            self.connector.open_connection()
        try:
            if embedding is None:
                return None
            if isinstance(embedding, list):
                embedding_str = json.dumps(embedding)
            elif hasattr(embedding, '__iter__'):
                embedding_str = json.dumps(list(embedding))
            else:
                embedding_str = str(embedding)

            query = """
                INSERT INTO youtube_video_embeddings (youtube_id, embedding)
                VALUES (%s, STRING_TO_VECTOR(%s))
                ON DUPLICATE KEY UPDATE embedding = STRING_TO_VECTOR(%s)
            """
            values = (youtube_id, embedding_str, embedding_str)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("upsert_youtube_video_embedding error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def upsert_paper_embedding(self, paper_id, embedding):
        """Insert or update cached embedding for a paper."""
        if self.manage_connection:
            self.connector.open_connection()
        try:
            if embedding is None:
                return None
            if isinstance(embedding, list):
                embedding_str = json.dumps(embedding)
            elif hasattr(embedding, '__iter__'):
                embedding_str = json.dumps(list(embedding))
            else:
                embedding_str = str(embedding)

            query = """
                INSERT INTO paper_embeddings (paper_id, embedding)
                VALUES (%s, STRING_TO_VECTOR(%s))
                ON DUPLICATE KEY UPDATE embedding = STRING_TO_VECTOR(%s)
            """
            values = (paper_id, embedding_str, embedding_str)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("upsert_paper_embedding error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def insert_paper_features(self, paper_id, features_list):
        """Insert features for a paper."""
        if self.manage_connection:
            self.connector.open_connection()
        try:
            if not features_list:
                return None

            # Delete existing features
            self.connector.cursor.execute(
                "DELETE FROM paper_features WHERE paper_id = %s",
                (paper_id,)
            )

            # Insert new features
            values = [(paper_id, category, feature) for category, feature in features_list]
            self.connector.cursor.executemany(
                "INSERT INTO paper_features (paper_id, category, feature) VALUES (%s, %s, %s)",
                values
            )
            self.connector.cnx.commit()
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("insert_paper_features error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def create_like(self, project_id, target_type, target_id, isLiked):
        """
        target_type must be 'youtube' or 'paper' (per CHECK).
        """
        self.connector.open_connection()
        try:
            if target_type == "youtube":
                # Check if it exists in the youtube table
                chk = "SELECT 1 FROM youtube WHERE youtube_id = %s AND project_id = %s"
                self.connector.cursor.execute(chk, (target_id, project_id))
                
                if self.connector.cursor.fetchone() is None:
                    raise ValueError(f"youtube id {target_id} not found for project {project_id}")
                        
            elif target_type == "paper":
                chk = "SELECT 1 FROM papers WHERE paper_id = %s AND project_id = %s"
                self.connector.cursor.execute(chk, (target_id, project_id))
                if self.connector.cursor.fetchone() is None:
                    raise ValueError(f"{target_type} id {target_id} not found for project {project_id}")
            else:
                raise ValueError("target_type must be 'youtube' or 'paper'")

            # Create the like/dislike record
            query = "INSERT INTO likes (project_id, target_type, target_id, isLiked) VALUES (%s, %s, %s, %s)"
            values = (project_id, target_type, target_id, isLiked)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
            # Return the like_id of the created like
            return self.connector.cursor.lastrowid
        except Exception as e:
            print("create_like error:", e)
            self.connector.cnx.rollback()
            return None
        finally:
            if self.manage_connection:
                self.connector.close_connection()

    def insert_youtube_features(self, youtube_id, features_list):
        """
        Insert features into youtube_features table.
        features_list should be a list of tuples (category, feature_value).
        """
        if self.manage_connection:
            self.connector.open_connection()
        try:
            # Delete existing features first
            self.connector.cursor.execute("DELETE FROM youtube_features WHERE youtube_id = %s", (youtube_id,))
            
            # Insert new features
            if features_list:
                self.connector.cursor.executemany(
                    "INSERT INTO youtube_features(youtube_id, category, feature) VALUES (%s, %s, %s)",
                    [(youtube_id, cat, feat) for cat, feat in features_list]
                )
            if self.manage_connection:
                self.connector.cnx.commit()
            return True
        except Exception as e:
            print("insert_youtube_features error:", e)
            if self.manage_connection:
                self.connector.cnx.rollback()
            return False
        finally:
            if self.manage_connection:
                self.connector.close_connection()
    