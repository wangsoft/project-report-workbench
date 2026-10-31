"""Explicit chart definitions and evidence-bound answers for electricity reporting."""
import math

REGIONS=['England','Scotland','Wales','Northern Ireland']
NAMES=dict(zip(REGIONS,['英格兰','苏格兰','威尔士','北爱尔兰']))


def build(e: dict) -> dict:
    year=e['year'];years=list(range(year-4,year+1));regions=['UK Total']+REGIONS
    fuel={(r['year'],r['region']):r['values'] for r in e['fuel_detail']}
    sm={m['region']:m for m in e['supply_metrics']};fm={(m['region'],m['fuel']):m for m in e['fuel_metrics']}
    net={g:sm[g]['values']['generation']-sm[g]['values']['own_other']-sm[g]['values']['own_mpp'] for g in regions}
    if net['UK Total']<=0:raise ValueError('Net supply denominator must be positive')
    curve={g:[fuel[y,g]['renewables']/fuel[y,g]['total']*100 for y in years] for g in regions}
    nuclear='；'.join(f"{NAMES[g]}核电同比 {fm[g,'nuclear']['growth']:+.2f}%" for g in ['Scotland','England'])+'。'
    a,b=[fm[g,'nuclear']['growth'] for g in ['Scotland','England']]
    nuclear+=('两个地区方向相反，全国总量会掩盖这种分化。' if a*b<0 else '两个地区并未呈现相反方向，应结合各自基数比较。')
    renewable='；'.join(f"{NAMES[g]}可再生同比 {fm[g,'renewables']['growth']:+.2f}%" for g in REGIONS)+'。'
    record='可再生发电达到本工作簿公布历史序列最高。' if e['records_summary']['renewables']['maximum'] else '可再生发电未超过本工作簿历史最高值。'
    return dict(schema_version=1,year=year,charts={
        'supply_share':dict(metric='net_generation_share',unit='%',numerator='generation - own_other - own_mpp',denominator='UK generation - UK own_other - UK own_mpp',values={g:net[g]/net['UK Total']*100 for g in REGIONS},net_gwh=net),
        'renewable_share':dict(metric='renewable_generation_share',unit='%',numerator='renewables',denominator='total generation',years=years,series=curve)},
        answers=dict(regional_nuclear=nuclear,regional_renewables=renewable,renewable_record=record),
        scope='Evidence-bound chart definitions and descriptive answers; context is separately sourced')


def check(e: dict, s: dict) -> list[str]:
    failures=[];year=e['year'];regions=['UK Total']+REGIONS
    try:
        charts=s['charts'];c=charts['renewable_share'];supply=charts['supply_share']
        if c['metric']!='renewable_generation_share' or c['numerator']!='renewables' or c['denominator']!='total generation' or c['unit']!='%':failures.append('renewable chart definition')
        years=list(range(year-4,year+1))
        if c['years']!=years or set(c['series'])!=set(regions):failures.append('renewable chart coverage')
        lookup={(r['year'],r['region']):r['values'] for r in e['fuel_detail']}
        for g in regions:
            expected=[lookup[y,g]['renewables']/lookup[y,g]['total']*100 for y in years]
            if len(c['series'][g])!=5 or any(not math.isfinite(a) or abs(a-b)>1e-8 for a,b in zip(c['series'][g],expected)):failures.append('renewable chart values '+g)
        v={m['region']:m['values'] for m in e['supply_metrics']};net={g:v[g]['generation']-v[g]['own_other']-v[g]['own_mpp'] for g in regions}
        if supply['metric']!='net_generation_share' or set(supply['values'])!=set(REGIONS):failures.append('supply definition/coverage')
        for g in REGIONS:
            if not math.isfinite(supply['values'][g]) or abs(supply['values'][g]-net[g]/net['UK Total']*100)>1e-8:failures.append('supply denominator '+g)
        expected_answers=build(e)['answers']
        if s['answers']!=expected_answers:failures.append('missing or changed business answer')
    except (KeyError,TypeError,ValueError):failures.append('invalid semantic payload')
    return failures
