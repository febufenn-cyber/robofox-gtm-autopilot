---
name: kill-criteria-review
description: "When the user wants a weekly GTM review, asks to compare live channels with pre-registered kill criteria, or says 'run my weekly GTM kill review.' Also triggers on 'Saturday GTM review,' 'keep iterate kill,' 'channel review,' and 'weekly commercialization review.' Reads HubSpot and Meta Ads through MCP and writes reviews/<ISO-week>.md. Do NOT use to auto-send outreach, edit ads, change budgets, launch campaigns, or invent missing performance data."
---

# Weekly GTM Kill-Criteria Review

Run this as a read-only Saturday operating review. Evaluate channels against rules registered before the results were known. The founder—not the agent—owns sends, ad changes, and relationship decisions.

## Required inputs

1. Latest applicable `plans/*-portfolio-*.md` file.
2. Relevant `context/products/*.md` file.
3. HubSpot MCP access.
4. Meta Ads MCP access when a Meta channel is live.
5. `references/review-schema.md`.

If an MCP is unauthenticated or a required field cannot be retrieved, record `INSUFFICIENT DATA`; do not fabricate it.

## Hard guardrails

- **Never auto-send outreach.** Every message remains a draft for founder review.
- **Never create, edit, pause, resume, or change an ad or budget.** This skill is read-only analysis.
- Alert and return `PAUSE — SAFETY` for outreach when complaint rate is above **0.1%** or bounce rate is above **2%**.
- Per-channel weekly primary KPI is **owner conversations and demos booked**, never features shipped.
- Preserve consent, opt-out, DND, and audit-log requirements.
- Do not substitute in-platform ROAS for CRM-confirmed outcomes.

## Procedure

### 1. Resolve the active plan

- Find the newest dated plan applicable to the product.
- Extract every ranked channel, budget share, primary KPI, and pre-registered kill criterion.
- If multiple plans have the same date, flag ambiguity rather than blending them.

### 2. Pull HubSpot data — read only

Use available HubSpot MCP tools to retrieve both the last 7 days and last 30 days:

- New contacts.
- Replies.
- Meetings or demos booked.
- Deals created.
- Deals won/lost when present.
- Source/channel for each metric.
- Verified sends, bounces, and complaints when those properties exist.

Keep raw denominator definitions visible. Do not calculate reply rate without verified sends; do not calculate CAC without attributable spend and customers.

### 3. Pull Meta Ads data — read only

Use available Meta Ads MCP tools for the same 7-day and 30-day windows:

- Spend.
- CTWA conversations started.
- Cost per conversation.
- Frequency.
- Campaign/ad-set/ad identifiers needed to attribute the result.

Use HubSpot-confirmed owner conversations, demos, and deals as the outcome layer whenever attribution exists. Treat Meta’s reported result as platform data, not final truth.

### 4. Normalize channel evidence

For each live channel, create one row containing:

| Field | Requirement |
|---|---|
| Channel | Exact name from the latest plan. |
| 7-day primary KPI | Owner conversations and demos booked. |
| 30-day primary KPI | Owner conversations and demos booked. |
| Supporting metrics | Replies, contacts, spend, CTWA conversations, frequency, deals. |
| Sample size | Denominator relevant to the criterion. |
| Criterion | Exact text from plan, or named default if absent. |
| Data confidence | Sufficient / insufficient, with reason. |

Do not merge channels merely because they share a platform.

### 5. Apply registered rules first

Use each channel’s plan criterion exactly. The plan criterion overrides defaults unless it violates a safety guardrail.

### 6. Apply defaults only when no criterion exists

| Channel type | Default kill rule |
|---|---|
| Cold outreach | `<2%` reply after `500` verified sends plus `2` copy iterations → `KILL`. |
| Paid | `CAC > ACV × 0.7 margin × (target_payback_months / 12)` after `$500` spend or `30 days` → `KILL`. |
| Any channel | Zero real conversations after `3 weeks` of genuine effort → `ITERATE` once, then `KILL` if the iteration also produces zero real conversations. |

If target payback months, attributable CAC, ACV, or spend is missing, use `INSUFFICIENT DATA`, not a guessed value.

### 7. Assign one verdict

| Verdict | Use when |
|---|---|
| `KEEP` | Criterion is met and the channel is producing relevant owner conversations/demos. |
| `ITERATE` | Evidence is below target but the registered criterion permits an iteration or sample is early but actionable. |
| `KILL` | A pre-registered or default kill threshold is conclusively crossed. |
| `INSUFFICIENT DATA` | Denominator, time window, attribution, or MCP data is inadequate. |
| `PAUSE — SAFETY` | Complaint/bounce guardrail is crossed or consent/compliance evidence is missing for active outreach. |

Do not use vanity metrics to rescue a channel that crossed its kill criterion.

### 8. Give one concrete next action per channel

The action must be singular and executable. Examples of action types:

- Keep the current offer and collect the next qualified owner conversation.
- Replace one copy hypothesis and return it as a draft for review.
- Stop new activity in the killed channel and document the learning.
- Repair attribution or required CRM fields before the next review.

Never include an action that directly sends a message or changes an ad.

### 9. Write the review

Write to `reviews/<ISO-week>.md`, using `references/review-schema.md`. Use the ISO week format `YYYY-Www`.

The review must state:

- Exact 7-day and 30-day windows.
- Source plan path.
- MCP data gaps.
- Safety alerts.
- One verdict and one action per channel.
- Which HubSpot-derived metrics have reached at least 30 relevant data points and therefore override industry benchmarks.

## First-party override rule

When a matching HubSpot-derived metric reaches at least 30 relevant data points, use it instead of the industry benchmark for that channel/segment/offer. Preserve sample size and denominator. Meta platform data alone does not override CRM outcome data.

## Completion check

Before saving, confirm:

- No send or ad mutation occurred.
- Every live channel appears exactly once.
- Every verdict cites a registered or default criterion.
- Every channel has exactly one concrete next action.
- Complaint and bounce thresholds were checked when data exists.
- Owner conversations and demos booked are the primary KPI.
