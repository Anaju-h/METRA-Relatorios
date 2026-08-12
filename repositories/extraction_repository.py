from typing import Optional

from database.connection import get_connection
from models.extracted_report import ExtractedReport


class ExtractionRepository:
    """
    Persistência das extrações documentais.

    Relação principal:

        Project
            1 ─── N ProjectDocument
            1 ─── N ExtractedReport

        ProjectDocument
            1 ─── 1 ExtractedReport
    """

    # =============================================================
    # BUSCAR POR DOCUMENTO
    # =============================================================

    def find_by_document_id(
        self,
        document_id: int,
    ) -> Optional[ExtractedReport]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_extractions
                WHERE document_id = ?
                LIMIT 1
                """,
                (document_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_extraction(
                row
            )

        finally:
            connection.close()

    # =============================================================
    # LISTAR TODAS DO PROJETO
    # =============================================================

    def find_all_by_project_id(
        self,
        project_id: int,
    ) -> list[ExtractedReport]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    extraction.*
                FROM report_extractions AS extraction

                LEFT JOIN project_documents AS document
                    ON document.id = extraction.document_id

                WHERE extraction.project_id = ?

                ORDER BY
                    CASE
                        WHEN document.document_order IS NULL
                            THEN 999999
                        ELSE document.document_order
                    END ASC,

                    extraction.id ASC
                """,
                (project_id,),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_extraction(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    # =============================================================
    # COMPATIBILIDADE — EXTRAÇÃO PRINCIPAL
    # =============================================================

    def find_by_project_id(
        self,
        project_id: int,
    ) -> Optional[ExtractedReport]:
        """
        Retorna a primeira extração do projeto.

        Este método permanece temporariamente porque algumas telas
        antigas ainda trabalham com apenas uma extração.

        Novos fluxos devem usar find_all_by_project_id().
        """

        extractions = (
            self.find_all_by_project_id(
                project_id
            )
        )

        if not extractions:
            return None

        return extractions[0]

    # =============================================================
    # BUSCAR POR ID
    # =============================================================

    def find_by_id(
        self,
        extraction_id: int,
    ) -> Optional[ExtractedReport]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_extractions
                WHERE id = ?
                LIMIT 1
                """,
                (extraction_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_extraction(
                row
            )

        finally:
            connection.close()

    # =============================================================
    # SALVAR
    # =============================================================

    def save(
        self,
        extraction: ExtractedReport,
    ) -> ExtractedReport:
        existing = self._find_existing(
            extraction
        )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            if existing is None:
                self._insert(
                    cursor=cursor,
                    extraction=extraction,
                )

                extraction.id = (
                    cursor.lastrowid
                )

            else:
                extraction.id = existing.id

                extraction.created_at = (
                    existing.created_at
                )

                self._update(
                    cursor=cursor,
                    extraction=extraction,
                )

            connection.commit()

            return extraction

        finally:
            connection.close()

    # =============================================================
    # LOCALIZAR REGISTRO EXISTENTE
    # =============================================================

    def _find_existing(
        self,
        extraction: ExtractedReport,
    ) -> Optional[ExtractedReport]:
        if extraction.id is not None:
            return self.find_by_id(
                extraction.id
            )

        if extraction.document_id is not None:
            return self.find_by_document_id(
                extraction.document_id
            )

        # Compatibilidade para registros antigos sem document_id.
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_extractions
                WHERE
                    project_id = ?
                    AND document_id IS NULL
                ORDER BY id ASC
                LIMIT 1
                """,
                (extraction.project_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_extraction(
                row
            )

        finally:
            connection.close()

    # =============================================================
    # INSERT
    # =============================================================

    def _insert(
        self,
        cursor,
        extraction: ExtractedReport,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO report_extractions (
                project_id,
                document_id,

                source_type,

                document_title,
                analysis_type,

                part_name,
                part_number,

                machine_name,
                machine_number,
                equipment_origin,

                operator,
                measurement_datetime,

                measurement_count,
                out_of_tolerance_count,
                measurement_duration,

                software_name,
                software_version,

                alignment,
                length_unit,

                page_count,

                extraction_confidence,
                warnings_json,

                reviewed,

                created_at,
                updated_at
            )
            VALUES (
                ?, ?,
                ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?,
                ?,
                ?, ?
            )
            """,
            self._values(
                extraction
            ),
        )

    # =============================================================
    # UPDATE
    # =============================================================

    def _update(
        self,
        cursor,
        extraction: ExtractedReport,
    ) -> None:
        cursor.execute(
            """
            UPDATE report_extractions
            SET
                project_id = ?,
                document_id = ?,

                source_type = ?,

                document_title = ?,
                analysis_type = ?,

                part_name = ?,
                part_number = ?,

                machine_name = ?,
                machine_number = ?,
                equipment_origin = ?,

                operator = ?,
                measurement_datetime = ?,

                measurement_count = ?,
                out_of_tolerance_count = ?,
                measurement_duration = ?,

                software_name = ?,
                software_version = ?,

                alignment = ?,
                length_unit = ?,

                page_count = ?,

                extraction_confidence = ?,
                warnings_json = ?,

                reviewed = ?,

                updated_at = ?

            WHERE id = ?
            """,
            (
                extraction.project_id,
                extraction.document_id,

                extraction.source_type,

                extraction.document_title,
                extraction.analysis_type,

                extraction.part_name,
                extraction.part_number,

                extraction.machine_name,
                extraction.machine_number,
                extraction.equipment_origin,

                extraction.operator,
                extraction.measurement_datetime,

                extraction.measurement_count,
                extraction.out_of_tolerance_count,
                extraction.measurement_duration,

                extraction.software_name,
                extraction.software_version,

                extraction.alignment,
                extraction.length_unit,

                extraction.page_count,

                extraction.extraction_confidence,
                extraction.warnings_json,

                int(
                    extraction.reviewed
                ),

                extraction.updated_at,

                extraction.id,
            ),
        )

    # =============================================================
    # VALORES PARA INSERT
    # =============================================================

    def _values(
        self,
        extraction: ExtractedReport,
    ) -> tuple:
        return (
            extraction.project_id,
            extraction.document_id,

            extraction.source_type,

            extraction.document_title,
            extraction.analysis_type,

            extraction.part_name,
            extraction.part_number,

            extraction.machine_name,
            extraction.machine_number,
            extraction.equipment_origin,

            extraction.operator,
            extraction.measurement_datetime,

            extraction.measurement_count,
            extraction.out_of_tolerance_count,
            extraction.measurement_duration,

            extraction.software_name,
            extraction.software_version,

            extraction.alignment,
            extraction.length_unit,

            extraction.page_count,

            extraction.extraction_confidence,
            extraction.warnings_json,

            int(
                extraction.reviewed
            ),

            extraction.created_at,
            extraction.updated_at,
        )

    # =============================================================
    # EXCLUIR
    # =============================================================

    def delete_by_document_id(
        self,
        document_id: int,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM report_extractions
                WHERE document_id = ?
                """,
                (document_id,),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # CONVERTER LINHA
    # =============================================================

    def _row_to_extraction(
        self,
        row,
    ) -> ExtractedReport:
        return ExtractedReport(
            id=row["id"],

            project_id=row[
                "project_id"
            ],

            document_id=row[
                "document_id"
            ],

            source_type=row[
                "source_type"
            ],

            document_title=row[
                "document_title"
            ],

            analysis_type=row[
                "analysis_type"
            ],

            part_name=row[
                "part_name"
            ],

            part_number=row[
                "part_number"
            ],

            machine_name=row[
                "machine_name"
            ],

            machine_number=row[
                "machine_number"
            ],

            equipment_origin=row[
                "equipment_origin"
            ],

            operator=row[
                "operator"
            ],

            measurement_datetime=row[
                "measurement_datetime"
            ],

            measurement_count=row[
                "measurement_count"
            ],

            out_of_tolerance_count=row[
                "out_of_tolerance_count"
            ],

            measurement_duration=row[
                "measurement_duration"
            ],

            software_name=row[
                "software_name"
            ],

            software_version=row[
                "software_version"
            ],

            alignment=row[
                "alignment"
            ],

            length_unit=row[
                "length_unit"
            ],

            page_count=row[
                "page_count"
            ],

            extraction_confidence=row[
                "extraction_confidence"
            ],

            warnings_json=row[
                "warnings_json"
            ],

            reviewed=bool(
                row["reviewed"]
            ),

            created_at=row[
                "created_at"
            ],

            updated_at=row[
                "updated_at"
            ],
        )