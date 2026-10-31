"""Check expanded calculations, source disagreements, coverage and PDF artifacts separately."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from pypdf import PdfReader
from quality import check
from normalize import REGIONS


def check_full(data:dict,e:dict,contract:dict,baseline:dict,context:dict) -> dict:
    result=check(data,e,contract,baseline);failures=result['failures'];count=result['checks']
    def require(ok,label):
        nonlocal count
        count+=1
        if not ok:failures.append(label)
    def equal(a,b):
        if a is None or b is None:return a is b
        return math.isfinite(a) and abs(a-b)<1e-6
    for key in ['fuel_detail','supply','historical_records']:require(e[key]==data[key],key+' source identity')
    require(e['context']==context and context['year']==data['year'],'context identity/year')
    fuel={(r['year'],r['region']):r for r in data['fuel_detail']};year=data['year']
    expected_keys={(r,k) for r in REGIONS for k in fuel[year,r]['values']}
    require({(m['region'],m['fuel']) for m in e['fuel_metrics']}==expected_keys,'fuel coverage')
    require(len(e['fuel_metrics'])==len(expected_keys),'fuel uniqueness')
    for m in e['fuel_metrics']:
        g=m['region'];k=m['fuel'];cur=fuel[year,g];prev=fuel[year-1,g];start=fuel[year-4,g]
        v=cur['values'][k];p=prev['values'][k];s=start['values'][k]
        require(equal(m['gwh'],v),'fuel value')
        require(equal(m['share'],v/cur['values']['total']*100 if v is not None else None),'fuel share')
        require(equal(m['growth'],(v-p)/p*100 if p and v is not None else None),'fuel growth')
        require(equal(m['five_year_growth'],(v-s)/s*100 if s and v is not None else None),'fuel window growth')
        require(equal(m['share_pp'],(v/cur['values']['total']-p/prev['values']['total'])*100 if v is not None and p is not None else None),'fuel pp')
        require(m['cell']==cur['locators'][k] and m['previous_cell']==prev['locators'][k],'fuel lineage')
    issues=[]
    for (y,g),rec in fuel.items():
        v=rec['values']
        gap=v['fossil']-sum(v[k] for k in ['coal','oil','gas'])
        if abs(gap)>.05:issues.append(dict(kind='fossil_components',year=y,region=g,gap_gwh=gap))
        require(abs(v['renewables']-sum(v[k] for k in ['wind','solar','hydro','tidal','bioenergy']))<.05,'renewable components')
    supply={(r['year'],r['region']):r for r in data['supply']}
    require([m['region'] for m in e['supply_metrics']]==REGIONS,'supply coverage')
    for y in data['available_years']:
        gap=sum(supply[y,g]['values']['consumption'] for g in REGIONS[1:])-supply[y,'UK Total']['values']['consumption']
        if abs(gap)>.05:issues.append(dict(kind='consumption_region_sum',year=y,gap_gwh=gap))
    for m in e['supply_metrics']:
        s=supply[year,m['region']];v=s['values'];p=supply[year-1,m['region']]['values']
        require(m['values']==v and m['cells']==s['locators'],'supply lineage')
        require(equal(m['consumption_share'],v['consumption']/supply[year,'UK Total']['values']['consumption']*100),'consumption share')
        require(equal(m['consumption_growth'],(v['consumption']/p['consumption']-1)*100),'consumption growth')
        require(equal(m['net_imports'],-v['to_europe']),'trade sign')
        balance=v['generation']-sum(v[k] for k in ['own_other','own_mpp','to_england','to_ni','to_europe','transmission','distribution'])
        require(equal(m['balance_consumption'],balance),'supply balance')
        for key,expected in [('balance_residual',balance-v['consumption']),('public_auto_residual',v['public_consumption']+v['auto_consumption']-v['consumption'])]:
            require(equal(m[key],expected),'source residual')
            if abs(expected)>.05:issues.append(dict(kind=key,year=year,region=m['region'],gap_gwh=m[key]))
    # Exact issue coverage protects against hiding contradictory source totals.
    require(len(issues)==len(e['source_issues']),'source issue count')
    for a,b in zip(issues,e['source_issues']):
        require({k:v for k,v in a.items() if k!='gap_gwh'}=={k:v for k,v in b.items() if k!='gap_gwh'} and equal(a['gap_gwh'],b['gap_gwh']),'source issue disclosure')
    history=[r for r in data['historical_records'] if r['region']=='UK Total'];latest=next(r for r in history if r['year']==year)['values']
    for k in ['total','fossil','nuclear','renewables','coal','wind']:
        vals=[r['values'][k] for r in history if r['values'][k] is not None];s=e['records_summary'][k]
        require(s['minimum']==(latest[k]<=min(vals)) and s['maximum']==(latest[k]>=max(vals)),'historic record')
    require(e['records_summary']['renewables_first_over_half']==(latest['renewables']/latest['total']>.5 and all(r['values']['renewables']/r['values']['total']<=.5 for r in history if r['year']<year)),'first over half')
    lc=[(r['values']['nuclear']+r['values']['renewables'])/r['values']['total'] for r in history]
    cur_lc=(latest['nuclear']+latest['renewables'])/latest['total']
    require(e['records_summary']['low_carbon_share_record']==(cur_lc>=max(lc)),'low carbon record')
    result.update(status='passed' if not failures else 'failed',checks=count,source_reconciliation='unresolved' if issues else 'balanced',source_issues=issues,scope='calculation and lineage correctness; source disagreements disclosed, not resolved')
    return result


def verify(directory:Path,coverage:dict) -> dict:
    e=json.loads((directory/'evidence.json').read_text());q=json.loads((directory/'quality.json').read_text())
    layout=json.loads((directory/'layout.json').read_text());c=json.loads((directory/'coverage.json').read_text())
    pages=PdfReader(directory/'report.pdf').pages;texts=[p.extract_text() for p in pages];text='\n'.join(texts);fail=[]
    if q['status']!='passed':fail.append('numeric gate')
    if len(pages)!=15 or layout['pages']!=15:fail.append('page count')
    if c!=coverage:fail.append('coverage manifest changed')
    for item in coverage['items']:
        for page in item['report_pages']:
            if not 1<=page<=len(pages) or item['token'] not in texts[page-1]:fail.append('topic missing '+item['id'])
    for m in e['fuel_metrics']:
        if m['region']=='UK Total' and m['fuel'] in ['coal','oil','gas','nuclear','renewables','fossil','wind','solar','hydro','bioenergy']:
            if f"{m['gwh']/1000:.2f}" not in text:fail.append('missing fuel number')
    for item in e['context']['items']+e['context']['historical_context']:
        if item['id'] not in text:fail.append('missing external attribution')
    for obj in layout['objects']:
        x,y,w,h=obj['bbox']
        if not (0<=x<x+w<=layout['width'] and 0<=y<y+h<=layout['height']):fail.append('out of bounds')
    if not pages[12].images:fail.append('missing map image')
    names=['report.pdf','report.md','evidence.json','quality.json','layout.json','coverage.json']
    return dict(status='passed' if not fail else 'failed',failures=fail,
        artifacts={n:hashlib.sha256((directory/n).read_bytes()).hexdigest() for n in names},
        topic_coverage='all_sections_addressed',full_analyst_equivalence='not_validated',
        source_reconciliation=q['source_reconciliation'],visual_review='pending',business_review='pending')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['normalized','evidence','contract','baseline','context','verify-dir','coverage']:p.add_argument('--'+name)
    p.add_argument('--out',required=True);a=p.parse_args();load=lambda x:json.loads(Path(x).read_text())
    result=verify(Path(a.verify_dir),load(a.coverage)) if a.verify_dir else check_full(load(a.normalized),load(a.evidence),load(a.contract),load(a.baseline),load(a.context))
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    if result['status']!='passed':raise SystemExit('Quality failed: '+str(result['failures']))
