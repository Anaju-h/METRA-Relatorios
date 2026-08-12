from database.connection import get_connection
from models.characteristic import Characteristic


class CharacteristicRepository:
    """
    Persistência das características extraídas.

    Cada característica pertence a uma extração específica.
    Consequentemente, cada documento mantém seus próprios
    resultados técnicos.
    """

    # =============================================================
    # EXCLUIR POR EXTRAÇÃO
    # =============================================================

    def delete_by_extraction_id(
        self,
        extraction_id: int,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM characteristics
                WHERE extraction_id = ?
                """,
                (extraction_id,),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # CRIAR
    # =============================================================

    def create(
        self,
        characteristic: Characteristic,
    ) -> Characteristic:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO characteristics (
                    extraction_id,

                    name,
                    group_name,

                    datum,
                    property_name,

                    measured_value,
                    nominal_value,

                    upper_tolerance,
                    lower_tolerance,

                    deviation,
                    unit,

                    status,

                    check_value,
                    out_value,

                    confidence,
                    extraction_method,

                    source_page,
                    raw_text,

                    extra_data_json,

                    created_at,
                    updated_at
                )
                VALUES (
                    ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?,
                    ?, ?
                )
                """,
                (
                    characteristic.extraction_id,

                    characteristic.name,
                    characteristic.group_name,

                    characteristic.datum,
                    characteristic.property_name,

                    characteristic.measured_value,
                    characteristic.nominal_value,

                    characteristic.upper_tolerance,
                    characteristic.lower_tolerance,

                    characteristic.deviation,
                    characteristic.unit,

                    characteristic.status,

                    characteristic.check_value,
                    characteristic.out_value,

                    characteristic.confidence,
                    characteristic.extraction_method,

                    characteristic.source_page,
                    characteristic.raw_text,

                    characteristic.extra_data_json,

                    characteristic.created_at,
                    characteristic.updated_at,
                ),
            )

            connection.commit()

            characteristic.id = (
                cursor.lastrowid
            )

            return characteristic

        finally:
            connection.close()

    # =============================================================
    # LISTAR POR EXTRAÇÃO
    # =============================================================

    def find_by_extraction_id(
        self,
        extraction_id: int,
    ) -> list[Characteristic]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM characteristics
                WHERE extraction_id = ?
                ORDER BY
                    CASE
                        WHEN source_page IS NULL
                            THEN 999999
                        ELSE source_page
                    END ASC,
                    id ASC
                """,
                (extraction_id,),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_characteristic(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    # =============================================================
    # LISTAR POR PROJETO
    # =============================================================

    def find_by_project_id(
        self,
        project_id: int,
    ) -> list[Characteristic]:
        """
        Retorna as características de todos os documentos
        pertencentes ao projeto.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    characteristic.*
                FROM characteristics AS characteristic

                INNER JOIN report_extractions AS extraction
                    ON extraction.id =
                        characteristic.extraction_id

                LEFT JOIN project_documents AS document
                    ON document.id =
                        extraction.document_id

                WHERE extraction.project_id = ?

                ORDER BY
                    CASE
                        WHEN document.document_order IS NULL
                            THEN 999999
                        ELSE document.document_order
                    END ASC,

                    CASE
                        WHEN characteristic.source_page IS NULL
                            THEN 999999
                        ELSE characteristic.source_page
                    END ASC,

                    characteristic.id ASC
                """,
                (project_id,),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_characteristic(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    # =============================================================
    # ATUALIZAR
    # =============================================================

    def update(
        self,
        characteristic: Characteristic,
    ) -> None:
        if characteristic.id is None:
            raise ValueError(
                (
                    "A característica não possui "
                    "um identificador válido."
                )
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE characteristics
                SET
                    name = ?,
                    group_name = ?,

                    datum = ?,
                    property_name = ?,

                    measured_value = ?,
                    nominal_value = ?,

                    upper_tolerance = ?,
                    lower_tolerance = ?,

                    deviation = ?,
                    unit = ?,

                    status = ?,

                    check_value = ?,
                    out_value = ?,

                    confidence = ?,
                    extraction_method = ?,

                    source_page = ?,
                    raw_text = ?,

                    extra_data_json = ?,

                    updated_at = ?

                WHERE id = ?
                """,
                (
                    characteristic.name,
                    characteristic.group_name,

                    characteristic.datum,
                    characteristic.property_name,

                    characteristic.measured_value,
                    characteristic.nominal_value,

                    characteristic.upper_tolerance,
                    characteristic.lower_tolerance,

                    characteristic.deviation,
                    characteristic.unit,

                    characteristic.status,

                    characteristic.check_value,
                    characteristic.out_value,

                    characteristic.confidence,
                    characteristic.extraction_method,

                    characteristic.source_page,
                    characteristic.raw_text,

                    characteristic.extra_data_json,

                    characteristic.updated_at,

                    characteristic.id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # CONVERTER LINHA
    # =============================================================

    def _row_to_characteristic(
        self,
        row,
    ) -> Characteristic:
        return Characteristic(
            id=row["id"],

            extraction_id=row[
                "extraction_id"
            ],

            name=row[
                "name"
            ],

            group_name=row[
                "group_name"
            ],

            datum=row[
                "datum"
            ],

            property_name=row[
                "property_name"
            ],

            measured_value=row[
                "measured_value"
            ],

            nominal_value=row[
                "nominal_value"
            ],

            upper_tolerance=row[
                "upper_tolerance"
            ],

            lower_tolerance=row[
                "lower_tolerance"
            ],

            deviation=row[
                "deviation"
            ],

            unit=row[
                "unit"
            ],

            status=row[
                "status"
            ],

            check_value=row[
                "check_value"
            ],

            out_value=row[
                "out_value"
            ],

            confidence=(
                row["confidence"]
                or 0.0
            ),

            extraction_method=row[
                "extraction_method"
            ],

            source_page=row[
                "source_page"
            ],

            raw_text=row[
                "raw_text"
            ],

            extra_data_json=row[
                "extra_data_json"
            ],

            created_at=row[
                "created_at"
            ],

            updated_at=row[
                "updated_at"
            ],
        )