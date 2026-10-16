import os, shutil,sys,json
from pathlib import Path

NAME='Bewake AI Download Manager'
VERSION='0.6.0'
DEFAULT_REPOSITORY='ruyaekin/BewakeAI'
try:
    release=json.loads((Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'release-config.json').read_text('utf-8-sig'))
    VERSION=release.get('version',VERSION); DEFAULT_REPOSITORY=release.get('repository',DEFAULT_REPOSITORY)
except (OSError,ValueError): pass

def default_state():
    root=Path(os.getenv('LOCALAPPDATA',Path.home()))
    current=root/'BewakeAI'; previous=root/'DownloadPilot'
    if not current.exists() and previous.is_dir(): shutil.copytree(previous,current)
    return current
