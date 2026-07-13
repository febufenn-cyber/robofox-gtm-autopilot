"""Deterministic arbitration over a frozen Phase 1 position snapshot."""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .scoring import evaluate,global_gate,rank
from .validation import DecisionError,canonical_hash,date,load_weights,validate_candidate,validate_request,validate_review,validate_snapshot

def arbitrate(snapshot:dict[str,Any],request:dict[str,Any],candidates:list[dict[str,Any]],reviews:list[dict[str,Any]],*,weights_path:Path|None=None,created_at:str|None=None)->dict[str,Any]:
    weights=load_weights(weights_path); validate_snapshot(snapshot); validate_request(request,weights)
    for x in candidates: validate_candidate(x)
    for x in reviews: validate_review(x)
    snapshot_hash=canonical_hash(snapshot)
    if request['snapshot_hash']!=snapshot_hash: raise DecisionError('request snapshot_hash does not match canonical snapshot')
    if request['product']!=snapshot['product']: raise DecisionError('request product does not match snapshot')
    c_map={x['candidate_id']:x for x in candidates}; r_map={x['review_id']:x for x in reviews}
    if len(c_map)!=len(candidates) or len(r_map)!=len(reviews): raise DecisionError('candidate or review identifiers are duplicated')
    if set(c_map)!=set(request['candidate_ids']): raise DecisionError('request candidate_ids do not match candidate files')
    if set(r_map)!=set(request['review_ids']): raise DecisionError('request review_ids do not match review files')
    by_candidate={x:[] for x in c_map}
    for review in reviews:
        if review['candidate_id'] not in by_candidate: raise DecisionError('review references an unknown candidate')
        by_candidate[review['candidate_id']].append(review)
    if any(len(x)!=1 for x in by_candidate.values()): raise DecisionError('each candidate requires exactly one review')
    global_status,global_blockers=global_gate(snapshot,weights)
    results=rank([evaluate(c_map[i],by_candidate[i][0],request,snapshot,weights,global_blockers) for i in request['candidate_ids']]); eligible=[x for x in results if x['eligible']]
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
        winner=next(x for x in results if x['candidate_id']==chosen); confidence='HIGH' if winner['evidence_strength']>=4 and current.get('status') in {'VERIFIED','OBSERVED'} and not snapshot['unknown_dimensions'] else 'MEDIUM'; exposure=dict(c_map[chosen]['exposure']); rationale=f"{chosen} is the highest-ranked eligible move after hard gates, adversarial review, exposure penalties, and deterministic tie-breaking."
    else:
        confidence='LOW'; exposure={'cash_usd':0.0,'founder_hours':0.0,'days_to_signal':0}; rationale={'BLOCKED_CONFLICT':'No move selected because the frozen board contains a configured blocking conflict.','NEEDS_EVIDENCE':'No move selected because the current constraint is unknown.','NO_MOVE':'No move selected because every candidate failed at least one hard eligibility gate.'}[status]
    now=created_at or datetime.now(timezone.utc).isoformat().replace('+00:00','Z'); date(now,'created_at')
    public=[{k:v for k,v in x.items() if k in {'candidate_id','eligible','blockers','positive_score','penalty_score','final_score','rank'}} for x in results]
    return {'version':1,'decision_id':request['decision_id'],'product':request['product'],'snapshot_hash':snapshot_hash,'status':status,'chosen_candidate_id':chosen,'current_constraint':current_value,'candidate_results':public,'rejected_alternatives':rejected,'unresolved_conflicts':unresolved,'unknown_dimensions':list(snapshot['unknown_dimensions']),'assumptions':assumptions,'maximum_exposure':exposure,'rationale':rationale,'confidence':confidence,'evidence_that_changes_decision':changes,'score_method':{'version':weights['version'],'ordinal_not_probability':True,'positive_weights':weights['positive_weights'],'penalty_weights':weights['penalty_weights'],'tie_break_order':weights['tie_break_order']},'input_hashes':{'request':canonical_hash(request),'candidates':{x['candidate_id']:canonical_hash(x) for x in candidates},'reviews':{x['review_id']:canonical_hash(x) for x in reviews},'weights':canonical_hash(weights)},'created_at':now}
