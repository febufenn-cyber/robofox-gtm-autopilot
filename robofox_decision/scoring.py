"""Eligibility gates and deterministic ordinal scoring."""
from __future__ import annotations
from typing import Any

def global_gate(snapshot:dict[str,Any],weights:dict[str,Any])->tuple[str|None,list[str]]:
    dims=snapshot['dimensions']
    conflicts=[k for k in weights['hard_block_conflicted_dimensions'] if dims.get(k,{}).get('status')=='CONFLICTED']
    unknown=[k for k in weights['hard_block_unknown_dimensions'] if dims.get(k,{}).get('status')=='UNKNOWN']
    if conflicts: return 'BLOCKED_CONFLICT',[f'blocking conflicted dimension: {k}' for k in conflicts]
    if unknown: return 'NEEDS_EVIDENCE',[f'blocking unknown dimension: {k}' for k in unknown]
    return None,[]

def evaluate(candidate,review,request,snapshot,weights,global_blockers):
    blockers=list(global_blockers)
    if candidate['product']!=request['product'] or candidate['product']!=snapshot['product']: blockers.append('product mismatch')
    if candidate['snapshot_hash']!=request['snapshot_hash'] or review['snapshot_hash']!=request['snapshot_hash']: blockers.append('snapshot hash mismatch')
    if review['candidate_id']!=candidate['candidate_id']: blockers.append('review candidate mismatch')
    limits=request['constraints']; exposure=candidate['exposure']
    if exposure['cash_usd']>limits['max_cash_usd']: blockers.append('cash exposure exceeds limit')
    if exposure['founder_hours']>limits['max_founder_hours']: blockers.append('founder-hour exposure exceeds limit')
    if exposure['days_to_signal']>limits['max_days_to_signal']: blockers.append('time-to-signal exceeds limit')
    if max(review['threat_level'],review['residual_risk'])>=weights['prophylaxis_required_at'] and not review['prophylaxis']: blockers.append('material threat lacks prophylaxis')
    references=candidate['evidence_record_ids']; missing=sorted(set(references)-set(snapshot['input_record_ids'])); strength=1 if not references else min(5,len(references)+1)
    if missing: blockers.append('unavailable evidence references: '+', '.join(missing))
    inputs={**candidate['scores'],'evidence_strength':strength}
    positive=sum(inputs[k]*w for k,w in weights['positive_weights'].items())
    cash_ratio=0.0 if limits['max_cash_usd']==0 and exposure['cash_usd']==0 else (1.0 if limits['max_cash_usd']==0 else min(1.0,exposure['cash_usd']/limits['max_cash_usd']))
    penalties={'trust_risk':candidate['trust_risk'],'residual_risk':review['residual_risk'],'cash_exposure':cash_ratio*5,'founder_time_exposure':min(1.0,exposure['founder_hours']/limits['max_founder_hours'])*5,'signal_time_exposure':min(1.0,exposure['days_to_signal']/limits['max_days_to_signal'])*5}
    penalty=sum(penalties[k]*w for k,w in weights['penalty_weights'].items()); p=weights['score_precision']
    return {'candidate_id':candidate['candidate_id'],'eligible':not blockers,'blockers':sorted(set(blockers)),'positive_score':round(positive,p),'penalty_score':round(penalty,p),'final_score':round(max(0.0,positive-penalty),p),'rank':None,'evidence_strength':strength,'residual_risk':review['residual_risk'],'trust_risk':candidate['trust_risk'],'exposure':dict(exposure)}

def rank(results):
    eligible=[x for x in results if x['eligible']]
    eligible.sort(key=lambda x:(-x['final_score'],x['residual_risk'],x['trust_risk'],x['exposure']['cash_usd'],x['exposure']['founder_hours'],x['exposure']['days_to_signal'],x['candidate_id']))
    ranks={x['candidate_id']:i for i,x in enumerate(eligible,1)}
    for x in results: x['rank']=ranks.get(x['candidate_id'])
    return sorted(results,key=lambda x:(x['rank'] is None,x['rank'] or 999,x['candidate_id']))
