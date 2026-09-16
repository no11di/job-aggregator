import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from models import JobItem
from scrapers.base import BaseScraper

class JobKoreaScraper(BaseScraper):
    def __init__(self, delay: float = 1.0):
        super().__init__(platform_name="jobkorea", delay=delay)
        self.base_url = "https://www.jobkorea.co.kr"
        self.api_url = f"{self.base_url}/Recruit/Home/_GI_List/"
        self.headers = {
            "Accept": "text/html, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://www.jobkorea.co.kr/recruit/joblist",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest"
        }

    def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
        collected: Dict[str, JobItem] = {}
        page = 1
        page_size = 50

        while True:
            payload = {
                "page": page,
                "pagesize": page_size,
                "condition[duty]": "1000247",          # 직무: QA
                "condition[local]": "I000,K000,B000",   # 서울, 경기, 인천
                "order": "20",                          # 최신순
                "tabindex": 0,
                "direct": 0,
                "onePick": 0,
                "confirm": 0,
                "profile": 0
            }

            try:
                res = requests.post(self.api_url, headers=self.headers, data=payload, timeout=10)
                res.raise_for_status()
            except Exception as e:
                print(f"[잡코리아] 요청 실패 (page={page}): {e}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("tr.devloopArea")

            if not rows:
                break

            for row in rows:
                post_id = row.get("data-gno", "").strip()
                if not post_id or post_id in collected:
                    continue

                co_elem = row.select_one("td.tplCo a.link")
                company_raw = co_elem.get_text(strip=True) if co_elem else "회사명 미제공"
                company_clean = self.clean_company_name(company_raw)

                tit_elem = row.select_one("td.tplTit strong a.link")
                if not tit_elem:
                    continue
                title = tit_elem.get_text(strip=True)
                raw_link = tit_elem.get("href", "")
                link = f"{self.base_url}{raw_link}" if raw_link.startswith("/") else raw_link

                date_elem = row.select_one("td.odd span.date")
                deadline = date_elem.get_text(strip=True) if date_elem else "상시채용"

                collected[post_id] = JobItem(
                    platform=self.platform_name,
                    post_id=post_id,
                    company_raw=company_raw,
                    company_clean=company_clean,
                    title=title,
                    link=link,
                    deadline=deadline
                )

            # 전체 카운트 도달 여부 체크
            total_cnt_elem = soup.select_one("#hdnGICnt")
            if total_cnt_elem:
                try:
                    total_cnt = int(total_cnt_elem.get("value", 0))
                    if len(collected) >= total_cnt:
                        break
                except ValueError:
                    pass

            page += 1
            self.sleep()

        return list(collected.values())