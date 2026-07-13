PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS approval_consumptions (
    approval_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL UNIQUE,
    action_type TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    consumed_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS approval_consumptions_no_update
BEFORE UPDATE ON approval_consumptions BEGIN
    SELECT RAISE(ABORT, 'append-only: approval consumptions cannot be updated');
END;

CREATE TRIGGER IF NOT EXISTS approval_consumptions_no_delete
BEFORE DELETE ON approval_consumptions BEGIN
    SELECT RAISE(ABORT, 'append-only: approval consumptions cannot be deleted');
END;
