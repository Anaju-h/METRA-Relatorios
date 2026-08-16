from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.components.page_header import PageHeader
from ui.components.step_indicator import StepIndicator


class ProjectFormStep(QWidget):
    """
    Última etapa da criação do processo.

    O usuário apenas revisa ou complementa
    os dados extraídos automaticamente antes
    da criação definitiva do projeto.
    """

    back_requested = Signal()

    create_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        self.flow_mode = "documents"

        self.setObjectName("pageBackground")

        self.build_ui()
    def build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(0,0,0,0)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        container = QWidget()

        container.setObjectName(
            "pageBackground"
        )

        layout = QVBoxLayout(container)

        layout.setContentsMargins(
            34,
            22,
            34,
            34,
        )

        layout.setSpacing(
            18
        )

        self.header = PageHeader(

            title="Criar processo",

            subtitle=(
                "Revise os dados e finalize "
                "a criação do processo."
            ),

            back_text="← Revisão",
        )

        self.header.back_button.clicked.connect(
            self.back_requested.emit
        )

        layout.addWidget(
            self.header
        )

        self.steps = StepIndicator(

            [
                "Documentos",
                "Revisão",
                "Criar",
            ],

            current_step=2,
        )

        layout.addWidget(
            self.steps
        )
        # ---------------------------------------------------------
        # INFORMAÇÕES DO PROCESSO
        # ---------------------------------------------------------

        process_card = QFrame()

        process_card.setObjectName(
            "formCard"
        )

        process_layout = QVBoxLayout(
            process_card
        )

        process_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        process_layout.setSpacing(
            16
        )

        process_title = QLabel(
            "Informações do processo"
        )

        process_title.setObjectName(
            "formSectionTitle"
        )

        process_description = QLabel(
            (
                "Defina a identificação principal, o tipo de inspeção "
                "e o modo de análise que será utilizado."
            )
        )

        process_description.setObjectName(
            "formSectionDescription"
        )

        process_description.setWordWrap(
            True
        )

        process_layout.addWidget(
            process_title
        )

        process_layout.addWidget(
            process_description
        )

        process_form = QFormLayout()

        process_form.setHorizontalSpacing(
            28
        )

        process_form.setVerticalSpacing(
            12
        )

        process_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
        )

        process_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.project_name_input = QLineEdit()

        self.project_name_input.setPlaceholderText(
            "Ex.: Inspeção dimensional — Carcaça da bomba"
        )

        self.inspection_type_input = QComboBox()

        self.inspection_type_input.addItems(
            [
                "Inspeção dimensional",
                "Inspeção tomográfica",
                "Inspeção óptica",
                "Escaneamento 3D",
                "Engenharia reversa",
                "Outro",
            ]
        )

        self.analysis_mode_input = QComboBox()

        self.analysis_mode_input.addItems(
            [
                "Peça única",
                "Lote / estatística",
                "Análise qualitativa",
                "Comparação com CAD",
                "Personalizada",
            ]
        )

        self.quantity_input = QSpinBox()

        self.quantity_input.setRange(
            1,
            9999,
        )

        self.quantity_input.setValue(
            1
        )

        self.quantity_input.setSuffix(
            " unidade(s)"
        )

        process_form.addRow(
            "Nome do processo *",
            self.project_name_input,
        )

        process_form.addRow(
            "Tipo de inspeção *",
            self.inspection_type_input,
        )

        process_form.addRow(
            "Modo da análise *",
            self.analysis_mode_input,
        )

        process_form.addRow(
            "Quantidade de peças *",
            self.quantity_input,
        )

        process_layout.addLayout(
            process_form
        )

        layout.addWidget(
            process_card
        )
        # ---------------------------------------------------------
        # TEMPLATE DO RELATÓRIO
        # ---------------------------------------------------------

        template_card = QFrame()

        template_card.setObjectName(
            "formCard"
        )

        template_layout = QVBoxLayout(
            template_card
        )

        template_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        template_layout.setSpacing(
            14
        )

        template_title = QLabel(
            "Template do relatório"
        )

        template_title.setObjectName(
            "formSectionTitle"
        )

        template_description = QLabel(
            (
                "O METRA sugere automaticamente um template com base "
                "no tipo de inspeção, no modo da análise, na quantidade "
                "de peças e no equipamento informado."
            )
        )

        template_description.setObjectName(
            "formSectionDescription"
        )

        template_description.setWordWrap(
            True
        )

        template_layout.addWidget(
            template_title
        )

        template_layout.addWidget(
            template_description
        )

        template_form = QFormLayout()

        template_form.setHorizontalSpacing(
            28
        )

        template_form.setVerticalSpacing(
            12
        )

        template_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
        )

        template_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.template_input = QComboBox()

        self.template_input.addItem(
            "Dimensional individual",
            "DIMENSIONAL_INDIVIDUAL",
        )

        self.template_input.addItem(
            "Dimensional em lote",
            "DIMENSIONAL_LOTE",
        )

        self.template_input.addItem(
            "Tomografia industrial",
            "TOMOGRAFIA_INDUSTRIAL",
        )

        self.template_input.addItem(
            "Personalizado",
            "PERSONALIZADO",
        )

        self.template_description_label = QLabel(
            "O template selecionado define os campos obrigatórios, "
            "as validações, as seções e o formato do relatório final."
        )

        self.template_description_label.setObjectName(
            "analysisModel"
        )

        self.template_description_label.setWordWrap(
            True
        )

        self.template_source_label = QLabel(
            "◆ Sugerido automaticamente pelo METRA"
        )

        self.template_source_label.setObjectName(
            "fieldSource"
        )

        template_form.addRow(
            "Template *",
            self.template_input,
        )

        template_layout.addLayout(
            template_form
        )

        template_layout.addWidget(
            self.template_source_label
        )

        template_layout.addWidget(
            self.template_description_label
        )

        layout.addWidget(
            template_card
        )
        # ---------------------------------------------------------
        # DADOS DA PEÇA
        # ---------------------------------------------------------

        piece_card = QFrame()

        piece_card.setObjectName(
            "formCard"
        )

        piece_layout = QVBoxLayout(
            piece_card
        )

        piece_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        piece_layout.setSpacing(
            16
        )

        piece_title = QLabel(
            "Dados da peça"
        )

        piece_title.setObjectName(
            "formSectionTitle"
        )

        piece_description = QLabel(
            (
                "Essas informações identificam a peça inspecionada "
                "e serão utilizadas no cabeçalho do relatório."
            )
        )

        piece_description.setObjectName(
            "formSectionDescription"
        )

        piece_description.setWordWrap(
            True
        )

        piece_layout.addWidget(
            piece_title
        )

        piece_layout.addWidget(
            piece_description
        )

        piece_form = QFormLayout()

        piece_form.setHorizontalSpacing(
            28
        )

        piece_form.setVerticalSpacing(
            12
        )

        self.part_name_input = QLineEdit()

        self.part_name_input.setPlaceholderText(
            "Nome da peça"
        )

        self.part_code_input = QLineEdit()

        self.part_code_input.setPlaceholderText(
            "Código interno"
        )

        self.client_input = QLineEdit()

        self.client_input.setPlaceholderText(
            "Cliente"
        )

        self.equipment_input = QComboBox()

        self.equipment_input.addItems(
            [
                "",
                "PRISMO",
                "DuraMax",
                "O-INSPECT",
                "ATOS Q",
                "T-SCAN",
                "Bosello Max",
            ]
        )

        self.equipment_source_label = QLabel(
            "Nenhum equipamento identificado automaticamente."
        )
        self.equipment_source_label.setObjectName(
            "fieldSource"
        )
        self.equipment_source_label.setWordWrap(
            True
        )

        self.technology_input = QComboBox()

        self.technology_input.addItems(
            [
                "",
                "Apalpação",
                "Sensor Óptico",
                "Tomografia Industrial",
                "Escaneamento 3D",
                "Engenharia Reversa",
            ]
        )

        piece_form.addRow(
            "Nome da peça",
            self.part_name_input,
        )

        piece_form.addRow(
            "Código da peça",
            self.part_code_input,
        )

        piece_form.addRow(
            "Cliente",
            self.client_input,
        )

        equipment_field = QWidget()
        equipment_field_layout = QVBoxLayout(
            equipment_field
        )
        equipment_field_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        equipment_field_layout.setSpacing(
            5
        )

        equipment_field_layout.addWidget(
            self.equipment_input
        )
        equipment_field_layout.addWidget(
            self.equipment_source_label
        )

        piece_form.addRow(
            "Equipamento",
            equipment_field,
        )

        piece_form.addRow(
            "Tecnologia",
            self.technology_input,
        )

        piece_layout.addLayout(
            piece_form
        )

        layout.addWidget(
            piece_card
        )
        # ---------------------------------------------------------
        # OBSERVAÇÕES
        # ---------------------------------------------------------

        notes_card = QFrame()

        notes_card.setObjectName(
            "formCard"
        )

        notes_layout = QVBoxLayout(
            notes_card
        )

        notes_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        notes_layout.setSpacing(
            14
        )

        notes_title = QLabel(
            "Observações"
        )

        notes_title.setObjectName(
            "formSectionTitle"
        )

        notes_description = QLabel(
            (
                "Inclua informações adicionais que possam auxiliar "
                "na elaboração do relatório técnico."
            )
        )

        notes_description.setObjectName(
            "formSectionDescription"
        )

        notes_description.setWordWrap(
            True
        )

        notes_layout.addWidget(
            notes_title
        )

        notes_layout.addWidget(
            notes_description
        )

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Observações sobre a inspeção, requisitos do cliente, "
            "normas aplicáveis, cuidados especiais, etc."
        )

        self.description_input.setMinimumHeight(
            130
        )

        notes_layout.addWidget(
            self.description_input
        )

        layout.addWidget(
            notes_card
        )

        # ---------------------------------------------------------
        # BOTÕES
        # ---------------------------------------------------------

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(
            10
        )

        self.cancel_button = QPushButton(
            "Cancelar"
        )

        self.cancel_button.setObjectName(
            "secondaryButton"
        )

        self.cancel_button.setMinimumHeight(
            46
        )

        self.cancel_button.clicked.connect(
            self.back_requested.emit
        )

        buttons_layout.addWidget(
            self.cancel_button
        )

        buttons_layout.addStretch()

        self.create_button = QPushButton(
            "Criar processo"
        )

        self.create_button.setObjectName(
            "primaryButton"
        )

        self.create_button.setMinimumHeight(
            46
        )

        self.create_button.clicked.connect(
            self.on_create_clicked
        )

        buttons_layout.addWidget(
            self.create_button
        )

        layout.addLayout(
            buttons_layout
        )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        root.addWidget(
            scroll
        )

        self.connect_signals()

        self.update_template_information()
    # =============================================================
    # MODO DO FLUXO
    # =============================================================

    def set_flow_mode(
        self,
        mode: str,
    ) -> None:
        normalized = str(
            mode
            or "documents"
        ).strip().lower()

        self.flow_mode = (
            "manual"
            if normalized == "manual"
            else "documents"
        )

        if self.flow_mode == "manual":
            self.header.set_title(
                "Informações do processo"
            )
            self.header.set_subtitle(
                "Preencha os dados iniciais para estruturar o processo. "
                "Documentos e informações técnicas poderão ser adicionados "
                "posteriormente."
            )
            self.header.back_button.setText(
                "← Forma de início"
            )

            self.steps.set_steps(
                [
                    "Informações",
                    "Criar",
                ],
                current_step=0,
            )

            self.template_source_label.setText(
                "Selecione o template mais adequado. O modelo Personalizado "
                "é indicado para casos ainda não mapeados pelo METRA."
            )

            self.equipment_source_label.setText(
                "Preenchimento opcional. Informe o equipamento quando ele "
                "já for conhecido."
            )

        else:
            self.header.set_title(
                "Criar processo"
            )
            self.header.set_subtitle(
                "Revise os dados identificados, complemente as informações "
                "necessárias e finalize a criação."
            )
            self.header.back_button.setText(
                "← Revisão"
            )

            self.steps.set_steps(
                [
                    "Documentos",
                    "Revisão",
                    "Criar",
                ],
                current_step=2,
            )

    # =============================================================
    # CONEXÕES
    # =============================================================

    def connect_signals(
        self,
    ) -> None:
        self.inspection_type_input.currentTextChanged.connect(
            self.update_template_suggestion
        )

        self.analysis_mode_input.currentTextChanged.connect(
            self.update_template_suggestion
        )

        self.quantity_input.valueChanged.connect(
            self.update_template_suggestion
        )

        self.equipment_input.currentTextChanged.connect(
            self.update_template_suggestion
        )

        self.template_input.currentIndexChanged.connect(
            self.update_template_information
        )

    # =============================================================
    # SUGESTÃO DE TEMPLATE
    # =============================================================

    def update_template_suggestion(
        self,
    ) -> None:
        inspection_type = (
            self.inspection_type_input
            .currentText()
            .strip()
        )

        analysis_mode = (
            self.analysis_mode_input
            .currentText()
            .strip()
        )

        quantity = (
            self.quantity_input
            .value()
        )

        equipment = (
            self.equipment_input
            .currentText()
            .strip()
        )

        suggested_code = (
            self.get_suggested_template_code(
                inspection_type=inspection_type,
                analysis_mode=analysis_mode,
                quantity=quantity,
                equipment=equipment,
            )
        )

        index = (
            self.template_input
            .findData(
                suggested_code
            )
        )

        if index >= 0:
            self.template_input.blockSignals(
                True
            )

            self.template_input.setCurrentIndex(
                index
            )

            self.template_input.blockSignals(
                False
            )

        self.template_source_label.setText(
            "◆ Sugerido automaticamente pelo METRA"
        )

        self.update_template_information()

    def get_suggested_template_code(
        self,
        *,
        inspection_type: str,
        analysis_mode: str,
        quantity: int,
        equipment: str,
    ) -> str:
        inspection = (
            inspection_type
            .strip()
            .lower()
        )

        mode = (
            analysis_mode
            .strip()
            .lower()
        )

        equipment_name = (
            equipment
            .strip()
            .lower()
        )

        if (
            "tomograf" in inspection
            or "bosello" in equipment_name
        ):
            return (
                "TOMOGRAFIA_INDUSTRIAL"
            )

        if (
            "dimension" in inspection
        ):
            if (
                quantity > 1
                or "lote" in mode
                or "estat" in mode
            ):
                return (
                    "DIMENSIONAL_LOTE"
                )

            return (
                "DIMENSIONAL_INDIVIDUAL"
            )

        return "PERSONALIZADO"
    # =============================================================
    # DESCRIÇÃO DO TEMPLATE
    # =============================================================

    def update_template_information(
        self,
    ) -> None:
        template_code = (
            self.template_input
            .currentData()
        )

        descriptions = {
            "DIMENSIONAL_INDIVIDUAL": (
                "Relatório dimensional para uma única peça, "
                "com características, valores nominais, tolerâncias, "
                "resultados, imagens e conclusão técnica."
            ),

            "DIMENSIONAL_LOTE": (
                "Relatório dimensional consolidado para várias peças, "
                "com estatística, conformidade, gráficos, resultados "
                "por unidade e interpretação técnica."
            ),

            "TOMOGRAFIA_INDUSTRIAL": (
                "Relatório de inspeção tomográfica industrial, "
                "com método, parâmetros de aquisição, imagens, "
                "resultados qualitativos, conclusão e limitações."
            ),

            "PERSONALIZADO": (
                "Modelo flexível para processos que ainda não possuem "
                "um template técnico específico."
            ),
        }

        description = descriptions.get(
            template_code,
            "Selecione um template.",
        )

        self.template_description_label.setText(
            description
        )
    # =============================================================
    # PREENCHIMENTO A PARTIR DO RASCUNHO
    # =============================================================

    def set_draft(
        self,
        draft,
    ) -> None:
        process_type = getattr(
            draft,
            "process_type",
            "manual",
        )

        is_batch = bool(
            getattr(
                draft,
                "is_batch",
                False,
            )
        )

        if is_batch:
            self.analysis_mode_input.setCurrentText(
                "Lote / estatística"
            )

            specimen_count = int(
                getattr(
                    draft,
                    "specimen_count",
                    1,
                )
                or 1
            )

            self.quantity_input.setValue(
                max(
                    1,
                    specimen_count,
                )
            )

        else:
            self.analysis_mode_input.setCurrentText(
                "Peça única"
            )

            self.quantity_input.setValue(
                1
            )

        equipment = getattr(
            draft,
            "equipment",
            None,
        )

        equipments = list(
            getattr(
                draft,
                "equipments",
                [],
            )
            or []
        )

        detected_equipment = None

        if equipment:
            detected_equipment = str(
                equipment
            )

        elif len(
            equipments
        ) == 1:
            detected_equipment = str(
                equipments[0]
            )

        if detected_equipment:
            index = self.equipment_input.findText(
                detected_equipment,
                Qt.MatchFlag.MatchFixedString,
            )

            if index >= 0:
                self.equipment_input.setCurrentIndex(
                    index
                )
            else:
                self.equipment_input.addItem(
                    detected_equipment
                )
                self.equipment_input.setCurrentText(
                    detected_equipment
                )

            self.equipment_source_label.setText(
                "◆ Identificado automaticamente a partir dos relatórios. "
                "Altere somente se precisar corrigir a identificação."
            )

        elif len(equipments) > 1:
            self.equipment_input.setCurrentIndex(
                0
            )

            self.equipment_source_label.setText(
                "◆ Foram identificados equipamentos diferentes nos relatórios. "
                "Selecione o equipamento principal apenas se necessário."
            )

        else:
            self.equipment_input.setCurrentIndex(
                0
            )

            self.equipment_source_label.setText(
                "Nenhum equipamento foi identificado automaticamente. "
                "Selecione manualmente apenas se essa informação for necessária."
            )

        base_part_name = getattr(
            draft,
            "base_part_name",
            None,
        )

        part_name = getattr(
            draft,
            "part_name",
            None,
        )

        self.part_name_input.setText(
            str(
                base_part_name
                or part_name
                or ""
            )
        )

        suggested_project_name = getattr(
            draft,
            "suggested_project_name",
            None,
        )

        if suggested_project_name:
            self.project_name_input.setText(
                str(
                    suggested_project_name
                )
            )

        source_types = {
            str(
                getattr(
                    document,
                    "source_type",
                    "",
                )
            ).strip().upper()
            for document in getattr(
                draft,
                "documents",
                [],
            )
            if getattr(
                document,
                "source_type",
                None,
            )
        }

        equipment_text = (
            self.equipment_input
            .currentText()
            .lower()
        )

        if (
            "bosello" in equipment_text
            or any(
                "CT" in source
                or "TOMOGRAPH" in source
                for source in source_types
            )
        ):
            self.inspection_type_input.setCurrentText(
                "Inspeção tomográfica"
            )

            self.analysis_mode_input.setCurrentText(
                "Análise qualitativa"
            )

            self.technology_input.setCurrentText(
                "Tomografia Industrial"
            )

        else:
            self.inspection_type_input.setCurrentText(
                "Inspeção dimensional"
            )

            if is_batch:
                self.analysis_mode_input.setCurrentText(
                    "Lote / estatística"
                )

            else:
                self.analysis_mode_input.setCurrentText(
                    "Peça única"
                )

            if self.equipment_input.currentText().strip():
                self.technology_input.setCurrentText(
                    "Apalpação"
                )

        suggested_template = getattr(
            draft,
            "suggested_template",
            None,
        )

        if suggested_template:
            template_index = (
                self.template_input.findData(
                    str(
                        suggested_template
                    )
                )
            )

            if template_index < 0:
                template_index = (
                    self.template_input.findText(
                        str(
                            suggested_template
                        )
                    )
                )

            if template_index >= 0:
                self.template_input.setCurrentIndex(
                    template_index
                )

                self.template_source_label.setText(
                    "◆ Sugerido a partir dos documentos analisados"
                )

            else:
                self.update_template_suggestion()

        else:
            self.update_template_suggestion()

        if process_type == "manual":
            self.set_flow_mode(
                "manual"
            )

            self.template_source_label.setText(
                "Selecione o template mais adequado. O modelo Personalizado "
                "é indicado para casos ainda não mapeados pelo METRA."
            )
        else:
            self.set_flow_mode(
                "documents"
            )

        self.update_template_information()
    # =============================================================
    # CRIAÇÃO
    # =============================================================

    def on_create_clicked(
        self,
    ) -> None:
        data = self.get_form_data()

        if not data["name"]:
            self._show_validation_message(
                "Nome obrigatório",
                "Informe o nome do processo.",
            )
            return

        if not data["inspection_type"]:
            self._show_validation_message(
                "Tipo de inspeção obrigatório",
                "Selecione o tipo de inspeção.",
            )
            return

        if not data["analysis_mode"]:
            self._show_validation_message(
                "Modo da análise obrigatório",
                "Selecione o modo da análise.",
            )
            return

        if not data["template"]:
            self._show_validation_message(
                "Template obrigatório",
                "Selecione o template do relatório.",
            )
            return

        if not data["part_name"]:
            self._show_validation_message(
                "Peça obrigatória",
                "Informe o nome da peça ou componente.",
            )
            return

        self.create_requested.emit(
            data
        )

    def get_form_data(
        self,
    ) -> dict:
        return {
            "name":
                self.project_name_input
                .text()
                .strip(),

            "inspection_type":
                self.inspection_type_input
                .currentText()
                .strip(),

            "analysis_mode":
                self.analysis_mode_input
                .currentText()
                .strip(),

            "quantity":
                self.quantity_input
                .value(),

            "template":
                str(
                    self.template_input
                    .currentData()
                    or ""
                ).strip(),

            "part_name":
                self.part_name_input
                .text()
                .strip(),

            "part_code":
                self.part_code_input
                .text()
                .strip(),

            "client":
                self.client_input
                .text()
                .strip(),

            "equipment":
                self.equipment_input
                .currentText()
                .strip(),

            "technology":
                self.technology_input
                .currentText()
                .strip(),

            "description":
                self.description_input
                .toPlainText()
                .strip(),
        }

    def set_creating(
        self,
        creating: bool,
    ) -> None:
        self.create_button.setEnabled(
            not creating
        )

        self.cancel_button.setEnabled(
            not creating
        )

        self.create_button.setText(
            (
                "Criando processo..."
                if creating
                else "Criar processo"
            )
        )

    def clear_form(
        self,
    ) -> None:
        self.project_name_input.clear()

        self.inspection_type_input.setCurrentIndex(
            0
        )

        self.analysis_mode_input.setCurrentIndex(
            0
        )

        self.quantity_input.setValue(
            1
        )

        self.part_name_input.clear()
        self.part_code_input.clear()
        self.client_input.clear()

        self.equipment_input.setCurrentIndex(
            0
        )

        self.equipment_source_label.setText(
            "Nenhum equipamento identificado automaticamente."
        )

        self.technology_input.setCurrentIndex(
            0
        )

        self.description_input.clear()

        self.template_input.setCurrentIndex(
            0
        )

        self.template_source_label.setText(
            "◆ Sugerido automaticamente pelo METRA"
        )

        self.update_template_suggestion()

    def reset_step(
        self,
    ) -> None:
        self.clear_form()

        self.set_creating(
            False
        )

    def _show_validation_message(
        self,
        title: str,
        message: str,
    ) -> None:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.warning(
            self,
            title,
            message,
        )