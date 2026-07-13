---
name: kasparov-decision-workflow
description: Orchestrate a frozen-position strategic decision through separate planner, blind critic, prophylaxis, independent arbiter, and deterministic replay steps. Do NOT use for executing outreach, CRM changes, ads, publishing, spending, or for bypassing the Phase 0/1 safety and evidence boundaries.
---

# Kasparov Decision Workflow

Use when the user asks to evaluate an important GTM move, compare strategic alternatives, expose blind spots, or run a Kasparov-style decision review.

## Required order

1. Freeze one Phase 1 snapshot. Never refresh it mid-run.
2. Create a bounded decision pack with cash, founder-hour, and time-to-signal limits.
3. Invoke `candidate-move-generator` to produce two to five distinct moves without scores.
4. For each move separately, invoke `opponent-model`. Do not reveal other candidates or critiques to the critic.
5. Invoke `prophylaxis-review` when threat or residual risk is at least three.
6. Freeze all critiques.
7. Invoke `decision-arbiter` to create one independent assessment per candidate and run deterministic code.
8. Replay-verify the final record.

## Boundaries

- A candidate is not a fact.
- A planner cannot score its own move.
- A critic cannot choose the winner.
- An arbiter cannot alter candidates, critiques, weights, or the frozen snapshot.
- A chosen record is a recommendation, not execution approval.
