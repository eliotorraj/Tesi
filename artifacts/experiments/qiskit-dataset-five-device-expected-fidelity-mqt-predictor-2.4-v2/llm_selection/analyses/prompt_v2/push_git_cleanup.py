"""Pubblica soltanto le due rimozioni RL già controllate; nessun force push."""
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path("/home/elio/Tesi-mqt-2.4-v2")
HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE/"git_cleanup_prepared.json").read_text())
def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout
refs = [row["ref"] for row in manifest["prepared"]]
remote = dict(line.split()[::-1] for line in git("ls-remote", "--heads", "origin", *refs).splitlines())
for row in manifest["prepared"]:
    if remote.get(row["ref"]) != row["before"]:
        raise ValueError("Remote changed; review again: "+row["ref"])
    if git("rev-parse", row["after"]+"^").strip() != row["before"]:
        raise ValueError("Cleanup must be a normal direct child")
status_before = git("status", "--porcelain")
command = ["git", "push", "--atomic", "origin", *[row["after"]+":"+row["ref"] for row in manifest["prepared"]]]
result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
record = {"at": datetime.now(timezone.utc).isoformat(), "command": command, "returncode": result.returncode,
          "stdout": result.stdout, "stderr": result.stderr}
(HERE/"git_cleanup_push.json").write_text(json.dumps(record, indent=2)+"\n")
print(json.dumps(record, indent=2), flush=True)
result.check_returncode()
remote_after = dict(line.split()[::-1] for line in git("ls-remote", "--heads", "origin", *refs).splitlines())
assert all(remote_after[row["ref"]] == row["after"] for row in manifest["prepared"])
assert status_before == git("status", "--porcelain")
record["verified_remote_heads"] = remote_after
record["working_tree_and_index_unchanged"] = True
record["lfs_storage_reclaimed"] = False
(HERE/"git_cleanup_push.json").write_text(json.dumps(record, indent=2)+"\n")
