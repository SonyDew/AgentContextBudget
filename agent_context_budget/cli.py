"""Read-only instruction-file size and duplicate report."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "copilot-instructions.md"}
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__"}
MAX_BYTES = 2 * 1024 * 1024


def discover(root):
    if root.is_symlink():
        raise ValueError("Symbolic link input is not supported")
    if root.is_file():
        if root.name not in NAMES:
            raise ValueError("Unsupported instruction filename")
        return [root]
    if not root.is_dir():
        raise ValueError("Input path is not a readable file or directory")
    found = []
    def onerror(error):
        raise ValueError("Cannot traverse input directory") from error
    for base, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            if name in NAMES and not path.is_symlink():
                found.append(path)
    return sorted(found)


def paragraphs(content):
    for part in re.split(r"\n\s*\n", content.replace("\r\n", "\n")):
        normalized = " ".join(part.split()).casefold()
        if len(normalized) >= 40:
            yield normalized


def analyze(root):
    entries = []
    repeated = {}
    for path in discover(root):
        try:
            if path.is_symlink():
                raise ValueError("Symbolic link input is not supported")
            if path.stat().st_size > MAX_BYTES:
                raise ValueError("Instruction file exceeds 2 MiB limit")
            with path.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("Instruction file exceeds 2 MiB limit")
            content = raw.decode("utf-8-sig")
        except (OSError, UnicodeError) as exc:
            raise ValueError("Cannot read instruction file as UTF-8") from exc
        rel = str(path.relative_to(root)) if root.is_dir() else path.name
        entries.append({"path": rel, "bytes": len(raw), "lines": len(content.splitlines()),
                        "estimated_tokens": (len(content) + 3) // 4})
        for part in set(paragraphs(content)):
            key = hashlib.sha256(part.encode()).hexdigest()[:16]
            repeated.setdefault(key, []).append(rel)
    duplicates = [{"fingerprint": key, "files": sorted(paths)}
                  for key, paths in sorted(repeated.items()) if len(paths) > 1]
    return {"files": entries, "totals": {
        "files": len(entries), "bytes": sum(e["bytes"] for e in entries),
        "estimated_tokens": sum(e["estimated_tokens"] for e in entries)},
        "duplicate_paragraphs": duplicates}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure local agent instruction files and repeated paragraphs.")
    parser.add_argument("path", nargs="?", default=".", help="Directory or supported instruction file")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args(argv)
    try:
        report = analyze(Path(args.path))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for entry in report["files"]:
            print(f'{entry["path"]}: {entry["bytes"]} bytes, ~{entry["estimated_tokens"]} tokens')
        totals = report["totals"]
        print(f'Total: {totals["files"]} files, {totals["bytes"]} bytes, ~{totals["estimated_tokens"]} tokens')
        print(f'Repeated paragraphs across files: {len(report["duplicate_paragraphs"])}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
