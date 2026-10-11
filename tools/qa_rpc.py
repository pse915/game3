"""A local test-only bridge from Chrome messages to the real save/reducer path."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import apply
from content import public_content
from storage import LocalStore
request=json.load(sys.stdin)
state,notice=apply(request['state'],request['message'])
store=LocalStore(Path(request['database']))
store.save(state)
state=store.load(state['class_code'],state['student_id'])
print(json.dumps({'state':state,'content':public_content(state),'notice':notice},ensure_ascii=False))
