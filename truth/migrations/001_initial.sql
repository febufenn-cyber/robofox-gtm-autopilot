PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    external_reference TEXT,
    captured_at TEXT NOT NULL,
    observed_at TEXT,
    sensitivity TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    record_hash TEXT NOT NULL UNIQUE,
    inserted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    value_json TEXT NOT NULL,
    unit TEXT,
    evidence_state TEXT NOT NULL,
    confidence TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    observed_at TEXT,
    valid_from TEXT,
    valid_until TEXT,
    max_age_days INTEGER,
    supersedes_id TEXT REFERENCES claims(id),
    sensitivity TEXT NOT NULL,
    notes TEXT,
    record_hash TEXT NOT NULL UNIQUE,
    inserted_at TEXT NOT NULL,
    CHECK (supersedes_id IS NULL OR supersedes_id <> id)
);

CREATE TABLE IF NOT EXISTS claim_sources (
    claim_id TEXT NOT NULL REFERENCES claims(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE IF NOT EXISTS assumptions (
    id TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    statement TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence TEXT NOT NULL,
    created_at TEXT NOT NULL,
    review_by TEXT,
    supersedes_id TEXT REFERENCES assumptions(id),
    sensitivity TEXT NOT NULL,
    record_hash TEXT NOT NULL UNIQUE,
    inserted_at TEXT NOT NULL,
    CHECK (supersedes_id IS NULL OR supersedes_id <> id)
);

CREATE TABLE IF NOT EXISTS assumption_resolution_claims (
    assumption_id TEXT NOT NULL REFERENCES assumptions(id),
    claim_id TEXT NOT NULL REFERENCES claims(id),
    PRIMARY KEY (assumption_id, claim_id)
);

CREATE TABLE IF NOT EXISTS metrics (
    id TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    denominator REAL,
    sample_size INTEGER,
    segment TEXT,
    experiment_id TEXT,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    record_hash TEXT NOT NULL UNIQUE,
    inserted_at TEXT NOT NULL,
    CHECK (period_end >= period_start)
);

CREATE TABLE IF NOT EXISTS metric_sources (
    metric_id TEXT NOT NULL REFERENCES metrics(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    PRIMARY KEY (metric_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_claim_position ON claims(product, subject, predicate);
CREATE INDEX IF NOT EXISTS idx_claim_supersedes ON claims(supersedes_id);
CREATE INDEX IF NOT EXISTS idx_assumption_product_status ON assumptions(product, status);
CREATE INDEX IF NOT EXISTS idx_metric_product_name_period ON metrics(product, metric, period_end);

CREATE TRIGGER IF NOT EXISTS sources_no_update BEFORE UPDATE ON sources BEGIN
    SELECT RAISE(ABORT, 'append-only: sources cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS sources_no_delete BEFORE DELETE ON sources BEGIN
    SELECT RAISE(ABORT, 'append-only: sources cannot be deleted');
END;
CREATE TRIGGER IF NOT EXISTS claims_no_update BEFORE UPDATE ON claims BEGIN
    SELECT RAISE(ABORT, 'append-only: claims cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS claims_no_delete BEFORE DELETE ON claims BEGIN
    SELECT RAISE(ABORT, 'append-only: claims cannot be deleted');
END;
CREATE TRIGGER IF NOT EXISTS claim_sources_no_update BEFORE UPDATE ON claim_sources BEGIN
    SELECT RAISE(ABORT, 'append-only: claim source links cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS claim_sources_no_delete BEFORE DELETE ON claim_sources BEGIN
    SELECT RAISE(ABORT, 'append-only: claim source links cannot be deleted');
END;
CREATE TRIGGER IF NOT EXISTS assumptions_no_update BEFORE UPDATE ON assumptions BEGIN
    SELECT RAISE(ABORT, 'append-only: assumptions cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS assumptions_no_delete BEFORE DELETE ON assumptions BEGIN
    SELECT RAISE(ABORT, 'append-only: assumptions cannot be deleted');
END;
CREATE TRIGGER IF NOT EXISTS assumption_links_no_update BEFORE UPDATE ON assumption_resolution_claims BEGIN
    SELECT RAISE(ABORT, 'append-only: assumption links cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS assumption_links_no_delete BEFORE DELETE ON assumption_resolution_claims BEGIN
    SELECT RAISE(ABORT, 'append-only: assumption links cannot be deleted');
END;
CREATE TRIGGER IF NOT EXISTS metrics_no_update BEFORE UPDATE ON metrics BEGIN
    SELECT RAISE(ABORT, 'append-only: metrics cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS metrics_no_delete BEFORE DELETE ON metrics BEGIN
    SELECT RAISE(ABORT, 'append-only: metrics cannot be deleted');
END;
CREATE TRIGGER IF NOT EXISTS metric_sources_no_update BEFORE UPDATE ON metric_sources BEGIN
    SELECT RAISE(ABORT, 'append-only: metric source links cannot be updated');
END;
CREATE TRIGGER IF NOT EXISTS metric_sources_no_delete BEFORE DELETE ON metric_sources BEGIN
    SELECT RAISE(ABORT, 'append-only: metric source links cannot be deleted');
END;
