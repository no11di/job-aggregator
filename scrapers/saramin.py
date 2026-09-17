import re
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from models import JobItem
import requests
from requests.adapters import HTTPAdapter
from scrapers.base import BaseScraper
from urllib3.util.retry import Retry


class SaraminScraper(BaseScraper):

  def __init__(self, delay: float = 1.0):
    super().__init__(platform_name="saramin", delay=delay)
    self.base_url = "https://www.saramin.co.kr"
    self.target_url = f"{self.base_url}/zf_user/search/recruit"

    self.headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.saramin.co.kr/",
        "Connection": "keep-alive",
    }

    # 세션 생성 및 재시도 정책 수립 (일시적 패킷 드롭 대비)
    self.session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    self.session.mount("https://", adapter)
    self.session.mount("http://", adapter)

  def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
    collected: Dict[str, JobItem] = {}
    page = 1
    page_size = 50
    total_count = None

    while True:
      params = {
          "recruitPage": page,
          "loc_mcd": "101000,102000,108000",  # 서울, 경기, 인천
          "cat_kewd": "2229,99",  # QA, 테스터
          "exp_cd": "2",  # 경력
          "recruitSort": "relation",
          "recruitPageCount": page_size,
      }

      try:
        # connect timeout 5초, read timeout 15초 분리
        res = self.session.get(
            self.target_url,
            headers=self.headers,
            params=params,
            timeout=(5, 15),
        )
        res.raise_for_status()
      except requests.exceptions.ConnectTimeout:
        print(
            f"[사람인] 연결 타임아웃 발생 (page={page}): 해외 데이터센터 IP"
            " 일시적 차단"
        )
        break
      except Exception as e:
        print(f"[사람인] 요청 실패 (page={page}): {e}")
        break

      soup = BeautifulSoup(res.text, "html.parser")
      items = soup.select(".item_recruit")

      if not items:
        break

      # 1페이지에서 전체 검색 건수 확인
      if total_count is None:
        cnt_el = soup.select_one(".cnt_result, .total_count")
        if cnt_el:
          num_match = re.search(r"[\d,]+", cnt_el.get_text())
          if num_match:
            total_count = int(num_match.group().replace(",", ""))
        if total_count is None:
          total_count = 500

      for item in items:
        tit_el = item.select_one(".job_tit a")
        if not tit_el:
          continue

        title = tit_el.get_text(strip=True)
        raw_link = tit_el.get("href", "")
        link = (
            urljoin(self.base_url, raw_link)
            if raw_link.startswith("/")
            else raw_link
        )

        idx_match = re.search(r"rec_idx=(\d+)", link)
        post_id = idx_match.group(1) if idx_match else item.get("value", "")
        if not post_id or post_id in collected:
          continue

        corp_el = item.select_one(".corp_name a")
        company_raw = (
            corp_el.get_text(strip=True) if corp_el else "회사명 미제공"
        )
        company_clean = self.clean_company_name(company_raw)

        date_el = item.select_one(".job_date .date")
        deadline = (
            date_el.get_text(strip=True) if date_el else "상시/채용시 마감"
        )

        collected[post_id] = JobItem(
            platform=self.platform_name,
            post_id=str(post_id),
            company_raw=company_raw,
            company_clean=company_clean,
            title=title,
            link=link,
            deadline=deadline,
        )

      if len(collected) >= total_count:
        break

      page += 1
      self.sleep()

      if page > 15:
        break

    return list(collected.values())