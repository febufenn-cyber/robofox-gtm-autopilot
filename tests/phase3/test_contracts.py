from __future__ import annotations
import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_phase3_contracts import verify as verify_contracts
from verify_phase3_skills import verify as verify_skills
class Phase3ContractTests(unittest.TestCase):
    def test_contract_verifier_passes(self): self.assertEqual([],verify_contracts(ROOT))
    def test_skill_verifier_passes(self): self.assertEqual([],verify_skills(ROOT))
    def test_every_mutation_requires_exact_approval(self):
        actions=json.loads((ROOT/'policies/action-registry.yaml').read_text())['actions']
        for name in ('register_experiment_definition','record_experiment_transition','record_experiment_execution','record_experiment_observation','finalize_experiment'):
            self.assertEqual('exact',actions[name]['approval'])
    def test_agent_cannot_approve_experiment(self):
        action=json.loads((ROOT/'policies/action-registry.yaml').read_text())['actions']['approve_experiment_action']
        self.assertFalse(action['enabled']); self.assertEqual('forbidden',action['approval'])
    def test_selected_move_execution_is_forbidden(self):
        action=json.loads((ROOT/'policies/action-registry.yaml').read_text())['actions']['execute_selected_move']
        self.assertFalse(action['enabled']); self.assertEqual('forbidden',action['approval'])
    def test_migration_uses_append_only_triggers(self):
        text=(ROOT/'robofox_experiment/migrations/001_experiment_operating_system.sql').read_text()
        self.assertEqual(5,text.count('CREATE TABLE IF NOT EXISTS'))
        self.assertEqual(5,text.count('_no_update'))
        self.assertEqual(5,text.count('_no_delete'))
if __name__=='__main__': unittest.main()
