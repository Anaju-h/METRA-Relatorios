from __future__ import annotations

from database.connection import get_connection
from models.annotation import Annotation


class AnnotationRepository:
    """
    Persistência das marcações vinculadas às imagens.
    """

    # =============================================================
    # CRIAR
    # =============================================================

    def create(
        self,
        annotation: Annotation,
    ) -> Annotation:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO annotations (
                    image_id,
                    annotation_type,

                    x,
                    y,
                    width,
                    height,

                    end_x,
                    end_y,

                    text,
                    marker_text,

                    font_size,
                    stroke_width,
                    color,

                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    annotation.image_id,
                    annotation.annotation_type,

                    annotation.x,
                    annotation.y,
                    annotation.width,
                    annotation.height,

                    annotation.end_x,
                    annotation.end_y,

                    annotation.text,
                    annotation.marker_text,

                    annotation.font_size,
                    annotation.stroke_width,
                    annotation.color,

                    annotation.created_at,
                    annotation.updated_at,
                ),
            )

            connection.commit()

            annotation.id = cursor.lastrowid

            return annotation

        finally:
            connection.close()

    # =============================================================
    # LISTAR POR IMAGEM
    # =============================================================

    def find_by_image_id(
        self,
        image_id: int,
    ) -> list[Annotation]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM annotations
                WHERE image_id = ?
                ORDER BY id ASC
                """,
                (image_id,),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_annotation(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    # =============================================================
    # EXCLUIR POR IMAGEM
    # =============================================================

    def delete_by_image_id(
        self,
        image_id: int,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM annotations
                WHERE image_id = ?
                """,
                (image_id,),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # CONTAR
    # =============================================================

    def count_by_image_id(
        self,
        image_id: int,
    ) -> int:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM annotations
                WHERE image_id = ?
                """,
                (image_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return 0

            return int(
                row["total"]
                or 0
            )

        finally:
            connection.close()

    # =============================================================
    # CONVERTER LINHA DO BANCO
    # =============================================================

    def _row_to_annotation(
        self,
        row,
    ) -> Annotation:
        return Annotation(
            id=row["id"],

            image_id=row[
                "image_id"
            ],

            annotation_type=row[
                "annotation_type"
            ],

            x=float(
                row["x"]
                or 0.0
            ),

            y=float(
                row["y"]
                or 0.0
            ),

            width=float(
                row["width"]
                or 0.0
            ),

            height=float(
                row["height"]
                or 0.0
            ),

            end_x=(
                float(
                    row["end_x"]
                )
                if row["end_x"]
                is not None
                else None
            ),

            end_y=(
                float(
                    row["end_y"]
                )
                if row["end_y"]
                is not None
                else None
            ),

            text=row[
                "text"
            ],

            marker_text=row[
                "marker_text"
            ],

            font_size=int(
                row["font_size"]
                or 18
            ),

            stroke_width=float(
                row["stroke_width"]
                or 3.0
            ),

            color=(
                row["color"]
                or "#EB2323"
            ),

            created_at=row[
                "created_at"
            ],

            updated_at=row[
                "updated_at"
            ],
        )