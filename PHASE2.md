# Phase 2 — Kasparov Decision Engine

Phase 2 converts a frozen Phase 1 commercial-position snapshot into an auditable strategic decision. It separates proposal, adversarial refutation, prophylaxis, and deterministic arbitration.

The model may author candidate moves and critiques. Deterministic code controls eligibility, exposure limits, conflict gates, scoring, tie-breaking, and the final decision record.

## Required sequence

1. Freeze one position snapshot and its canonical hash.
2. State one decision question and bounded cash, founder-time, and signal-time limits.
3. Produce two to five materially distinct candidate moves without self-scoring.
4. Produce one blind, independent adversarial review for every candidate.
5. Add threat-specific prophylaxis when threat or residual risk is material.
6. After critiques are frozen, produce one independent `ARBITER` score assessment per candidate.
7. Apply hard gates before scoring.
8. Rank only eligible candidates with the versioned ordinal scorecard.
9. Record the chosen move or an explicit no-move / needs-evidence / blocked-conflict result.
10. Preserve rejected alternatives and evidence that would change the decision.

Phase 2 never sends outreach, changes CRM, modifies ads, publishes content, spends money, or executes the chosen move.

## Role separation

- `PLANNER`: proposes moves and cannot score them.
- `CRITIC`: sees one candidate, produces the strongest refutation, and cannot see other critiques.
- `ARBITER`: sees all frozen candidates and critiques, supplies bounded ordinal assessments, then invokes deterministic code.
