from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)


SectionRenderer = Callable[
    [
        fitz.Page,
        float,
        float,
    ],
    float,
]


@dataclass(slots=True)
class ReportSection:
    """
    Componente reutilizável para uma seção técnica do relatório.

    Cada seção possui:

    - título;
    - altura estimada;
    - função responsável por desenhar o conteúdo;
    - título que pode ser repetido em uma nova página.

    O componente verifica automaticamente se o bloco cabe na
    página antes de iniciar o desenho.
    """

    title: str

    estimated_height: float

    renderer: SectionRenderer

    repeated_title: str | None = None

    # =============================================================
    # CORES
    # =============================================================

    COLOR_NAVY = (
        0.03,
        0.11,
        0.22,
    )

    COLOR_LIGHT_BLUE = (
        0.93,
        0.96,
        0.985,
    )

    COLOR_BORDER = (
        0.76,
        0.80,
        0.85,
    )

    COLOR_TEXT = (
        0.07,
        0.10,
        0.13,
    )

    TITLE_HEIGHT = 28.0

    GAP_AFTER_TITLE = 7.0

    GAP_AFTER_SECTION = 10.0

    # =============================================================
    # DESENHO
    # =============================================================

    def draw(
        self,
        layout: ReportLayoutEngine,
    ) -> float:
        """
        Desenha a seção completa e retorna a altura utilizada.

        A função de conteúdo precisa retornar a altura real
        consumida após o título da seção.
        """

        if self.estimated_height < 0:
            raise ValueError(
                "A altura estimada da seção não pode ser negativa."
            )

        required_height = (
            self.TITLE_HEIGHT
            + self.GAP_AFTER_TITLE
            + self.estimated_height
            + self.GAP_AFTER_SECTION
        )

        repeated_title = (
            self.repeated_title
            or self.title
        )

        page = layout.ensure_space(
            required_height,
            repeated_title=repeated_title,
        )

        start_y = layout.cursor_y

        self._draw_title(
            page=page,
            layout=layout,
        )

        layout.advance(
            self.TITLE_HEIGHT
            + self.GAP_AFTER_TITLE
        )

        content_height = self._draw_content(
            page=page,
            layout=layout,
        )

        layout.advance(
            content_height
            + self.GAP_AFTER_SECTION
        )

        return (
            layout.cursor_y
            - start_y
        )

    # =============================================================
    # TÍTULO
    # =============================================================

    def _draw_title(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
    ) -> None:
        geometry = layout.geometry

        title_rect = fitz.Rect(
            geometry.margin_left,
            layout.cursor_y,
            geometry.width
            - geometry.margin_right,
            layout.cursor_y
            + self.TITLE_HEIGHT,
        )

        page.draw_rect(
            title_rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                title_rect.x0 + 9,
                title_rect.y0 + 6,
                title_rect.x1 - 9,
                title_rect.y1 - 4,
            ),
            self.title,
            fontsize=8.4,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

    # =============================================================
    # CONTEÚDO
    # =============================================================

    def _draw_content(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
    ) -> float:
        content_height = self.renderer(
            page,
            layout.cursor_y,
            layout.geometry.content_width,
        )

        try:
            resolved_height = float(
                content_height
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise TypeError(
                (
                    "O renderizador da seção precisa "
                    "retornar a altura utilizada."
                )
            ) from error

        if resolved_height < 0:
            raise ValueError(
                (
                    "O renderizador da seção retornou "
                    "uma altura negativa."
                )
            )

        return resolved_height