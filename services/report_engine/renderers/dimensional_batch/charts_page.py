from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

from services.report_engine.layout_engine import ReportLayoutEngine
from services.report_engine.report_context import ReportRenderContext


class DimensionalBatchChartsPage:
    """
    Análise gráfica do lote.

    A seção combina gráficos consolidados com uma seleção limitada de
    gráficos de tendência por característica.

    A seleção é feita no ReportChartService e evita duplicidade.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    SECTION_TITLE_HEIGHT = 28.0
    CHART_TITLE_HEIGHT = 38.0

    CHART_HEIGHT_LARGE = 220.0
    CHART_HEIGHT_MEDIUM = 195.0
    CHART_HEIGHT_TREND = 205.0

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
            layout=layout
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
        charts = (
            render_context.charts
            or {}
        )

        blocks: list[
            dict[str, Any]
        ] = []

        seen_paths: set[str] = set()

        consolidated_candidates = [
            {
                "title":
                    "Conformidade geral do lote",

                "description":
                    (
                        "Distribuição consolidada entre resultados "
                        "conformes, não conformes e não avaliados."
                    ),

                "path":
                    charts.get(
                        "overall_conformity"
                    ),

                "height":
                    self.CHART_HEIGHT_MEDIUM,
            },
            {
                "title":
                    "Ocorrências por característica",

                "description":
                    (
                        "Comparação da quantidade de resultados "
                        "conformes e não conformes por característica."
                    ),

                "path":
                    charts.get(
                        "group_summary"
                    ),

                "height":
                    self.CHART_HEIGHT_LARGE,
            },
            {
                "title":
                    "Desvio médio em relação ao nominal",

                "description":
                    (
                        "Comparação do afastamento médio em relação "
                        "ao nominal para características compatíveis."
                    ),

                "path":
                    charts.get(
                        "mean_deviation"
                    ),

                "height":
                    self.CHART_HEIGHT_LARGE,
            },
        ]

        for candidate in consolidated_candidates:
            self._append_unique_block(
                blocks=blocks,
                seen_paths=seen_paths,
                block=candidate,
            )

        for item in (
            charts.get(
                "characteristic_charts",
                []
            )
            or []
        ):
            if not isinstance(
                item,
                dict,
            ):
                continue

            title = self._clean_text(
                item.get(
                    "title"
                ),
                fallback="Comportamento por unidade",
            )

            description = self._clean_text(
                item.get(
                    "description"
                ),
                fallback=(
                    "Evolução dos valores medidos ao longo "
                    "das unidades do lote."
                ),
            )

            self._append_unique_block(
                blocks=blocks,
                seen_paths=seen_paths,
                block={
                    "title":
                        title,

                    "description":
                        description,

                    "path":
                        item.get(
                            "path"
                        ),

                    "height":
                        self.CHART_HEIGHT_TREND,
                },
            )

        return blocks

    def _append_unique_block(
        self,
        *,
        blocks: list[dict[str, Any]],
        seen_paths: set[str],
        block: dict[str, Any],
    ) -> None:
        path = self._as_existing_path(
            block.get(
                "path"
            )
        )

        if path is None:
            return

        key = str(
            path.resolve()
        )

        if key in seen_paths:
            return

        seen_paths.add(
            key
        )

        prepared = dict(
            block
        )

        prepared[
            "path"
        ] = path

        blocks.append(
            prepared
        )

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
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
            + self.GAP
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
            )

            layout.advance(
                self.SECTION_TITLE_HEIGHT
                + self.GAP
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
                    block[
                        "path"
                    ]
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
            self.CHART_TITLE_HEIGHT
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.4,
        )

        title_width = (
            rect.width * 0.48
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 8,
                rect.y0 + 6,
                rect.x0
                + title_width,
                rect.y1 - 5,
            ),
            title,
            fontsize=6.3,
            fontname="hebo",
            color=self.COLOR_NAVY,
            lineheight=1.04,
        )

        if description:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0
                    + title_width
                    + 8,
                    rect.y0 + 6,
                    rect.x1 - 8,
                    rect.y1 - 5,
                ),
                description,
                fontsize=5.1,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_RIGHT,
                lineheight=1.04,
            )

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
            "5. ANÁLISE GRÁFICA DO LOTE",
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