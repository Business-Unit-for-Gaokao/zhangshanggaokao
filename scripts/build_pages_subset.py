import json
import shutil
import sys
from pathlib import Path


DATASETS = ["plans", "scores", "school_scores"]


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def normalize_school_payload(payload):
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"], payload
    if isinstance(payload, dict):
        return payload, payload
    return {}, {}


def normalize_label_text(text):
    return str(text or "").strip().replace(" ", "")


def has_any_label(labels, keywords):
    normalized = [normalize_label_text(x) for x in (labels or [])]
    for label in normalized:
        for kw in keywords:
            if kw in label:
                return True
    return False


def match_school(labels, mode):
    if mode == "985_only":
        return has_any_label(labels, ["985", "985工程"])
    if mode == "211_union":
        return has_any_label(labels, ["985", "985工程", "211", "211工程"])
    if mode == "double_first_class_union":
        return has_any_label(
            labels,
            ["985", "985工程", "211", "211工程", "双一流", "一流大学", "一流学科"],
        )
    raise ValueError(f"未知模式: {mode}")


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def collect_regular_file_stats(root: Path):
    file_count = 0
    total_bytes = 0
    for p in root.rglob("*"):
        try:
            if p.is_file() and not p.is_symlink():
                file_count += 1
                total_bytes += p.stat().st_size
        except Exception:
            continue
    return file_count, total_bytes


def load_school_index(repo_data: Path):
    schools = []

    schools_dir = repo_data / "schools"
    if schools_dir.exists():
        for path in sorted(schools_dir.rglob("*.json")):
            payload = load_json(path, {})
            school, raw = normalize_school_payload(payload)

            school_id = school.get("school_id") or raw.get("school_id")
            school_name = school.get("name") or raw.get("name") or path.stem
            labels = school.get("label_list") or raw.get("label_list") or []

            if school_id is None:
                continue

            schools.append({
                "school_id": str(school_id),
                "school_name": school_name,
                "labels": labels,
                "school": school,
                "raw": raw,
                "source_file": path,
            })
        return schools

    schools_json = repo_data / "schools.json"
    if schools_json.exists():
        payload = load_json(schools_json, {})
        rows = []
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
            rows = payload["data"]

        for idx, school in enumerate(rows, 1):
            if not isinstance(school, dict):
                continue
            school_id = school.get("school_id")
            if school_id is None:
                continue
            schools.append({
                "school_id": str(school_id),
                "school_name": school.get("name") or f"学校{idx}",
                "labels": school.get("label_list") or [],
                "school": school,
                "raw": school,
                "source_file": schools_json,
            })

    return schools


def build_school_subset(repo_data: Path, public_data: Path, mode: str):
    schools = load_school_index(repo_data)
    selected = [s for s in schools if match_school(s["labels"], mode)]
    selected_ids = {s["school_id"] for s in selected}

    dst_schools_dir = public_data / "schools"
    dst_schools_dir.mkdir(parents=True, exist_ok=True)

    copied_school_files = 0
    for item in selected:
        src = item["source_file"]
        schools_dir = repo_data / "schools"

        if schools_dir.exists() and src.exists() and src.is_file() and schools_dir in src.parents:
            rel = src.relative_to(schools_dir)
            dst = dst_schools_dir / rel
            copy_file(src, dst)
            copied_school_files += 1

    schools_json_rows = [item["school"] for item in selected]
    write_json(public_data / "schools.json", schools_json_rows)

    majors_src = repo_data / "majors.json"
    if majors_src.exists() and majors_src.is_file():
        copy_file(majors_src, public_data / "majors.json")

    summary_rows = []
    for item in selected:
        school = item["school"]
        summary_rows.append({
            "school_id": item["school_id"],
            "name": item["school_name"],
            "province": school.get("province"),
            "city": school.get("city"),
            "type": school.get("type"),
            "level": school.get("level"),
            "labels": item["labels"],
        })

    write_json(public_data / "subset_schools.json", summary_rows)

    return {
        "selected_school_ids": selected_ids,
        "selected_school_count": len(selected_ids),
        "copied_school_files": copied_school_files,
    }


def copy_dataset_subset(repo_data: Path, public_data: Path, dataset: str, selected_ids: set):
    src_dir = repo_data / dataset
    dst_dir = public_data / dataset
    dst_dir.mkdir(parents=True, exist_ok=True)

    copied_files = 0
    skipped_files = 0
    total_records = 0
    years = set()

    if not src_dir.exists():
        return {
            "dataset": dataset,
            "copied_files": 0,
            "skipped_files": 0,
            "record_count": 0,
            "years": [],
        }

    for path in sorted(src_dir.rglob("*.json")):
        payload = load_json(path, None)
        if not isinstance(payload, dict):
            skipped_files += 1
            continue

        school_id = payload.get("school_id")
        if school_id is None:
            skipped_files += 1
            continue

        school_id = str(school_id)
        if school_id not in selected_ids:
            skipped_files += 1
            continue

        rel = path.relative_to(src_dir)
        dst = dst_dir / rel
        copy_file(path, dst)
        copied_files += 1

        if isinstance(payload.get("records"), list):
            total_records += len(payload["records"])
        elif payload.get("record_count") is not None:
            try:
                total_records += int(payload["record_count"])
            except Exception:
                pass

        year = payload.get("year")
        if year is not None:
            years.add(str(year))
        elif len(rel.parts) >= 1:
            maybe_year = rel.parts[0]
            if str(maybe_year).isdigit():
                years.add(str(maybe_year))

    return {
        "dataset": dataset,
        "copied_files": copied_files,
        "skipped_files": skipped_files,
        "record_count": total_records,
        "years": sorted(years, key=lambda x: int(x), reverse=True),
    }


def main():
    output_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("public")
    mode = sys.argv[2] if len(sys.argv) > 2 else "985_only"

    repo_data = Path("data")
    public_data = output_root / "data"
    api_dir = output_root / "api"

    if public_data.exists():
        shutil.rmtree(public_data)
    public_data.mkdir(parents=True, exist_ok=True)
    api_dir.mkdir(parents=True, exist_ok=True)

    school_result = build_school_subset(repo_data, public_data, mode)
    selected_ids = school_result["selected_school_ids"]

    dataset_results = []
    for dataset in DATASETS:
        dataset_results.append(copy_dataset_subset(repo_data, public_data, dataset, selected_ids))

    file_count, total_bytes = collect_regular_file_stats(output_root)

    report = {
        "mode": mode,
        "selected_school_count": school_result["selected_school_count"],
        "copied_school_files": school_result["copied_school_files"],
        "datasets": dataset_results,
        "public_file_count": file_count,
        "public_total_bytes": total_bytes,
        "public_total_mb": round(total_bytes / 1024 / 1024, 2),
    }

    write_json(api_dir / "pages_subset_report.json", report)
    print("✅ Pages subset 构建完成")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
