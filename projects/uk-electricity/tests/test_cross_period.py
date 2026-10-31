"""Retrospective 2022 input compatibility and rejection of stale/mutated evidence."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
import tempfile
from pypdf import PdfReader

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'scripts'))
from full_report import render
from full_data import full_normalize
from full_compute import extend
from full_quality import check_full


class CrossPeriodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=Path(os.environ.get('ELECTRICITY_FIXTURES',str(PROJECT.parents[1]/'workspace/public-fixtures/uk-electricity')))
        cls.data=full_normalize(cls.fixtures/'2023-release/data.xlsx',2022)
        cls.old=json.loads((cls.fixtures/'2022-release/normalized.json').read_text())
        cls.context=json.loads((cls.fixtures/'context-2022/context.json').read_text())
        cls.e=extend(cls.data,cls.old,cls.context,cls.fixtures/'context-2022/dukes-2023.pdf',cls.fixtures/'context-2022/mpp-map.png')
        cls.contract=json.loads((PROJECT/'references/contract.json').read_text())

    def check(self,d,e):return check_full(d,e,self.contract,self.old,self.context)

    def test_older_schema_battery_absent_is_null(self):
        self.assertTrue(all(r['values']['battery'] is None and r['locators']['battery'] is None for r in self.data['fuel_detail']))
        self.assertTrue(all(r['values']['own_mpp']>0 for r in self.data['supply']))

    def test_exact_source_exception_disclosed(self):
        q=self.check(self.data,self.e)
        self.assertEqual(q['status'],'passed')
        self.assertIn('accepted_source_exception',q)
        self.assertEqual(len(q['source_issues']),5)
        self.assertAlmostEqual(max(x['gap_gwh'] for x in q['source_issues']),.444,places=6)

    def test_changed_source_cannot_inherit_exception(self):
        d=copy.deepcopy(self.data);e=copy.deepcopy(self.e)
        d['source_sha256']=e['source_sha256']='modified'
        self.assertIn('cross-sheet total',self.check(d,e)['failures'])

    def test_changed_difference_cannot_inherit_exception(self):
        d=copy.deepcopy(self.data);d['active_small_differences'][0]['gap_gwh']+=.1
        self.assertIn('cross-sheet total',self.check(d,self.e)['failures'])

    def test_2022_trade_reversal_and_balanced_flows(self):
        self.assertLess(self.e['supply_metrics'][0]['net_imports'],0)
        self.assertGreater(self.e['previous_net_imports'],0)
        self.assertFalse(any(r['kind']=='balance_residual' for r in self.e['source_issues']))

    def test_growth_drivers_are_additive(self):
        total=sum(r['growth_contribution_pp'] for r in self.e['drivers'])
        self.assertAlmostEqual(total,self.e['metrics'][0]['growth_pct']['total'])
        self.assertEqual(max(self.e['drivers'],key=lambda r:r['delta_gwh'])['key'],'renewables')

    def test_corrupt_driver_rejected(self):
        e=copy.deepcopy(self.e);e['drivers'][0]['delta_gwh']=123
        self.assertIn('driver arithmetic',self.check(self.data,e)['failures'])

    def test_render_switches_direction_and_removes_stale_context(self):
        style=json.loads((PROJECT/'templates/style.json').read_text())
        coverage=json.loads((self.fixtures/'2023-release/coverage.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            render(self.e,style,Path(tmp),self.fixtures/'context-2022/mpp-map.png',coverage)
            text='\n'.join(p.extract_text() for p in PdfReader(Path(tmp)/'report.pdf').pages)
            self.assertIn('净出口 5.34 TWh',text)
            self.assertIn('0.000444',text)
            self.assertNotIn('DUKES 2025',text)
            self.assertNotIn('Clean Power 2030',text)

    def test_no_future_policy_context(self):
        self.assertEqual(self.context['year'],2022)
        self.assertNotIn('Clean Power 2030',json.dumps(self.context))
        self.assertEqual(self.context['map_as_of'],'2023-05')


if __name__=='__main__':unittest.main()
