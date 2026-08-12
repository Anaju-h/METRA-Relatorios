from dataclasses import dataclass
from typing import Optional


@dataclass
class TechnicalControl:
    project_id: int

    prepared_by: Optional[str] = None
    prepared_at: Optional[str] = None

    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None

    status: str = "Em elaboração"

    review_notes: Optional[str] = None

    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None