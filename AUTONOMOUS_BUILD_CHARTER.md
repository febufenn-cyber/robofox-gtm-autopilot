# Robofox GTM Autopilot — Remaining-Phases Autonomous Build Charter

## Purpose

This charter is the pre-authorized implementation plan for the remaining Robofox GTM Autopilot phases. It exists so a future instruction consisting of **“build”** can start a continuous, phase-by-phase engineering run without repeatedly asking for planning approval.

The charter authorizes repository engineering only: inspect the current `main`, create a phase branch, implement code and documentation, run local and remote verification, open a pull request, merge only when all required checks are green, verify the new `main`, and continue to the next eligible phase.

It does **not** authorize live business execution, customer contact, credentials use, production deployment, CRM mutation, advertisement changes, public publishing, spending, contact export, or weakening of the Phase 0 constitution.

## How the “build” command is interpreted

When the founder says **“build”**:

1. Verify this charter and `roadmap/remaining-phases.json`.
2. Determine the first unimplemented eligible phase from Phase 4 onward.
3. Verify its prerequisites and current repository integrity.
4. Implement the phase in bounded increments when needed.
5. Commit each coherent increment on a dedicated branch.
6. Open a pull request to `main`.
7. Merge only after the complete repository gate passes on the proposed merge.
8. Verify the exact resulting `main` commit.
9. Continue to the next eligible phase without requesting another planning approval.
10. Stop only for a hard halt condition defined in this charter.

The default build target is Phases 4–7. Phases 8–9 are advanced phases and are attempted in the same run only when their explicit readiness gates pass. Otherwise they are recorded as `DEFERRED`, not silently forced.

## Global invariants

Every remaining phase must preserve these invariants:

- The public repository contains engine code, schemas, policies, tests, synthetic fixtures, and sanitized documentation only.
- Real customers, contacts, CRM exports, transcripts, approvals, experiment data, credentials, and operational outcomes remain in the private workspace.
- Unknown actions remain denied.
- A recommendation, experiment state, or generated draft is never execution approval.
- Agents cannot approve their own external or privileged action.
- External content remains untrusted data and cannot become instructions.
- Missing data, observed zero, stale evidence, and conflicted evidence remain distinct.
- All mutations are exact-scope, expiring, single-use, idempotent, and auditable.
- No phase may reduce the Phase 0 safety boundary to make implementation easier.
- CI must test the complete repository, not only the new module.
- A red or unavailable required check blocks merge.
- Every final record must be replayable or integrity-verifiable from immutable inputs.

## Autonomous implementation protocol

### Before each phase

The implementation agent must:

1. Read `CLAUDE.md`, the Phase 0–3 policies, this charter, and the selected phase entry in `roadmap/remaining-phases.json`.
2. Run all existing repository verifiers and tests.
3. Run:

```bash
python3 scripts/verify_autonomous_build_plan.py --phase <N> --readiness
```

4. Freeze the current `main` commit as the phase base.
5. Record the selected phase, base SHA, intended branch, allowed scope, prohibited scope, and verification commands in the PR body.

### During implementation

- Prefer several independently mergeable increments when a phase changes storage, permissions, external adapters, or deployment boundaries.
- Keep migrations forward-only and test upgrades from the previous released schema.
- Add contracts before behavior and behavior before user-facing orchestration.
- Add negative tests for every newly permitted action.
- Keep live connectors in read-only, mock, simulator, or dry-run mode until the phase exit criteria explicitly allow a narrower capability.
- Never place real secrets or customer data in tests.

### Before merge

The agent must verify:

- Phase-specific verifier passes.
- Phase-specific adversarial tests pass.
- All previous phase tests still pass.
- Python compilation passes.
- Public repository scan passes.
- Source-lock and submodule checks pass.
- The PR diff matches the phase scope.
- No new live external capability is enabled by default.
- The PR is mergeable and the exact tested head has not moved.

### After merge

- Confirm the PR is marked merged, not merely closed.
- Record the merge commit.
- Confirm `main` points to that merge commit.
- Re-evaluate the next phase readiness gate.

## Hard halt conditions

