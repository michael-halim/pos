# import sqlite3
# from pathlib import Path


# class DatabaseConnect:
#     def __init__(self):
#         # Database setup
#         self.db_folder = "./db"
#         self.db_path = f"{self.db_folder}/products_db.db"
#         self.table_name = "product_master"
#         self.connection = None
#         self.cursor = None

#         # Initialize the database
#         self.init_database()

#     def init_database(self):
#         # Create necessary folder and database file if they don't exist
#         folder_path = Path(self.db_folder)
#         db_path = Path(self.db_path)

#         if not folder_path.exists():
#             folder_path.mkdir(parents=True)

#         if not db_path.exists():
#             with open(self.db_path, "w"):
#                 pass

#         # Connect to the database and create the table if it doesnt exist
#         self.connector()
#         try:
#             # Check if the table exists
#             sql = f"SELECT name FROM sqlite_master WHERE type='table' and name='{self.table_name}'"
#             self.cursor.execute(sql)
#             result = self.cursor.fetchone()

#             if result:
#                 return
#             else:
#                 # Create the table if it doesnt exist
#                 sql = f"""
#                     CREATE TABLE '{self.table_name}' (
#                     "product_name"	TEXT NOT NULL,
#                     "cost"	NUMERIC,
#                     "price"	NUMERIC,
#                     "location"	INTEGER,
#                     "reorder_level"	INTEGER,
#                     "stock"	INTEGER DEFAULT 0,
#                     PRIMARY KEY("product_name")
#                     );                   
#                     """
#                 self.cursor.execute(sql)
#                 # Commit changes to the database
#                 self.connection.commit()

#         except Exception as e:
#             self.connection.rollback()
#             return e

#         finally:
#             # Close the cursor and connection
#             self.cursor.close()
#             self.connection.close()

#     def connector(self):
#         # Establish a connection to the SQLite database
#         self.connection = sqlite3.connect(self.db_path)
#         self.cursor = self.connection.cursor()


import sqlite3
from PyQt6.QtCore import QMutex, QMutexLocker

class DatabaseConnection:
    _instance = None
    _mutex = QMutex()

    def __new__(cls, db_path="./db/pos.db"):
        with QMutexLocker(cls._mutex):
            if cls._instance is None:
                cls._instance = super(DatabaseConnection, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.connection = sqlite3.connect(db_path, check_same_thread=False)
                cls._instance.connection.row_factory = sqlite3.Row  # For dict-like row access
            return cls._instance

    def get_connection(self):
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            DatabaseConnection._instance = None
