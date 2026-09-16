import json
import urllib.parse
from typing import Dict, List
from models import JobItem
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper


class CatchScraper(BaseScraper):

  def __init__(self, delay: float = 1.0):
    super().__init__(platform_name="catch", delay=delay)
    self.base_url = "https://www.catch.co.kr"

  def fetch_jobs(self, keywords: List[str] = None) -> List[JobItem]:
    collected: Dict[str, JobItem] = {}

    with sync_playwright() as p:
      browser = p.chromium.launch(
          headless=True,
          args=[
              "--disable-blink-features=AutomationControlled",
              "--no-sandbox",
              "--disable-setuid-sandbox",
              "--disable-dev-shm-usage",
          ],
      )
      context = browser.new_context(
          user_agent=(
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
          ),
          viewport={"width": 1920, "height": 1080},
          locale="ko-KR",
      )

      # 봇 감지 지표 은폐
      context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
            """)

      page = context.new_page()

      # 불필요한 리소스(이미지, 폰트, 미디어) 차단하여 로딩 속도 향상
      def block_unnecessary(route):
        if route.request.resource_type in ["image", "media", "font"]:
          route.abort()
        else:
          route.continue_()

      page.route("**/*", block_unnecessary)

      # API 응답 캡처 리스너
      intercepted_data = []

      def handle_response(response):
        if "getRecruitList" in response.url and response.status == 200:
          try:
            intercepted_data.append(response.json())
          except Exception:
            pass

      page.on("response", handle_response)

      cur_page = 1
      while True:
        prev_count = len(collected)
        intercepted_data.clear()

        sido_encoded = urllib.parse.quote("서울,인천,경기")
        search_page_url = (
            f"{self.base_url}/NCS/RecruitSearch?JobCode=0609&Sido={sido_encoded}"
            f"&Sort=0&curpage={cur_page}&pageSize=50&onRecruitYN=Y"
        )

        try:
          # networkidle 대신 domcontentloaded로 빠른 전환
          page.goto(
              search_page_url, wait_until="domcontentloaded", timeout=15000
          )
          # 비동기 API 응답이 들어올 수 있도록 최대 3초 짧게 대기
          page.wait_for_timeout(3000)
        except Exception as e:
          print(f"[캐치] 페이지 로딩 중단/타임아웃 (page={cur_page}): {e}")
          break

        parsed_via_api = False
        for res_json in intercepted_data:
          items = res_json.get("recruitData", [])
          if not items:
            continue

          parsed_via_api = True
          for item in items:
            post_id = str(item.get("RecruitID"))
            if not post_id or post_id in collected:
              continue

            title = item.get("RecruitTitle", "").strip()
            company_raw = item.get("CompName", "회사명 미제공")
            company_clean = self.clean_company_name(company_raw)
            link = f"{self.base_url}/NCS/RecruitInfoDetails/{post_id}"

            end_code = item.get("ApplyEndCode", "")
            if end_code in ["상시채용", "채용시 마감"]:
              deadline = end_code
            else:
              end_datetime = item.get("ApplyEndDatetime", "")
              deadline = (
                  end_datetime.split("T")[0]
                  if "T" in end_datetime
                  else "상시/채용시 마감"
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

        # API 가로채기가 안 되었을 경우 DOM 카드 파싱
        if not parsed_via_api:
          cards = page.query_selector_all(
              "tbody tr, .recruit_list li, [class*='recruit']"
          )
          for card in cards:
            link_el = card.query_selector("a[href*='RecruitInfoDetails']")
            if not link_el:
              continue

            href = link_el.get_attribute("href") or ""
            post_id = href.split("/")[-1].split("?")[0]
            if not post_id.isdigit() or post_id in collected:
              continue

            title = link_el.inner_text().strip()
            comp_el = card.query_selector(".name, .corp, td:first-child")
            company_raw = comp_el.inner_text().strip() if comp_el else "캐치 공고"
            company_clean = self.clean_company_name(company_raw)
            link = f"{self.base_url}/NCS/RecruitInfoDetails/{post_id}"

            date_el = card.query_selector(".date, .dday, td:last-child")
            deadline = (
                date_el.inner_text().strip() if date_el else "상시/채용시 마감"
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

        if len(collected) == prev_count:
          break

        cur_page += 1
        self.sleep()

        if cur_page > 3:
          break

      browser.close()

    return list(collected.values())