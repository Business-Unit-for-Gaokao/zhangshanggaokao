import os
import json
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
FINAL_DATA_DIR = DOCS_DIR / "data"
TMP_DATA_DIR = ROOT / "build" / "pages_data_tmp"

DB_SCHEMA = "crawler"
BUCKET_COUNT = 100
INDEX_PAGE_SIZE = 1000
PAGES_DATA_VERSION = "v0.2.0"
PAGES_BASE_PATH = ""


PROVINCE_DICT = {
    "11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古",
    "21": "辽宁", "22": "吉林", "23": "黑龙江",
    "31": "上海", "32": "江苏", "33": "浙江", "34": "安徽", "35": "福建", "36": "江西", "37": "山东",
    "41": "河南", "42": "湖北", "43": "湖南",
    "44": "广东", "45": "广西", "46": "海南",
    "50": "重庆", "51": "四川", "52": "贵州", "53": "云南", "54": "西藏",
    "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏", "65": "新疆",
    "71": "台湾", "81": "香港", "82": "澳门",
}


def load_env():
    load_dotenv(dotenv_path=ROOT / ".env")


def normalize_base_path(value):
    value = (value or "").strip()
    if not value or value == "/":
        return ""
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/")


def public_url(*parts):
    cleaned = [str(p).strip("/") for p in parts if str(p).strip("/")]
    suffix = "/".join(cleaned)
    if PAGES_BASE_PATH:
        return f"{PAGES_BASE_PATH}/{suffix}" if suffix else PAGES_BASE_PATH
    return f"/{suffix}" if suffix else "/"


def get_conn():
    return psycopg.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


def ensure_clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def ensure_docs_root():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    nojekyll = DOCS_DIR / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.write_text("", encoding="utf-8")


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def bucket_of(value) -> str:
    try:
        return f"{int(str(value)) % BUCKET_COUNT:02d}"
    except Exception:
        s = str(value)
        return f"{sum(ord(c) for c in s) % BUCKET_COUNT:02d}"


def paginate(items, page_size=INDEX_PAGE_SIZE):
    total = len(items)
    if total == 0:
        return
    for i in range(0, total, page_size):
        yield items[i:i + page_size], (i // page_size) + 1, total


def fetch_raw_documents(conn, crawler_name, entity_type, year=None):
    sql = f"""
        SELECT entity_key, year, payload
        FROM {DB_SCHEMA}.raw_documents
        WHERE crawler_name = %s
          AND entity_type = %s
    """
    params = [crawler_name, entity_type]

    if year is not None:
        sql += " AND year = %s"
        params.append(str(year))

    sql += " ORDER BY entity_key ASC"

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        {
            "entity_key": str(entity_key) if entity_key is not None else None,
            "year": str(row_year) if row_year is not None else None,
            "payload": payload or {},
        }
        for entity_key, row_year, payload in rows
    ]


def fetch_distinct_years(conn, crawler_name, entity_type):
    sql = f"""
        SELECT DISTINCT year
        FROM {DB_SCHEMA}.raw_documents
        WHERE crawler_name = %s
          AND entity_type = %s
          AND year IS NOT NULL
        ORDER BY year DESC
    """
    with conn.cursor() as cur:
        cur.execute(sql, (crawler_name, entity_type))
        rows = cur.fetchall()
    return [str(x[0]) for x in rows if x and x[0] is not None]


