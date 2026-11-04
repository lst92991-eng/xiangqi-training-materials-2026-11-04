"""Check the original delivered files against SHA256SUMS.txt (before local edits)."""
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent
failed=[];count=0
for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,rel=line.split('  ',1);path=(root/rel).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():failed.append(rel);continue
    with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=digest:failed.append(rel)
    count+=1
    if count%2000==0:print('Checked',count,flush=True)
if failed:raise SystemExit('Missing/changed files: '+repr(failed))
print('PASS:',count,'files match the delivered manifest.')
