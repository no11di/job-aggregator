import json
import os
from typing import Dict, List, Tuple
from models import JobItem

HISTORY_FILE = "data/history.json"
JOBS_FILE = "data/jobs.json"


class JobAggregator:

  def __init__(self):
    os.makedirs("data", exist_ok=True)
    self.history = self._load_history()

  def _load_history(self) -> Dict[str, str]:
    """이전에 수집된 { '플랫폼_공고ID': '등록일시' } 기록 로드"""
    if os.path.exists(HISTORY_FILE):
      try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
          return json.load(f)
      except Exception:
        return {}
    return {}

  def process(
      self, scraped_jobs: List[JobItem]
  ) -> Tuple[List[JobItem], List[dict]]:
    """1.

    신규 공고 식별
    2. 히스토리 갱신
    3. web/index.html이 사용할 회사별 그룹핑 데이터 생성
    """
    new_jobs: List[JobItem] = []
    company_groups: Dict[str, dict] = {}

    for job in scraped_jobs:
      unique_key = f"{job.platform}_{job.post_id}"

      # 1) 신규 공고 여부 체크
      if unique_key not in self.history:
        new_jobs.append(job)
        self.history[unique_key] = job.deadline

      # 2) web/index.html 표시용 회사별 그룹핑
      c_name = job.company_clean
      if c_name not in company_groups:
        company_groups[c_name] = {
            "company_name": c_name,
            "company_raw": job.company_raw,
            "postings": [],
        }

      company_groups[c_name]["postings"].append({
          "platform": job.platform,
          "post_id": job.post_id,
          "title": job.title,
          "link": job.link,
          "deadline": job.deadline,
          "is_new": unique_key not in self.history or job in new_jobs,
      })

    # 히스토리 저장
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
      json.dump(self.history, f, ensure_ascii=False, indent=2)

    # 웹 표시용 data/jobs.json 저장
    grouped_list = list(company_groups.values())
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
      json.dump(
          {
              "total_companies": len(grouped_list),
              "total_jobs": len(scraped_jobs),
              "data": grouped_list,
          },
          f,
          ensure_ascii=False,
          indent=2,
      )

    return new_jobs, grouped_list