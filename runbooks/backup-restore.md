# Backup and Restore Runbook

- Use a founder-controlled passphrase of at least 16 characters.
- Create encrypted, authenticated backups from a consistent SQLite backup snapshot.
- Store backup and passphrase separately.
- Restore first to a new staging path, never over the production file.
- Verify HMAC, schema label, plaintext digest, SQLite integrity, foreign keys, and application-level record hashes.
- Run the complete Phase 0–7 gate against the restored staging workspace.
- Record the backup identifier, restore target, operator, verification result, and rollback plan.
- Production replacement requires explicit founder approval and a final pre-cutover backup.
