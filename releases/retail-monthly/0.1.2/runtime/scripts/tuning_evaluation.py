"""Protected multi-period oracle, separate from report generation and candidate proposal."""
import json
import os
import signal
import subprocess
import sys
import math
from pathlib import Path
import time
import project_manager as pm
from periodic_analysis import validate_spec


def load_suite(path: Path, brief: dict) -> dict:
    suite=json.loads(path.read_text())
    if suite.get('schema_version')!=1 or suite.get('project_id')!=brief['project_id']:raise ValueError('Suite/project mismatch')
    trial=dict(brief,questions=suite.get('required_questions',[]));validate_spec(trial)
    tolerance=suite.get('absolute_tolerance')
    if type(tolerance) not in (int,float) or not math.isfinite(tolerance) or not 0<=tolerance<=.01:raise ValueError('Explicit absolute tolerance in [0,.01] required')
    budget=suite.get('max_case_seconds')
    if type(budget) not in (int,float) or not math.isfinite(budget) or not 0<budget<=300:raise ValueError('Case time budget required')
    cases=suite.get('cases',[])
    if not 3<=len(cases)<=12 or {c.get('role') for c in cases}!={'development','regression','holdout'}:raise ValueError('Need development, regression and holdout cases (3..12)')
    if len({c['id'] for c in cases})!=len(cases) or len({c['period'] for c in cases})!=len(cases):raise ValueError('Unique cases and distinct reporting periods required')
    mids={m['id'] for m in brief['metrics']}
    for c in cases:
        for check in c.get('report_checks',[]):
            if check.get('artifact') not in {'report.md','report.html'} or set(check)!={'artifact','contains'} or not isinstance(check['contains'],str) or not check['contains'].strip():raise ValueError('Invalid report assertion')
        if not pm.ID.fullmatch(c.get('id','')):raise ValueError('Invalid case id')
        if c['period'] not in brief['periods'][1:]:raise ValueError('Case outside declared comparison periods')
        c['data']=str((path.parent/c['data']).resolve())
        if not Path(c['data']).is_file():raise ValueError('Missing case data')
        if set(c.get('expected',{}))!=mids:raise ValueError('Oracle must cover every declared metric')
        for expected in c['expected'].values():
            if set(expected)!={'current','previous','delta','growth_pct'}:raise ValueError('Oracle requires total, baseline, delta and growth')
            for k,v in expected.items():
                if v is None and k=='growth_pct':continue
                if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('Nonfinite oracle')
            if abs(expected['current']-expected['previous']-expected['delta'])>tolerance:raise ValueError('Inconsistent oracle delta')
            growth=expected['delta']/expected['previous']*100 if expected['previous']>0 else None
            if (growth is None)!=(expected['growth_pct'] is None) or growth is not None and abs(growth-expected['growth_pct'])>tolerance:raise ValueError('Inconsistent oracle growth')
    return suite


def fingerprints(suite_path: Path, suite: dict) -> dict:
    return {str(p):pm.digest(p) for p in [suite_path]+[Path(c['data']) for c in suite['cases']]}


def evaluate_case(project: Path, brief: dict, suite: dict, case: dict, out: Path) -> dict:
    out.mkdir(parents=True,exist_ok=True)
    inputs=out/'inputs.json';inputs.write_text(json.dumps(dict(data=case['data'],period=case['period'])))
    start=time.perf_counter();failures=[];run_dir=None;missing=[];facts_ok=False
    try:
        command=[sys.executable,str(Path(pm.__file__)), 'run','--project',str(project),'--inputs',str(inputs),'--workspace',str(out/'runs')]
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=os.name=='posix')
        try:
            output,_=process.communicate(timeout=suite['max_case_seconds'])
        except subprocess.TimeoutExpired:
            if os.name=='posix':os.killpg(process.pid,signal.SIGKILL)
            else:process.kill()
            output,_=process.communicate();(out/'runner.log').write_text(output)
            raise ValueError('Case exceeded execution deadline') from None
        (out/'runner.log').write_text(output)
        if process.returncode:raise ValueError('Pipeline failed; see runner.log')
        candidates=list((out/'runs'/brief['project_id']).glob('*/run_state.json'))
        if len(candidates)!=1:raise ValueError('Expected exactly one case run')
        run_dir=candidates[0].parent
        delivery=json.loads((run_dir/'delivery.json').read_text())
        if delivery.get('status')!='ready_within_scope' or delivery.get('failures'):failures.append('pipeline delivery gate')
        if delivery.get('scope')!=brief['scope']:failures.append('scope changed')
        for relative,h in delivery.get('artifacts',{}).items():
            if pm.digest(pm.inside(run_dir,relative))!=h:failures.append('artifact changed')
        e=json.loads((run_dir/'evidence.json').read_text());metrics={m['id']:m for m in e['metrics']}
        if e.get('source_sha256')!=pm.digest(Path(case['data'])):failures.append('source identity')
        facts_ok=True
        for metric,expected in case['expected'].items():
            for key,value in expected.items():
                actual=metrics[metric][key]
                ok=actual is None if value is None else type(actual) in (int,float) and math.isfinite(actual) and abs(actual-value)<=suite['absolute_tolerance']
                if not ok:failures.append(f'oracle {metric}.{key}');facts_ok=False
        answer_list=json.loads((run_dir/'answers.json').read_text());answers={a['id']:a for a in answer_list}
        if len(answers)!=len(answer_list):failures.append('duplicate answers')
        report=(run_dir/'report.md').read_text()
        for q in suite['required_questions']:
            a=answers.get(q['id'])
            if not a:missing.append(q['id']);continue
            if any(a.get(k)!=q[k] for k in ['metric','kind','title']) or not a.get('text') or a['text'] not in report:failures.append('answer contract '+q['id'])
        if missing:failures.append('missing required questions')
        for check in case.get('report_checks',[]):
            if check['contains'] not in (run_dir/check['artifact']).read_text():failures.append('report assertion: '+check['contains'])
    except (OSError,ValueError,KeyError,TypeError) as exc:failures.append(str(exc))
    seconds=time.perf_counter()-start
    if seconds>suite['max_case_seconds']:failures.append('latency budget')
    result=dict(id=case['id'],role=case['role'],period=case['period'],passed=not failures,
                facts_passed=facts_ok,missing_questions=missing,failures=failures,seconds=seconds,
                run_dir=str(run_dir) if run_dir else None)
    (out/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));return result
