import mysql.connector
from dotenv import load_dotenv
import os

class Connector:
    def __init__(self):
        self.cnx = None
    
    def open_connection(self):
        load_dotenv()
        print("CONNECTING TO MYSQL")
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
            print("CONNECTED TO MYSQL")
            return None

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.cnx = None
    
    def close_connection(self):
        if self.cnx:
            self.cnx.close()
            print("CLOSED CONNECTION TO MYSQL")
        else:
            print("NO CONNECTION TO MYSQL")
    

if __name__ == '__main__':
    conn = Connector()
    conn.open_connection()
    conn.close_connection()
            