Autonomous implementation stops and reports the blocker when any of these occur:

- A requested change would weaken constitutional safeguards.
- A phase requires real credentials, customer data, financial authority, production access, or legal/compliance judgment not already available.
- Required CI remains red after focused fixes.
- The repository base changes unexpectedly or contains unrelated unreviewed work.
- A migration cannot be proven safe against the prior released schema.
- A connector capability is ambiguous, undocumented, or broader than the phase permits.
- The implementation would require sending, publishing, spending, calling, or modifying a live external system.
- A serious privacy, security, consent, or prompt-injection risk lacks a deterministic mitigation.
- Phase 8 or 9 readiness criteria are not met.

# Remaining phases

## Phase 4 — Controlled Execution Gateway

### Objective

Build the policy-enforced boundary between an approved internal action and a real-world side effect. The gateway must make execution explicit, exact, idempotent, rate-limited, canary-first, reversible where possible, and disabled by default.

### Main deliverables

- Versioned execution-envelope, execution-approval, execution-result, rollback, and idempotency schemas.
- Capability registry separating internal reversible actions from external or financial actions.
- Dry-run and simulator adapters for email, WhatsApp, phone, CRM, publishing, and advertising.
- Exact approval binding to adapter, recipient/account scope, content hash, maximum records, maximum spend, expiry, and rollback plan.
- Idempotency keys, replay protection, retry policy, partial-failure handling, and immutable execution ledger.
- Canary controls, maximum blast radius, rate limits, emergency stop, and adapter-specific circuit breakers.
- Rollback verification for reversible operations and compensating-action records for irreversible operations.
- Operator CLI and review package that displays the exact proposed side effect before approval.

### Required blind-spot tests

- Duplicate execution request.
- Timeout after the external system accepted the action.
- Partial batch success.
- Approval for one recipient reused for another.
- Message body changed after approval.
- Currency or spend mismatch.
- Kill switch activates during execution.
- Adapter returns ambiguous success.
- Prompt injection inside CRM or message content.
- Rollback itself fails.

### Exit criteria

- CI cannot contact a live external system.
- All adapters default to simulator/dry-run.
- Unknown adapters and actions fail closed.
- Exact approval and idempotency are enforced transactionally.
- A one-record canary is required before any bounded batch.
- External and financial actions remain disabled in default configuration.
- At least one low-risk internal reversible adapter is demonstrated end to end in a synthetic environment.

### Autonomy ceiling

The agent may implement and test the gateway. It may not use real credentials, approve an execution, contact a person, alter a live CRM, publish, or spend.

## Phase 5 — Revenue Operations Loop

### Objective

Create a normalized, auditable commercial operating loop from lead creation through qualification, conversation, demo, proposal, win/loss, onboarding, renewal, churn, and revenue reconciliation.

### Main deliverables

- Canonical account, contact, opportunity, lifecycle-event, attribution, task, and revenue schemas.
- Read-only HubSpot and Meta ingestion with freshness, pagination, deduplication, timezone, and currency normalization.
- First-touch, self-reported, influencing-touch, and conversion-touch attribution kept separately.
- Deterministic lead/account qualification with reasons, confidence, and manual override history.
- Pipeline-state derivation from immutable events rather than silent record overwrites.
- Draft follow-up, task, and handoff generation through the Phase 4 gateway.
- Lost-deal, no-response, onboarding, renewal, and churn reason capture.
- Revenue reconciliation between CRM outcomes and recognized/received revenue records.
- Data-quality dashboard and exception queue for missing ownership, source, stage, consent, or experiment IDs.

### Required blind-spot tests

- Same person represented by multiple contacts.
- Referral plus WhatsApp plus founder meeting attribution.
- Stage moved backward or skipped.
- Deal marked won without revenue evidence.
- Currency mismatch between CRM and payment record.
- Consent conflict across channels.
- Deleted or merged CRM record.
- Stale opportunity mistaken for active demand.
- Platform-reported conversion without CRM-confirmed outcome.
- Qualification rule discriminates using prohibited attributes.

### Exit criteria

