"""Bounded autonomous project improvement: diagnose, propose, replay, promote or rollback.

Current trusted repair: add missing, explicitly required descriptive business questions.
No arbitrary generated code, evaluator changes, metric edits or threshold relaxation.
"""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import uuid
import yaml
import project_manager as pm
import project_versions as pv
from periodic_analysis import validate_spec
from tuning_evaluation import load_suite, fingerprints, evaluate_case


def active_project(project: Path) -> Path:
    pointer=project.parent/'active-release.json'
    if not pointer.exists():return project
    v=json.loads(pointer.read_text());release=Path(v['release'])
    if pm.digest(release/'release.json')!=v['manifest_sha256']:raise ValueError('Active manifest changed')
    m=pv.validate_release(release)
    if m['project_id']!=pm.config(project)[0]['project_id']:raise ValueError('Active project mismatch')
    return release/'project/project.yaml'


def proposal(brief: dict, required: list) -> dict:
    existing={q['id']:q for q in brief['questions']};add=[]
    for q in required:
        if q['id'] in existing:
            if q!=existing[q['id']]:raise ValueError('Existing question conflict requires a reviewed adapter, not automatic rewriting')
        else:add.append(copy.deepcopy(q))
    candidate=copy.deepcopy(brief);candidate['questions']+=add;validate_spec(candidate)
    return dict(operator='add_required_questions',add_questions=add)


def copy_candidate(source: Path, out: Path, patch: dict, releases: Path) -> Path:
    cfg,_=pm.config(source);out.mkdir(parents=True,exist_ok=False)
    paths=set(cfg.get('resources',[]))|{s['script'] for s in cfg['pipeline']}
    for stage in cfg['pipeline']:paths.update(stage.get('cache',{}).get('resources',[]))
    for relative in paths:
        src=pm.inside(source.parent,relative);dst=pm.inside(out,relative);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    brief_path=out/'references/brief.json';brief=json.loads(brief_path.read_text());before=copy.deepcopy(brief)
    brief['questions']+=patch['add_questions'];validate_spec(brief)
    protected=lambda b:{k:v for k,v in b.items() if k!='questions'}
    if protected(brief)!=protected(before) or brief['questions'][:len(before['questions'])]!=before['questions']:raise ValueError('Protected contract changed')
    brief_path.write_text(json.dumps(brief,ensure_ascii=False,indent=2))
    nums=cfg['version'].split('.')
    if len(nums)!=3 or not all(n.isdigit() for n in nums):raise ValueError('Automatic tuning requires numeric semantic version')
    next_patch=int(nums[2])+1
    while (releases/cfg['project_id']/f'{nums[0]}.{nums[1]}.{next_patch}').exists():next_patch+=1
    cfg['version']=f'{nums[0]}.{nums[1]}.{next_patch}'
    target=out/'project.yaml';target.write_text(yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True));return target


def post_activation_check(project: Path, suite: dict, out: Path) -> dict:
    selected=active_project(project);brief=json.loads((selected.parent/'references/brief.json').read_text())
    # Replay all cases from the archive actually selected by the production pointer.
    results=[evaluate_case(selected,brief,suite,c,out/c['id']) for c in suite['cases']]
    if not all(r['passed'] for r in results):raise ValueError('Archived active release failed replay')
    return dict(passed=True,cases=results)


