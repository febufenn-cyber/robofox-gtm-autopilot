"""Deterministic arbitration over a frozen Phase 1 position snapshot."""
from __future__ import annotations
import re
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .scoring import evaluate,global_gate,rank
from .validation import DecisionError,canonical_hash,date,load_weights,validate_assessment,validate_candidate,validate_request,validate_review,validate_snapshot

def _fingerprint(text:str)->str: return ' '.join(re.findall(r'[a-z0-9]+',text.lower()))

def arbitrate(snapshot:dict[str,Any],request:dict[str,Any],candidates:list[dict[str,Any]],reviews:list[dict[str,Any]],assessments:list[dict[str,Any]],*,weights_path:Path|None=None,created_at:str|None=None)->dict[str,Any]:
    weights=load_weights(weights_path); validate_snapshot(snapshot); validate_request(request,weights)
    for x in candidates: validate_candidate(x)
    for x in reviews: validate_review(x)
    for x in assessments: validate_assessment(x)
    snapshot_hash=canonical_hash(snapshot)
    if request['snapshot_hash']!=snapshot_hash: raise DecisionError('request snapshot_hash does not match canonical snapshot')
    if request['product']!=snapshot['product']: raise DecisionError('request product does not match snapshot')
    c_map={x['candidate_id']:x for x in candidates}; r_map={x['review_id']:x for x in reviews}; a_map={x['assessment_id']:x for x in assessments}
    if len(c_map)!=len(candidates) or len(r_map)!=len(reviews) or len(a_map)!=len(assessments): raise DecisionError('candidate, review, or assessment identifiers are duplicated')
    if set(c_map)!=set(request['candidate_ids']): raise DecisionError('request candidate_ids do not match candidate files')
    if set(r_map)!=set(request['review_ids']): raise DecisionError('request review_ids do not match review files')
    if set(a_map)!=set(request['assessment_ids']): raise DecisionError('request assessment_ids do not match assessment files')
    mechanisms=[_fingerprint(x['mechanism']) for x in candidates]; titles=[_fingerprint(x['title']) for x in candidates]
    if len(set(mechanisms))!=len(mechanisms) or len(set(titles))!=len(titles): raise DecisionError('candidate moves must be materially distinct')
    by_review={x:[] for x in c_map}; by_assessment={x:[] for x in c_map}
    for review in reviews:
        if review['candidate_id'] not in by_review: raise DecisionError('review references an unknown candidate')
        by_review[review['candidate_id']].append(review)
    for assessment in assessments:
        if assessment['candidate_id'] not in by_assessment: raise DecisionError('assessment references an unknown candidate')
        by_assessment[assessment['candidate_id']].append(assessment)
    if any(len(x)!=1 for x in by_review.values()): raise DecisionError('each candidate requires exactly one review')
    if any(len(x)!=1 for x in by_assessment.values()): raise DecisionError('each candidate requires exactly one assessment')
    request_time=date(request['requested_at'],'request.requested_at')
    for candidate_id,candidate in c_map.items():
        review=by_review[candidate_id][0]; assessment=by_assessment[candidate_id][0]
        candidate_time=date(candidate['created_at'],'candidate.created_at'); review_time=date(review['reviewed_at'],'review.reviewed_at'); assessment_time=date(assessment['assessed_at'],'assessment.assessed_at')
        if not request_time<=candidate_time<=review_time<=assessment_time: raise DecisionError('role timestamps violate planner → critic → arbiter order')
    now=created_at or datetime.now(timezone.utc).isoformat().replace('+00:00','Z'); decision_time=date(now,'created_at')
    if any(date(x['assessed_at'],'assessment.assessed_at')>decision_time for x in assessments): raise DecisionError('decision predates an assessment')
    global_status,global_blockers=global_gate(snapshot,weights)
    results=rank([evaluate(c_map[i],by_review[i][0],by_assessment[i][0],request,snapshot,weights,global_blockers) for i in request['candidate_ids']]); eligible=[x for x in results if x['eligible']]
    status,chosen=(global_status,None) if global_status else (('NO_MOVE',None) if not eligible else ('CHOSEN',eligible[0]['candidate_id']))
    rejected=[]
    for result in results:
        if result['candidate_id']==chosen: continue
        reason='; '.join(result['blockers']) if result['blockers'] else f'lower deterministic rank than {chosen}'
        rejected.append({'candidate_id':result['candidate_id'],'reason':reason})
    changes=[]
    for review in reviews: changes.extend(review['disconfirming_evidence'])
    changes.extend(global_blockers); changes=list(dict.fromkeys(changes or ['A material change to the frozen position snapshot']))
    assumptions=list(dict.fromkeys([a for c in candidates for a in c['assumptions']]+list(snapshot.get('open_assumption_ids',[]))))
    current=snapshot['dimensions'].get('current_constraint',{}); current_value=current.get('value') if current.get('status') not in {'UNKNOWN','CONFLICTED'} else None
    unresolved=[x for x in snapshot['conflicts'] if x.get('blocks_dimension')]
    if chosen:
        winner=next(x for x in results if x['candidate_id']==chosen); confidence='HIGH' if winner['evidence_strength']>=4 and current.get('status') in {'VERIFIED','OBSERVED'} and not snapshot['unknown_dimensions'] else 'MEDIUM'; exposure=dict(c_map[chosen]['exposure']); rationale=f"{chosen} is the highest-ranked eligible move after hard gates, blind critique, independent assessment, exposure penalties, and deterministic tie-breaking."
    else:
        confidence='LOW'; exposure={'cash_usd':0.0,'founder_hours':0.0,'days_to_signal':0}; rationale={'BLOCKED_CONFLICT':'No move selected because the frozen board contains a configured blocking conflict.','NEEDS_EVIDENCE':'No move selected because the current constraint is unknown.','NO_MOVE':'No move selected because every candidate failed at least one hard eligibility gate.'}[status]
    public=[{k:v for k,v in x.items() if k in {'candidate_id','eligible','blockers','positive_score','penalty_score','final_score','rank'}} for x in results]
    return {'version':1,'decision_id':request['decision_id'],'product':request['product'],'snapshot_hash':snapshot_hash,'status':status,'chosen_candidate_id':chosen,'current_constraint':current_value,'candidate_results':public,'rejected_alternatives':rejected,'unresolved_conflicts':unresolved,'unknown_dimensions':list(snapshot['unknown_dimensions']),'assumptions':assumptions,'maximum_exposure':exposure,'rationale':rationale,'confidence':confidence,'evidence_that_changes_decision':changes,'score_method':{'version':weights['version'],'ordinal_not_probability':True,'independent_assessor':True,'positive_weights':weights['positive_weights'],'penalty_weights':weights['penalty_weights'],'tie_break_order':weights['tie_break_order']},'input_hashes':{'request':canonical_hash(request),'candidates':{x['candidate_id']:canonical_hash(x) for x in candidates},'reviews':{x['review_id']:canonical_hash(x) for x in reviews},'assessments':{x['assessment_id']:canonical_hash(x) for x in assessments},'weights':canonical_hash(weights)},'created_at':now}

def verify_decision_record(snapshot,request,candidates,reviews,assessments,record,*,weights_path=None):
    if not isinstance(record,dict) or 'created_at' not in record: raise DecisionError('decision record is missing created_at')
    expected=arbitrate(snapshot,request,candidates,reviews,assessments,weights_path=weights_path,created_at=record['created_at'])
    if canonical_hash(expected)!=canonical_hash(record): raise DecisionError('decision record does not replay from its frozen inputs')
    return True
