from dataclasses import dataclass
from typing import Optional


@dataclass
class Characteristic:
    """
    Resultado técnico ou característica metrológica
    identificada no relatório original.

    O modelo suporta tanto relatórios CALYPSO quanto
    resultados do ZEISS INSPECT.
    """

    extraction_id: int

    name: str

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

    # JSON serializado para dados específicos de uma família
    # documental que não justifiquem uma coluna própria.
    extra_data_json: Optional[str] = None

    # -------------------------------------------------------------
    # CONTROLE
    # -------------------------------------------------------------

    id: Optional[int] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None