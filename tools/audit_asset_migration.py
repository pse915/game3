"""Validate all source mappings, images, dimensions, and code-facing asset references."""
from pathlib import Path
from PIL import Image
import hashlib, json, re, sys
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'frontend'/'assets'
MAP=ROOT/'docs'/'3-3game_에셋_매핑.json'
manifest=json.loads((DIR/'manifest.json').read_text(encoding='utf-8'))
record=json.loads(MAP.read_text(encoding='utf-8'))
legacy=DIR/'legacy_game2'
errors=[]
for name, item in record['mapping'].items():
    p=DIR/f'{name}.png';old=legacy/f'{name}.png'
    if not p.exists() or not old.exists():errors.append(f'{name}: active or legacy missing');continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:errors.append(f'{name}: output SHA differs')
    if hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(old.read_bytes()).hexdigest():errors.append(f'{name}: unchanged legacy pixels')
    with Image.open(p) as im:
        if list(im.size)!=item['size']:errors.append(f'{name}: dimension mismatch')
    if name not in manifest['assets']:errors.append(f'{name}: missing manifest metadata')
for prefix,expected in [('avatar_',6),('teacher_',19),('building_',13),('interior_',13),('school_room_',11),('school_hall_',4),('tree_',3)]:
    matched=[n for n in record['mapping'] if n.startswith(prefix)]
    if len(matched)!=expected:errors.append(f'{prefix}: {len(matched)} != {expected}')
for r in ['donor_terrain','donor_fountain','donor_bench','donor_flowerbed','donor_lamp','donor_diary-panel','donor_ui-icons']:
    if not (DIR/(r+'.png')).is_file():errors.append('missing donor runtime '+r)
js=(ROOT/'frontend'/'game.js').read_text(encoding='utf-8')
css=(ROOT/'frontend'/'style.css').read_text(encoding='utf-8')
for name in ['donor_terrain','donor_fountain','donor_flowerbed','donor_lamp','donor_bench']:
    if name not in js:errors.append('JS missing donor asset '+name)
for name in ['donor_diary-panel','donor_ui-icons']:
    if name not in css:errors.append('CSS missing donor asset '+name)
print(json.dumps({'status':'PASS' if not errors else 'FAIL','active_legacy_assets_replaced':len(record['mapping']),'runtime_donor_resources':7,'old_assets_preserved':len(list(legacy.glob('*.png'))),'errors':errors},ensure_ascii=False,indent=2))
sys.exit(bool(errors))
