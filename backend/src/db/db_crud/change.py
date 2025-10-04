import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBChange:
    def __init__(self):
        self.connector = Connector()
    
    def update_like(self, liked_disliked_id):
        self.connector.open_connection()
        try:
            query = "UPDATE likes SET isLiked = NOT isLiked WHERE liked_disliked_id = %s"
            values = (liked_disliked_id,)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()
        except Exception as e:
            print(e)
            self.connector.cnx.rollback()
        finally:
            self.connector.close_connection()
    
if __name__ == "__main__":
    db_change = DBChange()

    print("Updating like...")
    db_change.update_like(2)

    print("✅ Test run finished. Check your DB for updated rows.")