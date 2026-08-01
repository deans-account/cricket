import sqlite3
SCHEMA='''
CREATE TABLE IF NOT EXISTS imports(
 id INTEGER PRIMARY KEY,
 archive_name TEXT,
 imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
 status TEXT
);
CREATE TABLE IF NOT EXISTS matches(
 id INTEGER PRIMARY KEY,
 market_id TEXT UNIQUE,
 event_name TEXT,
 market_time TEXT
);
CREATE TABLE IF NOT EXISTS price_history(
 id INTEGER PRIMARY KEY,
 market_id TEXT,
 ts TEXT,
 runner_id INTEGER,
 price REAL
);
'''
def create_database(path):
    con=sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.commit()
    con.close()
