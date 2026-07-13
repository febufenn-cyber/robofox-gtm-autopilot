import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_phase2_contracts import verify
class ContractTests(unittest.TestCase):
    def test_contracts_pass(self): self.assertEqual([],verify(ROOT))
    def test_positive_weights_sum_to_one(self):
        w=json.loads((ROOT/'config/decision-weights.json').read_text())
        self.assertAlmostEqual(1.0,sum(w['positive_weights'].values()))
    def test_two_to_five_candidates(self):
        s=json.loads((ROOT/'schemas/decision-request.schema.json').read_text())
        p=s['properties']['candidate_ids']; self.assertEqual((2,5),(p['minItems'],p['maxItems']))
    def test_blind_critic_is_contractual(self):
        s=json.loads((ROOT/'schemas/adversarial-review.schema.json').read_text())
        self.assertTrue(s['properties']['blind_review']['const'])
        self.assertFalse(s['properties']['saw_other_critiques']['const'])
    def test_no_move_statuses_exist(self):
        s=json.loads((ROOT/'schemas/decision-record.schema.json').read_text())
        values=set(s['properties']['status']['enum'])
        self.assertTrue({'NO_MOVE','NEEDS_EVIDENCE','BLOCKED_CONFLICT'} <= values)
    def test_final_tie_break_is_identifier(self):
        w=json.loads((ROOT/'config/decision-weights.json').read_text())
        self.assertEqual('candidate_id',w['tie_break_order'][-1])
if __name__=='__main__': unittest.main()
