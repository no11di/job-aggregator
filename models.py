from dataclasses import dataclass
from typing import Optional

@dataclass
class JobItem:
    platform: str          # saramin, jobkorea, wanted, remember, jumpit, catch
    post_id: str           # 고유 공고 ID
    company_raw: str       # 원본 회사명
    company_clean: str     # 정규화된 회사명 (괄호, 주식회사 등 제거)
    title: str             # 공고 제목
    link: str              # 원본 공고 URL
    deadline: Optional[str] # 마감일 (예: 2026-10-31, 채용시 마감 등)

    def to_dict(self):
        return {
            "platform": self.platform,
            "post_id": self.post_id,
            "company_raw": self.company_raw,
            "company_clean": self.company_clean,
            "title": self.title,
            "link": self.link,
            "deadline": self.deadline
        }