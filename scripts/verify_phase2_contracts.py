#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
  "PHASE2.md","policies/decision-layer-policy.md","config/decision-weights.json",
  "schemas/candidate-move.schema.json","schemas/adversarial-review.schema.json",
  "schemas/decision-request.schema.json","schemas/decision-record.schema.json",
  "decisions/ADR-0009-freeze-position-before-calculation.md",
  "decisions/ADR-0010-independent-planner-and-critic.md",
  "decisions/ADR-0011-deterministic-bounded-arbitration.md",
  "decisions/ADR-0012-no-move-is-valid.md"
]
def verify(root: Path = ROOT) -> list[str]:
    errors=[]
    for rel in REQUIRED:
        if not (root/rel).is_file(): errors.append(f"missing Phase 2 contract: {rel}")
    for rel in [x for x in REQUIRED if x.endswith('.json')]:
        try: data=json.loads((root/rel).read_text())
        except Exception as exc: errors.append(f"invalid JSON {rel}: {exc}"); continue
        if rel.startswith('schemas/'):
            if data.get('type')!='object' or data.get('additionalProperties') is not False:
                errors.append(f"schema must be a closed object: {rel}")
            if not data.get('required'): errors.append(f"schema missing required fields: {rel}")
    weights_path=root/'config/decision-weights.json'
    if weights_path.is_file():
        w=json.loads(weights_path.read_text())
        if w.get('version')!=1: errors.append('decision weights version must be 1')
        if abs(sum(w.get('positive_weights',{}).values())-1.0)>1e-9: errors.append('positive weights must sum to 1')
        if w.get('candidate_count')!={'minimum':2,'maximum':5}: errors.append('candidate count must be 2..5')
        if w.get('tie_break_order',[])[-1:] != ['candidate_id']: errors.append('candidate_id must be final deterministic tie-break')
    policy=(root/'policies/decision-layer-policy.md')
    if policy.is_file():
        text=policy.read_text()
        for phrase in ('Frozen board position','Adversarial independence','Hard gates before scoring','Deterministic arbitration','No-move is valid','External-action boundary','Fail closed'):
            if phrase not in text: errors.append(f"decision policy missing section: {phrase}")
    return errors
if __name__=='__main__':
    errors=verify()
    if errors:
        print('PHASE2 CONTRACTS: FAIL'); [print(f'- {e}') for e in errors]; raise SystemExit(1)
    print('PHASE2 CONTRACTS: PASS')
    print('- frozen snapshot, independent critic, hard gates, prophylaxis, deterministic arbitration')
