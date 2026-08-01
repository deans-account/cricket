import tarfile
from pathlib import Path

def scan_archive(path):
    p=Path(path)
    bz2=0
    members=0
    with tarfile.open(p,"r:*") as t:
        for m in t.getmembers():
            members+=1
            if m.name.endswith(".bz2"):
                bz2+=1
    return {
        "archive":p.name,
        "members":members,
        "bz2_files":bz2,
        "size_bytes":p.stat().st_size
    }
