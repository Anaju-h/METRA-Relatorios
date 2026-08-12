from dataclasses import dataclass
from typing import Optional


@dataclass
class Measurement:
    project_id: int

    responsible: Optional[str] = None
    measurement_datetime: Optional[str] = None

    drawing_reference: Optional[str] = None

    alignment: Optional[str] = None
    fixture: Optional[str] = None

    machine_details: Optional[str] = None
    accessories: Optional[str] = None

    sensors: Optional[str] = None

    special_instructions: Optional[str] = None

    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None