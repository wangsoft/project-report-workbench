"""Evaluate curated official numerical statements after generation, never as pipeline inputs."""
import argparse
import hashlib
import json
from pathlib import Path
from evaluate_reference import evaluate


def evaluate_full(run:Path,reference:Path,cases:dict,base_cases:dict) -> dict:
    e=json.loads((run/'evidence.json').read_text());fuel={(m['region'],m['fuel']):m for m in e['fuel_metrics']}
    supply={m['region']:m for m in e['supply_metrics']};rows=[]
    for case in cases['cases']:
        kind,region,key,field,divisor,expected,tolerance,page=case
        if kind=='fuel':actual=fuel[region,key][field]/divisor
        else:
            v=supply[region];actual=(v['values'][key] if field=='value' else v[field])/divisor
        rows.append(dict(kind=kind,region=region,key=key,field=field,actual=actual,reference=expected,tolerance=tolerance,page=page,passed=abs(actual-expected)<=tolerance))
    base=evaluate(run,reference,base_cases)
    conflicts=[r for r in rows if not r['passed']]
    return dict(status='passed' if not conflicts and base['status']=='passed' else 'reference_disagreements',scope='Selected numerical statements across official pages 1-8; topic coverage separately verified; not blind evaluation.',reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),base_checks=base['checks'],expanded_checks=rows,reference_disagreements=conflicts,passed=sum(r['passed'] for r in rows+base['checks']),total=len(rows)+len(base['checks']),interpretation='Retain workbook-derived values. Reference discrepancies require review, not tuning calculations to match prose.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['run','reference','cases','base-cases','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();result=evaluate_full(a.run,a.reference,json.loads(a.cases.read_text()),json.loads(a.base_cases.read_text()))
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'status':result['status'],'passed':result['passed'],'total':result['total'],'disagreements':result['reference_disagreements']},ensure_ascii=False))
