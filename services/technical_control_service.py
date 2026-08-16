from datetime import datetime
from typing import Any, Optional

from models.technical_control import TechnicalControl
from repositories.technical_control_repository import (
    TechnicalControlRepository,
)


class TechnicalControlService:
    VALID_STATUSES = {
        "Em elaboração",
        "Aguardando revisão",
        "Revisado",
        "Aprovado",
    }

    def __init__(self):
        self.repository = (
            TechnicalControlRepository()
        )

    def get_control(
        self,
        project_id: int,
    ) -> Optional[TechnicalControl]:

        return self.repository.find_by_project_id(
            project_id
        )

    def is_approved(
        self,
        project_id: int,
    ) -> bool:
        """
        Retorna True somente quando o Controle Técnico permite
        a emissão oficial do relatório.
        """
        control = self.get_control(
            project_id
        )

        if control is None:
            return False

        return bool(
            control.status == "Aprovado"
            and str(
                control.prepared_by
                or ""
            ).strip()
            and str(
                control.reviewed_by
                or ""
            ).strip()
        )

    def can_issue_report(
        self,
        project_id: int,
    ) -> bool:
        """
        Alias semântico usado pelo fluxo de exportação oficial.
        """
        return self.is_approved(
            project_id
        )

    def save_control(
        self,
        project_id: int,
        data: dict[str, Any],
    ) -> TechnicalControl:

        if project_id is None:
            raise ValueError(
                "Projeto inválido."
            )

        status = data.get(
            "status",
            "Em elaboração",
        )

        if status not in self.VALID_STATUSES:
            raise ValueError(
                "Status técnico inválido."
            )

        prepared_by = (
            data.get(
                "prepared_by",
                "",
            ).strip()
            or None
        )

        reviewed_by = (
            data.get(
                "reviewed_by",
                "",
            ).strip()
            or None
        )

        if status == "Aprovado":
            if not prepared_by:
                raise ValueError(
                    "Informe o responsável pela elaboração antes da aprovação."
                )

            if not reviewed_by:
                raise ValueError(
                    "Informe o responsável pela aprovação."
                )

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        existing = (
            self.repository.find_by_project_id(
                project_id
            )
        )

        control = TechnicalControl(
            project_id=project_id,

            prepared_by=prepared_by,

            prepared_at=data.get(
                "prepared_at"
            ),

            reviewed_by=reviewed_by,

            reviewed_at=data.get(
                "reviewed_at"
            ),

            status=status,

            review_notes=(
                data.get(
                    "review_notes",
                    "",
                ).strip()
                or None
            ),

            created_at=(
                existing.created_at
                if existing
                else now
            ),

            updated_at=now,
        )

        return self.repository.save(
            control
        )