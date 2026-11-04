"""Verify all primary image/label pairs, splits, class counts, groups and pixel hashes.
No model loading or training. Image decoding/pixel hashes were checked during build.
"""
import collections,json,math
from pathlib import Path

data=Path(__file__).resolve().parent.parent/'08_YOLO14_主数据'
manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
summary=json.loads((data/'summary.json').read_text(encoding='utf-8'))
groups={};hashes=set();allpaths=set();counts={s:[0]*14 for s in ('train','val','test')}
for r in manifest:
    assert (data/r['image']).is_file() and (data/r['label']).is_file()
    lines=(data/r['label']).read_text(encoding='utf-8').splitlines()
    assert len(lines)==r['boxes'] and lines
    actual=collections.Counter()
    for line in lines:
        vals=line.split();assert len(vals)==5
        c=int(vals[0]);cx,cy,w,h=map(float,vals[1:])
        assert 0<=c<14 and all(math.isfinite(x) for x in (cx,cy,w,h))
        assert w>0 and h>0 and min(cx-w/2,cy-h/2)>=-0.0001 and max(cx+w/2,cy+h/2)<=1.0001
        actual[c]+=1
    assert dict(actual)=={int(c):v for c,v in r['class_counts'].items()}
    if not r['eligible']:continue
    assert r['pixel_sha256'] not in hashes,'Duplicate pixels in active dataset'
    hashes.add(r['pixel_sha256'])
    assert r['group'] not in groups or groups[r['group']]==r['split'],'Capture group crosses splits'
    groups[r['group']]=r['split']
    for c,v in actual.items():counts[r['split']][c]+=v
for split in counts:
    rows=(data/(split+'.txt')).read_text(encoding='utf-8').splitlines()
    expected={'./'+r['image'] for r in manifest if r['eligible'] and r['split']==split}
    assert len(rows)==len(set(rows)) and set(rows)==expected
    assert not allpaths.intersection(rows);allpaths.update(rows)
    assert counts[split]==summary['class_box_counts'][split]
    assert min(counts[split])>0,'A class is absent from this split'
report=dict(status='PASS',converted_images=len(manifest),active_images=len(allpaths),capture_groups=len(groups),splits=summary['splits'],boxes=sum(sum(c) for c in counts.values()),checks=['all YOLO labels finite, valid classes and in-bounds','all image/label paths exist','class totals match manifest','no exact pixel duplicate in active lists','no known capture group crosses splits','all 14 classes present in every split'],limitations=['not exhaustive semantic annotation review','unknown sessions confined to training','near-duplicate scenes not exhaustively detected','requires independent current-camera evaluation'])
(data/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
