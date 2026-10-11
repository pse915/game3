"""Local SQLite throughput, separate from browser FPS and Google Sheets quotas."""
import json, sys, tempfile, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import new_state, apply
from storage import LocalStore
from content import REQUIRED, EVENTS

def percentile(values,p):
    return sorted(values)[min(len(values)-1,int(len(values)*p))]

results=[]
with tempfile.TemporaryDirectory() as d:
    store=LocalStore(Path(d)/'virtual-class.sqlite3')
    for count in (10,20,30):
        def run(i):
            s=new_state('QA-'+str(count),str(i),'가상');samples=[]
            def save():
                start=time.perf_counter();store.save(s);samples.append((time.perf_counter()-start)*1000)
            def message(kind,**extra):
                nonlocal s
                s,_=apply(s,{'type':kind,'nonce':str(s['revision'])+'-'+kind,**extra});save()
            save()
            for stage in range(3):
                for key in REQUIRED[stage]:message('choose',event_id=key,choice_id=next(iter(EVENTS[key]['choices'])))
                message('finish' if stage==2 else 'advance')
            message('reflection',text='인구 변화의 원인과 대응을 생각한 가상 소감문')
            loaded=store.load(s['class_code'],s['student_id'])
            assert loaded==s and loaded['ended']
            return samples
        started=time.perf_counter()
        with ThreadPoolExecutor(max_workers=count) as pool:
            samples=[x for group in pool.map(run,range(count)) for x in group]
        results.append({'users':count,'writes':len(samples),'total_seconds':time.perf_counter()-started,
                        'save_p50_ms':percentile(samples,.5),'save_p95_ms':percentile(samples,.95),
                        'isolated_complete_states':count})
output=ROOT/'docs'/'qa_results';output.mkdir(exist_ok=True)
(output/'sqlite_load.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
