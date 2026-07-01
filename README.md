# gaokao-crawler-factory
爬虫工厂

<!-- target-crawl-links:start -->
## Target Crawl Links

This repository is a crawler factory/management project. It does not define a single target site in its current source files. Generated crawler repositories currently target 掌上高考.

| Generated crawler line | Link |
| --- | --- |
| 掌上高考根域名 | `https://www.gaokao.cn` |
| 静态数据域名 | `https://static-data.gaokao.cn` |
<!-- target-crawl-links:end -->

<!-- crawl-sources:start -->
## 爬取链接 / 数据源

> 维护说明：本仓库是爬虫仓库生成工厂，源码中没有直接执行的数据爬取逻辑；爬取结果文件（data/results/output/json/csv/xlsx 等）不纳入统计。

### 生成目标涉及的源站

- `https://static-data.gaokao.cn`
- `https://www.gaokao.cn`
<!-- crawl-sources:end -->

## Included Crawlers

### Department crawler

This repository now contains the consolidated 掌上高考院系/院校部门数据 crawler formerly kept in `Business-Unit-for-Gaokao/gaokao-department-crawler`.

Crawler files:

- `crawlers/base.py`
- `crawlers/departments.py`
- `.github/workflows/crawl_departments.yml`
- `data/schools.json`

Target API:

- `https://static-data.gaokao.cn/www/2.0/school/department/{school_id}.json?a=www.gaokao.cn`

Output path when run:

- `data/departments/{school_id}.json`

Historical JSON results are consolidated in `Business-Unit-for-Gaokao/gaokao-data-json` under:

- `zsgk/gaokao-department-crawler/data/departments/`


### Jobs crawler

This repository now contains the consolidated 掌上高考就业/就业质量数据 crawler formerly kept in `Business-Unit-for-Gaokao/gaokao-jobs-crawler`.

Crawler files:

- `crawlers/jobs.py`
- `scripts/run_jobs_once.py`
- `.github/workflows/crawl_jobs.yml`
- shared `crawlers/base.py`
- shared `data/schools.json`

Target API:

- `https://static-data.gaokao.cn/www/2.0/school/{school_id}/pc_jobdetail.json?a=www.gaokao.cn`

Output path when run:

- `data/jobs/{school_id}.json`

Historical JSON results are consolidated in `Business-Unit-for-Gaokao/gaokao-data-json` under:

- `zsgk/gaokao-jobs-crawler/data/jobs/`



### Special crawler

This repository now contains the consolidated 掌上高考院校专业数据 crawler formerly kept in `Business-Unit-for-Gaokao/gaokao-special-crawler`.

Crawler files:

- `crawlers/specials.py`
- `scripts/run_specials_once.py`
- `.github/workflows/crawl_specials.yml`
- shared `crawlers/base.py`
- shared `data/schools.json`

Target API:

- `https://static-data.gaokao.cn/www/2.0/school/{school_id}/pc_special.json?a=www.gaokao.cn`

Output path when run:

- `data/specials/{school_id}.json`

Historical JSON results are consolidated in `Business-Unit-for-Gaokao/gaokao-data-json` under:

- `zsgk/gaokao-special-crawler/data/specials/`


## Pending Consolidation Notes

### Scores crawler / provinceline data

`Business-Unit-for-Gaokao/gaokao-scores-crawler` should not remain as a long-term standalone repository. Its reusable source should be consolidated into this `zhangshanggaokao` repository before the old repository is deleted.

Decision notes:

- Historical JSON results from `gaokao-scores-crawler` have already been consolidated into `Business-Unit-for-Gaokao/gaokao-data-json`.
- The existing `gaokao-scores-crawler` uses static `static-data.gaokao.cn/www/2.0/schoolspecialscore/...` data, which is not the right complete source for the `https://www.gaokao.cn/school/{school_id}/provinceline` page.
- Future implementation should use the dynamic 掌上高考 API observed from the page, especially `api-gaokao.zjzw.cn/apidata/web` with `uri=v1/school/province_score`, and parameters such as `school_id`, `year`, `local_province_id`, `local_type_id`, `page`, `size`, and `platform=2`.
- This note records the consolidation decision only; the scores/provinceline crawler is not implemented in this repository yet.

