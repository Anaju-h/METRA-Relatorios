from __future__ import annotations

from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class DimensionalBatchStatisticsPage:
    """
    Resumo estatístico consolidado do relatório dimensional em lote.

    O conteúdo é voltado ao cliente:
    - indicadores internos de ausência de avaliação não são exibidos;
    - Cp/Cpk aparecem somente quando disponíveis;
    - status indeterminado é apresentado de forma neutra;
    - tabelas quebram automaticamente entre páginas.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    COLOR_OK = (0.080, 0.500, 0.275)
    COLOR_OK_BG = (0.910, 0.975, 0.935)
    COLOR_NOK = (0.760, 0.160, 0.120)
    COLOR_NOK_BG = (0.995, 0.920, 0.905)

    SECTION_TITLE_HEIGHT = 28.0
    TABLE_HEADER_HEIGHT = 28.0
    TABLE_ROW_HEIGHT = 31.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        groups = (
            render_context.statistical_groups
        )

        if not groups:
            return

        self._draw_overview(
            layout=layout,
            render_context=render_context,
        )

        self._draw_statistics_table(
            layout=layout,
            groups=groups,
        )

    # =============================================================
    # VISÃO GERAL
    # =============================================================

    def _draw_overview(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        summary = (
            render_context.overall_statistics
        )

        evaluated_count = int(
            summary.get(
                "evaluated_count",
                0,
            )
            or 0
        )

        page = layout.ensure_space(
            106.0,
            repeated_title="RESUMO ESTATÍSTICO",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="3. RESUMO ESTATÍSTICO CONSOLIDADO",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        base_values = [
            (
                "Características",
                summary.get(
                    "group_count",
                    0,
                ),
                "grupos analisados",
                self.COLOR_LIGHT_BLUE,
                self.COLOR_NAVY,
            ),
            (
                "Resultados",
                summary.get(
                    "measurement_count",
                    0,
                ),
                "medições",
                self.COLOR_LIGHT_BLUE,
                self.COLOR_NAVY,
            ),
        ]

        if evaluated_count > 0:
            values = base_values + [
                (
                    "Conformes",
                    summary.get(
                        "ok_count",
                        0,
                    ),
                    "resultados",
                    self.COLOR_OK_BG,
                    self.COLOR_OK,
                ),
                (
                    "Não conformes",
                    summary.get(
                        "nok_count",
                        0,
                    ),
                    "resultados",
                    self.COLOR_NOK_BG,
                    self.COLOR_NOK,
                ),
            ]
        else:
            values = base_values

        gap = 7.0

        card_width = (
            layout.geometry.content_width
            - gap * (
                len(values) - 1
            )
        ) / len(values)

        card_height = 68.0

        for index, (
            label,
            value,
            helper,
            background,
            accent,
        ) in enumerate(values):
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
                layout.cursor_y + card_height,
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=background,
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 6,
                    rect.x1 - 4,
                    rect.y0 + 19,
                ),
                label,
                fontsize=5.5,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 24,
                    rect.x1 - 4,
                    rect.y0 + 44,
                ),
                str(
                    value
                ),
                fontsize=11.0,
                fontname="hebo",
                color=accent,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 47,
                    rect.x1 - 4,
                    rect.y1 - 5,
                ),
                helper,
                fontsize=5.1,
                fontname="helv",
                color=accent,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            card_height + self.GAP
        )

    # =============================================================
    # TABELA
    # =============================================================

    def _draw_statistics_table(
        self,
        *,
        layout: ReportLayoutEngine,
        groups: list[Any],
    ) -> None:
        self._draw_table_header(
            layout=layout,
        )

        for index, group in enumerate(
            groups
        ):
            page = layout.ensure_space(
                self.TABLE_ROW_HEIGHT,
                repeated_title="RESUMO ESTATÍSTICO",
            )

            if (
                layout.cursor_y
                <= layout.geometry.margin_top + 92
            ):
                self._draw_table_header(
                    layout=layout,
                )
                page = layout.current_page

            self._draw_table_row(
                page=page,
                layout=layout,
                group=group,
                alternate=(
                    index % 2 == 0
                ),
            )

            layout.advance(
                self.TABLE_ROW_HEIGHT
            )

        layout.advance(
            self.GAP
        )

    def _draw_table_header(
        self,
        *,
        layout: ReportLayoutEngine,
    ) -> None:
        required = (
            self.SECTION_TITLE_HEIGHT
            + self.TABLE_HEADER_HEIGHT
        )

        page = layout.ensure_space(
            required,
            repeated_title="RESUMO ESTATÍSTICO",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="4. ESTATÍSTICA POR CARACTERÍSTICA",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        headers = [
            "Característica",
            "n",
            "Nominal",
            "Mín.",
            "Máx.",
            "Média",
            "Amplitude",
            "Desv. padrão",
            "Cp",
            "Cpk",
            "Status",
        ]

        columns = self._columns(
            layout.geometry.content_width
        )

        for header, rect in zip(
            headers,
            columns,
        ):
            cell = fitz.Rect(
                layout.geometry.margin_left + rect.x0,
                layout.cursor_y,
                layout.geometry.margin_left + rect.x1,
                layout.cursor_y + self.TABLE_HEADER_HEIGHT,
            )

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=self.COLOR_NAVY,
                width=0.35,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 3,
                    cell.y0 + 7,
                    cell.x1 - 3,
                    cell.y1 - 4,
                ),
                header,
                fontsize=4.8,
                fontname="hebo",
                color=(1, 1, 1),
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if header == "Característica"
                    else fitz.TEXT_ALIGN_CENTER
                ),
            )

        layout.advance(
            self.TABLE_HEADER_HEIGHT
        )

    def _draw_table_row(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        group: Any,
        alternate: bool,
    ) -> None:
        values = [
            self._clean_text(
                getattr(
                    group,
                    "display_name",
                    None,
                ),
                fallback="Característica",
            ),
            str(
                getattr(
                    group,
                    "measurement_count",
                    0,
                )
                or 0
            ),
            self._format_number(
                getattr(
                    group,
                    "nominal_value",
                    None,
                )
            ),
            self._format_number(
                getattr(
                    group,
                    "minimum",
                    None,
                )
            ),
            self._format_number(
                getattr(
                    group,
                    "maximum",
                    None,
                )
            ),
            self._format_number(
                getattr(
                    group,
                    "mean",
                    None,
                )
            ),
            self._format_number(
                getattr(
                    group,
                    "amplitude",
                    None,
                )
            ),
            self._format_number(
                self._std_dev(
                    group
                )
            ),
            self._format_index(
                getattr(
                    group,
                    "cp",
                    None,
                )
            ),
            self._format_index(
                getattr(
                    group,
                    "cpk",
                    None,
                )
            ),
            self._status_label(
                group
            ),
        ]

        columns = self._columns(
            layout.geometry.content_width
        )

        base_fill = (
            self.COLOR_SURFACE
            if alternate
            else (1, 1, 1)
        )

        for index, (
            value,
            rect,
        ) in enumerate(
            zip(
                values,
                columns,
            )
        ):
            cell = fitz.Rect(
                layout.geometry.margin_left + rect.x0,
                layout.cursor_y,
                layout.geometry.margin_left + rect.x1,
                layout.cursor_y + self.TABLE_ROW_HEIGHT,
            )

            fill = base_fill
            color = self.COLOR_TEXT
            font = "helv"

            if index == 10:
                status = self._status_code(
                    group
                )
                font = "hebo"

                if status == "OK":
                    fill = self.COLOR_OK_BG
                    color = self.COLOR_OK
                elif status == "NOK":
                    fill = self.COLOR_NOK_BG
                    color = self.COLOR_NOK
                else:
                    fill = base_fill
                    color = self.COLOR_MUTED

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.3,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 3,
                    cell.y0 + 8,
                    cell.x1 - 3,
                    cell.y1 - 4,
                ),
                value,
                fontsize=4.9,
                fontname=font,
                color=color,
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if index == 0
                    else fitz.TEXT_ALIGN_CENTER
                ),
            )

    # =============================================================
    # COLUNAS
    # =============================================================

    def _columns(
        self,
        content_width: float,
    ) -> list[fitz.Rect]:
        ratios = [
            0.22,
            0.05,
            0.09,
            0.08,
            0.08,
            0.09,
            0.09,
            0.10,
            0.06,
            0.06,
            0.08,
        ]

        x = 0.0
        columns = []

        for ratio in ratios:
            width = content_width * ratio
            columns.append(
                fitz.Rect(
                    x,
                    0,
                    x + width,
                    0,
                )
            )
            x += width

        return columns

    # =============================================================
    # TÍTULO E STATUS
    # =============================================================

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

    def _status_code(
        self,
        group: Any,
    ) -> str:
        if int(
            getattr(
                group,
                "nok_count",
                0,
            )
            or 0
        ) > 0:
            return "NOK"

        if int(
            getattr(
                group,
                "ok_count",
                0,
            )
            or 0
        ) > 0:
            return "OK"

        return "UNKNOWN"

    def _status_label(
        self,
        group: Any,
    ) -> str:
        status = self._status_code(
            group
        )

        if status == "OK":
            return "CONFORME"

        if status == "NOK":
            return "NÃO CONFORME"

        return "—"

    # =============================================================
    # FORMATAÇÃO
    # =============================================================

    def _std_dev(
        self,
        group: Any,
    ) -> Any:
        value = getattr(
            group,
            "standard_deviation",
            None,
        )

        if value is not None:
            return value

        return getattr(
            group,
            "std_dev",
            None,
        )

    def _format_number(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            number = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return self._clean_text(
                value,
                fallback="—",
            )

        return (
            f"{number:.4f}"
            .replace(
                ".",
                ",",
            )
        )

    def _format_index(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            number = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return "—"

        return (
            f"{number:.2f}"
            .replace(
                ".",
                ",",
            )
        )

    def _clean_text(
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