"""Pinned, deterministic reports for explicitly mapped periodic additive tables."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
from html import escape
import json
from pathlib import Path
import re

ID = re.compile(r'[a-z][a-z0-9_-]*\Z')
KINDS = {'change', 'drivers', 'exceptions'}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_spec(spec: dict) -> None:
    if spec.get('schema_version') != 1 or spec.get('scope') != 'descriptive_periodic':
        raise ValueError('Supported scope: descriptive_periodic, schema_version 1')
    if not ID.fullmatch(spec.get('project_id','')):
        raise ValueError('Invalid project_id')
    for k in ['title','audience','period_column','entity_column']:
        if not isinstance(spec.get(k),str) or not spec[k].strip():raise ValueError('Missing '+k)
    if spec['period_column']==spec['entity_column']:raise ValueError('Distinct grain columns required')
    for k in ['periods','entities']:
        v=spec.get(k)
        if not isinstance(v,list) or not v or any(not isinstance(x,str) or not x.strip() for x in v) or len(set(v))!=len(v):
            raise ValueError('Explicit unique '+k+' required')
    if len(spec['periods'])<2:raise ValueError('At least two ordered periods required')
    metrics=spec.get('metrics',[]);ids=set();columns=set()
    if not metrics:raise ValueError('No metrics')
    for m in metrics:
        if not ID.fullmatch(m.get('id','')) or m['id'] in ids:raise ValueError('Invalid/duplicate metric')
        ids.add(m['id'])
        for k in ['column','label','unit']:
            if not isinstance(m.get(k),str) or not m[k].strip():raise ValueError('Missing metric '+k)
        if m['column'] in columns or m['column'] in [spec['period_column'],spec['entity_column']]:raise ValueError('Duplicate metric column')
        columns.add(m['column'])
        if m.get('aggregation')!='sum' or m.get('direction') not in ['higher','lower','neutral']:
            raise ValueError('Explicit sum aggregation and direction required; ratios need a domain adapter')
    questions=spec.get('questions',[]);qids=set()
    if not questions:raise ValueError('No business questions')
    for q in questions:
        if not ID.fullmatch(q.get('id','')) or q['id'] in qids:raise ValueError('Invalid/duplicate question')
        qids.add(q['id'])
        if q.get('kind') not in KINDS or q.get('metric') not in ids or not q.get('title'):
            raise ValueError('Unsupported question or metric; causal explanations require a sourced project adapter')


def read_rows(path: Path, spec: dict) -> tuple[list, list]:
    if path.suffix.lower()=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.reader(f))
    elif path.suffix.lower() in ['.xlsx','.xlsm']:
        from openpyxl import load_workbook
        book=load_workbook(path,read_only=True,data_only=False)
        try:
            sheet=spec.get('sheet')
            if not sheet or sheet not in book.sheetnames:raise ValueError('Explicit Excel sheet required')
            rows=list(book[sheet].values)
        finally:book.close()
    else:raise ValueError('Use CSV/XLSX/XLSM with one header row')
    if not rows:raise ValueError('Empty input')
    headers=list(rows[0])
    if any(not isinstance(h,str) or not h for h in headers) or len(set(headers))!=len(headers):
        raise ValueError('Blank/duplicate header')
    required=[spec['period_column'],spec['entity_column']]+[m['column'] for m in spec['metrics']]
    if not set(required)<=set(headers):raise ValueError('Missing mapped columns')
    return headers,rows[1:]


def analyze(path: Path, spec: dict, period: str) -> dict:
    validate_spec(spec)
    if period not in spec['periods'] or spec['periods'].index(period)==0:raise ValueError('Comparison period unavailable')
    previous=spec['periods'][spec['periods'].index(period)-1]
    headers,rows=read_rows(path,spec);records={};ignored=0
    for number,row in enumerate(rows,2):
        if all(v is None or v=='' for v in row):continue
        if len(row)!=len(headers):raise ValueError(f'Ragged row {number}')
        record=dict(zip(headers,row));p=str(record[spec['period_column']]);entity=str(record[spec['entity_column']])
        if p not in [period,previous]:ignored+=1;continue
        if entity not in spec['entities']:raise ValueError(f'Unexpected entity {entity}')
        key=(p,entity)
        if key in records:raise ValueError(f'duplicate grain at row {number}')
        values={}
        for m in spec['metrics']:
            try:value=Decimal(str(record[m['column']]))
            except InvalidOperation:raise ValueError(f'Invalid number at row {number}, {m["column"]}') from None
            if not value.is_finite():raise ValueError('Nonfinite value')
            values[m['id']]=value
        records[key]=(values,number)
    expected={(p,g) for p in [period,previous] for g in spec['entities']}
    if set(records)!=expected:raise ValueError('Incomplete entity/period coverage; missing values are not zero')
    result=[]
    for m in spec['metrics']:
        mid=m['id'];prior=sum(records[previous,g][0][mid] for g in spec['entities']);cur=sum(records[period,g][0][mid] for g in spec['entities']);delta=cur-prior
        # Percentage growth is not economically comparable for zero/negative baselines.
        growth=delta/prior*100 if prior>0 else None;drivers=[]
        for g in spec['entities']:
            a,n=records[period,g];b,pn=records[previous,g];d=a[mid]-b[mid]
            drivers.append(dict(entity=g,current=float(a[mid]),previous=float(b[mid]),delta=float(d),
                contribution_pp=float(d/prior*100) if prior>0 else None,
                source=dict(column=m['column'],current_row=n,previous_row=pn)))
        drivers.sort(key=lambda d:(-abs(d['delta']),d['entity']))
        result.append(dict(id=mid,label=m['label'],unit=m['unit'],direction=m['direction'],current=float(cur),previous=float(prior),delta=float(delta),
            growth_pct=float(growth) if growth is not None else None,drivers=drivers,
            opposite_direction=[d for d in drivers if d['delta']*float(delta)<0],
            movements_when_flat=[d for d in drivers if d['delta']!=0] if delta==0 else []))
    evidence=dict(schema_version=1,scope=spec['scope'],period=period,previous_period=previous,
        source_sha256=digest(path),spec_sha256=hashlib.sha256(json.dumps(spec,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
        grain='one row per declared period and entity',ignored_other_period_rows=ignored,metrics=result)
    if any(not Decimal(str(v)).is_finite() for m in result for v in [m['current'],m['previous'],m['delta']]):
        raise ValueError('Values exceed supported numeric range')
    try:json.dumps(evidence,allow_nan=False)
    except ValueError:raise ValueError('Values exceed supported numeric range') from None
    return evidence


def number(value: float | None) -> str:
    return '不适用（基期非正）' if value is None else f'{value:,.2f}'


def answers(e: dict, spec: dict) -> list[dict]:
    metrics={m['id']:m for m in e['metrics']};out=[]
    for q in spec['questions']:
        m=metrics[q['metric']];unit=m['unit']
        if q['kind']=='change':
            assessment=('符合' if (m['delta']>0)==(m['direction']=='higher') else '偏离')+'既定指标方向' if m['delta'] and m['direction']!='neutral' else '不作优劣判断'
            text=f"{m['label']}为 {number(m['current'])} {unit}，较上期变化 {number(m['delta'])} {unit}，增幅 {number(m['growth_pct'])}%。{assessment}。"
        elif q['kind']=='drivers':
            text='；'.join(f"{d['entity']}：变化 {number(d['delta'])} {unit}，贡献 {number(d['contribution_pp'])} 个百分点" for d in m['drivers'])+'。这是可加的数值分解，不是原因识别。'
        else:
            opposite=m['opposite_direction'];flat=m['movements_when_flat']
            text=('与总体方向相反：'+ '；'.join(f"{d['entity']}变化 {number(d['delta'])} {unit}" for d in opposite)) if opposite else ('总量不变但内部有对冲：'+ '；'.join(f"{d['entity']}变化 {number(d['delta'])} {unit}" for d in flat) if flat else '没有与总体方向相反的地区变化。')
        out.append(dict(id=q['id'],title=q['title'],metric=q['metric'],kind=q['kind'],text=text))
    return out


def joint_insight(e: dict) -> dict:
    """Project adapter compiled from the joint-performance experience card."""
    memory=Path(__file__).resolve().parents[1]/'references/experience.json'
    cards=json.loads(memory.read_text())
    if not any(c['id']=='joint-performance' for c in cards):raise ValueError('Missing compiled experience rule')
    metrics={m['id']:m for m in e['metrics']};revenue=metrics['revenue'];profit=metrics['profit']
    if revenue['unit']!=profit['unit']:raise ValueError('Margin needs comparable monetary units')
    rd,pd=revenue['delta'],profit['delta']
    if rd>0 and pd<0:direction='收入增长而利润下降'
    elif rd<0 and pd>0:direction='收入下降而利润增长'
    elif rd>0 and pd>0:direction='收入与利润同向增长'
    elif rd<0 and pd<0:direction='收入与利润同向下降'
    else:direction='收入或利润存在持平，需要分别观察'
    current=Decimal(str(profit['current']))/Decimal(str(revenue['current']))*100 if revenue['current']>0 else None
    previous=Decimal(str(profit['previous']))/Decimal(str(revenue['previous']))*100 if revenue['previous']>0 else None
    delta=current-previous if current is not None and previous is not None else None
    margin=(f'本期利润率为 {current:.2f}%，较上期变化 {delta:.2f} 个百分点' if delta is not None else '收入非正的期间不解释利润率，无法作可比的利润率变化判断')
    text=direction+'。'+margin+'。口径为同一期间、对象与单位下的总利润/总收入，不是地区利润率的平均值。仅描述数值关系，不能据此认定成本、价格或产品结构原因。'
    return dict(rule_id='joint-performance',memory_sha256=digest(memory),metrics=['revenue','profit'],
        current_margin_pct=float(current) if current is not None else None,
        previous_margin_pct=float(previous) if previous is not None else None,
        margin_delta_pp=float(delta) if delta is not None else None,text=text)


def documents(e: dict, spec: dict) -> tuple[str,str]:
    a=answers(e,spec);title=f"{spec['title']} · {e['period']}"
    md=f"# {title}\n\n面向：{spec['audience']}。比较期：{e['previous_period']}。\n\n"
    insight=joint_insight(e)
    md+='## 规模与利润率综合\n\n'+insight['text']+'\n\n'
    parts=['<section><h2>规模与利润率综合</h2><p>'+escape(insight['text'])+'</p></section>']
    for item in a:
        md+=f"## {item['title']}\n\n{item['text']}\n\n"
        parts.append(f'<section id="{item["id"]}"><h2>{escape(item["title"])}</h2><p>{escape(item["text"])}</p></section>')
    tables=[]
    for m in e['metrics']:
        rows=''.join('<tr>'+''.join(f'<td>{escape(str(v))}</td>' for v in [d['entity'],number(d['previous']),number(d['current']),number(d['delta']),number(d['contribution_pp'])])+'</tr>' for d in m['drivers'])
        tables.append(f'<h2>{escape(m["label"])}（{escape(m["unit"])}）</h2><table><tr><th>地区/对象</th><th>上期</th><th>本期</th><th>变化</th><th>贡献 pp</th></tr>{rows}</table>')
    boundary='交付范围：已声明对象、相邻期间和可加指标的描述性分析。未进行因果解释、预测或经营行动建议；这些问题需要额外证据与项目适配。'
    md+=boundary+'\n\n数据 SHA256：'+e['source_sha256']+'\n'
    html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(title)+'</title><style>body{font:16px/1.8 system-ui,sans-serif;color:#182b44;max-width:980px;margin:48px auto;padding:0 24px}h1{font-size:32px;border-bottom:4px solid #234f85}h2{font-size:21px}section{margin:28px 0}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{text-align:left;padding:10px;border-bottom:1px solid #d8e0eb}th{background:#edf2f8}footer{font-size:12px;overflow-wrap:anywhere;color:#526275}@media print{body{margin:0}section,table{break-inside:avoid}}</style><h1>'+escape(title)+'</h1><p>面向：'+escape(spec['audience'])+'；比较期：'+escape(e['previous_period'])+'</p>'+''.join(parts+tables)+'<footer>'+escape(boundary)+'<p>数据 SHA256：'+e['source_sha256']+'</p></footer></html>'
    return md,html


def render(e: dict, spec: dict, out: Path) -> None:
    md,html=documents(e,spec);(out/'report.md').write_text(md);(out/'report.html').write_text(html)
    (out/'answers.json').write_text(json.dumps(answers(e,spec),ensure_ascii=False,indent=2))
    (out/'experience-applied.json').write_text(json.dumps(joint_insight(e),ensure_ascii=False,indent=2))


def verify(path: Path, spec: dict, period: str, out: Path) -> dict:
    expected=analyze(path,spec,period);actual=json.loads((out/'evidence.json').read_text());fail=[]
    if actual!=expected:fail.append('evidence differs from source recomputation')
    if json.loads((out/'experience-applied.json').read_text())!=joint_insight(expected):fail.append('experience result differs from verified evidence')
    md,html=documents(expected,spec)
    for name,text in [('report.md',md),('report.html',html)]:
        if (out/name).read_text()!=text:fail.append(name+' not bound to verified evidence/questions')
    if json.loads((out/'answers.json').read_text())!=answers(expected,spec):fail.append('question answers changed')
    return dict(status='blocked' if fail else 'ready_within_scope',scope=spec['scope'],failures=fail,
        answered_questions=[q['id'] for q in spec['questions']],source_sha256=expected['source_sha256'],
        artifacts={n:digest(out/n) for n in ['report.md','report.html','answers.json','evidence.json','experience-applied.json']},
        analyst_replacement='bounded descriptive assignment only; explanatory or predictive assignments unsupported',
        visual_review='not_automatically_certified')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['analyze','render','verify'])
    for k in ['spec','data','period','out']:p.add_argument('--'+k,required=True)
    a=p.parse_args();spec=json.loads(Path(a.spec).read_text());out=Path(a.out)
    if a.mode=='analyze':(out/'evidence.json').write_text(json.dumps(analyze(Path(a.data),spec,a.period),ensure_ascii=False,indent=2))
    elif a.mode=='render':render(json.loads((out/'evidence.json').read_text()),spec,out)
    else:
        result=verify(Path(a.data),spec,a.period,out);(out/'delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        if result['status']=='blocked':raise SystemExit(str(result['failures']))


if __name__=='__main__':main()
