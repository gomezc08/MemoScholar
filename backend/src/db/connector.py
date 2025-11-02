import mysql.connector
from dotenv import load_dotenv
import os

class Connector:
    def __init__(self):
        self.cnx = None
        self.cursor = None
    
    def open_connection(self):
        # Don't reconnect if already connected
        if self.cnx is not None and self.cnx.is_connected():
            return None
            
        load_dotenv()
        try:
            config = {
                "user": os.getenv('USER'),
                "password" : os.getenv('PASSWORD'),
                "host": os.getenv('HOST'),
                "port": os.getenv('PORT'),
                "database": "memoscholar",
                "raise_on_warnings": True
            }
            self.cnx = mysql.connector.connect(**config)
            self.cursor = self.cnx.cursor()
            print("CONNECTED TO MYSQL")
            return None

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.cnx = None
            self.cursor = None
    
    def close_connection(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.cnx:
            self.cnx.close()
            print("CLOSED CONNECTION TO MYSQL")
            self.cnx = None  # Clear the reference