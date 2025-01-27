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
