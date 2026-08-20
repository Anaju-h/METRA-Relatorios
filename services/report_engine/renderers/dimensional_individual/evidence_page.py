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


class DimensionalIndividualEvidencePage:
    """
    Evidências técnicas do relatório dimensional individual.

    Regras:
    - usa as imagens adicionais do processo;
    - incorpora marcações salvas por meio do ReportRenderContext;
    - preserva a ordem definida pelo usuário;
    - exibe legenda somente quando houver caption;
    - nunca usa o nome físico do arquivo como legenda;
    - uma imagem isolada aproveita a largura total;
    - duas imagens são organizadas lado a lado.
    """

    COLOR_NAVY = (
        0.025,
        0.110,
        0.215,
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

    SECTION_TITLE_HEIGHT = 28.0
    IMAGE_HEIGHT = 205.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        prepared_images = (
            render_context
            .get_additional_report_images()
        )

        if not prepared_images:
            return

        index = 0
        title_drawn = False

        while index < len(
            prepared_images
        ):
            pair = prepared_images[
                index:index + 2
            ]

            captions = [
                self._optional_text(
                    getattr(
                        image,
                        "caption",
                        None,
                    )
                )
                for image, _ in pair
            ]

            caption_height = max(
                (
                    self._estimate_caption_height(
                        caption
                    )
                    if caption
                    else 0.0
                )
                for caption in captions
            )

            block_height = (
                self.IMAGE_HEIGHT
                + caption_height
            )

            if not title_drawn:
                # Mantém o título 7 junto do primeiro bloco de evidências.
                # Se título + conteúdo couberem no espaço restante, ficam
                # na página atual; caso contrário, ambos migram juntos.
                page = layout.ensure_space(
                    self.SECTION_TITLE_HEIGHT
                    + self.GAP
                    + block_height
                    + self.GAP,
                    repeated_title="EVIDÊNCIAS TÉCNICAS",
                )

                self._draw_section_title(
                    layout=layout,
                )
                title_drawn = True

                page = layout.current_page

            else:
                page = layout.ensure_space(
                    block_height + self.GAP,
                    repeated_title="EVIDÊNCIAS TÉCNICAS",
                )

            if len(pair) == 1:
                rects = [
                    layout.full_width_rect(
                        block_height
                    )
                ]

            else:
                gap = 10.0

                card_width = (
                    layout.geometry.content_width
                    - gap
                ) / 2.0

                y = layout.cursor_y

                rects = [
                    fitz.Rect(
                        layout.geometry.margin_left,
                        y,
                        layout.geometry.margin_left
                        + card_width,
                        y + block_height,
                    ),
                    fitz.Rect(
                        layout.geometry.margin_left
                        + card_width
                        + gap,
                        y,
                        layout.geometry.margin_left
                        + 2 * card_width
                        + gap,
                        y + block_height,
                    ),
                ]

            for (
                image,
                image_path,
            ), caption, rect in zip(
                pair,
                captions,
                rects,
            ):
                self._draw_image_block(
                    page=page,
                    rect=rect,
                    image_path=image_path,
                    caption=caption,
                    caption_height=caption_height,
                )

            layout.advance(
                block_height
                + self.GAP
            )

            index += 2

    # =============================================================
    # TÍTULO
    # =============================================================

    def _draw_section_title(
        self,
        *,
        layout: ReportLayoutEngine,
    ) -> None:
        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT,
            repeated_title="EVIDÊNCIAS TÉCNICAS",
        )

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
            "7. EVIDÊNCIAS TÉCNICAS",
            fontsize=7.3,
            fontname="hebo",
            color=(
                1,
                1,
                1,
            ),
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
            + self.GAP
        )

    # =============================================================
    # IMAGEM
    # =============================================================

    def _draw_image_block(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        image_path: Path,
        caption: str | None,
        caption_height: float,
    ) -> None:
        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_SURFACE,
            width=0.5,
        )

        image_rect = fitz.Rect(
            rect.x0 + 9,
            rect.y0 + 9,
            rect.x1 - 9,
            (
                rect.y1
                - caption_height
                - 8
                if caption
                else rect.y1 - 9
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
                pass

        if caption:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 9,
                    rect.y1
                    - caption_height,
                    rect.x1 - 9,
                    rect.y1 - 6,
                ),
                caption,
                fontsize=5.8,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
                lineheight=1.10,
            )

    # =============================================================
    # HELPERS
    # =============================================================

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
                len(text)
                + 65
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