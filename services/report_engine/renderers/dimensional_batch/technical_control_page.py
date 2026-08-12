from __future__ import annotations

from datetime import datetime
from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class DimensionalBatchTechnicalControlPage:
    """
    Encerramento do relatório dimensional em lote.

    A conclusão não declara "estabilidade do processo" apenas com base
    na conformidade, pois estabilidade estatística exige análise própria.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)

    COLOR_OK = (0.080, 0.500, 0.275)
    COLOR_OK_BG = (0.910, 0.975, 0.935)
    COLOR_NOK = (0.760, 0.160, 0.120)
    COLOR_NOK_BG = (0.995, 0.920, 0.905)

    SECTION_TITLE_HEIGHT = 28.0
    ROW_HEIGHT = 27.0
    GAP = 12.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        self._draw_conclusion(
            layout=layout,
            render_context=render_context,
        )

        self._draw_control(
            layout=layout,
            render_context=render_context,
        )

        self._draw_signature(
            layout=layout,
            render_context=render_context,
        )

    # =============================================================
    # CONCLUSÃO
    # =============================================================

    def _draw_conclusion(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        summary = (
            render_context.overall_statistics
        )

        nok_count = int(
            summary.get(
                "nok_count",
                0,
            )
            or 0
        )

        unknown_count = int(
            summary.get(
                "unknown_count",
                0,
            )
            or 0
        )

        evaluated_count = int(
            summary.get(
                "evaluated_count",
                0,
            )
            or 0
        )

        if nok_count > 0:
            title = (
                "CONCLUSÃO TÉCNICA: "
                "NÃO CONFORMIDADES NO LOTE"
            )

            color = self.COLOR_NOK
            background = self.COLOR_NOK_BG

            message = (
                f"Foram identificados {nok_count} resultado(s) fora "
                "dos limites especificados no conjunto analisado. "
                "As características correspondentes estão apresentadas "
                "nas seções estatística e gráfica deste relatório."
            )

        elif (
            evaluated_count > 0
            and unknown_count == 0
        ):
            title = (
                "CONCLUSÃO TÉCNICA: "
                "LOTE CONFORME"
            )

            color = self.COLOR_OK
            background = self.COLOR_OK_BG

            message = (
                "Todos os resultados avaliados encontram-se dentro "
                "dos limites especificados para o lote analisado."
            )

        else:
            title = "CONCLUSÃO TÉCNICA"

            color = self.COLOR_NAVY
            background = self.COLOR_SURFACE

            message = (
                "Os resultados dimensionais e estatísticos obtidos "
                "estão consolidados neste relatório e devem ser "
                "considerados em conjunto com as condições de medição "
                "e os dados de origem do processo."
            )

        height = self._estimate_text_height(
            message
        )

        page = layout.ensure_space(
            height,
            repeated_title="CONCLUSÃO TÉCNICA",
        )

        rect = layout.full_width_rect(
            height
        )

        page.draw_rect(
            rect,
            color=color,
            fill=background,
            width=0.9,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 10,
                rect.x1 - 12,
                rect.y0 + 27,
            ),
            title,
            fontsize=8.5,
            fontname="hebo",
            color=color,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 33,
                rect.x1 - 12,
                rect.y1 - 10,
            ),
            message,
            fontsize=6.7,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.16,
        )

        layout.advance(
            height + self.GAP
        )

    # =============================================================
    # CONTROLE TÉCNICO
    # =============================================================

    def _draw_control(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        control = (
            render_context.technical_control
        )

        if control is None:
            return

        values = [
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
            (
                "Status",
                getattr(
                    control,
                    "status",
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

        row_heights = [
            self._estimate_row_height(
                value
            )
            for _, value in values
        ]

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + sum(row_heights),
            repeated_title="CONTROLE TÉCNICO",
        )

        self._draw_title(
            page=page,
            layout=layout,
            text="CONTROLE TÉCNICO",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        label_width = (
            layout.geometry.content_width
            * 0.35
        )

        for index, (
            (
                label,
                value,
            ),
            row_height,
        ) in enumerate(
            zip(
                values,
                row_heights,
            )
        ):
            page = layout.ensure_space(
                row_height,
                repeated_title="CONTROLE TÉCNICO",
            )

            rect = layout.full_width_rect(
                row_height
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
                    rect.y1 - 5,
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
                    rect.y1 - 5,
                ),
                self._format_value(
                    value
                ),
                fontsize=6.4,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.12,
            )

            layout.advance(
                row_height
            )

        layout.advance(
            self.GAP
        )

    # =============================================================
    # ASSINATURAS
    # =============================================================

    def _draw_signature(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        control = (
            render_context.technical_control
        )

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

        height = 78.0

        page = layout.ensure_space(
            height,
            repeated_title="RESPONSABILIDADES",
        )

        gap = 16.0

        card_width = (
            layout.geometry.content_width
            - gap
        ) / 2.0

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
                + index * (
                    card_width + gap
                )
            )

            rect = fitz.Rect(
                x,
                layout.cursor_y,
                x + card_width,
                layout.cursor_y + height,
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=(1, 1, 1),
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 10,
                    rect.y0 + 10,
                    rect.x1 - 10,
                    rect.y0 + 30,
                ),
                self._clean(
                    person,
                    fallback=label,
                ),
                fontsize=6.4,
                fontname="hebo",
                color=self.COLOR_NAVY,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            line_y = rect.y1 - 22

            page.draw_line(
                fitz.Point(
                    rect.x0 + 20,
                    line_y,
                ),
                fitz.Point(
                    rect.x1 - 20,
                    line_y,
                ),
                color=self.COLOR_BORDER,
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    line_y + 4,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                label,
                fontsize=5.6,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            height
        )

    # =============================================================
    # HELPERS
    # =============================================================

    def _draw_title(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        text: str,
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
                rect.x0 + 10,
                rect.y0 + 7,
                rect.x1 - 10,
                rect.y1 - 4,
            ),
            text,
            fontsize=7.4,
            fontname="hebo",
            color=(1, 1, 1),
        )

    def _estimate_text_height(
        self,
        value: Any,
    ) -> float:
        text = self._clean(
            value,
            fallback="",
        )

        lines = max(
            1,
            (
                len(text) + 98
            )
            // 99,
        )

        return max(
            82.0,
            min(
                132.0,
                44.0 + lines * 10.0,
            ),
        )

    def _estimate_row_height(
        self,
        value: Any,
    ) -> float:
        text = self._format_value(
            value
        )

        lines = max(
            1,
            (
                len(text) + 75
            )
            // 76,
        )

        return max(
            self.ROW_HEIGHT,
            17.0 + lines * 9.0,
        )

    def _format_value(
        self,
        value: Any,
    ) -> str:
        if isinstance(
            value,
            datetime,
        ):
            return value.strftime(
                "%d/%m/%Y %H:%M"
            )

        text = self._clean(
            value
        )

        try:
            if (
                "T" in text
                and len(text) >= 16
            ):
                parsed = datetime.fromisoformat(
                    text.replace(
                        "Z",
                        "+00:00",
                    )
                )

                return parsed.strftime(
                    "%d/%m/%Y %H:%M"
                )
        except ValueError:
            pass

        return text

    def _has_text(
        self,
        value: Any,
    ) -> bool:
        return bool(
            str(
                value or ""
            ).strip()
        )

    def _clean(
        self,
        value: Any,
        *,
        fallback: str = "Não informado",
    ) -> str:
        cleaned = " ".join(
            str(
                value or ""
            ).split()
        )

        return cleaned or fallback