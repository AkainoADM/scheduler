from pydantic import BaseModel
from typing import List, Optional

class GeneratePayload(BaseModel):
    group_ids: List[int]
    start_date: str  # "DD.MM.YYYY"
    end_date: str
    options: Optional[dict] = None
