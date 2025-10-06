import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBChange:
    def __init__(self):
        self.connector = Connector()
    
    def update_like(self, liked_disliked_id):
        """
        Update an existing like/dislike record by toggling the isLiked status.
        Returns True if successful, False otherwise.
        """
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
            
            self.connector.cnx.commit()
            print(f"Successfully updated like/dislike record with ID {liked_disliked_id}")
            return True
            
        except Exception as e:
            print(f"Error updating like/dislike record: {e}")
            self.connector.cnx.rollback()
            return False
        finally:
            self.connector.close_connection()