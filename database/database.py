from pathlib import Path
import sqlite3

class Database:
    def __init__(self,path):
        self.path=Path(path)
    def initialise(self):
        con=sqlite3.connect(self.path)
        schema=(Path(__file__).with_name("schema.sql")).read_text()
        con.executescript(schema)
        con.commit()
        con.close()
