# Robofox GTM Autopilot

Internal commercialization tooling for a solo founder selling Robofox products. It combines Claude Code Agent Skills with read-only analysis from HubSpot and Meta Ads MCPs. It is not a customer-facing product, does not include a UI, and never authorizes automatic outreach sends or ad changes.

## Repository map

```text
.claude/skills/                 Claude Code skills
context/products/               Shared product context files
plans/                          Generated ranked channel portfolios
reviews/                        Saturday keep/iterate/kill reviews
vendor/agent-gtm-skills/        Read-only upstream reference snapshot
.mcp.json                      Project-scoped HubSpot and Meta Ads MCP definitions
scripts/register-mcps.sh        Optional MCP registration commands
scripts/publish-github.sh       Safe one-command private GitHub publication
scripts/verify_repo.py          Structural and dry-run verification
```

Installed upstream-derived skills:

- `positioning-icp`
- `solo-founder-gtm`
- `ai-cold-outreach`
- `ai-pricing`

Robofox-authored skills:

- `channel-portfolio-selector`
- `kill-criteria-review`

The full upstream versions are preserved under `vendor/`. Installed skills over 500 upstream lines were split into `references/` so every installed `SKILL.md` stays below 500 lines.

## 1. Register the remote MCPs

The project-scoped server definitions are already checked into `.mcp.json`. Open this repository in Claude Code, approve the project MCP configuration when prompted, then run `/mcp` to authenticate HubSpot and Meta Ads.

For an explicit CLI registration instead, run:

```bash
./scripts/register-mcps.sh
```

Equivalent commands:

```bash
claude mcp add --transport http hubspot https://mcp.hubspot.com/anthropic
claude mcp add --transport http meta-ads https://mcp.facebook.com/ads
```

Then open Claude Code and use `/mcp` to authenticate HubSpot and Meta Ads. The skills use read-only pulls for reviews; they do not send outreach or mutate ads.

## 2. Add a product

Copy the template:

```bash
cp context/products/_template.md context/products/<product-slug>.md
```

Fill every field without renaming or adding fields:

```text
product:
geography:
pricing_hypothesis:
ACV_usd:
motion:
stage:
team_size:
budget_monthly_usd:
existing_audience:
channels_already_available:
failed_channels:
```

Use lowercase kebab-case for the filename. Keep hypotheses explicitly marked as untested.

## 3. Run the channel selector

Natural prompt:

```text
Build a channel plan for my voice agent product using context/products/voice-agents.md.
```

The selector writes:

```text
plans/<product-slug>-portfolio-<YYYY-MM-DD>.md
```

It must rank three to five rule-selected channels, allocate 100% of the available budget, write Week 1–13 milestones, cite the benchmark reference, and pre-register kill criteria. Under a monthly budget below $500, it ranks owned channels only until first revenue.

The initial dry run is committed at:

```text
plans/voice-agents-portfolio-2026-07-12.md
```

## 4. Run the Saturday review

Natural prompt:

```text
Run my weekly GTM kill review for the voice agent product.
```

The review skill:

1. Finds the latest applicable plan.
2. Pulls last-7-day and last-30-day HubSpot data by source.
3. Pulls Meta spend, CTWA conversations, cost per conversation, and frequency when Meta is live.
4. Compares each channel with its pre-registered criterion.
5. Writes `KEEP`, `ITERATE`, `KILL`, `INSUFFICIENT DATA`, or `PAUSE — SAFETY` plus one concrete next action.
6. Saves `reviews/<ISO-week>.md`.

Primary KPIs are owner conversations and demos booked. Features shipped, impressions, and follower growth do not rescue a failing channel.

## 5. Monthly benchmark refresh

On the first Saturday after each completed month:

1. Pull the completed month’s HubSpot outcomes by channel, segment, offer, and geography.
2. Record the denominator and sample size for reply rate, meetings/demos, deals, CAC, and other used metrics.
3. Pull Meta platform data only as supporting data; use HubSpot-confirmed outcomes whenever attribution exists.
4. Update `.claude/skills/channel-portfolio-selector/references/benchmarks-2026.md` with the observed period, sample size, denominator, and a first-party label.
5. Once a matching metric has at least 30 relevant data points, mark the industry row `SUPERSEDED FOR ROBOFOX` and use the first-party metric in future plans/reviews.
6. Keep the old industry number for historical comparison and retain its vendor/aggregator bias flag.
7. Never add an unsupported benchmark; mark it `[UNVERIFIED]` or omit it.

## 6. Safety and operating rules

- Every outreach message is a draft until the founder reviews and sends it.
- Pause outreach if complaint rate exceeds 0.1% or bounce rate exceeds 2%.
- Preserve consent, opt-out, DND, and audit-log requirements.
- Do not trust in-platform ROAS as the sole outcome source.
- No skill may launch, edit, pause, or change an ad.
- This repository selects channels and reviews evidence; it does not replace founder judgment.

## 7. Verify the repo

```bash
python3 scripts/verify_repo.py
```

The verification checks structure, product fields, `<500`-line skill limits, negative trigger boundaries, natural prompt triggers, benchmark citation, the owned-channel budget gate, kill criteria, and Week 1–13 coverage.

## 8. Repository publication

The local repository is already initialized and committed on `main`. On a machine with an authenticated GitHub CLI, run:

```bash
./scripts/publish-github.sh
```

Defaults:

```text
owner: febufenn-cyber
repository: robofox-gtm-autopilot
visibility: choose deliberately; keep operating data in a separate private workspace
```

The script refuses to publish a dirty worktree or overwrite an existing `origin`. Override only when intentional:

```bash
GITHUB_OWNER=<owner> GITHUB_REPO=<name> GITHUB_VISIBILITY=private ./scripts/publish-github.sh
```

## 9. Phase 0 constitutional boundary

Phase 0 adds machine-checkable safeguards around the GTM skills:

- L1 advisory autonomy and an active-by-default kill switch
- default-deny action registry
- external sends, calls, CRM writes, ad changes, spending, publishing, and contact export disabled
- public-engine/private-workspace separation
- evidence-state, data-classification, and channel-contactability policies
- prompt-injection boundaries for CRM, MCP, web, document, and transcript content
- exact action-manifest and approval schemas
- public-repository scanning, source pinning, adversarial tests, and CI

Read [`PHASE0.md`](PHASE0.md) and [`policies/constitution.md`](policies/constitution.md), then run:

```bash
python3 scripts/verify_phase0.py
python3 -m unittest discover -s tests/phase0 -p 'test_*.py' -v
```

Create the operating workspace outside this public engine:

```bash
python3 scripts/bootstrap_private_workspace.py ~/private/robofox-gtm-workspace
```
