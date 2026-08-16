from dataclasses import dataclass
from typing import Optional


@dataclass
class Characteristic:
    """
    Característica técnica pertencente a um processo METRA.

    Pode ter origem automática, vinculada a uma extração documental,
    ou origem manual, cadastrada diretamente no processo.
    """

    project_id: int
    name: str

    # Origem: EXTRACTED ou MANUAL.
    origin: str = "EXTRACTED"

    # Obrigatório apenas para características extraídas.
    extraction_id: Optional[int] = None

    # -------------------------------------------------------------
    # ORGANIZAÇÃO
    # -------------------------------------------------------------

    group_name: Optional[str] = None

    # -------------------------------------------------------------
    # CAMPOS DO ZEISS INSPECT
    # -------------------------------------------------------------

    datum: Optional[str] = None
    property_name: Optional[str] = None

    # -------------------------------------------------------------
    # VALORES NUMÉRICOS
    # -------------------------------------------------------------

    measured_value: Optional[float] = None
    nominal_value: Optional[float] = None

    upper_tolerance: Optional[float] = None
    lower_tolerance: Optional[float] = None

    deviation: Optional[float] = None
    unit: Optional[str] = None

    # -------------------------------------------------------------
    # RESULTADO
    # -------------------------------------------------------------

    status: str = "UNKNOWN"

    check_value: Optional[str] = None
    out_value: Optional[str] = None

    # -------------------------------------------------------------
    # RASTREABILIDADE DA EXTRAÇÃO
    # -------------------------------------------------------------

    confidence: float = 0.0
    extraction_method: Optional[str] = None

    source_page: Optional[int] = None
    raw_text: Optional[str] = None

    extra_data_json: Optional[str] = None

    # -------------------------------------------------------------
    # CONTROLE
    # -------------------------------------------------------------

    id: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def is_manual(self) -> bool:
        return str(self.origin or "").upper() == "MANUAL"

    @property
    def is_extracted(self) -> bool:
        return not self.is_manual