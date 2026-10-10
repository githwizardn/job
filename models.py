from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Job:
    source: str
    title: str
    url: str
    company: str = ""
    location: str = ""
    posted: str = ""
    deadline: str = ""
    salary: str = ""
    remote: bool = False
    description: str = ""
    geo_status: str = ""  # ფილტრის შედეგი — რატომ დარჩა
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self):
        return asdict(self)