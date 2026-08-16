from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.measurement_service import MeasurementService
from ui.components.page_header import PageHeader
from ui.components.section_header import SectionHeader


class MeasurementPage(QWidget):
    """
    Revisão e preenchimento das informações gerais da medição.
    """

    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None
        self.current_context: dict[str, Any] = {}

        self.measurement_service = MeasurementService()

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

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
        content.setMaximumWidth(1320)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        # ---------------------------------------------------------
        # CABEÇALHO
        # ---------------------------------------------------------

        self.page_header = PageHeader(
            title="Informações da medição",
            subtitle=(
                "Registre as informações técnicas disponíveis sobre a medição. "
                "Quando houver dados extraídos de documentos, o METRA poderá "
                "sugerir valores para complementar o preenchimento."
            ),
            metadata="-",
            back_text="← Visão geral",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        content_layout.addWidget(self.page_header)

        # ---------------------------------------------------------
        # CONTEXTO DO PROCESSO
        # ---------------------------------------------------------

        context_card = QFrame()
        context_card.setObjectName("measurementContextCard")

        context_layout = QGridLayout(context_card)
        context_layout.setContentsMargins(20, 15, 20, 15)
        context_layout.setHorizontalSpacing(32)
        context_layout.setVerticalSpacing(5)

        self.project_value = self.create_context_field(
            context_layout,
            label="Processo",
            row=0,
            column=0,
        )

        self.part_value = self.create_context_field(
            context_layout,
            label="Peça ou modelo",
            row=0,
            column=1,
        )

        self.equipment_value = self.create_context_field(
            context_layout,
            label="Equipamento",
            row=0,
            column=2,
        )

        for column in range(3):
            context_layout.setColumnStretch(column, 1)

        content_layout.addWidget(context_card)

        # ---------------------------------------------------------
        # INFORMAÇÕES AUTOMÁTICAS
        # ---------------------------------------------------------

        self.suggestion_card = QFrame()
        self.suggestion_card.setObjectName("formCard")

        suggestion_layout = QVBoxLayout(self.suggestion_card)
        suggestion_layout.setContentsMargins(20, 17, 20, 17)
        suggestion_layout.setSpacing(14)

        self.apply_suggestions_button = QPushButton(
            "Aplicar aos campos vazios"
        )
        self.apply_suggestions_button.setObjectName("primaryButton")
        self.apply_suggestions_button.setMinimumHeight(40)
        self.apply_suggestions_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.apply_suggestions_button.clicked.connect(
            self.apply_suggestions
        )

        suggestion_header = SectionHeader(
            title="Informações identificadas automaticamente",
            description=(
                "Valores consolidados a partir dos relatórios "
                "vinculados ao processo."
            ),
        )

        suggestion_header.add_action(
            self.apply_suggestions_button
        )

        suggestion_layout.addWidget(suggestion_header)

        suggestion_grid = QGridLayout()
        suggestion_grid.setHorizontalSpacing(28)
        suggestion_grid.setVerticalSpacing(12)

        self.detected_responsible_value = (
            self.create_information_value()
        )

        self.detected_datetime_value = (
            self.create_information_value()
        )

        self.detected_equipment_value = (
            self.create_information_value()
        )

        self.detected_software_value = (
            self.create_information_value()
        )

        self.detected_alignment_value = (
            self.create_information_value()
        )

        self.detected_sensors_value = (
            self.create_information_value()
        )

        self.add_information_field(
            layout=suggestion_grid,
            row=0,
            column=0,
            label="Responsável identificado",
            value_widget=self.detected_responsible_value,
        )

        self.add_information_field(
            layout=suggestion_grid,
            row=0,
            column=1,
            label="Data e hora",
            value_widget=self.detected_datetime_value,
        )

        self.add_information_field(
            layout=suggestion_grid,
            row=2,
            column=0,
            label="Equipamento",
            value_widget=self.detected_equipment_value,
        )

        self.add_information_field(
            layout=suggestion_grid,
            row=2,
            column=1,
            label="Software",
            value_widget=self.detected_software_value,
        )

        self.add_information_field(
            layout=suggestion_grid,
            row=4,
            column=0,
            label="Alinhamento",
            value_widget=self.detected_alignment_value,
        )

        self.add_information_field(
            layout=suggestion_grid,
            row=4,
            column=1,
            label="Sensores ou tecnologias",
            value_widget=self.detected_sensors_value,
        )

        suggestion_grid.setColumnStretch(0, 1)
        suggestion_grid.setColumnStretch(1, 1)

        suggestion_layout.addLayout(suggestion_grid)

        self.conflict_frame = QFrame()
        self.conflict_frame.setObjectName("analysisWarning")

        conflict_layout = QVBoxLayout(self.conflict_frame)
        conflict_layout.setContentsMargins(14, 11, 14, 11)
        conflict_layout.setSpacing(4)

        conflict_title = QLabel(
            "Pontos que precisam de revisão"
        )
        conflict_title.setObjectName("cardTitle")

        self.conflict_label = QLabel("")
        self.conflict_label.setObjectName("cardDescription")
        self.conflict_label.setWordWrap(True)

        conflict_layout.addWidget(conflict_title)
        conflict_layout.addWidget(self.conflict_label)

        self.conflict_frame.hide()
        suggestion_layout.addWidget(self.conflict_frame)

        self.suggestion_card.hide()
        content_layout.addWidget(self.suggestion_card)

        # ---------------------------------------------------------
        # MEDIÇÕES INDIVIDUAIS
        # ---------------------------------------------------------

        self.individual_measurements_card = QFrame()
        self.individual_measurements_card.setObjectName("formCard")

        individual_layout = QVBoxLayout(
            self.individual_measurements_card
        )
        individual_layout.setContentsMargins(20, 17, 20, 17)
        individual_layout.setSpacing(12)

        self.individual_description = QLabel(
            "Cada relatório mantém sua identificação, data, hora "
            "e informações extraídas."
        )
        self.individual_description.setObjectName(
            "formSectionDescription"
        )
        self.individual_description.setWordWrap(True)

        individual_header = SectionHeader(
            title="Medições individuais do lote",
            description="",
        )

        individual_layout.addWidget(individual_header)
        individual_layout.addWidget(self.individual_description)

        self.individual_measurements_container = QWidget()

        self.individual_measurements_layout = QVBoxLayout(
            self.individual_measurements_container
        )
        self.individual_measurements_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.individual_measurements_layout.setSpacing(8)

        individual_layout.addWidget(
            self.individual_measurements_container
        )

        self.individual_measurements_card.hide()
        content_layout.addWidget(
            self.individual_measurements_card
        )

        # ---------------------------------------------------------
        # GRID PRINCIPAL DE FORMULÁRIOS
        # ---------------------------------------------------------

        forms_grid = QGridLayout()
        forms_grid.setHorizontalSpacing(14)
        forms_grid.setVerticalSpacing(14)

        execution_card = self.build_execution_card()
        setup_card = self.build_setup_card()
        equipment_card = self.build_equipment_card()
        instructions_card = self.build_instructions_card()

        forms_grid.addWidget(execution_card, 0, 0)
        forms_grid.addWidget(setup_card, 0, 1)
        forms_grid.addWidget(equipment_card, 1, 0)
        forms_grid.addWidget(instructions_card, 1, 1)

        forms_grid.setColumnStretch(0, 1)
        forms_grid.setColumnStretch(1, 1)

        content_layout.addLayout(forms_grid)

        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.cancel_button.clicked.connect(
            self.back_requested.emit
        )

        self.save_button = QPushButton(
            "Salvar informações"
        )
        self.save_button.setObjectName("primaryButton")
        self.save_button.setMinimumHeight(42)
        self.save_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.save_button.clicked.connect(
            self.save_measurement
        )

        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)

        content_layout.addLayout(actions)

        content_row = QHBoxLayout()
        content_row.addStretch(1)
        content_row.addWidget(content, 12)
        content_row.addStretch(1)

        scroll_layout.addLayout(content_row)
        scroll_layout.addSpacing(16)

        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area)

    # =============================================================
    # CARDS DE FORMULÁRIO
    # =============================================================

    def build_execution_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("formCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(11)

        self.execution_description = QLabel(
            "Informe o responsável e a data geral quando essas informações "
            "forem aplicáveis ao processo."
        )
        self.execution_description.setObjectName(
            "formSectionDescription"
        )
        self.execution_description.setWordWrap(True)

        header = SectionHeader(
            title="Execução da medição",
            description="",
        )

        layout.addWidget(header)
        layout.addWidget(self.execution_description)

        responsible_label = QLabel(
            "Responsável geral pela medição"
        )
        responsible_label.setObjectName("fieldLabel")

        self.responsible_input = QLineEdit()
        self.responsible_input.setPlaceholderText(
            "Nome da pessoa responsável"
        )

        self.datetime_enabled = QCheckBox(
            "Informar data e hora geral"
        )
        self.datetime_enabled.toggled.connect(
            self.update_datetime_enabled
        )

        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDisplayFormat(
            "dd/MM/yyyy HH:mm"
        )
        self.datetime_input.setDateTime(
            QDateTime.currentDateTime()
        )
        self.datetime_input.setEnabled(False)

        self.datetime_help = QLabel(
            "Use somente quando a data for válida para todo o processo."
        )
        self.datetime_help.setObjectName("fieldHelper")
        self.datetime_help.setWordWrap(True)

        drawing_label = QLabel(
            "Desenho, CAD ou ordem de produção"
        )
        drawing_label.setObjectName("fieldLabel")

        self.drawing_input = QLineEdit()
        self.drawing_input.setPlaceholderText(
            "Referência técnica do processo"
        )

        layout.addWidget(responsible_label)
        layout.addWidget(self.responsible_input)
        layout.addWidget(self.datetime_enabled)
        layout.addWidget(self.datetime_input)
        layout.addWidget(self.datetime_help)
        layout.addWidget(drawing_label)
        layout.addWidget(self.drawing_input)

        return card

    def build_setup_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("formCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(11)

        header = SectionHeader(
            title="Preparação e setup",
            description=(
                "Documente o alinhamento e a fixação "
                "utilizados na medição."
            ),
        )

        self.alignment_input = QTextEdit()
        self.alignment_input.setPlaceholderText(
            "Descreva o alinhamento da peça."
        )
        self.alignment_input.setMaximumHeight(95)

        self.fixture_input = QTextEdit()
        self.fixture_input.setPlaceholderText(
            "Descreva a fixação da peça."
        )
        self.fixture_input.setMaximumHeight(95)

        alignment_label = QLabel("Alinhamento da peça")
        alignment_label.setObjectName("fieldLabel")

        fixture_label = QLabel("Fixação da peça")
        fixture_label.setObjectName("fieldLabel")

        layout.addWidget(header)
        layout.addWidget(alignment_label)
        layout.addWidget(self.alignment_input)
        layout.addWidget(fixture_label)
        layout.addWidget(self.fixture_input)

        return card

    def build_equipment_card(self) -> QFrame:

        card = QFrame()
        card.setObjectName("formCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(11)

        header = SectionHeader(
            title="Equipamento e sensores",
            description=(
                "Registre os detalhes da máquina, acessórios "
                "e tecnologias utilizadas."
            ),
        )

        machine_label = QLabel(
            "Equipamento e detalhes da máquina"
        )
        machine_label.setObjectName("fieldLabel")

        self.machine_details_input = QLineEdit()
        self.machine_details_input.setPlaceholderText(
            "Equipamento, identificação, configuração ou software"
        )

        accessories_label = QLabel(
            "Acessórios e periféricos"
        )
        accessories_label.setObjectName("fieldLabel")

        self.accessories_input = QLineEdit()
        self.accessories_input.setPlaceholderText(
            "Dispositivo de fixação, mesa rotativa ou extensões"
        )

        sensors_label = QLabel(
            "Sensores ou tecnologias utilizados"
        )
        sensors_label.setObjectName("fieldLabel")

        sensors_grid = QGridLayout()
        sensors_grid.setHorizontalSpacing(20)
        sensors_grid.setVerticalSpacing(9)

        self.probe_sensor = QCheckBox("Apalpação")
        self.optical_sensor = QCheckBox("Sensor óptico")
        self.dotscan_sensor = QCheckBox("DotScan")
        self.linescan_sensor = QCheckBox("LineScan")
        self.ct_sensor = QCheckBox(
            "Tomografia computadorizada"
        )
        self.scan_sensor = QCheckBox("Escaneamento 3D")
        self.other_sensor = QCheckBox("Outro")

        self.other_sensor.toggled.connect(
            self.update_other_sensor_enabled
        )

        self.other_sensor_input = QLineEdit()
        self.other_sensor_input.setPlaceholderText(
            "Informe o outro sensor ou tecnologia"
        )
        self.other_sensor_input.setEnabled(False)

        sensors_grid.addWidget(
            self.probe_sensor,
            0,
            0,
        )
        sensors_grid.addWidget(
            self.optical_sensor,
            0,
            1,
        )
        sensors_grid.addWidget(
            self.dotscan_sensor,
            1,
            0,
        )
        sensors_grid.addWidget(
            self.linescan_sensor,
            1,
            1,
        )
        sensors_grid.addWidget(
            self.ct_sensor,
            2,
            0,
        )
        sensors_grid.addWidget(
            self.scan_sensor,
            2,
            1,
        )
        sensors_grid.addWidget(
            self.other_sensor,
            3,
            0,
        )
        sensors_grid.addWidget(
            self.other_sensor_input,
            3,
            1,
        )

        sensors_grid.setColumnStretch(0, 1)
        sensors_grid.setColumnStretch(1, 1)

        layout.addWidget(header)
        layout.addWidget(machine_label)
        layout.addWidget(self.machine_details_input)
        layout.addWidget(accessories_label)
        layout.addWidget(self.accessories_input)
        layout.addWidget(sensors_label)
        layout.addLayout(sensors_grid)

        return card

    def build_instructions_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("formCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(11)

        header = SectionHeader(
            title="Observações técnicas",
            description=(
                "Registre condições especiais, ressalvas "
                "e instruções relevantes para o relatório."
            ),
        )

        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText(
            "Temperatura controlada, inspeção parcial, "
            "reposicionamento ou preparação da superfície."
        )
        self.instructions_input.setMaximumHeight(185)

        layout.addWidget(header)
        layout.addWidget(self.instructions_input)

        return card

    # =============================================================
    # COMPONENTES AUXILIARES
    # =============================================================

    def create_context_field(
        self,
        layout: QGridLayout,
        label: str,
        row: int,
        column: int,
    ) -> QLabel:
        label_widget = QLabel(label)
        label_widget.setObjectName("dataLabel")

        value_widget = QLabel("-")
        value_widget.setObjectName("dataValue")
        value_widget.setWordWrap(True)

        layout.addWidget(
            label_widget,
            row,
            column,
        )
        layout.addWidget(
            value_widget,
            row + 1,
            column,
        )

        return value_widget

    def create_information_value(self) -> QLabel:
        label = QLabel("Não identificado")
        label.setObjectName("dataValue")
        label.setWordWrap(True)

        return label

    def add_information_field(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        label: str,
        value_widget: QLabel,
    ) -> None:
        label_widget = QLabel(label)
        label_widget.setObjectName("dataLabel")

        layout.addWidget(
            label_widget,
            row,
            column,
        )
        layout.addWidget(
            value_widget,
            row + 1,
            column,
        )

    # =============================================================
    # DEFINIR PROCESSO
    # =============================================================

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = project

        self.page_header.set_metadata(
            f"{project.report_id} · {project.name}"
        )

        self.project_value.setText(
            f"{project.report_id} · {project.name}"
        )

        self.part_value.setText(
            project.part_name
            or "-"
        )

        self.load_measurement_context()

        self.scroll_area.verticalScrollBar().setValue(0)

    # =============================================================
    # CARREGAR CONTEXTO
    # =============================================================

    def load_measurement_context(self) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        try:
            context = (
                self.measurement_service
                .get_measurement_context(
                    self.current_project.id
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao carregar medição",
                (
                    "Não foi possível carregar as informações "
                    "da medição.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        self.current_context = context

        suggestions = context.get(
            "suggestions",
            {},
        )

        equipment_summary = (
            suggestions.get(
                "equipment_summary"
            )
            or self.current_project.equipment
            or "-"
        )

        self.equipment_value.setText(
            equipment_summary
        )

        self.populate_suggestion_card(
            context
        )

        self.populate_individual_measurements(
            context
        )

        self.update_process_type_texts(
            context
        )

        measurement = context.get(
            "saved_measurement"
        )

        if measurement is None:
            self.clear_form()
        else:
            self.populate_saved_measurement(
                measurement
            )

    # =============================================================
    # TEXTOS POR TIPO
    # =============================================================

    def update_process_type_texts(
        self,
        context: dict[str, Any],
    ) -> None:
        is_batch = bool(
            context.get(
                "is_batch"
            )
        )

        if is_batch:
            self.execution_description.setText(
                "Informe o responsável geral pelo processo. "
                "As datas e horas individuais extraídas de cada "
                "relatório permanecem registradas acima."
            )

            self.datetime_help.setText(
                "Opcional. Use somente se existir uma data "
                "geral aplicável a todo o lote."
            )
        else:
            self.execution_description.setText(
                "Informe responsável e data quando essas informações "
                "forem conhecidas ou aplicáveis ao trabalho."
            )

            self.datetime_help.setText(
                "Opcional. Use quando a data e a hora da medição "
                "forem conhecidas."
            )

    # =============================================================
    # SUGESTÕES
    # =============================================================

    def populate_suggestion_card(
        self,
        context: dict[str, Any],
    ) -> None:
        suggestions = context.get(
            "suggestions",
            {},
        )

        document_count = int(
            context.get(
                "document_count",
                0,
            )
            or 0
        )

        has_data = bool(
            context.get(
                "has_extracted_data"
            )
        )

        is_batch = bool(
            context.get(
                "is_batch"
            )
        )

        if not has_data:
            self.suggestion_card.hide()
            return

        self.suggestion_card.show()

        responsible_values = suggestions.get(
            "responsible_values",
            [],
        )

        responsible_document_count = int(
            suggestions.get(
                "responsible_document_count",
                0,
            )
            or 0
        )

        responsible_total_documents = int(
            suggestions.get(
                "responsible_total_documents",
                0,
            )
            or 0
        )

        if responsible_values:
            responsible_text = self.format_values(
                responsible_values
            )

            if (
                responsible_document_count
                < responsible_total_documents
            ):
                responsible_text += (
                    f"\nIdentificado em "
                    f"{responsible_document_count} de "
                    f"{responsible_total_documents} documentos."
                )
        else:
            responsible_text = (
                "Não identificado"
            )

        self.detected_responsible_value.setText(
            responsible_text
        )

        datetime_values = suggestions.get(
            "measurement_datetime_values",
            [],
        )

        if (
            is_batch
            and datetime_values
        ):
            datetime_text = (
                f"{len(datetime_values)} horários individuais "
                "identificados."
            )
        else:
            datetime_text = self.format_values(
                datetime_values
            )

        self.detected_datetime_value.setText(
            datetime_text
        )

        self.detected_equipment_value.setText(
            suggestions.get(
                "equipment_summary"
            )
            or "Não identificado"
        )

        self.detected_software_value.setText(
            suggestions.get(
                "software_summary"
            )
            or "Não identificado"
        )

        self.detected_alignment_value.setText(
            self.format_values(
                suggestions.get(
                    "alignment_values",
                    [],
                )
            )
        )

        self.detected_sensors_value.setText(
            self.format_values(
                suggestions.get(
                    "suggested_sensors",
                    [],
                )
            )
        )

        conflicts = suggestions.get(
            "conflicts",
            [],
        )

        if conflicts:
            self.conflict_label.setText(
                "\n".join(
                    f"• {conflict}"
                    for conflict in conflicts
                )
            )

            self.conflict_frame.show()
        else:
            self.conflict_label.clear()
            self.conflict_frame.hide()

        has_applicable_value = any(
            [
                suggestions.get(
                    "responsible"
                ),
                suggestions.get(
                    "measurement_datetime"
                ),
                suggestions.get(
                    "alignment"
                ),
                suggestions.get(
                    "machine_details"
                ),
                suggestions.get(
                    "suggested_sensors"
                ),
            ]
        )

        self.apply_suggestions_button.setEnabled(
            bool(has_applicable_value)
        )

    # =============================================================
    # MEDIÇÕES INDIVIDUAIS
    # =============================================================

    def populate_individual_measurements(
        self,
        context: dict[str, Any],
    ) -> None:
        self.clear_layout(
            self.individual_measurements_layout
        )

        is_batch = bool(
            context.get(
                "is_batch"
            )
        )

        measurements = context.get(
            "individual_measurements",
            [],
        )

        if (
            not is_batch
            or len(measurements) <= 1
        ):
            self.individual_measurements_card.hide()
            return

        self.individual_measurements_card.show()

        dated_count = sum(
            1
            for item in measurements
            if item.get(
                "measurement_datetime"
            )
        )

        self.individual_description.setText(
            (
                f"{len(measurements)} documentos no lote. "
                f"{dated_count} possuem data e hora identificadas."
            )
        )

        for index, item in enumerate(measurements):
            row = self.create_individual_measurement_row(
                item=item,
                index=index,
            )

            self.individual_measurements_layout.addWidget(
                row
            )

    def create_individual_measurement_row(
        self,
        item: dict[str, Any],
        index: int,
    ) -> QFrame:
        row = QFrame()
        row.setObjectName("documentListItem")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(12)

        order_label = QLabel(
            f"{index + 1:02d}"
        )
        order_label.setObjectName("documentOrder")
        order_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        order_label.setFixedSize(38, 38)

        information_layout = QVBoxLayout()
        information_layout.setSpacing(3)

        specimen_identifier = item.get(
            "specimen_identifier"
        )

        file_name = (
            item.get(
                "file_name"
            )
            or f"Documento {index + 1:02d}"
        )

        title_text = (
            f"Unidade {specimen_identifier}"
            if specimen_identifier
            else file_name
        )

        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)

        details = []

        part_number = item.get(
            "part_number"
        )

        if part_number:
            details.append(
                f"Identificação: {part_number}"
            )

        measurement_datetime = item.get(
            "measurement_datetime"
        )

        if measurement_datetime:
            details.append(
                (
                    "Data/hora: "
                    f"{self.format_datetime_text(measurement_datetime)}"
                )
            )
        else:
            details.append(
                "Data/hora não identificada"
            )

        operator = item.get(
            "operator"
        )

        if operator:
            details.append(
                f"Responsável: {operator}"
            )

        machine_name = item.get(
            "machine_name"
        )

        machine_number = item.get(
            "machine_number"
        )

        if machine_name:
            machine_text = machine_name

            if machine_number:
                machine_text += (
                    f" · {machine_number}"
                )

            details.append(
                f"Equipamento: {machine_text}"
            )

        details_label = QLabel(
            " · ".join(details)
        )
        details_label.setObjectName(
            "cardDescription"
        )
        details_label.setWordWrap(True)

        information_layout.addWidget(title)
        information_layout.addWidget(details_label)

        layout.addWidget(order_label)
        layout.addLayout(
            information_layout,
            1,
        )

        status_label = QLabel(
            (
                "Identificada"
                if measurement_datetime
                else "Revisar"
            )
        )

        status_label.setObjectName(
            (
                "statusBadgeSuccess"
                if measurement_datetime
                else "statusBadgeWarning"
            )
        )

        layout.addWidget(
            status_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        return row

    # =============================================================
    # APLICAR SUGESTÕES
    # =============================================================

    def apply_suggestions(self) -> None:
        suggestions = self.current_context.get(
            "suggestions",
            {},
        )

        applied_fields = []

        responsible = suggestions.get(
            "responsible"
        )

        if (
            responsible
            and not self.responsible_input.text().strip()
        ):
            self.responsible_input.setText(
                responsible
            )
            applied_fields.append(
                "responsável"
            )

        measurement_datetime = suggestions.get(
            "measurement_datetime"
        )

        if (
            measurement_datetime
            and not self.datetime_enabled.isChecked()
        ):
            parsed_datetime = self.parse_datetime(
                measurement_datetime
            )

            if parsed_datetime is not None:
                self.datetime_enabled.setChecked(
                    True
                )
                self.datetime_input.setDateTime(
                    parsed_datetime
                )
                applied_fields.append(
                    "data e hora"
                )

        alignment = suggestions.get(
            "alignment"
        )

        if (
            alignment
            and not self.alignment_input.toPlainText().strip()
        ):
            self.alignment_input.setPlainText(
                alignment
            )
            applied_fields.append(
                "alinhamento"
            )

        machine_details = suggestions.get(
            "machine_details"
        )

        if (
            machine_details
            and not self.machine_details_input.text().strip()
        ):
            self.machine_details_input.setText(
                machine_details
            )
            applied_fields.append(
                "equipamento"
            )

        sensors = suggestions.get(
            "suggested_sensors",
            [],
        )

        sensors_applied = self.apply_sensor_values(
            sensors,
            preserve_existing=True,
        )

        if sensors_applied:
            applied_fields.append(
                "sensores"
            )

        if applied_fields:
            QMessageBox.information(
                self,
                "Sugestões aplicadas",
                (
                    "Foram preenchidos os campos vazios de: "
                    f"{', '.join(applied_fields)}."
                ),
            )
        else:
            QMessageBox.information(
                self,
                "Nenhum campo alterado",
                (
                    "Os campos correspondentes já estavam "
                    "preenchidos ou não existem valores "
                    "confiáveis para aplicar."
                ),
            )

    # =============================================================
    # SALVAR
    # =============================================================

    def save_measurement(self) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        sensors = self.collect_sensors()

        if self.datetime_enabled.isChecked():
            measurement_datetime = (
                self.datetime_input
                .dateTime()
                .toString(
                    Qt.DateFormat.ISODate
                )
            )
        else:
            measurement_datetime = None

        data = {
            "responsible":
                self.responsible_input.text(),

            "measurement_datetime":
                measurement_datetime,

            "drawing_reference":
                self.drawing_input.text(),

            "alignment":
                self.alignment_input.toPlainText(),

            "fixture":
                self.fixture_input.toPlainText(),

            "machine_details":
                self.machine_details_input.text(),

            "accessories":
                self.accessories_input.text(),

            "sensors":
                sensors,

            "special_instructions":
                self.instructions_input.toPlainText(),
        }

        try:
            measurement = (
                self.measurement_service
                .save_measurement(
                    self.current_project.id,
                    data,
                )
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
                "Erro ao salvar medição",
                (
                    "Não foi possível salvar as informações.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        self.current_context[
            "saved_measurement"
        ] = measurement

        QMessageBox.information(
            self,
            "Informações salvas",
            (
                "Os dados gerais da medição foram "
                "salvos com sucesso."
            ),
        )

    # =============================================================
    # MEDIÇÃO SALVA
    # =============================================================

    def populate_saved_measurement(
        self,
        measurement,
    ) -> None:
        self.clear_form()

        self.responsible_input.setText(
            measurement.responsible
            or ""
        )

        if measurement.measurement_datetime:
            parsed_datetime = self.parse_datetime(
                measurement.measurement_datetime
            )

            if parsed_datetime is not None:
                self.datetime_enabled.setChecked(
                    True
                )
                self.datetime_input.setDateTime(
                    parsed_datetime
                )

        self.drawing_input.setText(
            measurement.drawing_reference
            or ""
        )

        self.alignment_input.setPlainText(
            measurement.alignment
            or ""
        )

        self.fixture_input.setPlainText(
            measurement.fixture
            or ""
        )

        self.machine_details_input.setText(
            measurement.machine_details
            or ""
        )

        self.accessories_input.setText(
            measurement.accessories
            or ""
        )

        self.instructions_input.setPlainText(
            measurement.special_instructions
            or ""
        )

        sensors = (
            self.measurement_service
            .get_sensors(
                measurement
            )
        )

        self.apply_sensor_values(
            sensors,
            preserve_existing=False,
        )

    # =============================================================
    # SENSORES
    # =============================================================

    def collect_sensors(self) -> list[str]:
        sensors = []

        if self.probe_sensor.isChecked():
            sensors.append(
                "Apalpação"
            )

        if self.optical_sensor.isChecked():
            sensors.append(
                "Sensor óptico"
            )

        if self.dotscan_sensor.isChecked():
            sensors.append(
                "DotScan"
            )

        if self.linescan_sensor.isChecked():
            sensors.append(
                "LineScan"
            )

        if self.ct_sensor.isChecked():
            sensors.append(
                "Tomografia computadorizada"
            )

        if self.scan_sensor.isChecked():
            sensors.append(
                "Escaneamento 3D"
            )

        if self.other_sensor.isChecked():
            other_value = (
                self.other_sensor_input
                .text()
                .strip()
            )

            if other_value:
                sensors.append(
                    f"Outro: {other_value}"
                )
            else:
                sensors.append(
                    "Outro"
                )

        return sensors

    def apply_sensor_values(
        self,
        sensors: list[str],
        preserve_existing: bool,
    ) -> bool:
        if not preserve_existing:
            self.clear_sensor_checks()

        changed = False

        for sensor in sensors:
            normalized = str(
                sensor
            ).strip()

            normalized_lower = normalized.lower()

            checkbox = None

            if normalized_lower == "apalpação":
                checkbox = self.probe_sensor

            elif normalized_lower == "sensor óptico":
                checkbox = self.optical_sensor

            elif normalized_lower == "dotscan":
                checkbox = self.dotscan_sensor

            elif normalized_lower == "linescan":
                checkbox = self.linescan_sensor

            elif normalized_lower == (
                "tomografia computadorizada"
            ):
                checkbox = self.ct_sensor

            elif normalized_lower == "escaneamento 3d":
                checkbox = self.scan_sensor

            elif normalized_lower.startswith(
                "outro"
            ):
                if not self.other_sensor.isChecked():
                    self.other_sensor.setChecked(
                        True
                    )
                    changed = True

                if ":" in normalized:
                    detail = (
                        normalized
                        .split(
                            ":",
                            1,
                        )[1]
                        .strip()
                    )

                    if (
                        detail
                        and not self.other_sensor_input.text().strip()
                    ):
                        self.other_sensor_input.setText(
                            detail
                        )
                        changed = True

                continue

            if (
                checkbox is not None
                and not checkbox.isChecked()
            ):
                checkbox.setChecked(
                    True
                )
                changed = True

        return changed

    def clear_sensor_checks(self) -> None:
        self.probe_sensor.setChecked(
            False
        )
        self.optical_sensor.setChecked(
            False
        )
        self.dotscan_sensor.setChecked(
            False
        )
        self.linescan_sensor.setChecked(
            False
        )
        self.ct_sensor.setChecked(
            False
        )
        self.scan_sensor.setChecked(
            False
        )
        self.other_sensor.setChecked(
            False
        )
        self.other_sensor_input.clear()

    # =============================================================
    # LIMPAR FORMULÁRIO
    # =============================================================

    def clear_form(self) -> None:
        self.responsible_input.clear()

        self.datetime_enabled.setChecked(
            False
        )

        self.datetime_input.setDateTime(
            QDateTime.currentDateTime()
        )

        self.drawing_input.clear()
        self.alignment_input.clear()
        self.fixture_input.clear()
        self.machine_details_input.clear()
        self.accessories_input.clear()
        self.instructions_input.clear()

        self.clear_sensor_checks()

    # =============================================================
    # ESTADOS DOS CAMPOS
    # =============================================================

    def update_datetime_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.datetime_input.setEnabled(
            enabled
        )

    def update_other_sensor_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.other_sensor_input.setEnabled(
            enabled
        )

        if not enabled:
            self.other_sensor_input.clear()

    # =============================================================
    # DATA E HORA
    # =============================================================

    def parse_datetime(
        self,
        value: str,
    ) -> QDateTime | None:
        clean = str(
            value
        ).strip()

        if not clean:
            return None

        formats = [
            Qt.DateFormat.ISODate,
            Qt.DateFormat.ISODateWithMs,
        ]

        for date_format in formats:
            result = QDateTime.fromString(
                clean,
                date_format,
            )

            if result.isValid():
                return result

        custom_formats = [
            "dd/MM/yyyy HH:mm",
            "dd/MM/yyyy HH:mm:ss",
            "dd-MM-yyyy HH:mm",
            "dd-MM-yyyy HH:mm:ss",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd HH:mm",
        ]

        for date_format in custom_formats:
            result = QDateTime.fromString(
                clean,
                date_format,
            )

            if result.isValid():
                return result

        return None

    def format_datetime_text(
        self,
        value: str,
    ) -> str:
        parsed = self.parse_datetime(
            value
        )

        if parsed is None:
            return str(value)

        return parsed.toString(
            "dd/MM/yyyy HH:mm"
        )

    # =============================================================
    # FORMATAÇÃO
    # =============================================================

    def format_values(
        self,
        values: list[str],
    ) -> str:
        clean_values = [
            str(value).strip()
            for value in values
            if str(value).strip()
        ]

        if not clean_values:
            return "Não identificado"

        return " · ".join(
            clean_values
        )

    # =============================================================
    # LIMPEZA DE LAYOUT
    # =============================================================

    def clear_layout(
        self,
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()

            elif child_layout is not None:
                self.clear_layout(
                    child_layout
                )