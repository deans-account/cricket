PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archive_name TEXT NOT NULL,
    archive_path TEXT,
    archive_sha256 TEXT NOT NULL UNIQUE,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    status TEXT NOT NULL,
    files_scanned INTEGER NOT NULL DEFAULT 0,
    markets_parsed INTEGER NOT NULL DEFAULT 0,
    test_markets_found INTEGER NOT NULL DEFAULT 0,
    markets_imported INTEGER NOT NULL DEFAULT 0,
    duplicates_skipped INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS markets (
    market_id TEXT PRIMARY KEY,
    event_name TEXT,
    market_name TEXT,
    market_type TEXT NOT NULL,
    market_time TEXT,
    event_type_id TEXT,
    competition TEXT,
    country_code TEXT,
    timezone TEXT,
    number_of_winners INTEGER,
    status TEXT,
    in_play INTEGER,
    classification TEXT NOT NULL,
    classification_reason TEXT,
    source_import_id INTEGER NOT NULL,
    settled INTEGER NOT NULL DEFAULT 0,
    winner_selection_id INTEGER,
    first_publish_time INTEGER,
    last_publish_time INTEGER,
    FOREIGN KEY(source_import_id) REFERENCES imports(id)
);

CREATE TABLE IF NOT EXISTS runners (
    market_id TEXT NOT NULL,
    selection_id INTEGER NOT NULL,
    runner_name TEXT,
    sort_priority INTEGER,
    status TEXT,
    adjustment_factor REAL,
    PRIMARY KEY (market_id, selection_id),
    FOREIGN KEY(market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_history (
    market_id TEXT NOT NULL,
    publish_time INTEGER NOT NULL,
    selection_id INTEGER NOT NULL,
    last_traded_price REAL,
    total_matched REAL,
    best_back_price REAL,
    best_back_size REAL,
    best_lay_price REAL,
    best_lay_size REAL,
    in_play INTEGER,
    market_status TEXT,
    PRIMARY KEY (market_id, publish_time, selection_id),
    FOREIGN KEY(market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settlements (
    market_id TEXT NOT NULL,
    selection_id INTEGER NOT NULL,
    runner_status TEXT,
    settled_at INTEGER,
    PRIMARY KEY (market_id, selection_id),
    FOREIGN KEY(market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS integrity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    import_id INTEGER,
    market_id TEXT,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY(import_id) REFERENCES imports(id),
    FOREIGN KEY(market_id) REFERENCES markets(market_id)
);

CREATE INDEX IF NOT EXISTS idx_markets_time ON markets(market_time);
CREATE INDEX IF NOT EXISTS idx_markets_classification ON markets(classification);
CREATE INDEX IF NOT EXISTS idx_prices_market_time ON price_history(market_id, publish_time);
CREATE INDEX IF NOT EXISTS idx_prices_selection ON price_history(selection_id);
CREATE INDEX IF NOT EXISTS idx_integrity_market ON integrity_log(market_id);
