"""Opt-in file-artifact cache for deterministic, explicitly declared stage dependencies."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys
import tempfile


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def contained(root: Path, relative: str) -> Path:
    path=(root/relative).resolve()
    if path==root.resolve() or not path.is_relative_to(root.resolve()):raise ValueError('Cache path escape')
    return path


def validate(stage: dict, inputs: dict, project: Path, prior_outputs: set) -> None:
    declaration=stage.get('cache')
    if declaration is None:return
    if stage.get('role')=='quality':raise ValueError('Quality stages cannot be cached')
    if not isinstance(declaration,dict) or set(declaration)!={'inputs','resources','artifacts','packages'}:
        raise ValueError('cache requires explicit inputs/resources/artifacts/packages lists')
    for values in declaration.values():
        if not isinstance(values,list) or any(not isinstance(x,str) for x in values):raise ValueError('Cache dependencies must be string lists')
    if not set(declaration['inputs'])<=set(inputs):raise ValueError('Unknown cache input')
    if not set(declaration['artifacts'])<=prior_outputs:raise ValueError('Cache artifacts must be earlier stage outputs')
    for resource in declaration['resources']:
        if not contained(project,resource).is_file():raise ValueError('Missing cache resource')
    for arg in stage.get('args',[]):
        for key in inputs:
            if '{input:'+key+'}' in arg and key not in declaration['inputs']:
                raise ValueError('Referenced input missing from cache dependencies')


def key_for(stage: dict, cfg: dict, state: dict, run: Path) -> str:
    dep=stage['cache'];project=Path(state['project_config']).parent
    inputs={name:({'sha256':sha(Path(state['inputs'][name])),'path':state['inputs'][name]}
                  if cfg['inputs'][name]=='file' else state['inputs'][name]) for name in dep['inputs']}
    value=dict(schema_version=1,project=str(project),project_id=cfg['project_id'],stage=stage,
               script_sha256=sha(contained(project,stage['script'])),inputs=inputs,
               resources={r:sha(contained(project,r)) for r in dep['resources']},
               artifacts={r:sha(contained(run,r)) for r in dep['artifacts']},
               packages={p:importlib.metadata.version(p) for p in dep['packages']},
               runtime=[sys.version,sys.executable,platform.platform()],cache_code=sha(Path(__file__)))
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def restore(cache: Path, key: str, run: Path, outputs: list[str]) -> bool:
    folder=cache/key
    if not folder.exists():return False
    try:
        manifest=json.loads((folder/'manifest.json').read_text())
        if manifest['key']!=key or set(manifest['outputs'])!=set(outputs):return False
        for rel in outputs:
            path=contained(folder/'files',rel)
            if not path.is_file() or sha(path)!=manifest['outputs'][rel]:return False
        # Verify the entire entry before copying any of it.
        for rel in outputs:
            dest=contained(run,rel)
            if dest.exists():raise ValueError('Refusing to overwrite run output')
        for rel in outputs:
            dest=contained(run,rel);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(contained(folder/'files',rel),dest)
        return True
    except (OSError,ValueError,KeyError,TypeError):
        return False


def publish(cache: Path, key: str, run: Path, outputs: list[str]) -> None:
    cache.mkdir(parents=True,exist_ok=True)
    if (cache/key).exists():return
    temp=Path(tempfile.mkdtemp(prefix='.writing-',dir=cache))
    try:
        hashes={}
        for rel in outputs:
            source=contained(run,rel);dest=contained(temp/'files',rel)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
            hashes[rel]=sha(dest)
        (temp/'manifest.json').write_text(json.dumps(dict(key=key,outputs=hashes),sort_keys=True))
        try:temp.rename(cache/key)
        except OSError:
            if not (cache/key).exists():raise
    finally:
        if temp.exists():shutil.rmtree(temp)
