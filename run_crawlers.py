import os
import sys
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from crawlers import (
    SchoolCrawler,
    MajorCrawler,
    ScoreCrawler,
    PlanCrawler,
    SchoolScoreCrawler,
)


def parse_bool(value):
    if value is None:
        return None
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def set_env_if_present(key, value):
    if value is not None and str(value).strip() != "":
        os.environ[key] = str(value)


def run_schools(args):
    set_env_if_present("CRAWL_MODE", args.mode)
    set_env_if_present("SAMPLE_SCHOOLS", args.sample_schools)
    set_env_if_present("FETCH_COMPLETE_INFO", args.fetch_complete_info)
    set_env_if_present("SCHOOL_EXPORT_JSON", args.school_export_json)
    set_env_if_present("SCHOOL_SKIP_EXISTING", args.school_skip_existing)

    crawler = SchoolCrawler()
    return crawler.crawl(
        mode=args.mode,
        max_pages=args.max_pages,
        fetch_complete_info=parse_bool(args.fetch_complete_info) if args.fetch_complete_info is not None else None,
    )


def run_majors(args):
    set_env_if_present("CRAWL_MODE", args.mode)
    set_env_if_present("MAX_PAGES", args.max_pages)
    set_env_if_present("MAJOR_DEBUG", args.major_debug)
    set_env_if_present("MAJOR_EXPORT_JSON", args.major_export_json)
    set_env_if_present("MAJOR_SKIP_EXISTING", args.major_skip_existing)

    crawler = MajorCrawler()
    return crawler.crawl(
        mode=args.mode,
        max_pages=args.max_pages,
        debug=parse_bool(args.major_debug) if args.major_debug is not None else None,
    )


def run_school_scores(args):
    set_env_if_present("SAMPLE_SCHOOLS", args.sample_schools)
    set_env_if_present("SCHOOL_SCORE_EXPORT_JSON", args.school_score_export_json)
    set_env_if_present("SCHOOL_SCORE_SKIP_EXISTING", args.school_score_skip_existing)
    set_env_if_present("SCHOOL_SCORE_SCOPE_KEY", args.school_score_scope_key)

    crawler = SchoolScoreCrawler()
    return crawler.crawl()


def run_scores(args):
    set_env_if_present("SAMPLE_SCHOOLS", args.sample_schools)
    set_env_if_present("SCORE_EXPORT_JSON", args.score_export_json)
    set_env_if_present("SCORE_SKIP_EXISTING", args.score_skip_existing)
    set_env_if_present("SCORE_YEARS", args.years)

    crawler = ScoreCrawler()
    return crawler.crawl(
        years=args.years,
    )


def run_plans(args):
    set_env_if_present("CRAWL_MODE", args.mode)
    set_env_if_present("SAMPLE_SCHOOLS", args.sample_schools)
    set_env_if_present("PLAN_DEBUG", args.plan_debug)
    set_env_if_present("PLAN_SKIP_EXISTING", args.plan_skip_existing)
    set_env_if_present("PLAN_YEARS", args.years)

    crawler = PlanCrawler()
    return crawler.crawl(
        years=args.years,
        mode=args.mode,
    )


def run_all(args):
    results = {}

    print("\n" + "=" * 70)
    print("开始执行全量爬虫流程")
    print("=" * 70)

    print("\n[1/5] schools")
    results["schools"] = run_schools(args)

    print("\n[2/5] majors")
    results["majors"] = run_majors(args)

    print("\n[3/5] school_scores")
    results["school_scores"] = run_school_scores(args)

    print("\n[4/5] scores")
    results["scores"] = run_scores(args)

    print("\n[5/5] plans")
    results["plans"] = run_plans(args)

    print("\n" + "=" * 70)
    print("全量爬虫流程执行完成")
    print("=" * 70)
    return results


def build_parser():
    parser = argparse.ArgumentParser(
        description="统一运行 gaokao-crawler 的各类爬虫"
    )

    parser.add_argument(
        "task",
        choices=["all", "schools", "majors", "school_scores", "scores", "plans"],
        help="要执行的任务",
    )

    parser.add_argument(
        "--mode",
        default=os.getenv("CRAWL_MODE", "test"),
        help="运行模式，如 test / sample / full",
    )
    parser.add_argument(
        "--years",
        default=os.getenv("PLAN_YEARS") or os.getenv("SCORE_YEARS"),
        help="年份，如 2025,2024,2023 或 2021-2025",
    )
    parser.add_argument(
        "--sample-schools",
        type=int,
        default=int(os.getenv("SAMPLE_SCHOOLS", "3")),
        help="只处理前 N 所学校",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="最大页数，仅部分分页爬虫使用",
    )

    parser.add_argument(
        "--fetch-complete-info",
        default=os.getenv("FETCH_COMPLETE_INFO"),
        help="schools 是否抓完整详情，true/false",
    )
    parser.add_argument(
        "--major-debug",
        default=os.getenv("MAJOR_DEBUG"),
        help="majors 是否打印调试结构，true/false",
    )
    parser.add_argument(
        "--plan-debug",
        default=os.getenv("PLAN_DEBUG"),
        help="plans 是否打印调试结构，true/false",
    )

    parser.add_argument(
        "--school-export-json",
        default=os.getenv("SCHOOL_EXPORT_JSON"),
        help="schools 是否导出本地 json，true/false",
    )
    parser.add_argument(
        "--major-export-json",
        default=os.getenv("MAJOR_EXPORT_JSON"),
        help="majors 是否导出本地 json，true/false",
    )
    parser.add_argument(
        "--school-score-export-json",
        default=os.getenv("SCHOOL_SCORE_EXPORT_JSON"),
        help="school_scores 是否导出本地 json，true/false",
    )
    parser.add_argument(
        "--score-export-json",
        default=os.getenv("SCORE_EXPORT_JSON"),
        help="scores 是否导出本地 json，true/false",
    )

    parser.add_argument(
        "--school-skip-existing",
        default=os.getenv("SCHOOL_SKIP_EXISTING"),
        help="schools 是否跳过库中已存在记录，true/false",
    )
    parser.add_argument(
        "--major-skip-existing",
        default=os.getenv("MAJOR_SKIP_EXISTING"),
        help="majors 是否跳过库中已存在记录，true/false",
    )
    parser.add_argument(
        "--school-score-skip-existing",
        default=os.getenv("SCHOOL_SCORE_SKIP_EXISTING"),
        help="school_scores 是否跳过库中已存在记录，true/false",
    )
    parser.add_argument(
        "--score-skip-existing",
        default=os.getenv("SCORE_SKIP_EXISTING"),
        help="scores 是否跳过库中已存在记录，true/false",
    )
    parser.add_argument(
        "--plan-skip-existing",
        default=os.getenv("PLAN_SKIP_EXISTING"),
        help="plans 是否跳过库中已存在记录，true/false",
    )

    parser.add_argument(
        "--school-score-scope-key",
        default=os.getenv("SCHOOL_SCORE_SCOPE_KEY", "default"),
        help="school_scores 断点作用域标识",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.task == "all":
            run_all(args)
        elif args.task == "schools":
            run_schools(args)
        elif args.task == "majors":
            run_majors(args)
        elif args.task == "school_scores":
            run_school_scores(args)
        elif args.task == "scores":
            run_scores(args)
        elif args.task == "plans":
            run_plans(args)
        else:
            parser.error(f"不支持的任务: {args.task}")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断运行")
        raise SystemExit(130)
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
