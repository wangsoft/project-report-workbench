"""Experience updates must earn evidence and survive independent replay."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from experience_memory import update_memory, recall
from experience_loop import prepare, learn, finish
import test_auto_tune as fixtures

class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.losses=[dict(id='gap',case_id='feb',category='missing_rule',rule_ids=[],observation='Missed synthesis')]
        self.card=dict(id='synthesis',description='Compare opposing KPI movements',exclude='Noncomparable periods',scope='project',body='Compare directions; do not infer causes.',tags=['profit'],evidence=['gap'])
    def test_create_then_route_and_merge(self):
        cards=update_memory([], [dict(action='create',card=self.card)], self.losses, [])
        self.assertEqual(recall(cards,['profit'])[0]['id'],'synthesis')
        duplicate=dict(self.card,id='summary')
        cards=update_memory(cards,[dict(action='create',card=duplicate)],self.losses,[])
        cards=update_memory(cards,[dict(action='merge',card=self.card,remove=['summary'])],self.losses,[])
        self.assertEqual(len(cards),1)
    def test_general_rule_needs_multiple_periods(self):
        with self.assertRaisesRegex(ValueError,'multiple'):
            update_memory([], [dict(action='create',card=dict(self.card,scope='general'))],self.losses,[])
    def test_cannot_claim_unread_rule_misled(self):
        losses=[dict(self.losses[0],category='misleading_rule',rule_ids=['synthesis'])]
        with self.assertRaisesRegex(ValueError,'trace'):
            update_memory([self.card],[dict(action='correct',card=self.card)],losses,[])
    def test_bad_evidence_rejected(self):
        with self.assertRaises(ValueError):
            update_memory([], [dict(action='create',card=dict(self.card,evidence=['invented']))],self.losses,[])

class LearningTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.TuneTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.root=fixture.root;self.project=fixture.project;self.policy=fixture.policy
        suite=fixture.suite;suite['required_questions']=suite['required_questions'][:1]
        for case in suite['cases']:case['report_checks']=[dict(artifact='report.md',contains='新增综合说明')]
        self.policy.write_text(json.dumps(suite))
        ref=self.root/'reference.md';ref.write_text('新增综合说明：依据变化方向组织摘要。')
        self.comparisons=self.root/'comparisons.json'
        self.comparisons.write_text(json.dumps([dict(case_id='development',reference=str(ref),locator='synthetic paragraph 1')]))
        self.ep=self.root/'episode'
    def start(self):return prepare(self.project,self.policy,self.comparisons,self.ep,self.root/'releases')
    def proposal(self):
        state=json.loads((self.ep/'state.json').read_text());run=Path(state['baseline'][0]['run_dir'])
        quote=(run/'report.md').read_text().splitlines()[0]
        return dict(losses=[dict(id='gap',case_id='development',category='missing_rule',rule_ids=[],observation='Missing summary',reference_quote='新增综合说明',generated_quote=quote)],operations=[dict(action='create',card=dict(id='summary',description='Use for periodic summaries',exclude='Causal studies',scope='project',body='Summarize observed movements without inventing causes.',tags=['summary'],evidence=['gap']))])
    def test_baseline_gap_and_successful_learning_release(self):
        state=self.start();self.assertFalse(state['baseline'][0]['passed'])
        learn(self.ep,self.proposal())
        engine=self.ep/'candidate/scripts/periodic_analysis.py'
        engine.write_text(engine.read_text().replace("md+=boundary+", "md+='新增综合说明\\n\\n'\n    md+=boundary+"))
        result=finish(self.ep)
        self.assertEqual(result['status'],'promoted')
        release=Path(result['release']);self.assertTrue((release/'project/references/experience.json').exists())
        with self.assertRaises(ValueError):finish(self.ep)
    def test_unimplemented_rule_is_not_improvement(self):
        self.start();learn(self.ep,self.proposal());self.assertEqual(finish(self.ep)['status'],'rejected')
        self.assertFalse((self.project.parent/'active-release.json').exists())
    def test_fabricated_quote_rejected(self):
        self.start();p=self.proposal();p['losses'][0]['reference_quote']='invented'
        with self.assertRaises(ValueError):learn(self.ep,p)
    def test_holdout_cannot_be_learning_reference(self):
        refs=json.loads(self.comparisons.read_text());refs[0]['case_id']='holdout';self.comparisons.write_text(json.dumps(refs))
        with self.assertRaisesRegex(ValueError,'holdout'):self.start()
    def test_changed_suite_rejected(self):
        self.start();learn(self.ep,self.proposal());self.policy.write_text(self.policy.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'changed'):finish(self.ep)
    def test_post_activation_failure_rolls_back(self):
        self.start();learn(self.ep,self.proposal())
        engine=self.ep/'candidate/scripts/periodic_analysis.py'
        engine.write_text(engine.read_text().replace("md+=boundary+", "md+='新增综合说明\\n\\n'\n    md+=boundary+"))
        with patch('experience_loop.post_activation_check',side_effect=RuntimeError('archive replay failed')):
            result=finish(self.ep)
        self.assertEqual(result['status'],'rolled_back')
        self.assertFalse((self.project.parent/'active-release.json').exists())
    def test_cannot_remove_experience_from_release(self):
        import yaml
        self.start();learn(self.ep,self.proposal())
        p=self.ep/'candidate/project.yaml';cfg=yaml.safe_load(p.read_text());cfg['resources'].remove('references/experience.json');p.write_text(yaml.safe_dump(cfg))
        self.assertEqual(finish(self.ep)['status'],'blocked')
    def test_learning_retrieval_is_not_generation_evidence(self):
        from experience_memory import update_memory
        card=dict(id='summary',description='Periodic summary',exclude='Causal',scope='project',body='Compare movements',tags=['summary'],evidence=['gap'])
        loss=dict(id='gap',case_id='feb',category='misleading_rule',rule_ids=['summary'])
        with self.assertRaisesRegex(ValueError,'trace'):
            update_memory([card],[dict(action='correct',card=card)],[loss],[dict(case_id='feb',rule_id='summary',kind='explicit_host_retrieval')])
        result=update_memory([card],[dict(action='correct',card=card)],[loss],[dict(case_id='feb',rule_id='summary',kind='pipeline_applied_rule')])
        self.assertEqual(result[0]['id'],'summary')
