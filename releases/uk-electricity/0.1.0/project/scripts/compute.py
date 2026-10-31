"""Produce deterministic metrics, claim references, and vintage revisions."""
import argparse
from decimal import Decimal
import json
from pathlib import Path


def compute(data, baseline):
    year = data['year']
    index = {(r['year'], r['region']): r for r in data['records']}
    old = {(r['year'], r['region']): r for r in baseline['records']}
    metrics = []
    for region in ['UK Total', 'England', 'Scotland', 'Wales', 'Northern Ireland']:
        current = index[(year, region)]
        previous = index[(year - 1, region)]
        val = {k: Decimal(str(v)) for k, v in current['values'].items()}
        prev = {k: Decimal(str(v)) for k, v in previous['values'].items()}
        record = dict(region=region, current_gwh=current['values'], previous_gwh=previous['values'],
                      source_cells=current['locators'], previous_cells=previous['locators'])
        record['growth_pct'] = {k: float((val[k]/prev[k]-1)*100) if prev[k]>0 else None for k in val}
        record['shares_pct'] = {k: float(val[k]/val['total']*100) for k in ['fossil','nuclear','renewables']}
        record['shares_pct']['low_carbon'] = float((val['nuclear']+val['renewables'])/val['total']*100)
        record['residual_gwh'] = float(val['total']-val['fossil']-val['nuclear']-val['renewables'])
        record['delta_gwh'] = float(val['total']-prev['total'])
        record['uk_share_pct'] = float(val['total']/Decimal(str(index[(year,'UK Total')]['values']['total']))*100)
        metrics.append(record)
    revisions = []
    shared_year = min(year - 1, baseline['year'])
    for region in ['UK Total', 'England', 'Scotland', 'Wales', 'Northern Ireland']:
        a = old[(shared_year, region)]
        b = index[(shared_year, region)]
        revisions.append(dict(year=shared_year, region=region, old_gwh=a['values']['total'],
                              revised_gwh=b['values']['total'],
                              gap_gwh=b['values']['total']-a['values']['total'],
                              old_cell=a['locators']['total'], new_cell=b['locators']['total']))
    claims = [dict(claim_id=f'C-{i+1:03}', kind='computed_fact', metric_region=r['region'],
                   metric_fields=['current_gwh.total', 'growth_pct.total', 'shares_pct.low_carbon'],
                   evidence=[r['source_cells']['total'],r['previous_cells']['total'],
                             r['source_cells']['renewables'],r['source_cells']['nuclear']])
              for i,r in enumerate(metrics)]
    return dict(schema_version=1, year=year, unit='GWh', metrics=metrics, claims=claims,
                trend=[index[(y,'UK Total')] for y in range(year-4,year+1)], revisions=revisions,
                source_sha256=data['source_sha256'], baseline_sha256=baseline['source_sha256'],
                narrative_mode='deterministic_fact_template', model_calls=0,
                source_differences=dict(excluded=data.get('excluded_historical_conflicts',[]),active=data.get('active_small_differences',[])),
                limitations=data['limitations']+['No causal attribution, forecasts, or independently validated policy advice.',
                    'Replay evaluation, not a blind test: discovery search exposed reference headlines.'])


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--normalized',required=True)
    p.add_argument('--baseline',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    Path(a.out).write_text(json.dumps(compute(json.loads(Path(a.normalized).read_text()),
        json.loads(Path(a.baseline).read_text())),ensure_ascii=False,indent=2)+'\n')
