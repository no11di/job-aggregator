import urllib.parse
from playwright.sync_api import sync_playwright

sido_encoded = urllib.parse.quote("서울,인천,경기")
url = f"https://www.catch.co.kr/NCS/RecruitSearch?JobCode=0609&Sido={sido_encoded}&Sort=0&curpage=1&pageSize=50&onRecruitYN=Y"

print(f"[*] 테스트 URL 진입: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="ko-KR"
    )
    page = context.new_page()

    # 네트워크 요청/응답 실시간 로깅
    def on_response(res):
        if "getRecruitList" in res.url:
            print(f"[API 응답 포착!] 상태코드: {res.status}")
            try:
                data = res.json()
                print(f" -> recruitData 건수: {len(data.get('recruitData', []))}")
            except Exception as e:
                print(f" -> JSON 파싱 실패: {e}")

    page.on("response", on_response)

    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(4000)

    # 1. 페이지 제목 및 현재 주소 확인
    print(f"[페이지 타이틀]: {page.title()}")
    print(f"[최종 URL]: {page.url}")

    # 2. 스크린샷 캡처 (어떤 화면이 떴는지 확인용)
    page.screenshot(path="catch_screen.png")
    print("[*] 화면 캡처 저장 완료: catch_screen.png")

    # 3. HTML 파일 저장 (실제 태그 분석용)
    with open("catch_dump.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("[*] HTML 덤프 저장 완료: catch_dump.html")

    # 4. 공고 관련 태그가 DOM에 존재하는지 검사
    links = page.query_selector_all("a[href*='RecruitInfoDetails']")
    print(f"[*] 발견된 공고 링크 수: {len(links)}")

    browser.close()