PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS metadata(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS imports(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  archive_name TEXT NOT NULL,
  archive_sha256 TEXT NOT NULL UNIQUE,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  status TEXT NOT NULL,
  files_scanned INTEGER NOT NULL DEFAULT 0,
  markets_imported INTEGER NOT NULL DEFAULT 0,
  duplicates_skipped INTEGER NOT NULL DEFAULT 0,
  errors INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS markets(
  market_id TEXT PRIMARY KEY,
  match_key TEXT NOT NULL UNIQUE,
  event_name TEXT NOT NULL,
  market_name TEXT,
  market_type TEXT NOT NULL,
  market_time TEXT NOT NULL,
  competition TEXT,
  country_code TEXT,
  source_import_id INTEGER NOT NULL,
  source_member TEXT NOT NULL,
  first_publish_time INTEGER,
  last_publish_time INTEGER,
  final_status TEXT,
  final_in_play INTEGER,
  winner_selection_id INTEGER,
  settled INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(source_import_id) REFERENCES imports(id)
);

CREATE TABLE IF NOT EXISTS runners(
  market_id TEXT NOT NULL,
  selection_id INTEGER NOT NULL,
  runner_name TEXT NOT NULL,
  runner_role TEXT NOT NULL,
  sort_priority INTEGER,
  final_status TEXT,
  PRIMARY KEY(market_id,selection_id),
  FOREIGN KEY(market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_history(
  market_id TEXT NOT NULL,
  publish_time INTEGER NOT NULL,
  selection_id INTEGER NOT NULL,
  last_traded_price REAL,
  best_back_price REAL,
  best_back_size REAL,
  best_lay_price REAL,
  best_lay_size REAL,
  runner_total_matched REAL,
  market_total_matched REAL,
  in_play INTEGER,
  market_status TEXT,
  PRIMARY KEY(market_id,publish_time,selection_id),
  FOREIGN KEY(market_id,selection_id) REFERENCES runners(market_id,selection_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS integrity_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  import_id INTEGER,
  market_id TEXT,
  severity TEXT NOT NULL,
  code TEXT NOT NULL,
  message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_markets_time ON markets(market_time);
CREATE INDEX IF NOT EXISTS idx_prices_market_time ON price_history(market_id,publish_time);
CREATE INDEX IF NOT EXISTS idx_integrity_market ON integrity_log(market_id);


CREATE TABLE IF NOT EXISTS market_summary(
  market_id TEXT PRIMARY KEY,
  market_time TEXT NOT NULL,
  event_name TEXT NOT NULL,
  home_selection_id INTEGER,
  home_name TEXT,
  away_selection_id INTEGER,
  away_name TEXT,
  draw_selection_id INTEGER,
  draw_name TEXT,
  winner_role TEXT,
  first_inplay_time INTEGER,
  home_preplay_ltp REAL,
  away_preplay_ltp REAL,
  draw_preplay_ltp REAL,
  home_min_ltp REAL,
  home_max_ltp REAL,
  away_min_ltp REAL,
  away_max_ltp REAL,
  draw_min_ltp REAL,
  draw_max_ltp REAL,
  price_rows INTEGER NOT NULL DEFAULT 0,
  derived_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_summary_time ON market_summary(market_time);
