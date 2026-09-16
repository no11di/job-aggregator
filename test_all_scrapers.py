import sys
from scrapers.saramin import SaraminScraper
from scrapers.jobkorea import JobKoreaScraper
from scrapers.wanted import WantedScraper
from scrapers.remember import RememberScraper
from scrapers.jumpit import JumpitScraper
from scrapers.catch import CatchScraper

def test_scrapers():
    # 빠른 테스트를 위해 키워드는 1개만 사용
    test_keywords = ["QA"]

    scrapers = [
       # SaraminScraper(delay=0.5),
        #JobKoreaScraper(delay=0.5),
        WantedScraper(delay=0.5),
        #RememberScraper(delay=0.5),
        #JumpitScraper(delay=0.5),
        #CatchScraper(delay=0.5),
    ]

    print("=" * 60)
    print("🚀 6개 플랫폼 스크래퍼 동작 테스트 시작")
    print("=" * 60)

    results_summary = {}

    for scraper in scrapers:
        name = scraper.platform_name
        print(f"\n[{name}] 수집 테스트 중...")
        try:
            jobs = scraper.fetch_jobs(test_keywords)
            count = len(jobs)
            results_summary[name] = f"✅ 성공 ({count}건)"
            
            if count > 0:
                sample = jobs[0]
                print(f"  └ 샘플: [{sample.company_clean}] {sample.title} ({sample.deadline})")
                print(f"  └ 링크: {sample.link}")
            else:
                print("  └ ⚠️ 수집된 공고 0건 (셀렉터 점검 필요)")
        except Exception as e:
            results_summary[name] = f"❌ 실패 ({e})"
            print(f"  └ 에러 발생: {e}")

    print("\n" + "=" * 60)
    print("📊 최종 테스트 결과 요약")
    print("=" * 60)
    for platform, status in results_summary.items():
        print(f"{platform.ljust(12)} : {status}")
    print("=" * 60)

if __name__ == "__main__":
    test_scrapers()