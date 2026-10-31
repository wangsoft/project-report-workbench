"""Real-source regression plus deliberate faults; no reference PDF in generation."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parents[1]
sys.path.insert(0,str(PROJECT/'scripts'))
from normalize import normalize
from compute import compute
from quality import check


class ElectricityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=ROOT/'workspace/public-fixtures/uk-electricity'
        cls.old=normalize(cls.fixtures/'2024-release/data.xlsx',2023)
        cls.new=normalize(cls.fixtures/'2025-release/data.xlsx',2024)
        cls.evidence=compute(cls.new,cls.old)
        cls.contract=json.loads((PROJECT/'references/contract.json').read_text())

    def test_published_cell_and_same_vintage_baseline(self):
        uk=self.evidence['metrics'][0]
        self.assertAlmostEqual(uk['current_gwh']['total'],284956.2014,places=4)
        self.assertAlmostEqual(uk['previous_gwh']['total'],294078.6,delta=0.1)
        self.assertAlmostEqual(uk['growth_pct']['total'],-3.1019,delta=0.001)
        self.assertAlmostEqual(uk['shares_pct']['low_carbon'],64.675,delta=0.01)
        self.assertEqual(check(self.new,self.evidence,self.contract)['status'],'passed')

    def test_wrong_growth_blocked(self):
        broken=copy.deepcopy(self.evidence);broken['metrics'][0]['growth_pct']['total']=8
        self.assertEqual(check(self.new,broken,self.contract)['status'],'failed')

    def test_wrong_period_blocked(self):
        broken=copy.deepcopy(self.evidence);broken['year']=2023
        self.assertIn('period identity',check(self.new,broken,self.contract)['failures'])

    def test_missing_claim_blocked(self):
        broken=copy.deepcopy(self.evidence);broken['claims'].pop()
        self.assertEqual(check(self.new,broken,self.contract)['status'],'failed')

    def test_low_carbon_not_storage_or_other_fuels(self):
        uk=self.evidence['metrics'][0]
        expected=(40587.8448+143707.6921)/284956.2014*100
        self.assertAlmostEqual(uk['shares_pct']['low_carbon'],expected)
        self.assertGreater(uk['residual_gwh'],10000)

    def test_historical_conflicts_disclosed_not_used(self):
        self.assertEqual(self.new['available_years'],[2020,2021,2022,2023,2024])
        self.assertGreater(len(self.new['excluded_historical_conflicts']),0)
        self.assertTrue(any(r['year']==2022 for r in self.new['active_small_differences']))

    def test_future_data_not_silently_used(self):
        with self.assertRaisesRegex(ValueError,'latest year'):
            normalize(self.fixtures/'2025-release/data.xlsx',2023)

    def test_new_low_carbon_row_does_not_shift_total(self):
        self.assertTrue(self.old['records'][-1]['locators']['total'].endswith('42'))
        self.assertTrue(self.new['records'][-1]['locators']['total'].endswith('43'))


if __name__=='__main__':unittest.main()
