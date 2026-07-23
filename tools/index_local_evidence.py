#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a mode-aware index for ignored local evaluation evidence"
    )
    parser.add_argument(
        "--root",
        action="append",
        required=True,
        metavar="NAME=PATH",
        help="Evidence root to index; may be repeated",
    )
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def parse_root(value: str) -> tuple[str, Path]:
    name, separator, path = value.partition("=")
    if not separator or not name or not path:
        raise ValueError(f"invalid --root value: {value!r}")
    return name, Path(path).expanduser().resolve()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def entry_record(root: Path, path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    relative = "." if path == root else path.relative_to(root).as_posix()
    mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
    if stat.S_ISLNK(metadata.st_mode):
        return {
            "path": relative,
            "type": "symlink",
            "mode": mode,
            "target": os.readlink(path),
        }
    if stat.S_ISDIR(metadata.st_mode):
        return {"path": relative, "type": "directory", "mode": mode}
    if stat.S_ISREG(metadata.st_mode):
        return {
            "path": relative,
            "type": "file",
            "mode": mode,
            "size": metadata.st_size,
            "sha256": file_digest(path),
        }
    raise ValueError(f"unsupported evidence entry type: {path}")


def index_root(name: str, root: Path) -> dict[str, Any]:
    if not root.exists():
        raise FileNotFoundError(root)
    paths = [root, *sorted(root.rglob("*"), key=lambda item: item.as_posix())]
    records = [entry_record(root, path) for path in paths]
    encoded = b"".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        for record in records
    )
    counts = {
        kind: sum(record["type"] == kind for record in records)
        for kind in ("file", "directory", "symlink")
    }
    return {
        "name": name,
        "source_path": str(root),
        "tree_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        "entry_count": len(records),
        "file_count": counts["file"],
        "directory_count": counts["directory"],
        "symlink_count": counts["symlink"],
        "file_bytes": sum(
            record.get("size", 0) for record in records if record["type"] == "file"
        ),
        "entries": records,
    }


def write_private_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as output:
            json.dump(value, output, indent=2, sort_keys=True)
            output.write("\n")
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    args = parse_args()
    roots = [parse_root(value) for value in args.root]
    names = [name for name, _ in roots]
    if len(set(names)) != len(names):
        raise ValueError("evidence root names must be unique")
    index = {
        "schema_version": "1.0",
        "label": args.label,
        "roots": [index_root(name, path) for name, path in roots],
    }
    write_private_json(args.output.resolve(), index)
    for root in index["roots"]:
        print(
            f"{root['name']}: {root['tree_sha256']} "
            f"({root['file_count']} files, {root['file_bytes']} bytes)"
        )
    print(f"Wrote private evidence index to {args.output.resolve()}")


if __name__ == "__main__":
    main()
