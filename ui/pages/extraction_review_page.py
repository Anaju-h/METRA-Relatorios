from __future__ import annotations

import json

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.characteristic import (
    Characteristic,
)
from models.extracted_report import (
    ExtractedReport,
)
from models.project import Project

from services.pdf_service import (
    PDFService,
)
from services.report_extraction_service import (
    ReportExtractionService,
)
from ui.components.metric_card import MetricCard
from ui.components.page_header import PageHeader
from ui.components.section_header import SectionHeader


class ExtractionReviewPage(QWidget):
    """
    Tela de revisão da extração de um documento específico.

    Fluxo:

        Central de documentos
            ↓
        Visualizador do PDF
            ↓
        Revisão da extração do documento selecionado
    """

    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None

        self.current_document = None
        self.current_document_id: int | None = None

        self.service = (
            ReportExtractionService()
        )

        self.pdf_service = (
            PDFService()
        )

        self.current_extraction: (
            ExtractedReport
            | None
        ) = None

        self.current_characteristics: list[
            Characteristic
        ] = []

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setObjectName("pageBackground")

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(34, 22, 34, 34)
        scroll_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName("pageContent")
        content.setMaximumWidth(1400)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        # ---------------------------------------------------------
        # CABEÇALHO
        # ---------------------------------------------------------

        self.page_header = PageHeader(
            title="Revisão da extração",
            subtitle=(
                "Confira e ajuste os dados identificados "
                "automaticamente antes de utilizá-los no processo."
            ),
            metadata="-",
            back_text="← Documento",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        content_layout.addWidget(self.page_header)

        self.document_label = QLabel("-")
        self.document_label.setObjectName("documentReviewTitle")
        self.document_label.setWordWrap(True)

        content_layout.addWidget(self.document_label)

        # ---------------------------------------------------------
        # MÉTRICAS
        # ---------------------------------------------------------

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        self.review_status_group = MetricCard(
            label="Revisão",
            value="-",
            helper_text="Status dos dados",
            accent="blue",
        )

        self.confidence_group = MetricCard(
            label="Confiança",
            value="-",
            helper_text="Qualidade da extração",
            accent="navy",
        )

        self.characteristic_summary_group = MetricCard(
            label="Características",
            value="0",
            helper_text="Resultados identificados",
            accent="orange",
        )

        metrics_layout.addWidget(self.review_status_group)
        metrics_layout.addWidget(self.confidence_group)
        metrics_layout.addWidget(
            self.characteristic_summary_group
        )

        content_layout.addLayout(metrics_layout)

        # ---------------------------------------------------------
        # AVISOS
        # ---------------------------------------------------------

        self.warning_card = QFrame()
        self.warning_card.setObjectName("analysisWarning")

        warning_layout = QVBoxLayout(self.warning_card)
        warning_layout.setContentsMargins(14, 11, 14, 11)
        warning_layout.setSpacing(4)

        warning_title = QLabel("Pontos para revisão")
        warning_title.setObjectName("cardTitle")

        self.warning_label = QLabel("")
        self.warning_label.setObjectName("cardDescription")
        self.warning_label.setWordWrap(True)

        warning_layout.addWidget(warning_title)
        warning_layout.addWidget(self.warning_label)

        self.warning_card.hide()
        content_layout.addWidget(self.warning_card)

        # ---------------------------------------------------------
        # INFORMAÇÕES DO DOCUMENTO
        # ---------------------------------------------------------

        summary_card = QFrame()
        summary_card.setObjectName("formCard")

        summary_card_layout = QVBoxLayout(summary_card)
        summary_card_layout.setContentsMargins(20, 17, 20, 17)
        summary_card_layout.setSpacing(14)

        summary_header = SectionHeader(
            title="Informações do documento",
            description=(
                "Os campos permanecem editáveis. A origem "
                "documental é exibida somente para consulta."
            ),
        )

        summary_card_layout.addWidget(summary_header)

        summary_layout = QGridLayout()
        summary_layout.setHorizontalSpacing(22)
        summary_layout.setVerticalSpacing(8)

        self.source_input = self.create_field(read_only=True)
        self.part_name_input = self.create_field()
        self.machine_name_input = self.create_field()
        self.machine_number_input = self.create_field()
        self.operator_input = self.create_field()
        self.part_number_input = self.create_field()
        self.datetime_input = self.create_field()
        self.measurement_count_input = self.create_field()
        self.out_count_input = self.create_field()
        self.duration_input = self.create_field()
        self.software_input = self.create_field()
        self.version_input = self.create_field()

        fields = [
            ("Origem documental", self.source_input),
            ("Peça", self.part_name_input),
            ("Máquina", self.machine_name_input),
            (
                "Identificação da máquina",
                self.machine_number_input,
            ),
            ("Operador", self.operator_input),
            ("Número da peça", self.part_number_input),
            ("Data e hora", self.datetime_input),
            ("Número de medições", self.measurement_count_input),
            ("Fora da tolerância", self.out_count_input),
            ("Duração", self.duration_input),
            ("Software", self.software_input),
            ("Versão", self.version_input),
        ]

        for index, (label_text, field) in enumerate(fields):
            row = (index // 3) * 2
            column = index % 3

            label = QLabel(label_text)
            label.setObjectName("dataLabel")

            summary_layout.addWidget(label, row, column)
            summary_layout.addWidget(field, row + 1, column)

        for column in range(3):
            summary_layout.setColumnStretch(column, 1)

        summary_card_layout.addLayout(summary_layout)
        content_layout.addWidget(summary_card)

        # ---------------------------------------------------------
        # CARACTERÍSTICAS
        # ---------------------------------------------------------

        characteristics_card = QFrame()
        characteristics_card.setObjectName("formCard")

        characteristics_layout = QVBoxLayout(
            characteristics_card
        )
        characteristics_layout.setContentsMargins(
            16, 15, 16, 16
        )
        characteristics_layout.setSpacing(10)

        table_header = SectionHeader(
            title="Características identificadas",
            description="0 características identificadas",
        )

        self.characteristics_count = (
            table_header.description_label
        )

        characteristics_layout.addWidget(table_header)

        self.table = QTableWidget()
        self.table.setObjectName("extractionTable")
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "Grupo",
                "Característica",
                "Medido",
                "Nominal",
                "+Tol",
                "-Tol",
                "Desvio",
                "Unidade",
                "Status",
                "Página",
            ]
        )

        self.table.setMinimumHeight(320)
        self.table.setMaximumHeight(520)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        header.setStretchLastSection(True)

        column_widths = [
            120,
            230,
            105,
            105,
            85,
            85,
            95,
            85,
            105,
            65,
        ]

        for index, width in enumerate(column_widths):
            self.table.setColumnWidth(index, width)

        characteristics_layout.addWidget(self.table)
        content_layout.addWidget(characteristics_card)

        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()

        self.reanalyze_button = QPushButton(
            "Analisar novamente"
        )
        self.reanalyze_button.setObjectName("secondaryButton")
        self.reanalyze_button.setMinimumHeight(42)
        self.reanalyze_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.reanalyze_button.clicked.connect(
            self.reanalyze
        )

        self.save_button = QPushButton(
            "Aprovar dados revisados"
        )
        self.save_button.setObjectName("primaryButton")
        self.save_button.setMinimumHeight(42)
        self.save_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.save_button.clicked.connect(
            self.save_review
        )

        actions.addWidget(self.reanalyze_button)
        actions.addWidget(self.save_button)

        content_layout.addLayout(actions)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(content, 12)
        row.addStretch(1)

        scroll_layout.addLayout(row)
        scroll_layout.addSpacing(16)

        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area)

    # =============================================================
    # COMPONENTES AUXILIARES
    # =============================================================

    def create_field(
        self,
        read_only: bool = False,
    ) -> QLineEdit:
        field = QLineEdit()

        field.setMinimumHeight(
            40
        )

        field.setReadOnly(
            read_only
        )

        return field

    # =============================================================
    # DEFINIR DOCUMENTO
    # =============================================================

    def set_document(
        self,
        project: Project,
        document_id: int,
    ) -> None:
        self.current_project = project

        self.current_document_id = (
            document_id
        )

        self.current_document = (
            self.pdf_service
            .document_service
            .get_document(
                document_id
            )
        )

        if self.current_document is None:
            raise FileNotFoundError(
                "O documento selecionado não foi encontrado."
            )

        self.page_header.set_metadata(
            f"{project.report_id} · {project.name}"
        )

        self.document_label.setText(
            self.current_document.file_name
            or self.current_document.stored_name
            or "Documento PDF"
        )

        self.load_data()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # =============================================================
    # CARREGAR DADOS
    # =============================================================

    def load_data(
        self,
    ) -> None:
        if self.current_document_id is None:
            return

        try:
            extraction, characteristics = (
                self.service
                .get_document_extraction(
                    self.current_document_id
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao carregar extração",
                str(error),
            )

            return

        if extraction is None:
            self.reanalyze()

            return

        self.current_extraction = (
            extraction
        )

        self.current_characteristics = (
            characteristics
        )

        self.populate_header(
            extraction
        )

        self.populate_table(
            characteristics
        )

        self.populate_status(
            extraction=extraction,
            characteristics=characteristics,
        )

        self.populate_warnings(
            extraction
        )

    # =============================================================
    # REANALISAR DOCUMENTO
    # =============================================================

    def reanalyze(
        self,
    ) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
            or self.current_document_id is None
        ):
            return

        self.reanalyze_button.setEnabled(
            False
        )

        self.reanalyze_button.setText(
            "Analisando..."
        )

        try:
            (
                extraction,
                characteristics,
            ) = self.service.analyze_document(
                project_id=(
                    self.current_project.id
                ),
                document_id=(
                    self.current_document_id
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro na análise",
                (
                    "Não foi possível analisar este documento.\n\n"
                    f"Detalhes: {error}"
                ),
            )

            return

        finally:
            self.reanalyze_button.setEnabled(
                True
            )

            self.reanalyze_button.setText(
                "Analisar novamente"
            )

        self.current_extraction = (
            extraction
        )

        self.current_characteristics = (
            characteristics
        )

        self.populate_header(
            extraction
        )

        self.populate_table(
            characteristics
        )

        self.populate_status(
            extraction=extraction,
            characteristics=characteristics,
        )

        self.populate_warnings(
            extraction
        )

    # =============================================================
    # CABEÇALHO
    # =============================================================

    def populate_header(
        self,
        extraction: ExtractedReport,
    ) -> None:
        mapping = [
            (
                self.source_input,
                extraction.source_type,
            ),
            (
                self.part_name_input,
                extraction.part_name,
            ),
            (
                self.machine_name_input,
                extraction.machine_name,
            ),
            (
                self.machine_number_input,
                extraction.machine_number,
            ),
            (
                self.operator_input,
                extraction.operator,
            ),
            (
                self.part_number_input,
                extraction.part_number,
            ),
            (
                self.datetime_input,
                extraction.measurement_datetime,
            ),
            (
                self.measurement_count_input,
                extraction.measurement_count,
            ),
            (
                self.out_count_input,
                extraction.out_of_tolerance_count,
            ),
            (
                self.duration_input,
                extraction.measurement_duration,
            ),
            (
                self.software_input,
                extraction.software_name,
            ),
            (
                self.version_input,
                extraction.software_version,
            ),
        ]

        for field, value in mapping:
            field.setText(
                ""
                if value is None
                else str(value)
            )

    # =============================================================
    # STATUS E AVISOS
    # =============================================================

    def populate_status(
        self,
        extraction: ExtractedReport,
        characteristics: list[
            Characteristic
        ],
    ) -> None:
        review_text = (
            "Revisado"
            if extraction.reviewed
            else "Aguardando revisão"
        )

        self.review_status_group.set_value(
            review_text
        )

        confidence = (
            extraction.extraction_confidence
        )

        if confidence is None:
            confidence_text = (
                "Não informada"
            )

        else:
            confidence_text = (
                f"{confidence * 100:.0f}%"
            )

        self.confidence_group.set_value(
            confidence_text
        )

        self.characteristic_summary_group.set_value(
            str(len(characteristics))
        )

    def populate_warnings(
        self,
        extraction: ExtractedReport,
    ) -> None:
        warnings = []

        warnings_json = (
            extraction.warnings_json
        )

        if warnings_json:
            try:
                loaded = json.loads(
                    warnings_json
                )

                if isinstance(
                    loaded,
                    list,
                ):
                    warnings = [
                        str(item)
                        for item in loaded
                        if item
                    ]

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                warnings = [
                    str(
                        warnings_json
                    )
                ]

        if warnings:
            self.warning_label.setText(
                "\n".join(
                    f"• {warning}"
                    for warning in warnings
                )
            )

            self.warning_card.show()

        else:
            self.warning_label.clear()

            self.warning_card.hide()

    # =============================================================
    # TABELA
    # =============================================================

    def populate_table(
        self,
        characteristics: list[
            Characteristic
        ],
    ) -> None:
        self.table.clearContents()

        self.table.setRowCount(
            len(characteristics)
        )

        count = len(
            characteristics
        )

        self.characteristics_count.setText(
            (
                f"{count} característica identificada"
                if count == 1
                else (
                    f"{count} características "
                    "identificadas"
                )
            )
        )

        for row, characteristic in enumerate(
            characteristics
        ):
            values = [
                characteristic.group_name,
                characteristic.name,
                characteristic.measured_value,
                characteristic.nominal_value,
                characteristic.upper_tolerance,
                characteristic.lower_tolerance,
                characteristic.deviation,
                characteristic.unit,
                characteristic.status,
                characteristic.source_page,
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    self.format_value(
                        value
                    )
                )

                # A página de origem não é editável.
                if column == 9:
                    item.setFlags(
                        item.flags()
                        & ~Qt.ItemFlag.ItemIsEditable
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        visible_rows = min(
            max(
                count,
                3,
            ),
            10,
        )

        calculated_height = (
            42
            + visible_rows * 36
            + 4
        )

        self.table.setMinimumHeight(
            calculated_height
        )

        self.table.setMaximumHeight(
            440
        )

    # =============================================================
    # SALVAR REVISÃO
    # =============================================================

    def save_review(
        self,
    ) -> None:
        if self.current_extraction is None:
            return

        extraction = (
            self.current_extraction
        )

        # source_type permanece igual ao valor extraído.
        # O campo é somente leitura.
        extraction.source_type = (
            self.source_input.text().strip()
            or "UNKNOWN"
        )

        extraction.part_name = (
            self.part_name_input.text().strip()
            or None
        )

        extraction.machine_name = (
            self.machine_name_input.text().strip()
            or None
        )

        extraction.machine_number = (
            self.machine_number_input.text().strip()
            or None
        )

        extraction.operator = (
            self.operator_input.text().strip()
            or None
        )

        extraction.part_number = (
            self.part_number_input.text().strip()
            or None
        )

        extraction.measurement_datetime = (
            self.datetime_input.text().strip()
            or None
        )

        extraction.measurement_count = (
            self.parse_int(
                self.measurement_count_input.text()
            )
        )

        extraction.out_of_tolerance_count = (
            self.parse_int(
                self.out_count_input.text()
            )
        )

        extraction.measurement_duration = (
            self.duration_input.text().strip()
            or None
        )

        extraction.software_name = (
            self.software_input.text().strip()
            or None
        )

        extraction.software_version = (
            self.version_input.text().strip()
            or None
        )

        self.read_table_back()

        try:
            self.service.save_review(
                extraction,
                self.current_characteristics,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar revisão",
                str(error),
            )

            return

        self.current_extraction = (
            extraction
        )

        self.populate_status(
            extraction=extraction,
            characteristics=(
                self.current_characteristics
            ),
        )

        QMessageBox.information(
            self,
            "Revisão salva",
            (
                "Os dados revisados deste documento "
                "foram salvos com sucesso."
            ),
        )

    # =============================================================
    # LER DADOS DA TABELA
    # =============================================================

    def read_table_back(
        self,
    ) -> None:
        for row, characteristic in enumerate(
            self.current_characteristics
        ):
            characteristic.group_name = (
                self.get_cell(
                    row,
                    0,
                )
                or None
            )

            characteristic.name = (
                self.get_cell(
                    row,
                    1,
                )
                or characteristic.name
            )

            characteristic.measured_value = (
                self.parse_float(
                    self.get_cell(
                        row,
                        2,
                    )
                )
            )

            characteristic.nominal_value = (
                self.parse_float(
                    self.get_cell(
                        row,
                        3,
                    )
                )
            )

            characteristic.upper_tolerance = (
                self.parse_float(
                    self.get_cell(
                        row,
                        4,
                    )
                )
            )

            characteristic.lower_tolerance = (
                self.parse_float(
                    self.get_cell(
                        row,
                        5,
                    )
                )
            )

            characteristic.deviation = (
                self.parse_float(
                    self.get_cell(
                        row,
                        6,
                    )
                )
            )

            characteristic.unit = (
                self.get_cell(
                    row,
                    7,
                )
                or None
            )

            characteristic.status = (
                self.get_cell(
                    row,
                    8,
                )
                or "UNKNOWN"
            )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

    def get_cell(
        self,
        row: int,
        column: int,
    ) -> str:
        item = self.table.item(
            row,
            column,
        )

        if item is None:
            return ""

        return (
            item.text()
            .strip()
        )

    def format_value(
        self,
        value,
    ) -> str:
        if value is None:
            return ""

        if isinstance(
            value,
            float,
        ):
            return (
                f"{value:.6f}"
                .rstrip("0")
                .rstrip(".")
            )

        return str(
            value
        )

    def parse_float(
        self,
        value: str,
    ) -> float | None:
        value = (
            value.strip()
        )

        if not value:
            return None

        try:
            return float(
                value.replace(
                    ",",
                    ".",
                )
            )

        except ValueError:
            return None

    def parse_int(
        self,
        value: str,
    ) -> int | None:
        value = (
            value.strip()
        )

        if not value:
            return None

        try:
            return int(
                value
            )

        except ValueError:
            return None