"""Real Chromium canvas smoke test for 3-3game migration (no Streamlit secrets needed)."""
from __future__ import annotations
import json
import base64
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import new_state
from content import public_content

URL=(ROOT/'frontend'/'index.html').as_uri()
OUT=ROOT/'docs'/'asset_migration_screenshots'
OUT.mkdir(parents=True,exist_ok=True)
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1270,'height':970},device_scale_factor=1)
        errors=[];bad=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
        # Browser navigation is not available in some sandbox environments. Inject
        # the same HTML, CSS, JS and exact PNG bytes, with URL interception by an
        # Image.src adapter (not a renderer mock).
        html=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')
        html=html.replace('<link rel="stylesheet" href="style.css">','').replace('<script src="game.js" defer></script>','')
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'frontend'/'style.css').read_text(encoding='utf-8'))
        images={p.name:'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode('ascii') for p in (ROOT/'frontend'/'assets').glob('*.png')}
        page.evaluate('m => {window.__pngMap=m; window.__asked=[]; const old=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,"src");Object.defineProperty(HTMLImageElement.prototype,"src",{get(){return old.get.call(this);},set(v){window.__asked.push(v); old.set.call(this,window.__pngMap[v.split("/").pop()]||v);}});}',images)
        page.add_script_tag(content=(ROOT/'frontend'/'game.js').read_text(encoding='utf-8'))
        school=public_content()['school']
        r=next(x for group in school['floors'].values() for x in group if x['kind']=='class')
        print('Testing school class room:',r['id'])
        scenes=[('01_village_square','square',7,9),('02_shop','shop',9,12),('03_work','work',11,13),('04_school_hall','school:hall:1',15,9),('05_school_classroom','school:room:'+r['id'],15,16),('06_village_interior','inside:square',15,14)]
        state=new_state('3-1','07','테스트학생',appearance=2)
        for i,(tag,zone,x,y) in enumerate(scenes):
            new=dict(state)
            new.update(zone=zone,x=x,y=y,revision=i,run_id=state['run_id']+'-'+str(i))
            page.evaluate('payload => window.dispatchEvent(new MessageEvent("message", {data:{type:"streamlit:render",args:JSON.parse(payload)}}))',json.dumps({'state':new,'content':public_content(),'notice':''},ensure_ascii=False))
            page.wait_for_timeout(500 if i else 1800)
            page.locator('#game').screenshot(path=str(OUT/(tag+'.png')))
            if page.locator('#modal-layer').get_attribute('class') is None: raise AssertionError('Modal missing')
        # Setting a building in the inside scene is normally done by the game
        # after door interaction. The direct payload above does not exercise it.
        page.set_viewport_size({'width':768,'height':1024})
        page.wait_for_timeout(200)
        b=page.locator('#game').bounding_box()
        assert b and b['width']<=768,b
        btn=page.locator('[data-dir="up"]').bounding_box()
        assert btn and btn['height']>=36,btn
        page.screenshot(path=str(OUT/'07_tablet_768.png'),full_page=True)
        assert not errors,errors
        assert not bad,bad
        # Source-of-truth bytes must actually be loaded, not fallback sprites.
        good=page.evaluate('''() => {
          let names=['school_exterior','school_hall_1','school_classroom','avatar_0','teacher_00','building_cafe','donor_terrain','donor_fountain'];
          return names.map(name=>({name,ok:window.__asked.some(v=>v.includes('assets/'+name+'.png'))}));
        }''')
        assert all(row['ok'] for row in good),good
        print('CHROMIUM PASS: scene screenshots',len(scenes),'tablet width',b['width'],'asset requests',good)
        browser.close()
finally:
    pass
