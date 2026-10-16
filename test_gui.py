import tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
from app import App

class GuiTest(unittest.TestCase):
    def test_desktop_install_selection_keeps_workflows_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            app=App(Path(temp)/'state',first_run=False,enable_tray=False); app.withdraw(); app.paused=True
            try:
                app.store.config['installations']={'Comfy Desktop · A':{'Workflow':['C:/A/user/default/workflows'],'LoRA':['C:/shared/loras']},'Comfy Desktop · B':{'Workflow':['D:/B/user/default/workflows'],'LoRA':['C:/shared/loras']}}
                app.installation.set('Comfy Desktop · A'); app.category.set('Workflow'); app.refresh_targets(); self.assertEqual(app.destination.get(),'C:/A/user/default/workflows')
                app.installation.set('Comfy Desktop · B'); app.refresh_targets(); self.assertEqual(app.destination.get(),'D:/B/user/default/workflows')
                app.category.set('LoRA'); self.assertEqual(app.destination.get(),'C:/shared/loras')
            finally: app.destroy()
    def test_review_move_and_undo(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); downloads=root/'downloads'; downloads.mkdir(); target=root/'target'; source=downloads/'portrait_lora.safetensors'; source.write_bytes(b'test model')
            app=App(root/'state',first_run=False,enable_tray=False); app.withdraw(); app.paused=True; app.store.config['downloads']=str(downloads); app.store.config['notifications']=False
            try:
                app.add((str(source),('LoRA','Dateiname')))
                iid=app.tree.get_children()[0]; app.tree.selection_set(iid); app.select(); app.destination.set(str(target))
                self.assertEqual(app.category.get(),'LoRA')
                with patch('app.messagebox.askyesno',return_value=True): app.move()
                self.drain(app); self.assertFalse(source.exists()); self.assertFalse(app.tree.get_children()); self.assertTrue((target/source.name).exists())
                app.undo(); self.drain(app); self.assertTrue(source.exists()); self.assertFalse((target/source.name).exists())
            finally: app.destroy()
    def drain(self,app):
        deadline=time.time()+10
        while app.busy and time.time()<deadline:
            app.update()
            try:
                cb,result,err=app.q.get_nowait(); app.busy=False
                if err: raise err
                cb(result)
            except __import__('queue').Empty: time.sleep(.02)
        self.assertFalse(app.busy)

if __name__=='__main__': unittest.main()
