"""Download the public release, verify SHA256, combine and extract. Never trains.
Python 3.9+; standard library only. Re-run to resume interrupted downloads.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import zipfile


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def download(part,cache):
    dest=cache/part['name'];partial=dest.with_name(dest.name+'.partial')
    if dest.exists():
        if dest.stat().st_size==part['bytes'] and sha256(dest)==part['sha256']:
            print('Verified cached:',dest.name,flush=True);return dest
        raise RuntimeError('Existing file has wrong checksum; inspect/remove it: '+str(dest))
    for attempt in range(5):
        offset=partial.stat().st_size if partial.exists() else 0
        if offset==part['bytes']:
            if sha256(partial)!=part['sha256']:raise RuntimeError('Downloaded checksum mismatch: '+str(partial))
            partial.replace(dest);return dest
        if offset>part['bytes']:raise RuntimeError('Partial download exceeds expected size: '+str(partial))
        headers={'User-Agent':'xiangqi-training-materials-downloader','Accept-Encoding':'identity'}
        if offset:headers['Range']='bytes='+str(offset)+'-'
        request=urllib.request.Request(part['url'],headers=headers)
        try:
            with urllib.request.urlopen(request,timeout=60) as response:
                if response.status==206:
                    if not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                        raise RuntimeError('Server returned an unexpected range')
                    mode='ab'
                elif response.status==200:offset=0;mode='wb'
                else:raise RuntimeError('Unexpected HTTP status: '+str(response.status))
                print('Downloading:',dest.name,'from',offset,'bytes',flush=True)
                last=time.monotonic()
                with partial.open(mode) as f:
                    while block:=response.read(1024*1024):
                        f.write(block);offset+=len(block)
                        if offset>part['bytes']:raise RuntimeError('Download exceeds expected size')
                        if time.monotonic()-last>=10:
                            print(f'{dest.name}: {offset/part["bytes"]:.1%}',flush=True);last=time.monotonic()
            if offset!=part['bytes']:raise IOError('Incomplete response')
            if sha256(partial)!=part['sha256']:raise RuntimeError('Downloaded checksum mismatch: '+str(partial))
            partial.replace(dest);return dest
        except (OSError,TimeoutError) as e:
            print(f'Attempt {attempt+1}/5 failed: {type(e).__name__}; partial data retained.',flush=True)
            if attempt==4:raise
            time.sleep(min(2**attempt,8))
    raise RuntimeError('Download incomplete')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'data')
    p.add_argument('--cache',type=Path,default=Path(__file__).resolve().parent/'.downloads')
    p.add_argument('--download-only',action='store_true')
    a=p.parse_args();repo=Path(__file__).resolve().parent
    meta=json.loads((repo/'release-manifest.json').read_text(encoding='utf-8'))
    cache=a.cache.resolve();cache.mkdir(parents=True,exist_ok=True)
    parts=[download(part,cache) for part in meta['parts']]
    archive=cache/meta['archive']
    if archive.exists():
        if archive.stat().st_size!=meta['bytes'] or sha256(archive)!=meta['sha256']:
            raise RuntimeError('Existing ZIP does not match the manifest: '+str(archive))
    else:
        temp=archive.with_suffix('.zip.partial');h=hashlib.sha256()
        with temp.open('wb') as dst:
            for part in parts:
                with part.open('rb') as src:
                    while block:=src.read(4*1024*1024):dst.write(block);h.update(block)
        if temp.stat().st_size!=meta['bytes'] or h.hexdigest()!=meta['sha256']:
            raise RuntimeError('Combined ZIP failed checksum')
        temp.replace(archive)
    print('Complete ZIP verified:',archive,flush=True)
    if a.download_only:return
    out=a.output.resolve();target=out/meta['extracted_directory']
    marker=out/('.'+meta['extracted_directory']+'.extracted.json')
    if target.exists():
        if not marker.exists() or json.loads(marker.read_text(encoding='utf-8')).get('sha256')!=meta['sha256']:
            raise RuntimeError('Output exists without completion marker; choose a new --output directory: '+str(target))
        print('Using previously extracted dataset:',target,flush=True)
    else:
        out.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                path=(out/member.filename).resolve()
                if not path.is_relative_to(target):raise RuntimeError('Unexpected archive member path')
            print('Extracting verified archive...',flush=True);z.extractall(out)
        marker.write_text(json.dumps({'sha256':meta['sha256']}),encoding='utf-8')
    subprocess.run([sys.executable,str(target/'04_标注与组集/configure_paths.py')],check=True)
    print('\nDataset ready. Training data:',target/'08_YOLO14_主数据/data.local.yaml')
    print('No model training was started.')


if __name__=='__main__':main()
