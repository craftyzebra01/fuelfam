import sqlite3

class SqliteStationRepository:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)

