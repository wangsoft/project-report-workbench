import contextlib
import io
import json
from pathlib import Path
import unittest

import test_projects
import project_manager as pm
import project_versions as pv


class CacheVersionTests(unittest.TestCase):
    setUp=test_projects.ProjectTests.setUp
    write_config=test_projects.ProjectTests.write_config

    def prepare_cache(self):
        self.cfg['pipeline'][0]['checkpoint']=False
        self.cfg['pipeline'][0]['cache']=dict(inputs=['period','template'],resources=[],artifacts=[],packages=[])
        self.write_config()

    def execute(self):
        with contextlib.redirect_stdout(io.StringIO()):
            run=pm.run(self.project,self.inputs,self.root/'workspace',self.root/'cache')
        return run,json.loads((run/'run_state.json').read_text())

    def test_warm_cache_preserves_outputs(self):
        self.prepare_cache();first,a=self.execute();second,b=self.execute()
        self.assertEqual(a['stages'][0]['cache'],'miss')
        self.assertEqual(b['stages'][0]['cache'],'hit')
        self.assertEqual((first/'evidence.json').read_bytes(),(second/'evidence.json').read_bytes())
        self.assertEqual(b['stages'][1]['cache'],'disabled')

    def test_changed_input_misses(self):
        self.prepare_cache();self.execute();self.template.write_text('new data')
        self.assertEqual(self.execute()[1]['stages'][0]['cache'],'miss')

    def test_corrupt_cache_not_reused(self):
        self.prepare_cache();self.execute()
        artifact=next((self.root/'cache').glob('*/files/evidence.json'));artifact.write_text('bad')
        run,state=self.execute()
        self.assertEqual(state['stages'][0]['cache'],'miss')
        self.assertNotEqual((run/'evidence.json').read_text(),'bad')

    def test_unrelated_resource_keeps_cache(self):
        self.prepare_cache();self.execute()
        (self.project.parent/'style.json').write_text('{"color":"blue"}')
        self.cfg['resources']=['style.json'];self.write_config()
        self.assertEqual(self.execute()[1]['stages'][0]['cache'],'hit')

    def test_quality_stage_cannot_cache(self):
        self.prepare_cache();self.cfg['pipeline'][0]['role']='quality';self.write_config()
        with self.assertRaisesRegex(ValueError,'cannot be cached'):pm.config(self.project)

    def test_undeclared_input_rejected(self):
        self.prepare_cache();self.cfg['pipeline'][0]['cache']['inputs']=[];self.write_config()
        with self.assertRaisesRegex(ValueError,'missing from cache'):pm.config(self.project)

    def test_failed_pipeline_never_publishes_cache(self):
        self.prepare_cache();(self.project.parent/'render.py').write_text('raise SystemExit(1)')
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(list((self.root/'cache').glob('*/manifest.json')),[])

    def prepare_release(self):
        self.prepare_cache()
        script=self.project.parent/'render.py'
        script.write_text("import pathlib,json,hashlib\n"
                          "p=pathlib.Path('evidence.json')\n"
                          "a={'status':'passed','failures':[],'artifacts':{'evidence.json':hashlib.sha256(p.read_bytes()).hexdigest()}}\n"
                          "pathlib.Path('acceptance.json').write_text(json.dumps(a))\n")
        self.cfg['pipeline'][1]['outputs']=['acceptance.json'];self.write_config()
        run,_=self.execute()
        release=pv.freeze(self.project,run,self.root/'releases','synthetic pipeline only')
        return run,release

    def test_release_immutable_and_activation(self):
        run,release=self.prepare_release()
        self.assertEqual(pv.validate_release(release)['version'],'0.1.0')
        selected=pv.activate(self.project,release);self.assertTrue(selected.exists())
        with self.assertRaises(FileExistsError):pv.freeze(self.project,run,self.root/'releases','test')
        (release/'project/compute.py').write_text('modified')
        with self.assertRaisesRegex(ValueError,'modified'):pv.validate_release(release)

    def test_release_rejects_changed_acceptance(self):
        run,_=self.prepare_release();(run/'acceptance.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'artifact changed'):
            pv.freeze(self.project,run,self.root/'other','test')

    def test_feedback_requires_bound_regression(self):
        run,release=self.prepare_release()
        feedback=pv.feedback(self.project,run,'calculation','test finding','test remedy','evidence.json','0.1.0')
        regression=self.root/'regression.json'
        regression.write_text(json.dumps(dict(status='passed',project_version='0.1.0',release_manifest_sha256='wrong')))
        with self.assertRaisesRegex(ValueError,'bind'):
            pv.resolve_feedback(self.project,feedback,release,regression)
        regression.write_text(json.dumps(dict(status='passed',project_version='0.1.0',
                                             release_manifest_sha256=pm.digest(release/'release.json'))))
        self.assertTrue(pv.resolve_feedback(self.project,feedback,release,regression).exists())


if __name__=='__main__':unittest.main()
