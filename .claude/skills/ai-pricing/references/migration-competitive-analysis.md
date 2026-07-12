# AI pricing — migration and competitive analysis

Upstream detail moved here to keep `SKILL.md` below 500 lines.

## Pricing Migration Strategy

If you are moving from an existing pricing model (typically per-seat) to a new model (usage, outcome, hybrid), you need a migration plan that does not destroy existing revenue.

### Migration Playbook

| Phase | Duration | Actions |
|---|---|---|
| 1. Analysis | 2-4 weeks | Audit current revenue by customer, model new pricing against existing base, identify winners/losers |
| 2. Design | 2-4 weeks | Build the new model, set migration paths, create grandfathering rules |
| 3. Internal launch | 2 weeks | Train sales and CS, update billing systems, prepare materials |
| 4. Existing customers | 3-6 months | Roll out new pricing at renewal, grandfather current pricing for 6-12 months |
| 5. New customers | Immediate | All new customers on new pricing from day one |
| 6. Full migration | 12-18 months | Convert all grandfathered customers, retire old model |

### Grandfathering Rules

- Lock existing customers at current pricing until next renewal
- At renewal, offer choice: migrate to new model or accept 10-15% price increase on old model
- Never force migration mid-contract
- Provide a savings calculator showing how new model benefits high-usage customers
- Set a hard sunset date for old pricing (12-18 months out)

## Competitive Pricing Analysis Framework

### Positioning Matrix

```
                    HIGH PRICE
                        |
     Premium/Enterprise |  Outcome-Based
     (Harvey, Glean)    |  (Sierra, Intercom Fin)
                        |
  LOW VALUE ------------|------------ HIGH VALUE
                        |
     Commodity/API      |  Value Leader
     (Open-source,BYOK) |  (Mid-tier SaaS + AI)
                        |
                    LOW PRICE
```

### Competitive Response Playbook

| Competitor Move | Your Response | Do NOT |
|---|---|---|
| Drops price 30%+ | Hold price, emphasize ROI and outcomes | Race to the bottom |
| Launches free tier | Add a free tier if you do not have one, make it generous | Ignore it hoping it goes away |
| Moves to outcome pricing | Evaluate your outcome measurability, test with segment | Copy without clear outcome attribution |
| Bundles AI into platform | Unbundle and show superior depth in your niche | Try to out-bundle a platform player |
| Offers BYOK | Decide based on your archetype (see BYOK section) | Offer BYOK reactively without a strategy |

