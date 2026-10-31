"""Executable numeric/lineage checks and separate PDF structural acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from pypdf import PdfReader


def check(data, evidence, contract, baseline=None):
    failures=[]; checks=0
    def require(condition,label):
        nonlocal checks
        checks+=1
        if not condition:failures.append(label)
    def close(a,b,tol=1e-6):
        return a is not None and b is not None and math.isfinite(a) and abs(a-b)<=tol
    require(data['source_sha256']==evidence['source_sha256'],'source identity')
    require(data['year']==evidence['year'],'period identity')
    require(data['unit']==evidence['unit']=='GWh','unit identity')
    require(data['cross_table_max_gap_gwh']<=contract['source_total_gap_gwh'],'cross-sheet total')
    index={(r['year'],r['region']):r for r in data['records']}
    require(len(index)==len(data['records']),'duplicate normalized keys')
    for year in data['available_years']:
        for metric in ['total','fossil','nuclear','renewables']:
            expected=index[(year,'UK Total')]['values'][metric]
            actual=sum(index[(year,region)]['values'][metric] for region in contract['regions'][1:])
            require(close(actual,expected,contract['region_sum_gap_gwh']),f'region sum {year} {metric}')
    require([m['region'] for m in evidence['metrics']]==contract['regions'],'metric region coverage')
    for m in evidence['metrics']:
        cur=index[(data['year'],m['region'])];prev=index[(data['year']-1,m['region'])]
        for key,value in cur['values'].items():
            require(close(m['current_gwh'][key],value),f'current {m["region"]} {key}')
            require(close(m['previous_gwh'][key],prev['values'][key]),f'previous {m["region"]} {key}')
            require(m['source_cells'][key]==cur['locators'][key],f'lineage {key}')
            expected=(value-prev['values'][key])/prev['values'][key]*100 if prev['values'][key]>0 else None
            require(m['growth_pct'][key] is None if expected is None else close(m['growth_pct'][key],expected),f'growth {key}')
        for key in ['fossil','nuclear','renewables']:
            require(close(m['shares_pct'][key],cur['values'][key]/cur['values']['total']*100),f'share {key}')
        low=(cur['values']['nuclear']+cur['values']['renewables'])/cur['values']['total']*100
        require(close(m['shares_pct']['low_carbon'],low),'low-carbon definition')
        residual=cur['values']['total']-sum(cur['values'][k] for k in ['fossil','nuclear','renewables'])
        require(close(m['residual_gwh'],residual) and residual>=-contract['region_sum_gap_gwh'],'residual')
    valid_regions=set(contract['regions']);claim_ids=set()
    for claim in evidence['claims']:
        require(claim['claim_id'] not in claim_ids,'duplicate claim id');claim_ids.add(claim['claim_id'])
        require(claim['metric_region'] in valid_regions,'claim region')
        require(claim['kind']=='computed_fact' and bool(claim['evidence']),'claim type/evidence')
    require(len(claim_ids)==len(valid_regions),'claim coverage')
    for claim in evidence['claims']:
        region=claim['metric_region']
        if region in valid_regions:
            current=index[(data['year'],region)];previous=index[(data['year']-1,region)]
            expected=[current['locators']['total'],previous['locators']['total'],current['locators']['renewables'],current['locators']['nuclear']]
            require(claim['evidence']==expected,'claim evidence links')
    require([r['year'] for r in evidence['trend']]==data['available_years'],'trend period coverage')
    for r in evidence['trend']:
        require(r==index.get((r['year'],'UK Total')),'trend matches source')
    if baseline is not None:
        require(evidence['baseline_sha256']==baseline['source_sha256'],'baseline identity')
        old={(r['year'],r['region']):r for r in baseline['records']}
        require(len(evidence['revisions'])==5,'revision coverage')
        for r in evidence['revisions']:
            key=(r['year'],r['region'])
            require(close(r['old_gwh'],old[key]['values']['total']),'old vintage value')
            require(close(r['revised_gwh'],index[key]['values']['total']),'new vintage value')
            require(close(r['gap_gwh'],r['revised_gwh']-r['old_gwh']),'revision difference')
    return dict(status='passed' if not failures else 'failed',checks=checks,failures=failures,
                scope='numeric, reconciliation, period, source and claim checks',
                visual_review='pending',business_review='pending',
                warnings=dict(excluded_historical_conflicts=data.get('excluded_historical_conflicts',[]),
                              active_small_differences=data.get('active_small_differences',[])))


def verify(directory):
    evidence=json.loads((directory/'evidence.json').read_text())
    quality=json.loads((directory/'quality.json').read_text())
    layout=json.loads((directory/'layout.json').read_text())
    reader=PdfReader(directory/'report.pdf');text='\n'.join(p.extract_text() for p in reader.pages)
    failures=[]
    if quality['status']!='passed':failures.append('numeric gate failed')
    if len(reader.pages)!=4 or layout['pages']!=4:failures.append('page count')
    for m in evidence['metrics']:
        for token in [f"{m['current_gwh']['total']/1000:.2f}",f"{m['growth_pct']['total']:+.2f}%",f"{m['shares_pct']['low_carbon']:.2f}%"]:
            if token not in text:failures.append('missing report number '+token)
    for claim in evidence['claims']:
        if claim['claim_id'] not in text:failures.append('missing claim id')
    for obj in layout['objects']:
        x,y,w,h=obj['bbox']
        if not (0<=x<x+w<=layout['width'] and 0<=y<y+h<=layout['height']):failures.append('out of bounds')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
            if p.name in ['report.pdf','report.md','evidence.json','quality.json','layout.json']}
    return dict(schema_version=1,status='passed' if not failures else 'failed',failures=failures,
                scope='automated numeric and PDF structural checks only',visual_review='pending',
                business_review='pending',artifacts=hashes)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--normalized');p.add_argument('--evidence');p.add_argument('--contract');p.add_argument('--baseline')
    p.add_argument('--verify-dir');p.add_argument('--out',required=True)
    a=p.parse_args()
    if a.verify_dir:result=verify(Path(a.verify_dir))
    else:result=check(json.loads(Path(a.normalized).read_text()),json.loads(Path(a.evidence).read_text()),json.loads(Path(a.contract).read_text()), json.loads(Path(a.baseline).read_text()) if a.baseline else None)
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if result['status']!='passed':raise SystemExit('Quality gate failed: '+str(result['failures']))
