from __future__ import annotations

from typing import Any

from repositories.custom_report_section_repository import (
    CustomReportSectionRepository,
)
from repositories.technical_control_repository import (
    TechnicalControlRepository,
)


class CustomReportContentService:
    """
    Regras do conteúdo narrativo do template Personalizado.

    O conteúdo é persistido imediatamente e qualquer alteração
    invalida uma aprovação técnica anterior, pois modifica o
    documento que será oficialmente emitido.
    """

    def __init__(self) -> None:
        self.repository = (
            CustomReportSectionRepository()
        )

        self.technical_control_repository = (
            TechnicalControlRepository()
        )

    def get_sections(
        self,
        project_id: int,
    ) -> list[dict[str, Any]]:
        return self.repository.find_by_project_id(
            project_id
        )

    def save_sections(
        self,
        *,
        project_id: int,
        sections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized = self._normalize_sections(
            sections
        )

        previous = self.repository.find_by_project_id(
            project_id
        )

        if self._comparable(previous) == self._comparable(normalized):
            return previous

        saved = self.repository.replace_for_project(
            project_id,
            normalized,
        )

        self.technical_control_repository.invalidate_approval(
            project_id,
            reason=(
                "O conteúdo técnico do relatório personalizado "
                "foi alterado."
            ),
        )

        return saved

    def _normalize_sections(
        self,
        sections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for item in sections:
            if not isinstance(
                item,
                dict,
            ):
                continue

            title = str(
                item.get(
                    "title",
                    "",
                )
                or ""
            ).strip()

            content = str(
                item.get(
                    "content",
                    "",
                )
                or ""
            ).strip()

            image_ids: list[int] = []

            for value in item.get(
                "image_ids",
                [],
            ):
                try:
                    image_id = int(value)
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if (
                    image_id > 0
                    and image_id not in image_ids
                ):
                    image_ids.append(
                        image_id
                    )

            if (
                not title
                and not content
                and not image_ids
            ):
                continue

            normalized.append(
                {
                    "title": title,
                    "content": content,
                    "image_ids": image_ids,
                }
            )

        return normalized

    def _comparable(
        self,
        sections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "title": str(
                    item.get(
                        "title",
                        "",
                    )
                    or ""
                ).strip(),
                "content": str(
                    item.get(
                        "content",
                        "",
                    )
                    or ""
                ).strip(),
                "image_ids": [
                    int(value)
                    for value in item.get(
                        "image_ids",
                        [],
                    )
                    if str(value).isdigit()
                ],
            }
            for item in sections
        ]