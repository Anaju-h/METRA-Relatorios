from __future__ import annotations

from typing import Any

import fitz

from services.report_engine.layout_engine import ReportLayoutEngine
from services.report_engine.report_context import ReportRenderContext


class DimensionalBatchStatisticsPage:
    """
    Resultados estatísticos por característica.

    O resumo executivo já aparece na abertura do relatório; esta seção
    apresenta apenas a análise estatística detalhada.

    O valor de "n" representa a quantidade de valores numéricos válidos
    realmente utilizados nos cálculos estatísticos da característica.
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
    TABLE_HEADER_HEIGHT = 30.0
    BASE_ROW_HEIGHT = 31.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        groups = render_context.statistical_groups

        if not groups:
            return

        show_capability = self._has_capability_indices(
            groups
        )

        self._draw_table_header(
            layout=layout,
            show_capability=show_capability,
        )

        for index, group in enumerate(groups):
            row_height = self._row_height(
                group
            )

            page = layout.ensure_space(
                row_height,
                repeated_title="RESULTADOS ESTATÍSTICOS",
            )

            if (
                layout.cursor_y
                <= layout.geometry.margin_top + 92
            ):
                self._draw_table_header(
                    layout=layout,
                    show_capability=show_capability,
                )
                page = layout.current_page

            self._draw_table_row(
                page=page,
                layout=layout,
                group=group,
                alternate=index % 2 == 0,
                show_capability=show_capability,
                row_height=row_height,
            )

            layout.advance(
                row_height
            )

        layout.advance(
            self.GAP
        )

    # =============================================================
    # CABEÇALHO
    # =============================================================

    def _draw_table_header(
        self,
        *,
        layout: ReportLayoutEngine,
        show_capability: bool,
    ) -> None:
        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + self.TABLE_HEADER_HEIGHT,
            repeated_title="RESULTADOS ESTATÍSTICOS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        headers = self._headers(
            show_capability
        )

        columns = self._columns(
            layout.geometry.content_width,
            show_capability,
        )

        for index, (
            header,
            rect,
        ) in enumerate(
            zip(
                headers,
                columns,
            )
        ):
            cell = fitz.Rect(
                layout.geometry.margin_left
                + rect.x0,
                layout.cursor_y,
                layout.geometry.margin_left
                + rect.x1,
                layout.cursor_y
                + self.TABLE_HEADER_HEIGHT,
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
                fontsize=4.9,
                fontname="hebo",
                color=(1, 1, 1),
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if index == 0
                    else fitz.TEXT_ALIGN_CENTER
                ),
                lineheight=1.02,
            )

        layout.advance(
            self.TABLE_HEADER_HEIGHT
        )

    # =============================================================
    # LINHAS
    # =============================================================

    def _draw_table_row(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        group: Any,
        alternate: bool,
        show_capability: bool,
        row_height: float,
    ) -> None:
        values = self._row_values(
            group,
            show_capability,
        )

        columns = self._columns(
            layout.geometry.content_width,
            show_capability,
        )

        base_fill = (
            self.COLOR_SURFACE
            if alternate
            else (1, 1, 1)
        )

        status_column = (
            len(values) - 1
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
                layout.geometry.margin_left
                + rect.x0,
                layout.cursor_y,
                layout.geometry.margin_left
                + rect.x1,
                layout.cursor_y
                + row_height,
            )

            fill = base_fill
            color = self.COLOR_TEXT
            font = "helv"

            if index == status_column:
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
                    cell.y0 + 7,
                    cell.x1 - 3,
                    cell.y1 - 4,
                ),
                value,
                fontsize=(
                    5.0
                    if index == 0
                    else 4.9
                ),
                fontname=font,
                color=color,
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if index == 0
                    else fitz.TEXT_ALIGN_CENTER
                ),
                lineheight=1.05,
            )

    def _row_values(
        self,
        group: Any,
        show_capability: bool,
    ) -> list[str]:
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
                self._numeric_count(
                    group
                )
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
                self._std_dev(
                    group
                )
            ),
        ]

        if show_capability:
            values.extend(
                [
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
                ]
            )

        values.append(
            self._status_label(
                group
            )
        )

        return values

    def _numeric_count(
        self,
        group: Any,
    ) -> int:
        """
        O ReportStatisticsService preenche valid_numeric_count.
        measurement_count não faz parte do modelo estatístico do grupo.
        """
        valid_numeric_count = getattr(
            group,
            "valid_numeric_count",
            None,
        )

        if valid_numeric_count is not None:
            try:
                return int(
                    valid_numeric_count
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

        measurements = (
            getattr(
                group,
                "measurements",
                [],
            )
            or []
        )

        return sum(
            1
            for measurement in measurements
            if getattr(
                measurement,
                "measured_value",
                None,
            )
            is not None
        )

    # =============================================================
    # ESTRUTURA DA TABELA
    # =============================================================

    def _headers(
        self,
        show_capability: bool,
    ) -> list[str]:
        headers = [
            "Característica",
            "n",
            "Nominal",
            "Mín.",
            "Máx.",
            "Média",
            "Desv. padrão",
        ]

        if show_capability:
            headers.extend(
                [
                    "Cp",
                    "Cpk",
                ]
            )

        headers.append(
            "Status"
        )

        return headers

    def _columns(
        self,
        content_width: float,
        show_capability: bool,
    ) -> list[fitz.Rect]:
        ratios = (
            [
                0.30,
                0.06,
                0.10,
                0.10,
                0.10,
                0.10,
                0.11,
                0.06,
                0.06,
                0.11,
            ]
            if show_capability
            else [
                0.34,
                0.07,
                0.12,
                0.11,
                0.11,
                0.12,
                0.13,
                0.10,
            ]
        )

        total = sum(
            ratios
        )

        x = 0.0
        columns: list[fitz.Rect] = []

        for ratio in ratios:
            width = (
                content_width
                * ratio
                / total
            )

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

    def _row_height(
        self,
        group: Any,
    ) -> float:
        name = self._clean_text(
            getattr(
                group,
                "display_name",
                None,
            ),
            fallback="Característica",
        )

        lines = max(
            1,
            (
                len(name) + 35
            )
            // 36,
        )

        return min(
            58.0,
            max(
                self.BASE_ROW_HEIGHT,
                20.0
                + lines * 9.0,
            ),
        )

    def _has_capability_indices(
        self,
        groups: list[Any],
    ) -> bool:
        return any(
            getattr(
                group,
                "cp",
                None,
            )
            is not None
            or getattr(
                group,
                "cpk",
                None,
            )
            is not None
            for group in groups
        )

    # =============================================================
    # TÍTULO E STATUS
    # =============================================================

    def _draw_section_title(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
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
            "4. RESULTADOS ESTATÍSTICOS POR CARACTERÍSTICA",
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

        return (
            value
            if value is not None
            else getattr(
                group,
                "std_dev",
                None,
            )
        )

    def _format_number(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            return (
                f"{float(value):.4f}"
                .replace(
                    ".",
                    ",",
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return self._clean_text(
                value,
                fallback="—",
            )

    def _format_index(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            return (
                f"{float(value):.2f}"
                .replace(
                    ".",
                    ",",
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return "—"

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

        return (
            cleaned
            or fallback
        )