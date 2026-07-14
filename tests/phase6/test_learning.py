import sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from robofox_learning import *
class T(unittest.TestCase):
 def test_calibration(self):
  p=[{'id':'p1','predicted_probability':.9},{'id':'p2','predicted_probability':.8}];o=[{'prediction_id':'p1','actual':True},{'prediction_id':'p2','actual':False}];r=calibration(p,o);self.assertEqual(2,r['count']);self.assertGreater(r['brier_score'],0)
 def test_empty_calibration(self):self.assertIsNone(calibration([],[])['brier_score'])
 def test_correlated_families_discounted(self):self.assertLess(belief_update(.5,'SUPPORT',1,['s'],['same','same'])['effective_strength'],1)
 def test_refuting_evidence_lowers_belief(self):self.assertLess(belief_update(.7,'REFUTE',1,['s'],['a','b','c'])['posterior'],.7)
 def test_material_update_triggers_phase2(self):self.assertTrue(belief_update(.5,'SUPPORT',1,['s'],['a','b','c'])['trigger_phase2'])
 def test_small_sample_no_override(self):self.assertFalse(benchmark_override({'source_type':'FIRST_PARTY','sample_size':10,'relevance':1,'product_match':True,'segment_match':True,'offer_version_match':True,'metric':'x','value':1})['eligible'])
 def test_context_mismatch_no_override(self):self.assertFalse(benchmark_override({'source_type':'FIRST_PARTY','sample_size':30,'relevance':1,'product_match':True,'segment_match':False,'offer_version_match':True,'metric':'x','value':1})['eligible'])
 def test_valid_override(self):self.assertTrue(benchmark_override({'source_type':'FIRST_PARTY','sample_size':30,'relevance':.8,'product_match':True,'segment_match':True,'offer_version_match':True,'metric':'x','value':1})['eligible'])
 def score(self,x=1):return {k:x for k in WEIGHTS}
 def test_score_complete(self):self.assertEqual(1,channel_score(self.score()))
 def test_missing_score_field(self):
  r=self.score();r.pop('trust_safety')
  with self.assertRaises(LearningError):channel_score(r)
 def test_concentration_cap(self):self.assertLessEqual(max(allocate({'a':10,'b':1,'c':1}).values()),50)
 def test_allocation_sums(self):self.assertAlmostEqual(100,sum(allocate({'a':1,'b':1,'c':1}).values()),5)
 def test_sensitivity_reports(self):self.assertIn('robust',sensitivity({'a':self.score(.8),'b':self.score(.7)}))
 def test_append_only_and_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   c=sqlite3.connect(Path(d)/'x');install(c);r={'id':'PRD-TEST-0001','x':1};append(c,'predictions',r)
   with self.assertRaisesRegex(sqlite3.IntegrityError,'append-only'):c.execute("UPDATE predictions SET record_json='{}'")
if __name__=='__main__':unittest.main()