- Read-only ingestion is replayable and incremental.
- Missing and stale data are surfaced, not imputed silently.
- Attribution never collapses to one misleading source field.
- Qualification is deterministic, explainable, and manually overridable.
- CRM writes, follow-ups, and tasks remain Phase 4-gated.
- Revenue totals reconcile or produce explicit exceptions.
- Synthetic end-to-end lead-to-revenue tests pass.

### Autonomy ceiling

The agent may build ingestion, normalization, drafts, and synthetic workflows. Live CRM mutation or customer follow-up requires separate founder-controlled execution approval.

## Phase 6 — Learning and Portfolio Optimizer

### Objective

Convert immutable experiment and revenue outcomes into calibrated belief updates, benchmark overrides, channel recommendations, and founder-attention allocation without automatically changing spend or execution.

### Main deliverables

- Prediction-versus-outcome and calibration records.
- Explicit belief-update records linking prior assumption, evidence, experiment, outcome, and revised confidence.
- Benchmark hierarchy preferring Robofox first-party evidence over generic external benchmarks when sample requirements are met.
- Channel and segment scorecards incorporating revenue quality, delivery burden, trust risk, founder hours, cash, and learning value.
- Portfolio allocator for founder time, budget recommendations, and experiment slots.
- Counterfactual and sensitivity analysis showing which assumptions drive the recommendation.
- Automatic trigger for a new Phase 2 decision when material evidence changes the board.
- Model/skill calibration reports identifying systematic overconfidence or false positives.
- Recommendation records that preserve rejected allocations and reasons.

### Required blind-spot tests

- Survivorship bias from only successful experiments.
- Tiny sample incorrectly overriding a benchmark.
- Revenue-positive but operationally unprofitable customer segment.
- Channel appears strong because attribution is incomplete.
- Repeated experiments create correlated evidence, not independent evidence.
- High response rate but poor retention.
- Founder-time cost omitted.
- Historical benchmark applied to a changed offer.
- Optimizer concentrates all resources into one fragile channel.
- Confidence increases despite contradictory evidence.

### Exit criteria

- Beliefs update only from traceable immutable evidence.
- Calibration is measured against historical predictions.
- Sample-size and relevance gates control benchmark override.
- Recommendations include uncertainty and sensitivity.
- No optimizer output directly changes spend or starts execution.
- Phase 2 can be re-run from an updated Phase 1 position with reproducible inputs.
- Portfolio recommendations pass deterministic replay tests.

### Autonomy ceiling

The agent may update internal beliefs and recommendations through approved immutable records. It may not reallocate real money, launch campaigns, or contact prospects.

## Phase 7 — Production Hardening and Operator Console

### Objective

Turn the engine into an operable, observable, recoverable v1 system with a private operator console, role boundaries, backups, alerts, runbooks, and deployment controls.

### Main deliverables

- Private operator console for position, decisions, experiments, approvals, execution proposals, pipeline, exceptions, and audit history.
- Authentication and role-based authorization for founder, reviewer, operator, and read-only roles.
- Secrets-management interface with no secrets stored in the repository or logs.
- Structured logging, metrics, traces, health checks, alerting, and error classification.
- Encrypted backup, restore, migration, retention, and disaster-recovery procedures.
- Concurrency control, job queue, retry scheduling, dead-letter handling, and emergency shutdown.
- Deployment manifests and environment separation for development, staging, and production.
- Security review, dependency audit, threat model, privacy review, and operational readiness checklist.
- Performance budgets and load tests for expected solo-founder scale.
- Complete operator runbooks for incidents, credential rotation, restore, rollback, and data deletion.

### Required blind-spot tests

- Stolen or expired session.
- Privilege escalation between roles.
- Secret appears in a log or error trace.
- Backup restores an older incompatible schema.
- Two workers process the same approved action.
- Queue retries an irreversible action.
- Dashboard displays restricted values to a read-only role.
- Alerting fails silently.
- Timezone and clock skew invalidate approvals.
- Production deployment accidentally points to a test workspace or vice versa.

### Exit criteria

