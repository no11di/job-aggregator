from typing import List, Dict
from curl_cffi import requests  # 💡 툴킷 변경 (TLS 지문 우회)
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
        "wanted-user-agent": "user-web",
        "wanted-user-country": "KR",
        "wanted-user-language": "ko",
    }

  def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
    collected: Dict[str, JobItem] = {}
    offset = 0
    limit = 50  # 1회 요청당 공고 수

    while True:
      params = {
          "job_group_id": "518",
          "job_ids": "676",
          "country": "kr",
          "job_sort": "job.latest_order",
          "years": "-1",
          "locations": ["seoul.all", "incheon.all", "gyeonggi.all"],
          "limit": str(limit),
          "offset": str(offset),
      }

      try:
        # 💡 impersonate="chrome"을 주면 크롬 브라우저의 TLS 지문과 헤더를 그대로 흉내 냄
        res = requests.get(
            self.api_url,
            headers=self.headers,
            params=params,
            impersonate="chrome",
            timeout=10,
        )
        res.raise_for_status()
        res_data = res.json()
      except Exception as e:
        print(f"[원티드] 요청 실패 (offset={offset}): {e}")
        break

      items = res_data.get("data", [])
      if not isinstance(items, list) or not items:
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

      offset += limit
      self.sleep()

    return list(collected.values())