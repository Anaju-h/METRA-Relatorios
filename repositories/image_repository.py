from datetime import datetime
from typing import Optional

from database.connection import get_connection
from models.project_image import ProjectImage


class ImageRepository:
    """
    Persistência das imagens vinculadas aos processos.
    """

    # =============================================================
    # CRIAR
    # =============================================================

    def create(
        self,
        image: ProjectImage,
    ) -> ProjectImage:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO project_images (
                    project_id,
                    file_path,
                    file_name,
                    image_type,
                    caption,
                    position,
                    is_primary,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image.project_id,
                    image.file_path,
                    image.file_name,
                    image.image_type,
                    image.caption,
                    image.position,
                    int(
                        image.is_primary
                    ),
                    image.created_at,
                    image.updated_at,
                ),
            )

            image.id = cursor.lastrowid

            connection.commit()

            return image

        finally:
            connection.close()

    # =============================================================
    # BUSCAR POR PROCESSO
    # =============================================================

    def find_by_project_id(
        self,
        project_id: int,
    ) -> list[ProjectImage]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM project_images
                WHERE project_id = ?
                ORDER BY
                    is_primary DESC,
                    position ASC,
                    id ASC
                """,
                (
                    project_id,
                ),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_image(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    # =============================================================
    # BUSCAR IMAGEM
    # =============================================================

    def find_by_id(
        self,
        image_id: int,
    ) -> Optional[ProjectImage]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM project_images
                WHERE id = ?
                """,
                (
                    image_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_image(
                row
            )

        finally:
            connection.close()

    # =============================================================
    # IMAGEM PRINCIPAL
    # =============================================================

    def find_primary_by_project_id(
        self,
        project_id: int,
    ) -> Optional[ProjectImage]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM project_images
                WHERE
                    project_id = ?
                    AND is_primary = 1
                LIMIT 1
                """,
                (
                    project_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_image(
                row
            )

        finally:
            connection.close()

    def set_primary(
        self,
        project_id: int,
        image_id: int,
        updated_at: str,
    ) -> None:
        """
        Define uma única imagem principal para o processo.

        A remoção da anterior e a definição da nova imagem
        acontecem na mesma transação.
        """

        connection = get_connection()

        try:
            connection.execute(
                """
                PRAGMA foreign_keys = ON
                """
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id
                FROM project_images
                WHERE
                    id = ?
                    AND project_id = ?
                """,
                (
                    image_id,
                    project_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                raise ValueError(
                    (
                        "A imagem selecionada não pertence "
                        "ao processo atual."
                    )
                )

            cursor.execute(
                """
                UPDATE project_images
                SET
                    is_primary = 0,
                    updated_at = ?
                WHERE
                    project_id = ?
                    AND is_primary = 1
                """,
                (
                    updated_at,
                    project_id,
                ),
            )

            cursor.execute(
                """
                UPDATE project_images
                SET
                    is_primary = 1,
                    updated_at = ?
                WHERE
                    id = ?
                    AND project_id = ?
                """,
                (
                    updated_at,
                    image_id,
                    project_id,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()

            raise

        finally:
            connection.close()

    def clear_primary(
        self,
        project_id: int,
        updated_at: str,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE project_images
                SET
                    is_primary = 0,
                    updated_at = ?
                WHERE
                    project_id = ?
                    AND is_primary = 1
                """,
                (
                    updated_at,
                    project_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # METADADOS
    # =============================================================

    def update_metadata(
        self,
        image_id: int,
        image_type: str,
        caption: str | None,
        updated_at: str,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE project_images
                SET
                    image_type = ?,
                    caption = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    image_type,
                    caption,
                    updated_at,
                    image_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # POSIÇÃO
    # =============================================================

    def update_position(
        self,
        image_id: int,
        position: int,
        updated_at: str,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE project_images
                SET
                    position = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    position,
                    updated_at,
                    image_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def update_positions(
        self,
        images: list[ProjectImage],
    ) -> None:
        if not images:
            return

        connection = get_connection()

        try:
            cursor = connection.cursor()

            now = datetime.now().isoformat(
                timespec="seconds"
            )

            for position, image in enumerate(
                images
            ):
                if image.id is None:
                    continue

                cursor.execute(
                    """
                    UPDATE project_images
                    SET
                        position = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        position,
                        now,
                        image.id,
                    ),
                )

                image.position = position
                image.updated_at = now

            connection.commit()

        except Exception:
            connection.rollback()

            raise

        finally:
            connection.close()

    def get_next_position(
        self,
        project_id: int,
    ) -> int:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT MAX(position) AS max_position
                FROM project_images
                WHERE project_id = ?
                """,
                (
                    project_id,
                ),
            )

            row = cursor.fetchone()

            current = (
                row["max_position"]
                if row is not None
                else None
            )

            if current is None:
                return 0

            return int(
                current
            ) + 1

        finally:
            connection.close()

    # =============================================================
    # EXCLUIR
    # =============================================================

    def delete(
        self,
        image_id: int,
    ) -> None:
        connection = get_connection()

        try:
            connection.execute(
                """
                PRAGMA foreign_keys = ON
                """
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM project_images
                WHERE id = ?
                """,
                (
                    image_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # CONVERSÃO
    # =============================================================

    def _row_to_image(
        self,
        row,
    ) -> ProjectImage:
        row_keys = set(
            row.keys()
        )

        return ProjectImage(
            id=row["id"],

            project_id=row[
                "project_id"
            ],

            file_path=row[
                "file_path"
            ],

            file_name=row[
                "file_name"
            ],

            image_type=(
                row["image_type"]
                or "Fotografia"
            ),

            caption=row[
                "caption"
            ],

            position=int(
                row["position"]
                or 0
            ),

            is_primary=bool(
                row["is_primary"]
            )
            if "is_primary" in row_keys
            else False,

            created_at=row[
                "created_at"
            ],

            updated_at=row[
                "updated_at"
            ],
        )