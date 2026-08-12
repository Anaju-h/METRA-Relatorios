from __future__ import annotations

from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class DimensionalIndividualResultsPage:
    """
    Página de resultados do relatório dimensional individual.

    Regras principais:
    - uma única medição não gera gráfico de tendência;
    - resultados são exibidos em cartões técnicos compactos;
    - tabelas são quebradas automaticamente entre páginas;
    - gráficos só aparecem quando realmente agregam informação;
    - características sem tolerância são identificadas como
      "avaliação parcial", sem forçar status OK ou NOK.
    """

    COLOR_NAVY = (
        0.025,
        0.110,
        0.215,
    )

    COLOR_BLUE = (
        0.000,
        0.400,
        0.720,
    )

    COLOR_TEXT = (
        0.070,
        0.100,
        0.135,
    )

    COLOR_MUTED = (
        0.360,
        0.410,
        0.470,
    )

    COLOR_BORDER = (
        0.790,
        0.825,
        0.860,
    )

    COLOR_SURFACE = (
        0.975,
        0.982,
        0.988,
    )

    COLOR_LIGHT_BLUE = (
        0.925,
        0.960,
        0.987,
    )

    COLOR_OK = (
        0.080,
        0.500,
        0.275,
    )

    COLOR_OK_BG = (
        0.910,
        0.975,
        0.935,
    )

    COLOR_NOK = (
        0.760,
        0.160,
        0.120,
    )

    COLOR_NOK_BG = (
        0.995,
        0.920,
        0.905,
    )

    COLOR_WARNING = (
        0.800,
        0.430,
        0.000,
    )

    COLOR_WARNING_BG = (
        1.000,
        0.965,
        0.870,
    )

    SECTION_TITLE_HEIGHT = 28.0
    TABLE_HEADER_HEIGHT = 26.0
    TABLE_ROW_HEIGHT = 30.0
    CHARACTERISTIC_CARD_HEIGHT = 102.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        groups = render_context.statistical_groups

        if not groups:
            self._render_empty_state(
                layout=layout,
            )
            return

        self._render_summary(
            layout=layout,
            render_context=render_context,
        )

        self._render_results_table(
            layout=layout,
            groups=groups,
        )

        self._render_characteristic_cards(
            layout=layout,
            groups=groups,
        )

        self._render_relevant_chart(
            layout=layout,
            render_context=render_context,
        )

    # =============================================================
    # RESUMO
    # =============================================================

    def _render_summary(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        summary = render_context.overall_statistics

        total = int(
            summary.get(
                "measurement_count",
                0,
            )
            or 0
        )

        group_count = int(
            summary.get(
                "group_count",
                0,
            )
            or 0
        )

        ok_count = int(
            summary.get(
                "ok_count",
                0,
            )
            or 0
        )

        nok_count = int(
            summary.get(
                "nok_count",
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

        conformity = float(
            summary.get(
                "conformity_percentage",
                0.0,
            )
            or 0.0
        )

        height = 106.0

        page = layout.ensure_space(
            height,
            repeated_title="RESULTADOS DIMENSIONAIS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="3. RESULTADOS DIMENSIONAIS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        if evaluated_count > 0:
            indicators = [
                (
                    "Resultados",
                    total,
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
                (
                    "Conformes",
                    ok_count,
                    self.COLOR_OK_BG,
                    self.COLOR_OK,
                ),
                (
                    "Não conformes",
                    nok_count,
                    self.COLOR_NOK_BG,
                    self.COLOR_NOK,
                ),
                (
                    "Conformidade",
                    f"{conformity:.1f}%",
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
            ]
        else:
            indicators = [
                (
                    "Características",
                    group_count,
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
                (
                    "Resultados",
                    total,
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
                (
                    "Dados extraídos",
                    total,
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
            ]

        gap = 7.0
        card_height = 68.0

        card_width = (
            layout.geometry.content_width
            - gap
            * (
                len(indicators) - 1
            )
        ) / len(indicators)

        for index, (
            label,
            value,
            background,
            accent,
        ) in enumerate(indicators):
            x = (
                layout.geometry.margin_left
                + index
                * (
                    card_width
                    + gap
                )
            )

            rect = fitz.Rect(
                x,
                layout.cursor_y,
                x + card_width,
                layout.cursor_y
                + card_height,
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
                    rect.y0 + 8,
                    rect.x1 - 4,
                    rect.y0 + 22,
                ),
                label,
                fontsize=5.7,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 28,
                    rect.x1 - 4,
                    rect.y1 - 8,
                ),
                str(value),
                fontsize=12.0,
                fontname="hebo",
                color=accent,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            card_height
            + self.GAP
        )

    # =============================================================
    # TABELA
    # =============================================================

    def _render_results_table(
        self,
        *,
        layout: ReportLayoutEngine,
        groups: list[Any],
    ) -> None:
        if not groups:
            return

        self._draw_table_title(
            layout=layout,
        )

        for index, group in enumerate(
            groups
        ):
            required = self.TABLE_ROW_HEIGHT

            page = layout.ensure_space(
                required,
                repeated_title="RESULTADOS DIMENSIONAIS",
            )

            if (
                layout.cursor_y
                <= layout.geometry.margin_top + 90
            ):
                self._draw_table_title(
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

    def _draw_table_title(
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
            repeated_title="RESULTADOS DIMENSIONAIS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="TABELA CONSOLIDADA",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        columns = self._table_columns(
            layout.geometry.content_width
        )

        headers = [
            "Característica",
            "Nominal",
            "Medido",
            "Desvio",
            "Tol. inferior",
            "Tol. superior",
            "Status",
        ]

        for (
            header,
            rect,
        ) in zip(
            headers,
            columns,
        ):
            header_rect = fitz.Rect(
                rect.x0,
                layout.cursor_y,
                rect.x1,
                layout.cursor_y
                + self.TABLE_HEADER_HEIGHT,
            )

            page.draw_rect(
                header_rect,
                color=self.COLOR_BORDER,
                fill=self.COLOR_NAVY,
                width=0.4,
            )

            page.insert_textbox(
                fitz.Rect(
                    header_rect.x0 + 4,
                    header_rect.y0 + 7,
                    header_rect.x1 - 4,
                    header_rect.y1 - 4,
                ),
                header,
                fontsize=5.5,
                fontname="hebo",
                color=(
                    1,
                    1,
                    1,
                ),
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if header
                    == "Característica"
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
        columns = self._table_columns(
            layout.geometry.content_width
        )

        measurement = (
            group.measurements[0]
            if getattr(
                group,
                "measurements",
                None,
            )
            else None
        )

        measured_value = (
            getattr(
                measurement,
                "measured_value",
                None,
            )
            if measurement is not None
            else None
        )

        deviation = (
            getattr(
                measurement,
                "deviation",
                None,
            )
            if measurement is not None
            else None
        )

        values = [
            self._clean_text(
                getattr(
                    group,
                    "display_name",
                    None,
                ),
                fallback="Característica",
            ),
            self._format_number(
                getattr(
                    group,
                    "nominal_value",
                    None,
                )
            ),
            self._format_number(
                measured_value
            ),
            self._format_number(
                deviation
            ),
            self._format_number(
                getattr(
                    group,
                    "lower_limit",
                    None,
                )
            ),
            self._format_number(
                getattr(
                    group,
                    "upper_limit",
                    None,
                )
            ),
            self._status_label(
                group
            ),
        ]

        fill = (
            self.COLOR_SURFACE
            if alternate
            else (
                1,
                1,
                1,
            )
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
                rect.x0,
                layout.cursor_y,
                rect.x1,
                layout.cursor_y
                + self.TABLE_ROW_HEIGHT,
            )

            background = fill
            text_color = self.COLOR_TEXT

            if index == 6:
                status = self._status_code(
                    group
                )

                if status == "OK":
                    background = self.COLOR_OK_BG
                    text_color = self.COLOR_OK
                elif status == "NOK":
                    background = self.COLOR_NOK_BG
                    text_color = self.COLOR_NOK
                else:
                    background = self.COLOR_SURFACE
                    text_color = self.COLOR_MUTED

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=background,
                width=0.35,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 4,
                    cell.y0 + 7,
                    cell.x1 - 4,
                    cell.y1 - 4,
                ),
                value,
                fontsize=5.7,
                fontname=(
                    "hebo"
                    if index == 6
                    else "helv"
                ),
                color=text_color,
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if index == 0
                    else fitz.TEXT_ALIGN_CENTER
                ),
            )

    def _table_columns(
        self,
        content_width: float,
    ) -> list[fitz.Rect]:
        ratios = [
            0.26,
            0.12,
            0.12,
            0.11,
            0.14,
            0.14,
            0.11,
        ]

        columns = []

        current_x = 0.0

        for ratio in ratios:
            width = (
                content_width
                * ratio
            )

            columns.append(
                fitz.Rect(
                    current_x,
                    0,
                    current_x + width,
                    0,
                )
            )

            current_x += width

        offset = 34.0

        return [
            fitz.Rect(
                column.x0 + offset,
                0,
                column.x1 + offset,
                0,
            )
            for column in columns
        ]

    # =============================================================
    # CARDS
    # =============================================================

    def _render_characteristic_cards(
        self,
        *,
        layout: ReportLayoutEngine,
        groups: list[Any],
    ) -> None:
        if not groups:
            return

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + self.CHARACTERISTIC_CARD_HEIGHT,
            repeated_title="ANÁLISE POR CARACTERÍSTICA",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="ANÁLISE POR CARACTERÍSTICA",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        for group in groups:
            page = layout.ensure_space(
                self.CHARACTERISTIC_CARD_HEIGHT
                + self.GAP,
                repeated_title="ANÁLISE POR CARACTERÍSTICA",
            )

            if (
                layout.cursor_y
                <= layout.geometry.margin_top + 90
            ):
                self._draw_section_title(
                    page=page,
                    layout=layout,
                    title="ANÁLISE POR CARACTERÍSTICA",
                )

                layout.advance(
                    self.SECTION_TITLE_HEIGHT
                )

            self._draw_characteristic_card(
                page=page,
                layout=layout,
                group=group,
            )

            layout.advance(
                self.CHARACTERISTIC_CARD_HEIGHT
                + self.GAP
            )

    def _draw_characteristic_card(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        group: Any,
    ) -> None:
        rect = layout.full_width_rect(
            self.CHARACTERISTIC_CARD_HEIGHT
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(
                1,
                1,
                1,
            ),
            width=0.6,
        )

        status = self._status_code(
            group
        )

        if status == "OK":
            accent = self.COLOR_OK
            background = self.COLOR_OK_BG
        elif status == "NOK":
            accent = self.COLOR_NOK
            background = self.COLOR_NOK_BG
        else:
            accent = self.COLOR_BLUE
            background = self.COLOR_LIGHT_BLUE

        title_rect = fitz.Rect(
            rect.x0,
            rect.y0,
            rect.x1,
            rect.y0 + 27,
        )

        page.draw_rect(
            title_rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.4,
        )

        page.insert_textbox(
            fitz.Rect(
                title_rect.x0 + 9,
                title_rect.y0 + 7,
                title_rect.x1 - 94,
                title_rect.y1 - 4,
            ),
            self._clean_text(
                getattr(
                    group,
                    "display_name",
                    None,
                ),
                fallback="Característica",
            ),
            fontsize=7.2,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

        status_rect = fitz.Rect(
            title_rect.x1 - 84,
            title_rect.y0 + 5,
            title_rect.x1 - 8,
            title_rect.y1 - 5,
        )

        page.draw_rect(
            status_rect,
            color=accent,
            fill=background,
            width=0.6,
        )

        card_status_label = (
            "RESULTADO"
            if status == "UNKNOWN"
            else self._status_label(
                group
            )
        )

        page.insert_textbox(
            status_rect,
            card_status_label,
            fontsize=6.0,
            fontname="hebo",
            color=accent,
            align=fitz.TEXT_ALIGN_CENTER,
        )

        measurement = (
            group.measurements[0]
            if getattr(
                group,
                "measurements",
                None,
            )
            else None
        )

        values = [
            (
                "Nominal",
                self._format_number(
                    getattr(
                        group,
                        "nominal_value",
                        None,
                    )
                ),
            ),
            (
                "Medido",
                self._format_number(
                    getattr(
                        measurement,
                        "measured_value",
                        None,
                    )
                    if measurement is not None
                    else None
                ),
            ),
            (
                "Desvio",
                self._format_number(
                    getattr(
                        measurement,
                        "deviation",
                        None,
                    )
                    if measurement is not None
                    else None
                ),
            ),
            (
                "Limite inferior",
                self._format_number(
                    getattr(
                        group,
                        "lower_limit",
                        None,
                    )
                ),
            ),
            (
                "Limite superior",
                self._format_number(
                    getattr(
                        group,
                        "upper_limit",
                        None,
                    )
                ),
            ),
        ]

        gap = 6.0

        card_width = (
            rect.width
            - 16
            - gap
            * (
                len(values) - 1
            )
        ) / len(values)

        start_x = (
            rect.x0 + 8
        )

        start_y = (
            rect.y0 + 35
        )

        card_height = 52.0

        for index, (
            label,
            value,
        ) in enumerate(values):
            x = (
                start_x
                + index
                * (
                    card_width
                    + gap
                )
            )

            metric_rect = fitz.Rect(
                x,
                start_y,
                x + card_width,
                start_y + card_height,
            )

            page.draw_rect(
                metric_rect,
                color=self.COLOR_BORDER,
                fill=self.COLOR_SURFACE,
                width=0.4,
            )

            page.insert_textbox(
                fitz.Rect(
                    metric_rect.x0 + 3,
                    metric_rect.y0 + 6,
                    metric_rect.x1 - 3,
                    metric_rect.y0 + 18,
                ),
                label,
                fontsize=5.2,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    metric_rect.x0 + 3,
                    metric_rect.y0 + 23,
                    metric_rect.x1 - 3,
                    metric_rect.y1 - 5,
                ),
                value,
                fontsize=8.6,
                fontname="hebo",
                color=self.COLOR_NAVY,
                align=fitz.TEXT_ALIGN_CENTER,
            )

    # =============================================================
    # GRÁFICO RELEVANTE
    # =============================================================

    def _render_relevant_chart(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        chart_path = (
            render_context.group_summary_chart
        )

        if (
            chart_path is None
            or not chart_path.exists()
        ):
            return

        height = 232.0
        caption_height = 34.0

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + height
            + caption_height,
            repeated_title="ANÁLISE GRÁFICA",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="ANÁLISE GRÁFICA DAS CARACTERÍSTICAS",
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
            fill=(
                1,
                1,
                1,
            ),
            width=0.5,
        )

        page.insert_image(
            fitz.Rect(
                rect.x0 + 10,
                rect.y0 + 10,
                rect.x1 - 10,
                rect.y1 - 10,
            ),
            filename=str(
                chart_path
            ),
            keep_proportion=True,
        )

        layout.advance(
            height
        )

        caption_rect = layout.full_width_rect(
            caption_height
        )

        page.draw_rect(
            caption_rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_SURFACE,
            width=0.4,
        )

        page.insert_textbox(
            fitz.Rect(
                caption_rect.x0 + 10,
                caption_rect.y0 + 7,
                caption_rect.x1 - 10,
                caption_rect.y1 - 5,
            ),
            (
                "Visão comparativa das características dimensionais "
                "avaliadas. O gráfico complementa a tabela consolidada "
                "e facilita a identificação visual dos resultados críticos."
            ),
            fontsize=5.8,
            fontname="helv",
            color=self.COLOR_MUTED,
            lineheight=1.10,
        )

        layout.advance(
            caption_height
        )

    # =============================================================
    # VAZIO
    # =============================================================

    def _render_empty_state(
        self,
        *,
        layout: ReportLayoutEngine,
    ) -> None:
        height = 90.0

        page = layout.ensure_space(
            height,
            repeated_title="RESULTADOS DIMENSIONAIS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="3. RESULTADOS DIMENSIONAIS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        rect = layout.full_width_rect(
            height
            - self.SECTION_TITLE_HEIGHT
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_WARNING_BG,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 16,
                rect.x1 - 12,
                rect.y1 - 12,
            ),
            (
                "Nenhum resultado dimensional estruturado "
                "foi encontrado para este processo."
            ),
            fontsize=7.4,
            fontname="helv",
            color=self.COLOR_WARNING,
            align=fitz.TEXT_ALIGN_CENTER,
        )

        layout.advance(
            height
            - self.SECTION_TITLE_HEIGHT
        )

    # =============================================================
    # TÍTULOS
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
            fontsize=7.4,
            fontname="hebo",
            color=(
                1,
                1,
                1,
            ),
        )

    # =============================================================
    # STATUS
    # =============================================================

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

    def _format_number(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "-"

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
                fallback="-",
            )

        return (
            f"{number:.4f}"
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
                value
                or ""
            ).split()
        )

        return (
            cleaned
            or fallback
        )