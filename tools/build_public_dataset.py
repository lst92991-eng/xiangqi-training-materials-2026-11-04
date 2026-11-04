"""Build canonical 14-class YOLO data from downloaded archives. Does not train.
Requires Pillow. Originals remain unchanged. Re-run into a NEW output directory.
"""
import argparse, collections, hashlib, io, json, math, re, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

CLASSES=list('kabnrcpKABNRCP')
CN=['黑将','黑士','黑象','黑马','黑车','黑炮','黑卒','红帅','红仕','红相','红马','红车','红炮','红兵']
WOOD=dict(zip('b_jiang b_shi b_xiang b_ma b_che b_pao b_zu r_shuai r_shi r_xiang r_ma r_che r_pao r_bing'.split(),range(14)))
FPT=dict(zip('vua_den si_den tuong_den ma_den xe_den phao_den tot_den vua_do si_do tuong_do ma_do xe_do phao_do tot_do'.split(),range(14)))
VICTOR={0:1,1:5,2:4,3:2,4:0,5:3,6:6,8:8,9:12,10:11,11:9,12:7,13:10,14:13}
BAD='92.rf.b1ff3d95f5ac210d5ccd91f87c838b91.jpg'

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def group_split(source,parent,original_split):
    m=re.search(r'(20\d{6})_\d{6}',parent)
    if source=='wood' and m:
        day=m.group(1)
        return 'wood_day_'+day, {'20260711':'val','20260715':'test'}.get(day,'train')
    if source=='fpt' and m:
        day=m.group(1)
        return 'fpt_day_'+day, {'20260605':'val','20260610':'test'}.get(day,'train')
    # Unknown acquisition sessions are all training-only, including legacy data.
    return source+'_unknown_session','train'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wood',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); root=Path(__file__).resolve().parent.parent
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    sources=[('wood',a.wood,WOOD),('fpt',root/'07_完整外部数据集/FPT_v5_1645_COCO_原始导出.zip',FPT),('viktor',root/'07_完整外部数据集/ViktorNg_200_YOLO_原始导出.zip',None),('legacy',root/'02_旧数据原包/yolo14-v1.zip',None)]
    records=[];issues=[];hashes={};crops=collections.defaultdict(list);source_meta=[];removed_intersections=0;clipped=0
    for source,archive,mapping in sources:
        print('Reading',source,flush=True)
        source_meta.append(dict(source=source,archive=archive.name,sha256=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()))
        with zipfile.ZipFile(archive) as z:
            entries=[]
            for name in z.namelist():
                if name.endswith(('README.dataset.txt','README.roboflow.txt','data.yaml','_annotations.coco.json')):
                    dest=out/'source_metadata'/source/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
                if mapping is not None and name.endswith('_annotations.coco.json'):
                    d=json.loads(z.read(name)); cats={x['id']:x['name'] for x in d['categories']};anns=collections.defaultdict(list)
                    for ann in d['annotations']:anns[ann['image_id']].append(ann)
                    for im in d['images']:
                        n=str(Path(name).parent/im['file_name']).replace('\\','/')
                        entries.append((n,im['width'],im['height'],im.get('extra',{}).get('name',im['file_name'].split('.rf.')[0]),anns[im['id']],cats))
            if mapping is None:
                for n in sorted(z.namelist()):
                    if '/images/' in '/'+n and n.lower().endswith(('.jpg','.png','.jpeg')):
                        if Path(n).name==BAD:
                            issues.append(dict(source=source,image=n,reason='known incorrect red-general annotation'));continue
                        entries.append((n,None,None,Path(n).name.split('.rf.')[0],None,None))
            (out/'images'/source).mkdir(parents=True,exist_ok=True);(out/'labels'/source).mkdir(parents=True,exist_ok=True)
            for i,(n,mw,mh,parent,anns,cats) in enumerate(entries):
                try:
                    raw=z.read(n)
                    with Image.open(io.BytesIO(raw)) as tmp: im=tmp.convert('RGB');im.load()
                    w,h=im.size
                    if mw is not None and (w,h)!=(mw,mh):raise ValueError('COCO/image dimension mismatch')
                    boxes=[]; adjustments=0
                    if mapping is not None:
                        for ann in anns:
                            cname=cats[ann['category_id']]
                            if cname not in mapping:raise ValueError('Unknown annotated category: '+cname)
                            x,y,bw,bh=map(float,ann['bbox'])
                            if not all(math.isfinite(v) for v in (x,y,bw,bh)) or bw<=0 or bh<=0:raise ValueError('invalid bbox')
                            x2,y2=x+bw,y+bh
                            # Only accept <= 1 pixel rounding overflow; larger errors quarantine the image.
                            if min(x,y)<-1.01 or x2>w+1.01 or y2>h+1.01:raise ValueError('bbox beyond image by >1px')
                            nx,ny,nx2,ny2=max(0,x),max(0,y),min(w,x2),min(h,y2)
                            if (nx,ny,nx2,ny2)!=(x,y,x2,y2):adjustments+=1
                            if nx2<=nx or ny2<=ny:raise ValueError('empty clipped bbox')
                            boxes.append((mapping[cname],(nx+nx2)/2/w,(ny+ny2)/2/h,(nx2-nx)/w,(ny2-ny)/h))
                    else:
                        ln=n.replace('/images/','/labels/') if source=='viktor' else n.replace('images/','labels/',1)
                        ln=str(Path(ln).with_suffix('.txt')).replace('\\','/')
                        for line in z.read(ln).decode('utf-8-sig').splitlines():
                            if not line.strip():continue
                            v=line.split()
                            if len(v)!=5:raise ValueError('malformed YOLO row')
                            c=int(v[0]);cx,cy,bw,bh=map(float,v[1:])
                            if source=='viktor' and c==7:removed_intersections+=1;continue
                            c=VICTOR[c] if source=='viktor' else c
                            if not 0<=c<14 or not all(math.isfinite(v) for v in (cx,cy,bw,bh)) or min(bw,bh)<=0 or min(cx-bw/2,cy-bh/2)<-0.0001 or max(cx+bw/2,cy+bh/2)>1.0001:raise ValueError('invalid YOLO box')
                            boxes.append((c,cx,cy,bw,bh))
                    if not boxes:raise ValueError('no piece labels; requires manual negative confirmation')
                    original_split=next((s for s in n.split('/') if s in ('train','valid','val','test')),'train')
                    group,split=group_split(source,parent,original_split)
                    eligible=not(split in ('val','test') and original_split=='train')
                    pixel_hash=hashlib.sha256(f'{w},{h}:'.encode()+im.tobytes()).hexdigest()
                    signature=sorted(tuple([b[0]]+[round(v,4) for v in b[1:]]) for b in boxes)
                    rec=dict(source=source,archive_member=n,parent=parent,group=group,original_split=original_split,split=split,eligible=eligible,width=w,height=h,pixel_sha256=pixel_hash,boxes=len(boxes),class_counts=dict(collections.Counter(b[0] for b in boxes)),clipped_rounding_boxes=adjustments)
                    filename=f'{i:05d}_'+Path(n).name
                    rel='images/'+source+'/'+filename;rec['image']=rel
                    rec['label']='labels/'+source+'/'+Path(filename).stem+'.txt'
                    if pixel_hash in hashes:
                        old,old_sig=hashes[pixel_hash]
                        if old_sig!=signature:
                            old['eligible']=False;old['exclusion']='duplicate_pixels_label_conflict';rec['eligible']=False;rec['exclusion']='duplicate_pixels_label_conflict'
                        else:
                            rec['eligible']=False;rec['exclusion']='exact_pixel_duplicate'
                            if old['split']!=split:old['eligible']=False;old['exclusion']='duplicate_pixels_cross_split'
                        issues.append(dict(source=source,image=n,reason=rec['exclusion'],duplicate_of=old['image']))
                    else:hashes[pixel_hash]=(rec,signature)
                    if not eligible:rec.setdefault('exclusion','heldout_session_training_augmentation')
                    (out/rel).write_bytes(raw)
                    (out/rec['label']).write_text(''.join(f'{b[0]} '+ ' '.join(f'{v:.8f}' for v in b[1:])+'\n' for b in boxes),encoding='utf-8')
                    records.append(rec);clipped+=adjustments
                    # Deterministic spread across parent names, not adjacent augmentations.
                    if int(hashlib.sha256(parent.encode()).hexdigest()[:8],16)%19==0:
                        for c,cx,cy,bw,bh in boxes:
                            key=(source,c)
                            if len(crops[key])<6 and not any(t[0]==parent for t in crops[key]):
                                box=((cx-bw/2)*w,(cy-bh/2)*h,(cx+bw/2)*w,(cy+bh/2)*h)
                                crops[key].append((parent,ImageOps.contain(im.crop(box),(88,88)),n))
                except Exception as e:
                    issues.append(dict(source=source,image=n,reason=str(e)))
                if (i+1)%500==0:print(source,i+1,'/',len(entries),'issues',len(issues),flush=True)
        print('Finished',source,flush=True)
    splits={s:[] for s in ('train','val','test')};counts={s:[0]*14 for s in splits}
    for r in records:
        if r['eligible']:
            splits[r['split']].append('./'+r['image'])
            for c,v in r['class_counts'].items():counts[r['split']][int(c)]+=v
    for s,paths in splits.items():(out/(s+'.txt')).write_text('\n'.join(paths)+'\n',encoding='utf-8')
    for source,_,_ in sources:
        sheet=Image.new('RGB',(650,14*110),'white');draw=ImageDraw.Draw(sheet)
        index=[]
        for c in range(14):
            draw.text((2,c*110+4),f'{c} {CLASSES[c]}',fill='black')
            for j,(parent,im,n) in enumerate(crops[(source,c)]):
                sheet.paste(im,(65+j*96,c*110+18));index.append(dict(class_id=c,column=j,image=n,parent=parent))
        dest=out/'audit_previews';dest.mkdir(exist_ok=True);sheet.save(dest/(source+'_class_crops.jpg'),quality=92);dump(dest/(source+'_class_crops_index.json'),index)
    summary=dict(total_converted_images=len(records),recommended_images=sum(map(len,splits.values())),splits={s:len(v) for s,v in splits.items()},class_box_counts=counts,source_converted=dict(collections.Counter(r['source'] for r in records)),source_recommended=dict(collections.Counter(r['source'] for r in records if r['eligible'])),source_parent_names={src:len({r['parent'] for r in records if r['source']==src}) for src,_,_ in sources},exclusions=dict(collections.Counter(r.get('exclusion','') for r in records if not r['eligible'])),issues=len(issues),removed_intersection_boxes=removed_intersections,rounding_clipped_boxes=clipped,classes=CLASSES)
    dump(out/'summary.json',summary);dump(out/'manifest.json',records);dump(out/'issues.json',issues);dump(out/'source_archives.json',source_meta)
    (out/'data.yaml').write_text('path: .\ntrain: train.txt\nval: val.txt\ntest: test.txt\nnc: 14\nnames: '+json.dumps(CLASSES)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
