# Decision Layer Policy

## Frozen board position

Every decision binds to one canonical Phase 1 position snapshot hash. Candidate and critique files with another hash are invalid. The snapshot is never silently refreshed during calculation.

## Candidate independence

A decision requires two to five candidate moves. Candidates must be authored before critiques are revealed. A candidate is not evidence merely because it is plausible or eloquent.

## Adversarial independence

Every candidate requires exactly one blind critic record. The critic records the strongest refutation, concrete failure modes, disconfirming evidence, threat level, residual risk, and prophylaxis. Critiques do not see other critiques before submission.

## Hard gates before scoring

A candidate is ineligible when it exceeds cash, founder-hour, or time-to-signal limits; lacks a kill criterion, conversion plan, success signal, critique, or required prophylaxis; depends on unavailable evidence; or binds to the wrong product or snapshot.

The whole decision is blocked when the current constraint is `CONFLICTED` or `UNKNOWN`. Configured trust, delivery, or data-quality conflicts also block selection. A blocked decision may identify evidence to collect but cannot choose a move.

## Independent arbiter assessment

The planner cannot score its own proposal. After all blind critiques are frozen, exactly one independent `ARBITER` assessment supplies bounded ordinal scores and a justification for every score dimension. Assessment timestamps must follow the critique timestamps.

## Deterministic arbitration

Eligible moves are scored with versioned ordinal inputs. The score is not a probability or revenue forecast. Positive dimensions reward constraint alignment, learning value, reversibility, feasibility, conversion readiness, and evidence strength. Trust, residual-risk, and exposure penalties reduce the score.

Ties resolve by lower residual risk, lower trust risk, lower cash exposure, lower founder hours, lower time to signal, then candidate identifier. No language-model vote or consensus changes this order.

## Prophylaxis

Threat level or residual risk of three or higher requires at least one threat-specific mitigation and a verification condition. Generic advice such as “monitor carefully” is not sufficient.

## No-move is valid

When every candidate is ineligible, evidence is inadequate, or a blocking conflict exists, the correct output is `NO_MOVE`, `NEEDS_EVIDENCE`, or `BLOCKED_CONFLICT`. The engine must not choose merely to produce an answer.

## Audit record

The final record preserves the snapshot hash, input hashes, candidate component scores, blockers, rejected alternatives, current constraint, unresolved conflicts, assumptions, maximum exposure, rationale, confidence, and evidence that would change the decision.

## External-action boundary

Phase 2 produces recommendations only. Execution remains governed by later phases and Phase 0 action policy. No decision record is approval to contact a person, mutate a system, publish, or spend.

## Fail closed

Unknown fields, malformed scores, missing reviews, duplicated IDs, hash mismatches, non-finite values, future timestamps, or unsupported contract versions fail closed.
