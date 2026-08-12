from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ReportTemplateDefinition:
    code: str
    name: str
    inspection_type: str
    analysis_mode: str
    description: str
    version: str = "1.0"


DIMENSIONAL_INDIVIDUAL: Final = "DIMENSIONAL_INDIVIDUAL"
DIMENSIONAL_LOTE: Final = "DIMENSIONAL_LOTE"
TOMOGRAFIA_INDUSTRIAL: Final = "TOMOGRAFIA_INDUSTRIAL"
PERSONALIZADO: Final = "PERSONALIZADO"


REPORT_TEMPLATES: Final[
    dict[str, ReportTemplateDefinition]
] = {
    DIMENSIONAL_INDIVIDUAL: ReportTemplateDefinition(
        code=DIMENSIONAL_INDIVIDUAL,
        name="Dimensional individual",
        inspection_type="Inspeção dimensional",
        analysis_mode="Peça única",
        description=(
            "Relatório dimensional para uma única peça, "
            "com características, tolerâncias, resultados, "
            "imagens e conclusão técnica."
        ),
    ),
    DIMENSIONAL_LOTE: ReportTemplateDefinition(
        code=DIMENSIONAL_LOTE,
        name="Dimensional em lote",
        inspection_type="Inspeção dimensional",
        analysis_mode="Lote / estatística",
        description=(
            "Relatório dimensional consolidado para múltiplas "
            "unidades, com estatística, gráficos, conformidade "
            "e resultados por peça."
        ),
    ),
    TOMOGRAFIA_INDUSTRIAL: ReportTemplateDefinition(
        code=TOMOGRAFIA_INDUSTRIAL,
        name="Tomografia industrial",
        inspection_type="Inspeção tomográfica",
        analysis_mode="Análise qualitativa",
        description=(
            "Relatório de inspeção tomográfica industrial, "
            "com método, parâmetros de aquisição, imagens, "
            "resultados qualitativos e limitações."
        ),
    ),
    PERSONALIZADO: ReportTemplateDefinition(
        code=PERSONALIZADO,
        name="Personalizado",
        inspection_type="Outro",
        analysis_mode="Personalizada",
        description=(
            "Modelo flexível para processos que ainda não "
            "possuem um template técnico específico."
        ),
    ),
}


def get_template_definition(
    template_code: str,
) -> ReportTemplateDefinition:
    try:
        return REPORT_TEMPLATES[
            template_code
        ]

    except KeyError as error:
        raise ValueError(
            (
                "Template de relatório inválido: "
                f"{template_code}"
            )
        ) from error


def suggest_template_code(
    *,
    inspection_type: str,
    analysis_mode: str,
    quantity: int,
    equipment: str | None = None,
) -> str:
    inspection = (
        inspection_type
        or ""
    ).strip().lower()

    mode = (
        analysis_mode
        or ""
    ).strip().lower()

    equipment_name = (
        equipment
        or ""
    ).strip().lower()

    if (
        "tomograf" in inspection
        or "bosello" in equipment_name
    ):
        return TOMOGRAFIA_INDUSTRIAL

    if "dimension" in inspection:
        if (
            quantity > 1
            or "lote" in mode
            or "estat" in mode
        ):
            return DIMENSIONAL_LOTE

        return DIMENSIONAL_INDIVIDUAL

    return PERSONALIZADO