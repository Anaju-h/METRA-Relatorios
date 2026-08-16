from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
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
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.characteristic_service import CharacteristicService
from ui.components.page_header import PageHeader


class CharacteristicsPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None
        self.characteristic_service = CharacteristicService()

        self.current_context: dict[str, Any] = {}
        self.all_rows: list[dict[str, Any]] = []
        self.filtered_rows: list[dict[str, Any]] = []

        self.selected_row: dict[str, Any] | None = None
        self.form_mode = "none"

        self.build_ui()

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
        content.setMaximumWidth(1500)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        self.page_header = PageHeader(
            title="Características",
            subtitle=(
                "Gerencie os resultados técnicos do processo, "
                "sejam eles extraídos dos documentos ou cadastrados manualmente."
            ),
            metadata="-",
            back_text="← Visão geral",
        )
        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.refresh_button = QPushButton("Atualizar dados")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.load_context)

        self.new_button = QPushButton("+ Nova característica")
        self.new_button.setObjectName("primaryButton")
        self.new_button.setMinimumHeight(40)
        self.new_button.clicked.connect(
            self.start_new_characteristic
        )

        self.page_header.add_action(self.refresh_button)
        self.page_header.add_action(self.new_button)
        content_layout.addWidget(self.page_header)

        summary_layout = QGridLayout()
        summary_layout.setHorizontalSpacing(12)

        self.total_card, self.total_value = self.create_summary_card(
            "Características",
            "0",
        )
        self.ok_card, self.ok_value = self.create_summary_card(
            "Dentro da tolerância",
            "0",
        )
        self.nok_card, self.nok_value = self.create_summary_card(
            "Fora da tolerância",
            "0",
        )
        self.unknown_card, self.unknown_value = self.create_summary_card(
            "Não avaliadas",
            "0",
        )
        self.manual_card, self.manual_value = self.create_summary_card(
            "Manuais",
            "0",
        )

        cards = [
            self.total_card,
            self.ok_card,
            self.nok_card,
            self.unknown_card,
            self.manual_card,
        ]

        for column, card in enumerate(cards):
            summary_layout.addWidget(card, 0, column)
            summary_layout.setColumnStretch(column, 1)

        content_layout.addLayout(summary_layout)

        # =========================================================
        # FILTROS
        # =========================================================

        filters_card = QFrame()
        filters_card.setObjectName("dashboardCard")

        filters_layout = QGridLayout(filters_card)
        filters_layout.setContentsMargins(20, 18, 20, 18)
        filters_layout.setHorizontalSpacing(12)
        filters_layout.setVerticalSpacing(7)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Nome, grupo, documento ou propriedade"
        )
        self.search_input.setMinimumHeight(40)
        self.search_input.textChanged.connect(self.apply_filters)

        self.document_filter = QComboBox()
        self.document_filter.setMinimumHeight(40)
        self.document_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.origin_filter = QComboBox()
        self.origin_filter.setMinimumHeight(40)
        self.origin_filter.addItem("Todas as origens", "")
        self.origin_filter.addItem("Extraídas", "EXTRACTED")
        self.origin_filter.addItem("Manuais", "MANUAL")
        self.origin_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.status_filter = QComboBox()
        self.status_filter.setMinimumHeight(40)
        self.status_filter.addItem("Todos os status", "")
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
        self.status_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.group_filter = QComboBox()
        self.group_filter.setMinimumHeight(40)
        self.group_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        clear_filters_button = QPushButton("Limpar filtros")
        clear_filters_button.setObjectName("secondaryButton")
        clear_filters_button.setMinimumHeight(40)
        clear_filters_button.clicked.connect(self.clear_filters)

        filter_labels = [
            ("Pesquisar", 0),
            ("Documento", 1),
            ("Origem", 2),
            ("Status", 3),
            ("Grupo", 4),
        ]

        for text, column in filter_labels:
            label = QLabel(text)
            label.setObjectName("fieldLabel")
            filters_layout.addWidget(label, 0, column)

        filters_layout.addWidget(self.search_input, 1, 0)
        filters_layout.addWidget(self.document_filter, 1, 1)
        filters_layout.addWidget(self.origin_filter, 1, 2)
        filters_layout.addWidget(self.status_filter, 1, 3)
        filters_layout.addWidget(self.group_filter, 1, 4)
        filters_layout.addWidget(clear_filters_button, 1, 5)

        filters_layout.setColumnStretch(0, 2)

        for column in range(1, 5):
            filters_layout.setColumnStretch(column, 1)

        content_layout.addWidget(filters_card)

        # =========================================================
        # TABELA
        # =========================================================

        self.table_card = QFrame()
        self.table_card.setObjectName("dashboardCard")

        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)

        table_header = QHBoxLayout()

        table_title = QLabel("Resultados")
        table_title.setObjectName("cardTitle")

        self.results_count_label = QLabel("0 resultados")
        self.results_count_label.setObjectName("projectMeta")

        table_header.addWidget(table_title)
        table_header.addStretch()
        table_header.addWidget(self.results_count_label)

        table_layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "Nº",
                "Origem",
                "Documento",
                "Característica",
                "Grupo",
                "Nominal",
                "Medido",
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
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(310)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )

        self.table.itemSelectionChanged.connect(
            self.update_selected_characteristic
        )

        table_layout.addWidget(self.table)
        content_layout.addWidget(self.table_card)

        # =========================================================
        # ESTADO VAZIO
        # =========================================================

        self.empty_card = QFrame()
        self.empty_card.setObjectName("dashboardCard")

        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setContentsMargins(30, 30, 30, 30)
        empty_layout.setSpacing(10)

        empty_title = QLabel("Nenhuma característica cadastrada")
        empty_title.setObjectName("cardTitle")

        empty_description = QLabel(
            "Este processo ainda não possui características. "
            "Cadastre uma característica manualmente ou adicione "
            "documentos para utilizar a extração automática."
        )
        empty_description.setObjectName("cardDescription")
        empty_description.setWordWrap(True)

        empty_button = QPushButton("+ Adicionar característica")
        empty_button.setObjectName("primaryButton")
        empty_button.setMinimumHeight(42)
        empty_button.clicked.connect(
            self.start_new_characteristic
        )

        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_description)
        empty_layout.addWidget(
            empty_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        self.empty_card.hide()
        content_layout.addWidget(self.empty_card)

        # =========================================================
        # DETALHES EM LARGURA TOTAL
        # =========================================================

        self.details_card = QFrame()
        self.details_card.setObjectName("dashboardCard")

        details_layout = QVBoxLayout(self.details_card)
        details_layout.setContentsMargins(22, 18, 22, 20)
        details_layout.setSpacing(14)

        details_header = QHBoxLayout()

        self.details_title = QLabel("Detalhes da característica")
        self.details_title.setObjectName("cardTitle")

        details_header.addWidget(self.details_title)
        details_header.addStretch()

        self.delete_button = QPushButton("Excluir característica")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setMinimumHeight(38)
        self.delete_button.hide()
        self.delete_button.clicked.connect(
            self.delete_selected_characteristic
        )

        details_header.addWidget(self.delete_button)

        details_layout.addLayout(details_header)

        self.details_hint = QLabel(
            "Selecione uma linha da tabela para editar ou crie uma nova característica."
        )
        self.details_hint.setObjectName("cardDescription")
        self.details_hint.setWordWrap(True)
        details_layout.addWidget(self.details_hint)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(16)
        form_grid.setVerticalSpacing(9)

        self.name_input = self.add_grid_input(
            form_grid,
            row=0,
            column=0,
            label="Nome *",
        )
        self.group_input = self.add_grid_input(
            form_grid,
            row=0,
            column=1,
            label="Grupo",
        )
        self.unit_input = self.add_grid_input(
            form_grid,
            row=0,
            column=2,
            label="Unidade",
        )

        self.nominal_input = self.add_grid_input(
            form_grid,
            row=2,
            column=0,
            label="Valor nominal",
        )
        self.measured_input = self.add_grid_input(
            form_grid,
            row=2,
            column=1,
            label="Valor medido",
        )
        self.deviation_input = self.add_grid_input(
            form_grid,
            row=2,
            column=2,
            label="Desvio",
        )

        self.lower_input = self.add_grid_input(
            form_grid,
            row=4,
            column=0,
            label="Tolerância inferior",
        )
        self.upper_input = self.add_grid_input(
            form_grid,
            row=4,
            column=1,
            label="Tolerância superior",
        )

        status_label = QLabel("Status")
        status_label.setObjectName("fieldLabel")

        self.status_input = QComboBox()
        self.status_input.setMinimumHeight(38)
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

        form_grid.addWidget(status_label, 4, 2)
        form_grid.addWidget(self.status_input, 5, 2)

        for column in range(3):
            form_grid.setColumnStretch(column, 1)

        details_layout.addLayout(form_grid)

        traceability_frame = QFrame()
        traceability_frame.setObjectName("measurementContextCard")

        traceability_layout = QVBoxLayout(traceability_frame)
        traceability_layout.setContentsMargins(16, 12, 16, 12)
        traceability_layout.setSpacing(5)

        traceability_title = QLabel("Origem e rastreabilidade")
        traceability_title.setObjectName("fieldLabel")

        self.traceability_value = QLabel("-")
        self.traceability_value.setObjectName("cardDescription")
        self.traceability_value.setWordWrap(True)

        traceability_layout.addWidget(traceability_title)
        traceability_layout.addWidget(self.traceability_value)

        details_layout.addWidget(traceability_frame)

        self.raw_text_frame = QFrame()

        raw_layout = QVBoxLayout(self.raw_text_frame)
        raw_layout.setContentsMargins(0, 0, 0, 0)
        raw_layout.setSpacing(6)

        raw_text_label = QLabel("Texto original")
        raw_text_label.setObjectName("fieldLabel")

        self.raw_text_input = QTextEdit()
        self.raw_text_input.setReadOnly(True)
        self.raw_text_input.setMaximumHeight(95)

        raw_layout.addWidget(raw_text_label)
        raw_layout.addWidget(self.raw_text_input)

        details_layout.addWidget(self.raw_text_frame)

        actions = QHBoxLayout()
        actions.addStretch()

        self.cancel_edit_button = QPushButton("Cancelar")
        self.cancel_edit_button.setObjectName("secondaryButton")
        self.cancel_edit_button.setMinimumHeight(42)
        self.cancel_edit_button.clicked.connect(self.cancel_editing)

        self.save_characteristic_button = QPushButton(
            "Salvar característica"
        )
        self.save_characteristic_button.setObjectName("primaryButton")
        self.save_characteristic_button.setMinimumHeight(42)
        self.save_characteristic_button.clicked.connect(
            self.save_characteristic
        )

        actions.addWidget(self.cancel_edit_button)
        actions.addWidget(self.save_characteristic_button)

        details_layout.addLayout(actions)
        content_layout.addWidget(self.details_card)

        content_row = QHBoxLayout()
        content_row.addStretch(1)
        content_row.addWidget(content, 12)
        content_row.addStretch(1)

        scroll_layout.addLayout(content_row)
        scroll_layout.addSpacing(16)

        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area)

        self.clear_details()

    # =============================================================
    # COMPONENTES
    # =============================================================

    def create_summary_card(
        self,
        title: str,
        value: str,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("dashboardCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)

        title_label = QLabel(title, card)
        title_label.setObjectName("dataLabel")

        value_label = QLabel(value, card)
        value_label.setObjectName("summaryValue")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card, value_label

    def add_grid_input(
        self,
        layout: QGridLayout,
        *,
        row: int,
        column: int,
        label: str,
    ) -> QLineEdit:
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")

        field = QLineEdit()
        field.setMinimumHeight(38)

        layout.addWidget(label_widget, row, column)
        layout.addWidget(field, row + 1, column)

        return field

    # =============================================================
    # PROJETO / CARREGAMENTO
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

        self.scroll_area.verticalScrollBar().setValue(0)

    def load_context(self) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        try:
            context = self.characteristic_service.get_project_context(
                self.current_project
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
            context.get("rows", [])
        )

        self.populate_summary(
            context.get("summary", {})
        )
        self.populate_filters(
            context.get("filters", {})
        )

        self.apply_filters()

        has_rows = bool(self.all_rows)

        self.table_card.setVisible(has_rows)
        self.empty_card.setVisible(not has_rows)

        if not has_rows:
            self.clear_details()

    # =============================================================
    # RESUMO / FILTROS
    # =============================================================

    def populate_summary(
        self,
        summary: dict[str, int],
    ) -> None:
        self.total_value.setText(
            str(summary.get("total", 0))
        )
        self.ok_value.setText(
            str(summary.get("ok", 0))
        )
        self.nok_value.setText(
            str(summary.get("nok", 0))
        )
        self.unknown_value.setText(
            str(summary.get("unknown", 0))
        )
        self.manual_value.setText(
            str(summary.get("manual", 0))
        )

    def populate_filters(
        self,
        filters: dict[str, list[str]],
    ) -> None:
        current_document = self.document_filter.currentData()
        current_group = self.group_filter.currentData()

        self.document_filter.blockSignals(True)
        self.group_filter.blockSignals(True)

        self.document_filter.clear()
        self.document_filter.addItem(
            "Todos os documentos",
            "",
        )

        for document in filters.get("documents", []):
            self.document_filter.addItem(
                document,
                document,
            )

        self.group_filter.clear()
        self.group_filter.addItem(
            "Todos os grupos",
            "",
        )

        for group in filters.get("groups", []):
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

        self.document_filter.blockSignals(False)
        self.group_filter.blockSignals(False)

    def apply_filters(self) -> None:
        search_text = self.search_input.text().strip().lower()

        document_value = str(
            self.document_filter.currentData() or ""
        )
        origin_value = str(
            self.origin_filter.currentData() or ""
        )
        status_value = str(
            self.status_filter.currentData() or ""
        )
        group_value = str(
            self.group_filter.currentData() or ""
        )

        filtered = []

        for row in self.all_rows:
            if (
                document_value
                and row["document_name"] != document_value
            ):
                continue

            if (
                origin_value
                and row["origin"] != origin_value
            ):
                continue

            if (
                status_value
                and row["status"] != status_value
            ):
                continue

            if (
                group_value
                and (row["group_name"] or "") != group_value
            ):
                continue

            if search_text:
                searchable_values = [
                    row.get("name"),
                    row.get("group_name"),
                    row.get("datum"),
                    row.get("property_name"),
                    row.get("document_name"),
                    row.get("origin_label"),
                ]

                searchable_text = " ".join(
                    str(value)
                    for value in searchable_values
                    if value
                ).lower()

                if search_text not in searchable_text:
                    continue

            filtered.append(row)

        self.filtered_rows = filtered
        self.populate_table()

    def clear_filters(self) -> None:
        self.search_input.clear()
        self.document_filter.setCurrentIndex(0)
        self.origin_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.group_filter.setCurrentIndex(0)
        self.apply_filters()

    # =============================================================
    # TABELA
    # =============================================================

    def populate_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(
            len(self.filtered_rows)
        )

        for row_index, row in enumerate(
            self.filtered_rows
        ):
            values = [
                row["sequence"],
                row["origin_label"],
                (
                    row["document_name"]
                    if row["origin"] == "EXTRACTED"
                    else "-"
                ),
                row["name"],
                row["group_name"],
                self.format_number(
                    row["nominal_value"]
                ),
                self.format_number(
                    row["measured_value"]
                ),
                self.format_number(
                    row["deviation"],
                    show_sign=True,
                ),
                row["unit"],
                row["status_label"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(
                    str(
                        value
                        if value not in {None, ""}
                        else "-"
                    )
                )

                if column_index in {0, 5, 6, 7, 8}:
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

        self.table.setSortingEnabled(True)

        count = len(self.filtered_rows)

        self.results_count_label.setText(
            "1 resultado"
            if count == 1
            else f"{count} resultados"
        )

    # =============================================================
    # EDIÇÃO
    # =============================================================

    def update_selected_characteristic(self) -> None:
        selected_items = self.table.selectedItems()

        if not selected_items:
            return

        row_index = selected_items[0].row()
        first_item = self.table.item(row_index, 0)

        if first_item is None:
            return

        row = first_item.data(
            Qt.ItemDataRole.UserRole
        )

        if not isinstance(row, dict):
            return

        self.selected_row = row
        self.form_mode = "edit"
        self.populate_details(row)

    def start_new_characteristic(self) -> None:
        self.table.clearSelection()

        self.selected_row = None
        self.form_mode = "new"

        self.clear_form_fields()

        self.details_title.setText(
            "Nova característica"
        )
        self.details_hint.setText(
            "Cadastre manualmente um resultado técnico para este processo."
        )

        self.status_input.setCurrentIndex(2)

        self.traceability_value.setText(
            "Origem: Inserção manual\nDocumento: Não se aplica"
        )

        self.raw_text_frame.hide()
        self.delete_button.hide()
        self.save_characteristic_button.setEnabled(True)

        self.scroll_area.ensureWidgetVisible(
            self.details_card
        )

    def populate_details(
        self,
        row: dict[str, Any],
    ) -> None:
        self.details_title.setText(
            "Detalhes da característica"
        )

        self.details_hint.setText(
            f"{row['origin_label']} · {row['document_name']}"
        )

        self.name_input.setText(row["name"] or "")
        self.group_input.setText(row["group_name"] or "")
        self.unit_input.setText(row["unit"] or "")

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
        self.deviation_input.setText(
            self.format_editable_number(
                row["deviation"]
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

        status_index = self.status_input.findData(
            row["status"]
        )

        if status_index >= 0:
            self.status_input.setCurrentIndex(
                status_index
            )

        if row["origin"] == "MANUAL":
            self.traceability_value.setText(
                "Origem: Inserção manual\nDocumento: Não se aplica"
            )
            self.raw_text_input.clear()
            self.raw_text_frame.hide()
            self.delete_button.show()

        else:
            confidence = row.get("confidence")

            confidence_text = (
                f"{float(confidence) * 100:.0f}%"
                if confidence is not None
                else "-"
            )

            parts = [
                f"Documento: {row['document_name']}",
                f"Página: {row['source_page'] or '-'}",
                f"Origem: {row['source_type'] or '-'}",
                f"Confiança: {confidence_text}",
                f"Método: {row['extraction_method'] or '-'}",
            ]

            if row.get("datum"):
                parts.append(
                    f"Datum: {row['datum']}"
                )

            if row.get("property_name"):
                parts.append(
                    f"Propriedade: {row['property_name']}"
                )

            self.traceability_value.setText(
                "\n".join(parts)
            )

            self.raw_text_input.setPlainText(
                row["raw_text"] or ""
            )
            self.raw_text_frame.setVisible(
                bool(row["raw_text"])
            )
            self.delete_button.hide()

        self.save_characteristic_button.setEnabled(True)

    def cancel_editing(self) -> None:
        self.table.clearSelection()
        self.clear_details()

    def clear_details(self) -> None:
        self.selected_row = None
        self.form_mode = "none"

        self.clear_form_fields()

        self.details_title.setText(
            "Detalhes da característica"
        )
        self.details_hint.setText(
            "Selecione uma linha da tabela para editar ou crie uma nova característica."
        )

        self.status_input.setCurrentIndex(2)
        self.traceability_value.setText("-")
        self.raw_text_input.clear()
        self.raw_text_frame.hide()
        self.delete_button.hide()
        self.save_characteristic_button.setEnabled(False)

    def clear_form_fields(self) -> None:
        for field in [
            self.name_input,
            self.group_input,
            self.unit_input,
            self.nominal_input,
            self.measured_input,
            self.deviation_input,
            self.lower_input,
            self.upper_input,
        ]:
            field.clear()

    # =============================================================
    # SALVAR / EXCLUIR
    # =============================================================

    def save_characteristic(self) -> None:
        if self.current_project is None:
            return

        data = {
            "name": self.name_input.text(),
            "group_name": self.group_input.text(),
            "unit": self.unit_input.text(),
            "nominal_value": self.nominal_input.text(),
            "measured_value": self.measured_input.text(),
            "deviation": self.deviation_input.text(),
            "lower_tolerance": self.lower_input.text(),
            "upper_tolerance": self.upper_input.text(),
            "status": self.status_input.currentData(),
        }

        try:
            if self.form_mode == "new":
                self.characteristic_service.create_manual_characteristic(
                    project=self.current_project,
                    data=data,
                )
                message = (
                    "A característica foi cadastrada com sucesso."
                )

            elif (
                self.form_mode == "edit"
                and self.selected_row is not None
            ):
                characteristic = self.selected_row.get(
                    "characteristic"
                )

                if characteristic is None:
                    return

                self.characteristic_service.update_characteristic(
                    characteristic=characteristic,
                    data=data,
                )
                message = (
                    "As alterações foram salvas com sucesso."
                )

            else:
                return

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
            "Característica salva",
            message,
        )

        self.clear_details()
        self.load_context()

    def delete_selected_characteristic(self) -> None:
        if self.selected_row is None:
            return

        characteristic = self.selected_row.get(
            "characteristic"
        )

        if characteristic is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir característica",
            (
                "Deseja excluir esta característica manual?\n\n"
                "Essa ação removerá o registro deste processo."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            self.characteristic_service.delete_manual_characteristic(
                characteristic
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao excluir característica",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Característica excluída",
            "A característica manual foi removida.",
        )

        self.clear_details()
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
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return str(value)

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
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return str(value)

        return f"{number:g}"

    def restore_combo_value(
        self,
        combo: QComboBox,
        value,
    ) -> None:
        if value in {None, ""}:
            combo.setCurrentIndex(0)
            return

        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)