# External Action Policy

The repository operates at L1. The following are disabled:

- email or WhatsApp sends
- phone calls
- public publishing
- customer-visible pricing or promises
- CRM mutation
- advertisement launch, pause, edit, targeting, creative, or budget changes
- contact export

Allowed outputs are recommendations, plans, reviews, scripts, and drafts stored in approved local output directories. Draft generation must not imply that delivery occurred.

Tool availability is not permission. A write-capable third-party connector must be treated as read-only until a separate mediation layer enforces a per-method allowlist and invocation checks.
