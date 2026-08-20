from __future__ import annotations

from pathlib import Path
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
            # Regra METRA: se não há informação real, a seção não aparece.
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

        self._render_graphical_analysis(
            layout=layout,
            render_context=render_context,
            groups=groups,
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
    # ANÁLISE GRÁFICA
    # =============================================================

    def _render_graphical_analysis(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
        groups: list[Any],
    ) -> None:
        """
        Gráficos do template individual.

        Regras:
        - o gráfico principal mostra o desvio relativo ao nominal (%);
        - não exibe gráficos redundantes com a mesma informação;
        - só adiciona um segundo gráfico quando houver tolerâncias realmente
          avaliáveis e, portanto, uma leitura técnica diferente;
        - sem tolerâncias, permanece apenas o gráfico de desvio relativo.
        """

        comparable = self._collect_comparable_groups(
            groups
        )

        deviations = self._collect_deviation_groups(
            groups
        )

        summary = render_context.overall_statistics

        evaluated_count = int(
            summary.get(
                "evaluated_count",
                0,
            )
            or 0
        )

        blocks = []

        percentage_rows = self._collect_percentage_deviation_groups(
            groups
        )

        if len(percentage_rows) >= 2:
            blocks.append(
                (
                    "DESVIO RELATIVO AO NOMINAL",
                    "Apresenta o desvio percentual de cada característica em relação ao valor nominal, facilitando a comparação entre grandezas.",
                    "percentage_deviation",
                    percentage_rows,
                )
            )

        tolerance_rows = self._collect_tolerance_groups(
            groups
        )

        if (
            evaluated_count > 0
            and len(tolerance_rows) >= 1
        ):
            blocks.append(
                (
                    "POSIÇÃO DENTRO DA TOLERÂNCIA",
                    "Mostra onde o valor medido se encontra em relação aos limites inferior e superior informados.",
                    "tolerance",
                    tolerance_rows,
                )
            )

        if not blocks:
            return

        for (
            title,
            description,
            chart_type,
            data,
        ) in blocks:
            if chart_type == "percentage_deviation":
                self._draw_percentage_deviation_chart(
                    layout=layout,
                    title=title,
                    description=description,
                    rows=data,
                )
            elif chart_type == "tolerance":
                self._draw_tolerance_chart(
                    layout=layout,
                    title=title,
                    description=description,
                    rows=data,
                )

    def _collect_comparable_groups(
        self,
        groups: list[Any],
    ) -> list[dict[str, Any]]:
        rows = []

        for group in groups:
            measurement = (
                group.measurements[0]
                if getattr(
                    group,
                    "measurements",
                    None,
                )
                else None
            )

            if measurement is None:
                continue

            nominal = self._as_float(
                getattr(
                    group,
                    "nominal_value",
                    None,
                )
            )

            measured = self._as_float(
                getattr(
                    measurement,
                    "measured_value",
                    None,
                )
            )

            if nominal is None or measured is None:
                continue

            rows.append(
                {
                    "name": self._clean_text(
                        getattr(
                            group,
                            "display_name",
                            None,
                        ),
                        fallback="Característica",
                    ),
                    "nominal": nominal,
                    "measured": measured,
                }
            )

        return rows

    def _collect_deviation_groups(
        self,
        groups: list[Any],
    ) -> list[dict[str, Any]]:
        rows = []

        for group in groups:
            measurement = (
                group.measurements[0]
                if getattr(
                    group,
                    "measurements",
                    None,
                )
                else None
            )

            if measurement is None:
                continue

            deviation = self._as_float(
                getattr(
                    measurement,
                    "deviation",
                    None,
                )
            )

            if deviation is None:
                continue

            rows.append(
                {
                    "name": self._clean_text(
                        getattr(
                            group,
                            "display_name",
                            None,
                        ),
                        fallback="Característica",
                    ),
                    "deviation": deviation,
                }
            )

        return rows

    def _collect_percentage_deviation_groups(
        self,
        groups: list[Any],
    ) -> list[dict[str, Any]]:
        rows = []

        for group in groups:
            measurement = (
                group.measurements[0]
                if getattr(
                    group,
                    "measurements",
                    None,
                )
                else None
            )

            if measurement is None:
                continue

            nominal = self._as_float(
                getattr(
                    group,
                    "nominal_value",
                    None,
                )
            )
            measured = self._as_float(
                getattr(
                    measurement,
                    "measured_value",
                    None,
                )
            )

            if (
                nominal is None
                or measured is None
                or abs(nominal) <= 1e-12
            ):
                continue

            percentage = (
                (measured - nominal)
                / abs(nominal)
                * 100.0
            )

            rows.append(
                {
                    "name": self._clean_text(
                        getattr(
                            group,
                            "display_name",
                            None,
                        ),
                        fallback="Característica",
                    ),
                    "percentage": percentage,
                }
            )

        return rows

    def _draw_percentage_deviation_chart(
        self,
        *,
        layout: ReportLayoutEngine,
        title: str,
        description: str,
        rows: list[dict[str, Any]],
    ) -> None:
        rows = rows[:10]

        chart_height = max(
            150.0,
            48.0 + len(rows) * 31.0,
        )

        total_height = (
            self.SECTION_TITLE_HEIGHT
            + 34.0
            + chart_height
            + self.GAP
        )

        page = layout.ensure_space(
            total_height,
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

        self._draw_chart_heading(
            page=page,
            layout=layout,
            title=title,
            description=description,
        )
        layout.advance(34.0)

        rect = layout.full_width_rect(
            chart_height
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.5,
        )

        max_abs = max(
            abs(row["percentage"])
            for row in rows
        )

        if max_abs <= 1e-12:
            max_abs = 1.0

        label_width = min(
            180.0,
            rect.width * 0.34,
        )
        plot_x0 = rect.x0 + label_width
        plot_x1 = rect.x1 - 60.0
        zero_x = (
            plot_x0 + plot_x1
        ) / 2.0
        half_width = (
            plot_x1 - plot_x0
        ) / 2.0

        top = rect.y0 + 15.0
        row_height = (
            rect.height - 30.0
        ) / len(rows)

        page.draw_line(
            fitz.Point(
                zero_x,
                rect.y0 + 9,
            ),
            fitz.Point(
                zero_x,
                rect.y1 - 9,
            ),
            color=self.COLOR_MUTED,
            width=0.6,
        )

        for index, row in enumerate(rows):
            center_y = (
                top
                + index * row_height
                + row_height / 2
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    center_y - 10,
                    plot_x0 - 8,
                    center_y + 10,
                ),
                self._short_label(
                    row["name"],
                    30,
                ),
                fontsize=5.7,
                fontname="helv",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

            percentage = row["percentage"]
            length = (
                abs(percentage)
                / max_abs
                * (half_width - 10.0)
            )

            if percentage >= 0:
                x0 = zero_x
                x1 = zero_x + length
                fill = self.COLOR_BLUE
            else:
                x0 = zero_x - length
                x1 = zero_x
                fill = self.COLOR_NAVY

            if abs(x1 - x0) < 1.0:
                x1 = x0 + (
                    1.0
                    if percentage >= 0
                    else -1.0
                )

            page.draw_rect(
                fitz.Rect(
                    min(x0, x1),
                    center_y - 5.0,
                    max(x0, x1),
                    center_y + 5.0,
                ),
                color=fill,
                fill=fill,
                width=0.4,
            )

            page.insert_textbox(
                fitz.Rect(
                    plot_x1 + 4,
                    center_y - 9,
                    rect.x1 - 6,
                    center_y + 9,
                ),
                f"{percentage:+.2f}%",
                fontsize=5.6,
                fontname="hebo",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

        layout.advance(
            chart_height
            + self.GAP
        )

    def _collect_tolerance_groups(
        self,
        groups: list[Any],
    ) -> list[dict[str, Any]]:
        rows = []

        for group in groups:
            measurement = (
                group.measurements[0]
                if getattr(
                    group,
                    "measurements",
                    None,
                )
                else None
            )

            if measurement is None:
                continue

            measured = self._as_float(
                getattr(
                    measurement,
                    "measured_value",
                    None,
                )
            )
            lower = self._as_float(
                getattr(
                    group,
                    "lower_limit",
                    None,
                )
            )
            upper = self._as_float(
                getattr(
                    group,
                    "upper_limit",
                    None,
                )
            )

            if (
                measured is None
                or lower is None
                or upper is None
                or upper <= lower
            ):
                continue

            rows.append(
                {
                    "name": self._clean_text(
                        getattr(
                            group,
                            "display_name",
                            None,
                        ),
                        fallback="Característica",
                    ),
                    "measured": measured,
                    "lower": lower,
                    "upper": upper,
                }
            )

        return rows

    def _draw_tolerance_chart(
        self,
        *,
        layout: ReportLayoutEngine,
        title: str,
        description: str,
        rows: list[dict[str, Any]],
    ) -> None:
        rows = rows[:10]

        chart_height = max(
            150.0,
            48.0 + len(rows) * 31.0,
        )

        total_height = (
            self.SECTION_TITLE_HEIGHT
            + 34.0
            + chart_height
            + self.GAP
        )

        page = layout.ensure_space(
            total_height,
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

        self._draw_chart_heading(
            page=page,
            layout=layout,
            title=title,
            description=description,
        )
        layout.advance(34.0)

        rect = layout.full_width_rect(
            chart_height
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.5,
        )

        label_width = min(
            180.0,
            rect.width * 0.34,
        )
        plot_x0 = rect.x0 + label_width
        plot_x1 = rect.x1 - 70.0

        top = rect.y0 + 15.0
        row_height = (
            rect.height - 30.0
        ) / len(rows)

        for index, row in enumerate(rows):
            center_y = (
                top
                + index * row_height
                + row_height / 2
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    center_y - 10,
                    plot_x0 - 8,
                    center_y + 10,
                ),
                self._short_label(
                    row["name"],
                    30,
                ),
                fontsize=5.7,
                fontname="helv",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

            # A faixa inteira representa os limites de tolerância.
            page.draw_line(
                fitz.Point(
                    plot_x0,
                    center_y,
                ),
                fitz.Point(
                    plot_x1,
                    center_y,
                ),
                color=self.COLOR_BLUE,
                width=6.0,
            )

            position = (
                row["measured"] - row["lower"]
            ) / (
                row["upper"] - row["lower"]
            )

            # Permite visualizar também resultados fora da faixa.
            clamped = max(
                -0.12,
                min(
                    1.12,
                    position,
                ),
            )

            measured_x = (
                plot_x0
                + clamped
                * (
                    plot_x1 - plot_x0
                )
            )

            in_tolerance = (
                0.0 <= position <= 1.0
            )

            point_color = (
                self.COLOR_GREEN
                if in_tolerance
                else self.COLOR_RED
            )

            page.draw_circle(
                fitz.Point(
                    measured_x,
                    center_y,
                ),
                radius=4.2,
                color=point_color,
                fill=point_color,
                width=0.5,
            )

            status = (
                "Dentro"
                if in_tolerance
                else "Fora"
            )

            page.insert_textbox(
                fitz.Rect(
                    plot_x1 + 8,
                    center_y - 9,
                    rect.x1 - 6,
                    center_y + 9,
                ),
                status,
                fontsize=5.6,
                fontname="hebo",
                color=point_color,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

        layout.advance(
            chart_height
            + self.GAP
        )

    def _draw_nominal_measured_chart(
        self,
        *,
        layout: ReportLayoutEngine,
        title: str,
        description: str,
        rows: list[dict[str, Any]],
    ) -> None:
        rows = rows[:10]

        chart_height = max(
            150.0,
            48.0 + len(rows) * 31.0,
        )

        total_height = (
            self.SECTION_TITLE_HEIGHT
            + 34.0
            + chart_height
            + self.GAP
        )

        page = layout.ensure_space(
            total_height,
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

        self._draw_chart_heading(
            page=page,
            layout=layout,
            title=title,
            description=description,
        )
        layout.advance(34.0)

        rect = layout.full_width_rect(
            chart_height
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.5,
        )

        all_values = [
            value
            for row in rows
            for value in (
                row["nominal"],
                row["measured"],
            )
        ]

        minimum = min(all_values)
        maximum = max(all_values)
        span = maximum - minimum

        if span <= 1e-12:
            span = max(
                abs(maximum) * 0.02,
                1.0,
            )

        padding = span * 0.12
        axis_min = minimum - padding
        axis_max = maximum + padding

        label_width = min(
            180.0,
            rect.width * 0.34,
        )
        plot_x0 = rect.x0 + label_width
        plot_x1 = rect.x1 - 22.0
        top = rect.y0 + 18.0
        row_height = (
            rect.height - 34.0
        ) / len(rows)

        for index, row in enumerate(rows):
            center_y = (
                top
                + index * row_height
                + row_height / 2
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    center_y - 10,
                    plot_x0 - 8,
                    center_y + 10,
                ),
                self._short_label(
                    row["name"],
                    30,
                ),
                fontsize=5.7,
                fontname="helv",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

            page.draw_line(
                fitz.Point(
                    plot_x0,
                    center_y,
                ),
                fitz.Point(
                    plot_x1,
                    center_y,
                ),
                color=self.COLOR_BORDER,
                width=0.45,
            )

            nominal_x = self._scale_x(
                row["nominal"],
                axis_min,
                axis_max,
                plot_x0,
                plot_x1,
            )
            measured_x = self._scale_x(
                row["measured"],
                axis_min,
                axis_max,
                plot_x0,
                plot_x1,
            )

            # Nominal: marca vertical azul.
            page.draw_line(
                fitz.Point(
                    nominal_x,
                    center_y - 7,
                ),
                fitz.Point(
                    nominal_x,
                    center_y + 7,
                ),
                color=self.COLOR_BLUE,
                width=2.2,
            )

            # Medido: ponto navy.
            page.draw_circle(
                fitz.Point(
                    measured_x,
                    center_y,
                ),
                radius=3.5,
                color=self.COLOR_NAVY,
                fill=self.COLOR_NAVY,
                width=0.5,
            )

        legend_y = rect.y1 - 13.0

        page.draw_line(
            fitz.Point(
                rect.x0 + 14,
                legend_y - 3,
            ),
            fitz.Point(
                rect.x0 + 14,
                legend_y + 5,
            ),
            color=self.COLOR_BLUE,
            width=2.0,
        )

        page.insert_text(
            fitz.Point(
                rect.x0 + 22,
                legend_y + 3,
            ),
            "Nominal",
            fontsize=5.5,
            fontname="helv",
            color=self.COLOR_MUTED,
        )

        page.draw_circle(
            fitz.Point(
                rect.x0 + 82,
                legend_y + 1,
            ),
            radius=3.0,
            color=self.COLOR_NAVY,
            fill=self.COLOR_NAVY,
            width=0.4,
        )

        page.insert_text(
            fitz.Point(
                rect.x0 + 90,
                legend_y + 3,
            ),
            "Medido",
            fontsize=5.5,
            fontname="helv",
            color=self.COLOR_MUTED,
        )

        layout.advance(
            chart_height
            + self.GAP
        )

    def _draw_deviation_chart(
        self,
        *,
        layout: ReportLayoutEngine,
        title: str,
        description: str,
        rows: list[dict[str, Any]],
    ) -> None:
        rows = rows[:10]

        chart_height = max(
            150.0,
            48.0 + len(rows) * 31.0,
        )

        total_height = (
            self.SECTION_TITLE_HEIGHT
            + 34.0
            + chart_height
            + self.GAP
        )

        page = layout.ensure_space(
            total_height,
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

        self._draw_chart_heading(
            page=page,
            layout=layout,
            title=title,
            description=description,
        )
        layout.advance(34.0)

        rect = layout.full_width_rect(
            chart_height
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.5,
        )

        max_abs = max(
            abs(row["deviation"])
            for row in rows
        )

        if max_abs <= 1e-12:
            max_abs = 1.0

        label_width = min(
            180.0,
            rect.width * 0.34,
        )
        plot_x0 = rect.x0 + label_width
        plot_x1 = rect.x1 - 48.0
        zero_x = (
            plot_x0 + plot_x1
        ) / 2.0
        half_width = (
            plot_x1 - plot_x0
        ) / 2.0

        top = rect.y0 + 15.0
        row_height = (
            rect.height - 30.0
        ) / len(rows)

        page.draw_line(
            fitz.Point(
                zero_x,
                rect.y0 + 9,
            ),
            fitz.Point(
                zero_x,
                rect.y1 - 9,
            ),
            color=self.COLOR_MUTED,
            width=0.6,
        )

        for index, row in enumerate(rows):
            center_y = (
                top
                + index * row_height
                + row_height / 2
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    center_y - 10,
                    plot_x0 - 8,
                    center_y + 10,
                ),
                self._short_label(
                    row["name"],
                    30,
                ),
                fontsize=5.7,
                fontname="helv",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

            deviation = row["deviation"]
            length = (
                abs(deviation)
                / max_abs
                * (half_width - 10.0)
            )

            if deviation >= 0:
                x0 = zero_x
                x1 = zero_x + length
                fill = self.COLOR_BLUE
            else:
                x0 = zero_x - length
                x1 = zero_x
                fill = self.COLOR_NAVY

            bar = fitz.Rect(
                x0,
                center_y - 5.0,
                x1,
                center_y + 5.0,
            )

            page.draw_rect(
                bar,
                color=fill,
                fill=fill,
                width=0.4,
            )

            page.insert_textbox(
                fitz.Rect(
                    plot_x1 + 4,
                    center_y - 9,
                    rect.x1 - 6,
                    center_y + 9,
                ),
                self._format_number(
                    deviation
                ),
                fontsize=5.6,
                fontname="hebo",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

        layout.advance(
            chart_height
            + self.GAP
        )

    def _draw_image_chart(
        self,
        *,
        layout: ReportLayoutEngine,
        title: str,
        description: str,
        chart_path: Path,
    ) -> None:
        chart_height = 210.0

        total_height = (
            self.SECTION_TITLE_HEIGHT
            + 34.0
            + chart_height
            + self.GAP
        )

        page = layout.ensure_space(
            total_height,
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

        self._draw_chart_heading(
            page=page,
            layout=layout,
            title=title,
            description=description,
        )
        layout.advance(34.0)

        rect = layout.full_width_rect(
            chart_height
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.5,
        )

        try:
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
        except Exception:
            return

        layout.advance(
            chart_height
            + self.GAP
        )

    def _draw_chart_heading(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        title: str,
        description: str,
    ) -> None:
        rect = layout.full_width_rect(
            34.0
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_SURFACE,
            width=0.4,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 9,
                rect.y0 + 5,
                rect.x1 - 9,
                rect.y0 + 16,
            ),
            title,
            fontsize=6.5,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 9,
                rect.y0 + 17,
                rect.x1 - 9,
                rect.y1 - 4,
            ),
            description,
            fontsize=5.4,
            fontname="helv",
            color=self.COLOR_MUTED,
        )

    def _as_float(
        self,
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def _scale_x(
        self,
        value: float,
        minimum: float,
        maximum: float,
        x0: float,
        x1: float,
    ) -> float:
        if maximum <= minimum:
            return (
                x0 + x1
            ) / 2.0

        ratio = (
            value - minimum
        ) / (
            maximum - minimum
        )

        return (
            x0
            + ratio
            * (
                x1 - x0
            )
        )

    def _short_label(
        self,
        value: str,
        maximum: int,
    ) -> str:
        cleaned = " ".join(
            str(
                value
                or ""
            ).split()
        )

        if len(cleaned) <= maximum:
            return cleaned

        return (
            cleaned[
                : maximum - 1
            ]
            + "…"
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