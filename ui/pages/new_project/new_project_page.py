from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from models.project_draft import ProjectDraft
from services.batch_analysis_service import BatchAnalysisService

from ui.pages.new_project.project_documents_step import ProjectDocumentsStep
from ui.pages.new_project.project_form_step import ProjectFormStep
from ui.pages.new_project.project_review_step import ProjectReviewStep
from ui.pages.new_project.start_step import ProjectStartStep


class NewProjectPage(QWidget):
    back_requested = Signal()
    create_requested = Signal(dict, object)

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.batch_service = BatchAnalysisService()
        self.current_draft: ProjectDraft | None = None
        self.current_flow: str | None = None

        self._build_ui()
        self._connect_signals()
        self.show_start()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        self.start_page = ProjectStartStep()
        self.documents_page = ProjectDocumentsStep()
        self.review_page = ProjectReviewStep()
        self.form_page = ProjectFormStep()

        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.documents_page)
        self.stack.addWidget(self.review_page)
        self.stack.addWidget(self.form_page)

        root_layout.addWidget(self.stack)

    def _connect_signals(self) -> None:
        self.start_page.back_requested.connect(
            self.back_requested.emit
        )
        self.start_page.import_requested.connect(
            self.start_documents_flow
        )
        self.start_page.manual_requested.connect(
            self.start_manual_flow
        )

        self.documents_page.back_requested.connect(
            self.show_start
        )
        self.documents_page.cancel_requested.connect(
            self.back_requested.emit
        )
        self.documents_page.analyze_requested.connect(
            self.analyze_documents
        )

        self.review_page.back_requested.connect(
            self.show_documents
        )
        self.review_page.restart_requested.connect(
            self.restart_document_flow
        )
        self.review_page.continue_requested.connect(
            self.continue_to_form
        )

        self.form_page.back_requested.connect(
            self.return_from_form
        )
        self.form_page.create_requested.connect(
            self.handle_create_request
        )

    def show_start(self) -> None:
        self.current_flow = None
        self.stack.setCurrentWidget(self.start_page)

    def start_documents_flow(self) -> None:
        self.current_flow = "documents"
        self.current_draft = None

        self.documents_page.reset_step()
        self.review_page.reset_step()
        self.form_page.reset_step()
        self.form_page.set_flow_mode("documents")

        self.stack.setCurrentWidget(self.documents_page)

    def start_manual_flow(self) -> None:
        self.current_flow = "manual"
        self.current_draft = ProjectDraft(
            process_type="manual"
        )

        self.review_page.reset_step()
        self.form_page.reset_step()
        self.form_page.set_flow_mode("manual")
        self.form_page.set_draft(self.current_draft)

        self.stack.setCurrentWidget(self.form_page)

    def show_documents(self) -> None:
        self.current_flow = "documents"
        self.stack.setCurrentWidget(self.documents_page)

    def show_review(self) -> None:
        self.current_flow = "documents"
        self.stack.setCurrentWidget(self.review_page)

    def show_form(self) -> None:
        self.stack.setCurrentWidget(self.form_page)

    def restart_document_flow(self) -> None:
        self.current_flow = "documents"
        self.current_draft = None

        self.review_page.reset_step()
        self.form_page.reset_step()
        self.form_page.set_flow_mode("documents")

        self.stack.setCurrentWidget(self.documents_page)

    def continue_to_form(self) -> None:
        if self.current_draft is None:
            QMessageBox.warning(
                self,
                "Análise indisponível",
                "Não há um rascunho de processo disponível para continuar.",
            )
            return

        self.current_flow = "documents"
        self.form_page.reset_step()
        self.form_page.set_flow_mode("documents")
        self.form_page.set_draft(self.current_draft)

        self.stack.setCurrentWidget(self.form_page)

    def return_from_form(self) -> None:
        if self.current_flow == "manual":
            self.show_start()
            return

        self.show_review()

    def analyze_documents(
        self,
        source_paths: list[str],
        process_type: str,
    ) -> None:
        self.documents_page.set_analyzing(True)

        try:
            draft = self.batch_service.analyze_files(
                source_paths=source_paths,
                process_type=process_type,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro na análise",
                (
                    "Não foi possível concluir a análise dos documentos.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        finally:
            self.documents_page.set_analyzing(False)

        self.current_flow = "documents"
        self.current_draft = draft

        self.review_page.set_draft(draft)
        self.stack.setCurrentWidget(self.review_page)

    def handle_create_request(
        self,
        data: dict,
    ) -> None:
        if (
            self.current_draft is not None
            and self.current_draft.part_compatibility == "incompatible"
        ):
            confirmation = QMessageBox.question(
                self,
                "Documentos possivelmente incompatíveis",
                (
                    "O sistema identificou documentos que podem pertencer "
                    "a peças diferentes.\n\nDeseja criar o processo mesmo assim?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )

            if confirmation != QMessageBox.StandardButton.Yes:
                return

        self.form_page.set_creating(True)

        try:
            self.create_requested.emit(
                data,
                self.current_draft,
            )
        finally:
            self.form_page.set_creating(False)

    def reset_page(self) -> None:
        self.current_draft = None
        self.current_flow = None

        self.documents_page.reset_step()
        self.review_page.reset_step()
        self.form_page.reset_step()
        self.form_page.set_flow_mode("documents")

        self.show_start()

    def set_current_draft(
        self,
        draft: ProjectDraft | None,
    ) -> None:
        self.current_draft = draft

        if draft is None:
            self.review_page.reset_step()
            self.form_page.reset_step()
            return

        if draft.is_manual:
            self.current_flow = "manual"
            self.form_page.set_flow_mode("manual")
        else:
            self.current_flow = "documents"
            self.form_page.set_flow_mode("documents")

        self.review_page.set_draft(draft)
        self.form_page.set_draft(draft)