## 强基计划数据 crawler consolidation

Former source repository: `Business-Unit-for-Gaokao/gaokao-qiangji-crawler`.

This repository now contains the reusable 掌上高考强基计划 crawler source:

- `.github/workflows/crawl_qiangji.yml`
- `crawlers/qiangji.py`
- `scripts/run_qiangji_once.py`
- `scripts/dispatch_next_run.sh`
- `scripts/plan_chain.py`
- `scripts/resolve_years.sh`

Target source/API:

- `https://static-data.gaokao.cn/www/2.0/qiangji/school/{school_id}/info.json?a=www.gaokao.cn`

Runtime output path when this crawler runs:

- `data/qiangji/`
- `data/qiangji_progress/`

Historical JSON output is not duplicated in this source repository. It belongs in the consolidated data repository:

- `Business-Unit-for-Gaokao/gaokao-data-json`
- `zsgk/gaokao-qiangji-crawler/data/qiangji/`
## Legacy 掌上高考 crawler consolidation

Former source repository: `Business-Unit-for-Gaokao/zhangshang-gaokao-crawler`.

This repository is the retained 掌上高考 / `gaokao.cn` source repository. The reusable crawler source from the legacy repository has been consolidated here, including:

- `crawlers/schools.py` and `.github/workflows/crawl_schools.yml`
- `crawlers/majors.py` and `.github/workflows/crawl_majors.yml`
- `crawlers/plans.py` and `.github/workflows/crawl_plans.yml`
- `crawlers/school_scores.py` and `.github/workflows/crawl_school_scores.yml`
- `crawlers/scores.py` and `.github/workflows/crawl_scores.yml` as historical/static score-source reference
- `run_crawlers.py`, `utils/`, and legacy Pages data-building helper scripts under `scripts/`

Target/API sources found in the legacy code:

- `https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json`
- `https://static-data.gaokao.cn/www/2.0/schoolspecialplan/{school_id}/{year}/{province_id}.json`
- `https://static-data.gaokao.cn/www/2.0/schoolspecialscore/{school_id}/{year}/{province_id}.json`
- `https://api.zjzw.cn/web/api/` with `uri=apidata/api/gkv3/school/lists` and `uri=apidata/api/gkv3/special/lists`

Historical generated JSON output is not duplicated in this source repository. It belongs in:

- `Business-Unit-for-Gaokao/gaokao-data-json`
- legacy paths such as `zsgk/zhangshang-gaokao-crawler/data/plans/`, `data/scores/`, `data/school_scores/`, and `data/majors.json` if preserved there.

`deploy-pages.yml` from the legacy repository was intentionally not enabled here during source consolidation because Pages publishing is deployment behavior. Keep deployment/Pages publication in the `deploy` repository or add it through a separate explicit deployment change.

Note on scores/provinceline: the legacy `scores` crawler uses static `schoolspecialscore` data. The full `provinceline` page should use the dynamic `api-gaokao.zjzw.cn/apidata/web` API with `uri=v1/school/province_score` when that feature is implemented.

## 招生计划 crawler consolidation

- Former source repo: `Business-Unit-for-Gaokao/gaokao-plans-crawler`
- Primary static API: `https://static-data.gaokao.cn/www/2.0/schoolspecialplan/{school_id}/{year}/{province_id}.json`
- Runtime output path: `data/plans/` with progress in `data/plans_progress/`
- The retained repo uses `data/schools.json` as the school seed; bulk historical `data/plans/` and `data/oldplans/` JSON are not duplicated here.
- Historical JSON belongs in `Business-Unit-for-Gaokao/gaokao-data-json`, under the original source path when present.
- Legacy page-crawler experience from `FutureTechnique/plans` is kept as source/reference under `crawlers/gaokao_cn_school_plans_v13/` and `docs/futuretechnique-plans-migration.md`.
