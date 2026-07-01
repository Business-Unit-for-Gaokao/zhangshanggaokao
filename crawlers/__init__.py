__all__ = [
    "SchoolCrawler",
    "MajorCrawler",
    "ScoreCrawler",
    "PlanCrawler",
    "SchoolScoreCrawler",
    "DepartmentCrawler",
    "JobCrawler",
    "QiangjiCrawler",
    "SpecialCrawler",
]


def __getattr__(name):
    if name == "SchoolCrawler":
        from .schools import SchoolCrawler
        return SchoolCrawler
    if name == "MajorCrawler":
        from .majors import MajorCrawler
        return MajorCrawler
    if name == "ScoreCrawler":
        from .scores import ScoreCrawler
        return ScoreCrawler
    if name == "PlanCrawler":
        from .plans import PlanCrawler
        return PlanCrawler
    if name == "SchoolScoreCrawler":
        from .school_scores import SchoolScoreCrawler
        return SchoolScoreCrawler
    if name == "DepartmentCrawler":
        from .departments import DepartmentCrawler
        return DepartmentCrawler
    if name == "JobCrawler":
        from .jobs import JobCrawler
        return JobCrawler
    if name == "QiangjiCrawler":
        from .qiangji import QiangjiCrawler
        return QiangjiCrawler
    if name == "SpecialCrawler":
        from .specials import SpecialCrawler
        return SpecialCrawler
    raise AttributeError(f"module 'crawlers' has no attribute {name!r}")
