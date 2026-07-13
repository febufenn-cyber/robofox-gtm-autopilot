---
name: candidate-move-generator
description: Generate two to five materially distinct, bounded strategic candidate moves from one frozen position snapshot. Do NOT use to score candidates, view critiques, execute actions, fabricate evidence IDs, or exceed the decision request's exposure limits.
---

# Candidate Move Generator

For each candidate, write a record matching `schemas/candidate-move.schema.json`.

Requirements:

- Bind to the exact snapshot hash and product.
- Address the observed current constraint through a distinct mechanism.
- State assumptions explicitly.
- Cite only record IDs present in the frozen snapshot.
- Define success signal, kill criteria, conversion plan, trust risk, and maximum exposure.
- Use `created_by_role: PLANNER`.
- Do not include ranking scores or mention other candidate critiques.

Prefer reversible, high-learning moves over broad activity plans.
