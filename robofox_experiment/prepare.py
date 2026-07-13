"""Bind a Phase 3 definition to a chosen Phase 2 decision and candidate."""
from __future__ import annotations
from typing import Any
from robofox_decision import canonical_hash
from robofox_truth.validation import TruthStoreError
from .validation import validate_definition

def bind_definition(decision:dict[str,Any], candidate:dict[str,Any], spec:dict[str,Any])->dict[str,Any]:
    if decision.get('status')!='CHOSEN' or decision.get('chosen_candidate_id')!=candidate.get('candidate_id'):
        raise TruthStoreError('experiment requires the candidate chosen by the Phase 2 decision')
    candidate_hash=canonical_hash(candidate); expected=decision.get('input_hashes',{}).get('candidates',{}).get(candidate.get('candidate_id'))
    if candidate_hash!=expected: raise TruthStoreError('candidate does not match the hash recorded by the decision')
    if decision.get('product')!=candidate.get('product') or spec.get('product')!=decision.get('product'): raise TruthStoreError('product differs across decision, candidate, and experiment spec')
    if decision.get('snapshot_hash')!=candidate.get('snapshot_hash'): raise TruthStoreError('snapshot hash differs across decision and candidate')
    requested=spec.get('maximum_exposure',{}); allowed=decision.get('maximum_exposure',{})
    for key in ('cash_usd','founder_hours','days_to_signal'):
        if requested.get(key,0)>allowed.get(key,0): raise TruthStoreError(f'experiment {key} exceeds selected move exposure')
    raw={**spec,'version':1,'decision_id':decision['decision_id'],'decision_record_hash':canonical_hash(decision),'candidate_id':candidate['candidate_id'],'candidate_hash':candidate_hash,'snapshot_hash':decision['snapshot_hash'],'decision_status':'CHOSEN'}
    return validate_definition(raw)
