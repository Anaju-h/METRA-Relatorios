from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class DimensionalBatchCoverPage:
    """
    Primeira página do relatório dimensional em lote.

    Diretrizes:
    - identifica claramente o lote;
    - prioriza a imagem principal sem desperdiçar espaço;
    - adapta os indicadores à existência ou não de avaliação;
    - não expõe mensagens internas de diagnóstico ao cliente;
    - respeita a opção de exibir ou ocultar a versão.
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

        self._draw_process_and_image(
            page=page,
            layout=layout,
            render_context=render_context,
        )

        self._draw_batch_summary(
            page=page,
            layout=layout,
            render_context=render_context,
        )

        self._draw_global_result(
            page=page,
            layout=layout,
            render_context=render_context,
        )

    # =============================================================
    # IDENTIDADE
    # =============================================================

    def _draw_report_identity(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        height = 50.0
        layout.ensure_space(height)

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
                    rect.y0 + 34,
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
    # IDENTIFICAÇÃO + IMAGEM
    # =============================================================

    def _draw_process_and_image(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        unit_count = self._resolve_unit_count(
            render_context
        )

        rows = [
            (
                "Processo",
                render_context.project.name,
            ),
            (
                "Peça / modelo",
                render_context.project.part_name,
            ),
            (
                "Código da peça",
                render_context.project.part_code,
            ),
            (
                "Cliente",
                render_context.project.client,
            ),
            (
                "Equipamento",
                render_context.project.equipment,
            ),
            (
                "Quantidade medida",
                f"{unit_count} unidade(s)",
            ),
            (
                "Data de emissão",
                datetime.now().strftime(
                    "%d/%m/%Y"
                ),
            ),
        ]

        row_heights = self._calculate_row_heights(
            rows=rows,
            available_width=(
                layout.geometry.content_width
                * 0.42
            ),
        )

        content_height = max(
            218.0,
            sum(row_heights),
        )

        block_height = (
            self.SECTION_TITLE_HEIGHT
            + content_height
        )

        page = layout.ensure_space(
            block_height,
            repeated_title="IDENTIFICAÇÃO DO LOTE",
        )

        gap = 12.0

        left_width = (
            layout.geometry.content_width
            * 0.43
        )

        right_width = (
            layout.geometry.content_width
            - left_width
            - gap
        )

        start_y = layout.cursor_y

        left_rect = fitz.Rect(
            layout.geometry.margin_left,
            start_y,
            layout.geometry.margin_left + left_width,
            start_y + block_height,
        )

        right_rect = fitz.Rect(
            left_rect.x1 + gap,
            start_y,
            left_rect.x1 + gap + right_width,
            start_y + block_height,
        )

        self._draw_panel_title(
            page=page,
            rect=left_rect,
            title="1. IDENTIFICAÇÃO DO LOTE",
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
                left_rect.y0 + self.SECTION_TITLE_HEIGHT,
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
                right_rect.y0 + self.SECTION_TITLE_HEIGHT,
                right_rect.x1,
                right_rect.y1,
            ),
            render_context=render_context,
        )

        layout.advance(
            block_height + self.GAP
        )

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
            rect.y0 + self.SECTION_TITLE_HEIGHT,
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

    def _draw_identification_rows(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        rows: list[tuple[str, Any]],
        row_heights: list[float],
    ) -> None:
        label_width = rect.width * 0.37
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
                    row_rect.x0 + label_width - 4,
                    row_rect.y1 - 5,
                ),
                label,
                fontsize=6.0,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    row_rect.x0 + label_width,
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
            self._draw_image_placeholder(
                page=page,
                rect=rect,
                message="Imagem principal não definida",
            )
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

        caption_height = 0.0

        if caption:
            caption_height = (
                27.0
                if len(caption) <= 70
                else 38.0
            )

        image_rect = fitz.Rect(
            rect.x0 + 10,
            rect.y0 + 10,
            rect.x1 - 10,
            (
                rect.y1
                - caption_height
                - 8
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
                    message="Não foi possível carregar a imagem",
                )
        else:
            self._draw_image_placeholder(
                page=page,
                rect=image_rect,
                message="Arquivo da imagem não encontrado",
            )

        if caption:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 10,
                    rect.y1 - caption_height,
                    rect.x1 - 10,
                    rect.y1 - 6,
                ),
                caption,
                fontsize=5.6,
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
        message: str,
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
                rect.y0 + rect.height / 2 - 8,
                rect.x1 - 12,
                rect.y0 + rect.height / 2 + 12,
            ),
            message,
            fontsize=7.0,
            fontname="helv",
            color=self.COLOR_MUTED,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    # =============================================================
    # RESUMO DO LOTE
    # =============================================================

    def _draw_batch_summary(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        title_height = self.SECTION_TITLE_HEIGHT
        card_height = 66.0
        total_height = title_height + card_height

        page = layout.ensure_space(
            total_height,
            repeated_title="RESUMO DO LOTE",
        )

        title_rect = layout.full_width_rect(
            title_height
        )

        self._draw_panel_title(
            page=page,
            rect=title_rect,
            title="2. RESUMO ESTATÍSTICO DO LOTE",
        )

        summary = render_context.overall_statistics

        evaluated_count = int(
            summary.get(
                "evaluated_count",
                0,
            )
            or 0
        )

        base_indicators = [
            (
                "Unidades",
                self._resolve_unit_count(
                    render_context
                ),
                "medidas",
                self.COLOR_LIGHT_BLUE,
                self.COLOR_NAVY,
            ),
            (
                "Características",
                summary.get(
                    "group_count",
                    0,
                ),
                "analisadas",
                self.COLOR_LIGHT_BLUE,
                self.COLOR_NAVY,
            ),
            (
                "Resultados",
                summary.get(
                    "measurement_count",
                    0,
                ),
                "medidos",
                self.COLOR_LIGHT_BLUE,
                self.COLOR_NAVY,
            ),
        ]

        if evaluated_count > 0:
            indicators = base_indicators + [
                (
                    "Conformes",
                    summary.get(
                        "ok_count",
                        0,
                    ),
                    self._percentage_text(
                        summary.get(
                            "ok_count",
                            0,
                        ),
                        evaluated_count,
                    ),
                    self.COLOR_OK_BG,
                    self.COLOR_OK,
                ),
                (
                    "Não conformes",
                    summary.get(
                        "nok_count",
                        0,
                    ),
                    self._percentage_text(
                        summary.get(
                            "nok_count",
                            0,
                        ),
                        evaluated_count,
                    ),
                    self.COLOR_NOK_BG,
                    self.COLOR_NOK,
                ),
                (
                    "Conformidade",
                    (
                        f"{float(summary.get('conformity_percentage', 0.0) or 0.0):.1f}%"
                    ),
                    "dos avaliados",
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
            ]
        else:
            indicators = base_indicators + [
                (
                    "Documentos",
                    len(
                        render_context.documents
                    ),
                    "de origem",
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                ),
            ]

        gap = 6.0

        card_width = (
            layout.geometry.content_width
            - gap * (
                len(indicators) - 1
            )
        ) / len(indicators)

        start_y = layout.cursor_y + title_height

        for index, (
            label,
            value,
            helper,
            background,
            accent,
        ) in enumerate(indicators):
            x = (
                layout.geometry.margin_left
                + index * (
                    card_width + gap
                )
            )

            rect = fitz.Rect(
                x,
                start_y,
                x + card_width,
                start_y + card_height,
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
                    rect.y0 + 18,
                ),
                label,
                fontsize=5.4,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 23,
                    rect.x1 - 4,
                    rect.y0 + 43,
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
                    rect.y0 + 45,
                    rect.x1 - 4,
                    rect.y1 - 5,
                ),
                helper,
                fontsize=5.2,
                fontname="helv",
                color=accent,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            total_height + self.GAP
        )

    # =============================================================
    # RESULTADO DO LOTE
    # =============================================================

    def _draw_global_result(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        summary = render_context.overall_statistics

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
                "RESULTADO DO LOTE: "
                "NÃO CONFORMIDADES IDENTIFICADAS"
            )

            message = (
                f"Foram identificados {nok_count} resultado(s) "
                "fora dos limites especificados no conjunto analisado."
            )

            border = self.COLOR_NOK
            background = self.COLOR_NOK_BG

        elif (
            evaluated_count > 0
            and unknown_count == 0
        ):
            title = (
                "RESULTADO DO LOTE: CONFORME"
            )

            message = (
                "Todos os resultados avaliados encontram-se "
                "dentro dos limites especificados."
            )

            border = self.COLOR_OK
            background = self.COLOR_OK_BG

        else:
            return

        height = self._estimate_text_height(
            message,
            minimum=56.0,
            maximum=82.0,
        )

        page = layout.ensure_space(
            height,
            repeated_title="RESULTADO DO LOTE",
        )

        rect = layout.full_width_rect(
            height
        )

        page.draw_rect(
            rect,
            color=border,
            fill=background,
            width=0.8,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 8,
                rect.x1 - 12,
                rect.y0 + 23,
            ),
            title,
            fontsize=7.5,
            fontname="hebo",
            color=border,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 27,
                rect.x1 - 12,
                rect.y1 - 7,
            ),
            message,
            fontsize=6.6,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.12,
        )

        layout.advance(
            height
        )

    # =============================================================
    # HELPERS
    # =============================================================

    def _resolve_unit_count(
        self,
        render_context: ReportRenderContext,
    ) -> int:
        summary = render_context.overall_statistics

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
            available_width * 0.58,
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
                        31.0,
                        17.0 + line_count * 9.0,
                    ),
                )
            )

        return heights

    def _estimate_text_height(
        self,
        text: Any,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        cleaned = self._clean_text(
            text,
            fallback="",
        )

        line_count = max(
            1,
            (
                len(cleaned) + 92
            )
            // 93,
        )

        return max(
            minimum,
            min(
                maximum,
                42.0 + line_count * 10.0,
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
            cleaned or fallback
        )