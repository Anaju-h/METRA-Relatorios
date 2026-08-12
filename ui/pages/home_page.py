from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from ui.components.project_status_chart import (
    ProjectStatusChart,
)


class HomePage(QWidget):
    new_project_requested = Signal()
    browse_processes_requested = Signal()
    open_project_requested = Signal(str)

    def __init__(self):
        super().__init__()

        self.recent_projects: list[Project] = []
        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

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
            38,
            28,
            38,
            34,
        )
        scroll_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName(
            "pageContent"
        )
        content.setMaximumWidth(
            1320
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
        content_layout.setSpacing(0)

        # ---------------------------------------------------------
        # HERO
        # ---------------------------------------------------------

        hero = QFrame()
        hero.setObjectName(
            "homeHero"
        )
        hero.setMinimumHeight(
            260
        )

        hero_layout = QHBoxLayout(
            hero
        )
        hero_layout.setContentsMargins(
            34,
            28,
            34,
            28,
        )
        hero_layout.setSpacing(
            34
        )

        hero_text = QVBoxLayout()
        hero_text.setSpacing(
            10
        )

        eyebrow = QLabel(
            "BEM-VINDO AO METRA"
        )
        eyebrow.setObjectName(
            "homeEyebrow"
        )

        title = QLabel(
            "Comece um novo processo"
        )
        title.setObjectName(
            "homeTitle"
        )
        title.setWordWrap(
            True
        )

        description = QLabel(
            "Organize, revise e consolide relatórios técnicos de "
            "metrologia em um fluxo único, rastreável e profissional."
        )
        description.setObjectName(
            "homeDescription"
        )
        description.setWordWrap(
            True
        )
        description.setMaximumWidth(
            650
        )

        button_row = QHBoxLayout()
        button_row.setSpacing(
            12
        )

        self.new_project_button = QPushButton(
            "+  Novo processo"
        )
        self.new_project_button.setObjectName(
            "primaryButton"
        )
        self.new_project_button.setMinimumHeight(
            46
        )
        self.new_project_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.new_project_button.clicked.connect(
            self.new_project_requested.emit
        )

        self.open_project_button = QPushButton(
            "▭  Abrir processo"
        )
        self.open_project_button.setObjectName(
            "secondaryButton"
        )
        self.open_project_button.setMinimumHeight(
            46
        )
        self.open_project_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.open_project_button.clicked.connect(
            self.browse_processes_requested.emit
        )

        button_row.addWidget(
            self.new_project_button
        )
        button_row.addWidget(
            self.open_project_button
        )
        button_row.addStretch()

        hero_text.addStretch(1)
        hero_text.addWidget(
            eyebrow
        )
        hero_text.addWidget(
            title
        )
        hero_text.addWidget(
            description
        )
        hero_text.addSpacing(
            8
        )
        hero_text.addLayout(
            button_row
        )
        hero_text.addStretch(1)

        chart_card = QFrame()
        chart_card.setObjectName(
            "homeChartCard"
        )
        chart_card.setMinimumWidth(
            390
        )

        chart_layout = QHBoxLayout(
            chart_card
        )
        chart_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )
        chart_layout.setSpacing(
            18
        )

        self.status_chart = (
            ProjectStatusChart()
        )

        legend = QVBoxLayout()
        legend.setSpacing(
            10
        )

        legend_title = QLabel(
            "Visão dos projetos"
        )
        legend_title.setObjectName(
            "cardTitle"
        )

        self.editing_value = (
            self._create_legend_item(
                legend,
                "Em edição",
                "#F07C00",
            )
        )

        self.completed_value = (
            self._create_legend_item(
                legend,
                "Concluídos",
                "#006CB7",
            )
        )

        legend.insertWidget(
            0,
            legend_title
        )
        legend.addStretch()

        chart_layout.addWidget(
            self.status_chart,
            1,
        )
        chart_layout.addLayout(
            legend
        )

        hero_layout.addLayout(
            hero_text,
            3,
        )
        hero_layout.addWidget(
            chart_card,
            2,
        )

        content_layout.addWidget(
            hero
        )
        content_layout.addSpacing(
            26
        )

        # ---------------------------------------------------------
        # PROJETOS RECENTES
        # ---------------------------------------------------------

        recent_header = QHBoxLayout()

        recent_text = QVBoxLayout()
        recent_text.setSpacing(
            3
        )

        recent_title = QLabel(
            "Processos recentes"
        )
        recent_title.setObjectName(
            "sectionTitle"
        )

        recent_description = QLabel(
            "Continue um relatório em andamento ou consulte um processo anterior."
        )
        recent_description.setObjectName(
            "sectionDescription"
        )

        recent_text.addWidget(
            recent_title
        )
        recent_text.addWidget(
            recent_description
        )

        recent_header.addLayout(
            recent_text
        )
        recent_header.addStretch()

        content_layout.addLayout(
            recent_header
        )
        content_layout.addSpacing(
            14
        )

        self.recent_container = QWidget()
        self.recent_container.setObjectName(
            "recentProjectsContainer"
        )
        self.recent_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.recent_layout = QVBoxLayout(
            self.recent_container
        )
        self.recent_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.recent_layout.setSpacing(
            10
        )
        self.recent_layout.setSizeConstraint(
            QLayout.SizeConstraint.SetMinimumSize
        )

        content_layout.addWidget(
            self.recent_container
        )
        content_layout.addStretch(1)

        content_row = QHBoxLayout()
        content_row.addStretch(1)
        content_row.addWidget(
            content,
            12,
        )
        content_row.addStretch(1)

        scroll_layout.addLayout(
            content_row
        )

        self.scroll_area.setWidget(
            scroll_content
        )
        root_layout.addWidget(
            self.scroll_area
        )

        self.show_empty_state()

    def _create_legend_item(
        self,
        layout: QVBoxLayout,
        title: str,
        color: str,
    ) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(
            8
        )

        marker = QLabel()
        marker.setFixedSize(
            9,
            9,
        )
        marker.setStyleSheet(
            (
                f"background: {color}; "
                "border-radius: 4px;"
            )
        )

        text = QLabel(
            title
        )
        text.setObjectName(
            "homeLegendLabel"
        )

        value = QLabel(
            "0"
        )
        value.setObjectName(
            "homeLegendValue"
        )
        value.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        row.addWidget(
            marker
        )
        row.addWidget(
            text
        )
        row.addStretch()
        row.addWidget(
            value
        )

        layout.addLayout(
            row
        )

        return value

    # =============================================================
    # PROJETOS
    # =============================================================

    def set_recent_projects(
        self,
        projects: list[Project],
    ) -> None:
        self.recent_projects = (
            projects
        )

        self.clear_recent_projects()

        self.status_chart.set_projects(
            projects
        )

        self._update_chart_legend()

        if not projects:
            self.show_empty_state()
            return

        for project in projects:
            self.recent_layout.addWidget(
                self.create_project_card(
                    project
                )
            )

    def _update_chart_legend(
        self,
    ) -> None:
        values = (
            self.status_chart.values
        )

        self.editing_value.setText(
            str(
                values[
                    "Em edição"
                ]
            )
        )

        self.completed_value.setText(
            str(
                values[
                    "Concluídos"
                ]
            )
        )

    def create_project_card(
        self,
        project: Project,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName(
            "recentProjectCard"
        )
        card.setMinimumHeight(
            92
        )

        layout = QHBoxLayout(
            card
        )
        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )
        layout.setSpacing(
            16
        )

        icon = QLabel(
            "▤"
        )
        icon.setObjectName(
            "projectDocumentIcon"
        )
        icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        icon.setFixedSize(
            52,
            52,
        )

        info = QVBoxLayout()
        info.setSpacing(
            3
        )

        report_id = QLabel(
            project.report_id
        )
        report_id.setObjectName(
            "projectId"
        )

        name = QLabel(
            project.name
        )
        name.setObjectName(
            "cardTitle"
        )
        name.setWordWrap(
            True
        )

        part_name = (
            project.part_name
            if (
                project.part_name
                and project.part_name
                != "Não informado"
            )
            else "Peça não informada"
        )

        metadata = QLabel(
            (
                f"{project.template}  ·  "
                f"{part_name}"
            )
        )
        metadata.setObjectName(
            "cardDescription"
        )
        metadata.setWordWrap(
            True
        )

        info.addWidget(
            report_id
        )
        info.addWidget(
            name
        )
        info.addWidget(
            metadata
        )

        status = QLabel(
            project.status
        )
        status.setObjectName(
            "statusBadge"
        )

        version = QLabel(
            project.version
        )
        version.setObjectName(
            "versionBadge"
        )

        open_button = QPushButton(
            "Abrir processo  →"
        )
        open_button.setObjectName(
            "cardButton"
        )
        open_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        open_button.clicked.connect(
            (
                lambda checked=False,
                report_id=project.report_id:
                self.open_project_requested.emit(
                    report_id
                )
            )
        )

        layout.addWidget(
            icon
        )
        layout.addLayout(
            info,
            1,
        )
        layout.addWidget(
            status
        )
        layout.addWidget(
            version
        )
        layout.addWidget(
            open_button
        )

        return card

    def show_empty_state(
        self,
    ) -> None:
        label = QLabel(
            "Nenhum processo criado ainda.\n"
            "Crie seu primeiro relatório para começar."
        )
        label.setObjectName(
            "emptyState"
        )
        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        label.setMinimumHeight(
            118
        )

        self.recent_layout.addWidget(
            label
        )

    def clear_recent_projects(
        self,
    ) -> None:
        while self.recent_layout.count():
            item = (
                self.recent_layout
                .takeAt(
                    0
                )
            )

            widget = (
                item.widget()
            )

            if widget is not None:
                widget.deleteLater()