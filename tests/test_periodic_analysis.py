"""Independent small examples for executable onboarding and closed delivery gates."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from periodic_analysis import analyze, validate_spec, verify, render
from onboard_project import create_project

SPEC={'schema_version':1,'project_id':'sales','title':'销售分析','audience':'经营负责人',
      'scope':'descriptive_periodic','period_column':'month','entity_column':'region',
      'periods':['2026-01','2026-02'],'entities':['A','B'],
      'metrics':[{'id':'revenue','column':'amount','label':'收入','unit':'元','aggregation':'sum','direction':'higher'}],
      'questions':[{'id':'change','kind':'change','metric':'revenue','title':'收入如何变化？'},
                   {'id':'drivers','kind':'drivers','metric':'revenue','title':'增长来自哪里？'},
                   {'id':'exceptions','kind':'exceptions','metric':'revenue','title':'哪些地区逆势？'}]}

class PeriodicTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
        self.data=self.p/'data.csv';self.data.write_text('month,region,amount\n2026-01,A,100\n2026-01,B,100\n2026-02,A,150\n2026-02,B,80\n')
    def test_known_totals_contributions_and_counterexample(self):
        e=analyze(self.data,SPEC,'2026-02');m=e['metrics'][0]
        self.assertEqual(m['current'],230);self.assertEqual(m['delta'],30)
        self.assertAlmostEqual(m['growth_pct'],15)
        self.assertEqual([x['entity'] for x in m['opposite_direction']],['B'])
        self.assertEqual(sum(x['delta'] for x in m['drivers']),30)
        self.assertEqual(sum(x['contribution_pp'] for x in m['drivers']),15)
    def test_missing_entity_cannot_silently_be_zero(self):
        self.data.write_text('month,region,amount\n2026-01,A,100\n2026-01,B,100\n2026-02,A,150\n')
        with self.assertRaisesRegex(ValueError,'coverage'):analyze(self.data,SPEC,'2026-02')
    def test_duplicate_grain_rejected(self):
        with self.data.open('a') as f:f.write('2026-02,A,1\n')
        with self.assertRaisesRegex(ValueError,'duplicate'):analyze(self.data,SPEC,'2026-02')
    def test_invalid_numbers_rejected(self):
        for value in ['', 'NaN', 'inf', '=1+1']:
            self.data.write_text(f'month,region,amount\n2026-01,A,{value}\n')
            with self.assertRaises(ValueError):analyze(self.data,SPEC,'2026-02')
    def test_zero_baseline_growth_undefined(self):
        self.data.write_text('month,region,amount\n2026-01,A,0\n2026-01,B,0\n2026-02,A,150\n2026-02,B,80\n')
        m=analyze(self.data,SPEC,'2026-02')['metrics'][0]
        self.assertIsNone(m['growth_pct']);self.assertTrue(all(x['contribution_pp'] is None for x in m['drivers']))
    def test_no_implicit_causal_or_ratio_support(self):
        s=copy.deepcopy(SPEC);s['questions'][0]['kind']='cause'
        with self.assertRaises(ValueError):validate_spec(s)
        s=copy.deepcopy(SPEC);s['metrics'][0]['aggregation']='average'
        with self.assertRaises(ValueError):validate_spec(s)
    def test_tampered_evidence_or_missing_answer_blocks_delivery(self):
        e=analyze(self.data,SPEC,'2026-02');render(e,SPEC,self.p)
        (self.p/'evidence.json').write_text(json.dumps(e))
        self.assertEqual(verify(self.data,SPEC,'2026-02',self.p)['status'],'ready_within_scope')
        e['metrics'][0]['current']=999;(self.p/'evidence.json').write_text(json.dumps(e))
        self.assertEqual(verify(self.data,SPEC,'2026-02',self.p)['status'],'blocked')
    def test_bootstrap_creates_real_pipeline_and_refuses_overwrite(self):
        p=create_project(SPEC,self.p/'projects');self.assertTrue(p.exists())
        import yaml
        self.assertEqual(len(yaml.safe_load(p.read_text())['pipeline']),3)
        with self.assertRaises(FileExistsError):create_project(SPEC,self.p/'projects')

class IntegrationTests(unittest.TestCase):
    setUp = PeriodicTests.setUp
    def test_real_bootstrap_run_and_cache(self):
        from project_manager import run,config
        p=create_project(SPEC,self.p/'projects');config(p)
        inputs=self.p/'inputs.json';inputs.write_text(json.dumps({'data':str(self.data),'period':'2026-02'}))
        a=run(p,inputs,self.p/'runs',self.p/'cache');b=run(p,inputs,self.p/'runs',self.p/'cache')
        self.assertEqual((a/'report.html').read_bytes(),(b/'report.html').read_bytes())
        state=json.loads((b/'run_state.json').read_text())
        self.assertEqual([r['cache'] for r in state['stages']],['hit','hit','disabled'])
        self.assertEqual(json.loads((b/'delivery.json').read_text())['status'],'ready_within_scope')
    def test_xlsx_formula_and_mapped_sheet(self):
        from openpyxl import Workbook
        p=self.p/'data.xlsx';book=Workbook();sheet=book.active;sheet.title='Data'
        for row in [('month','region','amount'),('2026-01','A',100),('2026-01','B',100),('2026-02','A',150),('2026-02','B',80)]:sheet.append(row)
        book.save(p);s=copy.deepcopy(SPEC);s['sheet']='Data'
        self.assertEqual(analyze(p,s,'2026-02')['metrics'][0]['current'],230)
        sheet['C5']='=40*2';book.save(p)
        with self.assertRaises(ValueError):analyze(p,s,'2026-02')
    def test_render_escapes_user_labels_and_tamper_blocks(self):
        s=copy.deepcopy(SPEC);s['title']='<script>alert(1)</script>'
        e=analyze(self.data,s,'2026-02');render(e,s,self.p);(self.p/'evidence.json').write_text(json.dumps(e))
        self.assertNotIn('<script>',(self.p/'report.html').read_text())
        (self.p/'report.html').write_text('silently omitted questions')
        self.assertEqual(verify(self.data,s,'2026-02',self.p)['status'],'blocked')
