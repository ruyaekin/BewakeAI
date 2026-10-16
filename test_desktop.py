import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from desktop_paths import find_desktop
from branding import default_state
from core import import_paths

class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.roaming=self.root/'Roaming'; self.local=self.root/'Local'; self.home=self.root/'Home'
        self.config=self.roaming/'Comfy Desktop'; self.config.mkdir(parents=True)
        self.shared=self.root/'shared-models'; self.install=self.root/'installs'/'My Install'; self.comfy=self.install/'ComfyUI'; (self.comfy/'models').mkdir(parents=True)
        self.record={'id':'inst-test','name':'Studio','sourceId':'standalone','installPath':str(self.install)}
        self.write(self.config/'settings.json',{'modelsDirs':[str(self.shared)]}); self.records()
    def tearDown(self): self.temp.cleanup()
    def write(self,path,data): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data),'utf-8')
    def records(self,*additional): self.write(self.config/'installations.json',[self.record,*additional])
    def find(self): return find_desktop(self.roaming,self.local,self.home)
    def target(self): return next(iter(self.find().values()))
    def test_shared_models_and_local_workflows(self):
        data=self.target(); self.assertEqual(data['LoRA'],[str(self.comfy/'models'/'loras')]); self.assertEqual(data['Workflow'],[str(self.comfy/'user'/'default'/'workflows')])
    def test_multiple_instances_and_no_cloud(self):
        second=self.root/'second'; (second/'models').mkdir(parents=True)
        self.records({'id':'two','name':'Second','installPath':str(second)},{'sourceId':'cloud','name':'Comfy Cloud'})
        result=self.find(); self.assertEqual(len(result),2); self.assertTrue(any('Second' in name for name in result))
    def test_isolated_model_library(self):
        self.record['useSharedModels']=False; self.records(); self.assertEqual(self.target()['LoRA'][0],str(self.comfy/'models'/'loras')); self.assertNotIn(str(self.shared/'loras'),self.target()['LoRA'])
    def test_promoted_extra_dir(self):
        extra=self.root/'extra'; self.record.update(modelDirs=[str(extra)],modelDirsPrimary=str(extra)); self.records()
        self.assertEqual(self.target()['VAE'],[str(self.comfy/'models'/'vae')])
    def test_explicit_own_primary(self):
        self.record['modelDirsPrimary']=str(self.comfy/'models'); self.records(); self.assertEqual(self.target()['LoRA'][0],str(self.comfy/'models'/'loras'))
    def test_user_directory_launch_override(self):
        user=self.root/'Different User Dir'; self.record['launchArgs']=f'--user-directory="{user}"'; self.records()
        self.assertEqual(self.target()['Workflow'],[str(user/'default'/'workflows')])
    def test_adopted_base(self):
        base=self.root/'old-desktop-data'; base.mkdir(); self.record.update(adoptedBaseDir=str(base),useSharedModels=False); self.records()
        self.assertEqual(self.target()['Checkpoint'][0],str(base/'models'/'checkpoints')); self.assertEqual(self.target()['Workflow'][0],str(base/'user'/'default'/'workflows'))
    def test_legacy_desktop_base(self):
        self.write(self.config/'installations.json',[]); base=self.root/'legacy-data'; base.mkdir(); self.write(self.roaming/'ComfyUI'/'config.json',{'basePath':str(base)})
        self.assertEqual(self.target()['LoRA'][0],str(base/'models'/'loras'))
    def test_instance_yaml_external_paths(self):
        yaml=self.config/'instance-model-paths'/'inst-test.yaml'; yaml.parent.mkdir(); extra=self.root/'SpecialLoRA'
        yaml.write_text('external:\n  loras: '+json.dumps(str(extra))+'\n','utf-8')
        self.assertNotIn(str(extra),self.target()['LoRA'])
    def test_bad_config_and_yaml_do_not_break_detection(self):
        self.write(self.config/'settings.json',[]); (self.comfy/'extra_model_paths.yaml').write_text('bad: [','utf-8')
        self.assertEqual(len(self.find()),1)
    def test_yaml_lists(self):
        yaml=self.root/'paths.yaml'; yaml.write_text('models:\n  base_path: '+json.dumps(str(self.root))+'\n  loras:\n    - first\n    - second\n','utf-8')
        self.assertEqual(len(import_paths(yaml)),2)
    def test_brand_migration_preserves_old_data(self):
        old=self.local/'DownloadPilot'; old.mkdir(parents=True); self.write(old/'settings.json',{'rules':[{'pattern':'keep-me'}]})
        with patch.dict(os.environ,{'LOCALAPPDATA':str(self.local)}):
            new=default_state(); self.assertEqual(new,self.local/'BewakeAI'); self.assertEqual((new/'settings.json').read_bytes(),(old/'settings.json').read_bytes())
            self.write(new/'settings.json',{'rules':[]}); default_state(); self.assertEqual(json.loads((new/'settings.json').read_text())['rules'],[])
        self.assertTrue((old/'settings.json').exists())

if __name__=='__main__': unittest.main()
