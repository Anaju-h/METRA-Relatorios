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


class DimensionalBatchChartsPage:
    """
    Análise gráfica do relatório dimensional em lote.

    O módulo apenas apresenta gráficos já gerados pelo serviço.
    Mensagens internas de ausência/erro não são impressas no PDF do cliente.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    SECTION_TITLE_HEIGHT = 28.0
    CHART_TITLE_HEIGHT = 31.0
    CHART_HEIGHT_MEDIUM = 198.0
    CHART_HEIGHT_SMALL = 170.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        blocks = self._collect_chart_blocks(
            render_context
        )

        if not blocks:
            return

        self._draw_page_title(
            layout=layout,
        )

        for block in blocks:
            self._draw_chart_block(
                layout=layout,
                block=block,
            )

    # =============================================================
    # COLETA
    # =============================================================

    def _collect_chart_blocks(
        self,
        render_context: ReportRenderContext,
    ) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []

        charts = (
            render_context.charts
            or {}
        )

        groups = (
            render_context.statistical_groups
        )

        overall = (
            render_context.overall_statistics
        )

        evaluated_count = int(
            overall.get(
                "evaluated_count",
                0,
            )
            or 0
        )

        groups_with_results = [
            group
            for group in groups
            if int(
                getattr(
                    group,
                    "valid_numeric_count",
                    0,
                )
                or 0
            ) > 0
        ]

        overall_path = self._as_existing_path(
            charts.get(
                "overall_conformity"
            )
        )

        if (
            overall_path is not None
            and evaluated_count > 0
        ):
            blocks.append(
                {
                    "title": "Conformidade geral do lote",
                    "description": (
                        "Distribuição consolidada dos resultados "
                        "avaliados no conjunto."
                    ),
                    "path": overall_path,
                    "height": self.CHART_HEIGHT_SMALL,
                }
            )

        group_summary_path = self._as_existing_path(
            charts.get(
                "group_summary"
            )
        )

        if (
            group_summary_path is not None
            and len(groups_with_results) >= 2
        ):
            blocks.append(
                {
                    "title": "Comparação por característica",
                    "description": (
                        "Visão comparativa das características "
                        "dimensionais do lote."
                    ),
                    "path": group_summary_path,
                    "height": self.CHART_HEIGHT_MEDIUM,
                }
            )

        characteristic_charts = (
            charts.get(
                "characteristic_charts",
                [],
            )
            or []
        )

        for item in characteristic_charts:
            group = item.get(
                "group"
            )

            path = self._as_existing_path(
                item.get(
                    "path"
                )
            )

            if (
                group is None
                or path is None
            ):
                continue

            measurement_count = len(
                getattr(
                    group,
                    "measurements",
                    [],
                )
                or []
            )

            if measurement_count < 3:
                continue

            blocks.append(
                {
                    "title": self._clean_text(
                        getattr(
                            group,
                            "display_name",
                            None,
                        ),
                        fallback="Análise por característica",
                    ),
                    "description": self._characteristic_description(
                        group
                    ),
                    "path": path,
                    "height": self.CHART_HEIGHT_MEDIUM,
                }
            )

        return blocks

    # =============================================================
    # DESENHO
    # =============================================================

    def _draw_page_title(
        self,
        *,
        layout: ReportLayoutEngine,
    ) -> None:
        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT,
            repeated_title="ANÁLISE GRÁFICA",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="5. ANÁLISE GRÁFICA DO LOTE",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT + self.GAP
        )

    def _draw_chart_block(
        self,
        *,
        layout: ReportLayoutEngine,
        block: dict[str, Any],
    ) -> None:
        chart_height = float(
            block.get(
                "height",
                self.CHART_HEIGHT_MEDIUM,
            )
        )

        total_height = (
            self.CHART_TITLE_HEIGHT
            + chart_height
            + self.GAP
        )

        page = layout.ensure_space(
            total_height,
            repeated_title="ANÁLISE GRÁFICA",
        )

        if (
            layout.cursor_y
            <= layout.geometry.margin_top + 92
        ):
            self._draw_section_title(
                page=page,
                layout=layout,
                title="5. ANÁLISE GRÁFICA DO LOTE",
            )

            layout.advance(
                self.SECTION_TITLE_HEIGHT + self.GAP
            )

        self._draw_chart_heading(
            page=page,
            layout=layout,
            title=self._clean_text(
                block.get(
                    "title"
                ),
                fallback="Análise gráfica",
            ),
            description=self._clean_text(
                block.get(
                    "description"
                ),
                fallback="",
            ),
        )

        layout.advance(
            self.CHART_TITLE_HEIGHT
        )

        chart_rect = layout.full_width_rect(
            chart_height
        )

        page.draw_rect(
            chart_rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.5,
        )

        try:
            page.insert_image(
                fitz.Rect(
                    chart_rect.x0 + 10,
                    chart_rect.y0 + 10,
                    chart_rect.x1 - 10,
                    chart_rect.y1 - 10,
                ),
                filename=str(
                    block["path"]
                ),
                keep_proportion=True,
            )
        except Exception:
            return

        layout.advance(
            chart_height + self.GAP
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
            self.CHART_TITLE_HEIGHT
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.4,
        )

        title_width = rect.width * 0.42

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 8,
                rect.y0 + 7,
                rect.x0 + title_width,
                rect.y1 - 4,
            ),
            title,
            fontsize=6.4,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

        if description:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + title_width + 6,
                    rect.y0 + 6,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                description,
                fontsize=5.2,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_RIGHT,
                lineheight=1.05,
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

    # =============================================================
    # HELPERS
    # =============================================================

    def _as_existing_path(
        self,
        value: Any,
    ) -> Path | None:
        if not value:
            return None

        try:
            path = Path(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        if (
            not path.exists()
            or not path.is_file()
        ):
            return None

        return path

    def _characteristic_description(
        self,
        group: Any,
    ) -> str:
        count = len(
            getattr(
                group,
                "measurements",
                [],
            )
            or []
        )

        parts = [
            f"{count} medições"
        ]

        mean = getattr(
            group,
            "mean",
            None,
        )

        if mean is not None:
            parts.append(
                "média "
                f"{self._format_number(mean)}"
            )

        standard_deviation = getattr(
            group,
            "standard_deviation",
            None,
        )

        if standard_deviation is not None:
            parts.append(
                "desvio padrão "
                f"{self._format_number(standard_deviation)}"
            )

        return " · ".join(
            parts
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
            return "—"

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
                value or ""
            ).split()
        )

        return cleaned or fallback