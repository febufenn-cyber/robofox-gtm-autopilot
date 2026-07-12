# Data Classification

## PUBLIC

Reusable skills, schemas, synthetic fixtures, empty templates, public methodology, and reviewed documentation. PUBLIC data may be committed here.

## INTERNAL

Non-personal operating context such as product hypotheses, aggregate metrics, and generic experiment designs. INTERNAL data belongs in the private workspace unless deliberately sanitized and reviewed.

## CONFIDENTIAL

Pricing negotiations, pipeline values, win/loss analysis, customer objections, internal weaknesses, forecasts, and strategy. CONFIDENTIAL data is forbidden in the public engine.

## RESTRICTED

Names, personal email addresses, phone numbers, recordings, transcripts, health information, credentials, tokens, account identifiers, payment information, and consent records. RESTRICTED data is forbidden in the public engine.

## Handling rules

- Use aggregate data before pseudonymous records and pseudonymous records before identifiable data.
- The strongest applicable classification wins.
- Do not lower classification merely because information is already present in a third-party system.
- Logs must contain identifiers only when operationally necessary and must never contain secrets or full message bodies.
- Public examples must be synthetic and visibly labelled.
