"""Generate fictional browser QA input from current source, never student data."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content import public_content
from engine import new_state
target=ROOT/'tests'/'qa_payload.json'
target.write_text(json.dumps({'state':new_state('QA','01','가상 학생'),'content':public_content()},ensure_ascii=False),encoding='utf-8')
print('Created tests/qa_payload.json with fictional state')
