"""Convert the licensed 3-3game art atlases into game2's stable image contracts.

Usage: python tools/migrate_3_3_assets.py /path/to/3-3game-main
Run on a clean copy of game2; each generated file keeps the exact game2 dimensions.
Non-image gameplay, saved records and map coordinates are untouched.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'frontend'/'assets'
BACKUP=OUT/'legacy_game2'
TARGET=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT.parent/'3-3game-main'
SOURCE=TARGET/'components'/'rpg_game'/'assets'
if not (SOURCE/'avatars.png').is_file():
    raise SystemExit('3-3game 에셋 폴더를 찾지 못했습니다: '+str(SOURCE))
BACKUP.mkdir(exist_ok=True)
ATLAS={}
for a in ['avatars','npcs','terrain','environment','buildings','furniture','facilities','details','school','ui-icons','diary-panel']:
    ATLAS[a]=Image.open(SOURCE/(a+'.png')).convert('RGBA')

# Keep exact old dimensions: the game2 Canvas renderer and hitboxes depend on them.
original={p.stem: Image.open(p).size for p in OUT.glob('*.png') if not p.stem.startswith('donor_')}
for old in OUT.glob('*.png'):
    if old.stem.startswith('donor_'): continue
    b=BACKUP/old.name
    if not b.exists():shutil.copy2(old,b)

mapping={}
newfiles=set()

def save(name, image, provenance, method):
    assert name in original, f'Unknown game2 asset: {name}'
    target=original[name]
    if image.size != target: raise AssertionError((name,image.size,target))
    image.save(OUT/(name+'.png'),optimize=True)
    newfiles.add(name)
    mapping[name]={"source":provenance,"method":method,"size":list(image.size),"sha256":hashlib.sha256((OUT/(name+'.png')).read_bytes()).hexdigest()}

def atlas_cell(atlas, i, *, cols=4, cell=256):
    img=ATLAS[atlas]
    return img.crop(((i%cols)*cell,(i//cols)*cell,(i%cols+1)*cell,(i//cols+1)*cell))

def trim(img):
    box=img.getchannel('A').getbbox()
    return img.crop(box) if box else img

def fit(img,w,h,pad=0):
    img=trim(img)
    scale=min((w-pad*2)/img.width,(h-pad*2)/img.height)
    nw=max(1,round(img.width*scale));nh=max(1,round(img.height*scale))
    return img.resize((nw,nh),Image.Resampling.NEAREST)

def alpha_place(base,img,box, anchor='bottom'):
    x,y,w,h=box
    s=fit(img,w,h)
    yy=y+(h-s.height if anchor=='bottom' else (h-s.height)//2)
    xx=x+(w-s.width)//2
    base.alpha_composite(s,(int(xx),int(yy)))

def tile(img,idx,xy):
    x,y=xy
    img.alpha_composite(ATLAS['terrain'].crop((idx*32,0,idx*32+32,32)),(x,y))

def blank_room(kind, corridor=False, floor=1):
    w,h=960,608
    scene=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(scene)
    palette={'hall':(5,2),'classroom':(5,4),'science':(5,2),'technology':(5,2),'computer':(5,2),'homemaking':(5,4),'music':(5,4),'art':(5,4),'health':(5,5),'library':(5,4),'counsel':(5,4),'office':(5,2),'gym':(5,8),'bread':(5,4),'cafe':(5,4),'care':(5,4),'clinic':(5,2),'closed':(5,2),'factory':(5,2),'home':(5,4),'house':(5,4),'theater':(5,9),'school':(5,4)}
    wall,flooridx=palette.get(kind,(5,4))
    for y in range(0,h,32):
        for x in range(0,w,32):
            tile(scene,wall if y<224 else flooridx,(x,y))
    # Wall trim and a clearly defined floor plane, drawn in palette colors.
    d.rectangle((0,0,w-1,11),fill=(92,78,70));d.rectangle((0,197,w-1,209),fill=(122,91,71));
    d.rectangle((0,210,w-1,225),fill=(207,172,130));d.rectangle((0,h-5,w-1,h-1),fill=(114,87,68))
    for x in range(32,w,160):
        d.line((x,226,x,h-6),fill=(202,181,152,255),width=2)
    for y in range(254,h,64):d.line((0,y,w,y),fill=(220,201,178,255),width=2)
    # Glazed window segments for depth.
    for x in (46,824):
        d.rectangle((x,48,x+85,183),fill=(101,79,64));d.rectangle((x+6,55,x+79,174),fill=(136,188,193))
        d.rectangle((x+40,55,x+44,174),fill=(240,223,179));d.rectangle((x+6,109,x+79,114),fill=(240,223,179))
    return scene

# These 16 positions are real 3-3game object-atlas cells.
CLASS_OBJECTS={'classroom':[('environment',10,(346,60,266,176)),('details',8,(140,316,102,85)),('details',8,(370,316,102,85)),('details',8,(596,316,102,85)),('details',8,(140,455,102,85)),('details',8,(370,455,102,85)),('details',8,(596,455,102,85)),('furniture',3,(660,99,122,120))],
 'science':[('environment',10,(351,68,270,174)),('facilities',9,(150,310,185,149)),('facilities',10,(371,310,178,149)),('facilities',11,(591,310,177,147)),('details',3,(725,110,91,92))],
 'technology':[('furniture',5,(320,70,210,153)),('details',7,(110,320,245,145)),('environment',13,(420,320,172,142)),('facilities',15,(645,310,141,154))],
 'computer':[('furniture',5,(350,70,240,164)),('environment',13,(145,345,186,154)),('environment',13,(405,335,183,155)),('environment',13,(654,346,163,143))],
 'homemaking':[('facilities',8,(290,70,264,159)),('furniture',7,(300,345,256,180)),('furniture',0,(620,352,164,136))],
 'music':[('furniture',4,(342,53,279,184)),('facilities',13,(198,333,155,173)),('facilities',14,(424,328,158,173)),('facilities',13,(652,331,155,173))],
 'art':[('furniture',5,(390,54,193,166)),('furniture',6,(150,295,173,220)),('furniture',6,(427,296,173,220)),('furniture',6,(705,298,172,218))],
 'health':[('facilities',2,(293,68,323,183)),('furniture',2,(297,358,253,174)),('details',3,(641,75,148,138))],
 'library':[('environment',3,(156,55,189,187)),('details',7,(389,55,193,192)),('furniture',15,(637,75,183,177)),('furniture',1,(313,346,320,200))],
 'counsel':[('furniture',1,(295,64,328,203)),('furniture',0,(321,338,291,190)),('details',8,(719,338,144,161))],
 'office':[('furniture',12,(190,60,192,191)),('environment',13,(392,76,211,165)),('furniture',15,(657,71,171,186)),('furniture',7,(333,356,291,163))],
 'gym':[('details',9,(192,300,162,210)),('details',9,(404,302,162,210)),('facilities',14,(590,65,161,199))],
 'bread':[('environment',12,(324,65,295,202)),('furniture',0,(194,363,216,173)),('furniture',0,(516,363,216,173))],
 'cafe':[('environment',12,(300,58,346,205)),('furniture',0,(179,348,210,185)),('furniture',0,(582,348,210,185))],
 'care':[('furniture',9,(331,50,296,192)),('furniture',10,(196,342,207,185)),('details',10,(534,338,201,180))],
 'clinic':[('facilities',2,(316,66,322,203)),('furniture',4,(192,345,205,191)),('details',3,(645,75,150,147))],
 'closed':[('details',0,(326,67,292,194)),('furniture',7,(325,359,262,154))],
 'factory':[('facilities',9,(200,325,247,192)),('facilities',10,(490,329,233,192)),('details',4,(366,73,214,149))],
 'home':[('furniture',1,(299,58,324,194)),('furniture',2,(333,335,288,193)),('furniture',0,(131,371,156,159))],
 'house':[('furniture',1,(296,66,335,199)),('furniture',2,(340,355,261,182)),('furniture',0,(141,369,154,149))],
 'theater':[('furniture',4,(340,59,274,216)),('furniture',0,(256,356,200,169)),('furniture',0,(548,356,200,169))],
 'school':[('environment',10,(337,58,291,175)),('furniture',0,(219,348,198,157)),('furniture',0,(522,349,198,157))]}

# Player: 6 true 4-direction 32x48 animation strips. The donor 8x4 layout
# exposes frames 0-3 for walking; keep destination 4x4 sprite contract.
for a in range(6):
    image=Image.new('RGBA',(128,192))
    src=ATLAS['avatars']
    for direction in range(4):
        patch=src.crop((0,a*192+direction*48,128,a*192+(direction+1)*48))
        image.alpha_composite(patch,(0,direction*48))
    save('avatar_'+str(a),image,f'avatars.png avatar={a} cols=0..3','original 4-direction 16-frame sprite crop')

# Teachers use 19 distinct NPC faces. 3-3game contains 35 front-idle frames, not
# 4-direction walking animations. Horizontal flip creates turn variation; do not
# claim donor directional animation exists.
from PIL import ImageEnhance
for a in range(19):
    index=a%35
    cell=ATLAS['npcs'].crop(((index%7)*32,(index//7)*48,(index%7+1)*32,(index//7+1)*48))
    image=Image.new('RGBA',(128,192))
    for r in range(4):
        for col in range(4):
            sprite=cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if r==1 or (r==3 and col%2) else cell
            if r==2:sprite=cell
            image.alpha_composite(sprite,(col*32,r*48+(col%2)))
    save('teacher_'+str(a).zfill(2),image,f'npcs.png front-only variant={index}','front-idle adaptation; side/back approximate')

# These legacy PNGs were loaded by older code and appear in the manifest even if
# one is no longer used. Rebuild both for complete on-disk migration coverage.
for a in (17,18):
    assert 'teacher_'+str(a) in newfiles

BUILDINGS={'bread':('buildings',10),'cafe':('buildings',0),'care':('buildings',7),
           'clinic':('buildings',8),'closed':('buildings',13),'factory':('buildings',12),
           'hall':('buildings',6),'home':('buildings',1),'house':('buildings',3),
           'library':('buildings',9),'office':('buildings',2),'school':('school',0),
           'theater':('buildings',5)}
for kind,(atlas,index) in BUILDINGS.items():
    image=Image.new('RGBA',original['building_'+kind])
    src=ATLAS['school'] if atlas=='school' else atlas_cell(atlas,index)
    alpha_place(image,src,(5,0,image.width-10,image.height-4))
    save('building_'+kind,image, f'{atlas}.png '+('whole school facade' if atlas=='school' else f'cell {index}'), 'alpha-trim + nearest-neighbor scale')
# Facade is L shaped and red-brick in 3-3game, without replacing the school layout.
image=Image.new('RGBA',original['school_exterior']);alpha_place(image,ATLAS['school'],(0,0,*image.size))
save('school_exterior',image,'school.png whole facade','transparent facade resized into existing 480x288 canvas')

for idx,name in enumerate(['tree_0','tree_1','tree_2']):
    src=atlas_cell('environment',0 if idx!=1 else 1)
    if idx==2:src=src.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    image=Image.new('RGBA',original[name]);alpha_place(image,src,(0,0,*image.size))
    save(name,image,f'environment.png cell {0 if idx!=1 else 1}', 'scaled tree sprite')

for floor in range(1,5):
    img=blank_room('hall',corridor=True,floor=floor)
    d=ImageDraw.Draw(img)
    # A large L-corridor perspective, already retained in game2 logical paths.
    d.rectangle((17,18,226,208),fill=(79,73,73));d.rectangle((28,28,216,199),fill=(216,200,170))
    for x in [45,109,174]:
        d.rectangle((x,79,x+34,190),fill=(123,96,74));d.rectangle((x+4,83,x+30,174),fill=(146,197,202))
    for x in range(272,943,110):
        d.rectangle((x,94,x+60,205),fill=(104,85,72));d.rectangle((x+5,98,x+55,199),fill=(214,200,172))
        d.rectangle((x+10,122,x+42,179),fill=(122,162,162))
    # Center ornamental objects are furniture from the donor atlas.
    for atlas,cell,box in [('details',11,(80,321,125,142)),('furniture',15,(328,281,143,176)),('details',7,(580,293,139,168)),('environment',11,(766,292,131,178))]:
        alpha_place(img,atlas_cell(atlas,cell),box)
    save('school_hall_'+str(floor),img, f'terrain.png; details.png; furniture.png; environment.png (floor {floor})', 'composite corridor from donor textures and sprites')

def room_image(kind):
    img=blank_room(kind)
    for atlas,idx,box in CLASS_OBJECTS.get(kind,CLASS_OBJECTS['office']):
        alpha_place(img,atlas_cell(atlas,idx),box)
    return img
save('school_classroom',room_image('classroom'),'terrain.png; environment.png; furniture.png', 'donor-composited classroom')
for special in ['science','technology','homemaking','computer','music','art','health','library','counsel','office','gym']:
    save('school_room_'+special,room_image(special),'terrain.png; '+', '.join(sorted(set(a+'.png' for a,_,_ in CLASS_OBJECTS[special]))), 'donor-composited special room')
INTERIOR={'bread':'bread','cafe':'cafe','closed':'closed','hall':'office','library':'library','factory':'factory','office':'office','home':'home','house':'house','clinic':'clinic','care':'care','school':'school','theater':'theater'}
for kind,theme in INTERIOR.items():
    save('interior_'+kind,room_image(theme),'terrain.png; '+', '.join(sorted(set(a+'.png' for a,_,_ in CLASS_OBJECTS[theme]))), 'donor-composited interior')

# Runtime tiles and object decorations: use the exact donor texture, not copies of
# flat programmatic legacy tiles. Slices are from the donor's object atlases.
shutil.copy2(SOURCE/'terrain.png',OUT/'donor_terrain.png')
for n,atlas,idx in [('donor_fountain','environment',8),('donor_bench','environment',9),('donor_flowerbed','details',13),('donor_lamp','furniture',14)]:
    cropped=trim(atlas_cell(atlas,idx));cropped.save(OUT/(n+'.png'),optimize=True)
for n in ['diary-panel','ui-icons']:
    shutil.copy2(SOURCE/(n+'.png'),OUT/('donor_'+n+'.png'))

# Preserve game2's metadata shape, update source attribution and sha.
manifest_path=OUT/'manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
for name,info in mapping.items():
    if name in manifest['assets']:
        item=manifest['assets'][name]
        item.update(source='3-3game/'+info['source'],license='Imported from user-provided 3-3game repository; original licensing must be verified for redistribution',pixel_scale=1)
        item['migration_method']=info['method'];item['sha256']=info['sha256']
manifest['migration']={'donor':'https://github.com/pse915/3-3game','generated_file_count':len(newfiles),'strategy':'Preserve game2 stable image dimensions/IDs and replace all active visual sources','license_note':'Verify donor asset rights before public redistribution'}
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'original_png_count':len(original),'mapped_png_count':len(newfiles),'unmapped':sorted(set(original)-newfiles),'mapping':mapping,'donor_runtime_files':['donor_terrain.png','donor_fountain.png','donor_bench.png','donor_flowerbed.png','donor_lamp.png','donor_diary-panel.png','donor_ui-icons.png']}
(ROOT/'docs'/'3-3game_에셋_매핑.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Migrated',len(newfiles),'of',len(original),'active PNGs. Missing:',report['unmapped'])
