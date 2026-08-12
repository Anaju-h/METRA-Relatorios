from __future__ import annotations

import hashlib
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz

from models.project_document import (
    ProjectDocument,
)
from repositories.project_document_repository import (
    ProjectDocumentRepository,
)
from services.traceability_service import (
    TraceabilityService,
)


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"


class ProjectDocumentService:
    """
    Serviço responsável pelos documentos originais de um projeto.

    Um projeto pode possuir um ou vários PDFs.

    Responsabilidades:

    - validar arquivos;
    - detectar duplicidade;
    - copiar PDFs para o projeto;
    - gerar nomes seguros e únicos;
    - registrar os documentos no banco;
    - listar documentos;
    - remover logicamente;
    - recuperar caminhos físicos;
    - renderizar páginas.
    """

    def __init__(self):
        self.repository = (
            ProjectDocumentRepository()
        )

        self.traceability_service = (
            TraceabilityService()
        )

    # =============================================================
    # ADICIONAR UM DOCUMENTO
    # =============================================================

    def add_document(
        self,
        project_id: int,
        report_id: str,
        source_path: str,
        specimen_identifier: str | None = None,
        document_type: str = "Relatório de medição",
    ) -> ProjectDocument:
        """
        Copia um PDF para a pasta do projeto e o registra no banco.

        O método rejeita arquivos duplicados dentro do mesmo projeto
        usando SHA-256.
        """

        if project_id is None:
            raise ValueError(
                "O projeto não possui um identificador válido."
            )

        if not report_id:
            raise ValueError(
                "O projeto não possui um código válido."
            )

        source = Path(
            source_path
        )

        self._validate_pdf(
            source
        )

        file_hash = self.calculate_file_hash(
            source
        )

        duplicate = (
            self.repository
            .find_by_project_and_hash(
                project_id=project_id,
                file_hash=file_hash,
            )
        )

        if duplicate is not None:
            raise ValueError(
                (
                    "Este relatório já foi adicionado "
                    "ao projeto."
                )
            )

        document_order = (
            self.repository.get_next_order(
                project_id
            )
        )

        project_documents_dir = (
            self.get_project_documents_dir(
                report_id
            )
        )

        project_documents_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_original_name = (
            self._safe_file_name(
                source.stem
            )
        )

        stored_name = (
            self._build_stored_name(
                document_order=(
                    document_order
                ),
                safe_stem=(
                    safe_original_name
                ),
            )
        )

        destination = (
            project_documents_dir
            / stored_name
        )

        destination = (
            self._ensure_unique_destination(
                destination
            )
        )

        shutil.copy2(
            source,
            destination,
        )

        pdf_info = self.inspect_pdf(
            destination
        )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        document = ProjectDocument(
            project_id=project_id,

            file_name=source.name,

            stored_name=(
                destination.name
            ),

            file_path=str(
                destination.resolve()
            ),

            file_size=(
                destination.stat().st_size
            ),

            file_hash=file_hash,

            document_order=(
                document_order
            ),

            document_type=(
                document_type
            ),

            specimen_identifier=(
                specimen_identifier
            ),

            source_type="UNKNOWN",

            page_count=(
                pdf_info["page_count"]
            ),

            analysis_status="Pendente",

            analysis_message=None,

            is_active=True,

            created_at=now,
            updated_at=now,
        )

        try:
            created_document = (
                self.repository.create(
                    document
                )
            )

            self._invalidate_project_approval(
                project_id=project_id,
                reason=(
                    "Um novo documento técnico foi "
                    "adicionado ao processo."
                ),
            )

            return created_document

        except Exception:
            # Se o banco falhar, removemos a cópia criada
            # para evitar arquivo órfão.
            if destination.exists():
                destination.unlink()

            raise

    # =============================================================
    # ADICIONAR VÁRIOS DOCUMENTOS
    # =============================================================

    def add_documents(
        self,
        project_id: int,
        report_id: str,
        source_paths: list[str],
    ) -> tuple[
        list[ProjectDocument],
        list[dict],
    ]:
        """
        Adiciona vários documentos.

        Retorna:

            (
                documentos_adicionados,
                falhas
            )

        Uma falha não impede que os demais documentos sejam
        adicionados.
        """

        if not source_paths:
            raise ValueError(
                "Nenhum relatório foi selecionado."
            )

        added_documents = []
        failures = []

        for source_path in source_paths:
            try:
                document = self.add_document(
                    project_id=project_id,
                    report_id=report_id,
                    source_path=source_path,
                )

                added_documents.append(
                    document
                )

            except Exception as error:
                failures.append(
                    {
                        "source_path":
                            source_path,

                        "file_name":
                            Path(
                                source_path
                            ).name,

                        "error":
                            str(error),
                    }
                )

        return (
            added_documents,
            failures,
        )

    # =============================================================
    # LISTAR
    # =============================================================

    def get_project_documents(
        self,
        project_id: int,
        include_inactive: bool = False,
    ) -> list[ProjectDocument]:
        return (
            self.repository
            .find_by_project_id(
                project_id=project_id,
                include_inactive=(
                    include_inactive
                ),
            )
        )

    def get_document(
        self,
        document_id: int,
    ) -> Optional[ProjectDocument]:
        return self.repository.find_by_id(
            document_id
        )

    def count_project_documents(
        self,
        project_id: int,
    ) -> int:
        return (
            self.repository
            .count_by_project_id(
                project_id
            )
        )

    # =============================================================
    # CAMINHO
    # =============================================================

    def get_document_path(
        self,
        document_id: int,
    ) -> Path:
        document = self.get_document(
            document_id
        )

        if document is None:
            raise FileNotFoundError(
                "O documento solicitado não foi encontrado."
            )

        path = Path(
            document.file_path
        )

        if not path.exists():
            raise FileNotFoundError(
                (
                    "O registro do documento existe, "
                    "mas o arquivo físico não foi encontrado."
                )
            )

        return path

    def get_project_documents_dir(
        self,
        report_id: str,
    ) -> Path:
        return (
            PROJECTS_DIR
            / report_id
            / "documents"
        )

    # =============================================================
    # INSPEÇÃO
    # =============================================================

    def inspect_pdf(
        self,
        source_path: str | Path,
    ) -> dict:
        path = Path(
            source_path
        )

        self._validate_pdf(
            path
        )

        document = fitz.open(
            path
        )

        try:
            metadata = (
                document.metadata
                or {}
            )

            return {
                "path":
                    str(
                        path.resolve()
                    ),

                "file_name":
                    path.name,

                "page_count":
                    document.page_count,

                "title":
                    metadata.get(
                        "title"
                    ),

                "author":
                    metadata.get(
                        "author"
                    ),
            }

        finally:
            document.close()

    # =============================================================
    # RENDERIZAR PÁGINA
    # =============================================================

    def render_document_page(
        self,
        document_id: int,
        page_index: int,
        zoom: float = 1.5,
    ) -> bytes:
        path = self.get_document_path(
            document_id
        )

        return self.render_pdf_page(
            source_path=path,
            page_index=page_index,
            zoom=zoom,
        )

    def render_pdf_page(
        self,
        source_path: str | Path,
        page_index: int,
        zoom: float = 1.5,
    ) -> bytes:
        path = Path(
            source_path
        )

        self._validate_pdf(
            path
        )

        document = fitz.open(
            path
        )

        try:
            if (
                page_index < 0
                or page_index
                >= document.page_count
            ):
                raise IndexError(
                    "Página fora do intervalo do documento."
                )

            page = document.load_page(
                page_index
            )

            matrix = fitz.Matrix(
                zoom,
                zoom,
            )

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            return pixmap.tobytes(
                "png"
            )

        finally:
            document.close()

    # =============================================================
    # ATUALIZAR RESULTADO DA ANÁLISE
    # =============================================================

    def update_analysis_status(
        self,
        document_id: int,
        status: str,
        source_type: str | None = None,
        page_count: int | None = None,
        message: str | None = None,
    ) -> ProjectDocument:
        valid_statuses = {
            "Pendente",
            "Analisando",
            "Concluído",
            "Falha",
        }

        if status not in valid_statuses:
            raise ValueError(
                "Status de análise inválido."
            )

        document = self.get_document(
            document_id
        )

        if document is None:
            raise ValueError(
                "Documento não encontrado."
            )

        document.analysis_status = (
            status
        )

        document.analysis_message = (
            message
        )

        if source_type:
            document.source_type = (
                source_type
            )

        if page_count is not None:
            document.page_count = (
                page_count
            )

        document.updated_at = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        return self.repository.update(
            document
        )

    # =============================================================
    # IDENTIFICAÇÃO DA AMOSTRA
    # =============================================================

    def update_specimen_identifier(
        self,
        document_id: int,
        specimen_identifier: str | None,
    ) -> ProjectDocument:
        document = self.get_document(
            document_id
        )

        if document is None:
            raise ValueError(
                "Documento não encontrado."
            )

        clean_identifier = (
            specimen_identifier.strip()
            if specimen_identifier
            else None
        )

        normalized_identifier = (
            clean_identifier
            or None
        )

        changed = (
            document.specimen_identifier
            != normalized_identifier
        )

        document.specimen_identifier = (
            normalized_identifier
        )

        document.updated_at = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        updated_document = (
            self.repository.update(
                document
            )
        )

        if changed:
            self._invalidate_project_approval(
                project_id=document.project_id,
                reason=(
                    "A identificação de uma amostra "
                    "foi alterada."
                ),
            )

        return updated_document

    # =============================================================
    # REMOÇÃO LÓGICA
    # =============================================================

    def remove_document(
        self,
        document_id: int,
    ) -> None:
        document = self.get_document(
            document_id
        )

        if document is None:
            raise ValueError(
                "Documento não encontrado."
            )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        self.repository.deactivate(
            document_id=document_id,
            updated_at=now,
        )

        self._invalidate_project_approval(
            project_id=document.project_id,
            reason=(
                "Um documento técnico foi removido "
                "do processo."
            ),
        )

    # =============================================================
    # REORDENAR
    # =============================================================

    def reorder_documents(
        self,
        project_id: int,
        ordered_document_ids: list[int],
    ) -> None:
        documents = (
            self.get_project_documents(
                project_id
            )
        )

        available_ids = {
            document.id
            for document in documents
            if document.id is not None
        }

        received_ids = set(
            ordered_document_ids
        )

        if (
            available_ids
            != received_ids
        ):
            raise ValueError(
                (
                    "A lista de documentos informada "
                    "não corresponde aos documentos ativos "
                    "do projeto."
                )
            )

        current_order = [
            document.id
            for document in sorted(
                documents,
                key=lambda document: (
                    document.document_order,
                    document.id or 0,
                ),
            )
            if document.id is not None
        ]

        changed = (
            current_order
            != ordered_document_ids
        )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        for order, document_id in enumerate(
            ordered_document_ids,
            start=1,
        ):
            self.repository.update_order(
                document_id=document_id,
                document_order=order,
                updated_at=now,
            )

        if changed:
            self._invalidate_project_approval(
                project_id=project_id,
                reason=(
                    "A ordem dos documentos técnicos "
                    "foi alterada."
                ),
            )

    # =============================================================
    # RASTREABILIDADE
    # =============================================================

    def _invalidate_project_approval(
        self,
        *,
        project_id: int | None,
        reason: str,
    ) -> None:
        if project_id is None:
            return

        self.traceability_service.invalidate_technical_approval(
            project_id=project_id,
            reason=reason,
        )

    # =============================================================
    # HASH
    # =============================================================

    def calculate_file_hash(
        self,
        source_path: str | Path,
    ) -> str:
        path = Path(
            source_path
        )

        hasher = hashlib.sha256()

        with path.open(
            "rb"
        ) as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                hasher.update(
                    chunk
                )

        return hasher.hexdigest()

    # =============================================================
    # VALIDAÇÃO
    # =============================================================

    def _validate_pdf(
        self,
        path: Path,
    ) -> None:
        if not path.exists():
            raise FileNotFoundError(
                "O arquivo selecionado não foi encontrado."
            )

        if not path.is_file():
            raise ValueError(
                (
                    "O caminho informado não corresponde "
                    "a um arquivo."
                )
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "O arquivo selecionado não é um PDF."
            )

        if path.stat().st_size <= 0:
            raise ValueError(
                "O arquivo selecionado está vazio."
            )

    # =============================================================
    # NOME SEGURO
    # =============================================================

    def _safe_file_name(
        self,
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            value or "",
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        normalized = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            normalized,
        )

        normalized = re.sub(
            r"_+",
            "_",
            normalized,
        )

        normalized = normalized.strip(
            "_-"
        )

        return (
            normalized
            or "relatorio"
        )

    def _build_stored_name(
        self,
        document_order: int,
        safe_stem: str,
    ) -> str:
        return (
            f"{document_order:03d}_"
            f"{safe_stem}.pdf"
        )

    def _ensure_unique_destination(
        self,
        destination: Path,
    ) -> Path:
        if not destination.exists():
            return destination

        parent = destination.parent
        stem = destination.stem
        suffix = destination.suffix

        counter = 2

        while True:
            candidate = (
                parent
                / f"{stem}_{counter}{suffix}"
            )

            if not candidate.exists():
                return candidate

            counter += 1