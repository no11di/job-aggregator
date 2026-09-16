from aggregator import JobAggregator
from models import JobItem
from scrapers.jobkorea import JobKoreaScraper
from scrapers.jumpit import JumpitScraper
from scrapers.remember import RememberScraper
from scrapers.saramin import SaraminScraper
from scrapers.wanted import WantedScraper
from telegram_notifier import TelegramNotifier


def main():
  print("=" * 60)
  print("🚀 QA 채용공고 수집 및 처리 파이프라인 가동")
  print("=" * 60)

  # 캐치 제외 5개 플랫폼
  scrapers = [
      SaraminScraper(),
      JobKoreaScraper(),
      WantedScraper(),
      JumpitScraper(),
      RememberScraper(),
  ]

  all_jobs = []

  for scraper in scrapers:
    print(f"\n[{scraper.platform_name.upper()}] 수집 시작...")
    try:
      jobs = scraper.fetch_jobs()
      print(f" └ 수집 완료: {len(jobs)}건")
      all_jobs.extend(jobs)
    except Exception as e:
      print(f" └ 수집 중 오류: {e}")

  print("\n" + "=" * 60)
  print(f"📦 총 수집된 공고 원본: {len(all_jobs)}건")

  # 중복 제거, 그룹핑, data/jobs.json 저장, 신규 추출
  aggregator = JobAggregator()
  new_jobs, _ = aggregator.process(all_jobs)

  print(f"✨ 신규 등록된 공고: {len(new_jobs)}건")
  print("=" * 60)

  # 텔레그램 알림 발송
  notifier = TelegramNotifier()
  notifier.send_new_jobs(new_jobs)

  print("\n✅ 모든 처리가 완료되었습니다.")


if __name__ == "__main__":
  main()