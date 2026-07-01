import os
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseCrawler


def parse_bool(value, default=True):
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


class SchoolCrawler(BaseCrawler):
    DETAIL_CONNECT_TIMEOUT = 3
    DETAIL_READ_TIMEOUT = 12
    DETAIL_MAX_ATTEMPTS = 3

    DETAIL_SLEEP_MIN = 0.3
    DETAIL_SLEEP_MAX = 0.8

    PAGE_SLEEP_MIN = 1.0
    PAGE_SLEEP_MAX = 2.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        retry_strategy = Retry(
            total=2,
            connect=2,
            read=2,
            status=2,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def backoff_sleep(self, attempt):
        wait_s = min(0.8 * (2 ** (attempt - 1)) + random.uniform(0.0, 0.5), 4.0)
        time.sleep(wait_s)

    def get_school_complete_info(self, school_id, max_attempts=None):
        """获取学校完整信息，失败时做有限重试"""
        max_attempts = max_attempts or self.DETAIL_MAX_ATTEMPTS
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.session.get(
                    url,
                    timeout=(self.DETAIL_CONNECT_TIMEOUT, self.DETAIL_READ_TIMEOUT),
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == "0000" and "data" in result:
                        return result["data"]

                last_error = f"HTTP {response.status_code}"
            except Exception as e:
                last_error = str(e)

            if attempt < max_attempts:
                self.backoff_sleep(attempt)

        print(f"⚠️  获取完整信息失败 (ID:{school_id}): {last_error}")
        return None

    def crawl(self, mode=None, max_pages=None, fetch_complete_info=None):
        """爬取学校列表
        规则：
        - test: 固定 1 页
        - full: 忽略 max_pages，直到接口无数据
        - 其他: 使用 max_pages / 环境变量
        """
        mode = (mode or os.getenv("CRAWL_MODE", "test")).strip().lower()

        if fetch_complete_info is None:
            fetch_complete_info = parse_bool(os.getenv("FETCH_COMPLETE_INFO", "true"), True)
        else:
            fetch_complete_info = parse_bool(fetch_complete_info, True)

        if mode == "test":
            page_limit = 1
        elif mode == "full":
            page_limit = None
        else:
            if max_pages is None:
                page_limit = int(os.getenv("MAX_PAGES", "10"))
            else:
                page_limit = int(max_pages)

        schools = []
        page = 1
        total_detail_success = 0
        total_detail_fail = 0

        print(f"\n{'=' * 60}")
        print("开始爬取学校数据")
        print(f"模式: {mode}")
        print(f"页数限制: {'不限，直到最后一页' if page_limit is None else page_limit}")
        print(f"完整信息: {'✓' if fetch_complete_info else '✗'}")
        print(f"{'=' * 60}\n")

        while True:
            if page_limit is not None and page > page_limit:
                break

            payload = {
                "keyword": "",
                "page": page,
                "province_id": "",
                "ranktype": "",
                "request_type": 1,
                "size": 20,
                "type": "",
                "uri": "apidata/api/gkv3/school/lists",
            }

            data = self.make_request(payload)

            if not data or "data" not in data or "item" not in data["data"]:
                print(f"✗ 第 {page} 页请求失败")
                break

            items = data["data"]["item"]
            if not items:
                print(f"✓ 第 {page} 页无数据，已到最后一页")
                break

            print(f"第 {page} 页: 获取 {len(items)} 所学校", end="", flush=True)

            page_detail_success = 0
            page_detail_fail = 0

            for idx, item in enumerate(items, 1):
                school_id = item.get("school_id")

                school_info = {
                    "school_id": school_id,
                    "name": item.get("name"),

                    "province": item.get("province_name"),
                    "city": item.get("city_name"),
                    "county": item.get("county_name"),

                    "type": item.get("type_name"),
                    "level": item.get("level_name"),
                    "nature": item.get("nature_name"),
                    "belong": item.get("belong"),

                    "rank": item.get("rank"),
                    "f985": item.get("f985"),
                    "f211": item.get("f211"),
                    "dual_class": item.get("dual_class_name"),
                    "is_dual_class": item.get("dual_class"),

                    "view_total": item.get("view_total"),
                }

                if fetch_complete_info and school_id:
                    complete_info = self.get_school_complete_info(school_id)

                    if complete_info:
                        label_list_detail = complete_info.get("label_list", [])
                        if isinstance(label_list_detail, list):
                            label_list = [
                                x.get("name")
                                for x in label_list_detail
                                if isinstance(x, dict)
                            ]
                        else:
                            label_list = []

                        try:
                            rank_num = int(school_info.get("rank", 999))
                            is_top = 1 if rank_num <= 10 else 2
                        except Exception:
                            is_top = 2

                        school_info.update({
                            "content": complete_info.get("content"),
                            "motto": complete_info.get("motto"),
                            "old_name": complete_info.get("old_name"),

                            "email": complete_info.get("email"),
                            "school_email": complete_info.get("school_email"),
                            "phone": complete_info.get("phone"),
                            "school_phone": complete_info.get("school_phone"),
                            "address": complete_info.get("address"),
                            "postcode": complete_info.get("postcode"),

                            "site": complete_info.get("site"),
                            "school_site": complete_info.get("school_site"),

                            "create_date": complete_info.get("create_date"),
                            "area": complete_info.get("area"),

                            "num_doctor": complete_info.get("num_doctor"),
                            "num_master": complete_info.get("num_master"),
                            "num_subject": complete_info.get("num_subject"),
                            "num_academician": complete_info.get("num_academician"),
                            "num_library": complete_info.get("num_library"),

                            "recommend_master_rate": complete_info.get("recommend_master_rate"),
                            "recommend_master_level": complete_info.get("recommend_master_level"),
                            "upgrading_rate": complete_info.get("upgrading_rate"),

                            "ruanke_rank": complete_info.get("ruanke_rank"),
                            "xyh_rank": complete_info.get("xyh_rank"),
                            "wsl_rank": complete_info.get("wsl_rank"),
                            "qs_rank": complete_info.get("qs_rank"),
                            "us_rank": complete_info.get("us_rank"),
                            "qs_world": complete_info.get("qs_world"),

                            "label_list": label_list,
                            "label_list_detail": label_list_detail,
                            "attr_list": complete_info.get("attr_list", []),
                            "is_top": is_top,
                            "hightitle": complete_info.get("name"),

                            "dualclass": complete_info.get("dualclass"),
                            "special": complete_info.get("special"),
                            "province_score_min": complete_info.get("province_score_min"),
                            "rank_detail": complete_info.get("rank"),
                        })
                        page_detail_success += 1
                        total_detail_success += 1
                        self.polite_sleep(self.DETAIL_SLEEP_MIN, self.DETAIL_SLEEP_MAX)
                    else:
                        page_detail_fail += 1
                        total_detail_fail += 1

                schools.append(school_info)

                if idx % 5 == 0:
                    print(".", end="", flush=True)

            if fetch_complete_info:
                print(f" ✓ 详情成功:{page_detail_success} 失败:{page_detail_fail}")
            else:
                print(" ✓")

            page += 1
            self.polite_sleep(self.PAGE_SLEEP_MIN, self.PAGE_SLEEP_MAX)

        self.save_to_json(schools, "schools.json")

        print(f"\n{'=' * 60}")
        print(f"✅ 爬取完成！共 {len(schools)} 所学校")
        if fetch_complete_info:
            print(f"   详情成功: {total_detail_success}")
            print(f"   详情失败: {total_detail_fail}")
        if schools:
            field_count = len(schools[0].keys())
            has_content = bool(schools[0].get("content"))
            has_email = bool(schools[0].get("email"))
            has_labels = len(schools[0].get("label_list", []))
            print(f"   字段数: {field_count}")
            print(f"   学校介绍: {'✓' if has_content else '✗'}")
            print(f"   联系邮箱: {'✓' if has_email else '✗'}")
            print(f"   标签数量: {has_labels}")
        print(f"{'=' * 60}\n")

        return schools


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else os.getenv("CRAWL_MODE", "test")
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].strip() else None
    fetch_complete_info = parse_bool(sys.argv[3], True) if len(sys.argv) > 3 else None

    crawler = SchoolCrawler()
    crawler.crawl(
        mode=mode,
        max_pages=max_pages,
        fetch_complete_info=fetch_complete_info,
    )
