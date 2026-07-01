import json
import os
import shutil
from pathlib import Path


def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def is_regular_file(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink()
    except Exception:
        return False


def scan_links(root: Path):
    symlinks = []
    broken = []
    for p in root.rglob("*"):
        try:
            if p.is_symlink():
                target = None
                try:
                    target = os.readlink(p)
                except Exception:
                    target = None
                item = {
                    "path": str(p.relative_to(root)),
                    "target": target,
                    "type": "dir" if p.exists() and p.resolve().is_dir() else "file",
                }
                symlinks.append(item)
                if not p.exists():
                    broken.append(item)
        except Exception:
            continue
    return symlinks, broken


def prune_symlinks(root: Path):
    removed = []
    for p in sorted(root.rglob("*"), reverse=True):
        try:
            if p.is_symlink():
                removed.append(str(p.relative_to(root)))
                p.unlink()
        except Exception:
            pass
    return removed


def collect_stats(root: Path):
    file_count = 0
    total_bytes = 0
    for p in root.rglob("*"):
        try:
            if is_regular_file(p):
                file_count += 1
                total_bytes += p.stat().st_size
        except Exception:
            continue
    return file_count, total_bytes


def main():
    root = Path("public")
    api_dir = root / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    pre_symlinks, pre_broken = scan_links(root)
    removed = prune_symlinks(root)
    post_symlinks, post_broken = scan_links(root)

    file_count, total_bytes = collect_stats(root)

    report = {
        "file_count": file_count,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / 1024 / 1024, 2),
        "symlink_count_before": len(pre_symlinks),
        "symlink_count_after": len(post_symlinks),
        "broken_symlink_count_before": len(pre_broken),
        "removed_symlinks": removed,
        "sample_symlinks_before": pre_symlinks[:50],
        "sample_broken_symlinks_before": pre_broken[:50],
    }

    write_json(api_dir / "site_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
