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


class CustomCoverPage:
    """
    Primeira página do relatório personalizado.

    Estrutura flexível para processos que não pertencem aos
    templates técnicos específicos do METRA.

    Exibe:
    - identificação do processo;
    - peça;
    - cliente;
    - equipamento;
    - descrição / escopo;
    - imagem principal;
    - resumo dos dados disponíveis.
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

    SECTION_TITLE_HEIGHT = 26.0
    GAP = 10.0

    def __init__(
        self,
        *,
        base_dir: Path,
    ):
        self.base_dir = base_dir

    # =============================================================
    # RENDERIZAÇÃO
    # =============================================================

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

        self._draw_scope(
            page=page,
            layout=layout,
            render_context=render_context,
        )

        self._draw_available_data_summary(
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

        layout.ensure_space(
            height
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
            width=0.6,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 8,
                rect.x0 + 350,
                rect.y1 - 6,
            ),
            (
                "RELATÓRIO TÉCNICO\n"
                "PERSONALIZADO"
            ),
            fontsize=11.4,
            fontname="hebo",
            color=self.COLOR_NAVY,
            lineheight=1.05,
        )

        divider_x = (
            rect.x1 - 150
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
                rect.y0 + 19,
            ),
            "Relatório nº",
            fontsize=6.4,
            fontname="hebo",
            color=self.COLOR_MUTED,
        )

        page.insert_textbox(
            fitz.Rect(
                divider_x + 10,
                rect.y0 + 19,
                rect.x1 - 8,
                rect.y0 + 31,
            ),
            render_context.project.report_id,
            fontsize=8.4,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

        if render_context.section_enabled(
            "show_version"
        ):
            page.insert_textbox(
                fitz.Rect(
                    divider_x + 10,
                    rect.y0 + 31,
                    rect.x1 - 8,
                    rect.y1 - 5,
                ),
                (
                    "Versão "
                    f"{render_context.project.version or 'V1.0'}"
                ),
                fontsize=6.6,
                fontname="helv",
                color=self.COLOR_TEXT,
            )

        layout.advance(
            height + self.GAP
        )

    # =============================================================
    # PROCESSO + IMAGEM
    # =============================================================

    def _draw_process_and_image(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        block_height = 214.0

        layout.ensure_space(
            block_height
        )

        gap = 10.0

        left_width = (
            layout.geometry.content_width
            * 0.56
        )

        right_width = (
            layout.geometry.content_width
            - left_width
            - gap
        )

        start_y = (
            layout.cursor_y
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
            title="1. IDENTIFICAÇÃO DO PROCESSO",
        )

        self._draw_panel_title(
            page=page,
            rect=right_rect,
            title="IMAGEM PRINCIPAL",
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
                "Template",
                "Personalizado",
            ),
            (
                "Data de emissão",
                datetime.now().strftime(
                    "%d/%m/%Y"
                ),
            ),
        ]

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

    # =============================================================
    # ESCOPO / DESCRIÇÃO
    # =============================================================

    def _draw_scope(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        description = self._resolve_scope(
            render_context
        )

        height = self._text_block_height(
            description,
            minimum=82.0,
            maximum=145.0,
        )

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + height,
            repeated_title="ESCOPO DO RELATÓRIO",
        )

        self._draw_panel_title(
            page=page,
            rect=layout.full_width_rect(
                self.SECTION_TITLE_HEIGHT
            ),
            title="2. ESCOPO / DESCRIÇÃO",
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
            fill=self.COLOR_SURFACE,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 10,
                rect.y0 + 10,
                rect.x1 - 10,
                rect.y1 - 10,
            ),
            description,
            fontsize=6.8,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )

        layout.advance(
            height + self.GAP
        )

    # =============================================================
    # RESUMO DOS DADOS
    # =============================================================

    def _draw_available_data_summary(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        title_height = (
            self.SECTION_TITLE_HEIGHT
        )

        card_height = 64.0

        total_height = (
            title_height
            + card_height
        )

        page = layout.ensure_space(
            total_height,
            repeated_title="DADOS DISPONÍVEIS",
        )

        self._draw_panel_title(
            page=page,
            rect=layout.full_width_rect(
                title_height
            ),
            title="3. DADOS DISPONÍVEIS",
        )

        document_count = len(
            render_context.documents
        )

        image_count = len(
            render_context.images
        )

        extraction_count = len(
            render_context.extractions
        )

        characteristic_count = int(
            render_context.overall_statistics.get(
                "group_count",
                0,
            )
            or 0
        )

        indicators = [
            (
                "Documentos",
                document_count,
                "arquivos",
            ),
            (
                "Imagens",
                image_count,
                "registros",
            ),
            (
                "Extrações",
                extraction_count,
                "análises",
            ),
            (
                "Características",
                characteristic_count,
                "estruturadas",
            ),
        ]

        gap = 8.0

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

        for index, (
            label,
            value,
            helper,
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
                start_y,
                x + card_width,
                start_y + card_height,
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=self.COLOR_LIGHT_BLUE,
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 7,
                    rect.x1 - 4,
                    rect.y0 + 20,
                ),
                label,
                fontsize=5.6,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 24,
                    rect.x1 - 4,
                    rect.y0 + 43,
                ),
                str(value),
                fontsize=11.0,
                fontname="hebo",
                color=self.COLOR_NAVY,
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
                color=self.COLOR_BLUE,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            total_height
        )

    # =============================================================
    # ELEMENTOS VISUAIS
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
            fontsize=7.2,
            fontname="hebo",
            color=(
                1,
                1,
                1,
            ),
        )

    def _draw_identification_rows(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        rows: list[
            tuple[str, Any]
        ],
    ) -> None:
        row_height = (
            rect.height
            / len(rows)
        )

        label_width = (
            rect.width
            * 0.37
        )

        for index, (
            label,
            value,
        ) in enumerate(rows):
            row_y = (
                rect.y0
                + index
                * row_height
            )

            row_rect = fitz.Rect(
                rect.x0,
                row_y,
                rect.x1,
                row_y + row_height,
            )

            fill = (
                self.COLOR_SURFACE
                if index % 2 == 0
                else (
                    1,
                    1,
                    1,
                )
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
                    + label_width,
                    row_rect.y1 - 4,
                ),
                label,
                fontsize=6.1,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    row_rect.x0
                    + label_width,
                    row_rect.y0 + 7,
                    row_rect.x1 - 8,
                    row_rect.y1 - 4,
                ),
                self._clean_text(
                    value
                ),
                fontsize=6.4,
                fontname="helv",
                color=self.COLOR_TEXT,
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

        image = (
            render_context.primary_image
        )

        if image is None:
            self._draw_image_placeholder(
                page=page,
                rect=rect,
                message=(
                    "Imagem principal não definida"
                ),
            )
            return

        image_path = (
            render_context
            .primary_report_image_path
        )

        caption = self._optional_text(
            getattr(
                image,
                "caption",
                None,
            )
        )

        caption_height = (
            28.0
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
                - 8
                if caption
                else rect.y1 - 10
            ),
        )

        if (
            image_path is not None
            and image_path.exists()
        ):
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
                    message=(
                        "Não foi possível carregar a imagem"
                    ),
                )

        else:
            self._draw_image_placeholder(
                page=page,
                rect=image_rect,
                message=(
                    "Imagem indisponível"
                ),
            )

        if caption:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y1 - caption_height,
                    rect.x1 - 8,
                    rect.y1 - 6,
                ),
                caption,
                fontsize=5.8,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
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
                rect.y0
                + rect.height / 2
                - 8,
                rect.x1 - 12,
                rect.y0
                + rect.height / 2
                + 12,
            ),
            message,
            fontsize=7.0,
            fontname="helv",
            color=self.COLOR_MUTED,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    # =============================================================
    # DADOS
    # =============================================================

    def _resolve_scope(
        self,
        render_context: ReportRenderContext,
    ) -> str:
        candidates = [
            render_context.get_context_value(
                "custom_scope"
            ),
            render_context.get_context_value(
                "report_scope"
            ),
            render_context.get_context_value(
                "inspection_objective"
            ),
            render_context.project.description,
        ]

        for value in candidates:
            if self._has_text(
                value
            ):
                return self._clean_text(
                    value
                )

        return (
            "Relatório técnico personalizado elaborado com "
            "base nas informações, documentos e evidências "
            "disponíveis no processo."
        )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

    def _text_block_height(
        self,
        value: Any,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        text = self._clean_text(
            value,
            fallback="",
        )

        estimated = (
            48.0
            + len(text)
            * 0.12
        )

        return max(
            minimum,
            min(
                maximum,
                estimated,
            ),
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

    def _has_text(
        self,
        value: Any,
    ) -> bool:
        return bool(
            str(
                value
                or ""
            ).strip()
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