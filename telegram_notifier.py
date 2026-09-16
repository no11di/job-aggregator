import os
import requests
from typing import List
from models import JobItem

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.dashboard_url = os.getenv("DASHBOARD_URL", "")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def _get_keyboard(self):
        if not self.dashboard_url:
            return None
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "🌐 전체 공고 대시보드 보러가기",
                        "url": self.dashboard_url
                    }
                ]
            ]
        }

    def send_new_jobs(self, new_jobs: List[JobItem]):
        if not self.bot_token or not self.chat_id:
            print("[텔레그램] 토큰이나 챗ID가 설정되지 않아 발송을 건너뜁니다.")
            return

        keyboard = self._get_keyboard()

        # 1. 신규 공고가 없을 때
        if not new_jobs:
            msg = "📢 <b>[QA 채용공고 모니터링]</b>\n\n추가로 조회된 공고가 없습니다."
            payload = {
                "chat_id": self.chat_id,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if keyboard:
                payload["reply_markup"] = keyboard

            try:
                res = requests.post(self.api_url, json=payload, timeout=10)
                res.raise_for_status()
                print("[텔레그램] '추가 공고 없음' 알림 발송 완료.")
            except Exception as e:
                print(f"[텔레그램] 발송 실패: {e}")
            return

        # 2. 신규 공고가 있을 때 (5건씩 분할 발송)
        chunks = [new_jobs[i:i + 5] for i in range(0, len(new_jobs), 5)]
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks, 1):
            lines = [f"🔔 <b>[신규 QA 공고 알림] ({idx}/{total_chunks})</b>\n"]
            for job in chunk:
                lines.append(
                    f"🏢 <b>{job.company_clean}</b> [{job.platform.upper()}]\n"
                    f"📌 <a href=\"{job.link}\">{job.title}</a>\n"
                    f"⏰ 마감일: {job.deadline}\n"
                )
            msg = "\n".join(lines)

            payload = {
                "chat_id": self.chat_id,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }

            # 마지막 메시지 하단에 대시보드 버튼 부착
            if idx == total_chunks and keyboard:
                payload["reply_markup"] = keyboard

            try:
                res = requests.post(self.api_url, json=payload, timeout=10)
                res.raise_for_status()
            except Exception as e:
                print(f"[텔레그램] 발송 실패: {e}")