import sqlite3
import os
import sys
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DatabaseConnection:
    _instance = None
    _connection = None
    _key = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance


    def _generate_key(self, password: str, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt


    def _get_or_create_key(self):
        if self._key is None:
            # Get the application directory
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))

            # Create a 'data' directory in the same folder as the executable
            data_dir = os.path.join(application_path, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Key file path
            key_path = os.path.join(data_dir, 'db.key')
            salt_path = os.path.join(data_dir, 'db.salt')

            if os.path.exists(key_path) and os.path.exists(salt_path):
                # Load existing key and salt
                with open(key_path, 'rb') as f:
                    self._key = f.read()
                with open(salt_path, 'rb') as f:
                    salt = f.read()
            else:
                # Generate new key and salt
                password = input("Enter database encryption password: ")
                self._key, salt = self._generate_key(password)
                
                # Save key and salt
                with open(key_path, 'wb') as f:
                    f.write(self._key)
                with open(salt_path, 'wb') as f:
                    f.write(salt)

        return self._key


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
            
            # Get encryption key
            key = self._get_or_create_key()
            
            # Connect to the database with encryption
            self._connection = sqlite3.connect(db_path)
            self._connection.row_factory = sqlite3.Row
            
            # Set encryption key
            self._connection.execute(f"PRAGMA key='{key.decode()}'")
            
            # Verify encryption
            try:
                self._connection.execute("SELECT count(*) FROM sqlite_master")
            except sqlite3.DatabaseError:
                print("Invalid encryption key or database is not encrypted")
                raise

            print(f"Using database at: {db_path}")
            
        return self._connection


    def close_connection(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
