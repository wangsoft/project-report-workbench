"""Automatic promotion must earn independent multi-period acceptance."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from onboard_project import create_project
from auto_tune import tune

class TuneTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  questions=[dict(id=k,kind=k,metric='revenue',title=t) for k,t in [('change','收入如何变化？'),('drivers','增长来自哪里？'),('exceptions','谁逆势下降？')]]
  self.spec=dict(schema_version=1,project_id='retail',title='零售经营分析',audience='经营负责人',scope='descriptive_periodic',period_column='month',entity_column='region',periods=['01','02','03','04'],entities=['A','B'],metrics=[dict(id='revenue',column='sales',label='收入',unit='元',aggregation='sum',direction='higher')],questions=questions[:1])
  self.project=create_project(self.spec,self.root/'projects')
  cases=[]
  for i,(role,period,previous,current) in enumerate([('development','02',200,230),('regression','03',230,240),('holdout','04',240,220)]):
   data=self.root/f'{period}.csv';prior=str(int(period)-1).zfill(2)
   vals=[(100,100,150,80),(150,80,160,80),(160,80,150,70)][i]
   data.write_text(f'month,region,sales\n{prior},A,{vals[0]}\n{prior},B,{vals[1]}\n{period},A,{vals[2]}\n{period},B,{vals[3]}\n')
   cases.append(dict(id=role,role=role,period=period,data=data.name,expected={'revenue':dict(current=current,previous=previous,delta=current-previous,growth_pct=(current-previous)/previous*100)}))
  self.policy=self.root/'suite.json';self.suite=dict(schema_version=1,project_id='retail',required_questions=questions,cases=cases,absolute_tolerance=1e-8,max_case_seconds=30)
  self.policy.write_text(json.dumps(self.suite))
 def run_tune(self):return tune(self.project,self.policy,self.root/'work',self.root/'releases')
 def test_missing_questions_auto_improve_promote_then_noop(self):
  result=self.run_tune();self.assertEqual(result['status'],'promoted')
  self.assertEqual(len(result['proposal']['add_questions']),2)
  self.assertTrue(all(c['passed'] for c in result['candidate']))
  self.assertTrue((self.project.parent/'active-release.json').exists())
  self.assertEqual(json.loads((self.project.parent/'references/brief.json').read_text())['questions'],self.spec['questions'])
  self.assertEqual(self.run_tune()['status'],'no_change')
 def test_holdout_failure_preserves_no_previous_pointer(self):
  self.suite['cases'][-1]['expected']['revenue']=dict(current=999,previous=240,delta=759,growth_pct=316.25)
  self.policy.write_text(json.dumps(self.suite));r=self.run_tune()
  self.assertEqual(r['status'],'rejected');self.assertFalse((self.project.parent/'active-release.json').exists())
 def test_changed_metric_definition_is_not_an_auto_repair(self):
  self.suite['required_questions'][0]['metric']='invented'
  self.policy.write_text(json.dumps(self.suite))
  with self.assertRaises(ValueError):self.run_tune()
 def test_activation_failure_rolls_back_pointer(self):
  # Fail only after activation, to verify compensating rollback really executes.
  with patch('auto_tune.post_activation_check',side_effect=RuntimeError('simulated post-activation failure')):
   result=self.run_tune()
  self.assertEqual(result['status'],'rolled_back');self.assertFalse((self.project.parent/'active-release.json').exists())
 def test_data_changed_during_trial_blocks_promotion(self):
  import auto_tune
  original=auto_tune.evaluate_case;done=False
  def mutate(*args,**kwargs):
   nonlocal done
   r=original(*args,**kwargs)
   if not done:
    done=True;f=self.root/'04.csv';f.write_text(f.read_text()+'\n')
   return r
  with patch('auto_tune.evaluate_case',side_effect=mutate):r=self.run_tune()
  self.assertEqual(r['status'],'rejected');self.assertFalse((self.project.parent/'active-release.json').exists())
 def test_existing_active_pointer_restored_after_failed_upgrade(self):
  first=self.run_tune();self.assertEqual(first['status'],'promoted')
  pointer=self.project.parent/'active-release.json';before=pointer.read_bytes()
  self.suite['required_questions'].append(dict(id='extra-change',kind='change',metric='revenue',title='收入变化复核'))
  self.policy.write_text(json.dumps(self.suite))
  with patch('auto_tune.post_activation_check',side_effect=RuntimeError('archive replay failed')):r=self.run_tune()
  self.assertEqual(r['status'],'rolled_back');self.assertEqual(pointer.read_bytes(),before)
  retry=self.run_tune();self.assertEqual(retry['status'],'promoted');self.assertEqual(retry['version'],'0.1.3')
 def test_existing_pointer_preserved_when_new_case_fails(self):
  self.run_tune();pointer=self.project.parent/'active-release.json';before=pointer.read_bytes()
  self.suite['required_questions'].append(dict(id='extra-change',kind='change',metric='revenue',title='收入变化复核'))
  self.suite['cases'][-1]['expected']['revenue']=dict(current=999,previous=240,delta=759,growth_pct=316.25)
  self.policy.write_text(json.dumps(self.suite));r=self.run_tune()
  self.assertEqual(r['status'],'rejected');self.assertEqual(pointer.read_bytes(),before)
 def test_existing_question_cannot_be_redefined(self):
  self.suite['required_questions'][0]['kind']='drivers';self.policy.write_text(json.dumps(self.suite))
  with self.assertRaisesRegex(ValueError,'conflict'):self.run_tune()
 def test_unknown_engine_not_executed_or_promoted(self):
  engine=self.project.parent/'scripts/periodic_analysis.py';engine.write_text('raise RuntimeError("changed")')
  with self.assertRaisesRegex(ValueError,'Engine differs'):self.run_tune()
 def test_project_lock_blocks_competing_tuners(self):
  (self.project.parent/'.tune.lock').write_text('another run')
  with self.assertRaises(FileExistsError):self.run_tune()
 def test_bad_oracle_fails_before_trials(self):
  self.suite['cases'][0]['expected']['revenue']['delta']=999;self.policy.write_text(json.dumps(self.suite))
  with self.assertRaisesRegex(ValueError,'oracle'):self.run_tune()
 def test_recover_interrupted_activation_restores_previous_selection(self):
  import auto_tune
  r=self.run_tune();episode=Path(r['episode'])
  lock=self.project.parent/'.tune.lock';lock.write_text(json.dumps(dict(pid=987654,episode=str(episode))))
  with patch('auto_tune.os.kill',side_effect=ProcessLookupError()):result=auto_tune.recover(self.project,episode)
  self.assertEqual(result['status'],'recovered_rollback')
  self.assertFalse((self.project.parent/'active-release.json').exists());self.assertFalse(lock.exists())
 def test_recovery_refuses_live_owner(self):
  import auto_tune
  r=self.run_tune();episode=Path(r['episode']);pointer=self.project.parent/'active-release.json';before=pointer.read_bytes()
  (self.project.parent/'.tune.lock').write_text(json.dumps(dict(pid=987654,episode=str(episode))))
  with patch('auto_tune.os.kill',return_value=None):
   with self.assertRaisesRegex(ValueError,'alive'):auto_tune.recover(self.project,episode)
  self.assertEqual(pointer.read_bytes(),before)
 def test_execution_deadline_rejects_trial(self):
  self.suite['max_case_seconds']=.000001;self.policy.write_text(json.dumps(self.suite))
  r=self.run_tune();self.assertEqual(r['status'],'rejected');self.assertFalse((self.project.parent/'active-release.json').exists())
