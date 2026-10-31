"""Compare frozen generated evidence to separately curated reference statements."""
import argparse
import hashlib
import json
from pathlib import Path


def evaluate(run, reference, cases):
    evidence=json.loads((run/'evidence.json').read_text())
    metrics={r['region']:r for r in evidence['metrics']};rows=[]
    for region,field,expected,divisor,tolerance,page in cases[str(evidence['year'])]:
        group,key=field.split('.');actual=metrics[region][group][key]/divisor
        rows.append(dict(region=region,field=field,actual=actual,reference=expected,
                         tolerance=tolerance,page=page,passed=abs(actual-expected)<=tolerance))
    return dict(status='passed' if all(r['passed'] for r in rows) else 'failed',scope=cases['scope'],
                run=str(run.resolve()),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),checks=rows,
                omitted=['trade','consumption','capacity','causal explanations','whole-series record claims'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['run','reference','cases','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=evaluate(a.run,a.reference,json.loads(a.cases.read_text()))
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if result['status']!='passed':raise SystemExit(1)
