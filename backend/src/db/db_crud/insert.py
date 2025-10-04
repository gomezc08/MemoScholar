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

    def create_query(self, project_id, queries_text, special_instructions):
        self.connector.open_connection()
        try:
            query = "INSERT INTO queries (project_id, queries_text, special_instructions) VALUES (%s, %s, %s)"
            values = (project_id, queries_text, special_instructions)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
        except Exception as e:
            print("create_query error:", e)
            self.connector.cnx.rollback()
        finally:
            self.connector.close_connection()

    def create_paper(self, project_id, paper_title, paper_summary, published_year, pdf_link, query_id=None):
        self.connector.open_connection()
        try:
            query = """
                INSERT INTO papers (project_id, paper_title, paper_summary, published_year, pdf_link, query_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (project_id, paper_title, paper_summary, published_year, pdf_link, query_id)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
        except Exception as e:
            print("create_paper error:", e)
            self.connector.cnx.rollback()
        finally:
            self.connector.close_connection()

    def create_author(self, name):
        self.connector.open_connection()
        try:
            query = "INSERT INTO authors (name) VALUES (%s)"
            values = (name,)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
        except Exception as e:
            print("create_author error:", e)
            self.connector.cnx.rollback()
        finally:
            self.connector.close_connection()

    def add_paper_author(self, paper_id, author_id):
        self.connector.open_connection()
        try:
            query = "INSERT INTO paperauthors (paper_id, author_id) VALUES (%s, %s)"
            values = (paper_id, author_id)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
        except Exception as e:
            print("add_paper_author error:", e)
            self.connector.cnx.rollback()
        finally:
            self.connector.close_connection()

    def create_youtube(self, project_id, video_title, video_description, video_duration, video_url,
                       video_views=0, video_likes=0, query_id=None):
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
        except Exception as e:
            print("create_youtube error:", e)
            self.connector.cnx.rollback()
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
        except Exception as e:
            print("create_like error:", e)
            self.connector.cnx.rollback()
        finally:
            self.connector.close_connection()


if __name__ == '__main__':
    db_insert = DBInsert()

    print("Inserting user...")
    db_insert.create_user("Chris Gomez", "chris@example.com")

    print("Inserting project...")
    db_insert.create_project(
        user_id=1,   # assumes the new user got user_id=1
        topic="Machine Learning in Healthcare",
        objective="Understand how ML is applied to diagnosis, patient care, and drug discovery",
        guidelines="Focus on 2020-2024; include technical details and case studies"
    )

    print("Inserting query...")
    db_insert.create_query(
        project_id=1,
        queries_text="deep learning in clinical decision support 2022 review",
        special_instructions="Prefer peer-reviewed, exclude preprints"
    )

    print("Inserting paper...")
    db_insert.create_paper(
        project_id=1,
        paper_title="Deep Learning for Clinical Decision Support",
        paper_summary="Survey of DL-based CDS systems across specialties",
        published_year=2022,
        pdf_link="https://example.com/review.pdf",
        query_id=1
    )

    print("Inserting author...")
    db_insert.create_author("Jane Doe")

    print("Linking paper and author...")
    db_insert.add_paper_author(paper_id=1, author_id=1)

    print("Inserting youtube...")
    db_insert.create_youtube(
        project_id=1,
        video_title="Clinical AI in 2024",
        video_description="Panel on AI in healthcare",
        video_duration="00:30:00",   # TIME field, HH:MM:SS
        video_url="https://youtube.com/watch?v=abc123",
        video_views=12345,
        video_likes=678,
        query_id=1
    )

    print("Inserting likes...")
    db_insert.create_like(project_id=1, target_type="paper", target_id=1, isLiked=True)
    db_insert.create_like(project_id=1, target_type="youtube", target_id=1, isLiked=False)

    print("✅ Test run finished. Check your DB for inserted rows.")