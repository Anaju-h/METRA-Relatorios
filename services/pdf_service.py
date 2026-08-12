from __future__ import annotations

from pathlib import Path

from models.project_document import ProjectDocument
from services.project_document_service import ProjectDocumentService


class PDFService:
    """
    Fachada enxuta para operações de PDF usadas pela aplicação atual.

    Responsabilidades:
    - adicionar documentos ao processo;
    - listar documentos;
    - resolver o caminho físico de um documento;
    - renderizar páginas para o visualizador;
    - atualizar o status de análise.
    """

    def __init__(self):
        self.document_service = ProjectDocumentService()

    def add_pdf(
        self,
        project_id: int,
        report_id: str,
        source_path: str,
        specimen_identifier: str | None = None,
    ) -> ProjectDocument:
        return self.document_service.add_document(
            project_id=project_id,
            report_id=report_id,
            source_path=source_path,
            specimen_identifier=specimen_identifier,
        )

    def add_pdfs(
        self,
        project_id: int,
        report_id: str,
        source_paths: list[str],
    ) -> tuple[list[ProjectDocument], list[dict]]:
        return self.document_service.add_documents(
            project_id=project_id,
            report_id=report_id,
            source_paths=source_paths,
        )

    def get_project_documents(
        self,
        project_id: int,
        include_inactive: bool = False,
    ) -> list[ProjectDocument]:
        return self.document_service.get_project_documents(
            project_id=project_id,
            include_inactive=include_inactive,
        )

    def get_document_path(
        self,
        document_id: int,
    ) -> Path:
        return self.document_service.get_document_path(
            document_id
        )

    def render_document_page(
        self,
        document_id: int,
        page_index: int,
        zoom: float = 1.5,
    ) -> bytes:
        return self.document_service.render_document_page(
            document_id=document_id,
            page_index=page_index,
            zoom=zoom,
        )

    def update_document_analysis(
        self,
        document_id: int,
        status: str,
        source_type: str | None = None,
        page_count: int | None = None,
        message: str | None = None,
    ) -> ProjectDocument:
        return self.document_service.update_analysis_status(
            document_id=document_id,
            status=status,
            source_type=source_type,
            page_count=page_count,
            message=message,
        )