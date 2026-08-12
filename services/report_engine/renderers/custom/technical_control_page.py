from __future__ import annotations

from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class CustomTechnicalControlPage:
    """
    Página final do relatório personalizado.

    Exibe:
    - conclusão;
    - controle técnico;
    - elaboração e revisão;
    - assinaturas.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    SECTION_TITLE_HEIGHT = 28.0
    ROW_HEIGHT = 27.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        self._render_conclusion(
            layout=layout,
            render_context=render_context,
        )

        self._render_control(
            layout=layout,
            render_context=render_context,
        )

        self._render_signatures(
            layout=layout,
            render_context=render_context,
        )

    def _render_conclusion(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        value = (
            render_context.get_context_value(
                "custom_conclusion"
            )
            or render_context.get_context_value(
                "conclusion"
            )
        )

        conclusion = self._clean_text(
            value,
            fallback=(
                "O presente relatório consolida as informações "
                "e evidências disponíveis para o processo analisado."
            ),
        )

        height = max(
            82.0,
            min(
                150.0,
                52.0
                + len(
                    conclusion
                ) * 0.12,
            ),
        )

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT + height,
            repeated_title="CONCLUSÃO",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="8. CONCLUSÃO",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        rect = layout.full_width_rect(
            height
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 10,
                rect.y0 + 10,
                rect.x1 - 10,
                rect.y1 - 10,
            ),
            conclusion,
            fontsize=6.8,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )

        layout.advance(
            height + self.GAP
        )

    def _render_control(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        control = render_context.technical_control

        if control is None:
            return

        values = [
            (
                "Situação",
                getattr(
                    control,
                    "status",
                    None,
                ),
            ),
            (
                "Elaborado por",
                getattr(
                    control,
                    "prepared_by",
                    None,
                ),
            ),
            (
                "Data da elaboração",
                getattr(
                    control,
                    "prepared_at",
                    None,
                ),
            ),
            (
                "Revisado por",
                getattr(
                    control,
                    "reviewed_by",
                    None,
                ),
            ),
            (
                "Data da revisão",
                getattr(
                    control,
                    "reviewed_at",
                    None,
                ),
            ),
        ]

        values = [
            (
                label,
                value,
            )
            for label, value in values
            if self._has_text(
                value
            )
        ]

        if not values:
            return

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + len(values)
            * self.ROW_HEIGHT,
            repeated_title="CONTROLE TÉCNICO",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="9. CONTROLE TÉCNICO",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        label_width = (
            layout.geometry.content_width
            * 0.36
        )

        for index, (
            label,
            value,
        ) in enumerate(values):
            rect = layout.full_width_rect(
                self.ROW_HEIGHT
            )

            fill = (
                self.COLOR_SURFACE
                if index % 2 == 0
                else (1, 1, 1)
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.35,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x0 + label_width,
                    rect.y1 - 4,
                ),
                label,
                fontsize=6.1,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + label_width,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                self._clean_text(
                    value
                ),
                fontsize=6.4,
                fontname="helv",
                color=self.COLOR_TEXT,
            )

            layout.advance(
                self.ROW_HEIGHT
            )

        layout.advance(
            self.GAP
        )

    def _render_signatures(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        control = render_context.technical_control

        prepared_by = (
            getattr(
                control,
                "prepared_by",
                None,
            )
            if control is not None
            else None
        )

        reviewed_by = (
            getattr(
                control,
                "reviewed_by",
                None,
            )
            if control is not None
            else None
        )

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT + 70.0,
            repeated_title="RESPONSABILIDADES",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="10. RESPONSABILIDADES",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        gap = 12.0

        box_width = (
            layout.geometry.content_width
            - gap
        ) / 2

        box_height = 62.0

        entries = [
            (
                "Responsável técnico",
                prepared_by,
            ),
            (
                "Revisão / aprovação",
                reviewed_by,
            ),
        ]

        for index, (
            label,
            person,
        ) in enumerate(entries):
            x = (
                layout.geometry.margin_left
                + index
                * (
                    box_width
                    + gap
                )
            )

            rect = fitz.Rect(
                x,
                layout.cursor_y,
                x + box_width,
                layout.cursor_y + box_height,
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=(1, 1, 1),
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y0 + 20,
                ),
                self._clean_text(
                    person,
                    fallback=label,
                ),
                fontsize=6.2,
                fontname="hebo",
                color=self.COLOR_NAVY,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            line_y = rect.y1 - 20

            page.draw_line(
                fitz.Point(
                    rect.x0 + 18,
                    line_y,
                ),
                fitz.Point(
                    rect.x1 - 18,
                    line_y,
                ),
                color=self.COLOR_BORDER,
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 5,
                    line_y + 4,
                    rect.x1 - 5,
                    rect.y1 - 3,
                ),
                label,
                fontsize=5.5,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            box_height
        )

    def _draw_section_title(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        title: str,
    ) -> None:
        rect = layout.full_width_rect(
            self.SECTION_TITLE_HEIGHT
        )

        page.draw_rect(
            rect,
            color=self.COLOR_NAVY,
            fill=self.COLOR_NAVY,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 9,
                rect.y0 + 7,
                rect.x1 - 9,
                rect.y1 - 4,
            ),
            title,
            fontsize=7.3,
            fontname="hebo",
            color=(1, 1, 1),
        )

    def _has_text(
        self,
        value: Any,
    ) -> bool:
        return bool(
            str(
                value
                or ""
            ).strip()
        )

    def _clean_text(
        self,
        value: Any,
        *,
        fallback: str = "Não informado",
    ) -> str:
        cleaned = " ".join(
            str(
                value
                or ""
            ).split()
        )

        return (
            cleaned
            or fallback
        )