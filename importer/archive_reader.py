from __future__ import annotations

import tarfile
from pathlib import Path
from typing import Iterator


def iter_bz2_members(archive_path: str | Path) -> Iterator[tarfile.TarInfo]:
    path = Path(archive_path)
    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            if member.isfile() and member.name.lower().endswith(".bz2"):
                yield member


def scan_archive(archive_path: str | Path) -> dict:
    path = Path(archive_path)
    members = 0
    files = 0
    bz2_files = 0
    compressed_member_bytes = 0

    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            members += 1
            if member.isfile():
                files += 1
                compressed_member_bytes += max(member.size, 0)
                if member.name.lower().endswith(".bz2"):
                    bz2_files += 1

    return {
        "archive": path.name,
        "archive_size_bytes": path.stat().st_size,
        "members": members,
        "files": files,
        "bz2_files": bz2_files,
        "member_bytes": compressed_member_bytes,
    }
