from __future__ import annotations

from datetime import datetime
from typing import Optional

from database.connection import get_connection
from models.technical_control import TechnicalControl


class TechnicalControlRepository:
    def find_by_project_id(
        self,
        project_id: int,
    ) -> Optional[TechnicalControl]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM technical_controls
                WHERE project_id = ?
                """,
                (project_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return TechnicalControl(
                id=row["id"],
                project_id=row["project_id"],

                prepared_by=row["prepared_by"],
                prepared_at=row["prepared_at"],

                reviewed_by=row["reviewed_by"],
                reviewed_at=row["reviewed_at"],

                status=row["status"],

                review_notes=row["review_notes"],

                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        finally:
            connection.close()

    def save(
        self,
        control: TechnicalControl,
    ) -> TechnicalControl:
        existing = self.find_by_project_id(
            control.project_id
        )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            if existing is None:
                cursor.execute(
                    """
                    INSERT INTO technical_controls (
                        project_id,
                        prepared_by,
                        prepared_at,
                        reviewed_by,
                        reviewed_at,
                        status,
                        review_notes,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        control.project_id,
                        control.prepared_by,
                        control.prepared_at,
                        control.reviewed_by,
                        control.reviewed_at,
                        control.status,
                        control.review_notes,
                        control.created_at,
                        control.updated_at,
                    ),
                )

                control.id = cursor.lastrowid

            else:
                cursor.execute(
                    """
                    UPDATE technical_controls
                    SET
                        prepared_by = ?,
                        prepared_at = ?,
                        reviewed_by = ?,
                        reviewed_at = ?,
                        status = ?,
                        review_notes = ?,
                        updated_at = ?
                    WHERE project_id = ?
                    """,
                    (
                        control.prepared_by,
                        control.prepared_at,
                        control.reviewed_by,
                        control.reviewed_at,
                        control.status,
                        control.review_notes,
                        control.updated_at,
                        control.project_id,
                    ),
                )

                control.id = existing.id
                control.created_at = existing.created_at

            connection.commit()

            return control

        finally:
            connection.close()

    # =============================================================
    # INVALIDAR APROVAÇÃO
    # =============================================================

    def invalidate_approval(
        self,
        project_id: int,
        *,
        reason: str | None = None,
    ) -> bool:
        """
        Invalida uma aprovação/revisão anterior após alteração técnica.

        Retorna True quando havia controle técnico aprovado/revisado
        e o status precisou voltar para "Em elaboração".

        Os nomes dos responsáveis são preservados para rastreabilidade,
        mas as datas de revisão e aprovação deixam de representar o
        estado atual e por isso são limpas.
        """

        existing = self.find_by_project_id(
            project_id
        )

        if existing is None:
            return False

        status = str(
            existing.status
            or ""
        ).strip()

        if status not in {
            "Aguardando revisão",
            "Revisado",
            "Aprovado",
        }:
            return False

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        previous_notes = str(
            existing.review_notes
            or ""
        ).strip()

        reason_text = str(
            reason
            or "Conteúdo técnico alterado após revisão."
        ).strip()

        audit_note = (
            f"[{now}] Aprovação anterior invalidada: "
            f"{reason_text}"
        )

        if previous_notes:
            review_notes = (
                f"{previous_notes}\n{audit_note}"
            )
        else:
            review_notes = audit_note

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE technical_controls
                SET
                    status = 'Em elaboração',
                    reviewed_at = NULL,
                    review_notes = ?,
                    updated_at = ?
                WHERE project_id = ?
                """,
                (
                    review_notes,
                    now,
                    project_id,
                ),
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()