"""Semantic regressions derived from the official chart definitions, not its answers."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from report_semantics import build, check
from full_data import full_normalize
from full_compute import extend
ROOT=P.parents[1]
class SemanticsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  f=Path(os.environ.get('ELECTRICITY_FIXTURES',str(ROOT/'workspace/public-fixtures/uk-electricity')))
  data=full_normalize(f/'2023-release/data.xlsx',2022)
  cls.e=extend(data,json.loads((f/'2022-release/normalized.json').read_text()),json.loads((f/'context-2022/context.json').read_text()),f/'context-2022/dukes-2023.pdf',f/'context-2022/mpp-map.png')
 def test_supply_is_net_of_own_use(self):
  s=build(self.e);a=s['charts']['supply_share']['values'];self.assertAlmostEqual(a['England'],72.5,delta=.05);self.assertAlmostEqual(a['Wales'],8.8,delta=.05)
 def test_renewable_curve_excludes_nuclear(self):
  s=build(self.e);self.assertAlmostEqual(s['charts']['renewable_share']['series']['Scotland'][-1],70.98,delta=.01)
  bad=copy.deepcopy(s);bad['charts']['renewable_share']['series']['Scotland'][-1]=86.77
  self.assertTrue(check(self.e,bad))
 def test_regional_divergence_not_hidden_in_tables(self):
  s=build(self.e);text=s['answers']['regional_nuclear'];self.assertIn('-45.09',text);self.assertIn('+26.54',text)
 def test_missing_answer_blocks(self):
  s=build(self.e);del s['answers']['regional_nuclear'];self.assertTrue(check(self.e,s))
