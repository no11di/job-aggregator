import re
import time
from abc import ABC, abstractmethod
from typing import List
from models import JobItem

class BaseScraper(ABC):
    def __init__(self, platform_name: str, delay: float = 1.5):
        self.platform_name = platform_name
        self.delay = delay

    def clean_company_name(self, name: str) -> str:
        """(주), 주식회사, (유), 유한회사 등 법인격 표기 및 특수문자 정제"""
        if not name:
            return "미상"
        cleaned = re.sub(r'\(주\)|주식회사|\(유\)|유한회사|\(재\)|재단법인|\(사\)|사단법인', '', name)
        cleaned = re.sub(r'[\(\)\[\]]', '', cleaned)
        return cleaned.strip()

    def sleep(self):
        time.sleep(self.delay)

    @abstractmethod
    def fetch_jobs(self, keywords: List[str]) -> List[JobItem]:
        pass