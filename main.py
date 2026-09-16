import sys
from aggregator import JobAggregator
from scrapers.jobkorea import JobKoreaScraper
from scrapers.jumpit import JumpitScraper
from scrapers.remember import RememberScraper
from scrapers.saramin import SaraminScraper
from scrapers.wanted import WantedScraper
from telegram_notifier import TelegramNotifier


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
  for scraper in scrapers:
        try:
          jobs = scraper.fetch_jobs()
          print(f"[{scraper.platform_name}] 수집 성공: {len(jobs)}건")
          all_jobs.extend(jobs)
        except Exception as e:
          print(f"[{scraper.platform_name}] 오류 발생: {e}")

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
  # pending_jobs가 비어있으면 "추가로 조회된 공고가 없습니다." + 버튼 전송
  notifier.send_new_jobs(pending_jobs)
  print(f"✅ 알림 처리 완료: 전송 공고 수 {len(pending_jobs)}건")


if __name__ == "__main__":
  mode = sys.argv[1] if len(sys.argv) > 1 else "scrape"
  if mode == "notify":
    run_notify()
  else:
    run_scrape()