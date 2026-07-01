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


## Pending Consolidation Notes

### Scores crawler / provinceline data

`Business-Unit-for-Gaokao/gaokao-scores-crawler` should not remain as a long-term standalone repository. Its reusable source should be consolidated into this `zhangshanggaokao` repository before the old repository is deleted.

Decision notes:

- Historical JSON results from `gaokao-scores-crawler` have already been consolidated into `Business-Unit-for-Gaokao/gaokao-data-json`.
- The existing `gaokao-scores-crawler` uses static `static-data.gaokao.cn/www/2.0/schoolspecialscore/...` data, which is not the right complete source for the `https://www.gaokao.cn/school/{school_id}/provinceline` page.
- Future implementation should use the dynamic 掌上高考 API observed from the page, especially `api-gaokao.zjzw.cn/apidata/web` with `uri=v1/school/province_score`, and parameters such as `school_id`, `year`, `local_province_id`, `local_type_id`, `page`, `size`, and `platform=2`.
- This note records the consolidation decision only; the scores/provinceline crawler is not implemented in this repository yet.

