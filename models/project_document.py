from dataclasses import dataclass
from typing import Optional


@dataclass
class ProjectDocument:
    """
    Representa um PDF original pertencente a um projeto.

    Um projeto pode possuir:

        - um único documento;
        - vários documentos da mesma peça;
        - documentos complementares.

    Cada documento terá sua própria análise documental.
    """

    project_id: int

    # =============================================================
    # ARQUIVO
    # =============================================================

    file_name: str

    stored_name: str

    file_path: str

    file_size: Optional[int] = None

    file_hash: Optional[str] = None

    # =============================================================
    # ORGANIZAÇÃO
    # =============================================================

    document_order: int = 1

    document_type: str = "Relatório de medição"

    specimen_identifier: Optional[str] = None

    # =============================================================
    # ANÁLISE
    # =============================================================

    source_type: str = "UNKNOWN"

    page_count: int = 0

    analysis_status: str = "Pendente"

    analysis_message: Optional[str] = None

    # =============================================================
    # CONTROLE
    # =============================================================

    is_active: bool = True

    id: Optional[int] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None