from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentDraft:
    """
    Representa um PDF selecionado antes da criação definitiva
    do projeto.

    Cada arquivo recebe sua própria análise. Portanto, um projeto
    com vários PDFs terá vários DocumentDrafts.
    """

    # =============================================================
    # ARQUIVO
    # =============================================================

    source_path: str

    file_name: str

    # Ordem visual e futura ordem no relatório consolidado.
    document_order: int = 1

    # Identificação da amostra, quando disponível.
    #
    # Exemplos:
    #   Peça 01
    #   Amostra 04
    #   Parte 16
    specimen_identifier: Optional[str] = None

    # =============================================================
    # ANÁLISE
    # =============================================================

    source_type: Optional[str] = None

    part_name: Optional[str] = None

    equipment: Optional[str] = None

    machine_number: Optional[str] = None

    operator: Optional[str] = None

    measurement_datetime: Optional[str] = None

    software_name: Optional[str] = None

    software_version: Optional[str] = None

    measurement_count: Optional[int] = None

    out_of_tolerance_count: Optional[int] = None

    measurement_duration: Optional[str] = None

    suggested_template: Optional[str] = None

    characteristics_count: int = 0

    parsed_report: object | None = None

    # =============================================================
    # STATUS
    # =============================================================

    analysis_status: str = "Pendente"

    analysis_error: Optional[str] = None

    warnings: list[str] = field(
        default_factory=list
    )

    # =============================================================
    # HELPERS
    # =============================================================

    @property
    def analyzed(self) -> bool:
        return (
            self.analysis_status
            == "Concluído"
        )

    @property
    def failed(self) -> bool:
        return (
            self.analysis_status
            == "Falha"
        )

    @property
    def has_parsed_report(self) -> bool:
        return (
            self.parsed_report
            is not None
        )