def pick_first(payload, keys, default=None):
    for key in keys:
        value = payload.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def normalize_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_school_payload(entity_key, payload):
    school_id = str(pick_first(payload, ["school_id", "id"], entity_key))
    province_id_raw = pick_first(payload, ["province_id", "province_code"], "")
    province_id = str(province_id_raw) if province_id_raw is not None else ""

    province_name = pick_first(payload, ["province_name", "province"], "")
    if not province_name and province_id in PROVINCE_DICT:
        province_name = PROVINCE_DICT[province_id]

    city_name = pick_first(payload, ["city_name", "city"], "")
    name = pick_first(payload, ["name", "school_name"], "")

    is_985 = normalize_bool(payload.get("f985"))
    is_211 = normalize_bool(payload.get("f211"))
    dual_class_name = pick_first(payload, ["dual_class_name"], "")

    tags = []
    if is_985:
        tags.append("985")
    if is_211:
        tags.append("211")
    if dual_class_name:
        tags.append(str(dual_class_name))

    return {
        "school_id": school_id,
        "name": name,
        "province_id": province_id,
        "province": province_name,
        "city": city_name,
        "type": pick_first(payload, ["type_name", "type"], ""),
        "nature": pick_first(payload, ["school_nature_name", "nature_name"], ""),
        "belong": pick_first(payload, ["belong", "belong_name"], ""),
        "site": pick_first(payload, ["site", "school_site"], ""),
        "phone": pick_first(payload, ["phone"], ""),
        "email": pick_first(payload, ["email"], ""),
        "address": pick_first(payload, ["address"], ""),
        "intro": pick_first(payload, ["content", "introduce", "school_intro"], ""),
        "is_985": is_985,
        "is_211": is_211,
        "is_dual_first_class": bool(dual_class_name),
        "dual_class_name": dual_class_name or "",
        "tags": tags,
    }


def build_school_detail(school):
    school_id = school["school_id"]
    bucket = bucket_of(school_id)
    return {
        "school_id": school_id,
        "name": school["name"],
        "province_id": school["province_id"],
        "province": school["province"],
        "city": school["city"],
        "type": school["type"],
        "nature": school["nature"],
        "belong": school["belong"],
        "site": school["site"],
        "phone": school["phone"],
        "email": school["email"],
        "address": school["address"],
        "intro": school["intro"],
        "is_985": school["is_985"],
        "is_211": school["is_211"],
        "is_dual_first_class": school["is_dual_first_class"],
        "dual_class_name": school["dual_class_name"],
        "tags": school["tags"],
        "links": {
            "school_scores": public_url("data", "school-scores", "bucket", bucket, f"{school_id}.json"),
            "scores_root": public_url("data", "scores"),
            "plans_root": public_url("data", "plans"),
        },
    }


def build_school_index_item(school):
    school_id = school["school_id"]
    bucket = bucket_of(school_id)
    return {
        "school_id": school_id,
        "name": school["name"],
        "province_id": school["province_id"],
        "province": school["province"],
        "city": school["city"],
        "type": school["type"],
        "nature": school["nature"],
        "tags": school["tags"],
        "detail_url": public_url("data", "schools", "bucket", bucket, f"{school_id}.json"),
    }


def export_meta(conn, out_dir, stats):
    score_years = fetch_distinct_years(conn, "scores", "school_year_score")
    plan_years = fetch_distinct_years(conn, "plans", "school_year_plan")
    provinces = [{"id": k, "name": v} for k, v in PROVINCE_DICT.items()]

    write_json(out_dir / "meta" / "build.json", {
        "version": PAGES_DATA_VERSION,
        "built_at": now_iso(),
        "base_path": PAGES_BASE_PATH,
        "score_years": score_years,
        "plan_years": plan_years,
        "stats": stats,
    })
    write_json(out_dir / "meta" / "years.json", {
        "scores": score_years,
        "plans": plan_years,
    })
    write_json(out_dir / "meta" / "provinces.json", provinces)
    write_json(out_dir / "meta" / "stats.json", stats)


def export_schools(conn, out_dir):
    rows = fetch_raw_documents(conn, "schools", "school")
    province_groups = defaultdict(list)
    search_items = []
    count = 0

    for row in rows:
        school = normalize_school_payload(row["entity_key"], row["payload"])
        school_id = school["school_id"]
        bucket = bucket_of(school_id)

        write_json(
            out_dir / "schools" / "bucket" / bucket / f"{school_id}.json",
            build_school_detail(school),
        )

        idx = build_school_index_item(school)
        province_groups[school["province_id"] or "unknown"].append(idx)
        search_items.append(idx)
        count += 1

    for province_id, items in province_groups.items():
        items.sort(key=lambda x: ((x["name"] or ""), x["school_id"]))
        for chunk, page_no, total in paginate(items):
            filename = f"{province_id}.json" if page_no == 1 else f"{province_id}-{page_no}.json"
            write_json(
                out_dir / "schools" / "province" / filename,
                {
                    "province_id": province_id,
                    "province": PROVINCE_DICT.get(province_id, province_id),
                    "count": total,
                    "page": page_no,
                    "page_size": len(chunk),
                    "items": chunk,
                },
            )

    search_items.sort(key=lambda x: ((x["name"] or ""), x["school_id"]))
    write_json(out_dir / "search" / "schools.json", search_items)
    return {"school_count": count}


