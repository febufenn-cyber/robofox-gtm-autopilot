---
name: channel-portfolio-selector
description: "When the user wants to build a channel plan, rank acquisition channels, allocate a GTM budget, or asks 'build a channel plan for my voice agent product.' Also triggers on 'channel portfolio,' 'channel selection,' '90-day GTM plan,' 'which channels should I use,' and 'GTM budget split.' Takes a context/products/*.md file and writes a ranked portfolio to plans/. Do NOT use for executing campaigns, auto-sending outreach, changing ads, or writing a weekly keep/iterate/kill review."
---

# Channel Portfolio Selector

Select—not execute—a small channel portfolio for one Robofox product. The output must be defensible from the product context, explicit decision rules, first-party evidence, and the dated benchmark reference.

## Required input

Read one `context/products/*.md` file. It must contain:

- `product`
- `geography`
- `pricing_hypothesis`
- `ACV_usd`
- `motion`
- `stage`
- `team_size`
- `budget_monthly_usd`
- `existing_audience`
- `channels_already_available`
- `failed_channels`

If a value is missing, mark the resulting assumption `[UNVERIFIED]`; do not silently invent it. Do not add a channel that no applicable rule selects.

## Evidence precedence

| Priority | Evidence | Rule |
|---:|---|---|
| 1 | Robofox HubSpot/Meta data, matching metric and segment, `n >= 30` | Always overrides industry benchmarks. |
| 2 | Robofox data with `n < 30` | Use as an early signal; label insufficient for override. |
| 3 | `references/benchmarks-2026.md` | Directional comparison only; preserve its bias labels. |
| 4 | Any other number | Mark `[UNVERIFIED]` or omit it. |

Never average first-party and industry metrics into a synthetic benchmark.

## Rule order

Apply the rules in this order. When rules conflict, the more restrictive rule wins:

1. Safety and human-review guardrails.
2. Budget gate.
3. Geography gate.
4. ACV + motion fit.
5. Stage, audience, and channels already available.
6. Failed-channel exclusions.

## Explicit channel-selection rules

### ACV and motion

| IF | THEN prioritize | THEN skip / deprioritize |
|---|---|---|
| `ACV < $1K` **AND** `motion = self-serve` | PLG loops; Product Hunt/Hacker News launch; GEO/AI-citation pages; community; cheap Meta only if the budget gate permits | LinkedIn ads; field sales |
| `ACV = $1K–15K` | Founder-led sales; inbound/GEO; targeted newsletter or targeted LinkedIn; light signal-based outbound with human review only | Broad automated outbound; enterprise field sales; high-budget paid |
| `ACV > $50K` | Founder-led sales; ABM; partner/referral only | Broad self-serve launch tactics and non-targeted paid acquisition |

For ACV bands not covered above, mark the gap `[UNVERIFIED]` and choose no ACV-derived channel until the user supplies a rule.

### India-first B2B services

| IF | THEN prioritize | Constraint |
|---|---|---|
| `geography` is India-first B2B services | Local network/walk-ins; WhatsApp-first funnels; relevant community including SaaSBoomi; founder-led sales | Paid channels only after first organic proof, subject to the stricter budget gate. |

### Budget

| IF | THEN |
|---|---|
| `budget_monthly_usd < $500` | Select owned channels only until first revenue. Paid media, paid newsletters, and LinkedIn ads receive 0% and are not ranked. |
| Budget is unknown | Treat paid eligibility as `[UNVERIFIED]`; do not rank paid channels. |

### Stage and operating capacity

| IF | THEN |
|---|---|
| `stage = pre-first-10-customers` | Bias toward owner conversations, demos, proof collection, and short feedback loops. Do not optimize for reach. |
| `team_size = solo` | Rank at most five channels; each must fit founder time and have one primary KPI. |
| `existing_audience = minimal` | Do not assume audience-led launch performance; use build-in-public as support, not the sole acquisition engine. |
| A channel is listed in `failed_channels` | Do not reselect it unless the context includes a materially changed hypothesis; state the change. |

## Candidate normalization

Combine overlapping tactics into one channel when they share the same buyer journey. Examples:

- Local introductions, walk-ins, and founder demos → **Founder-led local sales**.
- Warm introductions and permission-based follow-up on WhatsApp → **WhatsApp-first warm funnel**.
- Comparison/entity/proof pages intended to earn search and AI citations → **Bottom-funnel GEO/entity content**.

Do not disguise paid acquisition as an owned channel.

## Ranking method

Score each rule-selected candidate qualitatively on:

| Dimension | Question |
|---|---|
| Buyer proximity | Does it create direct access to clinic/coaching-centre owners or decision-makers? |
| Speed to conversation | Can it generate owner conversations within the current stage? |
| Budget fit | Does it obey the strict budget gate? |
| Founder fit | Can one founder operate it without sacrificing delivery? |
| Evidence fit | Is it supported by the context, first-party data, or a cited benchmark? |

Rank buyer proximity and speed to real conversations above impressions, clicks, followers, or features shipped.

## Budget allocation

- Allocate exactly 100% across the ranked 3–5 channels.
- Percentages represent the available monthly GTM budget and may include travel, demo collateral, data verification, CRM/tools, hosting, or content production.
- Under the `<$500` gate, allocate 0% to ad spend and paid placements until first revenue.
- Do not fabricate exact rupee/dollar amounts when the context provides only a ceiling.

## Pre-registered kill criteria

Every ranked channel must have criteria written before execution:

| Channel type | Default criterion |
|---|---|
| Cold outreach | Kill if reply rate is below 2% after 500 verified sends and two copy iterations. All sends require human review. |
| Paid | Kill if `CAC > ACV × 0.7 margin × (target_payback_months / 12)` after $500 spend or 30 days. Only applicable when paid is eligible. |
| Any channel | Zero real conversations after three weeks of genuine effort → iterate once, then kill. |
| Generic informational SEO | Kill the generic informational approach; retain only comparison/entity/proof pages that can create qualified conversations. |

Any new threshold not supplied by these rules or first-party evidence must be labeled `[PRE-REGISTERED INTERNAL HYPOTHESIS — UNVERIFIED]`.

## 90-day plan rules

- Write weekly milestones for Weeks 1–13.
- Each week must prioritize owner conversations, demos, proof, and learning—not features shipped.
- Do not schedule automated sends or ad changes.
- A milestone may prepare a draft campaign, but publication/sending remains a founder action.

## Output contract

Write to:

`plans/<product-slug>-portfolio-<YYYY-MM-DD>.md`

The file must contain, in this order:

1. Title and date.
2. Source product context and benchmark citation.
3. Decision trace showing which IF/THEN rules fired.
4. Three to five ranked channels, each with one paragraph of reasoning.
5. A budget table totaling 100%.
6. A primary KPI and pre-registered kill criteria for every channel.
7. First-90-days plan with weekly milestones for Weeks 1–13.
8. Explicit excluded/deferred channels and the rule that excluded them.
9. Data override note: matching HubSpot-derived numbers supersede benchmarks once `n >= 30`.

## Quality gate

Before saving, verify:

- The benchmark file is cited.
- The budget totals 100%.
- No paid channel is ranked when budget is below $500/month.
- India-first local/founder channels rank above any eligible paid channel.
- Every ranked channel has a primary KPI and kill criteria.
- No outreach is authorized for automatic sending.
- No benchmark number was invented; unsupported numbers are marked `[UNVERIFIED]`.

If the output fails, fix the reasoning or this skill and regenerate the plan. Do not hand-edit the plan to conceal a rule failure.
