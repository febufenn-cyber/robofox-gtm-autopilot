PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    audience_key TEXT NOT NULL,
    planned_start TEXT NOT NULL,
    planned_end TEXT NOT NULL,
    change_dimensions_json TEXT NOT NULL,
    primary_metric TEXT NOT NULL,
    record_json TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL,
    UNIQUE(decision_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS experiment_transitions (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    record_json TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiment_transitions_state ON experiment_transitions(experiment_id, occurred_at, id);

CREATE TABLE IF NOT EXISTS experiment_executions (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    units INTEGER NOT NULL,
    cash_spent_usd REAL NOT NULL,
    founder_hours REAL NOT NULL,
    occurred_at TEXT NOT NULL,
    record_json TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiment_executions_time ON experiment_executions(experiment_id, occurred_at, id);

CREATE TABLE IF NOT EXISTS experiment_observations (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    sample_size INTEGER NOT NULL,
    observed_at TEXT NOT NULL,
    record_json TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiment_observations_metric ON experiment_observations(experiment_id, metric, observed_at, id);

CREATE TABLE IF NOT EXISTS experiment_outcomes (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL UNIQUE REFERENCES experiments(id),
    outcome TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    record_json TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS experiments_no_update BEFORE UPDATE ON experiments BEGIN SELECT RAISE(ABORT, 'append-only: experiments cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS experiments_no_delete BEFORE DELETE ON experiments BEGIN SELECT RAISE(ABORT, 'append-only: experiments cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS experiment_transitions_no_update BEFORE UPDATE ON experiment_transitions BEGIN SELECT RAISE(ABORT, 'append-only: experiment transitions cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS experiment_transitions_no_delete BEFORE DELETE ON experiment_transitions BEGIN SELECT RAISE(ABORT, 'append-only: experiment transitions cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS experiment_executions_no_update BEFORE UPDATE ON experiment_executions BEGIN SELECT RAISE(ABORT, 'append-only: experiment executions cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS experiment_executions_no_delete BEFORE DELETE ON experiment_executions BEGIN SELECT RAISE(ABORT, 'append-only: experiment executions cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS experiment_observations_no_update BEFORE UPDATE ON experiment_observations BEGIN SELECT RAISE(ABORT, 'append-only: experiment observations cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS experiment_observations_no_delete BEFORE DELETE ON experiment_observations BEGIN SELECT RAISE(ABORT, 'append-only: experiment observations cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS experiment_outcomes_no_update BEFORE UPDATE ON experiment_outcomes BEGIN SELECT RAISE(ABORT, 'append-only: experiment outcomes cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS experiment_outcomes_no_delete BEFORE DELETE ON experiment_outcomes BEGIN SELECT RAISE(ABORT, 'append-only: experiment outcomes cannot be deleted'); END;