def export_majors(conn, out_dir):
    rows = fetch_raw_documents(conn, "majors", "major")
    count = 0
    level1 = defaultdict(int)
    level2 = defaultdict(int)
    level3 = defaultdict(int)
    search_items = []

    for row in rows:
        payload = row["payload"] or {}
        special_id = str(pick_first(payload, ["special_id"], row["entity_key"]))
        bucket = bucket_of(special_id)

        detail = {
            "special_id": special_id,
            "code": pick_first(payload, ["code", "spcode"], ""),
            "name": pick_first(payload, ["name"], ""),
            "level1_name": pick_first(payload, ["level1_name"], ""),
            "level2_name": pick_first(payload, ["level2_name"], ""),
            "level3_name": pick_first(payload, ["level3_name"], ""),
            "degree": pick_first(payload, ["degree"], ""),
            "years": pick_first(payload, ["years", "limit_year"], ""),
            "salary_avg": pick_first(payload, ["salary_avg", "salaryavg"], ""),
            "salary_5year": pick_first(payload, ["salary_5year", "fivesalaryavg"], ""),
            "boy_rate": pick_first(payload, ["boy_rate"], ""),
            "girl_rate": pick_first(payload, ["girl_rate"], ""),
            "rank": pick_first(payload, ["rank"], ""),
            "view_total": pick_first(payload, ["view_total"], ""),
            "view_month": pick_first(payload, ["view_month"], ""),
            "view_week": pick_first(payload, ["view_week"], ""),
        }

        write_json(out_dir / "majors" / "bucket" / bucket / f"{special_id}.json", detail)

        if detail["level1_name"]:
            level1[detail["level1_name"]] += 1
        if detail["level2_name"]:
            level2[detail["level2_name"]] += 1
        if detail["level3_name"]:
            level3[detail["level3_name"]] += 1

        search_items.append({
            "special_id": special_id,
            "code": detail["code"],
            "name": detail["name"],
            "level1_name": detail["level1_name"],
            "level2_name": detail["level2_name"],
            "level3_name": detail["level3_name"],
            "detail_url": public_url("data", "majors", "bucket", bucket, f"{special_id}.json"),
        })
        count += 1

    write_json(out_dir / "majors" / "level1.json", dict(sorted(level1.items())))
    write_json(out_dir / "majors" / "level2.json", dict(sorted(level2.items())))
    write_json(out_dir / "majors" / "level3.json", dict(sorted(level3.items())))
    search_items.sort(key=lambda x: ((x["name"] or ""), x["special_id"]))
    write_json(out_dir / "search" / "majors.json", search_items)

    return {"major_count": count}


def export_school_scores(conn, out_dir):
    rows = fetch_raw_documents(conn, "school_scores", "school_score_bundle")
    count = 0

    for row in rows:
        school_id = str(row["entity_key"])
        bucket = bucket_of(school_id)
        payload = row["payload"] or {}
        summary = payload.get("summary") or {}
        records = payload.get("records") or []

        detail = {
            "school_id": school_id,
            "school_name": summary.get("school_name") or pick_first(payload, ["school_name"], ""),
            "province_count": summary.get("province_count", 0),
            "record_count": summary.get("record_count", len(records)),
            "years": summary.get("years", []),
            "records": records,
        }

        write_json(
            out_dir / "school-scores" / "bucket" / bucket / f"{school_id}.json",
            detail,
        )
        count += 1

    return {"school_score_bundle_count": count}