def tune(project: Path, suite_path: Path, workspace: Path, releases: Path) -> dict:
    project=project.resolve();suite_path=suite_path.resolve()
    lock=project.parent/'.tune.lock'
    with lock.open('x') as stream:json.dump(dict(pid=os.getpid()),stream)
    pointer=project.parent/'active-release.json'
    try:prior=pointer.read_bytes() if pointer.exists() else None
    except Exception:
        lock.unlink();raise
    episode=workspace.resolve()/('tune-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    try:episode.mkdir(parents=True,exist_ok=False)
    except Exception:
        lock.unlink();raise
    pm.save(lock,dict(pid=os.getpid(),episode=str(episode)))
    result=dict(status='running',episode=str(episode),project=str(project),scope='bounded descriptive-report configuration repair',evaluation_mode='Configured multi-period replay; holdout role is not a certified blind evaluation',baseline=[],candidate=[])
    activated=False;promoted_pointer=None
    try:
        selected=active_project(project);cfg,_=pm.config(selected)
        brief=json.loads((selected.parent/'references/brief.json').read_text());validate_spec(brief)
        # Restrict this operator to pinned quickstart projects, not arbitrary pipelines.
        trusted=Path(__file__).with_name('periodic_analysis.py')
        if pm.digest(selected.parent/'scripts/periodic_analysis.py')!=pm.digest(trusted):raise ValueError('Engine differs from trusted repair profile; adapter required')
        if cfg['inputs']!={'data':'file','period':'string'} or [s['id'] for s in cfg['pipeline']]!=['analyze','render','verify']:raise ValueError('Unsupported pipeline profile')
        for stage in cfg['pipeline']:
            expected=[stage['id'],'--spec','{project_dir}/references/brief.json','--data','{input:data}','--period','{input:period}','--out','{run_dir}']
            if stage['script']!='scripts/periodic_analysis.py' or stage['args']!=expected:raise ValueError('Unsupported pipeline adapter')
        suite=load_suite(suite_path,brief);before=fingerprints(suite_path,suite);code_before=pm.config(selected)[1]
        result['evaluation_fingerprints']=before;result['previous_pointer']=json.loads(prior) if prior else None
        (episode/'evaluation-lock.json').write_text(json.dumps(before,indent=2))
        # Proposal is based only on declared requirements, not oracle numeric answers.
        patch=proposal(brief,suite['required_questions']);result['proposal']=patch
        (episode/'proposal.json').write_text(json.dumps(patch,ensure_ascii=False,indent=2))
        for c in suite['cases']:
            result['baseline'].append(evaluate_case(selected,brief,suite,c,episode/'baseline'/c['id']))
        if fingerprints(suite_path,suite)!=before or pm.config(selected)[1]!=code_before:
            result.update(status='rejected',reason='Inputs or implementation changed during baseline');return result
        if not patch['add_questions']:
            result['status']='no_change' if all(r['passed'] for r in result['baseline']) else 'blocked'
            result['reason']='No supported automatic repair; keep selected version' if result['status']=='blocked' else 'All required questions already covered'
            return result
        candidate=copy_candidate(selected,episode/'candidate',patch,releases);new_brief=json.loads((candidate.parent/'references/brief.json').read_text())
        for c in suite['cases']:result['candidate'].append(evaluate_case(candidate,new_brief,suite,c,episode/'candidate-results'/c['id']))
        if not all(r['passed'] for r in result['candidate']):
            result.update(status='rejected',reason='Candidate did not pass every frozen case');return result
        if fingerprints(suite_path,suite)!=before or pm.config(selected)[1]!=code_before:
            result.update(status='rejected',reason='Input, oracle or selected implementation changed during evaluation');return result
        current=pointer.read_bytes() if pointer.exists() else None
        if current!=prior:raise ValueError('Active pointer changed concurrently; do not overwrite')
        final=Path(result['candidate'][-1]['run_dir']);delivery=json.loads((final/'delivery.json').read_text())
        acceptance=dict(status='passed',failures=[],artifacts=delivery['artifacts'],scope='All frozen numeric and required-question cases passed; not unrestricted analyst equivalence',evaluation_fingerprints=before)
        (final/'acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2))
        release=pv.freeze(candidate,final,releases,'Automatic required-question repair; every declared period passed independent numeric oracle and question checks; visual/causal generalization not certified')
        result['release']=str(release)
        # Save rollback information before changing the selected version.
        (episode/'promotion-intent.json').write_text(json.dumps(dict(project=str(project),previous=result['previous_pointer'],release=str(release),manifest_sha256=pm.digest(release/'release.json')),indent=2))
        pv.activate(project,release);activated=True;promoted_pointer=pointer.read_bytes()
        result['post_activation']=post_activation_check(project,suite,episode/'post-activation')
        if fingerprints(suite_path,suite)!=before:raise ValueError('Evaluation inputs changed after activation')
        result.update(status='promoted',version=pv.validate_release(release)['version'])
        return result
    except Exception as exc:
        if activated:
            if pointer.exists() and pointer.read_bytes()==promoted_pointer:
                if prior is None:pointer.unlink()
                else:pm.save(pointer,json.loads(prior))
                result.update(status='rolled_back',reason=str(exc))
            else:result.update(status='blocked',reason='Concurrent pointer change; rollback not applied: '+str(exc))
            return result
        result.update(status='blocked',reason=str(exc))
        raise
    finally:
        result['finished_at']=datetime.now(timezone.utc).isoformat()
        pm.save(episode/'result.json',result)
        lock.unlink()



def recover(project: Path, episode: Path) -> dict:
    project=project.resolve();episode=episode.resolve();lock=project.parent/'.tune.lock'
    owner=json.loads(lock.read_text())
    if owner.get('episode')!=str(episode):raise ValueError('Lock belongs to another episode')
    if type(owner.get('pid')) is not int or owner['pid']<=0:raise ValueError('Invalid lock owner')
    try:os.kill(owner['pid'],0)
    except ProcessLookupError:pass
    else:raise ValueError('Tuning owner is still alive; refuse recovery')
    if not (episode/'promotion-intent.json').exists():
        result=dict(status='recovered_rollback',episode=str(episode),reason='Interrupted before promotion; no pointer change to undo')
        pm.save(episode/'recovery.json',result);lock.unlink();return result
    intent=json.loads((episode/'promotion-intent.json').read_text())
    if intent['project']!=str(project):raise ValueError('Recovery project mismatch')
    pointer=project.parent/'active-release.json';current=json.loads(pointer.read_text()) if pointer.exists() else None
    expected=dict(release=intent['release'],manifest_sha256=intent['manifest_sha256'],version=json.loads((Path(intent['release'])/'release.json').read_text())['version'])
    previous=intent['previous']
    if current not in [expected,previous]:raise ValueError('Pointer changed after interrupted promotion')
    if previous:
        release=Path(previous['release']);pv.validate_release(release)
        if pm.digest(release/'release.json')!=previous['manifest_sha256']:raise ValueError('Rollback release changed')
    if current==expected:
        if previous is None:pointer.unlink()
        else:pm.save(pointer,previous)
    result=dict(status='recovered_rollback',episode=str(episode),previous=previous)
    pm.save(episode/'recovery.json',result);lock.unlink();return result


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--suite',type=Path)
    p.add_argument('--recover',type=Path)
    p.add_argument('--workspace',type=Path,default=pm.ROOT/'workspace/tuning')
    p.add_argument('--releases',type=Path,default=pm.ROOT/'releases')
    a=p.parse_args()
    if not a.recover and not a.suite:p.error('--suite or --recover required')
    try:result=recover(a.project,a.recover) if a.recover else tune(a.project,a.suite,a.workspace,a.releases)
    except (ValueError,OSError,KeyError,TypeError) as exc:p.exit(1,str(exc)+'\n')
    print(json.dumps({k:result[k] for k in ['status','episode']},ensure_ascii=False))
    if result['status'] not in ['promoted','no_change','recovered_rollback']:raise SystemExit(1)


if __name__=='__main__':main()
