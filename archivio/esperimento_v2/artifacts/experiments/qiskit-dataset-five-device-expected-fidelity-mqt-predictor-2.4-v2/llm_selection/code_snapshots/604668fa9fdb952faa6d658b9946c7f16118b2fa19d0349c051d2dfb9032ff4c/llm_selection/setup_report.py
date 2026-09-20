"""Installazione esplicita del solo compilatore LaTeX e del lettore PDF isolato."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from .acquire import fetch, download
from .common import OUTPUT, read_json, write_json, now

RELEASE="https://api.github.com/repos/tectonic-typesetting/tectonic/releases/tags/tectonic%400.17.0"
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--inspect",action="store_true",help="Read metadata only; do not download or install.")
    args=parser.parse_args()
    root=OUTPUT/"runtime/tectonic"
    manifest_path=root/"manifest.json"
    if manifest_path.exists(): info=read_json(manifest_path)
    else:
        release=json.loads(fetch(RELEASE))
        assets=[a for a in release["assets"] if a["name"].endswith("x86_64-unknown-linux-musl.tar.gz")]
        if len(assets)!=1: raise ValueError("Expected one official Linux x86_64 musl asset")
        asset=assets[0]
        digest=asset.get("digest","")
        if not digest.startswith("sha256:"): raise ValueError("Official release asset SHA-256 is missing; inspect release before installing")
        renderer=json.loads(fetch("https://pypi.org/pypi/PyMuPDF/json"))["info"]["version"]
        plotting=json.loads(fetch("https://pypi.org/pypi/matplotlib/json"))["info"]["version"]
        info={"release":release["tag_name"],"release_url":release["html_url"],"asset_url":asset["browser_download_url"],
              "asset_name":asset["name"],"asset_sha256":digest.split(":",1)[1],"asset_bytes":asset["size"],
              "renderer_requirement":"PyMuPDF=="+renderer,"plotting_requirement":"matplotlib=="+plotting,"recorded_at":now()}
    if args.inspect:
        print(json.dumps(info,indent=2));return
    root.mkdir(parents=True,exist_ok=True)
    if not manifest_path.exists(): write_json(manifest_path,info)
    archive=root/info["asset_name"]
    download(info["asset_url"],archive,info["asset_sha256"],info["asset_bytes"])
    executable=root/"tectonic"
    with tarfile.open(archive) as bundle:
        members=[member for member in bundle.getmembers() if member.isfile() and Path(member.name).name=="tectonic"]
        if len(members)!=1: raise ValueError("Unexpected compiler archive layout")
        binary=bundle.extractfile(members[0]).read()
    if executable.exists() and executable.read_bytes()!=binary: raise ValueError("Compiler binary changed")
    if not executable.exists(): executable.write_bytes(binary)
    executable.chmod(0o755)
    python=OUTPUT/"runtime/python/bin/python"
    if not python.exists(): raise ValueError("Separate runtime missing; see llm_selection/README.md")
    subprocess.run(["uv","pip","install","--python",str(python),info["renderer_requirement"],info["plotting_requirement"]],check=True)
    version=subprocess.check_output([str(executable),"--version"],text=True).strip()
    frozen=subprocess.check_output(["uv","pip","freeze","--python",str(python)],text=True)
    write_json(root/"installed.json",{"at":now(),"tectonic_version":version,"binary_sha256":hashlib.sha256(binary).hexdigest(),
                                     "renderer_requirement":info["renderer_requirement"],"plotting_requirement":info["plotting_requirement"],"isolated_environment":frozen})
    print("Compilatore e lettore PDF pronti. L'ambiente MQT non è stato modificato.")
if __name__=="__main__": main()
