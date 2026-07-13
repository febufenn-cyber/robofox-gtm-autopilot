"""Strict contracts and canonical hashing for Phase 2."""
from __future__ import annotations
import hashlib, json, math
from datetime import datetime
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_KEYS={"version","candidate_id","product","snapshot_hash","title","strategic_goal","mechanism","assumptions","evidence_record_ids","expected_upside","success_signal","kill_criteria","conversion_plan","scores","exposure","trust_risk","created_by_role","created_at"}
REVIEW_KEYS={"version","review_id","candidate_id","snapshot_hash","reviewer_role","blind_review","saw_other_critiques","strongest_refutation","failure_modes","disconfirming_evidence","threat_level","prophylaxis","residual_risk","reviewed_at"}
REQUEST_KEYS={"version","decision_id","product","snapshot_hash","decision_question","constraints","candidate_ids","review_ids","requested_at"}
SCORE_KEYS={"constraint_alignment","learning_value","reversibility","execution_feasibility","conversion_readiness"}
EXPOSURE_KEYS={"cash_usd","founder_hours","days_to_signal"}
STATUSES={"VERIFIED","OBSERVED","INFERRED","ASSUMED","STALE","CONFLICTED","UNKNOWN"}
class DecisionError(ValueError): pass

def canonical_json(value: object)->str:
    try: return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
    except (TypeError,ValueError) as exc: raise DecisionError(f"value is not canonical JSON: {exc}") from exc

def canonical_hash(value: object)->str: return "sha256:"+hashlib.sha256(canonical_json(value).encode()).hexdigest()

def date(value:Any,field:str)->datetime:
    if not isinstance(value,str) or not value: raise DecisionError(f"{field} must be a timezone-aware date-time")
    normalized=value[:-1]+"+00:00" if value.endswith("Z") else value
    try: result=datetime.fromisoformat(normalized)
    except ValueError as exc: raise DecisionError(f"{field} is not valid ISO-8601") from exc
    if result.tzinfo is None or result.utcoffset() is None: raise DecisionError(f"{field} must include a timezone")
    return result

def exact(record:dict[str,Any],keys:set[str],label:str)->None:
    if not isinstance(record,dict): raise DecisionError(f"{label} must be an object")
    missing,unknown=keys-set(record),set(record)-keys
    if missing or unknown: raise DecisionError(f"invalid {label} fields; missing={sorted(missing)} unknown={sorted(unknown)}")

def string(value:Any,field:str)->str:
    if not isinstance(value,str) or not value.strip(): raise DecisionError(f"{field} must be a non-empty string")
    return value

def strings(value:Any,field:str,minimum:int=0)->list[str]:
    if not isinstance(value,list) or len(value)<minimum or any(not isinstance(x,str) or not x.strip() for x in value): raise DecisionError(f"{field} must be a string list with at least {minimum} items")
    if len(value)!=len(set(value)): raise DecisionError(f"{field} contains duplicates")
    return list(value)

def bounded(value:Any,field:str,low:int=1,high:int=5)->int:
    if not isinstance(value,int) or isinstance(value,bool) or not low<=value<=high: raise DecisionError(f"{field} must be an integer from {low} to {high}")
    return value

def finite(value:Any,field:str,minimum:float=0.0,strict:bool=False)->float:
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(float(value)): raise DecisionError(f"{field} must be a finite number")
    n=float(value)
    if n<minimum or (strict and n<=minimum): raise DecisionError(f"{field} is below its minimum")
    return n

def load_weights(path:Path|None=None)->dict[str,Any]:
    source=path or ROOT/'config/decision-weights.json'
    try: weights=json.loads(source.read_text())
    except (OSError,json.JSONDecodeError) as exc: raise DecisionError(f"cannot load decision weights: {exc}") from exc
    if weights.get('version')!=1: raise DecisionError('unsupported decision weights version')
    if abs(sum(weights.get('positive_weights',{}).values())-1)>1e-9: raise DecisionError('positive decision weights must sum to one')
    return weights

