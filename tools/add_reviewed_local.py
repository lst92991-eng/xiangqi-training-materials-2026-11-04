"""Append manually approved local captures to the primary dataset. Does not train.
Requires Pillow. After use, rerun configure_paths.py. One local session is TRAIN only.
"""
import csv, hashlib, json
from pathlib import Path
from prepare_dataset import labels, inside, pixels

root=Path(__file__).resolve().parent.parent
data=root/'08_YOLO14_主数据'
target=data/'local_review_manifest.json'
if target.exists():raise SystemExit('Local session already imported; avoid duplicate imports.')
pool={r['image']:r['group_id'] for r in json.loads((root/'01_本机实拍/crop-provenance.json').read_text(encoding='utf-8'))}
accepted=[];seen=set()
for r in csv.DictReader((root/'04_标注与组集/reviews.csv').open(encoding='utf-8-sig',newline='')):
    if r['reviewed'].strip().lower()!='yes':continue
    if r['image'] not in pool:raise ValueError('Only this local session may be imported: '+r['image'])
    if r['image'] in seen:raise ValueError('Duplicate review row')
    seen.add(r['image'])
    if r['group_id']!=pool[r['image']] or r['split']!='train':raise ValueError('Keep this entire capture session in TRAIN; collect a separate session for evaluation.')
    if not r['reviewer'].strip() or not r['label'].strip():raise ValueError('Missing reviewer/label path')
    image=inside(root,r['image']).read_bytes()
    label=labels(inside(root,r['label']).read_text(encoding='utf-8-sig'),r['negative_confirmed'].lower()=='yes')
    pixel_hash=pixels(image)
    if any(x[3]==pixel_hash for x in accepted):raise ValueError('Duplicate local pixels')
    accepted.append((r,image,label,pixel_hash))
if not accepted:raise SystemExit('No manually approved images. Nothing changed.')
# Validate all inputs before writing. New file paths cannot overwrite public images.
for kind in ('images','labels'):(data/kind/'local_reviewed').mkdir(exist_ok=False)
records=[];paths=[]
for i,(r,image,label,pixel_hash) in enumerate(accepted):
    name=f'local_{i:04d}_'+Path(r['image']).name
    rel='images/local_reviewed/'+name
    (data/rel).write_bytes(image)
    (data/'labels/local_reviewed'/Path(name).with_suffix('.txt')).write_text(label,encoding='utf-8')
    records.append(dict(review=r,image=rel,pixel_sha256=pixel_hash,boxes=len(label.splitlines())))
    paths.append('./'+rel)
with (data/'train.txt').open('a',encoding='utf-8') as f:f.write('\n'.join(paths)+'\n')
target.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('Added manually reviewed local training images:',len(records))
print('Public summary.json is the original baseline; local_review_manifest.json records additions.')
print('Run configure_paths.py again. No training was started.')
