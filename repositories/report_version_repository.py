from __future__ import annotations

from typing import Optional

from database.connection import get_connection
from models.report_version import ReportVersion


class ReportVersionRepository:
    """Persistência do histórico de emissões dos relatórios."""

    def create(
        self,
        report_version: ReportVersion,
    ) -> ReportVersion:
        connection = get_connection()

        try:
            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO report_versions (
                    project_id,
                    version,
                    file_path,
                    file_name,
                    status,
                    created_by,
                    reviewed_by,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_version.project_id,
                    report_version.version,
                    report_version.file_path,
                    report_version.file_name,
                    report_version.status,
                    report_version.created_by,
                    report_version.reviewed_by,
                    report_version.created_at,
                ),
            )

            connection.commit()
            report_version.id = cursor.lastrowid

            return report_version

        finally:
            connection.close()

    def find_by_id(
        self,
        version_id: int,
    ) -> Optional[ReportVersion]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_versions
                WHERE id = ?
                """,
                (version_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_report_version(
                row
            )

        finally:
            connection.close()

    def find_by_project_id(
        self,
        project_id: int,
    ) -> list[ReportVersion]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_versions
                WHERE project_id = ?
                ORDER BY id ASC
                """,
                (project_id,),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_report_version(
                    row
                )
                for row in rows
            ]

        finally:
            connection.close()

    def find_by_project_and_version(
        self,
        project_id: int,
        version: str,
    ) -> Optional[ReportVersion]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_versions
                WHERE project_id = ?
                  AND version = ?
                LIMIT 1
                """,
                (
                    project_id,
                    version,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_report_version(
                row
            )

        finally:
            connection.close()

    def find_latest_by_project_id(
        self,
        project_id: int,
    ) -> Optional[ReportVersion]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM report_versions
                WHERE project_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_report_version(
                row
            )

        finally:
            connection.close()

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
                FROM report_versions
                WHERE project_id = ?
                """,
                (project_id,),
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

    def delete(
        self,
        version_id: int | None,
    ) -> None:
        if version_id is None:
            return

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM report_versions
                WHERE id = ?
                """,
                (version_id,),
            )

            connection.commit()

        finally:
            connection.close()

    def _row_to_report_version(
        self,
        row,
    ) -> ReportVersion:
        return ReportVersion(
            id=row["id"],
            project_id=row["project_id"],
            version=row["version"],
            file_path=row["file_path"],
            file_name=row["file_name"],
            status=row["status"],
            created_by=row["created_by"],
            reviewed_by=row["reviewed_by"],
            created_at=row["created_at"],
        )