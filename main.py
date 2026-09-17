import json
import os
import sys
from aggregator import JobAggregator
from models import JobItem
from scrapers.jobkorea import JobKoreaScraper
from scrapers.jumpit import JumpitScraper
from scrapers.remember import RememberScraper
from scrapers.saramin import SaraminScraper
from scrapers.wanted import WantedScraper
from telegram_notifier import TelegramNotifier


def load_existing_wanted_jobs() -> list:
  """기존 jobs.json에서 wanted 공고만 안전하게 복원하여 가져옵니다."""
  jobs_file = "data/jobs.json"
  if not os.path.exists(jobs_file):
    return []

  try:
    with open(jobs_file, "r", encoding="utf-8") as f:
      items = json.load(f)

    if not isinstance(items, list):
      return []

    wanted_jobs = []
    for item in items:
      # dict 타입이 아닌 경우(문자열 등) 건너뛰어 파싱 에러 방지
      if not isinstance(item, dict):
        continue

      if item.get("platform") == "wanted":
        wanted_jobs.append(
            JobItem(
                platform="wanted",
                post_id=str(item.get("post_id", "")),
                company_raw=item.get("company_raw", ""),
                company_clean=item.get("company_clean", ""),
                title=item.get("title", ""),
                link=item.get("link", ""),
                deadline=item.get("deadline", "상시채용"),
            )
        )
    return wanted_jobs
  except Exception as e:
    print(f"[경고] 기존 원티드 데이터 로드 실패: {e}")
    return []


def run_scrape():
  print("=" * 60)
  print("🚀 [09:00 / 21:00] 채용공고 수집 및 대시보드 갱신")
  print("=" * 60)

  scrapers = [
      SaraminScraper(),
      JobKoreaScraper(),
      WantedScraper(),
      JumpitScraper(),
      RememberScraper(),
  ]

  all_jobs = []
  wanted_collected_count = 0

  for scraper in scrapers:
    try:
      jobs = scraper.fetch_jobs()
      print(f"[{scraper.platform_name}] 수집 성공: {len(jobs)}건")
      if scraper.platform_name == "wanted":
        wanted_collected_count = len(jobs)
      all_jobs.extend(jobs)
    except Exception as e:
      print(f"[{scraper.platform_name}] 오류 발생: {e}")

  # 원티드 수집이 0건일 경우 기존 jobs.json 데이터 유지 (Fallback)
  if wanted_collected_count == 0:
    fallback_wanted = load_existing_wanted_jobs()
    if fallback_wanted:
      print(
          f"🛡️ [원티드] 차단/실패 감지: 기존 수집 데이터 {len(fallback_wanted)}건 유지"
      )
      all_jobs.extend(fallback_wanted)

  aggregator = JobAggregator()
  new_jobs, _ = aggregator.process(all_jobs)
  print(f"✅ 수집 완료: 총 {len(all_jobs)}건 (신규 {len(new_jobs)}건 누적 대기)")


def run_notify():
  print("=" * 60)
  print("🔔 [10:00] 텔레그램 일일 알림 발송")
  print("=" * 60)

  aggregator = JobAggregator()
  pending_jobs = aggregator.pop_pending_jobs()

  notifier = TelegramNotifier()
  notifier.send_new_jobs(pending_jobs)
  print(f"✅ 알림 처리 완료: 전송 공고 수 {len(pending_jobs)}건")


if __name__ == "__main__":
  mode = sys.argv[1] if len(sys.argv) > 1 else "scrape"
  if mode == "notify":
    run_notify()
  else:
    run_scrape()