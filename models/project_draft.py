from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from models.document_draft import DocumentDraft


@dataclass
class ProjectDraft:
    """
    Rascunho geral do processo antes da criação definitiva.

    Ele pode representar:

    - processo manual;
    - processo de peça única;
    - processo em lote.

    Cada PDF permanece armazenado individualmente em documents.
    Os demais campos representam o resumo consolidado.
    """

    # =============================================================
    # MODALIDADE DO PROCESSO
    # =============================================================

    # Valores:
    #
    # manual
    # single_piece
    # batch
    process_type: str = "single_piece"

    documents: list[DocumentDraft] = field(
        default_factory=list
    )

    # =============================================================
    # COMPATIBILIDADE COM O FLUXO ANTIGO
    # =============================================================

    source_path: Optional[str] = None
    source_type: Optional[str] = None

    parsed_report: object | None = None

    # =============================================================
    # IDENTIFICAÇÃO CONSOLIDADA
    # =============================================================

    # Nome-base utilizado no processo.
    #
    # Exemplo de lote:
    # PISTAO DE PRODUTO CARGILL
    base_part_name: Optional[str] = None

    # Mantido por compatibilidade com o restante do sistema.
    # Deve acompanhar base_part_name.
    part_name: Optional[str] = None

    # Nomes completos identificados nos documentos.
    #
    # Exemplo:
    # [
    #   "PISTAO DE PRODUTO CARGILL 5",
    #   "PISTAO DE PRODUTO CARGILL 6",
    #   "PISTAO DE PRODUTO CARGILL 7",
    # ]
    detected_part_names: list[str] = field(
        default_factory=list
    )

    # Identificadores das unidades ou amostras.
    #
    # Exemplo:
    # ["5", "6", "7"]
    specimen_identifiers: list[str] = field(
        default_factory=list
    )

    specimen_count: int = 0

    # =============================================================
    # EQUIPAMENTO E EXECUÇÃO
    # =============================================================

    equipment: Optional[str] = None

    # Todos os equipamentos encontrados.
    equipments: list[str] = field(
        default_factory=list
    )

    machine_number: Optional[str] = None
    operator: Optional[str] = None

    measurement_datetime: Optional[str] = None

    software_name: Optional[str] = None
    software_version: Optional[str] = None

    # =============================================================
    # TOTAIS CONSOLIDADOS
    # =============================================================

    measurement_count: Optional[int] = None

    out_of_tolerance_count: Optional[int] = None

    measurement_duration: Optional[str] = None

    characteristics_count: int = 0

    # =============================================================
    # SUGESTÕES
    # =============================================================

    suggested_template: Optional[str] = None

    suggested_project_name: Optional[str] = None

    # =============================================================
    # AVALIAÇÃO DE COMPATIBILIDADE
    # =============================================================

    # Valores:
    #
    # compatible
    # variation
    # incompatible
    part_compatibility: str = "compatible"

    warnings: list[str] = field(
        default_factory=list
    )

    # =============================================================
    # HELPERS
    # =============================================================

    @property
    def is_batch(self) -> bool:
        return self.process_type == "batch"

    @property
    def is_single_piece(self) -> bool:
        return self.process_type == "single_piece"

    @property
    def is_manual(self) -> bool:
        return self.process_type == "manual"

    # Compatibilidade temporária com código antigo que ainda utiliza
    # os nomes is_package e is_individual.
    @property
    def is_package(self) -> bool:
        return self.is_batch

    @property
    def is_individual(self) -> bool:
        return self.is_single_piece

    @property
    def project_mode(self) -> str:
        """
        Mantém compatibilidade com chamadas antigas.

        package corresponde agora a batch.
        individual corresponde agora a single_piece.
        """

        if self.is_batch:
            return "package"

        if self.is_manual:
            return "manual"

        return "individual"

    @property
    def document_count(self) -> int:
        return len(
            self.documents
        )

    @property
    def analyzed_document_count(self) -> int:
        return sum(
            1
            for document in self.documents
            if document.analyzed
        )

    @property
    def failed_document_count(self) -> int:
        return sum(
            1
            for document in self.documents
            if document.failed
        )

    @property
    def has_documents(self) -> bool:
        return bool(
            self.documents
        )

    def sync_legacy_fields(self) -> None:
        """
        Mantém os campos antigos disponíveis para telas que ainda
        trabalham com apenas um relatório.

        O fluxo novo deve utilizar documents.
        """

        if not self.documents:
            self.source_path = None
            self.source_type = None
            self.parsed_report = None
            return

        first_document = self.documents[0]

        self.source_path = (
            first_document.source_path
        )

        self.source_type = (
            first_document.source_type
        )

        self.parsed_report = (
            first_document.parsed_report
        )

    def get_process_type_label(self) -> str:
        if self.is_batch:
            return "Lote de peças"

        if self.is_manual:
            return "Processo manual"

        return "Peça única"