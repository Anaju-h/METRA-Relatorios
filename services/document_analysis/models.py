from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ================================================================
# ESTRUTURA FÍSICA DO DOCUMENTO
# ================================================================


@dataclass(frozen=True)
class DocumentWord:
    """
    Palavra individual extraída do PDF com posição espacial.

    As coordenadas seguem o sistema utilizado pelo PyMuPDF:
    x cresce da esquerda para a direita;
    y cresce de cima para baixo.
    """

    text: str

    x0: float
    y0: float
    x1: float
    y1: float

    page_number: int

    block_number: Optional[int] = None
    line_number: Optional[int] = None
    word_number: Optional[int] = None

    @property
    def width(self) -> float:
        return max(
            0.0,
            self.x1 - self.x0,
        )

    @property
    def height(self) -> float:
        return max(
            0.0,
            self.y1 - self.y0,
        )

    @property
    def center_x(self) -> float:
        return (
            self.x0
            + self.x1
        ) / 2

    @property
    def center_y(self) -> float:
        return (
            self.y0
            + self.y1
        ) / 2


@dataclass(frozen=True)
class DocumentBlock:
    """
    Bloco de conteúdo identificado pelo mecanismo do PDF.
    """

    text: str

    x0: float
    y0: float
    x1: float
    y1: float

    page_number: int

    block_number: Optional[int] = None

    @property
    def width(self) -> float:
        return max(
            0.0,
            self.x1 - self.x0,
        )

    @property
    def height(self) -> float:
        return max(
            0.0,
            self.y1 - self.y0,
        )

    @property
    def center_x(self) -> float:
        return (
            self.x0
            + self.x1
        ) / 2

    @property
    def center_y(self) -> float:
        return (
            self.y0
            + self.y1
        ) / 2


@dataclass
class DocumentPage:
    """
    Representação completa de uma página do documento.
    """

    number: int

    width: float
    height: float

    text: str

    words: list[DocumentWord] = field(
        default_factory=list
    )

    blocks: list[DocumentBlock] = field(
        default_factory=list
    )


@dataclass
class DocumentContent:
    """
    Documento completo já transformado em estrutura manipulável.

    Nenhuma interpretação semântica acontece aqui.
    """

    source_path: str

    file_name: str

    page_count: int

    pages: list[DocumentPage] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def full_text(self) -> str:
        return "\n".join(
            page.text
            for page in self.pages
        )

    def get_page(
        self,
        page_number: int,
    ) -> Optional[DocumentPage]:
        for page in self.pages:
            if page.number == page_number:
                return page

        return None


# ================================================================
# RESULTADOS EXTRAÍDOS
# ================================================================


@dataclass
class ExtractedField:
    """
    Valor identificado pelo motor documental.

    confidence:
        0.0 = nenhuma confiança
        1.0 = confiança máxima

    method:
        Estratégia responsável pelo resultado.

        Exemplos:
        text
        anchor
        spatial
        block
        table_text
        table_spatial
        merged
    """

    value: Any = None

    confidence: float = 0.0

    method: str = "unknown"

    source_page: Optional[int] = None

    source_text: Optional[str] = None

    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def found(self) -> bool:
        return self.value not in (
            None,
            "",
        )


