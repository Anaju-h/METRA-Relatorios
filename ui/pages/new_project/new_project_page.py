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

from ui.pages.new_project.project_documents_step import (
    ProjectDocumentsStep,
)
from ui.pages.new_project.project_form_step import (
    ProjectFormStep,
)
from ui.pages.new_project.project_review_step import (
    ProjectReviewStep,
)
from ui.pages.new_project.start_step import (
    ProjectStartStep,
)


class NewProjectPage(QWidget):
    """
    Controlador do fluxo de criação de processos.

    As etapas visuais ficam separadas em componentes próprios,
    enquanto esta classe coordena a navegação, a análise dos PDFs
    e o envio dos dados ao MainWindow.
    """

    back_requested = Signal()

    # Mantém compatibilidade com o MainWindow atual:
    # 1º argumento: dados do formulário;
    # 2º argumento: ProjectDraft ou None.
    create_requested = Signal(
        dict,
        object,
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.batch_service = BatchAnalysisService()

        self.current_draft: ProjectDraft | None = None

        self._build_ui()
        self._connect_signals()

        self.show_start()
    # =============================================================
    # INTERFACE
    # =============================================================

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.stack = QStackedWidget()

        self.start_page = ProjectStartStep()
        self.documents_page = ProjectDocumentsStep()
        self.review_page = ProjectReviewStep()
        self.form_page = ProjectFormStep()

        self.stack.addWidget(
            self.start_page
        )
        self.stack.addWidget(
            self.documents_page
        )
        self.stack.addWidget(
            self.review_page
        )
        self.stack.addWidget(
            self.form_page
        )

        root_layout.addWidget(
            self.stack
        )

    # =============================================================
    # CONEXÕES
    # =============================================================

    def _connect_signals(self) -> None:
        # Etapa inicial
        self.start_page.back_requested.connect(
            self.back_requested.emit
        )
        self.start_page.import_requested.connect(
            self.start_documents_flow
        )
        self.start_page.manual_requested.connect(
            self.start_manual_flow
        )

        # Documentos
        self.documents_page.back_requested.connect(
            self.show_start
        )
        self.documents_page.cancel_requested.connect(
            self.back_requested.emit
        )
        self.documents_page.analyze_requested.connect(
            self.analyze_documents
        )

        # Revisão
        self.review_page.back_requested.connect(
            self.show_documents
        )
        self.review_page.restart_requested.connect(
            self.restart_document_flow
        )
        self.review_page.continue_requested.connect(
            self.continue_to_form
        )

        # Formulário final
        self.form_page.back_requested.connect(
            self.return_from_form
        )
        self.form_page.create_requested.connect(
            self.handle_create_request
        )
    # =============================================================
    # NAVEGAÇÃO
    # =============================================================

    def show_start(
        self,
    ) -> None:
        self.stack.setCurrentWidget(
            self.start_page
        )

    def start_documents_flow(
        self,
    ) -> None:
        self.current_draft = None

        self.documents_page.reset_step()

        self.review_page.reset_step()

        self.form_page.reset_step()

        self.stack.setCurrentWidget(
            self.documents_page
        )

    def start_manual_flow(
        self,
    ) -> None:
        self.current_draft = ProjectDraft(
            process_type="manual"
        )

        self.review_page.reset_step()

        self.form_page.reset_step()

        self.form_page.set_draft(
            self.current_draft
        )

        self.stack.setCurrentWidget(
            self.form_page
        )

    def show_documents(
        self,
    ) -> None:
        self.stack.setCurrentWidget(
            self.documents_page
        )

    def show_review(
        self,
    ) -> None:
        self.stack.setCurrentWidget(
            self.review_page
        )

    def show_form(
        self,
    ) -> None:
        self.stack.setCurrentWidget(
            self.form_page
        )

    def restart_document_flow(
        self,
    ) -> None:
        self.current_draft = None

        self.review_page.reset_step()

        self.form_page.reset_step()

        self.stack.setCurrentWidget(
            self.documents_page
        )

    def continue_to_form(
        self,
    ) -> None:
        if self.current_draft is None:
            QMessageBox.warning(
                self,
                "Análise indisponível",
                (
                    "Não há um rascunho de processo disponível "
                    "para continuar."
                ),
            )
            return

        self.form_page.reset_step()

        self.form_page.set_draft(
            self.current_draft
        )

        self.stack.setCurrentWidget(
            self.form_page
        )

    def return_from_form(
        self,
    ) -> None:
        if (
            self.current_draft is not None
            and self.current_draft.is_manual
        ):
            self.show_start()
            return

        self.show_review()
    # =============================================================
    # ANÁLISE DOS DOCUMENTOS
    # =============================================================

    def analyze_documents(
        self,
        source_paths: list[str],
        process_type: str,
    ) -> None:
        self.documents_page.set_analyzing(
            True
        )

        try:
            draft = (
                self.batch_service
                .analyze_files(
                    source_paths=source_paths,
                    process_type=process_type,
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro na análise",
                (
                    "Não foi possível concluir a análise "
                    "dos documentos.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        finally:
            self.documents_page.set_analyzing(
                False
            )

        self.current_draft = draft

        self.review_page.set_draft(
            draft
        )

        self.stack.setCurrentWidget(
            self.review_page
        )

    # =============================================================
    # CRIAÇÃO DO PROCESSO
    # =============================================================

    def handle_create_request(
        self,
        data: dict,
    ) -> None:
        if (
            self.current_draft is not None
            and self.current_draft.part_compatibility
            == "incompatible"
        ):
            confirmation = QMessageBox.question(
                self,
                "Documentos possivelmente incompatíveis",
                (
                    "O sistema identificou documentos que podem "
                    "pertencer a peças diferentes.\n\n"
                    "Deseja criar o processo mesmo assim?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )

            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

        self.form_page.set_creating(
            True
        )

        try:
            self.create_requested.emit(
                data,
                self.current_draft,
            )

        finally:
            self.form_page.set_creating(
                False
            )
    # =============================================================
    # ESTADO DA PÁGINA
    # =============================================================

    def reset_page(
        self,
    ) -> None:
        self.current_draft = None

        self.documents_page.reset_step()
        self.review_page.reset_step()
        self.form_page.reset_step()

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

        self.review_page.set_draft(
            draft
        )

        self.form_page.set_draft(
            draft
        )