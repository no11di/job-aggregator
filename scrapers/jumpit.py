import re
from typing import List, Dict
import requests
from models import JobItem
from scrapers.base import BaseScraper


class JumpitScraper(BaseScraper):

  def __init__(self, delay: float = 1.0):
    super().__init__(platform_name="jumpit", delay=delay)
    self.api_url = "https://jumpit-api.saramin.co.kr/api/positions"
    self.headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://jumpit.saramin.co.kr/",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }

  def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
    collected: Dict[str, JobItem] = {}
    page = 1

    while True:
      params = [
          ("jobCategory", "11"),  # QA 엔지니어 카테고리
          ("locationTag", "101000"),  # 서울
          ("locationTag", "102000"),  # 경기
          ("locationTag", "108000"),  # 인천
          ("sort", "popular"),  # 인기순/최신순
          ("highlight", "false"),
          ("page", str(page)),
      ]

      try:
        res = requests.get(
            self.api_url, headers=self.headers, params=params, timeout=10
        )
        res.raise_for_status()
        res_json = res.json()
      except Exception as e:
        print(f"[점핏] 요청 실패 (page={page}): {e}")
        break

      result = res_json.get("result", {})
      positions = result.get("positions", [])

      if not positions:
        break

      for p in positions:
        post_id = str(p.get("id"))
        if not post_id or post_id in collected:
          continue

        # HTML 태그 제거 (<span>QA</span> 등 방지)
        raw_title = p.get("title", "").strip()
        title = re.sub(r"<[^>]+>", "", raw_title).strip()

        company_raw = p.get("companyName", "회사명 미제공")
        company_clean = self.clean_company_name(company_raw)
        link = f"https://www.jumpit.co.kr/position/{post_id}"

        # 마감일 정제
        if p.get("alwaysOpen", False):
          deadline = "상시채용"
        else:
          closed_at = p.get("closedAt", "")
          # '2026-09-25T23:59:59' 형태일 경우 날짜만 추출
          deadline = (
              closed_at.split("T")[0] if "T" in closed_at else "상시/채용시 마감"
          )

        collected[post_id] = JobItem(
            platform=self.platform_name,
            post_id=post_id,
            company_raw=company_raw,
            company_clean=company_clean,
            title=title,
            link=link,
            deadline=deadline,
        )

      total_count = result.get("totalCount", 0)
      if len(collected) >= total_count:
        break

      page += 1
      self.sleep()

    return list(collected.values())