def validate_snapshot(s:dict[str,Any])->None:
    required={"version","product","as_of","generated_at","dimensions","conflicts","stale_claim_ids","open_assumption_ids","overdue_assumption_ids","unknown_dimensions","restricted_records_excluded","prohibited_claims_excluded","input_record_ids"}
    missing=required-set(s)
    if missing: raise DecisionError(f"position snapshot missing fields: {sorted(missing)}")
    if s.get('version')!=1: raise DecisionError('unsupported position snapshot version')
    string(s.get('product'),'snapshot.product'); date(s.get('as_of'),'snapshot.as_of'); date(s.get('generated_at'),'snapshot.generated_at')
    if not isinstance(s.get('dimensions'),dict): raise DecisionError('snapshot.dimensions must be an object')
    for key,item in s['dimensions'].items():
        if not isinstance(item,dict) or item.get('status') not in STATUSES: raise DecisionError(f"invalid position dimension: {key}")
    if not isinstance(s.get('conflicts'),list): raise DecisionError('snapshot.conflicts must be a list')
    strings(s.get('input_record_ids'),'snapshot.input_record_ids')

def validate_candidate(c:dict[str,Any])->None:
    exact(c,CANDIDATE_KEYS,'candidate')
    if c['version']!=1: raise DecisionError('unsupported candidate version')
    for f in ('candidate_id','product','snapshot_hash','title','strategic_goal','mechanism','expected_upside','success_signal','conversion_plan'): string(c[f],f'candidate.{f}')
    strings(c['assumptions'],'candidate.assumptions'); strings(c['evidence_record_ids'],'candidate.evidence_record_ids'); strings(c['kill_criteria'],'candidate.kill_criteria',1)
    if c['created_by_role']!='PLANNER': raise DecisionError('candidate.created_by_role must be PLANNER')
    date(c['created_at'],'candidate.created_at'); exact(c['scores'],SCORE_KEYS,'candidate.scores')
    for k,v in c['scores'].items(): bounded(v,f'candidate.scores.{k}')
    exact(c['exposure'],EXPOSURE_KEYS,'candidate.exposure'); finite(c['exposure']['cash_usd'],'candidate.exposure.cash_usd'); finite(c['exposure']['founder_hours'],'candidate.exposure.founder_hours'); bounded(c['exposure']['days_to_signal'],'candidate.exposure.days_to_signal',1,3650); bounded(c['trust_risk'],'candidate.trust_risk')

def validate_review(r:dict[str,Any])->None:
    exact(r,REVIEW_KEYS,'review')
    if r['version']!=1: raise DecisionError('unsupported review version')
    for f in ('review_id','candidate_id','snapshot_hash','strongest_refutation'): string(r[f],f'review.{f}')
    if r['reviewer_role']!='CRITIC' or r['blind_review'] is not True or r['saw_other_critiques'] is not False: raise DecisionError('review independence contract is invalid')
    strings(r['failure_modes'],'review.failure_modes',1); strings(r['disconfirming_evidence'],'review.disconfirming_evidence',1); bounded(r['threat_level'],'review.threat_level'); bounded(r['residual_risk'],'review.residual_risk')
    if not isinstance(r['prophylaxis'],list): raise DecisionError('review.prophylaxis must be a list')
    for i,item in enumerate(r['prophylaxis']):
        exact(item,{"threat","mitigation","verification"},f'review.prophylaxis[{i}]')
        for f in item: string(item[f],f'review.prophylaxis[{i}].{f}')
    date(r['reviewed_at'],'review.reviewed_at')

def validate_request(q:dict[str,Any],weights:dict[str,Any])->None:
    exact(q,REQUEST_KEYS,'decision request')
    if q['version']!=1: raise DecisionError('unsupported decision request version')
    for f in ('decision_id','product','snapshot_hash','decision_question'): string(q[f],f'request.{f}')
    date(q['requested_at'],'request.requested_at'); candidates=strings(q['candidate_ids'],'request.candidate_ids'); reviews=strings(q['review_ids'],'request.review_ids')
    bounds=weights['candidate_count']
    if not bounds['minimum']<=len(candidates)<=bounds['maximum']: raise DecisionError('decision requires two to five candidates')
    if len(reviews)!=len(candidates): raise DecisionError('decision requires one review per candidate')
    exact(q['constraints'],{"max_cash_usd","max_founder_hours","max_days_to_signal"},'request.constraints')
    finite(q['constraints']['max_cash_usd'],'request.constraints.max_cash_usd'); finite(q['constraints']['max_founder_hours'],'request.constraints.max_founder_hours',strict=True); bounded(q['constraints']['max_days_to_signal'],'request.constraints.max_days_to_signal',1,3650)
