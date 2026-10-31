"""Measure cold/warm/no-cache execution and dependency invalidation on isolated copies."""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import statistics
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import project_manager as pm
from openpyxl import load_workbook


def revised_workbook(source, dest):
    # Synthetic historical correction; never modify the official workbook.
    wb=load_workbook(source,read_only=True,data_only=True);changes={}
    for index,sheet_name in enumerate(wb.sheetnames,1):
        if sheet_name not in ['Generation and supply','Electricity generation by fuel']:continue
        sheet=wb[sheet_name];rows=list(sheet.iter_rows())
        header=rows[3] if sheet_name=='Generation and supply' else rows[4]
        cols=[c.column for c in header if c.value in ['2023 UK Total','2023 England']]
        chosen=[]
        for row in rows:
            if sheet_name=='Generation and supply':
                include=row[0].value=='Total electricity generated'
            else:
                include=row[0].value=='All generating companies' and row[1].value in ['Total all generating companies','Fossil fuels [Note 5]','Gas']
            if include:
                for col in cols:chosen.append(row[col-1])
        changes[f'xl/worksheets/sheet{index}.xml']={c.coordinate:c.value+1000 for c in chosen}
    wb.close();ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(source) as old,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as new:
        for item in old.infolist():
            data=old.read(item.filename)
            if item.filename in changes:
                tree=ET.fromstring(data)
                for cell in tree.findall('.//s:c',ns):
                    if cell.get('r') in changes[item.filename]:cell.find('s:v',ns).text=str(changes[item.filename][cell.get('r')])
                data=ET.tostring(tree,encoding='utf-8')
            new.writestr(item,data)


def benchmark(project, inputs, output):
    output.mkdir(parents=True,exist_ok=False)
    copied=output/'project';shutil.copytree(project.parent,copied,ignore=shutil.ignore_patterns('__pycache__','feedback'))
    cfg=copied/'project.yaml';parameters=json.loads(inputs.read_text())
    original_cfg,_=pm.config(project)
    for name,kind in original_cfg['inputs'].items():
        if kind=='file':parameters[name]=str((inputs.parent/parameters[name]).resolve())
    inp=output/'inputs.json';pm.save(inp,parameters);results=[]
    def run(label,cache):
        start=time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):folder=pm.run(cfg,inp,output/'runs',cache)
        elapsed=time.perf_counter()-start
        state=json.loads((folder/'run_state.json').read_text())
        result=dict(scenario=label,seconds=elapsed,run=str(folder),
                    stages={s['id']:dict(cache=s['cache'],seconds=s['seconds']) for s in state['stages']},
                    evidence_sha256=pm.digest(folder/'evidence.json'),pdf_sha256=pm.digest(folder/'report.pdf'),
                    acceptance=json.loads((folder/'acceptance.json').read_text())['status'])
        results.append(result);return result
    for i in range(3):run('cold',output/f'cold-cache-{i}')
    for i in range(3):run('warm',output/'cold-cache-0')
    for i in range(3):run('uncached',None)
    base=results[0]
    if not all(r['evidence_sha256']==base['evidence_sha256'] and r['pdf_sha256']==base['pdf_sha256'] for r in results):
        raise ValueError('Repeated/cached outputs differ')
    style=copied/'templates/style.json';original_style=style.read_bytes()
    changed=json.loads(original_style);changed['accent']='#24563B';pm.save(style,changed)
    style_result=run('style-change',output/'cold-cache-0')
    assert style_result['stages']['normalize']['cache']=='hit'
    assert style_result['stages']['compute']['cache']=='hit'
    assert style_result['stages']['render']['cache']=='miss'
    assert style_result['evidence_sha256']==base['evidence_sha256']
    style.write_bytes(original_style)
    revised=output/'synthetic-revised.xlsx';revised_workbook(Path(parameters['data']),revised)
    parameters['data']=str(revised.resolve());pm.save(inp,parameters)
    revision=run('historical-revision',output/'cold-cache-0')
    full=run('historical-revision-uncached',None)
    assert revision['evidence_sha256']==full['evidence_sha256']
    assert revision['pdf_sha256']==full['pdf_sha256']
    assert revision['evidence_sha256']!=base['evidence_sha256']
    assert all(revision['stages'][s]['cache']=='miss' for s in ['normalize','compute','render'])
    assert all(r['stages'][s]['cache']=='disabled' for r in results for s in ['check','verify'])
    medians={name:statistics.median(r['seconds'] for r in results if r['scenario']==name) for name in ['cold','warm','uncached']}
    report=dict(status='passed',scope='Fifteen-page full-topic candidate PDF with supplied external context/map; includes numeric and PDF gates, excludes external evidence research, human/agent review and initial build.',
                medians_seconds=medians,warm_vs_uncached_speedup=medians['uncached']/medians['warm'],
                model_calls=0,model_tokens=None,peak_memory=None,runs=results,
                checks=['cached/uncached evidence and PDF byte-equivalence','style-only compute reuse',
                        'synthetic historical revision invalidation and full-recompute equivalence','quality stages always execute'])
    pm.save(output/'benchmark.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(benchmark(a.project.resolve(),a.inputs.resolve(),a.out.resolve())['medians_seconds']))
