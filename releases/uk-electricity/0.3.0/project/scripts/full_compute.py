"""Compute complete report facts; attach separately sourced, year-bound context."""
import argparse
import hashlib
import json
from pathlib import Path
from compute import compute
from normalize import REGIONS


def digest(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extend(data: dict, baseline: dict, context: dict, source: str, map_path: str) -> dict:
    if context['year']!=data['year']:raise ValueError('Context year mismatch; obtain current-period external evidence')
    if context['source_sha256']!=digest(source) or context['map_sha256']!=digest(map_path):
        raise ValueError('Context source/map changed')
    e=compute(data,baseline);year=data['year']
    e.update({k:data[k] for k in ['fuel_detail','supply','historical_records']})
    e['context']=context
    fuel={(r['year'],r['region']):r for r in data['fuel_detail']}
    supply={(r['year'],r['region']):r for r in data['supply']}
    e['fuel_metrics']=[];e['supply_metrics']=[]
    for region in REGIONS:
        cur=fuel[year,region]['values'];prev=fuel[year-1,region]['values'];start=fuel[year-4,region]['values']
        for key,value in cur.items():
            e['fuel_metrics'].append(dict(region=region,fuel=key,gwh=value,share=value/cur['total']*100 if value is not None else None,
                growth=(value/prev[key]-1)*100 if prev[key] and value is not None else None,
                five_year_growth=(value/start[key]-1)*100 if start[key] and value is not None else None,
                share_pp=(value/cur['total']-prev[key]/prev['total'])*100 if value is not None and prev[key] is not None else None,
                cell=fuel[year,region]['locators'][key],previous_cell=fuel[year-1,region]['locators'][key]))
        s=supply[year,region]['values'];old=supply[year-1,region]['values']
        balance=s['generation']-s['own_other']-s['own_mpp']-s['to_england']-s['to_ni']-s['to_europe']-s['transmission']-s['distribution']
        e['supply_metrics'].append(dict(region=region,values=s,cells=supply[year,region]['locators'],
            consumption_share=s['consumption']/supply[year,'UK Total']['values']['consumption']*100,
            consumption_growth=(s['consumption']/old['consumption']-1)*100,
            net_imports=-s['to_europe'],balance_consumption=balance,
            balance_residual=balance-s['consumption'],
            public_auto_residual=s['public_consumption']+s['auto_consumption']-s['consumption']))
    e['source_issues']=[]
    for record in data['fuel_detail']:
        v=record['values'];gap=v['fossil']-sum(v[k] for k in ['coal','oil','gas'])
        if abs(gap)>.05:e['source_issues'].append(dict(kind='fossil_components',year=record['year'],region=record['region'],gap_gwh=gap))
    for y in data['available_years']:
        uk=supply[y,'UK Total']['values']
        gap=sum(supply[y,r]['values']['consumption'] for r in REGIONS[1:])-uk['consumption']
        if abs(gap)>.05:e['source_issues'].append(dict(kind='consumption_region_sum',year=y,gap_gwh=gap))
    for r in e['supply_metrics']:
        for key in ['balance_residual','public_auto_residual']:
            if abs(r[key])>.05:e['source_issues'].append(dict(kind=key,year=year,region=r['region'],gap_gwh=r[key]))
    # Use the fuel table consistently for published-series extrema; never join conflicting early totals.
    history=[r for r in data['historical_records'] if r['region']=='UK Total']
    latest=next(r for r in history if r['year']==year)['values']
    e['records_summary']={}
    for key in ['total','fossil','nuclear','renewables','coal','wind']:
        vals=[r['values'][key] for r in history if r['values'][key] is not None]
        e['records_summary'][key]=dict(minimum=latest[key]<=min(vals),maximum=latest[key]>=max(vals),start_year=min(r['year'] for r in history))
    shares=[(r['values']['nuclear']+r['values']['renewables'])/r['values']['total']*100 for r in history]
    renewable_shares=[r['values']['renewables']/r['values']['total']*100 for r in history]
    e['records_summary']['low_carbon_share_record']=shares[-1]>=max(shares)
    e['records_summary']['renewables_first_over_half']=renewable_shares[-1]>50 and all(v<=50 for v in renewable_shares[:-1])
    e['report_mode']='full_topic_candidate'
    return e


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['normalized','baseline','context','context-source','map','out']:p.add_argument('--'+key,required=True)
    a=p.parse_args();load=lambda p:json.loads(Path(p).read_text())
    Path(a.out).write_text(json.dumps(extend(load(a.normalized),load(a.baseline),load(a.context),a.context_source,a.map),ensure_ascii=False,indent=2))
