from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from database.connection import get_connection


class CustomReportSectionRepository:
    """
    Persistência das seções livres do relatório Personalizado.

    A tabela é criada de forma idempotente pelo próprio repositório.
    Isso mantém compatibilidade com bancos METRA já existentes sem
    exigir apagar ou recriar o arquivo SQLite.
    """

    def __init__(self) -> None:
        self._ensure_table()

    # =============================================================
    # ESTRUTURA
    # =============================================================

    def _ensure_table(self) -> None:
        connection = get_connection()

        try:
            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_report_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    project_id INTEGER NOT NULL,

                    title TEXT,
                    content TEXT,

                    image_ids_json TEXT NOT NULL DEFAULT '[]',

                    position INTEGER NOT NULL DEFAULT 0,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    FOREIGN KEY (project_id)
                        REFERENCES projects(id)
                        ON DELETE CASCADE
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_custom_report_sections_project_position
                ON custom_report_sections (
                    project_id,
                    position,
                    id
                )
                """
            )

            connection.commit()

        finally:
            connection.close()

    # =============================================================
    # LEITURA
    # =============================================================

    def find_by_project_id(
        self,
        project_id: int,
    ) -> list[dict[str, Any]]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM custom_report_sections
                WHERE project_id = ?
                ORDER BY position ASC, id ASC
                """,
                (project_id,),
            )

            rows = cursor.fetchall()

            result: list[dict[str, Any]] = []

            for row in rows:
                try:
                    image_ids = json.loads(
                        row["image_ids_json"]
                        or "[]"
                    )
                except (
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                ):
                    image_ids = []

                image_ids = [
                    int(value)
                    for value in image_ids
                    if str(value).isdigit()
                ]

                result.append(
                    {
                        "id": row["id"],
                        "title": str(
                            row["title"]
                            or ""
                        ).strip(),
                        "content": str(
                            row["content"]
                            or ""
                        ).strip(),
                        "image_ids": image_ids,
                        "position": int(
                            row["position"]
                            or 0
                        ),
                    }
                )

            return result

        finally:
            connection.close()

    # =============================================================
    # SUBSTITUIÇÃO ATÔMICA
    # =============================================================

    def replace_for_project(
        self,
        project_id: int,
        sections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        connection = get_connection()

        try:
            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM custom_report_sections
                WHERE project_id = ?
                """,
                (project_id,),
            )

            now = datetime.now().isoformat(
                timespec="seconds"
            )

            for position, section in enumerate(
                sections
            ):
                title = str(
                    section.get(
                        "title",
                        "",
                    )
                    or ""
                ).strip()

                content = str(
                    section.get(
                        "content",
                        "",
                    )
                    or ""
                ).strip()

                image_ids = [
                    int(value)
                    for value in section.get(
                        "image_ids",
                        [],
                    )
                    if str(value).isdigit()
                ]

                if (
                    not title
                    and not content
                    and not image_ids
                ):
                    continue

                cursor.execute(
                    """
                    INSERT INTO custom_report_sections (
                        project_id,
                        title,
                        content,
                        image_ids_json,
                        position,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        title or None,
                        content or None,
                        json.dumps(
                            image_ids,
                            ensure_ascii=False,
                        ),
                        position,
                        now,
                        now,
                    ),
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        return self.find_by_project_id(
            project_id
        )