"""Project configuration and conservative, fingerprint-checked pipeline execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

import yaml
import stage_cache

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z][a-z0-9_-]*\Z")
TOKEN = re.compile(r"\{([^{}]+)\}")


def digest(path):
    with Path(path).open('rb') as stream:
        result = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
        return result.hexdigest()


def inside(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError('Expected a relative path')
    path = (root / relative).resolve()
    if path == root.resolve() or not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes directory: {relative}')
    return path


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def config(path):
    path = Path(path).resolve()
    value = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise ValueError('Expected schema_version: 1')
    if not isinstance(value.get('project_id'), str) or not ID.fullmatch(value['project_id']):
        raise ValueError('Invalid project_id')
    if not isinstance(value.get('version'), str) or not value['version']:
        raise ValueError('version must be a nonempty string')
    if value.get('status') not in ('candidate', 'validated'):
        raise ValueError('status must be candidate or validated')
    inputs = value.get('inputs', {})
    if not isinstance(inputs, dict) or any(not isinstance(k, str) or not ID.fullmatch(k)
                                         or v not in ('file', 'string') for k, v in inputs.items()):
        raise ValueError('inputs must map names to file/string')
    resources = value.get('resources', [])
    stages = value.setdefault('pipeline', [])
    if not isinstance(resources, list) or not isinstance(stages, list):
        raise ValueError('resources and pipeline must be lists')
    dependencies = [path]
    dependencies.extend(inside(path.parent, p) for p in resources)
    ids, outputs = set(), set()
    prior_outputs = set()
    for stage in stages:
        if not isinstance(stage, dict) or not isinstance(stage.get('id'), str) or not ID.fullmatch(stage['id']):
            raise ValueError('Invalid stage id')
        if stage['id'] in ids:
            raise ValueError('Duplicate stage id')
        ids.add(stage['id'])
        stage_cache.validate(stage, inputs, path.parent, prior_outputs)
        prior_outputs.update(stage.get('outputs', []))
        if stage.get('cache'):
            dependencies.extend(inside(path.parent,r) for r in stage['cache']['resources'])
        script = inside(path.parent, stage.get('script'))
        if script.suffix != '.py':
            raise ValueError('Stage scripts must be Python files')
        dependencies.append(script)
        args = stage.get('args', [])
        if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
            raise ValueError('args must be a list of strings')
        allowed = {'run_dir', 'project_dir', 'project_config'} | {f'input:{k}' for k in inputs}
        for arg in args:
            if any(t not in allowed for t in TOKEN.findall(arg)):
                raise ValueError('Unknown argument placeholder')
        declared = stage.get('outputs')
        if not isinstance(declared, list) or not declared:
            raise ValueError('Each stage must declare output files')
        for output in declared:
            target = inside(Path('/run'), output).relative_to('/run').as_posix()
            if target.split('/')[0] in ('run_state.json', 'run_state.tmp', '.lock', 'logs'):
                raise ValueError('Reserved output path')
            if any(target == p or target.startswith(p + '/') or p.startswith(target + '/') for p in outputs):
                raise ValueError('Overlapping output paths')
            outputs.add(target)
        if type(stage.get('checkpoint', False)) is not bool:
            raise ValueError('checkpoint must be boolean')
        timeout = stage.get('timeout_seconds', 600)
        if type(timeout) not in (int, float) or not 0 < timeout <= 86400:
            raise ValueError('timeout_seconds must be in (0, 86400]')
    if any(not p.is_file() for p in dependencies):
        raise ValueError('Missing script or declared resource')
    # Shared helpers and interpreter identity are part of the conservative fingerprint.
    dependencies.extend(sorted((ROOT / 'scripts').glob('*.py')))
    dependencies.append(ROOT / 'config/requirements.txt')
    return value, {str(p): digest(p) for p in dependencies}


def initialize(project_id, projects):
    if not ID.fullmatch(project_id):
        raise ValueError('Invalid project id')
    target = Path(projects).resolve() / project_id
    target.mkdir(parents=True, exist_ok=False)
    value = dict(schema_version=1, project_id=project_id, version='0.1.0', status='candidate',
                 inputs={}, resources=[], pipeline=[])
    (target / 'project.yaml').write_text(yaml.safe_dump(value, sort_keys=False), encoding='utf-8')
    return target / 'project.yaml'


def execute(run_dir, acknowledge=None):
    run_dir = Path(run_dir).resolve()
    lock = run_dir / '.lock'
    with lock.open('x'):
        pass
    try:
        state = json.loads((run_dir / 'run_state.json').read_text())
        cfg, fingerprints = config(state['project_config'])
        if fingerprints != state['dependencies'] or state['interpreter'] != [sys.executable, sys.version]:
            raise ValueError('Configuration/code/runtime changed; create a new run')
        for path, expected in state['input_hashes'].items():
            if digest(path) != expected:
                raise ValueError('Input changed; create a new run')
        for record in state['stages']:
            if record['status'] == 'completed':
                for relative, expected in record['outputs'].items():
                    if digest(inside(run_dir, relative)) != expected:
                        raise ValueError('Completed output changed; create a new run')
        if state['status'] == 'completed':
            return state
        if state['status'] == 'waiting':
            if acknowledge != state['waiting_for']:
                raise ValueError('Resume requires --acknowledge ' + state['waiting_for'])
            state['acknowledgements'].append(acknowledge)
            state.pop('waiting_for')
        replacements = {'run_dir': str(run_dir), 'project_dir': str(Path(state['project_config']).parent),
                        'project_config': state['project_config']}
        replacements.update({f'input:{k}': v for k, v in state['inputs'].items()})
        for index, stage in enumerate(cfg['pipeline']):
            record = state['stages'][index]
            if record['status'] == 'completed':
                continue
            paths = [inside(run_dir, p) for p in stage['outputs']]
            if any(p.exists() for p in paths):
                raise ValueError('Unverified partial output exists; create a new run')
            state['status'] = record['status'] = 'running'
            save(run_dir / 'run_state.json', state)
            args = [TOKEN.sub(lambda m: replacements[m[1]], a) for a in stage.get('args', [])]
            command = [sys.executable, str(inside(Path(state['project_config']).parent, stage['script'])), *args]
            start = time.perf_counter()
            try:
                cache_key = stage_cache.key_for(stage, cfg, state, run_dir) if stage.get('cache') and state.get('cache_dir') else None
                hit = bool(cache_key and stage_cache.restore(Path(state['cache_dir']), cache_key, run_dir, stage['outputs']))
                record['cache'] = 'hit' if hit else ('miss' if cache_key else 'disabled')
                record['cache_key'] = cache_key
                if not hit:
                    with (run_dir / 'logs' / (stage['id'] + '.log')).open('ab') as log:
                        result = subprocess.run(command, cwd=run_dir, stdout=log, stderr=subprocess.STDOUT,
                                                timeout=stage.get('timeout_seconds', 600), check=False)
                    if result.returncode:
                        raise ValueError(f'Stage {stage["id"]} exited {result.returncode}')
                if any(not p.is_file() for p in paths):
                    raise ValueError('Stage did not produce all declared outputs')
                record['outputs'] = {p: digest(inside(run_dir, p)) for p in stage['outputs']}
                record['status'] = 'completed'
                record.pop('error', None)
            except Exception as error:
                record['status'] = state['status'] = 'failed'
                record['error'] = str(error)
                raise
            finally:
                record['seconds'] = time.perf_counter() - start
                save(run_dir / 'run_state.json', state)
            if stage.get('checkpoint', False):
                state.update(status='waiting', waiting_for=stage['id'])
                save(run_dir / 'run_state.json', state)
                return state
        # Never promote partial/failed pipelines into the cache; detect downstream mutation.
        for stage, record in zip(cfg['pipeline'],state['stages']):
            for relative, expected in record['outputs'].items():
                if digest(inside(run_dir,relative)) != expected:
                    state['status'] = 'failed'
                    save(run_dir / 'run_state.json',state)
                    raise ValueError('A downstream stage modified an earlier output')
        if config(state['project_config'])[1] != state['dependencies'] or any(digest(p)!=h for p,h in state['input_hashes'].items()):
            state['status'] = 'failed'
            save(run_dir / 'run_state.json',state)
            raise ValueError('Dependencies changed during execution')
        for stage, record in zip(cfg['pipeline'],state['stages']):
            if record.get('cache_key'):
                stage_cache.publish(Path(state['cache_dir']),record['cache_key'],run_dir,stage['outputs'])
        state['status'] = 'completed'
        save(run_dir / 'run_state.json', state)
        return state
    finally:
        lock.unlink()


def run(project, inputs_file, workspace, cache_dir=None):
    project = Path(project).resolve()
    cfg, dependencies = config(project)
    if not cfg['pipeline']:
        raise ValueError('Candidate has no executable pipeline')
    inputs_file = Path(inputs_file).resolve()
    inputs = json.loads(inputs_file.read_text(encoding='utf-8'))
    if not isinstance(inputs, dict) or inputs.keys() != cfg.get('inputs', {}).keys():
        raise ValueError('Input names must match the project configuration')
    hashes = {}
    for key, kind in cfg.get('inputs', {}).items():
        if not isinstance(inputs[key], str) or not inputs[key]:
            raise ValueError('Input values must be nonempty strings')
        if kind == 'file':
            path = (inputs_file.parent / inputs[key]).resolve()
            hashes[str(path)] = digest(path)
            inputs[key] = str(path)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
    run_dir = Path(workspace).resolve() / cfg['project_id'] / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / 'logs').mkdir()
    state = dict(project_config=str(project), project_id=cfg['project_id'], project_version=cfg['version'],
                 config_snapshot=cfg, dependencies=dependencies, interpreter=[sys.executable, sys.version],
                 inputs=inputs, input_hashes=hashes, status='ready', acknowledgements=[],
                 cache_dir=str(Path(cache_dir).resolve()) if cache_dir else None,
                 stages=[dict(id=s['id'], status='pending', outputs={}) for s in cfg['pipeline']])
    save(run_dir / 'run_state.json', state)
    print(run_dir, flush=True)
    execute(run_dir)
    return run_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('project_id')
    init.add_argument('--projects', default=ROOT / 'projects')
    listing = sub.add_parser('list')
    listing.add_argument('--projects', default=ROOT / 'projects')
    validate = sub.add_parser('validate')
    validate.add_argument('--project', required=True)
    running = sub.add_parser('run')
    running.add_argument('--project', required=True)
    running.add_argument('--inputs', required=True)
    running.add_argument('--cache-dir', help='Opt-in deterministic stage cache; quality stages always execute')
    running.add_argument('--active', action='store_true', help='Use the verified archived release selected for this project')
    running.add_argument('--workspace', default=ROOT / 'workspace')
    resume = sub.add_parser('resume')
    resume.add_argument('--run-dir', required=True)
    resume.add_argument('--acknowledge')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            print(initialize(args.project_id, args.projects))
        elif args.command == 'list':
            for p in sorted(Path(args.projects).glob('*/project.yaml')):
                print(p)
        elif args.command == 'validate':
            cfg, _ = config(args.project)
            print(json.dumps(dict(project_id=cfg['project_id'], stages=len(cfg['pipeline']),
                                  business_validation='not checked')))
        elif args.command == 'run':
            project = args.project
            if args.active:
                from project_versions import validate_release
                pointer = json.loads((Path(project).resolve().parent / 'active-release.json').read_text())
                release = Path(pointer['release'])
                if digest(release/'release.json') != pointer['manifest_sha256']:
                    raise ValueError('Active release manifest changed')
                manifest = validate_release(release)
                if manifest['project_id'] != config(project)[0]['project_id']:
                    raise ValueError('Active release project mismatch')
                project = release/'project/project.yaml'
            run(project, args.inputs, args.workspace, args.cache_dir)
        else:
            print(execute(args.run_dir, args.acknowledge)['status'])
    except (ValueError, OSError, KeyError, TypeError, yaml.YAMLError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