@dataclass
class ParsedCharacteristic:
    """
    Resultado técnico individual encontrado no documento.

    O nome histórico "Characteristic" é mantido porque já é utilizado
    pelo restante da aplicação, mas o objeto também consegue representar
    resultados de ZEISS INSPECT que não são características dimensionais
    tradicionais.

    CALYPSO, por exemplo:
        name = "DIAMETRO A"
        measured_value = 29.9679
        nominal_value = 29.9713

    ZEISS INSPECT, por exemplo:
        name = "Defeito do volume 1.Vp.147"
        property_name = "Vp"
        deviation = 44.82
    """

    name: str

    # -------------------------------------------------------------
    # CLASSIFICAÇÃO / CONTEXTO
    # -------------------------------------------------------------

    group_name: Optional[str] = None

    datum: Optional[str] = None

    property_name: Optional[str] = None

    # -------------------------------------------------------------
    # VALORES METROLÓGICOS
    # -------------------------------------------------------------

    measured_value: Optional[float] = None

    nominal_value: Optional[float] = None

    upper_tolerance: Optional[float] = None

    lower_tolerance: Optional[float] = None

    deviation: Optional[float] = None

    unit: Optional[str] = None

    # -------------------------------------------------------------
    # RESULTADO / CONFORMIDADE
    # -------------------------------------------------------------

    status: str = "UNKNOWN"

    check_value: Optional[str] = None

    out_value: Optional[str] = None

    # -------------------------------------------------------------
    # RASTREABILIDADE
    # -------------------------------------------------------------

    source_page: Optional[int] = None

    raw_text: Optional[str] = None

    confidence: float = 0.0

    extraction_method: str = "unknown"

    # -------------------------------------------------------------
    # DADOS ESPECÍFICOS DA FONTE
    # -------------------------------------------------------------

    extra_data: dict[str, Any] = field(
        default_factory=dict
    )


# ================================================================
# VALIDAÇÃO
# ================================================================


@dataclass
class ValidationIssue:
    """
    Problema ou alerta identificado após a extração.
    """

    code: str

    message: str

    severity: str = "warning"

    field: Optional[str] = None


@dataclass
class ValidationResult:
    """
    Resultado global da validação do documento.
    """

    is_valid: bool = True

    confidence: float = 1.0

    issues: list[ValidationIssue] = field(
        default_factory=list
    )

    def add_issue(
        self,
        issue: ValidationIssue,
    ) -> None:
        self.issues.append(
            issue
        )

        if issue.severity == "error":
            self.is_valid = False

    @property
    def has_warnings(self) -> bool:
        return any(
            issue.severity == "warning"
            for issue in self.issues
        )

    @property
    def has_errors(self) -> bool:
        return any(
            issue.severity == "error"
            for issue in self.issues
        )


# ================================================================
# RELATÓRIO ANALISADO
# ================================================================


@dataclass
class ParsedReport:
    """
    Resultado padronizado da análise documental.

    Esse objeto deve servir de contrato entre o motor documental
    e o restante da aplicação.

    Ele não depende de CALYPSO, INSPECT, PRISMO, DuraMax,
    Bosello ou qualquer outro equipamento específico.
    """

    source_type: str

    # -------------------------------------------------------------
    # IDENTIFICAÇÃO DO DOCUMENTO / TRABALHO
    # -------------------------------------------------------------

    document_title: Optional[str] = None

    analysis_type: Optional[str] = None

    part_name: Optional[str] = None

    part_number: Optional[str] = None

    # -------------------------------------------------------------
    # EQUIPAMENTO
    # -------------------------------------------------------------

    machine_name: Optional[str] = None

    machine_number: Optional[str] = None

    # -------------------------------------------------------------
    # RESPONSÁVEL / MEDIÇÃO
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

    # -------------------------------------------------------------
    # RESULTADOS
    # -------------------------------------------------------------

    characteristics: list[
        ParsedCharacteristic
    ] = field(
        default_factory=list
    )

    # -------------------------------------------------------------
    # CAMPOS COM PROVENIÊNCIA
    # -------------------------------------------------------------

    fields: dict[
        str,
        ExtractedField,
    ] = field(
        default_factory=dict
    )

    # -------------------------------------------------------------
    # DADOS ESPECÍFICOS DA FONTE
    # -------------------------------------------------------------

    extra_data: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    # -------------------------------------------------------------
    # VALIDAÇÃO
    # -------------------------------------------------------------

    validation: Optional[
        ValidationResult
    ] = None

    warnings: list[str] = field(
        default_factory=list
    )