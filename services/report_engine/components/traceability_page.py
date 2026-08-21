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


class TraceabilityReportPage:
    """
    Seção compartilhada de rastreabilidade.

    É usada por todos os templates e só aparece quando o usuário
    escolhe explicitamente incluir o histórico no PDF.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    SECTION_TITLE_HEIGHT = 28.0
    HEADER_HEIGHT = 24.0
    ROW_HEIGHT = 30.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        if render_context.section_enabled(
            "version_history"
        ):
            self._render_version_history(
                layout=layout,
                render_context=render_context,
            )

        if render_context.section_enabled(
            "validation_history"
        ):
            self._render_validation_history(
                layout=layout,
                render_context=render_context,
            )

    # =============================================================
    # VERSÕES
    # =============================================================

    def _render_version_history(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        rows = (
            render_context.get_context_value(
                "version_history",
                [],
            )
            or []
        )

        if not rows:
            return

        self._draw_table(
            layout=layout,
            section_title="HISTÓRICO DE VERSÕES",
            columns=[
                ("Versão", 0.13),
                ("Data / hora", 0.20),
                ("Responsável", 0.22),
                ("Situação", 0.16),
                ("Descrição", 0.29),
            ],
            rows=[
                [
                    self._clean(
                        row.get(
                            "version"
                        )
                    ),
                    self._format_datetime(
                        row.get(
                            "datetime"
                        )
                    ),
                    self._clean(
                        row.get(
                            "responsible"
                        )
                    ),
                    self._clean(
                        row.get(
                            "status"
                        )
                    ),
                    self._clean(
                        row.get(
                            "description"
                        )
                    ),
                ]
                for row in rows
                if isinstance(
                    row,
                    dict,
                )
            ],
        )

    # =============================================================
    # VALIDAÇÃO
    # =============================================================

    def _render_validation_history(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        rows = (
            render_context.get_context_value(
                "validation_history",
                [],
            )
            or []
        )

        if not rows:
            return

        self._draw_table(
            layout=layout,
            section_title="HISTÓRICO DE VALIDAÇÃO",
            columns=[
                ("Data / hora", 0.22),
                ("Evento", 0.22),
                ("Responsável", 0.20),
                ("Observação", 0.36),
            ],
            rows=[
                [
                    self._format_datetime(
                        row.get(
                            "datetime"
                        )
                    ),
                    self._clean(
                        row.get(
                            "event"
                        )
                    ),
                    self._clean(
                        row.get(
                            "responsible"
                        )
                    ),
                    self._clean(
                        row.get(
                            "observation"
                        )
                    ),
                ]
                for row in rows
                if isinstance(
                    row,
                    dict,
                )
            ],
        )

    # =============================================================
    # TABELA
    # =============================================================

    def _draw_table(
        self,
        *,
        layout: ReportLayoutEngine,
        section_title: str,
        columns: list[tuple[str, float]],
        rows: list[list[str]],
    ) -> None:
        if not rows:
            return

        first_required = (
            self.SECTION_TITLE_HEIGHT
            + self.HEADER_HEIGHT
            + self.ROW_HEIGHT
            + self.GAP
        )

        page = layout.ensure_space(
            first_required,
            repeated_title=section_title,
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title=section_title,
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        self._draw_header_row(
            page=layout.current_page,
            layout=layout,
            columns=columns,
        )

        layout.advance(
            self.HEADER_HEIGHT
        )

        for row in rows:
            page = layout.ensure_space(
                self.ROW_HEIGHT,
                repeated_title=section_title,
            )

            # A paginação é controlada pelo próprio ensure_space().
            # O ReportLayoutEngine atual não expõe um atributo content_top.
            self._draw_data_row(
                page=layout.current_page,
                layout=layout,
                columns=columns,
                values=row,
            )

            layout.advance(
                self.ROW_HEIGHT
            )

        layout.advance(
            self.GAP
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
                rect.x0 + 10,
                rect.y0 + 7,
                rect.x1 - 10,
                rect.y1 - 5,
            ),
            title,
            fontsize=7.0,
            fontname="hebo",
            color=(1, 1, 1),
        )

    def _draw_header_row(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        columns: list[tuple[str, float]],
    ) -> None:
        rect = layout.full_width_rect(
            self.HEADER_HEIGHT
        )

        x = rect.x0

        for title, ratio in columns:
            width = (
                rect.width
                * ratio
            )

            cell = fitz.Rect(
                x,
                rect.y0,
                x + width,
                rect.y1,
            )

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=self.COLOR_LIGHT_BLUE,
                width=0.45,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 5,
                    cell.y0 + 6,
                    cell.x1 - 5,
                    cell.y1 - 4,
                ),
                title,
                fontsize=5.8,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            x += width

    def _draw_data_row(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        columns: list[tuple[str, float]],
        values: list[str],
    ) -> None:
        rect = layout.full_width_rect(
            self.ROW_HEIGHT
        )

        x = rect.x0

        for index, (_, ratio) in enumerate(
            columns
        ):
            width = (
                rect.width
                * ratio
            )

            cell = fitz.Rect(
                x,
                rect.y0,
                x + width,
                rect.y1,
            )

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=self.COLOR_SURFACE,
                width=0.4,
            )

            value = (
                values[index]
                if index < len(values)
                else "-"
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 5,
                    cell.y0 + 5,
                    cell.x1 - 5,
                    cell.y1 - 4,
                ),
                value,
                fontsize=5.3,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.05,
            )

            x += width

    # =============================================================
    # HELPERS
    # =============================================================

    def _clean(
        self,
        value: Any,
    ) -> str:
        cleaned = " ".join(
            str(
                value
                or ""
            ).split()
        )

        return (
            cleaned
            or "-"
        )

    def _format_datetime(
        self,
        value: Any,
    ) -> str:
        text = self._clean(
            value
        )

        if text == "-":
            return text

        try:
            parsed = datetime.fromisoformat(
                text
            )
            return parsed.strftime(
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            return text