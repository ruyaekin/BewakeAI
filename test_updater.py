import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import updater

class UpdateTests(unittest.TestCase):
    def release(self,data=b'installer'):
        return {'tag_name':'v0.7.0','assets':[{'name':updater.SETUP,'browser_download_url':'https://github.com/ruyaekin/BewakeAI/releases/download/v0.7.0/'+updater.SETUP,'size':len(data),'digest':'sha256:'+hashlib.sha256(data).hexdigest()}]}
    def test_repository_and_versions(self):
        self.assertEqual(updater.repository('https://github.com/ruyaekin/BewakeAI/'),'ruyaekin/BewakeAI')
        self.assertGreater(updater.version('v0.10.0'),updater.version('0.9.0'))
        for invalid in ('https://example.com/owner/repo','../bad','owner/repo/issues'):
            with self.assertRaises(ValueError): updater.repository(invalid)
    def test_only_newer_complete_release(self):
        with patch('updater.read',return_value=json.dumps(self.release()).encode()):
            self.assertEqual(updater.check('ruyaekin/BewakeAI','0.6.0')['version'],'0.7.0')
            self.assertIsNone(updater.check('ruyaekin/BewakeAI','0.7.0'))
        release=self.release(); release['assets']=[]
        with patch('updater.read',return_value=json.dumps(release).encode()): self.assertIsNone(updater.check('ruyaekin/BewakeAI','0.6.0'))
    def test_missing_checksum_rejected(self):
        release=self.release(); release['assets'][0].pop('digest')
        with patch('updater.read',return_value=json.dumps(release).encode()):
            with self.assertRaises(ValueError): updater.check('ruyaekin/BewakeAI','0.6.0')
    def test_wrong_repository_asset_rejected(self):
        release=self.release(); release['assets'][0]['browser_download_url']='https://github.com/other/repo/releases/download/v0.7.0/setup.exe'
        with patch('updater.read',return_value=json.dumps(release).encode()):
            with self.assertRaises(ValueError): updater.check('ruyaekin/BewakeAI','0.6.0')
    def test_verified_download_and_corruption(self):
        data=b'installer'; info={'version':'0.7.0','url':'https://github.com/ruyaekin/BewakeAI/releases/download/v0.7.0/'+updater.SETUP,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        for actual,success in ((data,True),(b'corrupted',False)):
            with tempfile.TemporaryDirectory() as temp,patch('updater.urlopen') as request:
                response=MagicMock(); response.url='https://release-assets.githubusercontent.com/github-production-release-asset/123'; response.read.side_effect=[actual,b'']; request.return_value.__enter__.return_value=response
                if success:
                    result=updater.download(info,temp); self.assertEqual(result.read_bytes(),data)
                else:
                    with self.assertRaises(ValueError): updater.download(info,temp)
                    self.assertFalse(list(Path(temp).rglob('*.exe'))); self.assertFalse(list(Path(temp).rglob('*.partial')))
    def test_tampered_file_cannot_launch(self):
        with tempfile.TemporaryDirectory() as temp,patch('updater.subprocess.Popen') as launch:
            path=Path(temp)/'setup.exe'; path.write_bytes(b'changed')
            with self.assertRaises(ValueError): updater.launch({'sha256':hashlib.sha256(b'expected').hexdigest()},path,temp)
            launch.assert_not_called()

if __name__=='__main__': unittest.main()
