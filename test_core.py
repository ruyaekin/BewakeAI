import unittest, tempfile, json, struct, os
from pathlib import Path
from core import *

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.store=Store(self.root/'state'); self.mover=Mover(self.store)
    def tearDown(self): self.tmp.cleanup()
    def file(self,name='sample.bin',content=b'hello'):
        p=self.root/name; p.write_bytes(content); return p
    def test_move_undo(self):
        p=self.file(); dst=self.mover.move(p,self.root/'target'); self.assertFalse(p.exists()); self.assertEqual(dst.read_bytes(),b'hello'); self.assertEqual(self.mover.undo(),p); self.assertFalse(dst.exists()); self.assertEqual(p.read_bytes(),b'hello')
    def test_duplicate_different_name(self):
        p=self.file(); target=self.root/'target'; target.mkdir(); (target/'different.bin').write_bytes(b'hello')
        with self.assertRaises(ValueError): self.mover.move(p,target)
        self.assertTrue(p.exists())
    def test_collision(self):
        p=self.file(); target=self.root/'target'; target.mkdir(); (target/p.name).write_bytes(b'other')
        with self.assertRaises(ValueError): self.mover.move(p,target)
        self.assertEqual((target/p.name).read_bytes(),b'other')
    def test_undo_changed(self):
        p=self.file(); dst=self.mover.move(p,self.root/'target'); dst.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.mover.undo()
        self.assertFalse(p.exists())
    def test_undo_collision(self):
        p=self.file(); self.mover.move(p,self.root/'target'); p.write_bytes(b'new')
        with self.assertRaises(ValueError): self.mover.undo()
        self.assertEqual(p.read_bytes(),b'new')
    def test_stability(self):
        p=self.file(); os.utime(p,(10,10)); s=Stability(); self.assertFalse(s.ready(p,100)); self.assertFalse(s.ready(p,109)); self.assertTrue(s.ready(p,111)); p.write_bytes(b'new data'); self.assertFalse(s.ready(p,112))
    def test_partial(self):
        p=self.file('a.crdownload'); s=Stability(); self.assertFalse(s.ready(p,100)); self.assertFalse(s.ready(p,200))
    def test_pending_sibling(self):
        p=self.file(); Path(str(p)+'.part').write_bytes(b'x'); s=Stability(); self.assertFalse(s.ready(p,100)); self.assertFalse(s.ready(p,200))
    def test_metadata(self):
        head=json.dumps({'lora_unet.test':{},'__metadata__':{}}).encode(); p=self.file('unknown.safetensors',struct.pack('<Q',len(head))+head); self.assertEqual(classify(p)[0],'LoRA')
    def test_workflow(self):
        self.assertEqual(classify(self.file('x.json',b'{"nodes":[]}'))[0],'Workflow')
        self.assertEqual(classify(self.file('api.json',b'{"1":{"class_type":"KSampler"}}'))[0],'Workflow')
    def test_unknown_model(self): self.assertEqual(classify(self.file('model.safetensors'))[0],'Unbekannt')
    def test_rule_persistence(self):
        self.store.config['rules']=[dict(pattern='*lora*',category='LoRA',target='D:/models',auto=True)]; self.store.save(); self.assertEqual(Store(self.store.folder).rule('ABC_LORA.bin')['category'],'LoRA')
    def test_discover(self):
        (self.root/'ComfyUI'/'models').mkdir(parents=True); self.assertEqual(len(discover(self.root)),1)
    def test_yaml_multiple(self):
        p=self.root/'extra_model_paths.yaml'; p.write_text('shared:\n  base_path: ./models\n  loras: |\n    one\n    two\n'); self.assertEqual(len(import_paths(p)),2)
    def test_truncated_journal(self):
        self.store.log('test')
        with self.store.journal.open('a') as f: f.write('{broken')
        self.assertEqual(len(self.store.events()),1)

if __name__=='__main__': unittest.main()
