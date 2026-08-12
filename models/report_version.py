from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReportVersion:
    """
    Representa uma emissão oficial de um relatório do METRA.

    Cada registro preserva a versão emitida, o arquivo correspondente
    e os responsáveis registrados no momento da emissão.
    """

    project_id: int
    version: str

    file_path: str
    file_name: str

    status: str = "Emitido"

    created_by: Optional[str] = None
    reviewed_by: Optional[str] = None

    created_at: Optional[str] = None

    id: Optional[int] = None