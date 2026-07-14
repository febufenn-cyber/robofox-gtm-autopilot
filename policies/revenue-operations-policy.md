# Revenue Operations Policy

## Read-only ingestion

HubSpot, Meta, manual, and synthetic inputs enter only as versioned read-only snapshots with source, cursor, timestamped records, and canonical hash. This layer has no connector write method.

## Identity and privacy

Public contracts and normalized records use pseudonymous identifiers. Direct names, email addresses, phone numbers, addresses, credentials, secrets, and tokens are prohibited.

## Attribution

First touch, self-reported source, influencing channels, and conversion touch are stored independently. No single platform field becomes unquestioned attribution truth.

## Qualification

Qualification is deterministic and explainable. It may use segment fit, pain, authority, urgency, budget signals, and consent status. Race, religion, caste, gender, health, disability, age, nationality, and political views are prohibited.

## Pipeline and revenue

Lifecycle state is derived from immutable events. Stage regressions and suspicious skips are exceptions rather than silent corrections. `WON` without recognized or received positive revenue is unreconciled.

## External-action boundary

Follow-up messages, CRM tasks, stage changes, and other writes are proposals only and remain Phase 4-gated. No customer contact or live CRM mutation is authorized.
