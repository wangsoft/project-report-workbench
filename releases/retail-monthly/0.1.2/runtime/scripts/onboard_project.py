"""Create an executable, version-pinned periodic-report project from a complete brief."""
import argparse
import json
from pathlib import Path
import shutil
import yaml
from periodic_analysis import validate_spec


def create_project(spec: dict, projects: Path) -> Path:
    validate_spec(spec)
    target=projects.resolve()/spec['project_id'];target.mkdir(parents=True,exist_ok=False)
    (target/'scripts').mkdir();(target/'references').mkdir()
    # Pin the shared implementation into the project; later shared upgrades are explicit.
    shutil.copyfile(Path(__file__).with_name('periodic_analysis.py'),target/'scripts/periodic_analysis.py')
    (target/'references/brief.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
    pipeline=[]
    for mode,outputs in [('analyze',['evidence.json']),('render',['report.md','report.html','answers.json']),('verify',['delivery.json'])]:
        s=dict(id=mode,script='scripts/periodic_analysis.py',args=[mode,'--spec','{project_dir}/references/brief.json','--data','{input:data}','--period','{input:period}','--out','{run_dir}'],outputs=outputs)
        if mode=='verify':s['role']='quality'
        else:s['cache']=dict(inputs=['data','period'],resources=['references/brief.json'],artifacts=[] if mode=='analyze' else ['evidence.json'],packages=['openpyxl'] if mode=='analyze' else [])
        pipeline.append(s)
    config=dict(schema_version=1,project_id=spec['project_id'],version='0.1.0',status='candidate',inputs=dict(data='file',period='string'),resources=['references/brief.json'],pipeline=pipeline)
    path=target/'project.yaml';path.write_text(yaml.safe_dump(config,allow_unicode=True,sort_keys=False));return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--brief',type=Path,required=True);p.add_argument('--projects',type=Path,default=Path(__file__).resolve().parents[1]/'projects');a=p.parse_args()
    print(create_project(json.loads(a.brief.read_text()),a.projects))
