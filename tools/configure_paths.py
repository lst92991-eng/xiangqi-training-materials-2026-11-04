"""Run once after copying this package to the training computer. No training."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
data=root/'08_YOLO14_主数据'
assert (data/'summary.json').is_file(), 'Complete dataset is missing'
for split in ('train','val','test'):
    paths=[]
    for row in (data/(split+'.txt')).read_text(encoding='utf-8').splitlines():
        p=(data/row).resolve()
        assert p.is_relative_to(data.resolve()) and p.is_file(), 'Missing image: '+row
        assert (data/'labels'/p.relative_to(data/'images')).with_suffix('.txt').is_file()
        paths.append(p.as_posix())
    (data/(split+'.absolute.txt')).write_text('\n'.join(paths)+'\n',encoding='utf-8')
text='path: '+json.dumps(data.as_posix(),ensure_ascii=False)+'\n'
for split in ('train','val','test'):text+=split+': '+split+'.absolute.txt\n'
text+='nc: 14\nnames: '+json.dumps(list('kabnrcpKABNRCP'))+'\n'
(data/'data.local.yaml').write_text(text,encoding='utf-8')
print('Use this data file:',data/'data.local.yaml')
print('Paths verified; no training started.')
