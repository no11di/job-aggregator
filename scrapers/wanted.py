from typing import List, Dict
import requests
from models import JobItem
from scrapers.base import BaseScraper


class WantedScraper(BaseScraper):

  def __init__(self, delay: float = 1.0):
    super().__init__(platform_name="wanted", delay=delay)
    self.api_url = (
        "https://www.wanted.co.kr/api/chaos/navigation/v1/results"
    )
    self.headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.wanted.co.kr/wdlist/518/676",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "wanted-user-agent": "user-web",
        "wanted-user-country": "KR",
        "wanted-user-language": "ko",
    }

  def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
    collected: Dict[str, JobItem] = {}
    offset = 0
    limit = 50  # 1회 요청당 공고 수

    while True:
      params = [
          ("job_group_id", "518"),
          ("job_ids", "676"),
          ("country", "kr"),
          ("job_sort", "job.latest_order"),
          ("years", "-1"),
          ("locations", "seoul.all"),
          ("locations", "incheon.all"),
          ("locations", "gyeonggi.all"),
          ("limit", str(limit)),
          ("offset", str(offset)),
      ]

      try:
        res = requests.get(
            self.api_url, headers=self.headers, params=params, timeout=10
        )
        res.raise_for_status()
        res_data = res.json()
      except Exception as e:
        print(f"[원티드] 요청 실패 (offset={offset}): {e}")
        break

      items = res_data.get("data", [])
      if not isinstance(items, list) or not items:
        # 더 이상 불러올 공고가 없으면 스크롤 종료
        break

      for item in items:
        if not isinstance(item, dict):
          continue

        post_id = str(item.get("id"))
        if not post_id or post_id in collected:
          continue

        title = item.get("position", "").strip()
        company_info = item.get("company") or {}
        company_raw = (
            company_info.get("name", "회사명 미제공")
            if isinstance(company_info, dict)
            else str(company_info)
        )
        company_clean = self.clean_company_name(company_raw)
        link = f"https://www.wanted.co.kr/wd/{post_id}"
        deadline = item.get("due_time") or "상시채용"

        collected[post_id] = JobItem(
            platform=self.platform_name,
            post_id=post_id,
            company_raw=company_raw,
            company_clean=company_clean,
            title=title,
            link=link,
            deadline=deadline,
        )

      # 다음 스크롤 오프셋으로 이동
      offset += limit
      self.sleep()

    return list(collected.values())