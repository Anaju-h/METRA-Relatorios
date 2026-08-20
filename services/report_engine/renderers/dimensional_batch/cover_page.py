from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import fitz

from services.report_engine.layout_engine import ReportLayoutEngine
from services.report_engine.report_context import ReportRenderContext


class DimensionalBatchCoverPage:
    """
    Página de abertura do relatório dimensional em lote.

    A abertura deve responder rapidamente:
    - qual processo está sendo apresentado;
    - qual peça foi avaliada;
    - qual o tamanho da amostra;
    - quantos resultados foram obtidos;
    - qual a situação geral dos resultados avaliados.

    Nenhuma conclusão técnica é apresentada nesta etapa.
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
    COLOR_NOK_BG = (0.995, 0.955, 0.945)

    SECTION_TITLE_HEIGHT = 26.0
    GAP = 10.0

    def __init__(
        self,
        *,
        base_dir: Path,
    ):
        self.base_dir = base_dir

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        page = layout.ensure_page()

        self._draw_report_identity(
            page=page,
            layout=layout,
            render_context=render_context,
        )

        self._draw_process_overview(
            page=page,
            layout=layout,
            render_context=render_context,
        )

        self._draw_batch_summary(
            layout=layout,
            render_context=render_context,
        )

    # =============================================================
    # IDENTIDADE DO RELATÓRIO
    # =============================================================

    def _draw_report_identity(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        height = 54.0

        page = layout.ensure_space(height)

        rect = layout.full_width_rect(height)

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.6,
        )

        divider_x = rect.x1 - 154.0

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 8,
                divider_x - 10,
                rect.y1 - 6,
            ),
            (
                "RELATÓRIO ESTATÍSTICO\n"
                "DE INSPEÇÃO DIMENSIONAL EM LOTE"
            ),
            fontsize=11.0,
            fontname="hebo",
            color=self.COLOR_NAVY,
            lineheight=1.05,
        )

        page.draw_line(
            fitz.Point(
                divider_x,
                rect.y0 + 7,
            ),
            fitz.Point(
                divider_x,
                rect.y1 - 7,
            ),
            color=self.COLOR_BORDER,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                divider_x + 10,
                rect.y0 + 7,
                rect.x1 - 8,
                rect.y0 + 18,
            ),
            "Relatório nº",
            fontsize=6.0,
            fontname="hebo",
            color=self.COLOR_MUTED,
        )

        page.insert_textbox(
            fitz.Rect(
                divider_x + 10,
                rect.y0 + 18,
                rect.x1 - 8,
                rect.y0 + 32,
            ),
            self._clean_text(
                render_context.project.report_id
            ),
            fontsize=8.0,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

        if render_context.section_enabled(
            "show_version"
        ):
            page.insert_textbox(
                fitz.Rect(
                    divider_x + 10,
                    rect.y0 + 35,
                    rect.x1 - 8,
                    rect.y1 - 5,
                ),
                (
                    "Versão "
                    f"{render_context.project.version or 'V1.0'}"
                ),
                fontsize=6.2,
                fontname="helv",
                color=self.COLOR_TEXT,
            )

        layout.advance(
            height + self.GAP
        )

    # =============================================================
    # VISÃO GERAL
    # =============================================================

    def _draw_process_overview(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        rows = self._build_overview_rows(
            render_context
        )

        has_image = (
            render_context.primary_image
            is not None
        )

        if has_image:
            left_width_ratio = 0.45
        else:
            left_width_ratio = 1.0

        available_width = (
            layout.geometry.content_width
            * left_width_ratio
        )

        row_heights = self._calculate_row_heights(
            rows=rows,
            available_width=available_width,
        )

        content_height = max(
            190.0 if has_image else 0.0,
            sum(row_heights),
        )

        block_height = (
            self.SECTION_TITLE_HEIGHT
            + content_height
        )

        page = layout.ensure_space(
            block_height,
            repeated_title="RESUMO DO PROCESSO",
        )

        start_y = layout.cursor_y

        if not has_image:
            full_rect = fitz.Rect(
                layout.geometry.margin_left,
                start_y,
                layout.geometry.margin_left
                + layout.geometry.content_width,
                start_y + block_height,
            )

            self._draw_panel_title(
                page=page,
                rect=full_rect,
                title="1. RESUMO DO PROCESSO",
            )

            self._draw_identification_rows(
                page=page,
                rect=fitz.Rect(
                    full_rect.x0,
                    full_rect.y0
                    + self.SECTION_TITLE_HEIGHT,
                    full_rect.x1,
                    full_rect.y1,
                ),
                rows=rows,
                row_heights=row_heights,
            )

        else:
            gap = 12.0

            left_width = (
                layout.geometry.content_width
                * left_width_ratio
            )

            right_width = (
                layout.geometry.content_width
                - left_width
                - gap
            )

            left_rect = fitz.Rect(
                layout.geometry.margin_left,
                start_y,
                layout.geometry.margin_left
                + left_width,
                start_y + block_height,
            )

            right_rect = fitz.Rect(
                left_rect.x1 + gap,
                start_y,
                left_rect.x1
                + gap
                + right_width,
                start_y + block_height,
            )

            self._draw_panel_title(
                page=page,
                rect=left_rect,
                title="1. RESUMO DO PROCESSO",
            )

            self._draw_panel_title(
                page=page,
                rect=right_rect,
                title="VISÃO GERAL DA PEÇA",
            )

            self._draw_identification_rows(
                page=page,
                rect=fitz.Rect(
                    left_rect.x0,
                    left_rect.y0
                    + self.SECTION_TITLE_HEIGHT,
                    left_rect.x1,
                    left_rect.y1,
                ),
                rows=rows,
                row_heights=row_heights,
            )

            self._draw_primary_image(
                page=page,
                rect=fitz.Rect(
                    right_rect.x0,
                    right_rect.y0
                    + self.SECTION_TITLE_HEIGHT,
                    right_rect.x1,
                    right_rect.y1,
                ),
                render_context=render_context,
            )

        layout.advance(
            block_height + self.GAP
        )

    def _build_overview_rows(
        self,
        render_context: ReportRenderContext,
    ) -> list[tuple[str, Any]]:
        project = render_context.project

        candidates = [
            (
                "Processo",
                project.name,
                True,
            ),
            (
                "Peça / modelo",
                project.part_name,
                True,
            ),
            (
                "Código da peça",
                project.part_code,
                False,
            ),
            (
                "Cliente",
                project.client,
                False,
            ),
            (
                "Equipamento",
                project.equipment,
                False,
            ),
            (
                "Data de emissão",
                datetime.now().strftime(
                    "%d/%m/%Y"
                ),
                True,
            ),
        ]

        rows: list[tuple[str, Any]] = []

        for label, value, always_show in candidates:
            cleaned = self._optional_text(
                value
            )

            if (
                cleaned is not None
                or always_show
            ):
                rows.append(
                    (
                        label,
                        cleaned
                        or "Não informado",
                    )
                )

        return rows

    # =============================================================
    # TÍTULOS DOS PAINÉIS
    # =============================================================

    def _draw_panel_title(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        title: str,
    ) -> None:
        title_rect = fitz.Rect(
            rect.x0,
            rect.y0,
            rect.x1,
            rect.y0
            + self.SECTION_TITLE_HEIGHT,
        )

        page.draw_rect(
            title_rect,
            color=self.COLOR_NAVY,
            fill=self.COLOR_NAVY,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                title_rect.x0 + 9,
                title_rect.y0 + 6,
                title_rect.x1 - 9,
                title_rect.y1 - 3,
            ),
            title,
            fontsize=7.1,
            fontname="hebo",
            color=(1, 1, 1),
        )

    # =============================================================
    # IDENTIFICAÇÃO
    # =============================================================

    def _draw_identification_rows(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        rows: list[tuple[str, Any]],
        row_heights: list[float],
    ) -> None:
        label_width = (
            rect.width * 0.34
        )

        y = rect.y0

        for index, (
            label,
            value,
        ) in enumerate(rows):
            height = row_heights[index]

            row_rect = fitz.Rect(
                rect.x0,
                y,
                rect.x1,
                y + height,
            )

            fill = (
                self.COLOR_SURFACE
                if index % 2 == 0
                else (1, 1, 1)
            )

            page.draw_rect(
                row_rect,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.35,
            )

            page.insert_textbox(
                fitz.Rect(
                    row_rect.x0 + 8,
                    row_rect.y0 + 7,
                    row_rect.x0
                    + label_width
                    - 4,
                    row_rect.y1 - 5,
                ),
                label,
                fontsize=6.0,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    row_rect.x0
                    + label_width,
                    row_rect.y0 + 7,
                    row_rect.x1 - 8,
                    row_rect.y1 - 5,
                ),
                self._clean_text(
                    value
                ),
                fontsize=6.2,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.12,
            )

            y += height

        if y < rect.y1:
            page.draw_rect(
                fitz.Rect(
                    rect.x0,
                    y,
                    rect.x1,
                    rect.y1,
                ),
                color=self.COLOR_BORDER,
                fill=(1, 1, 1),
                width=0.35,
            )

    # =============================================================
    # IMAGEM PRINCIPAL
    # =============================================================

    def _draw_primary_image(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        render_context: ReportRenderContext,
    ) -> None:
        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_SURFACE,
            width=0.5,
        )

        image = render_context.primary_image

        if image is None:
            return

        image_path = Path(
            str(
                getattr(
                    image,
                    "file_path",
                    "",
                )
            )
        )

        caption = self._optional_text(
            getattr(
                image,
                "caption",
                None,
            )
        )

        caption_height = (
            self._estimate_caption_height(
                caption
            )
            if caption
            else 0.0
        )

        image_rect = fitz.Rect(
            rect.x0 + 10,
            rect.y0 + 10,
            rect.x1 - 10,
            (
                rect.y1
                - caption_height
                - 7
                if caption
                else rect.y1 - 10
            ),
        )

        if image_path.exists():
            try:
                page.insert_image(
                    image_rect,
                    filename=str(
                        image_path
                    ),
                    keep_proportion=True,
                )
            except Exception:
                self._draw_image_placeholder(
                    page=page,
                    rect=image_rect,
                )
        else:
            self._draw_image_placeholder(
                page=page,
                rect=image_rect,
            )

        if caption:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 10,
                    rect.y1
                    - caption_height,
                    rect.x1 - 10,
                    rect.y1 - 5,
                ),
                caption,
                fontsize=5.8,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
                lineheight=1.10,
            )

    def _draw_image_placeholder(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
    ) -> None:
        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0
                + rect.height / 2
                - 8,
                rect.x1 - 12,
                rect.y0
                + rect.height / 2
                + 12,
            ),
            "Imagem indisponível",
            fontsize=7.0,
            fontname="helv",
            color=self.COLOR_MUTED,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    # =============================================================
    # INDICADORES
    # =============================================================

    def _draw_batch_summary(
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

        indicators = [
            {
                "label": "AMOSTRA",
                "value": self._resolve_unit_count(
                    render_context
                ),
                "helper": "UNIDADES",
                "background": self.COLOR_LIGHT_BLUE,
                "accent": self.COLOR_NAVY,
                "emphasis": True,
            },
            {
                "label": "CARACTERÍSTICAS",
                "value": summary.get(
                    "group_count",
                    0,
                ),
                "helper": "ANALISADAS",
                "background": self.COLOR_SURFACE,
                "accent": self.COLOR_NAVY,
            },
            {
                "label": "RESULTADOS",
                "value": summary.get(
                    "measurement_count",
                    0,
                ),
                "helper": "MEDIDOS",
                "background": self.COLOR_SURFACE,
                "accent": self.COLOR_NAVY,
            },
        ]

        if evaluated_count > 0:
            indicators.extend(
                [
                    {
                        "label": "CONFORMES",
                        "value": summary.get(
                            "ok_count",
                            0,
                        ),
                        "helper": self._percentage_text(
                            summary.get(
                                "ok_count",
                                0,
                            ),
                            evaluated_count,
                        ),
                        "background": self.COLOR_OK_BG,
                        "accent": self.COLOR_OK,
                    },
                    {
                        "label": "NÃO CONFORMES",
                        "value": summary.get(
                            "nok_count",
                            0,
                        ),
                        "helper": self._percentage_text(
                            summary.get(
                                "nok_count",
                                0,
                            ),
                            evaluated_count,
                        ),
                        "background": self.COLOR_NOK_BG,
                        "accent": self.COLOR_NOK,
                    },
                    {
                        "label": "CONFORMIDADE",
                        "value": (
                            f"{float(summary.get('conformity_percentage', 0.0) or 0.0):.1f}%"
                            .replace(
                                ".",
                                ",",
                            )
                        ),
                        "helper": "DOS AVALIADOS",
                        "background": self.COLOR_SURFACE,
                        "accent": self.COLOR_NAVY,
                    },
                ]
            )

        title_height = (
            self.SECTION_TITLE_HEIGHT
        )

        card_height = 72.0

        total_height = (
            title_height
            + card_height
        )

        page = layout.ensure_space(
            total_height,
            repeated_title="RESUMO DO LOTE",
        )

        title_rect = (
            layout.full_width_rect(
                title_height
            )
        )

        self._draw_panel_title(
            page=page,
            rect=title_rect,
            title="2. RESUMO DO LOTE",
        )

        gap = 6.0

        card_width = (
            layout.geometry.content_width
            - gap
            * (
                len(indicators) - 1
            )
        ) / len(indicators)

        start_y = (
            layout.cursor_y
            + title_height
        )

        for index, indicator in enumerate(
            indicators
        ):
            x = (
                layout.geometry.margin_left
                + index
                * (
                    card_width + gap
                )
            )

            rect = fitz.Rect(
                x,
                start_y,
                x + card_width,
                start_y + card_height,
            )

            emphasis = bool(
                indicator.get(
                    "emphasis",
                    False,
                )
            )

            border_width = (
                1.0
                if emphasis
                else 0.5
            )

            border_color = (
                self.COLOR_NAVY
                if emphasis
                else self.COLOR_BORDER
            )

            page.draw_rect(
                rect,
                color=border_color,
                fill=indicator[
                    "background"
                ],
                width=border_width,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 7,
                    rect.x1 - 4,
                    rect.y0 + 20,
                ),
                str(
                    indicator["label"]
                ),
                fontsize=5.4,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 22,
                    rect.x1 - 4,
                    rect.y0 + 49,
                ),
                str(
                    indicator["value"]
                ),
                fontsize=(
                    16.0
                    if emphasis
                    else 11.5
                ),
                fontname="hebo",
                color=indicator[
                    "accent"
                ],
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 51,
                    rect.x1 - 4,
                    rect.y1 - 5,
                ),
                str(
                    indicator["helper"]
                ),
                fontsize=(
                    5.8
                    if emphasis
                    else 5.2
                ),
                fontname=(
                    "hebo"
                    if emphasis
                    else "helv"
                ),
                color=indicator[
                    "accent"
                ],
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            total_height
            + self.GAP
        )

    # =============================================================
    # HELPERS
    # =============================================================

    def _resolve_unit_count(
        self,
        render_context: ReportRenderContext,
    ) -> int:
        summary = (
            render_context.overall_statistics
        )

        unit_count = int(
            summary.get(
                "unit_count",
                0,
            )
            or 0
        )

        if unit_count > 0:
            return unit_count

        document_summary = (
            render_context.document_summary
        )

        unit_count = int(
            document_summary.get(
                "unit_count",
                0,
            )
            or 0
        )

        if unit_count > 0:
            return unit_count

        return max(
            1,
            render_context.quantity,
        )

    def _calculate_row_heights(
        self,
        *,
        rows: list[tuple[str, Any]],
        available_width: float,
    ) -> list[float]:
        value_width = max(
            90.0,
            available_width * 0.64,
        )

        heights: list[float] = []

        for _, value in rows:
            text = self._clean_text(
                value
            )

            estimated_chars = max(
                15,
                int(
                    value_width / 3.15
                ),
            )

            line_count = max(
                1,
                (
                    len(text)
                    + estimated_chars
                    - 1
                )
                // estimated_chars,
            )

            heights.append(
                min(
                    50.0,
                    max(
                        30.0,
                        16.0
                        + line_count
                        * 9.0,
                    ),
                )
            )

        return heights

    def _estimate_caption_height(
        self,
        value: Any,
    ) -> float:
        text = self._optional_text(
            value
        )

        if not text:
            return 0.0

        lines = max(
            1,
            (
                len(text) + 65
            )
            // 66,
        )

        return min(
            42.0,
            max(
                24.0,
                14.0
                + lines
                * 8.0,
            ),
        )

    def _percentage_text(
        self,
        value: Any,
        total: Any,
    ) -> str:
        try:
            value_number = float(
                value or 0
            )
            total_number = float(
                total or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return "0,0%"

        if total_number <= 0:
            return "0,0%"

        return (
            f"{value_number / total_number * 100.0:.1f}%"
            .replace(
                ".",
                ",",
            )
        )

    def _optional_text(
        self,
        value: Any,
    ) -> str | None:
        cleaned = " ".join(
            str(
                value or ""
            ).split()
        )

        return (
            cleaned
            or None
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

        return (
            cleaned
            or fallback
        )