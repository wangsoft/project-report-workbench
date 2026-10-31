import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import project_manager as pm


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = pm.initialize('sales', self.root / 'projects')
        (self.project.parent / 'compute.py').write_text(
            "import pathlib,sys,json\n"
            "pathlib.Path('evidence.json').write_text(json.dumps(sys.argv[1:]))\n")
        (self.project.parent / 'render.py').write_text(
            "import pathlib,sys,json\n"
            "pathlib.Path('report.json').write_text(json.dumps(sys.argv[1:]))\n")
        self.cfg = yaml.safe_load(self.project.read_text())
        self.cfg.update(inputs={'period': 'string', 'template': 'file'}, pipeline=[
            dict(id='compute', script='compute.py', args=['{input:period}', '{input:template}'],
                 outputs=['evidence.json'], checkpoint=True),
            dict(id='render', script='render.py', args=['{input:period}', '{input:template}'],
                 outputs=['report.json'])])
        self.write_config()
        self.template = self.root / 'template.txt'
        self.template.write_text('template v1')
        self.inputs = self.root / 'inputs.json'
        self.inputs.write_text(json.dumps({'period': '2026-10', 'template': 'template.txt'}))

    def write_config(self):
        self.project.write_text(yaml.safe_dump(self.cfg))

    def run_project(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return pm.run(self.project, self.inputs, self.root / 'workspace')

    def test_resume_retains_parameters_and_completed_stage(self):
        run = self.run_project()
        before = (run / 'evidence.json').stat().st_mtime_ns
        with self.assertRaisesRegex(ValueError, 'acknowledge'):
            pm.execute(run)
        state = pm.execute(run, 'compute')
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(json.loads((run / 'report.json').read_text()),
                         ['2026-10', str(self.template.resolve())])
        self.assertEqual((run / 'evidence.json').stat().st_mtime_ns, before)
        self.assertEqual(pm.execute(run)['status'], 'completed')

    def test_unique_runs(self):
        self.assertNotEqual(self.run_project(), self.run_project())

    def test_changed_input_rejected(self):
        run = self.run_project()
        self.template.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Input changed'):
            pm.execute(run, 'compute')

    def test_changed_config_rejected(self):
        run = self.run_project()
        self.cfg['version'] = '0.2.0'
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'Configuration'):
            pm.execute(run, 'compute')

    def test_changed_artifact_rejected(self):
        run = self.run_project()
        (run / 'evidence.json').write_text('corrupt')
        with self.assertRaisesRegex(ValueError, 'output changed'):
            pm.execute(run, 'compute')

    def test_failure_never_completed(self):
        (self.project.parent / 'compute.py').write_text('raise SystemExit(7)')
        with self.assertRaisesRegex(ValueError, 'exited 7'):
            self.run_project()
        state_path = next((self.root / 'workspace').glob('*/*/run_state.json'))
        state = json.loads(state_path.read_text())
        self.assertEqual(state['status'], 'failed')
        self.assertEqual(state['stages'][0]['status'], 'failed')
        self.assertFalse((state_path.parent / '.lock').exists())

    def test_missing_output_fails(self):
        (self.project.parent / 'compute.py').write_text('pass')
        with self.assertRaisesRegex(ValueError, 'declared outputs'):
            self.run_project()

    def test_path_escape_and_duplicate_outputs_rejected(self):
        for outputs in [['../escape'], ['run_state.json'], ['logs/x'], ['a', 'a/b']]:
            with self.subTest(outputs=outputs):
                self.cfg['pipeline'][0]['outputs'] = outputs
                self.write_config()
                with self.assertRaises(ValueError):
                    pm.config(self.project)

    def test_duplicate_init_and_empty_candidate(self):
        with self.assertRaises(FileExistsError):
            pm.initialize('sales', self.root / 'projects')
        empty = pm.initialize('empty', self.root / 'projects')
        self.assertEqual(pm.config(empty)[0]['pipeline'], [])
        with self.assertRaisesRegex(ValueError, 'no executable pipeline'):
            pm.run(empty, self.inputs, self.root / 'workspace')

    def test_partial_output_not_reused(self):
        run = self.run_project()
        (run / 'report.json').write_text('incomplete')
        with self.assertRaisesRegex(ValueError, 'partial output'):
            pm.execute(run, 'compute')

    def test_exclusive_lock(self):
        run = self.run_project()
        (run / '.lock').touch()
        with self.assertRaises(FileExistsError):
            pm.execute(run, 'compute')


if __name__ == '__main__':
    unittest.main()
