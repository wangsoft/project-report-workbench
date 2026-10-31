"""Freeze project releases, select archived versions, and record evidence-linked feedback."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile
import uuid

import project_manager as pm


def checked_run(project: Path, run_dir: Path) -> dict:
    cfg, dependencies = pm.config(project)
    state = json.loads((run_dir/'run_state.json').read_text())
    if state['status'] != 'completed' or state['dependencies'] != dependencies:
        raise ValueError('Release requires a completed run of the current project/runtime')
    if state['project_config'] != str(project.resolve()):
        raise ValueError('Run belongs to a different project')
    for path, expected in state['input_hashes'].items():
        if pm.digest(path) != expected:
            raise ValueError('Run input changed')
    for record in state['stages']:
        for relative, expected in record['outputs'].items():
            if pm.digest(pm.inside(run_dir,relative)) != expected:
                raise ValueError('Run artifact changed')
    acceptance=json.loads((run_dir/'acceptance.json').read_text())
    if acceptance.get('status') != 'passed' or acceptance.get('failures') != [] or not acceptance.get('artifacts'):
        raise ValueError('Missing or failed executable acceptance')
    for relative, expected in acceptance['artifacts'].items():
        if pm.digest(pm.inside(run_dir,relative)) != expected:
            raise ValueError('Acceptance artifact changed')
    return state


def freeze(project: Path, run_dir: Path, releases: Path, scope: str) -> Path:
    if not scope.strip():
        raise ValueError('Explicit validated scope required')
    project=project.resolve();run_dir=run_dir.resolve()
    state=checked_run(project,run_dir)
    version=state['project_version']
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?',version):
        raise ValueError('Use a portable semantic version for releases')
    parent=releases.resolve()/state['project_id'];parent.mkdir(parents=True,exist_ok=True)
    target=parent/version
    if target.exists():
        raise FileExistsError('Release already exists; increment project version')
    temp=Path(tempfile.mkdtemp(prefix='.candidate-',dir=parent))
    try:
        # Snapshot only declared dependencies, plus project tests. Raw input data stays external.
        for filename in state['dependencies']:
            source=Path(filename)
            if source.is_relative_to(project.parent):
                dest=temp/'project'/source.relative_to(project.parent)
            elif source.is_relative_to(pm.ROOT):
                dest=temp/'runtime'/source.relative_to(pm.ROOT)
            else:
                raise ValueError('Dependency cannot be packaged')
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        for source in (project.parent/'tests').rglob('*.py'):
            dest=temp/'project'/source.relative_to(project.parent)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        evidence=temp/'evidence';evidence.mkdir()
        for name in ['acceptance.json','quality.json','visual-review.json']:
            source=run_dir/name
            if source.exists():shutil.copy2(source,evidence/name)
        hashes={str(p.relative_to(temp)):pm.digest(p) for p in temp.rglob('*') if p.is_file()}
        manifest=dict(schema_version=1,project_id=state['project_id'],version=version,
                      status='validated_for_scope',scope=scope,created_at=datetime.now(timezone.utc).isoformat(),
                      source_run=str(run_dir),source_inputs=state['input_hashes'],
                      interpreter=state['interpreter'],file_sha256=hashes,
                      limitation='Scope is supplied by the maintainer; no automated human-quality certification. Inputs and full environment are not bundled.')
        pm.save(temp/'release.json',manifest)
        temp.rename(target)
        return target
    finally:
        if temp.exists():shutil.rmtree(temp)


def validate_release(release: Path) -> dict:
    manifest=json.loads((release/'release.json').read_text())
    for relative, expected in manifest['file_sha256'].items():
        if pm.digest(pm.inside(release,relative)) != expected:
            raise ValueError('Archived release modified')
    return manifest


def activate(project: Path, release: Path) -> Path:
    cfg,_=pm.config(project)
    release=release.resolve();manifest=validate_release(release)
    if manifest['project_id']!=cfg['project_id']:
        raise ValueError('Release belongs to another project')
    pointer=project.parent/'active-release.json'
    pm.save(pointer,dict(release=str(release),manifest_sha256=pm.digest(release/'release.json'),
                        version=manifest['version']))
    return release/'project/project.yaml'


def feedback(project: Path, run_dir: Path, category: str, observation: str,
             action: str, evidence: str, target_version: str | None = None) -> Path:
    cfg,_=pm.config(project)
    state=json.loads((run_dir/'run_state.json').read_text())
    if state['project_id']!=cfg['project_id'] or Path(state['project_config']).resolve()!=project.resolve():
        raise ValueError('Feedback run belongs to another project')
    source=pm.inside(run_dir,evidence)
    if not source.is_file() or not observation.strip() or not action.strip():
        raise ValueError('Observation, proposed action and existing evidence are required')
    folder=project.parent/'feedback';folder.mkdir(exist_ok=True)
    identifier=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:10]
    record=dict(id=identifier,created_at=datetime.now(timezone.utc).isoformat(),project_id=cfg['project_id'],
                run_dir=str(run_dir.resolve()),project_version=state['project_version'],category=category,
                observation=observation,proposed_action=action,evidence_path=evidence,
                evidence_sha256=pm.digest(source),target_version=target_version,status='proposed')
    path=folder/(identifier+'.json')
    with path.open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2)
    return path


def resolve_feedback(project: Path, feedback_file: Path, release: Path, regression: Path) -> Path:
    cfg,_=pm.config(project);m=validate_release(release)
    original=json.loads(feedback_file.read_text());checks=json.loads(regression.read_text())
    if original['project_id']!=cfg['project_id'] or m['project_id']!=cfg['project_id']:
        raise ValueError('Project identity mismatch')
    if original.get('target_version') and original['target_version']!=m['version']:
        raise ValueError('Target version mismatch')
    if checks.get('status')!='passed' or checks.get('project_version')!=m['version']:
        raise ValueError('Passing regression for the release version required')
    # Link the exact archived implementation, not merely a matching version string.
    if checks.get('release_manifest_sha256')!=pm.digest(release/'release.json'):
        raise ValueError('Regression must bind the archived release manifest')
    path=feedback_file.with_name(feedback_file.stem+'.resolved.json')
    record=dict(feedback_id=original['id'],status='resolved',release=str(release.resolve()),
                regression=str(regression.resolve()),regression_sha256=pm.digest(regression),
                original_sha256=pm.digest(feedback_file))
    with path.open('x') as stream:json.dump(record,stream,ensure_ascii=False,indent=2)
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('release');r.add_argument('--project',type=Path,required=True)
    r.add_argument('--run-dir',type=Path,required=True);r.add_argument('--releases',type=Path,default=pm.ROOT/'releases')
    r.add_argument('--scope',required=True)
    a=sub.add_parser('activate');a.add_argument('--project',type=Path,required=True);a.add_argument('--release',type=Path,required=True)
    f=sub.add_parser('feedback');f.add_argument('--project',type=Path,required=True);f.add_argument('--run-dir',type=Path,required=True)
    f.add_argument('--category',choices=['data','calculation','analysis','visual','performance'],required=True)
    for name in ['observation','action','evidence']:f.add_argument('--'+name,required=True)
    f.add_argument('--target-version')
    x=sub.add_parser('resolve');x.add_argument('--project',type=Path,required=True)
    x.add_argument('--feedback-file',type=Path,required=True);x.add_argument('--release',type=Path,required=True)
    x.add_argument('--regression',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.cmd=='release':result=freeze(args.project,args.run_dir,args.releases,args.scope)
        elif args.cmd=='activate':result=activate(args.project,args.release)
        elif args.cmd=='resolve':result=resolve_feedback(args.project,args.feedback_file,args.release,args.regression)
        else:result=feedback(args.project,args.run_dir,args.category,args.observation,args.action,args.evidence,args.target_version)
        print(result)
    except (ValueError,OSError,KeyError,TypeError) as error:p.exit(1,f'Error: {error}\n')


if __name__=='__main__':main()
