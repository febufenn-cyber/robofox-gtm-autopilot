# Operations and Deployment Policy

The operator console binds localhost by default and enforces authorization server-side. Roles are founder, reviewer, operator, and read-only. Restricted fields and secrets are redacted before logging or presentation.

Jobs use unique idempotency keys and expiring leases. Two workers cannot own one job. Irreversible jobs have one attempt and are never retried automatically. Exhausted jobs enter a dead-letter state.

Backups use scrypt-derived separate encryption and authentication keys, AES-256-CTR through the operating-system OpenSSL implementation, and encrypt-then-MAC verification. Restore checks authentication, schema identity, plaintext digest, and SQLite integrity.

Development, staging, and production workspaces are distinct. Production deployment, credential rotation, public exposure, and live execution require explicit founder action.
