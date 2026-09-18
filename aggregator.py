import json
import os
import re
from typing import Dict, List, Tuple
from models import JobItem

HISTORY_FILE = "data/history.json"
JOBS_FILE = "data/jobs.json"
PENDING_FILE = "data/pending_notifications.json"


def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    
    cleaned = name
    patterns = [
        r"\(주\)", r"\(재\)", r"\(유\)", r"\(사\)",
        r"㈜", r"㈔", r"㈲",
        r"주식회사", r"유한회사", r"재단법인", r"사단법인",
        r"^주\)", r"주\)$", r"^재\)", r"재\)$"
    ]
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r"[ \t\n\r]+", "", cleaned)
    return cleaned.strip()


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

            is_new = unique_key not in self.history
            if is_new:
                new_jobs.append(job)
                self.history[unique_key] = job.deadline

            c_key = normalize_company_name(job.company_clean or job.company_raw)
            if not c_key:
                c_key = "기타"

            if c_key not in company_groups:
                company_groups[c_key] = {
                    "company_name": c_key,
                    "company_raw": job.company_raw,
                    "postings": [],
                }

            company_groups[c_key]["postings"].append({
                "platform": job.platform,
                "post_id": job.post_id,
                "title": job.title,
                "link": job.link,
                "deadline": job.deadline,
                "is_new": is_new,
            })

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

        pending = self._load_json(PENDING_FILE)
        pending_list = pending.get("jobs", [])
        for job in new_jobs:
            pending_list.append(job.__dict__)
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump({"jobs": pending_list}, f, ensure_ascii=False, indent=2)

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
        pending = self._load_json(PENDING_FILE)
        jobs_dict_list = pending.get("jobs", [])

        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump({"jobs": []}, f, ensure_ascii=False, indent=2)

        seen = set()
        result = []
        for d in jobs_dict_list:
            key = f"{d['platform']}_{d['post_id']}"
            if key not in seen:
                seen.add(key)
                result.append(JobItem(**d))
        return result
