from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.project_service import (
    ProjectService,
)
from services.report_templates.template_catalog import (
    get_template_definition,
)


class ProcessesPage(QWidget):
    """
    Central de processos do METRA.

    Permite pesquisar, filtrar e abrir qualquer processo cadastrado.
    """

    back_requested = Signal()
    refresh_requested = Signal()
    new_project_requested = Signal()
    open_project_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.all_projects: list[Project] = []
        self.project_service = ProjectService()

        self.setObjectName("pageBackground")
        self._build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def _build_ui(self) -> None:
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
        scroll_layout.setSpacing(18)

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

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        back_button = QPushButton("← Início")
        back_button.setObjectName("backButton")
        back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        back_button.clicked.connect(
            self.back_requested.emit
        )

        self.new_project_button = QPushButton(
            "+ Novo processo"
        )
        self.new_project_button.setObjectName(
            "primaryButton"
        )
        self.new_project_button.setMinimumHeight(
            38
        )
        self.new_project_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.new_project_button.clicked.connect(
            self.new_project_requested.emit
        )

        refresh_button = QPushButton(
            "Atualizar lista"
        )
        refresh_button.setObjectName(
            "secondaryButton"
        )
        refresh_button.setMinimumHeight(
            38
        )
        refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        refresh_button.clicked.connect(
            self.refresh_requested.emit
        )

        top_row.addWidget(back_button)
        top_row.addStretch()
        top_row.addWidget(
            self.new_project_button
        )
        top_row.addWidget(refresh_button)

        content_layout.addLayout(top_row)

        title = QLabel("Central de processos")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Consulte todos os processos cadastrados, aplique filtros "
            "e continue exatamente de onde o trabalho foi interrompido."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)

        # ---------------------------------------------------------
        # FILTROS
        # ---------------------------------------------------------

        filters_card = QFrame()
        filters_card.setObjectName("formCard")

        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(20, 16, 20, 16)
        filters_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Pesquisar por ID, processo, peça, código ou cliente..."
        )
        self.search_input.setClearButtonEnabled(True)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos os status", "")

        self.inspection_filter = QComboBox()
        self.inspection_filter.addItem(
            "Todos os tipos de inspeção",
            "",
        )

        self.template_filter = QComboBox()
        self.template_filter.addItem(
            "Todos os templates",
            "",
        )

        filters_layout.addWidget(self.search_input, 3)
        filters_layout.addWidget(self.status_filter, 1)
        filters_layout.addWidget(self.inspection_filter, 1)
        filters_layout.addWidget(self.template_filter, 1)

        content_layout.addWidget(filters_card)

        # ---------------------------------------------------------
        # RESUMO
        # ---------------------------------------------------------

        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)

        self.total_label = QLabel("0 processos")
        self.total_label.setObjectName("sectionTitle")

        self.result_label = QLabel("0 exibidos")
        self.result_label.setObjectName("sectionDescription")

        summary_row.addWidget(self.total_label)
        summary_row.addWidget(self.result_label)
        summary_row.addStretch()

        content_layout.addLayout(summary_row)

        # ---------------------------------------------------------
        # LISTA
        # ---------------------------------------------------------

        self.projects_container = QWidget()
        self.projects_container.setObjectName(
            "recentProjectsContainer"
        )
        self.projects_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.projects_layout = QVBoxLayout(
            self.projects_container
        )
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(10)

        content_layout.addWidget(self.projects_container)
        content_layout.addStretch()

        centered_row = QHBoxLayout()
        centered_row.addStretch()
        centered_row.addWidget(content, 12)
        centered_row.addStretch()

        scroll_layout.addLayout(centered_row)

        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area)

        self.search_input.textChanged.connect(
            self.apply_filters
        )
        self.status_filter.currentIndexChanged.connect(
            self.apply_filters
        )
        self.inspection_filter.currentIndexChanged.connect(
            self.apply_filters
        )
        self.template_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self._show_empty_state(
            "Nenhum processo cadastrado ainda."
        )

    # =============================================================
    # DADOS
    # =============================================================

    def set_projects(
        self,
        projects: list[Project],
    ) -> None:
        self.all_projects = list(projects)

        self._populate_filters()
        self.apply_filters()

        self.scroll_area.verticalScrollBar().setValue(0)

    def _populate_filters(self) -> None:
        current_status = self.status_filter.currentData()
        current_inspection = self.inspection_filter.currentData()
        current_template = self.template_filter.currentData()

        statuses = sorted(
            {
                project.status
                for project in self.all_projects
                if project.status
            }
        )

        inspections = sorted(
            {
                project.inspection_type
                for project in self.all_projects
                if project.inspection_type
            }
        )

        templates = sorted(
            {
                project.template
                for project in self.all_projects
                if project.template
            }
        )

        self.status_filter.blockSignals(True)
        self.inspection_filter.blockSignals(True)
        self.template_filter.blockSignals(True)

        self.status_filter.clear()
        self.status_filter.addItem("Todos os status", "")
        for status in statuses:
            self.status_filter.addItem(status, status)

        self.inspection_filter.clear()
        self.inspection_filter.addItem(
            "Todos os tipos de inspeção",
            "",
        )
        for inspection in inspections:
            self.inspection_filter.addItem(
                inspection,
                inspection,
            )

        self.template_filter.clear()
        self.template_filter.addItem(
            "Todos os templates",
            "",
        )
        for template_code in templates:
            self.template_filter.addItem(
                self._template_name(template_code),
                template_code,
            )

        self._restore_filter(
            self.status_filter,
            current_status,
        )
        self._restore_filter(
            self.inspection_filter,
            current_inspection,
        )
        self._restore_filter(
            self.template_filter,
            current_template,
        )

        self.status_filter.blockSignals(False)
        self.inspection_filter.blockSignals(False)
        self.template_filter.blockSignals(False)

    def _restore_filter(
        self,
        combo: QComboBox,
        value,
    ) -> None:
        index = combo.findData(value)

        combo.setCurrentIndex(
            index if index >= 0 else 0
        )

    # =============================================================
    # FILTROS
    # =============================================================

    def apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        status = str(
            self.status_filter.currentData()
            or ""
        )
        inspection_type = str(
            self.inspection_filter.currentData()
            or ""
        )
        template = str(
            self.template_filter.currentData()
            or ""
        )

        filtered: list[Project] = []

        for project in self.all_projects:
            searchable_values = [
                project.report_id,
                project.name,
                project.part_name,
                project.part_code,
                project.client,
                project.equipment,
                project.inspection_type,
                self._template_name(project.template),
            ]

            searchable_text = " ".join(
                str(value or "")
                for value in searchable_values
            ).lower()

            if query and query not in searchable_text:
                continue

            if status and project.status != status:
                continue

            if (
                inspection_type
                and project.inspection_type
                != inspection_type
            ):
                continue

            if template and project.template != template:
                continue

            filtered.append(project)

        self._render_projects(filtered)

    def _render_projects(
        self,
        projects: list[Project],
    ) -> None:
        self._clear_layout(self.projects_layout)

        total = len(self.all_projects)
        shown = len(projects)

        self.total_label.setText(
            (
                f"{total} processo"
                if total == 1
                else f"{total} processos"
            )
        )
        self.result_label.setText(
            (
                f"{shown} exibido"
                if shown == 1
                else f"{shown} exibidos"
            )
        )

        if not projects:
            message = (
                "Nenhum processo corresponde aos filtros selecionados."
                if self.all_projects
                else "Nenhum processo cadastrado ainda."
            )
            self._show_empty_state(message)
            return

        for project in projects:
            self.projects_layout.addWidget(
                self._create_project_card(project)
            )

    # =============================================================
    # CARD
    # =============================================================

    def _create_project_card(
        self,
        project: Project,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("recentProjectCard")
        card.setMinimumHeight(112)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(16)

        icon = QLabel("▤")
        icon.setObjectName("projectDocumentIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(52, 52)

        information = QVBoxLayout()
        information.setSpacing(4)

        report_id = QLabel(project.report_id)
        report_id.setObjectName("projectId")

        name = QLabel(project.name)
        name.setObjectName("cardTitle")
        name.setWordWrap(True)

        part_name = (
            project.part_name
            if project.part_name
            and project.part_name != "Não informado"
            else "Peça não informada"
        )

        template_name = self._template_name(
            project.template
        )

        metadata = QLabel(
            (
                f"{template_name} · {part_name} · "
                f"{project.quantity} unidade(s)"
            )
        )
        metadata.setObjectName("cardDescription")
        metadata.setWordWrap(True)

        details = QLabel(
            " · ".join(
                value
                for value in [
                    project.client or "",
                    project.equipment or "",
                    (
                        "Atualizado "
                        + self._format_datetime(
                            project.updated_at
                        )
                    ),
                ]
                if value
            )
        )
        details.setObjectName("cardDescription")
        details.setWordWrap(True)

        information.addWidget(report_id)
        information.addWidget(name)
        information.addWidget(metadata)
        information.addWidget(details)

        status = QLabel(project.status)
        status.setObjectName("statusBadge")

        version = QLabel(project.version)
        version.setObjectName("versionBadge")

        actions = QVBoxLayout()
        actions.setSpacing(7)

        open_button = QPushButton(
            "Abrir processo →"
        )
        open_button.setObjectName(
            "cardButton"
        )
        open_button.setMinimumWidth(150)
        open_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        open_button.clicked.connect(
            lambda checked=False,
            report_id=project.report_id:
            self.open_project_requested.emit(
                report_id
            )
        )

        actions.addWidget(
            open_button
        )

        if project.status == "Concluído":
            status_button = QPushButton(
                "Reabrir processo"
            )
            status_button.setObjectName(
                "secondaryButton"
            )
            status_button.clicked.connect(
                lambda checked=False,
                selected_project=project:
                self._confirm_reopen_project(
                    selected_project
                )
            )
        else:
            status_button = QPushButton(
                "Concluir processo"
            )
            status_button.setObjectName(
                "secondaryButton"
            )
            status_button.clicked.connect(
                lambda checked=False,
                selected_project=project:
                self._confirm_complete_project(
                    selected_project
                )
            )

        status_button.setMinimumWidth(150)
        status_button.setMinimumHeight(32)
        status_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        actions.addWidget(
            status_button
        )

        delete_button = QPushButton(
            "Excluir processo"
        )
        delete_button.setObjectName(
            "deleteProcessButton"
        )
        delete_button.setMinimumWidth(150)
        delete_button.setMinimumHeight(32)
        delete_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        delete_button.setStyleSheet(
            """
            QPushButton#deleteProcessButton {
                background: transparent;
                border: 1px solid #D9A3A3;
                border-radius: 6px;
                color: #A51D1D;
                padding: 5px 12px;
                font-weight: 600;
            }

            QPushButton#deleteProcessButton:hover {
                background: #FFF4F4;
                border-color: #C94C4C;
            }

            QPushButton#deleteProcessButton:pressed {
                background: #FDE7E7;
            }
            """
        )
        delete_button.clicked.connect(
            lambda checked=False,
            selected_project=project:
            self._confirm_delete_project(
                selected_project
            )
        )

        actions.addWidget(
            delete_button
        )

        layout.addWidget(icon)
        layout.addLayout(information, 1)
        layout.addWidget(
            status,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        layout.addWidget(
            version,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        layout.addLayout(actions)

        return card

    # =============================================================
    # AÇÕES DO PROCESSO
    # =============================================================

    def _confirm_complete_project(
        self,
        project: Project,
    ) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(
            "Concluir processo"
        )
        dialog.setIcon(
            QMessageBox.Icon.Question
        )
        dialog.setText(
            (
                f'Deseja concluir o processo '
                f'"{project.name}"?'
            )
        )
        dialog.setInformativeText(
            (
                "A conclusão indica que o trabalho foi encerrado. "
                "O histórico e as versões emitidas permanecem "
                "preservados e o processo poderá ser reaberto depois."
            )
        )

        cancel_button = dialog.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole,
        )
        confirm_button = dialog.addButton(
            "Concluir processo",
            QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.setDefaultButton(
            cancel_button
        )
        dialog.exec()

        if dialog.clickedButton() is not confirm_button:
            return

        try:
            self.project_service.complete_project(
                project
            )
        except Exception as error:
            self._show_error(
                "Não foi possível concluir o processo.",
                str(error),
            )
            return

        self._reload_projects()

        self._show_information(
            "Processo concluído",
            (
                "O processo foi marcado como Concluído. "
                "Ele poderá ser reaberto posteriormente, "
                "sem perda do histórico."
            ),
        )

    def _confirm_reopen_project(
        self,
        project: Project,
    ) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(
            "Reabrir processo"
        )
        dialog.setIcon(
            QMessageBox.Icon.Question
        )
        dialog.setText(
            (
                f'Deseja reabrir o processo '
                f'"{project.name}"?'
            )
        )
        dialog.setInformativeText(
            (
                "O processo voltará para Em edição. "
                "As versões já emitidas e o histórico serão mantidos."
            )
        )

        cancel_button = dialog.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole,
        )
        confirm_button = dialog.addButton(
            "Reabrir processo",
            QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.setDefaultButton(
            cancel_button
        )
        dialog.exec()

        if dialog.clickedButton() is not confirm_button:
            return

        try:
            self.project_service.reopen_project(
                project
            )
        except Exception as error:
            self._show_error(
                "Não foi possível reabrir o processo.",
                str(error),
            )
            return

        self._reload_projects()

        self._show_information(
            "Processo reaberto",
            (
                "O processo voltou para Em edição. "
                "O histórico anterior permanece preservado."
            ),
        )

    def _confirm_delete_project(
        self,
        project: Project,
    ) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(
            "Excluir processo"
        )
        dialog.setIcon(
            QMessageBox.Icon.Warning
        )
        dialog.setText(
            (
                f'Deseja excluir o processo '
                f'"{project.name}"?'
            )
        )
        dialog.setInformativeText(
            (
                f"ID: {project.report_id}\n\n"
                "O processo deixará de aparecer nas listas normais "
                "do METRA. Os dados, documentos, versões e evidências "
                "serão preservados para rastreabilidade."
            )
        )

        cancel_button = dialog.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole,
        )
        delete_button = dialog.addButton(
            "Excluir processo",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        dialog.setDefaultButton(
            cancel_button
        )
        dialog.exec()

        if dialog.clickedButton() is not delete_button:
            return

        try:
            self.project_service.delete_project(
                project
            )
        except Exception as error:
            self._show_error(
                "Não foi possível excluir o processo.",
                str(error),
            )
            return

        self._reload_projects()

        self._show_information(
            "Processo excluído",
            (
                "O processo foi removido das listas ativas. "
                "Seu histórico permanece preservado para "
                "rastreabilidade."
            ),
        )

    def _reload_projects(
        self,
    ) -> None:
        self.set_projects(
            self.project_service.get_all_projects()
        )

        self.refresh_requested.emit()

    def _show_error(
        self,
        title: str,
        details: str,
    ) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setIcon(
            QMessageBox.Icon.Critical
        )
        dialog.setText(title)
        dialog.setInformativeText(
            details
        )
        dialog.addButton(
            "Entendi",
            QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.exec()

    def _show_information(
        self,
        title: str,
        message: str,
    ) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setIcon(
            QMessageBox.Icon.Information
        )
        dialog.setText(message)
        dialog.addButton(
            "Entendi",
            QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.exec()

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

    def _show_empty_state(
        self,
        message: str,
    ) -> None:
        label = QLabel(message)
        label.setObjectName("emptyState")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setMinimumHeight(130)

        self.projects_layout.addWidget(label)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _template_name(
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

    def _format_datetime(
        self,
        value: str | None,
    ) -> str:
        if not value:
            return "-"

        try:
            parsed = datetime.fromisoformat(value)
            return parsed.strftime(
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            return value