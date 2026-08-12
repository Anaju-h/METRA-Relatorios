from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    report_id: str
    name: str
    template: str
    part_name: str

    inspection_type: str = "Inspeção dimensional"
    analysis_mode: str = "Peça única"
    quantity: int = 1
    technology: Optional[str] = None
    template_version: str = "1.0"

    client: Optional[str] = None
    part_code: Optional[str] = None
    equipment: Optional[str] = None
    description: Optional[str] = None

    status: str = "Em edição"
    version: str = "V1.0"

    id: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None