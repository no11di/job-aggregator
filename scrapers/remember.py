import requests
from typing import List, Dict
from models import JobItem
from scrapers.base import BaseScraper

class RememberScraper(BaseScraper):
    def __init__(self, delay: float = 1.0):
        super().__init__(platform_name="remember", delay=delay)
        self.api_url = "https://career-api.rememberapp.co.kr/job_postings/search"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://career.rememberapp.co.kr/"
        }

    def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
        collected: Dict[str, JobItem] = {}
        page = 1
        per_page = 30

        while True:
            payload = {
                "search": {
                    "job_category_names": [
                        {"level1": "SW개발", "level2": "QA·테스터·검증"}
                    ],
                    "addresses": [["서울특별시"], ["인천광역시"], ["경기도"]],
                    "include_applied_job_posting": False,
                    "min_salary": None,
                    "max_salary": None,
                    "only_salary_negotiable": True
                },
                "sort": "starts_at_desc",
                "page": page,
                "per": per_page
            }

            try:
                res = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=10
                )
                res.raise_for_status()
                res_json = res.json()
            except Exception as e:
                print(f"[리멤버] 요청 실패 (page={page}): {e}")
                break

            items = res_json.get("data", [])
            if not items:
                break

            for item in items:
                post_id = str(item.get("id"))
                if not post_id or post_id in collected:
                    continue

                title = item.get("title", "").strip()
                org = item.get("organization") or {}
                company_raw = org.get("name", "회사명 미제공")
                company_clean = self.clean_company_name(company_raw)
                link = f"https://career.rememberapp.co.kr/job/posting/{post_id}"

                ends_at = item.get("ends_at")
                if ends_at:
                    deadline = ends_at.split("T")[0] if "T" in ends_at else ends_at
                else:
                    deadline = "상시채용"

                collected[post_id] = JobItem(
                    platform=self.platform_name,
                    post_id=post_id,
                    company_raw=company_raw,
                    company_clean=company_clean,
                    title=title,
                    link=link,
                    deadline=deadline
                )

            meta = res_json.get("meta", {})
            total_pages = meta.get("total_pages") or meta.get("total_page", 1)
            total_count = meta.get("total_count", 0)

            if page >= total_pages or len(collected) >= total_count:
                break

            page += 1
            self.sleep()

        return list(collected.values())