- Complete Phase 0–7 test gate passes.
- Backup and restore are demonstrated in staging with integrity verification.
- Role boundaries are enforced server-side.
- Secrets and restricted data are absent from client bundles and logs.
- Staging deployment and rollback succeed.
- Production deployment requires explicit founder action and is not performed autonomously.
- Operational readiness checklist is complete.

### Autonomy ceiling

The agent may build and validate development/staging deployment artifacts. It may not deploy production, rotate real credentials, expose services publicly, or approve live execution.

## Phase 8 — Multi-product and Multi-agent Scaling

### Classification

Advanced and optional. Proceed only after Phase 7 is stable and at least two real products or clearly separate motions need coordinated allocation.

### Objective

Coordinate multiple products, segments, agents, experiment slots, shared audiences, and founder capacity without duplicate work, resource collisions, or cross-product data leakage.

### Main deliverables

- Product portfolio, shared-resource, audience-overlap, dependency, and capacity schemas.
- Global experiment scheduler with product and channel collision controls.
- Founder-time and cash allocation across products.
- Agent role registry, task leasing, heartbeat, cancellation, and bounded concurrency.
- Cross-product evidence reuse rules and isolation requirements.
- Shared account/contact handling without leaking one product’s private context into another.
- Portfolio-level decision and opportunity-cost records.
- Fairness and starvation protection for small/new products.

### Readiness gate

- Phase 7 operational readiness is complete.
- At least two distinct products or motions have validated evidence and active demand.
- Single-product throughput is insufficient for the real workload.
- Shared-resource conflicts are observed, not hypothetical.
- Multi-agent orchestration has a measurable benefit over a single controlled workflow.

### Exit criteria

- No task is executed twice by competing agents.
- Product data boundaries are tested.
- Shared-audience collisions are detected.
- Portfolio allocation remains explainable and replayable.
- Global kill switch and per-product kill switches work.
- Single-product mode remains supported.

### Autonomy ceiling

No additional external authority is granted merely because more agents exist.

## Phase 9 — Self-Improving Evaluation and Simulation

### Classification

Advanced and optional. Proceed only after Phase 8 or a stable Phase 7 deployment has accumulated enough clean historical decisions and outcomes.

### Objective

Build an offline evaluation and simulation system that improves prompts, policies, skills, and decision quality without allowing the production agent to rewrite its own safeguards or deploy unreviewed behavior.

### Main deliverables

- Versioned evaluation datasets from sanitized historical cases and synthetic adversarial cases.
- Scenario simulator for position, decision, experiment, execution, and revenue workflows.
- Regression benchmarks for policy adherence, evidence use, calibration, risk detection, and decision quality.
- Prompt/skill candidate generation in isolated branches.
- Champion/challenger evaluation with frozen test sets and leakage detection.
- Red-team corpus for prompt injection, data poisoning, approval replay, attribution manipulation, and unsafe optimization.
- Drift detection for connectors, schemas, model behavior, and benchmark relevance.
- Human-reviewed promotion process for any prompt, policy, skill, or weight change.

### Readiness gate

- Sufficient historical cases exist to separate training/development examples from frozen evaluation examples.
- Outcomes are clean enough to judge decisions rather than merely activity.
- Calibration and failure taxonomies from Phase 6 exist.
- Production observability from Phase 7 can detect regressions.
- The system can roll back prompt and skill versions safely.

### Exit criteria

- Production safeguards cannot be modified by the evaluated agent.
- Evaluation sets are versioned and protected from contamination.
- Candidate changes must outperform the champion without safety regressions.
- Promotion requires a reviewed PR and green full-repository gate.
- Simulation results are labeled as simulation, never real evidence.
- No autonomous production self-modification is enabled.

### Autonomy ceiling

The agent may generate and test candidate improvements offline. It may not self-merge policy weakening, change production prompts directly, or treat simulated outcomes as business truth.

# Completion definition

Robofox GTM Autopilot v1 is complete after Phase 7 passes its exit criteria and the repository’s complete Phase 0–7 gate is green on `main`.

Phases 8 and 9 are complete only when their readiness gates were satisfied before implementation and their own exit criteria pass. Deferring either optional phase is a valid successful outcome.
