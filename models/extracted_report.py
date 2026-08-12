from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractedReport:
    """
    Informações estruturadas extraídas de um documento PDF.

    Cada ProjectDocument pode possuir uma única extração.

    Um projeto pode possuir várias extrações porque pode conter
    vários documentos.
    """

    project_id: int

    # Documento ao qual esta extração pertence.
    #
    # Pode permanecer None somente para registros antigos
    # ou projetos criados manualmente.
    document_id: Optional[int] = None

    source_type: str = "UNKNOWN"

    # -------------------------------------------------------------
    # DOCUMENTO / PROCESSO
    # -------------------------------------------------------------

    document_title: Optional[str] = None
    analysis_type: Optional[str] = None

    # -------------------------------------------------------------
    # PEÇA
    # -------------------------------------------------------------

    part_name: Optional[str] = None
    part_number: Optional[str] = None

    # -------------------------------------------------------------
    # EQUIPAMENTO
    # -------------------------------------------------------------

    machine_name: Optional[str] = None
    machine_number: Optional[str] = None

    equipment_origin: Optional[str] = None

    # -------------------------------------------------------------
    # EXECUÇÃO DA MEDIÇÃO
    # -------------------------------------------------------------

    operator: Optional[str] = None
    measurement_datetime: Optional[str] = None

    measurement_count: Optional[int] = None
    out_of_tolerance_count: Optional[int] = None

    measurement_duration: Optional[str] = None

    # -------------------------------------------------------------
    # SOFTWARE
    # -------------------------------------------------------------

    software_name: Optional[str] = None
    software_version: Optional[str] = None

    # -------------------------------------------------------------
    # CONTEXTO TÉCNICO
    # -------------------------------------------------------------

    alignment: Optional[str] = None
    length_unit: Optional[str] = None

    # -------------------------------------------------------------
    # DOCUMENTO
    # -------------------------------------------------------------

    page_count: int = 0

    extraction_confidence: Optional[float] = None

    # JSON com avisos gerados pelo motor documental.
    warnings_json: Optional[str] = None

    # -------------------------------------------------------------
    # REVISÃO
    # -------------------------------------------------------------

    reviewed: bool = False

    # -------------------------------------------------------------
    # CONTROLE
    # -------------------------------------------------------------

    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None