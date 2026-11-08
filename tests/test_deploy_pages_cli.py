"""The deployment entry point delegates only the exact pushed SHA to normal Jenkins."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deploy_cli',ROOT/'deploy_pages.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class DeployCliTests(unittest.TestCase):
    def invoke(self,protocol='graphicsrepair-normal/v1'):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        submit=Path(temporary.name)/'submit.py';submit.write_text('# test trusted path')
        env={'DEPLOY_IT_BRANCH':'main','DEPLOY_IT_COMMIT':'a'*40,'JENKINS_GRAPHICSREPAIR_SUBMIT':str(submit)}
        run=Mock(return_value=Mock(stdout=protocol+'\n'))
        return env,run,submit
    def test_exact_revision_normal_chain_only(self):
        env,run,submit=self.invoke()
        with patch.dict(os.environ,env,clear=True),patch('sys.argv',['deploy_pages.py']),patch.object(subprocess,'run',run):cli.main()
        self.assertEqual(run.call_count,2)
        self.assertEqual(run.call_args_list[0].args[0][-1],'--protocol')
        self.assertEqual(run.call_args_list[1].args[0][-1],'a'*40)
        self.assertEqual(run.call_args_list[1].args[0][1],str(submit))
    def test_old_protocol_never_submits_revision(self):
        env,run,_=self.invoke('graphicsrepair-cold-cohort/v1')
        with patch.dict(os.environ,env,clear=True),patch('sys.argv',['deploy_pages.py']),patch.object(subprocess,'run',run),self.assertRaises(RuntimeError):cli.main()
        self.assertEqual(run.call_count,1)
    def test_wrong_branch_or_sha_never_invokes_client(self):
        for field,value in [('DEPLOY_IT_BRANCH','pages'),('DEPLOY_IT_COMMIT','main')]:
            env,run,_=self.invoke();env[field]=value
            with self.subTest(field=field),patch.dict(os.environ,env,clear=True),patch('sys.argv',['deploy_pages.py']),patch.object(subprocess,'run',run),self.assertRaises(RuntimeError):cli.main()
            run.assert_not_called()
if __name__=='__main__':unittest.main()
