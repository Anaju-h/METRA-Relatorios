from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.components.page_header import PageHeader
from ui.components.step_indicator import StepIndicator


class ProjectReviewStep(QWidget):
    """
    Etapa responsável pela revisão dos documentos
    analisados antes da criação definitiva do processo.

    Aqui o usuário confirma as informações extraídas
    automaticamente pelo METRA antes de continuar.
    """

    back_requested = Signal()

    continue_requested = Signal()

    restart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.documents = []

        self.setObjectName("pageBackground")

        self.build_ui()
    def build_ui(self):

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        container = QWidget()

        container.setObjectName("pageBackground")

        layout = QVBoxLayout(container)

        layout.setContentsMargins(
            34,
            22,
            34,
            34,
        )

        layout.setSpacing(18)

        self.header = PageHeader(

            title="Revisão dos documentos",

            subtitle=(
                "Confira as informações "
                "identificadas automaticamente "
                "antes de criar o processo."
            ),

            back_text="← Voltar",
        )

        self.header.back_button.clicked.connect(
            self.back_requested.emit
        )

        layout.addWidget(self.header)

        self.step_indicator = StepIndicator(

            [
                "Documentos",
                "Revisão",
                "Criar",
            ],

            current_step=1,
        )

        layout.addWidget(self.step_indicator)
        # ---------------------------------------------------------
        # RESUMO DA ANÁLISE
        # ---------------------------------------------------------

        self.summary_card = QFrame()
        self.summary_card.setObjectName("dashboardCard")

        summary_layout = QVBoxLayout(
            self.summary_card
        )

        summary_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        summary_layout.setSpacing(14)

        summary_title = QLabel(
            "Resumo da análise"
        )

        summary_title.setObjectName(
            "formSectionTitle"
        )

        summary_description = QLabel(
            (
                "Confira os principais dados identificados "
                "nos relatórios antes de continuar."
            )
        )

        summary_description.setObjectName(
            "formSectionDescription"
        )

        summary_description.setWordWrap(
            True
        )

        summary_layout.addWidget(
            summary_title
        )

        summary_layout.addWidget(
            summary_description
        )

        metrics_layout = QHBoxLayout()

        metrics_layout.setSpacing(
            12
        )

        self.documents_metric = (
            self.create_metric_card(
                title="Documentos",
                value="0",
                helper="Arquivos analisados",
                accent="blue",
            )
        )

        self.characteristics_metric = (
            self.create_metric_card(
                title="Características",
                value="0",
                helper="Resultados identificados",
                accent="navy",
            )
        )

        self.success_metric = (
            self.create_metric_card(
                title="Concluídos",
                value="0",
                helper="Análises realizadas",
                accent="blue",
            )
        )

        self.warning_metric = (
            self.create_metric_card(
                title="Pendências",
                value="0",
                helper="Itens que exigem revisão",
                accent="orange",
            )
        )

        metrics_layout.addWidget(
            self.documents_metric
        )

        metrics_layout.addWidget(
            self.characteristics_metric
        )

        metrics_layout.addWidget(
            self.success_metric
        )

        metrics_layout.addWidget(
            self.warning_metric
        )

        summary_layout.addLayout(
            metrics_layout
        )

        layout.addWidget(
            self.summary_card
        )
        # ---------------------------------------------------------
        # CONTEXTO IDENTIFICADO
        # ---------------------------------------------------------

        self.context_card = QFrame()

        self.context_card.setObjectName(
            "formCard"
        )

        context_layout = QVBoxLayout(
            self.context_card
        )

        context_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        context_layout.setSpacing(
            14
        )

        context_title = QLabel(
            "Contexto identificado"
        )

        context_title.setObjectName(
            "formSectionTitle"
        )

        context_description = QLabel(
            (
                "Essas informações serão usadas para sugerir "
                "o tipo de inspeção e o template do relatório."
            )
        )

        context_description.setObjectName(
            "formSectionDescription"
        )

        context_description.setWordWrap(
            True
        )

        context_layout.addWidget(
            context_title
        )

        context_layout.addWidget(
            context_description
        )

        context_grid = QHBoxLayout()

        context_grid.setSpacing(
            12
        )

        self.process_type_box = (
            self.create_context_box(
                title="Modo da análise",
                value="-",
            )
        )

        self.equipment_box = (
            self.create_context_box(
                title="Equipamento identificado",
                value="-",
            )
        )

        self.software_box = (
            self.create_context_box(
                title="Software de origem",
                value="-",
            )
        )

        context_grid.addWidget(
            self.process_type_box
        )

        context_grid.addWidget(
            self.equipment_box
        )

        context_grid.addWidget(
            self.software_box
        )

        context_layout.addLayout(
            context_grid
        )

        self.model_label = QLabel(
            ""
        )

        self.model_label.setObjectName(
            "analysisModel"
        )

        self.model_label.setWordWrap(
            True
        )

        self.model_label.hide()

        self.warning_label = QLabel(
            ""
        )

        self.warning_label.setObjectName(
            "analysisWarning"
        )

        self.warning_label.setWordWrap(
            True
        )

        self.warning_label.hide()

        context_layout.addWidget(
            self.model_label
        )

        context_layout.addWidget(
            self.warning_label
        )

        layout.addWidget(
            self.context_card
        )
        # ---------------------------------------------------------
        # DOCUMENTOS ANALISADOS
        # ---------------------------------------------------------

        self.documents_card = QFrame()

        self.documents_card.setObjectName(
            "formCard"
        )

        documents_layout = QVBoxLayout(
            self.documents_card
        )

        documents_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        documents_layout.setSpacing(
            14
        )

        title = QLabel(
            "Documentos analisados"
        )

        title.setObjectName(
            "formSectionTitle"
        )

        subtitle = QLabel(
            (
                "Cada documento importado é exibido abaixo "
                "com o resultado da análise automática."
            )
        )

        subtitle.setObjectName(
            "formSectionDescription"
        )

        subtitle.setWordWrap(
            True
        )

        documents_layout.addWidget(
            title
        )

        documents_layout.addWidget(
            subtitle
        )

        self.documents_container = QWidget()

        self.documents_list_layout = QVBoxLayout(
            self.documents_container
        )

        self.documents_list_layout.setSpacing(
            10
        )

        self.documents_list_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        documents_layout.addWidget(
            self.documents_container
        )

        layout.addWidget(
            self.documents_card
        )
        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        buttons = QHBoxLayout()

        buttons.setSpacing(
            10
        )

        self.restart_button = QPushButton(
            "Importar novamente"
        )

        self.restart_button.setObjectName(
            "secondaryButton"
        )

        self.restart_button.setMinimumHeight(
            44
        )

        self.restart_button.clicked.connect(
            self.restart_requested.emit
        )

        buttons.addWidget(
            self.restart_button
        )

        buttons.addStretch()

        self.continue_button = QPushButton(
            "Continuar"
        )

        self.continue_button.setObjectName(
            "primaryButton"
        )

        self.continue_button.setMinimumHeight(
            44
        )

        self.continue_button.clicked.connect(
            self.continue_requested.emit
        )

        buttons.addWidget(
            self.continue_button
        )

        layout.addLayout(
            buttons
        )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        root_layout.addWidget(
            scroll
        )
    # =============================================================
    # COMPONENTES AUXILIARES
    # =============================================================

    def create_metric_card(
        self,
        *,
        title: str,
        value: str,
        helper: str,
        accent: str,
    ) -> QFrame:
        card = QFrame()

        card.setObjectName(
            "metricCard"
        )

        card.setProperty(
            "accent",
            accent,
        )

        card.setMinimumHeight(
            112
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
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

        layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "metricLabel"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "metricValue"
        )

        helper_label = QLabel(
            helper
        )

        helper_label.setObjectName(
            "metricHelper"
        )

        helper_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            helper_label
        )

        card.value_label = (
            value_label
        )

        card.helper_label = (
            helper_label
        )

        return card

    def create_context_box(
        self,
        *,
        title: str,
        value: str,
    ) -> QFrame:
        box = QFrame()

        box.setObjectName(
            "documentListCard"
        )

        box.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(
            box
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(
            5
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
            "dataValue"
        )

        value_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        box.value_label = (
            value_label
        )

        return box

    def create_document_card(
        self,
        document,
    ) -> QFrame:
        card = QFrame()

        card.setObjectName(
            "analyzedDocumentCard"
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        layout.setSpacing(
            16
        )

        order = getattr(
            document,
            "document_order",
            0,
        )

        order_label = QLabel(
            f"{order:02d}"
        )

        order_label.setObjectName(
            "documentOrder"
        )

        information_layout = QVBoxLayout()

        information_layout.setSpacing(
            5
        )

        file_name = QLabel(
            getattr(
                document,
                "file_name",
                "Documento sem nome",
            )
        )

        file_name.setObjectName(
            "cardTitle"
        )

        file_name.setWordWrap(
            True
        )

        failed = bool(
            getattr(
                document,
                "failed",
                False,
            )
        )

        details: list[str] = []

        part_name = getattr(
            document,
            "part_name",
            None,
        )

        equipment = getattr(
            document,
            "equipment",
            None,
        )

        measurement_count = getattr(
            document,
            "measurement_count",
            None,
        )

        characteristics_count = getattr(
            document,
            "characteristics_count",
            0,
        )

        if failed:
            details.append(
                "A análise automática não foi concluída."
            )

            error_message = getattr(
                document,
                "analysis_message",
                None,
            )

            if error_message:
                details.append(
                    str(
                        error_message
                    )
                )

        else:
            if part_name:
                details.append(
                    f"Peça: {part_name}"
                )

            if equipment:
                details.append(
                    f"Equipamento: {equipment}"
                )

            if (
                measurement_count
                is not None
            ):
                details.append(
                    (
                        "Medições: "
                        f"{measurement_count}"
                    )
                )

            details.append(
                (
                    "Características: "
                    f"{characteristics_count}"
                )
            )

        details_label = QLabel(
            " · ".join(
                details
            )
        )

        details_label.setObjectName(
            "cardDescription"
        )

        details_label.setWordWrap(
            True
        )

        information_layout.addWidget(
            file_name
        )

        information_layout.addWidget(
            details_label
        )

        status_label = QLabel(
            (
                "Falha"
                if failed
                else "Concluído"
            )
        )

        status_label.setObjectName(
            (
                "documentFailureBadge"
                if failed
                else "documentSuccessBadge"
            )
        )

        layout.addWidget(
            order_label
        )

        layout.addLayout(
            information_layout,
            1,
        )

        layout.addWidget(
            status_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        return card
    # =============================================================
    # ATUALIZAÇÃO DA REVISÃO
    # =============================================================

    def set_draft(
        self,
        draft,
    ) -> None:
        self.documents = list(
            getattr(
                draft,
                "documents",
                [],
            )
        )

        document_count = int(
            getattr(
                draft,
                "document_count",
                len(
                    self.documents
                ),
            )
            or 0
        )

        characteristics_count = int(
            getattr(
                draft,
                "characteristics_count",
                0,
            )
            or 0
        )

        successful_count = int(
            getattr(
                draft,
                "analyzed_document_count",
                0,
            )
            or 0
        )

        failed_count = int(
            getattr(
                draft,
                "failed_document_count",
                0,
            )
            or 0
        )

        warnings = list(
            getattr(
                draft,
                "warnings",
                [],
            )
            or []
        )

        pending_count = (
            failed_count
            + len(
                warnings
            )
        )

        self.documents_metric.value_label.setText(
            str(
                document_count
            )
        )

        self.characteristics_metric.value_label.setText(
            str(
                characteristics_count
            )
        )

        self.success_metric.value_label.setText(
            str(
                successful_count
            )
        )

        self.warning_metric.value_label.setText(
            str(
                pending_count
            )
        )

        process_type_label = (
            draft.get_process_type_label()
            if hasattr(
                draft,
                "get_process_type_label",
            )
            else (
                "Lote de peças"
                if getattr(
                    draft,
                    "is_batch",
                    False,
                )
                else "Peça única"
            )
        )

        self.process_type_box.value_label.setText(
            process_type_label
        )

        equipments = list(
            getattr(
                draft,
                "equipments",
                [],
            )
            or []
        )

        equipment = getattr(
            draft,
            "equipment",
            None,
        )

        if len(
            equipments
        ) > 1:
            equipment_text = ", ".join(
                equipments
            )

        elif equipment:
            equipment_text = str(
                equipment
            )

        else:
            equipment_text = (
                "Não identificado"
            )

        self.equipment_box.value_label.setText(
            equipment_text
        )

        software_values: list[str] = []

        for document in self.documents:
            software_name = getattr(
                document,
                "software_name",
                None,
            )

            software_version = getattr(
                document,
                "software_version",
                None,
            )

            if not software_name:
                continue

            software_text = str(
                software_name
            )

            if software_version:
                software_text += (
                    f" {software_version}"
                )

            if (
                software_text
                not in software_values
            ):
                software_values.append(
                    software_text
                )

        self.software_box.value_label.setText(
            (
                ", ".join(
                    software_values
                )
                if software_values
                else "Não identificado"
            )
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

        identified_part = (
            base_part_name
            or part_name
        )

        if identified_part:
            label_prefix = (
                "Modelo identificado"
                if getattr(
                    draft,
                    "is_batch",
                    False,
                )
                else "Peça identificada"
            )

            self.model_label.setText(
                (
                    f"{label_prefix}: "
                    f"{identified_part}"
                )
            )

            self.model_label.show()

        else:
            self.model_label.clear()
            self.model_label.hide()

        if warnings:
            self.warning_label.setText(
                (
                    "Atenção: "
                    + " ".join(
                        str(
                            warning
                        )
                        for warning in warnings
                    )
                )
            )

            self.warning_label.show()

        else:
            self.warning_label.clear()
            self.warning_label.hide()

        self.refresh_documents()

        can_continue = (
            document_count > 0
            and successful_count > 0
        )

        self.continue_button.setEnabled(
            can_continue
        )

    def refresh_documents(
        self,
    ) -> None:
        self.clear_layout(
            self.documents_list_layout
        )

        if not self.documents:
            empty_label = QLabel(
                "Nenhum documento analisado."
            )

            empty_label.setObjectName(
                "emptyState"
            )

            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.documents_list_layout.addWidget(
                empty_label
            )

            return

        for document in self.documents:
            self.documents_list_layout.addWidget(
                self.create_document_card(
                    document
                )
            )

    # =============================================================
    # ESTADO DA TELA
    # =============================================================

    def set_loading(
        self,
        loading: bool,
    ) -> None:
        self.continue_button.setEnabled(
            not loading
            and bool(
                self.documents
            )
        )

        self.restart_button.setEnabled(
            not loading
        )

        self.continue_button.setText(
            (
                "Carregando..."
                if loading
                else "Continuar"
            )
        )

    def reset_step(
        self,
    ) -> None:
        self.documents = []

        self.documents_metric.value_label.setText(
            "0"
        )

        self.characteristics_metric.value_label.setText(
            "0"
        )

        self.success_metric.value_label.setText(
            "0"
        )

        self.warning_metric.value_label.setText(
            "0"
        )

        self.process_type_box.value_label.setText(
            "-"
        )

        self.equipment_box.value_label.setText(
            "-"
        )

        self.software_box.value_label.setText(
            "-"
        )

        self.model_label.clear()
        self.model_label.hide()

        self.warning_label.clear()
        self.warning_label.hide()

        self.continue_button.setEnabled(
            False
        )

        self.refresh_documents()

    # =============================================================
    # LIMPEZA DE LAYOUT
    # =============================================================

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