import sqlite3
import os
import sys


class DatabaseConnection:
    _instance = None
    _connection = None
    _key = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance


    def get_connection(self):
        if self._connection is None:
            # Get the application directory
            if getattr(sys, 'frozen', False):
                # If the application is run as a bundle (compiled)
                application_path = os.path.dirname(sys.executable)
            else:
                # If the application is run as a script
                application_path = os.path.dirname(os.path.abspath(__file__))

            # Create a 'data' directory in the same folder as the executable
            data_dir = os.path.join(application_path, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Database file path
            db_path = os.path.join(data_dir, 'pos.db')
            
            # Connect to the database with check_same_thread=False to allow cross-thread access
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row

            print(f"Using database at: {db_path}")
            
        return self._connection


    def close_connection(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