def export_school_year_docs(conn, out_dir, crawler_name, entity_type, output_top_dir):
    years = fetch_distinct_years(conn, crawler_name, entity_type)
    total_docs = 0

    for year in years:
        rows = fetch_raw_documents(conn, crawler_name, entity_type, year=year)
        province_groups = defaultdict(list)

        for row in rows:
            school_id = str(row["entity_key"])
            bucket = bucket_of(school_id)
            payload = row["payload"] or {}
            summary = payload.get("summary") or {}
            records = payload.get("records") or []

            school_name = summary.get("school_name") or pick_first(payload, ["school_name"], "")
            province_ids = [str(x) for x in (summary.get("province_ids") or [])]

            detail = {
                "school_id": school_id,
                "school_name": school_name,
                "year": str(year),
                "province_count": summary.get("province_count") or summary.get("province_hit_count") or len(province_ids),
                "record_count": summary.get("record_count", len(records)),
                "province_ids": province_ids,
                "province_names": summary.get("province_names", []),
                "records": records,
            }

            write_json(
                out_dir / output_top_dir / str(year) / "bucket" / bucket / f"{school_id}.json",
                detail,
            )

            for province_id in province_ids:
                province_groups[province_id].append({
                    "school_id": school_id,
                    "school_name": school_name,
                    "record_count": detail["record_count"],
                    "detail_url": public_url("data", output_top_dir, str(year), "bucket", bucket, f"{school_id}.json"),
                })

            total_docs += 1

        for province_id, items in province_groups.items():
            items.sort(key=lambda x: ((x["school_name"] or ""), x["school_id"]))
            for chunk, page_no, total in paginate(items):
                filename = f"{province_id}.json" if page_no == 1 else f"{province_id}-{page_no}.json"
                write_json(
                    out_dir / output_top_dir / str(year) / "province" / filename,
                    {
                        "year": str(year),
                        "province_id": province_id,
                        "province": PROVINCE_DICT.get(province_id, province_id),
                        "count": total,
                        "page": page_no,
                        "page_size": len(chunk),
                        "items": chunk,
                    },
                )

    return {
        f"{output_top_dir.replace('-', '_')}_doc_count": total_docs,
        f"{output_top_dir.replace('-', '_')}_years": years,
    }


def validate_build(out_dir):
    json_count = 0
    total_size = 0
    largest_path = ""
    largest_size = 0

    for path in out_dir.rglob("*.json"):
        size = path.stat().st_size
        json_count += 1
        total_size += size
        if size > largest_size:
            largest_size = size
            largest_path = str(path.relative_to(out_dir))

    return {
        "json_file_count": json_count,
        "total_size_bytes": total_size,
        "largest_file": {
            "path": largest_path,
            "size_bytes": largest_size,
        },
    }


def publish_build(tmp_dir, final_dir):
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = final_dir.parent / "_data_backup"

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    if final_dir.exists():
        final_dir.rename(backup_dir)

    tmp_dir.rename(final_dir)

    if backup_dir.exists():
        shutil.rmtree(backup_dir)


def main():
    global DB_SCHEMA, BUCKET_COUNT, INDEX_PAGE_SIZE, PAGES_DATA_VERSION, PAGES_BASE_PATH

    load_env()

    DB_SCHEMA = os.getenv("DB_SCHEMA", "crawler")
    BUCKET_COUNT = int(os.getenv("PAGES_BUCKET_COUNT", "100"))
    INDEX_PAGE_SIZE = int(os.getenv("PAGES_INDEX_PAGE_SIZE", "1000"))
    PAGES_DATA_VERSION = os.getenv("PAGES_DATA_VERSION", "v0.2.0")
    PAGES_BASE_PATH = normalize_base_path(os.getenv("PAGES_BASE_PATH", ""))

    ensure_docs_root()
    ensure_clean_dir(TMP_DATA_DIR)

    stats = {}

    with get_conn() as conn:
        stats.update(export_schools(conn, TMP_DATA_DIR))
        stats.update(export_majors(conn, TMP_DATA_DIR))
        stats.update(export_school_scores(conn, TMP_DATA_DIR))
        stats.update(export_school_year_docs(conn, TMP_DATA_DIR, "scores", "school_year_score", "scores"))
        stats.update(export_school_year_docs(conn, TMP_DATA_DIR, "plans", "school_year_plan", "plans"))
        stats.update(validate_build(TMP_DATA_DIR))
        export_meta(conn, TMP_DATA_DIR, stats)

    publish_build(TMP_DATA_DIR, FINAL_DATA_DIR)

    print("✅ Pages 数据构建完成")
    print(f"输出目录: {FINAL_DATA_DIR}")
    print(f"版本号: {PAGES_DATA_VERSION}")
    print(f"Base Path: {PAGES_BASE_PATH or '/'}")


if __name__ == "__main__":
    main()
