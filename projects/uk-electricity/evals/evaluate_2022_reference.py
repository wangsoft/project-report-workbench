from pathlib import Path
import json, hashlib
root=Path(__file__).resolve().parents[3]
p=root/'workspace/public-fixtures/uk-electricity/2023-release'
freeze=json.loads((p/'generation-freeze.json').read_text());run=Path(freeze['run'])
assert all(hashlib.sha256((run/k).read_bytes()).hexdigest()==v for k,v in freeze['artifact_sha256'].items())
e=json.loads((run/'evidence.json').read_text());metrics={x['region']:x for x in e['metrics']};fuel={(x['region'],x['fuel']):x for x in e['fuel_metrics']};supply={x['region']:x for x in e['supply_metrics']}
# Manually transcribed from official text and visually inspected Appendix A.
# Expected values are independent of the frozen computed values.
gold={}
for region,total,growth,lc in [('UK Total',325,5.3,56.2),('England',234937,5.1,53.9),('Scotland',50300,5.3,86.8),('Wales',29713,6.5,26.8),('Northern Ireland',10307,6.7,44.3)]:
 gold[region,'current_gwh.total']=(total,0,1 if region=='UK Total' else 10,1000 if region=='UK Total' else 1)
 gold[region,'growth_pct.total']=(growth,1,1,1)
 gold[region,'shares_pct.low_carbon']=(lc,1,1,1)
for name,field,value,digits,page,divisor in [('fossil','growth',.9,1,2,1),('nuclear','gwh',47.7,1,4,1000),('nuclear','growth',4.,1,4,1),('renewables','gwh',135,0,2,1000),('renewables','growth',10,0,2,1),('wind','gwh',80.3,1,8,1000),('solar','growth',10.,1,8,1),('hydro','growth',4.5,1,8,1),('gas','gwh',125,0,4,1000),('gas','growth',1.5,1,4,1)]:gold['UK Total',name,field]=(value,digits,page,divisor)
rows=[]
for item in freeze['primary_numeric_registry']:
 region=item['region'];field=item['field'];name=item.get('fuel');key=(region,name,field) if name else (region,field)
 if name:actual=fuel[region,name][field]
 else:
  a,b=field.split('.');actual=metrics[region][a][b]
 row=dict(item,computed=actual)
 if key not in gold:row.update(status='not_stated',reason='Target does not explicitly state this exact UK metric; no inference from chart heights or foreign/regional figures.')
 else:
  expected,digits,page,divisor=gold[key];actual/=divisor;tol=.5*10**(-digits)
  row.update(actual=actual,official=expected,tolerance=tol,pdf_page=page,status='matched' if abs(actual-expected)<=tol+1e-9 else 'disagreed')
 rows.append(row)
extra=[]
def check(label,actual,expected,digits,page,note=''):
 tol=.5*10**(-digits);extra.append(dict(metric=label,actual=actual,official=expected,tolerance=tol,pdf_page=page,note=note,status='matched' if abs(actual-expected)<=tol+1e-9 else 'disagreed'))
check('UK consumption TWh',supply['UK Total']['values']['consumption']/1000,279,0,1)
check('UK consumption growth %',supply['UK Total']['consumption_growth'],-4.5,1,1)
check('UK net exports TWh',-supply['UK Total']['net_imports']/1000,5.3,1,1)
check('England gas growth %, first statement',fuel['England','gas']['growth'],-.5,1,1)
check('England gas growth %, later statement',fuel['England','gas']['growth'],-4.6,1,4,'Contradicts page 1 and frozen workbook calculation; retain both statements.')
check('Scotland nuclear growth %',fuel['Scotland','nuclear']['growth'],-45,0,4)
check('England nuclear growth %',fuel['England','nuclear']['growth'],27,0,4)
check('Scotland renewables growth %',fuel['Scotland','renewables']['growth'],30,0,1)
for region,val in [('England',226305),('Scotland',27310),('Wales',17271),('Northern Ireland',8205)]:check(region+' consumption GWh, Appendix A',supply[region]['values']['consumption'],val,0,10)
for region,val in [('England',72.2),('Scotland',15.5),('Wales',9.1),('Northern Ireland',3.2)]:check(region+' generation share %, body',metrics[region]['uk_share_pct'],val,1,2)
for region,val in [('England',72.5),('Scotland',15.6),('Wales',8.8),('Northern Ireland',3.2)]:check(region+' chart 2A supply share vs generation share',metrics[region]['uk_share_pct'],val,1,3,'Diagnostic comparison, not equivalent metrics: official caption says supply; generated table says generation. Do not classify mismatch as calculation error.')
result=dict(scope='Retrospective target-reference-delayed-reveal evaluation; historical-data exposure disclosed. Same generating agent performed review. Not strict temporal or independent blind test.',reference_sha256=hashlib.sha256((p/'reference.pdf').read_bytes()).hexdigest(),report_sha256=freeze['artifact_sha256']['report.pdf'],frozen_artifacts_unchanged=True,rounding_rule='half of last printed decimal unit; no post-hoc tolerance relaxation',primary_counts={s:sum(r['status']==s for r in rows) for s in ['matched','disagreed','not_stated']},primary_registry=rows,exploratory_checks=extra,exploratory_scope='Selected after reveal, kept separate from primary score. Chart 2A comparisons are definition diagnostics, excluded from accuracy scoring.')
(run/'target-reference-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'primary':result['primary_counts'],'exploratory_disagreements':[r for r in extra if r['status']=='disagreed']},ensure_ascii=False,indent=2))
assert len(rows)==33
assert result['primary_counts']=={'matched':25,'disagreed':0,'not_stated':8}
