import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBInsert:
    def __init__(self):
        self.connector = Connector()

    def create_user(self, name, email):
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
            self.connector.close_connection()

    def create_project(self, user_id, topic, objective, guidelines):
        """Note: user_id is REQUIRED by schema."""
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
            self.connector.close_connection()

    def create_like(self, project_id, target_type, target_id, isLiked):
        """
        target_type must be 'youtube' or 'paper' (per CHECK).
        Optionally, validate that the target exists before inserting to avoid orphans.
        """
        self.connector.open_connection()
        try:
            # Optional validation
            if target_type == "youtube":
                chk = "SELECT 1 FROM youtube WHERE youtube_id = %s AND project_id = %s"
            elif target_type == "paper":
                chk = "SELECT 1 FROM papers WHERE paper_id = %s AND project_id = %s"
            else:
                raise ValueError("target_type must be 'youtube' or 'paper'")

            self.connector.cursor.execute(chk, (target_id, project_id))
            if self.connector.cursor.fetchone() is None:
                raise ValueError(f"{target_type} id {target_id} not found for project {project_id}")

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
            self.connector.close_connection()