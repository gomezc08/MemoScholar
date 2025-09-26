import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.db.connector import Connector

class DBInsert:
    def __init__(self):
        self.connector = Connector()

    def insert_project(self, topic, objective, guidelines):
        self.connector.open_connection()
        try:
            query = "INSERT INTO Project (topic, objective, guidelines) VALUES (%s, %s, %s)"
            values = (topic, objective, guidelines)
            self.connector.cursor.execute(query, values)
            self.connector.cnx.commit()

        except Exception as e:
            print(e)
            self.connector.cnx.rollback()

        finally:
            self.connector.close_connection()

if __name__ == '__main__':
    db_insert = DBInsert()
    db_insert.insert_project("Machine Learning in Healthcare", "Understand how machine learning algorithms are being applied to medical diagnosis, patient care, and drug discovery in the healthcare industry", "Focus on recent developments (2020-2024). Include both technical implementation details and real-world case studies")



