PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS execution_envelopes (
 id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, action_type TEXT NOT NULL, adapter TEXT NOT NULL,
 mode TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE, batch_size INTEGER NOT NULL,
 canary_for_id TEXT, content_hash TEXT NOT NULL, created_at TEXT NOT NULL,
 record_json TEXT NOT NULL, record_hash TEXT NOT NULL, inserted_at TEXT NOT NULL,
 FOREIGN KEY(canary_for_id) REFERENCES execution_envelopes(id)
);
CREATE TABLE IF NOT EXISTS execution_attempts (
 id TEXT PRIMARY KEY, envelope_id TEXT NOT NULL, attempt_no INTEGER NOT NULL,
 started_at TEXT NOT NULL, finished_at TEXT NOT NULL, status TEXT NOT NULL,
 record_json TEXT NOT NULL, record_hash TEXT NOT NULL, inserted_at TEXT NOT NULL,
 UNIQUE(envelope_id, attempt_no), FOREIGN KEY(envelope_id) REFERENCES execution_envelopes(id)
);
CREATE TABLE IF NOT EXISTS execution_results (
 id TEXT PRIMARY KEY, envelope_id TEXT NOT NULL UNIQUE, outcome TEXT NOT NULL,
 affected_records INTEGER NOT NULL, spend_usd REAL NOT NULL, reversible INTEGER NOT NULL,
 completed_at TEXT NOT NULL, record_json TEXT NOT NULL, record_hash TEXT NOT NULL, inserted_at TEXT NOT NULL,
 FOREIGN KEY(envelope_id) REFERENCES execution_envelopes(id)
);
CREATE TABLE IF NOT EXISTS execution_rollbacks (
 id TEXT PRIMARY KEY, envelope_id TEXT NOT NULL UNIQUE, result_id TEXT NOT NULL UNIQUE,
 outcome TEXT NOT NULL, occurred_at TEXT NOT NULL, record_json TEXT NOT NULL, record_hash TEXT NOT NULL, inserted_at TEXT NOT NULL,
 FOREIGN KEY(envelope_id) REFERENCES execution_envelopes(id), FOREIGN KEY(result_id) REFERENCES execution_results(id)
);
CREATE TABLE IF NOT EXISTS execution_circuit_events (
 id TEXT PRIMARY KEY, adapter TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL,
 occurred_at TEXT NOT NULL, record_json TEXT NOT NULL, record_hash TEXT NOT NULL, inserted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS execution_approval_consumptions (
 approval_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE, action_type TEXT NOT NULL,
 manifest_hash TEXT NOT NULL, payload_hash TEXT NOT NULL, envelope_id TEXT NOT NULL,
 consumed_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS execution_envelopes_no_update BEFORE UPDATE ON execution_envelopes BEGIN SELECT RAISE(ABORT,'append-only: execution envelopes cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS execution_envelopes_no_delete BEFORE DELETE ON execution_envelopes BEGIN SELECT RAISE(ABORT,'append-only: execution envelopes cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS execution_attempts_no_update BEFORE UPDATE ON execution_attempts BEGIN SELECT RAISE(ABORT,'append-only: execution attempts cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS execution_attempts_no_delete BEFORE DELETE ON execution_attempts BEGIN SELECT RAISE(ABORT,'append-only: execution attempts cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS execution_results_no_update BEFORE UPDATE ON execution_results BEGIN SELECT RAISE(ABORT,'append-only: execution results cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS execution_results_no_delete BEFORE DELETE ON execution_results BEGIN SELECT RAISE(ABORT,'append-only: execution results cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS execution_rollbacks_no_update BEFORE UPDATE ON execution_rollbacks BEGIN SELECT RAISE(ABORT,'append-only: rollbacks cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS execution_rollbacks_no_delete BEFORE DELETE ON execution_rollbacks BEGIN SELECT RAISE(ABORT,'append-only: rollbacks cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS execution_circuit_events_no_update BEFORE UPDATE ON execution_circuit_events BEGIN SELECT RAISE(ABORT,'append-only: circuit events cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS execution_circuit_events_no_delete BEFORE DELETE ON execution_circuit_events BEGIN SELECT RAISE(ABORT,'append-only: circuit events cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS execution_approvals_no_update BEFORE UPDATE ON execution_approval_consumptions BEGIN SELECT RAISE(ABORT,'append-only: execution approvals cannot be updated'); END;
CREATE TRIGGER IF NOT EXISTS execution_approvals_no_delete BEFORE DELETE ON execution_approval_consumptions BEGIN SELECT RAISE(ABORT,'append-only: execution approvals cannot be deleted'); END;
