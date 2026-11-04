"""Assemble reviewed additions with the preserved base YOLO14 split; never train.

Requires Pillow. Paths in reviews.csv are relative to the package root.
Unreviewed images are not negative examples and are never copied to data_ready.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import zipfile

from PIL import Image

CLASSES = list('kabnrcpKABNRCP')
BAD_BASE_IMAGE = '92.rf.b1ff3d95f5ac210d5ccd91f87c838b91.jpg'


def labels(text, allow_negative=False):
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if not lines and not allow_negative:
        raise ValueError('Empty labels require negative_confirmed=yes')
    for line in lines:
        values = line.split()
        if len(values) != 5 or not values[0].isdigit():
            raise ValueError('YOLO line must be class_id cx cy width height')
        cls = int(values[0])
        cx, cy, w, h = map(float, values[1:])
        if not 0 <= cls < 14 or not all(math.isfinite(x) for x in (cx,cy,w,h)):
            raise ValueError('Invalid class or nonfinite coordinate')
        if not 0 <= cx <= 1 or not 0 <= cy <= 1 or not 0 < w <= 1 or not 0 < h <= 1:
            raise ValueError('Invalid normalized bounding box')
        if min(cx-w/2,cy-h/2) < -1e-4 or max(cx+w/2,cy+h/2) > 1.0001:
            raise ValueError('Bounding box extends outside image')
    return '\n'.join(lines)+'\n' if lines else ''


def inside(root, relative):
    path = (root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path outside package: '+relative)
    return path


def pixels(data):
    with Image.open(io.BytesIO(data)) as im:
        im = im.convert('RGB')
        return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reviews',type=Path,default=Path(__file__).with_name('reviews.csv'))
    p.add_argument('--output',type=Path)
    p.add_argument('--check-only',action='store_true')
    args = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    pool = {r['image']:r['group_id'] for r in json.loads(
        (root/'01_本机实拍/crop-provenance.json').read_text(encoding='utf-8'))}
    external = json.loads((root/'03_相似公开实拍/ORIGINAL-SOURCES.json').read_text(encoding='utf-8'))
    for r in external:
        if r.get('training_candidate'):
            pool['03_相似公开实拍/'+r['file']] = 'finaltest-public-samples'
    accepted, groups, seen_rows = [], {}, set()
    for r in csv.DictReader(args.reviews.open(encoding='utf-8-sig',newline='')):
        if r['reviewed'].strip().lower() != 'yes':
            continue
        if r['image'] not in pool or r['image'] in seen_rows:
            raise ValueError('Unknown or duplicate image in review table: '+r['image'])
        seen_rows.add(r['image'])
        if not r['reviewer'].strip() or not r['label'].strip():
            raise ValueError('Reviewed image requires reviewer and label path')
        if r['group_id'] != pool[r['image']] or r['split'] not in ('train','val','test'):
            raise ValueError('Invalid group or split')
        if r['group_id'] in groups and groups[r['group_id']] != r['split']:
            raise ValueError('One capture/source group cannot cross train/val/test')
        groups[r['group_id']] = r['split']
        image = inside(root,r['image']); label = inside(root,r['label'])
        if not image.is_file() or not label.is_file():
            raise ValueError('Missing reviewed image or label')
        text = labels(label.read_text(encoding='utf-8-sig'),r['negative_confirmed'].lower()=='yes')
        accepted.append((r,image.read_bytes(),text))
    if not args.check_only and not accepted:
        raise ValueError('No reviewed additions. Annotate new images first; base-only retraining is not the requested remedy.')
    records, hashes, class_counts = [], {}, Counter()
    items = []
    def add(name, split, image, text, source, group):
        sha = pixels(image)
        if sha in hashes:
            if hashes[sha] != split:
                raise ValueError('Identical image pixels cross splits: '+source)
            return  # Exact duplicate within split is unnecessary.
        hashes[sha] = split
        for line in text.splitlines():
            if line.strip():class_counts[int(line.split()[0])] += 1
        items.append((name,split,image,text))
        records.append(dict(name=name,split=split,source=source,group_id=group,pixel_sha256=sha))
    with zipfile.ZipFile(root/'02_旧数据原包/yolo14-v1.zip') as z:
        for name in sorted(z.namelist()):
            if not name.startswith('images/') or not name.lower().endswith(('.jpg','.png','.jpeg')):
                continue
            _, split, filename = name.split('/')
            if split == 'train' and filename == BAD_BASE_IMAGE:
                continue
            label = 'labels/'+split+'/'+Path(filename).stem+'.txt'
            text = labels(z.read(label).decode('utf-8-sig'))
            add('base_'+filename,split,z.read(name),text,'base_zip:'+name,'base_frozen_'+split)
    for i,(r,image,text) in enumerate(accepted):
        add(f'extra_{i:04d}_'+Path(r['image']).name,r['split'],image,text,r['image'],r['group_id'])
    summary = dict(base_known_issue_excluded=BAD_BASE_IMAGE,reviewed_additions=len(accepted),
                   output_images=len(items),splits=dict(Counter(x[1] for x in items)),
                   class_box_counts={CLASSES[i]:class_counts[i] for i in range(14)},
                   note='Exact pixel duplicate check only; review near duplicates and collect a separate current-camera holdout session.')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if args.check_only:
        print('CHECK ONLY: no dataset written; no training performed.')
        return
    if args.output is None:
        p.error('--output is required to write a new dataset directory')
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    for name,split,image,text in items:
        for kind in ('images','labels'):(out/kind/split).mkdir(parents=True,exist_ok=True)
        (out/'images'/split/name).write_bytes(image)
        (out/'labels'/split/(Path(name).stem+'.txt')).write_text(text,encoding='utf-8')
    yaml='path: '+json.dumps(str(out),ensure_ascii=False)+'\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 14\nnames: '+json.dumps(CLASSES)+'\n'
    (out/'data.yaml').write_text(yaml,encoding='utf-8')
    (out/'manifest.json').write_text(json.dumps(dict(summary=summary,images=records),indent=2,ensure_ascii=False),encoding='utf-8')
    print('Prepared dataset:',out)


if __name__ == '__main__':
    main()
