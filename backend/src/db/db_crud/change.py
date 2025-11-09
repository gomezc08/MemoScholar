import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBChange:
    def __init__(self):
        self.connector = Connector()
        self.manage_connection = True  # Set to False to skip opening/closing connections
    
    def update_like(self, liked_disliked_id):
        """
        Update an existing like/dislike record by toggling the isLiked status.
        Returns True if successful, False otherwise.
        """
        if self.manage_connection:
            self.connector.open_connection()
        try:
            query = "UPDATE likes SET isLiked = NOT isLiked WHERE liked_disliked_id = %s"
            values = (liked_disliked_id,)
            self.connector.cursor.execute(query, values)
            
            # Check if any rows were affected
            rows_affected = self.connector.cursor.rowcount
            if rows_affected == 0:
                print(f"No like/dislike record found with ID {liked_disliked_id}")
                return False
            
            if self.manage_connection:
                self.connector.cnx.commit()
            print(f"Successfully updated like/dislike record with ID {liked_disliked_id}")
            return True
            
        except Exception as e:
            print(f"Error updating like/dislike record: {e}")
            if self.manage_connection:
                self.connector.cnx.rollback()
            return False
        finally:
            if self.manage_connection:
                self.connector.close_connection()
    
    def mark_youtube_as_recommended(self, youtube_id):
        """
        Mark a YouTube video as recommended in youtube_has_rec table.
        If entry exists, updates it. Otherwise, inserts a new entry.
        Returns True if successful, False otherwise.
        """
        if self.manage_connection:
            self.connector.open_connection()
        try:
            # Check if entry already exists
            self.connector.cursor.execute(
                "SELECT youtube_has_rec_id FROM youtube_has_rec WHERE youtube_id = %s",
                (youtube_id,)
            )
            if self.connector.cursor.fetchone():
                # Update existing entry
                self.connector.cursor.execute(
                    "UPDATE youtube_has_rec SET hasBeenRecommended = TRUE WHERE youtube_id = %s",
                    (youtube_id,)
                )
            else:
                # Insert new entry
                self.connector.cursor.execute(
                    "INSERT INTO youtube_has_rec(youtube_id, hasBeenRecommended) VALUES (%s, TRUE)",
                    (youtube_id,)
                )
            
            if self.manage_connection:
                self.connector.cnx.commit()
            return True
        except Exception as e:
            print(f"mark_youtube_as_recommended error: {e}")
            if self.manage_connection:
                self.connector.cnx.rollback()
            return False
        finally:
            if self.manage_connection:
                self.connector.close_connection()
    
    def mark_youtube_videos_as_recommended(self, youtube_ids):
        """
        Mark multiple YouTube videos as recommended.
        youtube_ids: list of YouTube video IDs
        Returns True if all successful, False otherwise.
        """
        if self.manage_connection:
            self.connector.open_connection()
        try:
            for youtube_id in youtube_ids:
                # Check if entry already exists
                self.connector.cursor.execute(
                    "SELECT youtube_has_rec_id FROM youtube_has_rec WHERE youtube_id = %s",
                    (youtube_id,)
                )
                if self.connector.cursor.fetchone():
                    # Update existing entry
                    self.connector.cursor.execute(
                        "UPDATE youtube_has_rec SET hasBeenRecommended = TRUE WHERE youtube_id = %s",
                        (youtube_id,)
                    )
                else:
                    # Insert new entry
                    self.connector.cursor.execute(
                        "INSERT INTO youtube_has_rec(youtube_id, hasBeenRecommended) VALUES (%s, TRUE)",
                        (youtube_id,)
                    )
            
            if self.manage_connection:
                self.connector.cnx.commit()
            return True
        except Exception as e:
            print(f"mark_youtube_videos_as_recommended error: {e}")
            if self.manage_connection:
                self.connector.cnx.rollback()
            return False
        finally:
            if self.manage_connection:
                self.connector.close_connection()