from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path
from typing import Iterator


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def iter_bz2_members(archive_path: str | Path) -> Iterator[tarfile.TarInfo]:
    with tarfile.open(Path(archive_path), "r:*") as archive:
        for member in archive:
            if member.isfile() and member.name.lower().endswith(".bz2"):
                yield member


def scan_archive(archive_path: str | Path) -> dict:
    path = Path(archive_path)
    members = files = bz2_files = member_bytes = 0

    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            members += 1
            if member.isfile():
                files += 1
                member_bytes += max(member.size, 0)
                if member.name.lower().endswith(".bz2"):
                    bz2_files += 1

    return {
        "archive": path.name,
        "archive_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "members": members,
        "files": files,
        "bz2_files": bz2_files,
        "member_bytes": member_bytes,
    }
