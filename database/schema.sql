PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS imports(
 id INTEGER PRIMARY KEY,
 archive_name TEXT NOT NULL,
 imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
 status TEXT NOT NULL,
 notes TEXT
);
CREATE TABLE IF NOT EXISTS markets(
 market_id TEXT PRIMARY KEY,
 event_name TEXT,
 market_time TEXT,
 market_type TEXT
);
CREATE TABLE IF NOT EXISTS matches(
 id INTEGER PRIMARY KEY,
 market_id TEXT UNIQUE,
 home_team TEXT,
 away_team TEXT,
 start_time TEXT,
 result TEXT,
 FOREIGN KEY(market_id) REFERENCES markets(market_id)
);
CREATE TABLE IF NOT EXISTS price_history(
 id INTEGER PRIMARY KEY,
 market_id TEXT,
 ts TEXT,
 runner_id INTEGER,
 price REAL,
 traded_volume REAL,
 FOREIGN KEY(market_id) REFERENCES markets(market_id)
);
CREATE TABLE IF NOT EXISTS integrity_log(
 id INTEGER PRIMARY KEY,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 level TEXT,
 message TEXT
);
