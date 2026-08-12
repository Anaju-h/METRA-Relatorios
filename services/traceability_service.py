from __future__ import annotations

from repositories.technical_control_repository import (
    TechnicalControlRepository,
)


class TraceabilityService:
    """
    Serviço central de rastreabilidade de alterações técnicas.

    Qualquer módulo que altere conteúdo relevante do relatório pode
    chamar invalidate_technical_approval(). A regra de invalidação
    permanece concentrada em um único ponto.
    """

    def __init__(self) -> None:
        self.technical_control_repository = (
            TechnicalControlRepository()
        )

    def invalidate_technical_approval(
        self,
        *,
        project_id: int,
        reason: str,
    ) -> bool:
        if project_id is None:
            return False

        return (
            self.technical_control_repository
            .invalidate_approval(
                project_id,
                reason=reason,
            )
        )