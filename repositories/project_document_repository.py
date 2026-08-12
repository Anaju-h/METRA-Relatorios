from typing import Optional

from database.connection import get_connection
from models.project_document import (
    ProjectDocument,
)


class ProjectDocumentRepository:
    """
    Repositório dos documentos originais de um projeto.

    Um projeto pode possuir vários documentos.
    """

    # =============================================================
    # CRIAR
    # =============================================================

    def create(
        self,
        document: ProjectDocument,
    ) -> ProjectDocument:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO project_documents (
                    project_id,

                    file_name,
                    stored_name,
                    file_path,

                    file_size,
                    file_hash,

                    document_order,
                    document_type,
                    specimen_identifier,

                    source_type,
                    page_count,

                    analysis_status,
                    analysis_message,

                    is_active,

                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    document.project_id,

                    document.file_name,
                    document.stored_name,
                    document.file_path,

                    document.file_size,
                    document.file_hash,

                    document.document_order,
                    document.document_type,
                    document.specimen_identifier,

                    document.source_type,
                    document.page_count,

                    document.analysis_status,
                    document.analysis_message,

                    int(
                        document.is_active
                    ),

                    document.created_at,
                    document.updated_at,
                ),
            )

            connection.commit()

            document.id = (
                cursor.lastrowid
            )

            return document

        finally:
            connection.close()

    # =============================================================
    # ATUALIZAR
    # =============================================================

    def update(
        self,
        document: ProjectDocument,
    ) -> ProjectDocument:
        if document.id is None:
            raise ValueError(
                "O documento não possui um identificador válido."
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE project_documents
                SET
                    file_name = ?,
                    stored_name = ?,
                    file_path = ?,

                    file_size = ?,
                    file_hash = ?,

                    document_order = ?,
                    document_type = ?,
                    specimen_identifier = ?,

                    source_type = ?,
                    page_count = ?,

                    analysis_status = ?,
                    analysis_message = ?,

                    is_active = ?,

                    updated_at = ?
                WHERE id = ?
                """,
                (
                    document.file_name,
                    document.stored_name,
                    document.file_path,

                    document.file_size,
                    document.file_hash,

                    document.document_order,
                    document.document_type,
                    document.specimen_identifier,

                    document.source_type,
                    document.page_count,

                    document.analysis_status,
                    document.analysis_message,

                    int(
                        document.is_active
                    ),

                    document.updated_at,

                    document.id,
                ),
            )

            connection.commit()

            return document

        finally:
            connection.close()

    # =============================================================
    # BUSCAR POR ID
    # =============================================================

    def find_by_id(
        self,
        document_id: int,
    ) -> Optional[ProjectDocument]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM project_documents
                WHERE id = ?
                """,
                (
                    document_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_document(
                row
            )

        finally:
            connection.close()

    # =============================================================
    # LISTAR DOCUMENTOS DO PROJETO
    # =============================================================

    def find_by_project_id(
        self,
        project_id: int,
        include_inactive: bool = False,
    ) -> list[ProjectDocument]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            if include_inactive:
                cursor.execute(
                    """
                    SELECT *
                    FROM project_documents
                    WHERE project_id = ?
                    ORDER BY
                        document_order ASC,
                        id ASC
                    """,
                    (
                        project_id,
                    ),
                )

            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM project_documents
                    WHERE
                        project_id = ?
                        AND is_active = 1
                    ORDER BY
                        document_order ASC,
                        id ASC
                    """,
                    (
                        project_id,
                    ),
                )

            rows = cursor.fetchall()

            return [
                self._row_to_document(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    # =============================================================
    # BUSCAR PELO HASH
    # =============================================================

    def find_by_project_and_hash(
        self,
        project_id: int,
        file_hash: str,
    ) -> Optional[ProjectDocument]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM project_documents
                WHERE
                    project_id = ?
                    AND file_hash = ?
                    AND is_active = 1
                LIMIT 1
                """,
                (
                    project_id,
                    file_hash,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_document(
                row
            )

        finally:
            connection.close()

    # =============================================================
    # CONTAGEM
    # =============================================================

    def count_by_project_id(
        self,
        project_id: int,
    ) -> int:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM project_documents
                WHERE
                    project_id = ?
                    AND is_active = 1
                """,
                (
                    project_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return 0

            return int(
                row["total"]
            )

        finally:
            connection.close()

    # =============================================================
    # PRÓXIMA ORDEM
    # =============================================================

    def get_next_order(
        self,
        project_id: int,
    ) -> int:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COALESCE(
                        MAX(document_order),
                        0
                    ) AS current_order
                FROM project_documents
                WHERE
                    project_id = ?
                    AND is_active = 1
                """,
                (
                    project_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return 1

            return (
                int(
                    row["current_order"]
                )
                + 1
            )

        finally:
            connection.close()

    # =============================================================
    # DESATIVAR
    # =============================================================

    def deactivate(
        self,
        document_id: int,
        updated_at: str,
    ) -> None:
        """
        Faz remoção lógica.

        O arquivo não é apagado imediatamente, preservando
        rastreabilidade e permitindo recuperação futura.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE project_documents
                SET
                    is_active = 0,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    updated_at,
                    document_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # REORDENAR
    # =============================================================

    def update_order(
        self,
        document_id: int,
        document_order: int,
        updated_at: str,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE project_documents
                SET
                    document_order = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    document_order,
                    updated_at,
                    document_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # CONVERTER LINHA
    # =============================================================

    def _row_to_document(
        self,
        row,
    ) -> ProjectDocument:
        return ProjectDocument(
            id=row["id"],

            project_id=row[
                "project_id"
            ],

            file_name=row[
                "file_name"
            ],

            stored_name=row[
                "stored_name"
            ],

            file_path=row[
                "file_path"
            ],

            file_size=row[
                "file_size"
            ],

            file_hash=row[
                "file_hash"
            ],

            document_order=row[
                "document_order"
            ],

            document_type=row[
                "document_type"
            ],

            specimen_identifier=row[
                "specimen_identifier"
            ],

            source_type=row[
                "source_type"
            ],

            page_count=row[
                "page_count"
            ],

            analysis_status=row[
                "analysis_status"
            ],

            analysis_message=row[
                "analysis_message"
            ],

            is_active=bool(
                row["is_active"]
            ),

            created_at=row[
                "created_at"
            ],

            updated_at=row[
                "updated_at"
            ],
        )   