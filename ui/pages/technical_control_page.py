from PySide6.QtCore import (
    QDateTime,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.technical_control_service import (
    TechnicalControlService,
)
from ui.components.page_header import PageHeader
from ui.components.section_header import SectionHeader


class TechnicalControlPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project = None

        self.service = (
            TechnicalControlService()
        )

        self.build_ui()

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        # SCROLL

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
            56,
            36,
            56,
            48,
        )

        # CONTEÚDO CENTRAL

        content = QWidget()

        content.setObjectName(
            "pageContent"
        )

        content.setMaximumWidth(
            1240
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
            20
        )

        self.page_header = PageHeader(
            title="Controle técnico",
            subtitle="Registre a elaboração, revisão e aprovação do relatório antes da emissão.",
            metadata="-",
            back_text="← Visão geral",
        )
        self.page_header.back_button.clicked.connect(self.back_requested.emit)
        content_layout.addWidget(self.page_header)

        # STATUS

        status_card = QFrame()

        status_card.setObjectName(
            "formCard"
        )

        status_layout = QVBoxLayout(
            status_card
        )

        status_layout.setContentsMargins(20,17,20,17)

        status_layout.setSpacing(
            14
        )

        status_title = QLabel(
            "Status técnico"
        )

        status_title.setObjectName(
            "formSectionTitle"
        )

        status_description = QLabel(
            "Indique em qual etapa de revisão o relatório se encontra."
        )

        status_description.setObjectName(
            "formSectionDescription"
        )

        self.status_input = QComboBox()

        self.status_input.addItems(
            [
                "Em elaboração",
                "Aguardando revisão",
                "Revisado",
                "Aprovado",
            ]
        )

        status_layout.addWidget(
            status_title
        )

        status_layout.addWidget(
            status_description
        )

        status_layout.addWidget(
            self.status_input
        )

        content_layout.addWidget(
            status_card
        )

        # ELABORAÇÃO

        preparation_card = QFrame()

        preparation_card.setObjectName(
            "formCard"
        )

        preparation_layout = QVBoxLayout(
            preparation_card
        )

        preparation_layout.setContentsMargins(20,17,20,17)

        preparation_layout.setSpacing(
            16
        )

        preparation_title = QLabel(
            "Elaboração técnica"
        )

        preparation_title.setObjectName(
            "formSectionTitle"
        )

        preparation_description = QLabel(
            "Identifique quem preparou o relatório técnico."
        )

        preparation_description.setObjectName(
            "formSectionDescription"
        )

        preparation_layout.addWidget(
            preparation_title
        )

        preparation_layout.addWidget(
            preparation_description
        )

        preparation_grid = QGridLayout()

        preparation_grid.setHorizontalSpacing(
            24
        )

        prepared_by_label = QLabel(
            "Responsável pela elaboração"
        )

        prepared_by_label.setObjectName(
            "fieldLabel"
        )

        self.prepared_by_input = QLineEdit()

        self.prepared_by_input.setPlaceholderText(
            "Nome do responsável"
        )

        prepared_at_label = QLabel(
            "Data e hora"
        )

        prepared_at_label.setObjectName(
            "fieldLabel"
        )

        self.prepared_at_input = (
            QDateTimeEdit()
        )

        self.prepared_at_input.setCalendarPopup(
            True
        )

        self.prepared_at_input.setDisplayFormat(
            "dd/MM/yyyy HH:mm"
        )

        preparation_grid.addWidget(
            prepared_by_label,
            0,
            0,
        )

        preparation_grid.addWidget(
            prepared_at_label,
            0,
            1,
        )

        preparation_grid.addWidget(
            self.prepared_by_input,
            1,
            0,
        )

        preparation_grid.addWidget(
            self.prepared_at_input,
            1,
            1,
        )

        preparation_grid.setColumnStretch(
            0,
            1,
        )

        preparation_grid.setColumnStretch(
            1,
            1,
        )

        preparation_layout.addLayout(
            preparation_grid
        )

        content_layout.addWidget(
            preparation_card
        )

        # REVISÃO / APROVAÇÃO

        review_card = QFrame()

        review_card.setObjectName(
            "formCard"
        )

        review_layout = QVBoxLayout(
            review_card
        )

        review_layout.setContentsMargins(20,17,20,17)

        review_layout.setSpacing(
            16
        )

        review_title = QLabel(
            "Revisão e aprovação"
        )

        review_title.setObjectName(
            "formSectionTitle"
        )

        review_description = QLabel(
            "Registre o responsável pela revisão ou aprovação técnica."
        )

        review_description.setObjectName(
            "formSectionDescription"
        )

        review_layout.addWidget(
            review_title
        )

        review_layout.addWidget(
            review_description
        )

        review_grid = QGridLayout()

        review_grid.setHorizontalSpacing(
            24
        )

        reviewed_by_label = QLabel(
            "Responsável pela revisão / aprovação"
        )

        reviewed_by_label.setObjectName(
            "fieldLabel"
        )

        self.reviewed_by_input = (
            QLineEdit()
        )

        self.reviewed_by_input.setPlaceholderText(
            "Nome do responsável"
        )

        reviewed_at_label = QLabel(
            "Data e hora"
        )

        reviewed_at_label.setObjectName(
            "fieldLabel"
        )

        self.reviewed_at_input = (
            QDateTimeEdit()
        )

        self.reviewed_at_input.setCalendarPopup(
            True
        )

        self.reviewed_at_input.setDisplayFormat(
            "dd/MM/yyyy HH:mm"
        )

        review_grid.addWidget(
            reviewed_by_label,
            0,
            0,
        )

        review_grid.addWidget(
            reviewed_at_label,
            0,
            1,
        )

        review_grid.addWidget(
            self.reviewed_by_input,
            1,
            0,
        )

        review_grid.addWidget(
            self.reviewed_at_input,
            1,
            1,
        )

        review_grid.setColumnStretch(
            0,
            1,
        )

        review_grid.setColumnStretch(
            1,
            1,
        )

        review_layout.addLayout(
            review_grid
        )

        notes_label = QLabel(
            "Observações da revisão"
        )

        notes_label.setObjectName(
            "fieldLabel"
        )

        self.review_notes_input = (
            QTextEdit()
        )

        self.review_notes_input.setPlaceholderText(
            "Pendências, correções solicitadas, justificativas "
            "ou observações da aprovação..."
        )

        self.review_notes_input.setMaximumHeight(
            130
        )

        review_layout.addWidget(
            notes_label
        )

        review_layout.addWidget(
            self.review_notes_input
        )

        content_layout.addWidget(
            review_card
        )

        # AÇÕES

        actions = QHBoxLayout()

        actions.addStretch()

        self.cancel_button = QPushButton(
            "Cancelar"
        )

        self.cancel_button.setObjectName(
            "secondaryButton"
        )

        self.cancel_button.clicked.connect(
            self.back_requested.emit
        )

        self.save_button = QPushButton(
            "Salvar controle técnico"
        )

        self.save_button.setObjectName(
            "primaryButton"
        )

        self.save_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.save_button.clicked.connect(
            self.save_control
        )

        actions.addWidget(
            self.cancel_button
        )

        actions.addWidget(
            self.save_button
        )

        content_layout.addLayout(
            actions
        )

        # CENTRALIZAÇÃO

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

    # PROJETO

    def set_project(
        self,
        project: Project,
    ) -> None:

        self.current_project = project

        self.page_header.set_metadata(f"{project.report_id} · {project.name}")

        self.load_control()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # CARREGAR

    def load_control(self) -> None:

        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        control = self.service.get_control(
            self.current_project.id
        )

        if control is None:
            self.clear_form()
            return

        self.status_input.setCurrentText(
            control.status
        )

        self.prepared_by_input.setText(
            control.prepared_by or ""
        )

        self.reviewed_by_input.setText(
            control.reviewed_by or ""
        )

        self.review_notes_input.setPlainText(
            control.review_notes or ""
        )

        if control.prepared_at:
            value = QDateTime.fromString(
                control.prepared_at,
                Qt.DateFormat.ISODate,
            )

            if value.isValid():
                self.prepared_at_input.setDateTime(
                    value
                )

        if control.reviewed_at:
            value = QDateTime.fromString(
                control.reviewed_at,
                Qt.DateFormat.ISODate,
            )

            if value.isValid():
                self.reviewed_at_input.setDateTime(
                    value
                )

    # LIMPAR

    def clear_form(self) -> None:

        now = QDateTime.currentDateTime()

        self.status_input.setCurrentText(
            "Em elaboração"
        )

        self.prepared_by_input.clear()

        self.reviewed_by_input.clear()

        self.review_notes_input.clear()

        self.prepared_at_input.setDateTime(
            now
        )

        self.reviewed_at_input.setDateTime(
            now
        )

    # SALVAR

    def save_control(self) -> None:

        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        data = {
            "status":
                self.status_input.currentText(),

            "prepared_by":
                self.prepared_by_input.text(),

            "prepared_at":
                self.prepared_at_input
                .dateTime()
                .toString(
                    Qt.DateFormat.ISODate
                ),

            "reviewed_by":
                self.reviewed_by_input.text(),

            "reviewed_at":
                self.reviewed_at_input
                .dateTime()
                .toString(
                    Qt.DateFormat.ISODate
                ),

            "review_notes":
                self.review_notes_input.toPlainText(),
        }

        try:
            self.service.save_control(
                self.current_project.id,
                data,
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Dados incompletos",
                str(error),
            )

            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar",
                (
                    "Não foi possível salvar o controle técnico.\n\n"
                    f"Detalhes: {error}"
                ),
            )

            return