from __future__ import annotations

from pathlib import Path
import shutil

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from services.final_report_generator import (
    FinalReportGenerator,
)
from services.technical_control_service import (
    TechnicalControlService,
)
from services.pdf_service import PDFService
from services.project_service import ProjectService
from services.report_extraction_service import (
    ReportExtractionService,
)
from services.report_version_service import (
    ReportVersionService,
)

from ui.editor.image_editor import ImageEditor
from ui.components.app_header import AppHeader
from ui.components.app_sidebar import AppSidebar

from ui.pages.characteristics_page import (
    CharacteristicsPage,
)
from ui.pages.documents_page import (
    DocumentsPage,
)
from ui.pages.extraction_review_page import (
    ExtractionReviewPage,
)
from ui.pages.final_report_page import (
    FinalReportPage,
)
from ui.pages.final_report_preview_page import (
    FinalReportPreviewPage,
)
from ui.pages.home_page import HomePage
from ui.pages.images_page import ImagesPage
from ui.pages.measurement_page import MeasurementPage
from ui.pages.new_project_page import NewProjectPage
from ui.pages.overview_page import OverviewPage
from ui.pages.processes_page import ProcessesPage
from ui.pages.report_page import ReportPage
from ui.pages.technical_control_page import (
    TechnicalControlPage,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "METRA - Sistema Inteligente de Pós-processamento de Relatórios"
        )

        self.setMinimumSize(900, 620)

        self.resize(
            1200,
            750,
        )

        self.current_project = None

        self.current_document_id: (
            int
            | None
        ) = None

        self.last_final_report_payload: (
            dict
            | None
        ) = None

        self.last_generated_report_path: (
            Path
            | None
        ) = None

        self._loaded_page_projects: dict[str, int | str] = {}

        # =========================================================
        # SERVIÇOS
        # =========================================================

        self.project_service = (
            ProjectService()
        )

        self.pdf_service = (
            PDFService()
        )

        self.extraction_service = (
            ReportExtractionService()
        )

        self.final_report_generator = (
            FinalReportGenerator()
        )

        self.technical_control_service = (
            TechnicalControlService()
        )

        self.report_version_service = (
            ReportVersionService()
        )

        # =========================================================
        # PÁGINAS
        # =========================================================
        #
        # Apenas a Home é criada durante a inicialização da janela.
        # As demais páginas são construídas somente quando o usuário
        # acessa cada módulo. Isso reduz significativamente o tempo
        # entre executar o programa e a janela aparecer.
        # =========================================================

        self.pages = QStackedWidget()
        self.pages.setMinimumSize(0, 0)
        self.pages.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored,
        )

        self.home_page = HomePage()
        self.home_page.setMinimumSize(0, 0)
        self.home_page.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored,
        )
        self.pages.addWidget(self.home_page)

        self.new_project_page = None
        self.processes_page = None
        self.overview_page = None
        self.documents_page = None
        self.report_page = None
        self.extraction_review_page = None
        self.characteristics_page = None
        self.measurement_page = None
        self.images_page = None
        self.image_editor = None
        self.technical_control_page = None
        self.final_report_page = None
        self.final_report_preview_page = None

        # =========================================================
        # ESTRUTURA GLOBAL
        # =========================================================

        self.app_header = AppHeader()
        self.app_sidebar = AppSidebar()

        shell = QWidget()
        shell.setObjectName("appShell")

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        shell_layout.addWidget(self.app_header)

        body = QWidget()
        body.setObjectName("appBody")

        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        body_layout.addWidget(self.app_sidebar)
        body_layout.addWidget(self.pages, 1)

        shell_layout.addWidget(body, 1)

        self.setCentralWidget(shell)

        self.connect_signals()
        self.connect_sidebar_signals()

        self.show_home()

    # =============================================================
    # NAVEGAÇÃO GLOBAL
    # =============================================================

    def connect_sidebar_signals(self) -> None:
        self.app_sidebar.home_requested.connect(
            self.show_home
        )

        self.app_sidebar.processes_requested.connect(
            self.show_processes
        )

        self.app_sidebar.overview_requested.connect(
            self.show_current_overview
        )

        self.app_sidebar.documents_requested.connect(
            self.show_documents
        )

        self.app_sidebar.characteristics_requested.connect(
            self.show_characteristics
        )

        self.app_sidebar.measurement_requested.connect(
            self.show_measurement
        )

        self.app_sidebar.images_requested.connect(
            self.show_images
        )

        self.app_sidebar.technical_control_requested.connect(
            self.show_technical_control
        )

        self.app_sidebar.final_report_requested.connect(
            self.show_final_report
        )

    def set_current_page(
        self,
        page,
        navigation_key: str,
    ) -> None:
        self.pages.setCurrentWidget(
            page
        )

        self.app_sidebar.set_active(
            navigation_key
        )

    def update_project_navigation(self) -> None:
        self.app_sidebar.set_project_available(
            self.current_project is not None
        )

    # =============================================================
    # SINAIS
    # =============================================================

    def connect_signals(self) -> None:
        self.home_page.new_project_requested.connect(
            self.show_new_project
        )

        self.home_page.open_project_requested.connect(
            self.open_project
        )

        self.home_page.browse_processes_requested.connect(
            self.show_processes
        )

    # =============================================================
    # CRIAÇÃO PREGUIÇOSA DAS PÁGINAS
    # =============================================================

    def _create_page(self, page_class):
        """
        Cria a página sem permitir que o tamanho mínimo dela altere
        a geometria da janela na primeira abertura.
        """
        page = page_class()

        page.setMinimumSize(0, 0)
        page.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored,
        )

        self.pages.addWidget(page)

        # Mantém o stack preso à área disponível do corpo da aplicação,
        # em vez de adotar o sizeHint da página recém-adicionada.
        self.pages.setMinimumSize(0, 0)
        self.pages.updateGeometry()

        return page

    def _open_project_page(
        self,
        *,
        page,
        navigation_key: str,
        cache_key: str,
        loader,
        force_reload: bool = False,
    ) -> None:
        """
        Evita recarregar os mesmos dados em toda troca de tela.

        A página só executa o carregamento completo quando:
        - é aberta pela primeira vez;
        - o projeto mudou;
        - foi solicitado force_reload.
        """
        if self.current_project is None:
            return

        project_key = (
            self.current_project.id
            if self.current_project.id is not None
            else self.current_project.report_id
        )

        already_loaded = (
            self._loaded_page_projects.get(cache_key)
            == project_key
        )

        if not already_loaded or force_reload:
            QApplication.setOverrideCursor(
                Qt.CursorShape.WaitCursor
            )

            try:
                loader()
                self._loaded_page_projects[cache_key] = project_key
            finally:
                QApplication.restoreOverrideCursor()

        self.set_current_page(
            page,
            navigation_key,
        )

    def ensure_new_project_page(self):
        if self.new_project_page is None:
            self.new_project_page = self._create_page(NewProjectPage)
            self.new_project_page.back_requested.connect(
                self.show_home
            )
            self.new_project_page.create_requested.connect(
                self.create_project
            )

        return self.new_project_page

    def ensure_processes_page(self):
        if self.processes_page is None:
            self.processes_page = self._create_page(
                ProcessesPage
            )

            self.processes_page.back_requested.connect(
                self.show_home
            )

            self.processes_page.open_project_requested.connect(
                self.open_project
            )

            self.processes_page.new_project_requested.connect(
                self.show_new_project
            )

            self.processes_page.refresh_requested.connect(
                self.refresh_processes_and_home
            )

        return self.processes_page

    def ensure_overview_page(self):
        if self.overview_page is None:
            self.overview_page = self._create_page(OverviewPage)
            self.overview_page.home_requested.connect(
                self.show_home
            )
            self.overview_page.report_requested.connect(
                self.show_documents
            )
            self.overview_page.characteristics_requested.connect(
                self.show_characteristics
            )
            self.overview_page.measurement_requested.connect(
                self.show_measurement
            )
            self.overview_page.images_requested.connect(
                self.show_images
            )
            self.overview_page.technical_control_requested.connect(
                self.show_technical_control
            )
            self.overview_page.final_report_requested.connect(
                self.show_final_report
            )

        return self.overview_page

    def ensure_documents_page(self):
        if self.documents_page is None:
            self.documents_page = self._create_page(DocumentsPage)
            self.documents_page.back_requested.connect(
                self.show_current_overview
            )
            self.documents_page.open_document_requested.connect(
                self.show_document
            )
            self.documents_page.add_documents_requested.connect(
                self.add_documents_to_current_project
            )

        return self.documents_page

    def ensure_report_page(self):
        if self.report_page is None:
            self.report_page = self._create_page(ReportPage)
            self.report_page.back_requested.connect(
                self.show_documents
            )
            self.report_page.extraction_requested.connect(
                self.show_extraction_review
            )

        return self.report_page

    def ensure_extraction_review_page(self):
        if self.extraction_review_page is None:
            self.extraction_review_page = self._create_page(ExtractionReviewPage)
            self.extraction_review_page.back_requested.connect(
                self.return_from_extraction_review
            )

        return self.extraction_review_page

    def ensure_characteristics_page(self):
        if self.characteristics_page is None:
            self.characteristics_page = self._create_page(CharacteristicsPage)
            self.characteristics_page.back_requested.connect(
                self.show_current_overview
            )

        return self.characteristics_page

    def ensure_measurement_page(self):
        if self.measurement_page is None:
            self.measurement_page = self._create_page(MeasurementPage)
            self.measurement_page.back_requested.connect(
                self.show_current_overview
            )

        return self.measurement_page

    def ensure_images_page(self):
        if self.images_page is None:
            self.images_page = self._create_page(ImagesPage)
            self.images_page.back_requested.connect(
                self.show_current_overview
            )
            self.images_page.edit_image_requested.connect(
                self.show_image_editor
            )

        return self.images_page

    def ensure_image_editor(self):
        if self.image_editor is None:
            self.image_editor = self._create_page(ImageEditor)
            self.image_editor.back_requested.connect(
                self.show_images
            )

        return self.image_editor

    def ensure_technical_control_page(self):
        if self.technical_control_page is None:
            self.technical_control_page = self._create_page(TechnicalControlPage)
            self.technical_control_page.back_requested.connect(
                self.show_current_overview
            )

        return self.technical_control_page

    def ensure_final_report_page(self):
        if self.final_report_page is None:
            self.final_report_page = self._create_page(FinalReportPage)
            self.final_report_page.back_requested.connect(
                self.show_current_overview
            )
            self.final_report_page.documents_requested.connect(
                self.show_documents
            )
            self.final_report_page.characteristics_requested.connect(
                self.show_characteristics
            )
            self.final_report_page.measurement_requested.connect(
                self.show_measurement
            )
            self.final_report_page.images_requested.connect(
                self.show_images
            )
            self.final_report_page.technical_control_requested.connect(
                self.show_technical_control
            )
            self.final_report_page.generate_requested.connect(
                self.generate_final_report
            )

        return self.final_report_page

    def ensure_final_report_preview_page(self):
        if self.final_report_preview_page is None:
            self.final_report_preview_page = self._create_page(
                FinalReportPreviewPage
            )
            self.final_report_preview_page.back_requested.connect(
                self.show_final_report
            )
            self.final_report_preview_page.approve_export_requested.connect(
                self.approve_and_export_final_report
            )

        return self.final_report_preview_page

    # =============================================================
    # HOME
    # =============================================================

    def show_home(self) -> None:
        self.current_project = None

        self.current_document_id = None

        self.last_final_report_payload = None

        self.last_generated_report_path = None
        self._loaded_page_projects.clear()

        self.refresh_home()

        self.update_project_navigation()

        self.set_current_page(
            self.home_page,
            "home",
        )

    def refresh_home(self) -> None:
        try:
            projects = (
                self.project_service
                .get_recent_projects()
            )

            self.home_page.set_recent_projects(
                projects
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao carregar processos",
                str(
                    error
                ),
            )

    # =============================================================
    # CENTRAL DE PROCESSOS
    # =============================================================

    def show_processes(self) -> None:
        """
        Abre a central global de processos.

        Entrar nesta área encerra o contexto do processo que estava
        aberto. Assim, os módulos técnicos da sidebar voltam a ficar
        bloqueados até que um processo seja aberto novamente.
        """
        self.current_project = None
        self.current_document_id = None

        self.last_final_report_payload = None
        self.last_generated_report_path = None

        self._loaded_page_projects.clear()

        self.update_project_navigation()

        try:
            page = self.ensure_processes_page()

            page.set_projects(
                self.project_service.get_all_projects()
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir processos",
                str(error),
            )
            return

        self.set_current_page(
            page,
            "processes",
        )

    def refresh_processes_and_home(
        self,
    ) -> None:
        try:
            if self.processes_page is not None:
                self.processes_page.set_projects(
                    self.project_service.get_all_projects()
                )

            self.refresh_home()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao atualizar processos",
                str(error),
            )

    # =============================================================
    # NOVO PROCESSO
    # =============================================================

    def show_new_project(self) -> None:
        page = self.ensure_new_project_page()
        page.reset_page()

        self.set_current_page(
            page,
            "home",
        )

    def create_project(
        self,
        data,
        draft,
    ) -> None:
        try:
            project = (
                self.project_service
                .create_project(
                    data
                )
            )

            if project.id is None:
                raise RuntimeError(
                    (
                        "O processo foi criado sem "
                        "um identificador válido."
                    )
                )

            if (
                draft is not None
                and getattr(
                    draft,
                    "documents",
                    None,
                )
            ):
                self._persist_project_documents(
                    project=project,
                    draft=draft,
                )

            elif (
                draft is not None
                and draft.source_path
            ):
                imported_document = (
                    self.pdf_service.add_pdf(
                        project_id=project.id,
                        report_id=project.report_id,
                        source_path=(
                            draft.source_path
                        ),
                    )
                )

                if (
                    imported_document.id
                    is not None
                    and draft.parsed_report
                    is not None
                ):
                    self.extraction_service.persist_draft(
                        project_id=project.id,
                        draft=draft,
                        document_id=(
                            imported_document.id
                        ),
                    )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Não foi possível criar",
                str(
                    error
                ),
            )

            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao criar processo",
                (
                    "O processo não pôde ser "
                    "concluído corretamente.\n\n"
                    f"Detalhes: {error}"
                ),
            )

            return

        self.show_overview(
            project
        )

    def _persist_project_documents(
        self,
        project,
        draft,
    ) -> None:
        if project.id is None:
            raise ValueError(
                (
                    "O processo não possui "
                    "identificador."
                )
            )

        failures = []

        ordered_documents = sorted(
            draft.documents,
            key=lambda document:
                document.document_order,
        )

        for document_draft in ordered_documents:
            try:
                stored_document = (
                    self.pdf_service.add_pdf(
                        project_id=project.id,
                        report_id=(
                            project.report_id
                        ),
                        source_path=(
                            document_draft.source_path
                        ),
                        specimen_identifier=(
                            document_draft.specimen_identifier
                        ),
                    )
                )

                if stored_document.id is None:
                    raise RuntimeError(
                        (
                            "O documento foi salvo sem "
                            "um identificador válido."
                        )
                    )

                if (
                    document_draft.parsed_report
                    is not None
                ):
                    self.extraction_service.persist_document_draft(
                        project_id=project.id,
                        document_id=stored_document.id,
                        draft=document_draft,
                    )

                elif document_draft.failed:
                    self.pdf_service.update_document_analysis(
                        document_id=stored_document.id,
                        status="Falha",
                        source_type=(
                            document_draft.source_type
                            or "UNKNOWN"
                        ),
                        message=(
                            document_draft.analysis_error
                            or (
                                "A extração automática "
                                "não foi concluída."
                            )
                        ),
                    )

                else:
                    self.pdf_service.update_document_analysis(
                        document_id=stored_document.id,
                        status="Pendente",
                        source_type=(
                            document_draft.source_type
                            or "UNKNOWN"
                        ),
                        message=None,
                    )

            except Exception as error:
                failures.append(
                    (
                        f"{document_draft.file_name}: "
                        f"{error}"
                    )
                )

        if failures:
            QMessageBox.warning(
                self,
                "Processo criado com pendências",
                (
                    "O processo foi criado, mas alguns "
                    "documentos não puderam ser "
                    "armazenados corretamente:\n\n"
                    + "\n".join(
                        failures
                    )
                ),
            )

    # =============================================================
    # ABRIR PROCESSO
    # =============================================================

    def open_project(
        self,
        report_id: str,
    ) -> None:
        try:
            project = (
                self.project_service
                .get_project(
                    report_id
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir processo",
                str(
                    error
                ),
            )

            return

        if project is None:
            QMessageBox.warning(
                self,
                "Processo não encontrado",
                (
                    "O processo solicitado "
                    "não foi encontrado."
                ),
            )

            return

        self.show_overview(
            project
        )

    # =============================================================
    # VISÃO GERAL
    # =============================================================

    def show_overview(
        self,
        project,
    ) -> None:
        project_changed = (
            self.current_project is None
            or self.current_project.id != project.id
        )

        self.current_project = project
        self.current_document_id = None

        if project_changed:
            self._loaded_page_projects.clear()

        page = self.ensure_overview_page()

        self.update_project_navigation()

        try:
            self._open_project_page(
                page=page,
                navigation_key="overview",
                cache_key="overview",
                loader=lambda: page.set_project(project),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir visão geral",
                str(error),
            )
            return


    def show_current_overview(
        self,
    ) -> None:
        if self.current_project is None:
            self.show_home()

            return

        self.show_overview(
            self.current_project
        )

    # =============================================================
    # DOCUMENTOS
    # =============================================================

    def show_documents(
        self,
    ) -> None:
        if self.current_project is None:
            return

        page = self.ensure_documents_page()
        project = self.current_project

        try:
            self._open_project_page(
                page=page,
                navigation_key="documents",
                cache_key="documents",
                loader=lambda: page.set_project(project),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir documentos",
                str(error),
            )

    def show_document(
        self,
        document_id: int,
    ) -> None:
        if self.current_project is None:
            return

        self.current_document_id = document_id

        page = self.ensure_report_page()
        cache_key = f"report:{document_id}"
        project = self.current_project

        try:
            project_key = (
                project.id
                if project.id is not None
                else project.report_id
            )

            if (
                self._loaded_page_projects.get(cache_key)
                != project_key
            ):
                QApplication.setOverrideCursor(
                    Qt.CursorShape.WaitCursor
                )
                try:
                    page.set_document(
                        project=project,
                        document_id=document_id,
                    )
                    self._loaded_page_projects[cache_key] = project_key
                finally:
                    QApplication.restoreOverrideCursor()

            self.set_current_page(
                page,
                "documents",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir documento",
                str(error),
            )

    def add_documents_to_current_project(
        self,
    ) -> None:
        if (
            self.current_project is None
            or self.current_project.id
            is None
        ):
            return

        file_paths, _ = (
            QFileDialog.getOpenFileNames(
                self,
                (
                    "Adicionar documentos "
                    "ao processo"
                ),
                "",
                "Arquivos PDF (*.pdf)",
            )
        )

        if not file_paths:
            return

        try:
            (
                added_documents,
                import_failures,
            ) = self.pdf_service.add_pdfs(
                project_id=(
                    self.current_project.id
                ),
                report_id=(
                    self.current_project.report_id
                ),
                source_paths=file_paths,
            )

            analysis_failures = []

            for document in added_documents:
                if document.id is None:
                    continue

                try:
                    self.extraction_service.analyze_document(
                        project_id=(
                            self.current_project.id
                        ),
                        document_id=document.id,
                    )

                except Exception as error:
                    analysis_failures.append(
                        (
                            f"{document.file_name}: "
                            f"{error}"
                        )
                    )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao adicionar documentos",
                str(
                    error
                ),
            )

            return

        messages = []

        if added_documents:
            messages.append(
                (
                    f"{len(added_documents)} "
                    "documento(s) adicionado(s)."
                )
            )

        if import_failures:
            messages.append(
                (
                    f"{len(import_failures)} arquivo(s) "
                    "não puderam ser importados."
                )
            )

        if analysis_failures:
            messages.append(
                (
                    f"{len(analysis_failures)} documento(s) "
                    "ficaram com falha na análise."
                )
            )

        QMessageBox.information(
            self,
            "Documentos atualizados",
            (
                "\n".join(
                    messages
                )
                or "Nenhuma alteração realizada."
            ),
        )

        page = self.ensure_documents_page()
        page.set_project(
            self.current_project
        )

    # =============================================================
    # REVISÃO
    # =============================================================

    def show_extraction_review(
        self,
    ) -> None:
        if (
            self.current_project is None
            or self.current_document_id
            is None
        ):
            QMessageBox.warning(
                self,
                "Documento não selecionado",
                (
                    "Abra um documento antes de "
                    "revisar os dados extraídos."
                ),
            )

            return

        try:
            page = self.ensure_extraction_review_page()
            page.set_document(
                project=self.current_project,
                document_id=(
                    self.current_document_id
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir revisão",
                str(
                    error
                ),
            )

            return

        self.set_current_page(
            page,
            "documents",
        )

    def return_from_extraction_review(
        self,
    ) -> None:
        if self.current_document_id is not None:
            self.show_document(
                self.current_document_id
            )

            return

        self.show_documents()

    # =============================================================
    # CARACTERÍSTICAS
    # =============================================================

    def show_characteristics(
        self,
    ) -> None:
        if self.current_project is None:
            return

        page = self.ensure_characteristics_page()
        project = self.current_project

        try:
            self._open_project_page(
                page=page,
                navigation_key="characteristics",
                cache_key="characteristics",
                loader=lambda: page.set_project(project),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir características",
                str(error),
            )

    # =============================================================
    # MEDIÇÃO
    # =============================================================

    def show_measurement(
        self,
    ) -> None:
        if self.current_project is None:
            return

        page = self.ensure_measurement_page()
        project = self.current_project

        try:
            self._open_project_page(
                page=page,
                navigation_key="measurement",
                cache_key="measurement",
                loader=lambda: page.set_project(project),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir medição",
                str(error),
            )

    # =============================================================
    # IMAGENS
    # =============================================================

    def show_images(
        self,
    ) -> None:
        if self.current_project is None:
            return

        page = self.ensure_images_page()
        project = self.current_project

        try:
            self._open_project_page(
                page=page,
                navigation_key="images",
                cache_key="images",
                loader=lambda: page.set_project(project),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir imagens",
                str(error),
            )

    def show_image_editor(
        self,
        image,
    ) -> None:
        try:
            page = self.ensure_image_editor()
            page.set_image(
                image
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir editor",
                str(
                    error
                ),
            )

            return

        self.set_current_page(
            page,
            "images",
        )

    # =============================================================
    # CONTROLE TÉCNICO
    # =============================================================

    def show_technical_control(
        self,
    ) -> None:
        if self.current_project is None:
            return

        page = self.ensure_technical_control_page()
        project = self.current_project

        try:
            self._open_project_page(
                page=page,
                navigation_key="technical",
                cache_key="technical_control",
                loader=lambda: page.set_project(project),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir controle técnico",
                str(error),
            )

    # =============================================================
    # RELATÓRIO FINAL
    # =============================================================

    def show_final_report(
        self,
    ) -> None:
        if self.current_project is None:
            return

        page = self.ensure_final_report_page()
        project = self.current_project

        try:
            self._open_project_page(
                page=page,
                navigation_key="final_report",
                cache_key="final_report",
                loader=lambda: page.set_project(project),
                force_reload=True,
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao preparar relatório final",
                str(error),
            )

    def generate_final_report(
        self,
        payload: dict,
    ) -> None:
        """
        Gera um PDF temporário para pré-visualização.

        Nenhuma janela de salvamento é exibida nesta etapa.
        """
        project = payload.get(
            "project"
        )

        context = payload.get(
            "context",
            {},
        )

        sections = payload.get(
            "sections",
            {},
        )

        if (
            project is None
            or project.id is None
        ):
            QMessageBox.warning(
                self,
                "Processo inválido",
                (
                    "Não foi possível identificar "
                    "o processo atual."
                ),
            )
            return

        preview_directory = (
            Path(__file__)
            .resolve()
            .parent
            .parent
            / "projects"
            / project.report_id
            / "previews"
        )

        preview_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        preview_path = (
            preview_directory
            / (
                f"{project.report_id}_"
                "pre_visualizacao.pdf"
            )
        )

        report_page = self.ensure_final_report_page()
        preview_page = self.ensure_final_report_preview_page()

        # Libera qualquer PDF de pré-visualização que ainda esteja
        # aberto no PdfViewer antes de sobrescrever o arquivo temporário.
        # No Windows, o fitz mantém um handle aberto enquanto o documento
        # está carregado, o que provoca WinError 32 ao tentar substituir
        # a pré-visualização anterior.
        preview_page.clear_preview()

        # Remove referências a uma geração anterior para impedir que uma
        # prévia antiga continue disponível caso a nova geração falhe.
        self.last_final_report_payload = None
        self.last_generated_report_path = None

        report_page.set_generating(
            True
        )

        try:
            generated_path = (
                self.final_report_generator
                .generate(
                    project=project,
                    context=context,
                    sections=sections,
                    output_path=preview_path,
                )
            )

            payload[
                "report_version"
            ] = (
                self.report_version_service
                .normalize_version(
                    project.version
                )
            )

            self.last_final_report_payload = (
                payload
            )

            self.last_generated_report_path = (
                generated_path
            )

            preview_page.set_export_allowed(
                bool(
                    project.id is not None
                    and self.technical_control_service.can_issue_report(
                        project.id
                    )
                )
            )

            preview_page.set_pdf(
                generated_path
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao gerar pré-visualização",
                (
                    "O PDF temporário não pôde ser gerado.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        finally:
            report_page.set_generating(
                False
            )

        self.set_current_page(
            preview_page,
            "final_report",
        )

    def approve_and_export_final_report(
        self,
    ) -> None:
        """
        Exporta a pré-visualização como relatório oficial.

        A emissão somente é permitida com Controle Técnico aprovado.
        A versão emitida é registrada no histórico e o processo avança
        para a próxima versão de trabalho.
        """
        if (
            self.last_final_report_payload is None
            or self.last_generated_report_path is None
            or not self.last_generated_report_path.exists()
        ):
            QMessageBox.warning(
                self,
                "Pré-visualização indisponível",
                (
                    "Gere uma pré-visualização válida "
                    "antes de exportar o relatório."
                ),
            )
            return

        project = (
            self.last_final_report_payload.get(
                "project"
            )
        )

        if (
            project is None
            or project.id is None
        ):
            QMessageBox.warning(
                self,
                "Processo inválido",
                (
                    "Não foi possível identificar "
                    "o processo atual."
                ),
            )
            return

        if not self.technical_control_service.can_issue_report(
            project.id
        ):
            QMessageBox.warning(
                self,
                "Controle técnico pendente",
                (
                    "A pré-visualização pode ser consultada normalmente, "
                    "mas a exportação oficial exige Controle Técnico "
                    "com status 'Aprovado' e responsáveis de elaboração "
                    "e aprovação preenchidos."
                ),
            )

            preview_page = (
                self.ensure_final_report_preview_page()
            )
            preview_page.set_export_allowed(
                False
            )
            return

        try:
            emission_version = (
                self.report_version_service
                .normalize_version(
                    self.last_final_report_payload.get(
                        "report_version",
                        project.version,
                    )
                )
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Versão inválida",
                str(error),
            )
            return

        default_name = (
            f"{project.report_id}_"
            f"{self.sanitize_file_name(project.name)}_"
            f"{emission_version}.pdf"
        )

        export_directory = (
            Path(__file__)
            .resolve()
            .parent
            .parent
            / "projects"
            / project.report_id
            / "exports"
        )

        export_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        initial_path = (
            export_directory
            / default_name
        )

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar relatório",
            str(initial_path),
            "Arquivo PDF (*.pdf)",
        )

        if not output_path:
            return

        destination = Path(
            output_path
        )

        if destination.suffix.lower() != ".pdf":
            destination = destination.with_suffix(
                ".pdf"
            )

        preview_page = (
            self.ensure_final_report_preview_page()
        )

        preview_page.set_exporting(
            True
        )

        file_was_created = False

        try:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if destination.exists():
                destination.unlink()

            shutil.copy2(
                self.last_generated_report_path,
                destination,
            )

            file_was_created = True

            # Busca o controle novamente no banco para registrar a
            # emissão com o estado técnico realmente aprovado.
            technical_control = (
                self.technical_control_service
                .get_control(
                    project.id
                )
            )

            emission = (
                self.report_version_service
                .register_emission(
                    project=project,
                    version=emission_version,
                    file_path=destination,
                    technical_control=technical_control,
                )
            )

        except Exception as error:
            if (
                file_was_created
                and destination.exists()
            ):
                try:
                    destination.unlink()
                except OSError:
                    pass

            QMessageBox.critical(
                self,
                "Erro ao emitir relatório",
                (
                    "O relatório não pôde ser concluído "
                    "com rastreabilidade de versão.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        finally:
            preview_page.set_exporting(
                False
            )

        self.last_final_report_payload = None
        self.last_generated_report_path = None

        preview_page.clear_preview()

        self.current_project = project
        self._loaded_page_projects.clear()

        QMessageBox.information(
            self,
            "Relatório emitido",
            (
                "O relatório foi exportado e registrado "
                "no histórico de versões.\n\n"
                f"Versão emitida: {emission.version}\n"
                f"Próxima versão de trabalho: {project.version}\n\n"
                f"{destination}"
            ),
        )

        self.show_final_report()

    # =============================================================
    # ARQUIVO
    # =============================================================

    def sanitize_file_name(
        self,
        value: str,
    ) -> str:
        invalid_characters = (
            '<>:"/\\|?*'
        )

        result = str(
            value
            or "relatorio"
        )

        for character in invalid_characters:
            result = result.replace(
                character,
                "_",
            )

        result = "_".join(
            result.split()
        )

        return (
            result[:80]
            or "relatorio"
        )