#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_schools(payload):
    if isinstance(payload, dict):
        return payload.get("data", [])
    if isinstance(payload, list):
        return payload
    return []


def build_target_school_ids(schools_payload, sample_schools: int):
    schools = extract_schools(schools_payload)
    return [
        str(item.get("school_id"))
        for item in schools[:sample_schools]
        if isinstance(item, dict) and item.get("school_id")
    ]


def is_year_complete(year: str, schools_file: Path, plans_file: Path, sample_schools: int) -> bool:
    if not schools_file.exists() or not plans_file.exists():
        return False

    schools_payload = load_json(schools_file)
    target_school_ids = build_target_school_ids(schools_payload, sample_schools)
    if not target_school_ids:
        return False

    payload = load_json(plans_file)

    complete = payload.get("complete") is True
    saved_year = str(payload.get("year", ""))
    target_saved = [str(x) for x in payload.get("target_school_ids", [])]
    completed_saved = set(str(x) for x in payload.get("completed_school_ids", []))

    try:
        school_done = int(payload.get("school_done", -1))
        school_total = int(payload.get("school_total", -1))
    except Exception:
        return False

    return (
        complete
        and saved_year == str(year)
        and target_saved == target_school_ids
        and completed_saved.issuperset(target_school_ids)
        and school_done == len(target_school_ids)
        and school_total == len(target_school_ids)
    )


def main():
    parser = argparse.ArgumentParser(description="检查某个 plans 年份是否已完整覆盖当前目标学校")
    parser.add_argument("--year", required=True, help="年份，例如 2025")
    parser.add_argument("--schools-file", required=True, help="schools.json 路径")
    parser.add_argument("--plans-file", required=True, help="plans 年度文件路径")
    parser.add_argument("--sample-schools", required=True, type=int, help="本次目标学校数量")
    args = parser.parse_args()

    try:
        ok = is_year_complete(
            year=str(args.year),
            schools_file=Path(args.schools_file),
            plans_file=Path(args.plans_file),
            sample_schools=args.sample_schools,
        )
        print("complete" if ok else "incomplete")
    except Exception:
        print("incomplete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
