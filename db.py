import sqlite3
from contextlib import contextmanager
from config import DB_NAME

class DatabaseManager:
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def conn(self):
        if self._connection is None:
            self._connection = sqlite3.connect(DB_NAME)
            self._connection.row_factory = sqlite3.Row
            
        return self._connection
    
    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def transaction(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
    
    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return [list(row) for row in rows]
    
    def fetch_one(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        if row:
            return list(row)
        return None

db = DatabaseManager()
