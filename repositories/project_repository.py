from __future__ import annotations

from typing import Optional

from database.connection import get_connection
from models.project import Project


class ProjectRepository:
    """
    Persistência dos processos do METRA.

    Processos excluídos são preservados no banco com status "Excluído"
    para manter rastreabilidade, mas deixam de aparecer nas consultas
    normais da aplicação.
    """

    EXCLUDED_STATUS = "Excluído"

    def create(
        self,
        project: Project,
    ) -> Project:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO projects (
                    report_id,
                    name,
                    template,
                    inspection_type,
                    analysis_mode,
                    quantity,
                    technology,
                    template_version,
                    client,
                    part_name,
                    part_code,
                    equipment,
                    description,
                    status,
                    version,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    project.report_id,
                    project.name,
                    project.template,
                    project.inspection_type,
                    project.analysis_mode,
                    project.quantity,
                    project.technology,
                    project.template_version,
                    project.client,
                    project.part_name,
                    project.part_code,
                    project.equipment,
                    project.description,
                    project.status,
                    project.version,
                    project.created_at,
                    project.updated_at,
                ),
            )

            connection.commit()
            project.id = cursor.lastrowid

            return project

        finally:
            connection.close()

    def find_by_report_id(
        self,
        report_id: str,
        *,
        include_excluded: bool = False,
    ) -> Optional[Project]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            if include_excluded:
                cursor.execute(
                    """
                    SELECT *
                    FROM projects
                    WHERE report_id = ?
                    """,
                    (report_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM projects
                    WHERE
                        report_id = ?
                        AND status <> ?
                    """,
                    (
                        report_id,
                        self.EXCLUDED_STATUS,
                    ),
                )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_project(
                row
            )

        finally:
            connection.close()

    def find_recent(
        self,
        limit: int = 6,
    ) -> list[Project]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM projects
                WHERE status <> ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (
                    self.EXCLUDED_STATUS,
                    limit,
                ),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_project(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    def find_all(
        self,
        *,
        include_excluded: bool = False,
    ) -> list[Project]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            if include_excluded:
                cursor.execute(
                    """
                    SELECT *
                    FROM projects
                    ORDER BY updated_at DESC, id DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM projects
                    WHERE status <> ?
                    ORDER BY updated_at DESC, id DESC
                    """,
                    (
                        self.EXCLUDED_STATUS,
                    ),
                )

            rows = cursor.fetchall()

            return [
                self._row_to_project(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    def update(
        self,
        project: Project,
    ) -> Project:
        if project.id is None:
            raise ValueError(
                "O processo não possui identificador."
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE projects
                SET
                    name = ?,
                    template = ?,
                    inspection_type = ?,
                    analysis_mode = ?,
                    quantity = ?,
                    technology = ?,
                    template_version = ?,
                    client = ?,
                    part_name = ?,
                    part_code = ?,
                    equipment = ?,
                    description = ?,
                    status = ?,
                    version = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    project.name,
                    project.template,
                    project.inspection_type,
                    project.analysis_mode,
                    project.quantity,
                    project.technology,
                    project.template_version,
                    project.client,
                    project.part_name,
                    project.part_code,
                    project.equipment,
                    project.description,
                    project.status,
                    project.version,
                    project.updated_at,
                    project.id,
                ),
            )

            connection.commit()

            if cursor.rowcount == 0:
                raise ValueError(
                    "O processo informado não foi encontrado."
                )

            return project

        finally:
            connection.close()

    def update_status(
        self,
        project_id: int,
        status: str,
        updated_at: str,
    ) -> None:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE projects
                SET
                    status = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    updated_at,
                    project_id,
                ),
            )

            connection.commit()

            if cursor.rowcount == 0:
                raise ValueError(
                    "O processo informado não foi encontrado."
                )

        finally:
            connection.close()

    def soft_delete(
        self,
        project_id: int,
        updated_at: str,
    ) -> None:
        self.update_status(
            project_id=project_id,
            status=self.EXCLUDED_STATUS,
            updated_at=updated_at,
        )

    def _row_to_project(
        self,
        row,
    ) -> Project:
        column_names = set(
            row.keys()
        )

        return Project(
            id=row["id"],
            report_id=row["report_id"],
            name=row["name"],
            template=row["template"],
            inspection_type=(
                row["inspection_type"]
                if "inspection_type" in column_names
                else "Inspeção dimensional"
            ),
            analysis_mode=(
                row["analysis_mode"]
                if "analysis_mode" in column_names
                else "Peça única"
            ),
            quantity=(
                row["quantity"]
                if "quantity" in column_names
                else 1
            ),
            technology=(
                row["technology"]
                if "technology" in column_names
                else None
            ),
            template_version=(
                row["template_version"]
                if "template_version" in column_names
                else "1.0"
            ),
            client=row["client"],
            part_name=row["part_name"],
            part_code=row["part_code"],
            equipment=row["equipment"],
            description=row["description"],
            status=row["status"],
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )