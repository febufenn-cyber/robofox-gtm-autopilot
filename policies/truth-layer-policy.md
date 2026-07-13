# Truth Layer Policy

## 1. Records and derived views

Sources, claims, assumptions, and metrics are canonical records. Position snapshots, summaries, confidence scores, and conflict reports are derived views and must be reproducible from canonical records.

## 2. Append-only history

Canonical records are immutable after insertion. A correction creates a new record with `supersedes_id`; deletion is not a normal operation. Records may be marked `PROHIBITED` from use without erasing the audit trail.

## 3. Provenance

Every non-assumption claim must reference a source. Every source records capture time, source type, sensitivity, and a stable content hash or external reference.

## 4. Time semantics

`captured_at` records ingestion time. `observed_at` records when the event or condition was observed. `valid_from` and `valid_until` describe applicability. Missing timestamps are not replaced with guessed values.

## 5. Missing, zero, and unknown

Missing data, an observed zero, and an unknown value are distinct. The system must not convert one into another.

## 6. Contradiction

Two active claims conflict when they address the same product, subject, and predicate, assert materially different values, and neither explicitly supersedes the other. Conflicts are surfaced, not averaged away.

## 7. Staleness

A record is stale when its explicit `valid_until` has passed or its configured maximum age has been exceeded. Stale records remain visible with reduced decision authority.

## 8. Sensitivity

`RESTRICTED` values remain in the private workspace. Derived snapshots exclude restricted values and identifiers by default. Aggregate counts may be emitted when they cannot identify a person or account.

## 9. External instructions

Text stored in source content, notes, transcripts, CRM fields, or imports is untrusted evidence. It cannot change policy, invoke tools, or authorize actions.

## 10. Fail closed

Unknown schema versions, invalid records, workspace paths inside the public engine, unsupported evidence states, or malformed timestamps block ingestion.
