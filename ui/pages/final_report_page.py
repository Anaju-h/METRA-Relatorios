from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.final_report_service import (
    FinalReportService,
)
from services.report_templates.template_catalog import (
    get_template_definition,
)
from ui.components.page_header import PageHeader


class FinalReportPage(QWidget):
    """
    Preparação e validação do relatório técnico.

    Esta tela reúne o contexto do processo, valida os dados,
    permite escolher o conteúdo do documento e solicita a
    pré-visualização antes da aprovação e exportação.

    A escolha realizada aqui representa o conteúdo que deverá
    compor também o documento final aprovado.
    """

    back_requested = Signal()

    documents_requested = Signal()
    characteristics_requested = Signal()
    measurement_requested = Signal()
    images_requested = Signal()
    technical_control_requested = Signal()

    generate_requested = Signal(dict)

    VERSION_SECTION_KEY = "show_version"

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.current_project: Project | None = None
        self.service = FinalReportService()

        self.current_context: dict[str, Any] = {}
        self.section_inputs: dict[str, QCheckBox] = {}

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
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
        scroll_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName(
            "pageContent"
        )
        content.setMaximumWidth(1240)
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
        content_layout.setSpacing(18)

        # ---------------------------------------------------------
        # CABEÇALHO
        # ---------------------------------------------------------

        self.page_header = PageHeader(
            title="Relatório final",
            subtitle=(
                "Valide o processo, defina o conteúdo do relatório "
                "e gere uma pré-visualização antes da aprovação "
                "e exportação."
            ),
            metadata="-",
            back_text="← Visão geral",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.refresh_button = QPushButton(
            "Atualizar validação"
        )
        self.refresh_button.setObjectName(
            "secondaryButton"
        )
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.refresh_button.clicked.connect(
            self.load_context
        )

        self.page_header.add_action(
            self.refresh_button
        )

        content_layout.addWidget(
            self.page_header
        )

        # ---------------------------------------------------------
        # CONTEXTO DO RELATÓRIO
        # ---------------------------------------------------------

        context_card = QFrame()
        context_card.setObjectName(
            "formCard"
        )

        context_layout = QGridLayout(
            context_card
        )
        context_layout.setContentsMargins(
            20,
            16,
            20,
            16,
        )
        context_layout.setHorizontalSpacing(32)
        context_layout.setVerticalSpacing(7)

        self.template_value = self._add_data_field(
            context_layout,
            "Template",
            0,
            0,
        )

        self.template_version_value = self._add_data_field(
            context_layout,
            "Versão do template",
            0,
            1,
        )

        self.scope_value = self._add_data_field(
            context_layout,
            "Escopo",
            0,
            2,
        )

        self.output_value = self._add_data_field(
            context_layout,
            "Fluxo do documento",
            0,
            3,
        )

        for column in range(4):
            context_layout.setColumnStretch(
                column,
                1,
            )

        content_layout.addWidget(
            context_card
        )

        # ---------------------------------------------------------
        # SITUAÇÃO GERAL
        # ---------------------------------------------------------

        self.general_status_card = QFrame()
        self.general_status_card.setObjectName(
            "dashboardCard"
        )

        general_layout = QHBoxLayout(
            self.general_status_card
        )
        general_layout.setContentsMargins(
            24,
            20,
            24,
            20,
        )
        general_layout.setSpacing(18)

        general_text = QVBoxLayout()
        general_text.setSpacing(4)

        self.general_status_title = QLabel(
            "Verificando o processo"
        )
        self.general_status_title.setObjectName(
            "cardTitle"
        )

        self.general_status_description = QLabel(
            "Aguarde enquanto os módulos do processo são validados."
        )
        self.general_status_description.setObjectName(
            "cardDescription"
        )
        self.general_status_description.setWordWrap(
            True
        )

        general_text.addWidget(
            self.general_status_title
        )
        general_text.addWidget(
            self.general_status_description
        )

        self.general_status_badge = QLabel(
            "Verificando"
        )
        self.general_status_badge.setObjectName(
            "statusBadge"
        )

        general_layout.addLayout(
            general_text,
            1,
        )
        general_layout.addWidget(
            self.general_status_badge,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        content_layout.addWidget(
            self.general_status_card
        )

        # ---------------------------------------------------------
        # INDICADORES
        # ---------------------------------------------------------

        indicators_layout = QGridLayout()
        indicators_layout.setHorizontalSpacing(12)
        indicators_layout.setVerticalSpacing(12)

        (
            documents_card,
            self.documents_value,
        ) = self.create_summary_card(
            "Documentos"
        )

        (
            units_card,
            self.units_value,
        ) = self.create_summary_card(
            "Unidades"
        )

        (
            characteristics_card,
            self.characteristics_value,
        ) = self.create_summary_card(
            "Características"
        )

        (
            approved_card,
            self.approved_value,
        ) = self.create_summary_card(
            "Conformes"
        )

        (
            rejected_card,
            self.rejected_value,
        ) = self.create_summary_card(
            "Não conformes"
        )

        (
            images_card,
            self.images_value,
        ) = self.create_summary_card(
            "Imagens"
        )

        indicator_cards = [
            documents_card,
            units_card,
            characteristics_card,
            approved_card,
            rejected_card,
            images_card,
        ]

        for column, card in enumerate(
            indicator_cards
        ):
            indicators_layout.addWidget(
                card,
                0,
                column,
            )
            indicators_layout.setColumnStretch(
                column,
                1,
            )

        content_layout.addLayout(
            indicators_layout
        )

        # ---------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------

        validation_card = QFrame()
        validation_card.setObjectName(
            "formCard"
        )

        validation_layout = QVBoxLayout(
            validation_card
        )
        validation_layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        validation_layout.setSpacing(14)

        validation_title = QLabel(
            "Validação do processo"
        )
        validation_title.setObjectName(
            "formSectionTitle"
        )

        validation_description = QLabel(
            "Os itens obrigatórios devem ser concluídos antes da "
            "pré-visualização. Itens opcionais podem enriquecer "
            "o relatório."
        )
        validation_description.setObjectName(
            "formSectionDescription"
        )
        validation_description.setWordWrap(
            True
        )

        self.validation_container = QWidget()

        self.validation_items_layout = QVBoxLayout(
            self.validation_container
        )
        self.validation_items_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.validation_items_layout.setSpacing(10)

        validation_layout.addWidget(
            validation_title
        )
        validation_layout.addWidget(
            validation_description
        )
        validation_layout.addWidget(
            self.validation_container
        )

        content_layout.addWidget(
            validation_card
        )

        # ---------------------------------------------------------
        # CONTEÚDO DO RELATÓRIO
        # ---------------------------------------------------------

        sections_card = QFrame()
        sections_card.setObjectName(
            "formCard"
        )

        sections_layout = QVBoxLayout(
            sections_card
        )
        sections_layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        sections_layout.setSpacing(15)

        sections_title = QLabel(
            "Conteúdo do relatório"
        )
        sections_title.setObjectName(
            "formSectionTitle"
        )

        sections_description = QLabel(
            "Escolha as informações que serão incluídas no relatório. "
            "A mesma seleção será utilizada na pré-visualização e no "
            "documento final. Seções sem dados permanecem indisponíveis."
        )
        sections_description.setObjectName(
            "formSectionDescription"
        )
        sections_description.setWordWrap(
            True
        )

        sections_layout.addWidget(
            sections_title
        )
        sections_layout.addWidget(
            sections_description
        )

        sections_grid = QGridLayout()
        sections_grid.setHorizontalSpacing(14)
        sections_grid.setVerticalSpacing(12)

        section_definitions = [
            (
                "process_summary",
                "Resumo executivo",
                (
                    "Identificação, imagem principal, template, "
                    "equipamento e indicadores gerais."
                ),
            ),
            (
                "documents",
                "Documentos e unidades",
                (
                    "Arquivos de origem, páginas e identificações "
                    "das unidades analisadas."
                ),
            ),
            (
                "measurement",
                "Informações da medição",
                (
                    "Responsável, equipamento, sensores, alinhamento, "
                    "fixação e instruções."
                ),
            ),
            (
                "characteristics",
                "Resultados metrológicos",
                (
                    "Resultados, tolerâncias, estatísticas, gráficos "
                    "e interpretação por característica."
                ),
            ),
            (
                "images",
                "Imagens técnicas",
                (
                    "Fotografias, CAD, renders, setup, fixação "
                    "e evidências anotadas."
                ),
            ),
            (
                "observations",
                "Observações técnicas",
                (
                    "Condições especiais, ressalvas e notas "
                    "da elaboração ou revisão."
                ),
            ),
            (
                "technical_control",
                "Elaboração e aprovação",
                (
                    "Responsáveis, datas, situação da revisão "
                    "e controle técnico."
                ),
            ),
            (
                self.VERSION_SECTION_KEY,
                "Identificação da versão",
                (
                    "Exibe a versão do relatório no documento entregue. "
                    "A rastreabilidade interna continua sendo mantida "
                    "mesmo quando esta opção estiver desmarcada."
                ),
            ),
        ]

        for index, (
            key,
            title,
            description,
        ) in enumerate(
            section_definitions
        ):
            row = (
                index // 2
            )
            column = (
                index % 2
            )

            sections_grid.addWidget(
                self.create_section_option(
                    key=key,
                    title=title,
                    description=description,
                ),
                row,
                column,
            )

        sections_grid.setColumnStretch(
            0,
            1,
        )
        sections_grid.setColumnStretch(
            1,
            1,
        )

        sections_layout.addLayout(
            sections_grid
        )

        content_layout.addWidget(
            sections_card
        )

        # ---------------------------------------------------------
        # RESUMO
        # ---------------------------------------------------------

        preview_card = QFrame()
        preview_card.setObjectName(
            "formCard"
        )

        preview_layout = QVBoxLayout(
            preview_card
        )
        preview_layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        preview_layout.setSpacing(10)

        preview_title = QLabel(
            "Resumo do relatório"
        )
        preview_title.setObjectName(
            "formSectionTitle"
        )

        self.preview_description = QLabel(
            "O resumo será atualizado após a validação do processo."
        )
        self.preview_description.setObjectName(
            "cardDescription"
        )
        self.preview_description.setWordWrap(
            True
        )

        preview_layout.addWidget(
            preview_title
        )
        preview_layout.addWidget(
            self.preview_description
        )

        content_layout.addWidget(
            preview_card
        )

        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.back_action_button = QPushButton(
            "Voltar"
        )
        self.back_action_button.setObjectName(
            "secondaryButton"
        )
        self.back_action_button.setMinimumHeight(
            44
        )
        self.back_action_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.back_action_button.clicked.connect(
            self.back_requested.emit
        )

        self.generate_button = QPushButton(
            "Gerar pré-visualização"
        )
        self.generate_button.setObjectName(
            "primaryButton"
        )
        self.generate_button.setMinimumHeight(
            44
        )
        self.generate_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.generate_button.clicked.connect(
            self.request_generation
        )

        actions.addStretch()
        actions.addWidget(
            self.back_action_button
        )
        actions.addWidget(
            self.generate_button
        )

        content_layout.addLayout(
            actions
        )

        # ---------------------------------------------------------
        # CENTRALIZAÇÃO
        # ---------------------------------------------------------

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(
            content,
            10,
        )
        row.addStretch(1)

        scroll_layout.addLayout(
            row
        )
        scroll_layout.addSpacing(
            20
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

    def _add_data_field(
        self,
        layout: QGridLayout,
        title: str,
        row: int,
        column: int,
    ) -> QLabel:
        title_label = QLabel(
            title
        )
        title_label.setObjectName(
            "dataLabel"
        )

        value_label = QLabel(
            "-"
        )
        value_label.setObjectName(
            "dataValue"
        )
        value_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label,
            row,
            column,
        )
        layout.addWidget(
            value_label,
            row + 1,
            column,
        )

        return value_label

    def create_summary_card(
        self,
        title: str,
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
        layout.setSpacing(4)

        label = QLabel(
            title
        )
        label.setObjectName(
            "dataLabel"
        )
        label.setWordWrap(
            True
        )

        value = QLabel(
            "0"
        )
        value.setObjectName(
            "summaryValue"
        )

        layout.addWidget(
            label
        )
        layout.addWidget(
            value
        )

        return (
            card,
            value,
        )

    def create_section_option(
        self,
        key: str,
        title: str,
        description: str,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName(
            "documentListItem"
        )

        layout = QHBoxLayout(
            frame
        )
        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )
        layout.setSpacing(12)

        checkbox = QCheckBox()
        checkbox.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        checkbox.stateChanged.connect(
            self.update_preview_from_selection
        )

        self.section_inputs[
            key
        ] = checkbox

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_label = QLabel(
            title
        )
        title_label.setObjectName(
            "cardTitle"
        )

        description_label = QLabel(
            description
        )
        description_label.setObjectName(
            "cardDescription"
        )
        description_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            title_label
        )
        text_layout.addWidget(
            description_label
        )

        layout.addWidget(
            checkbox,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        layout.addLayout(
            text_layout,
            1,
        )

        return frame

    def create_validation_row(
        self,
        item: dict[str, Any],
    ) -> QFrame:
        row = QFrame()
        row.setObjectName(
            "documentListItem"
        )

        layout = QHBoxLayout(
            row
        )
        layout.setContentsMargins(
            16,
            13,
            16,
            13,
        )
        layout.setSpacing(14)

        status = item[
            "status"
        ]
        required = bool(
            item.get(
                "required",
                False,
            )
        )

        if status == "complete":
            symbol = "✓"
            status_text = "Concluído"
            badge_name = (
                "statusBadgeSuccess"
            )
        else:
            symbol = "!"
            status_text = (
                "Obrigatório"
                if required
                else "Opcional"
            )
            badge_name = (
                "statusBadgeWarning"
            )

        symbol_label = QLabel(
            symbol
        )
        symbol_label.setObjectName(
            "documentOrder"
        )
        symbol_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        symbol_label.setFixedSize(
            40,
            40,
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel(
            item[
                "title"
            ]
        )
        title.setObjectName(
            "cardTitle"
        )

        description = QLabel(
            item[
                "message"
            ]
        )
        description.setObjectName(
            "cardDescription"
        )
        description.setWordWrap(
            True
        )

        text_layout.addWidget(
            title
        )
        text_layout.addWidget(
            description
        )

        status_label = QLabel(
            status_text
        )
        status_label.setObjectName(
            badge_name
        )

        action_button = (
            self.create_validation_action(
                item[
                    "key"
                ]
            )
        )

        layout.addWidget(
            symbol_label
        )
        layout.addLayout(
            text_layout,
            1,
        )
        layout.addWidget(
            status_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        if action_button is not None:
            layout.addWidget(
                action_button,
                alignment=Qt.AlignmentFlag.AlignTop,
            )

        return row

    def create_validation_action(
        self,
        key: str,
    ) -> QPushButton | None:
        actions = {
            "documents": (
                "Abrir documentos",
                self.documents_requested.emit,
            ),
            "characteristics": (
                "Ver características",
                self.characteristics_requested.emit,
            ),
            "measurement": (
                "Completar medição",
                self.measurement_requested.emit,
            ),
            "images": (
                "Abrir imagens",
                self.images_requested.emit,
            ),
            "primary_image": (
                "Selecionar imagem",
                self.images_requested.emit,
            ),
            "technical_control": (
                "Abrir controle",
                self.technical_control_requested.emit,
            ),
        }

        action = actions.get(
            key
        )

        if action is None:
            return None

        text, callback = (
            action
        )

        button = QPushButton(
            text
        )
        button.setObjectName(
            "cardButton"
        )
        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        button.clicked.connect(
            callback
        )

        return button

    # =============================================================
    # PROJETO E CONTEXTO
    # =============================================================

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = (
            project
        )

        self.page_header.set_metadata(
            (
                f"{project.report_id} "
                f"· {project.name}"
            )
        )

        self.template_value.setText(
            self._get_template_name(
                project.template
            )
        )

        self.template_version_value.setText(
            project.template_version
            or "1.0"
        )

        self.output_value.setText(
            "Pré-visualização → aprovação → exportação"
        )

        self.load_context()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

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
                self.service.get_report_context(
                    self.current_project
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao validar relatório",
                (
                    "Não foi possível preparar o contexto "
                    f"do relatório.\n\nDetalhes: {error}"
                ),
            )
            return

        self.current_context = (
            context
        )

        self.populate_scope(
            context
        )
        self.populate_summary(
            context
        )
        self.populate_validation(
            context
        )
        self.populate_sections(
            context
        )
        self.populate_general_status(
            context
        )
        self.populate_preview_summary(
            context
        )

    # =============================================================
    # PREENCHIMENTO
    # =============================================================

    def populate_scope(
        self,
        context: dict[str, Any],
    ) -> None:
        is_batch = bool(
            context.get(
                "is_batch",
                False,
            )
        )

        document_summary = context.get(
            "document_summary",
            {},
        )

        unit_count = int(
            document_summary.get(
                "unit_count",
                0,
            )
            or 0
        )

        if is_batch:
            scope = (
                "Relatório consolidado de lote "
                f"· {unit_count} unidade(s)"
            )
        else:
            scope = (
                "Relatório de peça única"
            )

        self.scope_value.setText(
            scope
        )

    def populate_summary(
        self,
        context: dict[str, Any],
    ) -> None:
        documents = context[
            "document_summary"
        ]
        characteristics = context[
            "characteristic_summary"
        ]
        images = context[
            "image_summary"
        ]

        self.documents_value.setText(
            str(
                documents[
                    "total"
                ]
            )
        )

        self.units_value.setText(
            str(
                documents.get(
                    "unit_count",
                    documents[
                        "total"
                    ],
                )
            )
        )

        self.characteristics_value.setText(
            str(
                characteristics[
                    "total"
                ]
            )
        )

        self.approved_value.setText(
            str(
                characteristics[
                    "ok"
                ]
            )
        )

        self.rejected_value.setText(
            str(
                characteristics[
                    "nok"
                ]
            )
        )

        self.images_value.setText(
            str(
                images[
                    "total"
                ]
            )
        )

    def populate_validation(
        self,
        context: dict[str, Any],
    ) -> None:
        self.clear_layout(
            self.validation_items_layout
        )

        for item in context[
            "validation_items"
        ]:
            self.validation_items_layout.addWidget(
                self.create_validation_row(
                    item
                )
            )

    def populate_sections(
        self,
        context: dict[str, Any],
    ) -> None:
        available_sections = context[
            "available_sections"
        ]
        default_sections = context[
            "default_sections"
        ]

        for (
            key,
            checkbox,
        ) in self.section_inputs.items():
            checkbox.blockSignals(
                True
            )

            if (
                key
                == self.VERSION_SECTION_KEY
            ):
                checkbox.setEnabled(
                    True
                )
                checkbox.setChecked(
                    False
                )
                checkbox.blockSignals(
                    False
                )
                continue

            available = bool(
                available_sections.get(
                    key,
                    False,
                )
            )

            checked = bool(
                default_sections.get(
                    key,
                    False,
                )
            )

            checkbox.setEnabled(
                available
            )

            checkbox.setChecked(
                available
                and checked
            )

            checkbox.blockSignals(
                False
            )

    def populate_general_status(
        self,
        context: dict[str, Any],
    ) -> None:
        blocking_count = len(
            context[
                "blocking_items"
            ]
        )

        warning_count = len(
            context[
                "warning_items"
            ]
        )

        if blocking_count == 0:
            self.general_status_title.setText(
                "Processo pronto para pré-visualização"
            )

            if warning_count == 0:
                description = (
                    "Todos os itens obrigatórios e opcionais "
                    "foram preenchidos."
                )
            else:
                description = (
                    "Os itens obrigatórios estão concluídos. "
                    f"Há {warning_count} item(ns) opcional(is) "
                    "pendente(s)."
                )

            self.general_status_description.setText(
                description
            )

            self.general_status_badge.setText(
                "Pronto"
            )

            self.general_status_badge.setObjectName(
                "statusBadgeSuccess"
            )

        else:
            self.general_status_title.setText(
                "O processo ainda possui pendências"
            )

            self.general_status_description.setText(
                (
                    f"{blocking_count} item(ns) obrigatório(s) "
                    "precisa(m) ser concluído(s) antes da "
                    "pré-visualização."
                )
            )

            self.general_status_badge.setText(
                "Pendente"
            )

            self.general_status_badge.setObjectName(
                "statusBadgeWarning"
            )

        self.general_status_badge.style().unpolish(
            self.general_status_badge
        )

        self.general_status_badge.style().polish(
            self.general_status_badge
        )

        self.generate_button.setEnabled(
            bool(
                context[
                    "can_generate"
                ]
            )
        )

    def populate_preview_summary(
        self,
        context: dict[str, Any],
    ) -> None:
        project = context[
            "project"
        ]
        documents = context[
            "document_summary"
        ]
        characteristics = context[
            "characteristic_summary"
        ]
        images = context[
            "image_summary"
        ]
        control = context[
            "control_summary"
        ]

        selected_content_count = sum(
            1
            for (
                key,
                checkbox,
            ) in self.section_inputs.items()
            if (
                key
                != self.VERSION_SECTION_KEY
                and checkbox.isEnabled()
                and checkbox.isChecked()
            )
        )

        show_version = (
            self.section_inputs[
                self.VERSION_SECTION_KEY
            ].isChecked()
        )

        scope_text = (
            (
                "Um PDF consolidado será montado "
                f"para {documents.get('unit_count', 0)} "
                "unidade(s)."
            )
            if context.get(
                "is_batch",
                False,
            )
            else (
                "Um PDF técnico será montado "
                "para a peça única."
            )
        )

        primary_text = (
            "Imagem principal definida."
            if images.get(
                "has_primary",
                False,
            )
            else (
                "Imagem principal não definida."
            )
        )

        version_text = (
            "A identificação da versão será exibida no PDF."
            if show_version
            else (
                "A versão será mantida apenas para "
                "rastreabilidade interna."
            )
        )

        parts = [
            (
                f"Processo {project.report_id}: "
                f"{project.name}."
            ),
            scope_text,
            (
                f"{documents['total']} documento(s) de origem "
                f"e {documents['pages']} página(s)."
            ),
            (
                f"{characteristics['total']} característica(s): "
                f"{characteristics['ok']} conforme(s) e "
                f"{characteristics['nok']} não conforme(s)."
            ),
            (
                f"{images['total']} imagem(ns). "
                f"{primary_text}"
            ),
            (
                f"Controle técnico: {control['status']}."
            ),
            (
                f"{selected_content_count} módulo(s) de conteúdo "
                "será(ão) incluído(s)."
            ),
            version_text,
            (
                "A pré-visualização será gerada antes da "
                "aprovação e exportação."
            ),
        ]

        self.preview_description.setText(
            "\n".join(
                parts
            )
        )

    def update_preview_from_selection(
        self,
    ) -> None:
        if self.current_context:
            self.populate_preview_summary(
                self.current_context
            )

    # =============================================================
    # SOLICITAÇÃO
    # =============================================================

    def request_generation(
        self,
    ) -> None:
        if not self.current_context:
            return

        if not self.current_context.get(
            "can_generate",
            False,
        ):
            QMessageBox.warning(
                self,
                "Processo incompleto",
                (
                    "Conclua os itens obrigatórios antes "
                    "de gerar a pré-visualização."
                ),
            )
            return

        selected_sections = {
            key:
                checkbox.isChecked()
            for (
                key,
                checkbox,
            ) in self.section_inputs.items()
            if checkbox.isEnabled()
        }

        content_sections = {
            key:
                selected
            for (
                key,
                selected,
            ) in selected_sections.items()
            if (
                key
                != self.VERSION_SECTION_KEY
            )
        }

        if not any(
            content_sections.values()
        ):
            QMessageBox.warning(
                self,
                "Nenhuma seção selecionada",
                (
                    "Selecione pelo menos uma seção "
                    "para gerar a pré-visualização."
                ),
            )
            return

        payload = {
            "project":
                self.current_project,

            "context":
                self.current_context,

            "sections":
                selected_sections,
        }

        self.generate_requested.emit(
            payload
        )

    def set_generating(
        self,
        generating: bool,
    ) -> None:
        self.generate_button.setEnabled(
            (
                not generating
                and bool(
                    self.current_context.get(
                        "can_generate",
                        False,
                    )
                )
            )
        )

        self.refresh_button.setEnabled(
            not generating
        )

        self.back_action_button.setEnabled(
            not generating
        )

        self.generate_button.setText(
            (
                "Gerando pré-visualização..."
                if generating
                else "Gerar pré-visualização"
            )
        )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

    def _get_template_name(
        self,
        template_code: str,
    ) -> str:
        try:
            return get_template_definition(
                template_code
            ).name

        except ValueError:
            return (
                template_code
                or "Template não informado"
            )

    def clear_layout(
        self,
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(
                0
            )

            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()

            elif child_layout is not None:
                self.clear_layout(
                    child_layout
                )