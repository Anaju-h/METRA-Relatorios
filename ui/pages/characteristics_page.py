from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.project import Project

from services.characteristic_service import (
    CharacteristicService,
)
from ui.components.page_header import PageHeader


class CharacteristicsPage(QWidget):
    """
    Consulta e revisão das características extraídas.

    A tabela pode apresentar:

    - todas as características;
    - somente um documento;
    - somente um grupo;
    - somente um status;
    - resultados encontrados pela busca textual.
    """

    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None

        self.characteristic_service = (
            CharacteristicService()
        )

        self.current_context: dict[
            str,
            Any,
        ] = {}

        self.all_rows: list[
            dict[str, Any]
        ] = []

        self.filtered_rows: list[
            dict[str, Any]
        ] = []

        self.selected_row: (
            dict[str, Any]
            | None
        ) = None

        self.updating_details = False

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()

        scroll_content.setObjectName(
            "pageBackground"
        )

        scroll_layout = QVBoxLayout(
            scroll_content
        )

        scroll_layout.setContentsMargins(
            34,
            22,
            34,
            34,
        )

        scroll_layout.setSpacing(
            0
        )

        content = QWidget()

        content.setObjectName(
            "pageContent"
        )

        content.setMaximumWidth(
            1500
        )

        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            18
        )

        self.page_header = PageHeader(
            title="Características extraídas",
            subtitle=(
                "Consulte, filtre e revise os resultados "
                "metrológicos identificados nos documentos."
            ),
            metadata="-",
            back_text="← Visão geral",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.refresh_button = QPushButton(
            "Atualizar dados"
        )
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.load_context)

        self.page_header.add_action(self.refresh_button)
        content_layout.addWidget(self.page_header)

        # =========================================================
        # RESUMO
        # =========================================================

        summary_layout = QGridLayout()

        summary_layout.setHorizontalSpacing(
            12
        )

        (
            self.total_card,
            self.total_value,
        ) = self.create_summary_card(
            "Características",
            "0",
        )

        (
            self.ok_card,
            self.ok_value,
        ) = self.create_summary_card(
            "Dentro da tolerância",
            "0",
        )

        (
            self.nok_card,
            self.nok_value,
        ) = self.create_summary_card(
            "Fora da tolerância",
            "0",
        )

        (
            self.unknown_card,
            self.unknown_value,
        ) = self.create_summary_card(
            "Não avaliadas",
            "0",
        )

        (
            self.documents_card,
            self.documents_value,
        ) = self.create_summary_card(
            "Documentos",
            "0",
        )

        summary_layout.addWidget(
            self.total_card,
            0,
            0,
        )

        summary_layout.addWidget(
            self.ok_card,
            0,
            1,
        )

        summary_layout.addWidget(
            self.nok_card,
            0,
            2,
        )

        summary_layout.addWidget(
            self.unknown_card,
            0,
            3,
        )

        summary_layout.addWidget(
            self.documents_card,
            0,
            4,
        )

        for column in range(
            5
        ):
            summary_layout.setColumnStretch(
                column,
                1,
            )

        content_layout.addLayout(
            summary_layout
        )

        # =========================================================
        # FILTROS
        # =========================================================

        filters_card = QFrame()

        filters_card.setObjectName(
            "dashboardCard"
        )

        filters_layout = QGridLayout(
            filters_card
        )

        filters_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        filters_layout.setHorizontalSpacing(
            14
        )

        filters_layout.setVerticalSpacing(
            7
        )

        search_label = QLabel(
            "Pesquisar"
        )

        search_label.setObjectName(
            "fieldLabel"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Nome, grupo, datum, propriedade ou documento"
        )

        self.search_input.setMinimumHeight(
            40
        )

        self.search_input.textChanged.connect(
            self.apply_filters
        )

        document_label = QLabel(
            "Documento ou unidade"
        )

        document_label.setObjectName(
            "fieldLabel"
        )

        self.document_filter = QComboBox()

        self.document_filter.setMinimumHeight(
            40
        )

        self.document_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        status_label = QLabel(
            "Status"
        )

        status_label.setObjectName(
            "fieldLabel"
        )

        self.status_filter = QComboBox()

        self.status_filter.addItem(
            "Todos os status",
            "",
        )

        self.status_filter.addItem(
            "Dentro da tolerância",
            "OK",
        )

        self.status_filter.addItem(
            "Fora da tolerância",
            "NOK",
        )

        self.status_filter.addItem(
            "Não avaliadas",
            "UNKNOWN",
        )

        self.status_filter.setMinimumHeight(
            40
        )

        self.status_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        group_label = QLabel(
            "Grupo"
        )

        group_label.setObjectName(
            "fieldLabel"
        )

        self.group_filter = QComboBox()

        self.group_filter.setMinimumHeight(
            40
        )

        self.group_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        clear_filters_button = QPushButton(
            "Limpar filtros"
        )

        clear_filters_button.setObjectName(
            "secondaryButton"
        )

        clear_filters_button.setMinimumHeight(
            40
        )

        clear_filters_button.clicked.connect(
            self.clear_filters
        )

        filters_layout.addWidget(
            search_label,
            0,
            0,
        )

        filters_layout.addWidget(
            document_label,
            0,
            1,
        )

        filters_layout.addWidget(
            status_label,
            0,
            2,
        )

        filters_layout.addWidget(
            group_label,
            0,
            3,
        )

        filters_layout.addWidget(
            self.search_input,
            1,
            0,
        )

        filters_layout.addWidget(
            self.document_filter,
            1,
            1,
        )

        filters_layout.addWidget(
            self.status_filter,
            1,
            2,
        )

        filters_layout.addWidget(
            self.group_filter,
            1,
            3,
        )

        filters_layout.addWidget(
            clear_filters_button,
            1,
            4,
        )

        filters_layout.setColumnStretch(
            0,
            2,
        )

        filters_layout.setColumnStretch(
            1,
            1,
        )

        filters_layout.setColumnStretch(
            2,
            1,
        )

        filters_layout.setColumnStretch(
            3,
            1,
        )

        content_layout.addWidget(
            filters_card
        )

        # =========================================================
        # TABELA + DETALHES
        # =========================================================

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        splitter.setChildrenCollapsible(
            False
        )

        # ---------------------------------------------------------
        # TABELA
        # ---------------------------------------------------------

        table_card = QFrame()

        table_card.setObjectName(
            "dashboardCard"
        )

        table_layout = QVBoxLayout(
            table_card
        )

        table_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        table_layout.setSpacing(
            10
        )

        table_header = QHBoxLayout()

        table_title = QLabel(
            "Resultados"
        )

        table_title.setObjectName(
            "cardTitle"
        )

        self.results_count_label = QLabel(
            "0 resultados"
        )

        self.results_count_label.setObjectName(
            "projectMeta"
        )

        table_header.addWidget(
            table_title
        )

        table_header.addStretch()

        table_header.addWidget(
            self.results_count_label
        )

        table_layout.addLayout(
            table_header
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            11
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Nº",
                "Documento",
                "Característica",
                "Grupo",
                "Nominal",
                "Medido",
                "Tol. inferior",
                "Tol. superior",
                "Desvio",
                "Unidade",
                "Status",
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        self.table.itemSelectionChanged.connect(
            self.update_selected_characteristic
        )

        table_layout.addWidget(
            self.table,
            1,
        )

        # ---------------------------------------------------------
        # DETALHES
        # ---------------------------------------------------------

        details_card = QFrame()

        details_card.setObjectName(
            "dashboardCard"
        )

        details_card.setMinimumWidth(
            340
        )

        details_card.setMaximumWidth(
            430
        )

        details_layout = QVBoxLayout(
            details_card
        )

        details_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        details_layout.setSpacing(
            10
        )

        details_title = QLabel(
            "Detalhes da característica"
        )

        details_title.setObjectName(
            "cardTitle"
        )

        self.details_hint = QLabel(
            "Selecione uma linha da tabela para consultar os detalhes."
        )

        self.details_hint.setObjectName(
            "cardDescription"
        )

        self.details_hint.setWordWrap(
            True
        )

        details_layout.addWidget(
            details_title
        )

        details_layout.addWidget(
            self.details_hint
        )

        self.name_input = self.create_detail_input(
            details_layout,
            "Nome",
        )

        self.group_input = self.create_detail_input(
            details_layout,
            "Grupo",
        )

        self.nominal_input = self.create_detail_input(
            details_layout,
            "Valor nominal",
        )

        self.measured_input = self.create_detail_input(
            details_layout,
            "Valor medido",
        )

        tolerances_layout = QHBoxLayout()

        lower_container = QWidget()

        lower_layout = QVBoxLayout(
            lower_container
        )

        lower_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        lower_label = QLabel(
            "Tol. inferior"
        )

        lower_label.setObjectName(
            "fieldLabel"
        )

        self.lower_input = QLineEdit()

        lower_layout.addWidget(
            lower_label
        )

        lower_layout.addWidget(
            self.lower_input
        )

        upper_container = QWidget()

        upper_layout = QVBoxLayout(
            upper_container
        )

        upper_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        upper_label = QLabel(
            "Tol. superior"
        )

        upper_label.setObjectName(
            "fieldLabel"
        )

        self.upper_input = QLineEdit()

        upper_layout.addWidget(
            upper_label
        )

        upper_layout.addWidget(
            self.upper_input
        )

        tolerances_layout.addWidget(
            lower_container
        )

        tolerances_layout.addWidget(
            upper_container
        )

        details_layout.addLayout(
            tolerances_layout
        )

        self.deviation_input = self.create_detail_input(
            details_layout,
            "Desvio",
        )

        self.unit_input = self.create_detail_input(
            details_layout,
            "Unidade",
        )

        status_detail_label = QLabel(
            "Status"
        )

        status_detail_label.setObjectName(
            "fieldLabel"
        )

        self.status_input = QComboBox()

        self.status_input.addItem(
            "Dentro da tolerância",
            "OK",
        )

        self.status_input.addItem(
            "Fora da tolerância",
            "NOK",
        )

        self.status_input.addItem(
            "Não avaliada",
            "UNKNOWN",
        )

        details_layout.addWidget(
            status_detail_label
        )

        details_layout.addWidget(
            self.status_input
        )

        traceability_title = QLabel(
            "Rastreabilidade"
        )

        traceability_title.setObjectName(
            "fieldLabel"
        )

        self.traceability_value = QLabel(
            "-"
        )

        self.traceability_value.setObjectName(
            "cardDescription"
        )

        self.traceability_value.setWordWrap(
            True
        )

        details_layout.addWidget(
            traceability_title
        )

        details_layout.addWidget(
            self.traceability_value
        )

        raw_text_label = QLabel(
            "Texto original"
        )

        raw_text_label.setObjectName(
            "fieldLabel"
        )

        self.raw_text_input = QTextEdit()

        self.raw_text_input.setReadOnly(
            True
        )

        self.raw_text_input.setMaximumHeight(
            105
        )

        details_layout.addWidget(
            raw_text_label
        )

        details_layout.addWidget(
            self.raw_text_input
        )

        self.save_characteristic_button = QPushButton(
            "Salvar alterações"
        )

        self.save_characteristic_button.setObjectName(
            "primaryButton"
        )

        self.save_characteristic_button.setMinimumHeight(
            42
        )

        self.save_characteristic_button.setEnabled(
            False
        )

        self.save_characteristic_button.clicked.connect(
            self.save_selected_characteristic
        )

        details_layout.addWidget(
            self.save_characteristic_button
        )

        details_layout.addStretch()

        splitter.addWidget(
            table_card
        )

        splitter.addWidget(
            details_card
        )

        splitter.setStretchFactor(
            0,
            1,
        )

        splitter.setStretchFactor(
            1,
            0,
        )

        splitter.setSizes(
            [
                950,
                380,
            ]
        )

        content_layout.addWidget(
            splitter,
            1,
        )

        # =========================================================
        # VAZIO
        # =========================================================

        self.empty_card = QFrame()

        self.empty_card.setObjectName(
            "dashboardCard"
        )

        empty_layout = QVBoxLayout(
            self.empty_card
        )

        empty_layout.setContentsMargins(
            30,
            34,
            30,
            34,
        )

        empty_title = QLabel(
            "Nenhuma característica identificada"
        )

        empty_title.setObjectName(
            "cardTitle"
        )

        empty_description = QLabel(
            (
                "Os documentos deste processo ainda não possuem "
                "resultados técnicos estruturados."
            )
        )

        empty_description.setObjectName(
            "cardDescription"
        )

        empty_description.setWordWrap(
            True
        )

        empty_layout.addWidget(
            empty_title
        )

        empty_layout.addWidget(
            empty_description
        )

        self.empty_card.hide()

        content_layout.addWidget(
            self.empty_card
        )

        # =========================================================
        # CENTRALIZAÇÃO
        # =========================================================

        content_row = QHBoxLayout()

        content_row.addStretch(
            1
        )

        content_row.addWidget(
            content,
            12,
        )

        content_row.addStretch(
            1
        )

        scroll_layout.addLayout(
            content_row
        )

        self.scroll_area.setWidget(
            scroll_content
        )

        root_layout.addWidget(
            self.scroll_area
        )

    # =============================================================
    # COMPONENTES
    # =============================================================

    def create_summary_card(
        self,
        title: str,
        value: str,
    ) -> tuple[
        QFrame,
        QLabel,
    ]:
        card = QFrame()

        card.setObjectName(
            "dashboardCard"
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "dataLabel"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "summaryValue"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        return (
            card,
            value_label,
        )

    def create_detail_input(
        self,
        parent_layout: QVBoxLayout,
        label_text: str,
    ) -> QLineEdit:
        label = QLabel(
            label_text
        )

        label.setObjectName(
            "fieldLabel"
        )

        field = QLineEdit()

        field.setMinimumHeight(
            36
        )

        parent_layout.addWidget(
            label
        )

        parent_layout.addWidget(
            field
        )

        return field

    # =============================================================
    # PROJETO
    # =============================================================

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = project

        self.page_header.set_metadata(
            f"{project.report_id} · {project.name}"
        )

        self.load_context()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # =============================================================
    # CARREGAR
    # =============================================================

    def load_context(
        self,
    ) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        try:
            context = (
                self.characteristic_service
                .get_project_context(
                    self.current_project
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao carregar características",
                str(error),
            )

            return

        self.current_context = context

        self.all_rows = list(
            context.get(
                "rows",
                [],
            )
        )

        self.populate_summary(
            context.get(
                "summary",
                {},
            )
        )

        self.populate_filters(
            context.get(
                "filters",
                {},
            )
        )

        self.apply_filters()

        has_rows = bool(
            self.all_rows
        )

        self.empty_card.setVisible(
            not has_rows
        )

        self.table.parentWidget().setVisible(
            has_rows
        )

    # =============================================================
    # RESUMO
    # =============================================================

    def populate_summary(
        self,
        summary: dict[str, int],
    ) -> None:
        self.total_value.setText(
            str(
                summary.get(
                    "total",
                    0,
                )
            )
        )

        self.ok_value.setText(
            str(
                summary.get(
                    "ok",
                    0,
                )
            )
        )

        self.nok_value.setText(
            str(
                summary.get(
                    "nok",
                    0,
                )
            )
        )

        self.unknown_value.setText(
            str(
                summary.get(
                    "unknown",
                    0,
                )
            )
        )

        self.documents_value.setText(
            str(
                summary.get(
                    "documents",
                    0,
                )
            )
        )

    # =============================================================
    # FILTROS
    # =============================================================

    def populate_filters(
        self,
        filters: dict[str, list[str]],
    ) -> None:
        current_document = (
            self.document_filter
            .currentData()
        )

        current_group = (
            self.group_filter
            .currentData()
        )

        self.document_filter.blockSignals(
            True
        )

        self.group_filter.blockSignals(
            True
        )

        self.document_filter.clear()

        self.document_filter.addItem(
            "Todos os documentos",
            "",
        )

        for document in filters.get(
            "documents",
            [],
        ):
            self.document_filter.addItem(
                document,
                document,
            )

        self.group_filter.clear()

        self.group_filter.addItem(
            "Todos os grupos",
            "",
        )

        for group in filters.get(
            "groups",
            [],
        ):
            self.group_filter.addItem(
                group,
                group,
            )

        self.restore_combo_value(
            self.document_filter,
            current_document,
        )

        self.restore_combo_value(
            self.group_filter,
            current_group,
        )

        self.document_filter.blockSignals(
            False
        )

        self.group_filter.blockSignals(
            False
        )

    def apply_filters(
        self,
    ) -> None:
        search_text = (
            self.search_input
            .text()
            .strip()
            .lower()
        )

        document_value = str(
            self.document_filter
            .currentData()
            or ""
        )

        status_value = str(
            self.status_filter
            .currentData()
            or ""
        )

        group_value = str(
            self.group_filter
            .currentData()
            or ""
        )

        filtered = []

        for row in self.all_rows:
            if (
                document_value
                and row["document_name"]
                != document_value
            ):
                continue

            if (
                status_value
                and row["status"]
                != status_value
            ):
                continue

            if (
                group_value
                and (
                    row["group_name"]
                    or ""
                )
                != group_value
            ):
                continue

            if search_text:
                searchable_values = [
                    row.get(
                        "name"
                    ),
                    row.get(
                        "group_name"
                    ),
                    row.get(
                        "datum"
                    ),
                    row.get(
                        "property_name"
                    ),
                    row.get(
                        "document_name"
                    ),
                    row.get(
                        "specimen_identifier"
                    ),
                ]

                searchable_text = " ".join(
                    str(value)
                    for value in searchable_values
                    if value
                ).lower()

                if (
                    search_text
                    not in searchable_text
                ):
                    continue

            filtered.append(
                row
            )

        self.filtered_rows = filtered

        self.populate_table()

    def clear_filters(
        self,
    ) -> None:
        self.search_input.clear()

        self.document_filter.setCurrentIndex(
            0
        )

        self.status_filter.setCurrentIndex(
            0
        )

        self.group_filter.setCurrentIndex(
            0
        )

        self.apply_filters()

    # =============================================================
    # TABELA
    # =============================================================

    def populate_table(
        self,
    ) -> None:
        self.table.setSortingEnabled(
            False
        )

        self.table.clearContents()

        self.table.setRowCount(
            len(
                self.filtered_rows
            )
        )

        for row_index, row in enumerate(
            self.filtered_rows
        ):
            values = [
                row["sequence"],
                row["document_name"],
                row["name"],
                row["group_name"],
                self.format_number(
                    row["nominal_value"]
                ),
                self.format_number(
                    row["measured_value"]
                ),
                self.format_number(
                    row["lower_tolerance"]
                ),
                self.format_number(
                    row["upper_tolerance"]
                ),
                self.format_number(
                    row["deviation"],
                    show_sign=True,
                ),
                row["unit"],
                row["status_label"],
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(
                        value
                        if value not in {
                            None,
                            "",
                        }
                        else "-"
                    )
                )

                if column_index in {
                    0,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                }:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column_index == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        row,
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.table.setSortingEnabled(
            True
        )

        count = len(
            self.filtered_rows
        )

        self.results_count_label.setText(
            (
                "1 resultado"
                if count == 1
                else f"{count} resultados"
            )
        )

        self.clear_details()

    # =============================================================
    # SELEÇÃO
    # =============================================================

    def update_selected_characteristic(
        self,
    ) -> None:
        selected_items = (
            self.table.selectedItems()
        )

        if not selected_items:
            self.clear_details()

            return

        selected_row_index = (
            selected_items[0]
            .row()
        )

        first_item = self.table.item(
            selected_row_index,
            0,
        )

        if first_item is None:
            self.clear_details()

            return

        row = first_item.data(
            Qt.ItemDataRole.UserRole
        )

        if not isinstance(
            row,
            dict,
        ):
            self.clear_details()

            return

        self.selected_row = row

        self.populate_details(
            row
        )

    def populate_details(
        self,
        row: dict[str, Any],
    ) -> None:
        self.updating_details = True

        try:
            self.details_hint.setText(
                (
                    f"{row['document_name']}"
                    f" · página "
                    f"{row['source_page'] or '-'}"
                )
            )

            self.name_input.setText(
                row["name"]
                or ""
            )

            self.group_input.setText(
                row["group_name"]
                or ""
            )

            self.nominal_input.setText(
                self.format_editable_number(
                    row["nominal_value"]
                )
            )

            self.measured_input.setText(
                self.format_editable_number(
                    row["measured_value"]
                )
            )

            self.lower_input.setText(
                self.format_editable_number(
                    row["lower_tolerance"]
                )
            )

            self.upper_input.setText(
                self.format_editable_number(
                    row["upper_tolerance"]
                )
            )

            self.deviation_input.setText(
                self.format_editable_number(
                    row["deviation"]
                )
            )

            self.unit_input.setText(
                row["unit"]
                or ""
            )

            status_index = (
                self.status_input
                .findData(
                    row["status"]
                )
            )

            if status_index >= 0:
                self.status_input.setCurrentIndex(
                    status_index
                )

            confidence = row.get(
                "confidence"
            )

            confidence_text = (
                (
                    f"{float(confidence) * 100:.0f}%"
                )
                if confidence is not None
                else "-"
            )

            traceability_parts = [
                (
                    f"Documento: "
                    f"{row['document_name']}"
                ),
                (
                    f"Página: "
                    f"{row['source_page'] or '-'}"
                ),
                (
                    f"Origem: "
                    f"{row['source_type'] or '-'}"
                ),
                (
                    f"Confiança: "
                    f"{confidence_text}"
                ),
                (
                    f"Método: "
                    f"{row['extraction_method'] or '-'}"
                ),
            ]

            if row.get(
                "datum"
            ):
                traceability_parts.append(
                    f"Datum: {row['datum']}"
                )

            if row.get(
                "property_name"
            ):
                traceability_parts.append(
                    (
                        "Propriedade: "
                        f"{row['property_name']}"
                    )
                )

            self.traceability_value.setText(
                "\n".join(
                    traceability_parts
                )
            )

            self.raw_text_input.setPlainText(
                row["raw_text"]
                or ""
            )

            self.save_characteristic_button.setEnabled(
                True
            )

        finally:
            self.updating_details = False

    def clear_details(
        self,
    ) -> None:
        self.selected_row = None

        self.details_hint.setText(
            (
                "Selecione uma linha da tabela "
                "para consultar os detalhes."
            )
        )

        for field in [
            self.name_input,
            self.group_input,
            self.nominal_input,
            self.measured_input,
            self.lower_input,
            self.upper_input,
            self.deviation_input,
            self.unit_input,
        ]:
            field.clear()

        self.status_input.setCurrentIndex(
            2
        )

        self.traceability_value.setText(
            "-"
        )

        self.raw_text_input.clear()

        self.save_characteristic_button.setEnabled(
            False
        )

    # =============================================================
    # SALVAR
    # =============================================================

    def save_selected_characteristic(
        self,
    ) -> None:
        if self.selected_row is None:
            return

        characteristic = (
            self.selected_row.get(
                "characteristic"
            )
        )

        if characteristic is None:
            return

        data = {
            "name":
                self.name_input.text(),

            "group_name":
                self.group_input.text(),

            "nominal_value":
                self.nominal_input.text(),

            "measured_value":
                self.measured_input.text(),

            "lower_tolerance":
                self.lower_input.text(),

            "upper_tolerance":
                self.upper_input.text(),

            "deviation":
                self.deviation_input.text(),

            "unit":
                self.unit_input.text(),

            "status":
                self.status_input.currentData(),
        }

        try:
            self.characteristic_service.update_characteristic(
                characteristic=characteristic,
                data=data,
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Dados inválidos",
                str(error),
            )

            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar característica",
                str(error),
            )

            return

        QMessageBox.information(
            self,
            "Característica atualizada",
            (
                "As alterações foram salvas "
                "com sucesso."
            ),
        )

        self.load_context()

    # =============================================================
    # FORMATAÇÃO
    # =============================================================

    def format_number(
        self,
        value,
        show_sign: bool = False,
    ) -> str:
        if value is None:
            return "-"

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return str(
                value
            )

        if show_sign:
            return f"{number:+.4f}"

        return f"{number:.4f}"

    def format_editable_number(
        self,
        value,
    ) -> str:
        if value is None:
            return ""

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return str(
                value
            )

        return f"{number:g}"

    def restore_combo_value(
        self,
        combo: QComboBox,
        value,
    ) -> None:
        if value in {
            None,
            "",
        }:
            combo.setCurrentIndex(
                0
            )

            return

        index = combo.findData(
            value
        )

        if index >= 0:
            combo.setCurrentIndex(
                index
            )