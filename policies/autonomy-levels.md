# Autonomy Levels

| Level | Name | Allowed examples | Prohibited examples |
|---|---|---|---|
| L0 | Observe | Read approved files, validate schemas, summarize evidence, identify contradictions | Draft outreach, mutate records, recommend spend |
| L1 | Advise | Plans, experiments, reviews, drafts, proposed internal tasks | Send, call, publish, change CRM, change ads, spend money |
| L2 | Reversible internal | Bounded internal labels/tasks/status updates after exact approval | Customer contact, financial or public action |
| L3 | Limited operational | Pre-approved reversible internal operations with expiry, cap, rollback, and canary | Open-ended execution or relationship decisions |
| L4 | External/financial | Sends, calls, publishing, pricing offers, campaign changes, budget changes | Disabled until separately designed and approved |

## Rules

- The configured level is a ceiling, not a target.
- Possessing a tool does not grant permission to use it.
- Unknown or ambiguous actions are denied.
- L2 and above require an action manifest and approval unless a future policy explicitly identifies a deterministic exception.
- L4 remains disabled during Phase 0.
