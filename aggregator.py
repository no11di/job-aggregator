import json
import os
from typing import Dict, List, Tuple
from models import JobItem

HISTORY_FILE = "data/history.json"
JOBS_FILE = "data/jobs.json"
PENDING_FILE = "data/pending_notifications.json"


class JobAggregator:

  def __init__(self):
    os.makedirs("data", exist_ok=True)
    self.history = self._load_json(HISTORY_FILE)

  def _load_json(self, path: str) -> dict:
    if os.path.exists(path):
      try:
        with open(path, "r", encoding="utf-8") as f:
          return json.load(f)
      except Exception:
        return {}
    return {}

  def process(
      self, scraped_jobs: List[JobItem]
  ) -> Tuple[List[JobItem], List[dict]]:
    new_jobs: List[JobItem] = []
    company_groups: Dict[str, dict] = {}

    for job in scraped_jobs:
      unique_key = f"{job.platform}_{job.post_id}"

      if unique_key not in self.history:
        new_jobs.append(job)
        self.history[unique_key] = job.deadline

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

    # 10시 알림 발송용 대기 큐에 신규 건 누적
    pending = self._load_json(PENDING_FILE)
    pending_list = pending.get("jobs", [])
    for job in new_jobs:
      pending_list.append(job.__dict__)
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
      json.dump({"jobs": pending_list}, f, ensure_ascii=False, indent=2)

    # 웹 대시보드 표시용 데이터 저장
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

  def pop_pending_jobs(self) -> List[JobItem]:
    """10시 알림 발송 시 대기 중인 신규 공고를 꺼내고 비움"""
    pending = self._load_json(PENDING_FILE)
    jobs_dict_list = pending.get("jobs", [])

    # 대기 큐 비우기
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
      json.dump({"jobs": []}, f, ensure_ascii=False, indent=2)

    # 중복 제거 후 JobItem 리스트 복원
    seen = set()
    result = []
    for d in jobs_dict_list:
      key = f"{d['platform']}_{d['post_id']}"
      if key not in seen:
        seen.add(key)
        result.append(JobItem(**d))
    return result