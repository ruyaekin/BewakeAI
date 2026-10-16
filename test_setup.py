import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import onboarding
from app import App
from tkinter import ttk

class SetupTests(unittest.TestCase):
    def test_only_comfy_paths_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'ComfyUI'/'models').mkdir(parents=True)
            found=onboarding.find_installations([root,root/'ComfyUI'])
            self.assertEqual(len(found),1)
            self.assertTrue(next(iter(found.values()))['LoRA'].endswith('models\\loras'))

    def test_existing_ai_requires_no_install_or_pull(self):
        with tempfile.TemporaryDirectory() as temp, patch('onboarding.models',return_value=[onboarding.MODEL]), patch('onboarding.subprocess.run') as run, patch('onboarding.urlopen') as request:
            self.assertEqual(onboarding.setup_ai(temp,lambda msg:None),onboarding.MODEL)
            run.assert_not_called(); request.assert_not_called()

    def test_ai_download_and_failure(self):
        for rows,raises in [([{'status':'pulling','total':100,'completed':50},{'status':'success'}],False),([{'error':'network unavailable'}],True)]:
            with tempfile.TemporaryDirectory() as temp, patch('onboarding.models',return_value=[]), patch('onboarding.urlopen') as request:
                response=MagicMock(); response.__enter__.return_value=iter(json.dumps(row).encode() for row in rows); request.return_value=response
                if raises:
                    with self.assertRaises(RuntimeError): onboarding.setup_ai(temp,lambda msg:None)
                else: self.assertEqual(onboarding.setup_ai(temp,lambda msg:None),onboarding.MODEL)

    def test_first_run_saved_and_preserves_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); downloads=root/'downloads'; downloads.mkdir()
            app=App(root/'state',first_run=False,enable_tray=False); app.withdraw(); app.store.config['downloads']=str(downloads)
            app.store.config['rules']=[{'pattern':'test*','category':'LoRA','target':str(root/'models'),'auto':False}]; app.store.save()
            try:
                with patch('onboarding.find_installations',return_value={}),patch('onboarding.models',return_value=[]):
                    app.setup()
                    cb,result,err=app.q.get(timeout=5); self.assertIsNone(err); app.busy=False; cb(result)
                    def buttons(widget):
                        for child in widget.winfo_children():
                            if isinstance(child,ttk.Button): yield child
                            yield from buttons(child)
                    finish=next(button for button in buttons(app.setup_window) if button.cget('text')=='Einrichtung abschließen'); finish.invoke()
                config=json.loads(app.store.file.read_text('utf-8'))
                self.assertTrue(config['setup_complete']); self.assertFalse(config['auto']); self.assertEqual(len(config['rules']),1)
                self.assertEqual(config['downloads'],str(downloads)); self.assertIn('Dokument',config['targets']); self.assertFalse(app.setup_open)
            finally: app.destroy()

if __name__=='__main__': unittest.main()
