-- Cloudflare D1 schema. Run with wrangler d1 execute <DB_NAME> --file backend/schema.sql
CREATE TABLE IF NOT EXISTS reports (
 id TEXT PRIMARY KEY,
 owner_hash TEXT NOT NULL,
 machine TEXT NOT NULL,
 condition_key TEXT NOT NULL,
 condition_json TEXT NOT NULL,
 vote TEXT NOT NULL CHECK(vote IN ('play','skip')),
 analysis_json TEXT NOT NULL,
 result TEXT NOT NULL DEFAULT '',
 net INTEGER,
 status TEXT NOT NULL DEFAULT 'accepted' CHECK(status IN ('accepted','quarantined','rejected','withdrawn')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_reports_machine_status ON reports(machine,status);
CREATE INDEX IF NOT EXISTS idx_reports_owner_time ON reports(owner_hash,created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_owner_condition ON reports(owner_hash,condition_key) WHERE status='accepted';
CREATE TABLE IF NOT EXISTS revisions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 report_id TEXT NOT NULL REFERENCES reports(id),
 previous_json TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS moderation_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 report_id TEXT NOT NULL REFERENCES reports(id),
 reason TEXT NOT NULL,
 previous_status TEXT NOT NULL,
 new_status TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aggregate_snapshots (
 machine TEXT NOT NULL,
 condition_key TEXT NOT NULL,
 vote TEXT NOT NULL,
 result TEXT NOT NULL DEFAULT '',
 n INTEGER NOT NULL CHECK(n>=0),
 generated_at TEXT NOT NULL,
 PRIMARY KEY(machine,condition_key,vote,result)
);
CREATE INDEX IF NOT EXISTS idx_reports_burst ON reports(condition_key,vote,created_at);
