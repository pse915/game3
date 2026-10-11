/* Real Chrome Canvas QA over the DevTools pipe; no npm dependencies. */
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),mode=process.argv[2]||'baseline',out=path.resolve(root,'../work',mode);
fs.mkdirSync(out,{recursive:true});
const chrome=process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe';
const child=spawn(chrome,['--headless=new','--disable-gpu','--no-sandbox','--no-first-run','--remote-debugging-pipe','--user-data-dir='+path.join(out,'profile'),'about:blank'],{stdio:['ignore','ignore','pipe','pipe','pipe'],windowsHide:true});
let seq=0,buffer='',pending=new Map(),errors=[];
child.stderr.on('data',()=>{});
child.stdio[4].on('data',chunk=>{buffer+=chunk.toString();let end;while((end=buffer.indexOf('\0'))>=0){const line=buffer.slice(0,end);buffer=buffer.slice(end+1);if(!line)continue;const msg=JSON.parse(line);if(msg.id){const p=pending.get(msg.id);if(p){pending.delete(msg.id);msg.error?p.reject(new Error(JSON.stringify(msg.error))):p.resolve(msg.result)}}else if(msg.method==='Runtime.exceptionThrown')errors.push(msg.params.exceptionDetails);else if(msg.method==='Fetch.requestPaused')cdp('Fetch.fulfillRequest',{requestId:msg.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'text/html'}],body:Buffer.from('<!doctype html><html><head></head><body></body></html>').toString('base64')},msg.sessionId).catch(e=>errors.push(String(e)));}});
function cdp(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});child.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+'\0')})}
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let session;
async function evaluate(expression){const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
const quantile=(a,p)=>a.slice().sort((a,b)=>a-b)[Math.min(a.length-1,Math.floor(a.length*p))]||0;
async function main(){
 const version=await cdp('Browser.getVersion');
 const {targetId}=await cdp('Target.createTarget',{url:'about:blank'});
 session=(await cdp('Target.attachToTarget',{targetId,flatten:true})).sessionId;
 await cdp('Runtime.enable',{},session);await cdp('Page.enable',{},session);
 await cdp('Emulation.setDeviceMetricsOverride',{width:1320,height:1000,deviceScaleFactor:1,mobile:false},session);
 await cdp('Fetch.enable',{patterns:[{urlPattern:'http://qa.invalid/*',requestStage:'Request'}]},session);
 await cdp('Page.navigate',{url:'http://qa.invalid/'},session);await delay(250);
 const frame=(await cdp('Page.getFrameTree',{},session)).frameTree.frame.id;
 let html=fs.readFileSync(path.join(root,'frontend/index.html'),'utf8').replace('<script src="game.js" defer></script>','').replace('<link rel="stylesheet" href="style.css">','<style>'+fs.readFileSync(path.join(root,'frontend/style.css'),'utf8')+'</style>');
 await cdp('Page.setDocumentContent',{frameId:frame,html},session);
 const assets=Object.fromEntries(fs.readdirSync(path.join(root,'frontend/assets')).filter(f=>f.endsWith('.png')).map(f=>[f.slice(0,-4),'data:image/png;base64,'+fs.readFileSync(path.join(root,'frontend/assets',f)).toString('base64')]));
 await evaluate('window.TEST_ASSETS='+JSON.stringify(assets)+';window.__messages=[];window.addEventListener("message",e=>{if(e.data?.type==="streamlit:setComponentValue")window.__messages.push(e.data.value)});window.__perf={frames:[],draw:[],last:0,active:true};');
 let js=fs.readFileSync(process.env.QA_SOURCE||path.join(root,'frontend/game.js'),'utf8');
 js=js.replace("im.src='assets/'+name+'.png'",'im.src=window.TEST_ASSETS[name]');
 js=js.replace('updateMovement(now);draw(now);','updateMovement(now);const begin=performance.now();draw(now);if(window.__perf.active!==false){window.__perf.draw.push(performance.now()-begin);if(window.__perf.last)window.__perf.frames.push(now-window.__perf.last);window.__perf.last=now;}');
 js=js.replace('  componentReady();',`  window.__qa={pos:()=>({...pos}),guidePixels:()=>{modalOpen=false;guideEnabled=false;draw(1000);const a=canvas.toDataURL();guideEnabled=true;draw(1000);return a!==canvas.toDataURL();},close:closeModal,restore:()=>{rememberPosition();lastRun='';updateFromPython({state,content:data});},timing:hz=>{pos={zone:'shop',x:0,y:12,prevX:0,prevY:12,moveTime:0,dir:'right'};lastStep=0;pressed.clear();pressed.add('right');for(let i=1;i<=Math.round(hz*2.9);i++)updateMovement(i*1000/hz);pressed.clear();return pos.x;},assets:()=>Object.entries(art).filter(([k,v])=>v&&v.src).map(([k])=>k),set:p=>{Object.assign(pos,p);pos.prevX=pos.x;pos.prevY=pos.y;mapKey='';routeMemo={};},hall:enterSchoolHall,room:enterSchoolRoom,interact,warp,enter:enterInterior,path:(x,y)=>{pathNextStep(pos.x,pos.y,x,y,pos.zone);return routeMemo.route;},blocked:obstacle,update:updateMovement,press:d=>pressed.add(d),release:stopAll,draw,ready:()=>Promise.all(Object.values(art).filter(Boolean).map(i=>i.decode().catch(()=>{}))),render:updateFromPython,modal:()=>modalOpen,pending:()=>eventsPending}; componentReady();`);
 await evaluate(js);const fixture=JSON.parse(fs.readFileSync(path.join(root,'tests/qa_payload.json'),'utf8'));fixture.state.run_id=require('node:crypto').randomUUID();
 await evaluate('window.__qa.render('+JSON.stringify(fixture)+');window.__qa.ready()');
 const requested=await evaluate('window.__qa.assets()');const startupBytes=requested.reduce((sum,k)=>sum+fs.statSync(path.join(root,'frontend/assets',k+'.png')).size,0);const movement={};for(const hz of [60,30,15])movement[hz]=await evaluate('window.__qa.timing('+hz+')');console.log(JSON.stringify({startupImages:requested.length,startupBytes,movement}));
 const scenarios=[['square',null],['shop',null],['school:hall:1',null],['school:room:1-2',null],['inside:shop','shop']];let rows=[];
 for(const rate of (mode==='interaction'?[]:[1,4])){
  await cdp('Emulation.setCPUThrottlingRate',{rate},session);
  await cdp('Emulation.setDeviceMetricsOverride',{width:rate===1?1320:810,height:rate===1?1000:1100,deviceScaleFactor:1,mobile:rate!==1},session);
  for(const [zone,outer] of scenarios){
   if(outer)await evaluate('window.__qa.warp("shop");window.__qa.enter('+JSON.stringify(fixture.content.buildings.shop[0])+')');
   else if(zone.includes('hall'))await evaluate('window.__qa.hall(1)');else if(zone.includes('room'))await evaluate('window.__qa.room("1-2")');else await evaluate('window.__qa.warp('+JSON.stringify(zone)+')');
   for(let run=0;run<3;run++){
    await evaluate('window.__perf={frames:[],draw:[],last:0}');await delay(2100);
    const metrics=await evaluate('({frames:window.__perf.frames,draw:window.__perf.draw,memory:performance.memory?.usedJSHeapSize})');
    rows.push({zone,rate,run:run+1,fps:1000/(metrics.frames.reduce((a,b)=>a+b,0)/metrics.frames.length),fpsLow1:1000/quantile(metrics.frames,.99),p50:quantile(metrics.frames,.5),p95:quantile(metrics.frames,.95),drawP50:quantile(metrics.draw,.5),drawP95:quantile(metrics.draw,.95),memory:metrics.memory});
   }
   console.log(mode,zone,'CPU',rate,'measured');fs.writeFileSync(path.join(out,'performance.json'),JSON.stringify({version:version.product,startupImages:requested.length,startupBytes,movement,rows,errors},null,2));
  }
 }
 await cdp('Emulation.setCPUThrottlingRate',{rate:1},session);
 if(mode!=='baseline'&&mode!=='interaction'){
  await evaluate('window.__qa.hall(1)');
  for(const [floor,rooms] of Object.entries(fixture.content.school.floors)){
   await evaluate('window.__qa.hall('+floor+')');for(const room of rooms){const route=await evaluate('window.__qa.path('+room.door.join(',')+')');assert(route.length||Math.abs(room.door[0]-15)+Math.abs(room.door[1]-9)<=1);assert(await evaluate(JSON.stringify(route)+'.every(p=>!window.__qa.blocked("school:hall:'+floor+'",...p))'));}
  }
  await evaluate('window.__qa.warp("square");window.__qa.set({x:7,y:9});window.__qa.interact()');assert.equal((await evaluate('window.__qa.pos()')).zone,'school:hall:1');
  await evaluate('window.__qa.room("1-2");window.__qa.set({x:14,y:10});window.__qa.interact()');assert((await evaluate('document.getElementById("modal-content").textContent')).includes('선생님'));
  await evaluate('document.querySelector(".dialog-actions button").click()');assert.equal((await evaluate('window.__messages.at(-1)')).type,'school_activity');
  await evaluate('window.__qa.render('+JSON.stringify(fixture)+');window.__qa.warp("shop");window.__qa.enter('+JSON.stringify(fixture.content.buildings.shop[0])+');window.__qa.set({x:15,y:17});window.__qa.interact()');assert.equal((await evaluate('window.__qa.pos()')).zone,'shop');
  for(const width of [810,390]){await cdp('Emulation.setDeviceMetricsOverride',{width,height:1100,deviceScaleFactor:1,mobile:true},session);const boxes=await evaluate('Array.from(document.querySelectorAll(".dpad button")).map(b=>({w:b.getBoundingClientRect().width,h:b.getBoundingClientRect().height}))');assert(boxes.every(b=>b.w>=44&&b.h>=44));}
  await evaluate('window.__qa.hall(1)');const before=(await evaluate('window.__qa.pos()')).x;
  const point=await evaluate('(()=>{let r=document.querySelector("[data-dir=left]").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()');
  await cdp('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]},session);await delay(450);await cdp('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},session);assert((await evaluate('window.__qa.pos()')).x<before);
  assert.equal(errors.length,0);console.log('Browser regression checks passed: room routes, entrance, NPC, interior exit, tablet touch, 44px controls');
 }
 if(mode==='interaction'){
  await evaluate('window.__qa.warp("square");window.__qa.set({x:7,y:9})');assert(await evaluate('window.__qa.guidePixels()'),'Guidance must actually draw an arrow');
  const {spawnSync}=require('node:child_process');let payload=fixture,nonce=0;
  async function applyMessage(message){
   const proc=spawnSync(process.env.QA_PYTHON||'python',[path.join(root,'tools/qa_rpc.py')],{input:JSON.stringify({state:payload.state,message,database:path.join(out,'bridge.sqlite3')}),encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'},windowsHide:true});
   assert.equal(proc.status,0,proc.stderr);payload=JSON.parse(proc.stdout);await evaluate('window.__qa.render('+JSON.stringify(payload)+')');
  }
  async function choose(event,option){
   const npc=payload.content.npcs.find(n=>n.event===event);
   await evaluate('window.__qa.warp('+JSON.stringify(npc.zone)+');window.__qa.set({x:'+npc.x+',y:'+(npc.y+1)+'});window.__qa.interact()');
   if(payload.content.events[event].witnesses){
    assert(await evaluate('Array.from(document.querySelectorAll("[data-choice]")).every(b=>b.disabled)'));
    for(let i=0;i<3;i++)await evaluate('document.querySelector("[data-voice=\\"'+i+'\\"]").click()');
   }
   await evaluate('document.querySelector("[data-choice=\\"'+option+'\\"]").click()');
   const message=await evaluate('window.__messages.at(-1)');assert.equal(message.event_id,event);await applyMessage(message);
  }
  for(let stage=0;stage<3;stage++){
   for(const event of payload.content.requirements[stage])await choose(event,Object.keys(payload.content.events[event].choices)[0]);
   await evaluate('document.getElementById("next-stage").click();document.querySelector(".dialog-actions button").click()');
   await applyMessage(await evaluate('window.__messages.at(-1)'));
   if(stage<2)await evaluate('document.querySelector(".dialog-actions button").click()');
  }
  assert(payload.state.ended);assert.equal(payload.state.world_changes.length,4);assert(payload.state.community.budget<12);
  await evaluate('window.__qa.warp("shop");window.__qa.set({x:22,y:13});window.__qa.interact()');assert((await evaluate('document.getElementById("modal-content").textContent')).includes('도준'));
  await evaluate('window.__qa.close();window.__qa.warp("welfare");window.__qa.ready()');
  const image=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:true},session);fs.writeFileSync(path.join(out,'internal-review.png'),Buffer.from(image.data,'base64'));
  await evaluate('window.__qa.warp("shop");window.__qa.enter('+JSON.stringify(fixture.content.buildings.shop[0])+');window.__qa.set({x:8,y:11});window.__qa.restore()');
  assert.equal((await evaluate('window.__qa.pos()')).zone,'inside:shop');assert.equal((await evaluate('window.__qa.pos()')).building[4],'베이커리');
  assert.equal(errors.length,0);fs.writeFileSync(path.join(out,'journey.json'),JSON.stringify({ended:true,decisions:Object.keys(payload.state.decisions),concepts:payload.state.concepts,community:payload.state.community,errors:errors.length},null,2));console.log('Real Canvas UI -> reducer -> SQLite -> restored UI: full journey and all witness choices passed');
 }
 if(process.argv.includes('--soak')){
  await evaluate('window.__perf={active:false,frames:[],draw:[],last:0}');
  for(let minute=0;minute<20;minute++){
   for(let chunk=0;chunk<3;chunk++){await evaluate('window.__qa.release();window.__qa.press('+JSON.stringify(minute%2?'left':'right')+')');await delay(20000);}
   const memory=(await cdp('Runtime.getHeapUsage',{},session)).usedSize;fs.appendFileSync(path.join(out,'soak.jsonl'),JSON.stringify({minute:minute+1,memory,errors:errors.length})+'\n');
   await evaluate('window.__qa.release();window.__qa.warp('+JSON.stringify(['square','shop','work','home','welfare','river'][minute%6])+')');console.log('20-minute soak:',minute+1,'minutes');
  }
 }
 console.log(JSON.stringify({browser:version.product,samples:rows.length,errors:errors.length}));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1}).finally(async()=>{try{await cdp('Browser.close')}catch{}child.kill();});
