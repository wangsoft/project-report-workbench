"""Whole-topic regression and deliberate corruption of new evidence paths."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'scripts'))
from full_data import full_normalize
from normalize import normalize
from full_compute import extend
from full_quality import check_full, verify
from full_report import render
from pypdf import PdfReader, PdfWriter
from report_canvas import safe_text


class FullReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=Path(os.environ.get('ELECTRICITY_FIXTURES',str(PROJECT.parents[1]/'workspace/public-fixtures/uk-electricity')))
        cls.data=full_normalize(cls.fixtures/'2025-release/data.xlsx',2024)
        cls.baseline=normalize(cls.fixtures/'2024-release/data.xlsx',2023)
        cls.ctxdir=cls.fixtures/'context-2024';cls.context=json.loads((cls.ctxdir/'context.json').read_text())
        cls.evidence=extend(cls.data,cls.baseline,cls.context,cls.ctxdir/'dukes-2025.pdf',cls.ctxdir/'mpp-map.png')
        cls.contract=json.loads((PROJECT/'references/contract.json').read_text())

    def checked(self,e):
        return check_full(self.data,e,self.contract,self.baseline,self.context)

    def test_full_numeric_pass_does_not_certify_source_balance(self):
        q=self.checked(self.evidence)
        self.assertEqual(q['status'],'passed');self.assertEqual(q['source_reconciliation'],'unresolved')
        self.assertEqual(q['business_review'],'pending')

    def test_missing_battery_is_not_zero(self):
        row=next(r for r in self.data['fuel_detail'] if r['year']==2020 and r['region']=='Northern Ireland')
        self.assertIsNone(row['values']['battery'])

    def test_fuel_source_conflict_preserved(self):
        gap=next(r['gap_gwh'] for r in self.evidence['source_issues'] if r['kind']=='fossil_components' and r['region']=='Wales')
        self.assertAlmostEqual(gap,1234.617,places=3)

    def test_consumption_regional_sum_is_balanced(self):
        self.assertFalse(any(r['kind']=='consumption_region_sum' for r in self.evidence['source_issues']))
        uk=next(r for r in self.evidence['supply_metrics'] if r['region']=='UK Total')
        self.assertAlmostEqual(uk['public_auto_residual'],2270.5013,places=3)

    def test_trade_net_sign_and_values(self):
        uk=self.evidence['supply_metrics'][0];self.assertAlmostEqual(uk['net_imports'],33407.8202,places=3)
        self.assertGreater(uk['balance_residual'],4000)

    def test_corrupt_fuel_growth_rejected(self):
        e=copy.deepcopy(self.evidence);e['fuel_metrics'][0]['growth']=99
        self.assertIn('fuel growth',self.checked(e)['failures'])

    def test_corrupt_trade_sign_rejected(self):
        e=copy.deepcopy(self.evidence);e['supply_metrics'][0]['net_imports']*=-1
        self.assertIn('trade sign',self.checked(e)['failures'])

    def test_removed_disagreement_rejected(self):
        e=copy.deepcopy(self.evidence);e['source_issues'].pop()
        self.assertIn('source issue count',self.checked(e)['failures'])

    def test_changed_context_rejected(self):
        e=copy.deepcopy(self.evidence);e['context']['items'][0]['text']='invented cause'
        self.assertIn('context identity/year',self.checked(e)['failures'])

    def test_old_context_cannot_be_reused(self):
        c=copy.deepcopy(self.context);c['year']=2023
        with self.assertRaisesRegex(ValueError,'year mismatch'):
            extend(self.data,self.baseline,c,self.ctxdir/'dukes-2025.pdf',self.ctxdir/'mpp-map.png')

    def test_replaced_map_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'map.png';f.write_bytes(b'wrong map')
            with self.assertRaisesRegex(ValueError,'source/map changed'):
                extend(self.data,self.baseline,self.context,self.ctxdir/'dukes-2025.pdf',f)

    def test_false_historic_record_rejected(self):
        e=copy.deepcopy(self.evidence);e['records_summary']['low_carbon_share_record']=False
        self.assertIn('low carbon record',self.checked(e)['failures'])

    def test_report_missing_page_or_topic_rejected(self):
        style=json.loads((PROJECT/'templates/style.json').read_text())
        coverage=json.loads((PROJECT/'references/coverage.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);render(self.evidence,style,d,self.ctxdir/'mpp-map.png',coverage)
            (d/'evidence.json').write_text(json.dumps(self.evidence))
            (d/'quality.json').write_text(json.dumps(self.checked(self.evidence)))
            self.assertEqual(verify(d,coverage)['status'],'passed')
            layout=json.loads((d/'layout.json').read_text())
            original=copy.deepcopy(layout)
            next(obj for obj in layout['objects'] if obj['kind']=='line_chart')['metric_id']='low_carbon_share'
            (d/'layout.json').write_text(json.dumps(layout))
            self.assertIn('plotted series differs from semantic contract',verify(d,coverage)['failures'])
            (d/'layout.json').write_text(json.dumps(original))
            reader=PdfReader(d/'report.pdf');writer=PdfWriter()
            for page in list(reader.pages)[:-1]:writer.add_page(page)
            with (d/'report.pdf').open('wb') as stream:writer.write(stream)
            failures=verify(d,coverage)['failures']
            self.assertIn('page count',failures)
            self.assertTrue(any('topic missing' in f for f in failures))

    def test_old_coverage_contract_cannot_be_reused(self):
        coverage=json.loads((PROJECT/'references/coverage.json').read_text());coverage['reference_year']=2023
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'Coverage contract year mismatch'):
                render(self.evidence,{},Path(tmp),self.ctxdir/'mpp-map.png',coverage)

    def test_missing_cid_glyphs_normalized(self):
        self.assertEqual(safe_text('A·B−C–D©'),'A / B-C-D(c)')


if __name__=='__main__':unittest.main()
