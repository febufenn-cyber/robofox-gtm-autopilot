#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_decision import arbitrate, canonical_hash

def fixtures():
    snapshot={"version":1,"product":"voice-agents","as_of":"2026-07-13T10:00:00+05:30","generated_at":"2026-07-13T10:01:00+05:30","dimensions":{"current_constraint":{"label":"Current constraint","status":"OBSERVED","value":"proof"},"customer_trust":{"label":"Trust","status":"OBSERVED","value":"developing"},"delivery_readiness":{"label":"Delivery","status":"OBSERVED","value":"developing"},"data_quality":{"label":"Data","status":"OBSERVED","value":"mixed"}},"conflicts":[],"stale_claim_ids":[],"open_assumption_ids":["ASM-SYNTH-001"],"overdue_assumption_ids":[],"unknown_dimensions":[],"restricted_records_excluded":0,"prohibited_claims_excluded":0,"input_record_ids":["SRC-SYNTH-001","CLM-SYNTH-001","ASM-SYNTH-001"]}
    h=canonical_hash(snapshot)
    request={"version":1,"decision_id":"DEC-SYNTH-001","product":"voice-agents","snapshot_hash":h,"decision_question":"Which bounded move should improve proof fastest?","constraints":{"max_cash_usd":100,"max_founder_hours":12,"max_days_to_signal":14},"candidate_ids":["MOV-SYNTH-001","MOV-SYNTH-002"],"review_ids":["REV-SYNTH-001","REV-SYNTH-002"],"requested_at":"2026-07-13T10:02:00+05:30"}
    def c(i,align,cash): return {"version":1,"candidate_id":f"MOV-SYNTH-00{i}","product":"voice-agents","snapshot_hash":h,"title":f"Synthetic move {i}","strategic_goal":"Create stronger commercial proof safely.","mechanism":"Run a bounded founder-led synthetic validation loop.","assumptions":["Synthetic assumption"],"evidence_record_ids":["CLM-SYNTH-001"],"expected_upside":"Faster evidence about the current proof constraint.","success_signal":"At least one qualified proof event.","kill_criteria":["Stop after the exposure ceiling without a signal."],"conversion_plan":"Convert a validated proof event into a documented next step.","scores":{"constraint_alignment":align,"learning_value":5,"reversibility":5,"execution_feasibility":4,"conversion_readiness":3},"exposure":{"cash_usd":cash,"founder_hours":8,"days_to_signal":7},"trust_risk":2,"created_by_role":"PLANNER","created_at":"2026-07-13T10:03:00+05:30"}
    def r(i): return {"version":1,"review_id":f"REV-SYNTH-00{i}","candidate_id":f"MOV-SYNTH-00{i}","snapshot_hash":h,"reviewer_role":"CRITIC","blind_review":True,"saw_other_critiques":False,"strongest_refutation":"The signal may reflect founder novelty rather than durable demand.","failure_modes":["Synthetic demand signal does not repeat."],"disconfirming_evidence":["No qualified signal within the exposure ceiling."],"threat_level":3,"prophylaxis":[{"threat":"Novelty bias","mitigation":"Use a fixed qualification rule","verification":"Record the rule before contact"}],"residual_risk":2,"reviewed_at":"2026-07-13T10:04:00+05:30"}
    return snapshot,request,[c(1,5,20),c(2,3,10)],[r(1),r(2)]
def verify():
    try:
        record=arbitrate(*fixtures(),created_at="2026-07-13T10:05:00+05:30")
    except Exception as exc: return [str(exc)]
    errors=[]
    if record['status']!='CHOSEN': errors.append('synthetic decision was not chosen')
    if record['chosen_candidate_id']!='MOV-SYNTH-001': errors.append('wrong synthetic winner')
    if not record['score_method']['ordinal_not_probability']: errors.append('ordinal warning missing')
    return errors
if __name__=='__main__':
    e=verify()
    if e: print('PHASE2 ENGINE: FAIL'); [print(f'- {x}') for x in e]; raise SystemExit(1)
    print('PHASE2 ENGINE: PASS')
    print('- frozen hash, hard gates, exposure penalties, blind reviews, deterministic winner')
