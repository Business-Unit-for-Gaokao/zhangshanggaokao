import json
import re
import sys
from pathlib import Path


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


def rel_path(path: Path, root: Path) -> str:
    return "./" + path.relative_to(root).as_posix()


def normalize_school_payload(payload):
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"], payload
    if isinstance(payload, dict):
        return payload, payload
    return {}, {}


def extract_year(payload, rel_parts):
    candidates = []

    if isinstance(payload, dict):
        if payload.get("year") is not None:
            candidates.append(str(payload.get("year")).strip())

        summary = payload.get("summary")
        if isinstance(summary, dict) and summary.get("year") is not None:
            candidates.append(str(summary.get("year")).strip())

    if rel_parts:
        first = rel_parts[0]
        first_stem = Path(first).stem
        candidates.extend([first, first_stem])

    for part in rel_parts:
        text = str(part)
        for match in re.findall(r"(20\d{2})", text):
            candidates.append(match)

    for value in candidates:
        if value and str(value).isdigit() and len(str(value)) == 4:
            return str(value)

    return ""


def should_include_dataset_payload(payload):
    if not isinstance(payload, dict):
        return False

    if isinstance(payload.get("data"), list):
        return False

    if payload.get("school_id") is not None:
        return True

    if payload.get("province_id") is not None:
        return True

    if payload.get("year") is not None:
        return True

    if isinstance(payload.get("records"), list):
        return True

    if payload.get("record_count") is not None:
        return True

    return False


def build_schools_manifest(root: Path):
    data_dir = root / "data"
    schools_dir = data_dir / "schools"
    schools_json = data_dir / "schools.json"

    manifest = []

    if schools_dir.exists():
        for path in sorted(schools_dir.rglob("*.json")):
            payload = load_json(path, {})
            school, raw = normalize_school_payload(payload)

            school_id = school.get("school_id") or raw.get("school_id")
            school_name = school.get("name") or raw.get("name") or path.stem

            manifest.append({
                "school_id": str(school_id) if school_id is not None else "",
                "school_name": school_name,
                "province": school.get("province"),
                "city": school.get("city"),
                "county": school.get("county"),
                "type": school.get("type"),
                "level": school.get("level"),
                "nature": school.get("nature"),
                "labels": school.get("label_list") or [],
                "file": rel_path(path, root),
            })

        return manifest

    if schools_json.exists():
        payload = load_json(schools_json, {})
        rows = []

        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            if isinstance(payload.get("data"), list):
                rows = payload["data"]
            else:
                rows = [payload]

        for idx, school in enumerate(rows, 1):
            if not isinstance(school, dict):
                continue
            school_id = school.get("school_id")
            school_name = school.get("name") or f"学校{idx}"
            manifest.append({
                "school_id": str(school_id) if school_id is not None else "",
                "school_name": school_name,
                "province": school.get("province"),
                "city": school.get("city"),
                "county": school.get("county"),
                "type": school.get("type"),
                "level": school.get("level"),
                "nature": school.get("nature"),
                "labels": school.get("label_list") or [],
                "file": rel_path(schools_json, root),
            })

    return manifest


def build_majors_manifest(root: Path):
    majors_file = root / "data" / "majors.json"
    if not majors_file.exists():
        return []

    payload = load_json(majors_file, {})
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("data", "items", "list"):
            if isinstance(payload.get(key), list):
                return payload.get(key)

    return []


def build_dataset_manifest(root: Path, dataset_name: str):
    dataset_dir = root / "data" / dataset_name
    manifest = []
    years = set()

    if not dataset_dir.exists():
        return manifest, []

    for path in sorted(dataset_dir.rglob("*.json")):
        payload = load_json(path, None)
        if not should_include_dataset_payload(payload):
            continue

        rel_parts = path.relative_to(dataset_dir).parts
        year = extract_year(payload, rel_parts)

        province = payload.get("province")
        province_id = str(payload.get("province_id") or "")
        school_id = str(payload.get("school_id") or "")
        school_name = payload.get("school_name") or path.stem
        record_count = payload.get("record_count")
        update_time = payload.get("update_time")

        if not province and len(rel_parts) >= 2:
            province = rel_parts[1] if rel_parts[0] != rel_parts[-1] else ""

        if record_count is None and isinstance(payload.get("records"), list):
            record_count = len(payload.get("records"))

        if not update_time and isinstance(payload.get("summary"), dict):
            update_time = payload["summary"].get("fetched_at")

        manifest.append({
            "dataset": dataset_name,
            "year": year,
            "province": province,
            "province_id": province_id,
            "school_id": school_id,
            "school_name": school_name,
            "record_count": int(record_count or 0),
            "update_time": update_time,
            "file": rel_path(path, root),
        })

        if year:
            years.add(year)

    sorted_years = sorted(
        years,
        key=lambda x: int(x) if str(x).isdigit() else -1,
        reverse=True,
    )

    return manifest, sorted_years


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("public")
    api_dir = root / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    schools_manifest = build_schools_manifest(root)
    majors_manifest = build_majors_manifest(root)

    plans_manifest, plans_years = build_dataset_manifest(root, "plans")
    scores_manifest, scores_years = build_dataset_manifest(root, "scores")
    school_scores_manifest, school_scores_years = build_dataset_manifest(root, "school_scores")

    write_json(api_dir / "schools_manifest.json", schools_manifest)
    write_json(api_dir / "majors_manifest.json", majors_manifest)
    write_json(api_dir / "plans_manifest.json", plans_manifest)
    write_json(api_dir / "scores_manifest.json", scores_manifest)
    write_json(api_dir / "school_scores_manifest.json", school_scores_manifest)

    summary = {
        "counts": {
            "schools": len(schools_manifest),
            "majors": len(majors_manifest),
            "plans_files": len(plans_manifest),
            "scores_files": len(scores_manifest),
            "school_scores_files": len(school_scores_manifest),
        },
        "years": {
            "plans": plans_years,
            "scores": scores_years,
            "school_scores": school_scores_years,
        },
    }
    write_json(api_dir / "summary.json", summary)

    print("✅ Pages manifest 生成完成")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
