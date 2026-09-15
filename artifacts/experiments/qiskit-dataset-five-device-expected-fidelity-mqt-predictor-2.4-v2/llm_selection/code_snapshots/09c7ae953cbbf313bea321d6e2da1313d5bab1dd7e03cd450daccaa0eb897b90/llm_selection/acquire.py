"""Download riprendibile di pesi pubblici con revisioni e SHA-256 verificati."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from .common import OUTPUT, now, read_json, write_json, append_jsonl
MODELS = {
    "qwen": ("Qwen/Qwen3.5-4B", "unsloth/Qwen3.5-4B-GGUF", "Qwen3.5-4B-BF16.gguf"),
    "phi": ("microsoft/Phi-4-mini-instruct", "unsloth/Phi-4-mini-instruct-GGUF", "Phi-4-mini-instruct.BF16.gguf"),
    "gemma": ("google/gemma-4-E4B-it", "ggml-org/gemma-4-E4B-it-GGUF", "gemma-4-E4B-it-BF16.gguf"),
}
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"tesi-llm-validation/1"}), timeout=60) as response:
        return response.read()
def sha(path):
    result=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b""):
            result.update(chunk)
    return result.hexdigest()
def download(url, destination, expected_sha, expected_size, repair_tail=False):
    events=destination.with_suffix(".download_events.jsonl")
    if destination.exists():
        if destination.stat().st_size != expected_size or sha(destination) != expected_sha:
            raise ValueError(f"File esistente alterato: {destination}")
        append_jsonl(events,{"at":now(),"event":"existing_file_verified","sha256":expected_sha})
        return
    partial = destination.with_suffix(".part")
    if partial.exists() and partial.stat().st_size == expected_size:
        observed=sha(partial)
        if observed == expected_sha:
            partial.replace(destination)
            append_jsonl(events,{"at":now(),"event":"completed_partial_verified","sha256":observed})
            return
        append_jsonl(events,{"at":now(),"event":"partial_hash_mismatch","sha256":observed,"size_bytes":expected_size})
        if not repair_tail: raise ValueError("Complete partial failed SHA256; original retained")
    if repair_tail and partial.exists():
        size=partial.stat().st_size
        overlap=min(size,256*1024*1024)
        backup=partial.with_name(partial.name+".interrupted-tail-"+str(size)+"-"+now().replace(":","-"))
        with partial.open("rb") as source, backup.open("xb") as target:
            source.seek(size-overlap)
            while chunk:=source.read(8*1024*1024): target.write(chunk)
            target.flush(); os.fsync(target.fileno())
        append_jsonl(events,{"at":now(),"event":"preserved_and_rewind_uncommitted_tail","old_size_bytes":size,"resume_at":size-overlap,"backup":str(backup)})
        with partial.open("r+b") as stream:
            stream.truncate(size-overlap); stream.flush(); os.fsync(stream.fileno())
    offset=partial.stat().st_size if partial.exists() else 0
    request=urllib.request.Request(url,headers={"User-Agent":"tesi-llm-validation/1",**({"Range":f"bytes={offset}-"} if offset else {})})
    with urllib.request.urlopen(request,timeout=120) as response:
        if response.status == 206 and not response.headers.get("Content-Range","").startswith(f"bytes {offset}-"):
            raise ValueError("Download resume returned a different byte offset")
        if offset and response.status != 206:
            raise ValueError("Server ignored Range; partial retained unchanged")
        append_jsonl(events,{"at":now(),"event":"transfer_started","offset":offset,"status":response.status,"content_range":response.headers.get("Content-Range"),"content_length":response.headers.get("Content-Length")})
        count=offset
        reported=count//(1024**3)
        with partial.open("ab" if offset else "xb") as stream:
            while chunk:=response.read(8*1024*1024):
                stream.write(chunk); stream.flush(); os.fsync(stream.fileno())
                count+=len(chunk)
                if count//(1024**3)>reported:
                    reported=count//(1024**3)
                    append_jsonl(events,{"at":now(),"event":"progress_flushed","bytes":count})
                    print(f"{destination.name}: {count/1024**3:.1f} GiB",flush=True)
    if partial.stat().st_size != expected_size:
        append_jsonl(events,{"at":now(),"event":"incomplete_transfer","bytes":partial.stat().st_size,"expected_bytes":expected_size})
        raise ValueError("Transfer ended before expected size; resumable partial retained")
    observed=sha(partial)
    append_jsonl(events,{"at":now(),"event":"hash_checked","sha256":observed,"expected_sha256":expected_sha,"valid":observed==expected_sha})
    if observed != expected_sha:
        raise ValueError(f"SHA-256 errato per {destination.name}: {observed}")
    partial.replace(destination)

def acquire(name, quant, repair_tail=False):
    base, repo, filename=MODELS[name]
    if quant=="Q8_0":
        filename=filename.replace("BF16",quant)
    directory=OUTPUT/"models"/name
    directory.mkdir(parents=True,exist_ok=True)
    manifest_path=directory/(quant+"_manifest.json")
    if manifest_path.exists():
        info=read_json(manifest_path)
    else:
        metadata=json.loads(fetch("https://huggingface.co/api/models/"+repo+"?blobs=true"))
        base_metadata=json.loads(fetch("https://huggingface.co/api/models/"+base+"?blobs=true"))
        item=next(r for r in metadata["siblings"] if r["rfilename"]==filename)
        info={"model_key":name,"base_repository":base,"base_revision_observed":base_metadata["sha"],
              "gguf_repository":repo,"gguf_revision":metadata["sha"],"filename":filename,
              "gguf_sha256":item["lfs"]["sha256"],"size_bytes":item["size"],"weight_precision":quant,
              "downloaded_at":now(),"base_revision_of_conversion":"not independently established",
              "url":f"https://huggingface.co/{repo}/resolve/{metadata['sha']}/{filename}",
              "local_path":str(directory/(quant+".gguf"))}
        write_json(manifest_path,info)
        for source_id,revision,label in ((base,base_metadata["sha"],"official"),(repo,metadata["sha"],"gguf")):
            for file in (["README.md","tokenizer.json","tokenizer_config.json","config.json"] if label=="official" else ["README.md"]):
                destination=directory/(label+"_"+file)
                if not destination.exists():
                    destination.write_bytes(fetch(f"https://huggingface.co/{source_id}/resolve/{revision}/{file}"))
    download(info["url"],Path(info["local_path"]),info["gguf_sha256"],info["size_bytes"],repair_tail)
    write_json(directory/(quant+"_verified.json"),{"verified_at":now(),"sha256":info["gguf_sha256"],"size_bytes":Path(info["local_path"]).stat().st_size})
    print(f"VERIFIED {name} {quant} {info['gguf_sha256']}",flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("models",nargs="+",choices=MODELS)
    parser.add_argument("--quant",default="BF16",choices=("BF16","Q8_0"))
    parser.add_argument("--repair-tail",action="store_true")
    args=parser.parse_args()
    for name in args.models: acquire(name,args.quant,args.repair_tail)
