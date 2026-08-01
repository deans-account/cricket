PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY,
    archive_name TEXT NOT NULL,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS integrity_log (
    id INTEGER PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    message TEXT NOT NULL
);
