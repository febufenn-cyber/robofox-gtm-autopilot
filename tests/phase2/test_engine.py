import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))
from robofox_decision import DecisionError,arbitrate,canonical_hash,write_decision
from verify_phase2_engine import fixtures
class EngineTests(unittest.TestCase):
    def decide(self,s=None,q=None,c=None,r=None,a=None):
        base=fixtures(); return arbitrate(s or base[0],q or base[1],c or base[2],r or base[3],a or base[4],created_at='2026-07-13T10:06:00+05:30')
    def test_deterministic_winner(self): self.assertEqual('MOV-SYNTH-001',self.decide()['chosen_candidate_id'])
    def test_replay_is_identical(self): self.assertEqual(self.decide(),self.decide())
    def test_snapshot_hash_mismatch_fails(self):
        s,q,c,r,a=fixtures(); q['snapshot_hash']='sha256:'+'0'*64
        with self.assertRaisesRegex(DecisionError,'canonical snapshot'): arbitrate(s,q,c,r,a)
    def test_missing_review_fails(self):
        s,q,c,r,a=fixtures(); q['review_ids']=q['review_ids'][:1]
        with self.assertRaisesRegex(DecisionError,'review and assessment'): arbitrate(s,q,c,r,a)
    def test_missing_assessment_fails(self):
        s,q,c,r,a=fixtures(); q['assessment_ids']=q['assessment_ids'][:1]
        with self.assertRaisesRegex(DecisionError,'review and assessment'): arbitrate(s,q,c,r,a)
    def test_duplicate_candidate_fails(self):
        s,q,c,r,a=fixtures(); c[1]['candidate_id']=c[0]['candidate_id']; q['candidate_ids']=[c[0]['candidate_id'],'MOV-OTHER-001']
        with self.assertRaisesRegex(DecisionError,'duplicated|do not match'): arbitrate(s,q,c,r,a)
    def test_identical_mechanisms_fail(self):
        s,q,c,r,a=fixtures(); c[1]['mechanism']=c[0]['mechanism']
        with self.assertRaisesRegex(DecisionError,'materially distinct'): arbitrate(s,q,c,r,a)
    def test_planner_cannot_supply_scores(self):
        s,q,c,r,a=fixtures(); c[0]['scores']=a[0]['scores']
        with self.assertRaisesRegex(DecisionError,'unknown=.*scores'): arbitrate(s,q,c,r,a)
    def test_assessor_role_is_required(self):
        s,q,c,r,a=fixtures(); a[0]['assessor_role']='PLANNER'
        with self.assertRaisesRegex(DecisionError,'assessment independence'): arbitrate(s,q,c,r,a)
    def test_timestamp_order_is_enforced(self):
        s,q,c,r,a=fixtures(); a[0]['assessed_at']='2026-07-13T10:03:30+05:30'
        with self.assertRaisesRegex(DecisionError,'planner → critic → arbiter'): arbitrate(s,q,c,r,a)
    def test_cash_limit_makes_candidate_ineligible(self):
        s,q,c,r,a=fixtures(); c[0]['exposure']['cash_usd']=101
        first=next(x for x in arbitrate(s,q,c,r,a)['candidate_results'] if x['candidate_id']=='MOV-SYNTH-001'); self.assertIn('cash exposure exceeds limit',first['blockers'])
    def test_material_threat_requires_prophylaxis(self):
        s,q,c,r,a=fixtures(); r[0]['prophylaxis']=[]
        first=next(x for x in arbitrate(s,q,c,r,a)['candidate_results'] if x['candidate_id']=='MOV-SYNTH-001'); self.assertIn('material threat lacks prophylaxis',first['blockers'])
    def test_unavailable_evidence_blocks_candidate(self):
        s,q,c,r,a=fixtures(); c[0]['evidence_record_ids']=['CLM-NOT-IN-SNAPSHOT']
        first=next(x for x in arbitrate(s,q,c,r,a)['candidate_results'] if x['candidate_id']=='MOV-SYNTH-001'); self.assertTrue(any('unavailable evidence' in x for x in first['blockers']))
    def test_current_constraint_conflict_blocks_all(self):
        s,q,c,r,a=fixtures(); s['dimensions']['current_constraint']={'label':'Current constraint','status':'CONFLICTED','claim_ids':['CLM-A','CLM-B'],'value_withheld':True}; q['snapshot_hash']=canonical_hash(s); [x.update(snapshot_hash=q['snapshot_hash']) for x in c+r+a]
        out=arbitrate(s,q,c,r,a); self.assertEqual('BLOCKED_CONFLICT',out['status']); self.assertIsNone(out['chosen_candidate_id'])
    def test_unknown_current_constraint_needs_evidence(self):
        s,q,c,r,a=fixtures(); s['dimensions']['current_constraint']={'label':'Current constraint','status':'UNKNOWN','claim_ids':[]}; s['unknown_dimensions']=['current_constraint']; q['snapshot_hash']=canonical_hash(s); [x.update(snapshot_hash=q['snapshot_hash']) for x in c+r+a]
        self.assertEqual('NEEDS_EVIDENCE',arbitrate(s,q,c,r,a)['status'])
    def test_all_ineligible_returns_no_move(self):
        s,q,c,r,a=fixtures(); [x['exposure'].update(cash_usd=1000) for x in c]
        self.assertEqual('NO_MOVE',arbitrate(s,q,c,r,a)['status'])
    def test_tie_break_prefers_lower_risk(self):
        s,q,c,r,a=fixtures(); a[1]['scores']=copy.deepcopy(a[0]['scores']); c[1]['exposure']=copy.deepcopy(c[0]['exposure']); r[1]['residual_risk']=1
        self.assertEqual('MOV-SYNTH-002',arbitrate(s,q,c,r,a)['chosen_candidate_id'])
    def test_final_tie_break_is_candidate_id(self):
        s,q,c,r,a=fixtures(); a[1]['scores']=copy.deepcopy(a[0]['scores']); c[1]['exposure']=copy.deepcopy(c[0]['exposure']); c[1]['trust_risk']=c[0]['trust_risk']; r[1]['residual_risk']=r[0]['residual_risk']
        self.assertEqual('MOV-SYNTH-001',arbitrate(s,q,c,r,a)['chosen_candidate_id'])
    def test_non_finite_exposure_rejected(self):
        s,q,c,r,a=fixtures(); c[0]['exposure']['cash_usd']=float('nan')
        with self.assertRaisesRegex(DecisionError,'finite'): arbitrate(s,q,c,r,a)
    def test_weight_tampering_rejected(self):
        s,q,c,r,a=fixtures()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'weights.json'; weights=json.loads((ROOT/'config/decision-weights.json').read_text()); weights['positive_weights']['constraint_alignment']=-1; p.write_text(json.dumps(weights))
            with self.assertRaises(DecisionError): arbitrate(s,q,c,r,a,weights_path=p)
    def test_write_outside_engine(self):
        with tempfile.TemporaryDirectory() as d:
            paths=write_decision(self.decide(),Path(d)); self.assertTrue(paths[0].is_file()); self.assertTrue(paths[1].is_file())
    def test_input_hashes_include_assessments(self): self.assertIn('assessments',self.decide()['input_hashes'])
if __name__=='__main__': unittest.main()
