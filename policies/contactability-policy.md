# Consent and Contactability Policy

A record existing in a CRM does not authorize contact. Contactability is evaluated independently for each channel.

Allowed statuses:

- `unknown`
- `not_requested`
- `opted_in`
- `opted_out`
- `do_not_contact`
- `expired`
- `legitimate_existing_relationship`
- `requires_manual_review`

## Rules

- Unknown consent does not authorize automated outreach.
- `do_not_contact` and `opted_out` suppress contact.
- Conflicting records resolve to the most restrictive status.
- Missing capture time or source requires manual review.
- Permission for one channel does not transfer to another channel.
- Suppression records are retained as needed to honour the restriction.
- Phase 0 never sends, even when a record is opted in.
