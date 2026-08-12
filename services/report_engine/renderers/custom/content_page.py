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


class CustomContentPage:
    """
    Conteúdo flexível do relatório personalizado.

    Exibe somente os blocos disponíveis no processo:
    - documentos;
    - características;
    - imagens adicionais;
    - observações.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    SECTION_TITLE_HEIGHT = 28.0
    ROW_HEIGHT = 27.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        self._render_documents(
            layout=layout,
            render_context=render_context,
        )

        self._render_characteristics(
            layout=layout,
            render_context=render_context,
        )

        self._render_images(
            layout=layout,
            render_context=render_context,
        )

        self._render_observations(
            layout=layout,
            render_context=render_context,
        )

    def _render_documents(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        documents = render_context.documents

        if not documents:
            return

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT + 60.0,
            repeated_title="DOCUMENTOS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="4. DOCUMENTOS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        for index, document in enumerate(
            documents,
            start=1,
        ):
            page = layout.ensure_space(
                self.ROW_HEIGHT,
                repeated_title="DOCUMENTOS",
            )

            rect = layout.full_width_rect(
                self.ROW_HEIGHT
            )

            fill = (
                self.COLOR_SURFACE
                if index % 2 == 1
                else (1, 1, 1)
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.35,
            )

            identifier = (
                getattr(
                    document,
                    "specimen_identifier",
                    None,
                )
                or f"Documento {index}"
            )

            file_name = (
                getattr(
                    document,
                    "file_name",
                    None,
                )
                or "Arquivo"
            )

            source_type = (
                getattr(
                    document,
                    "source_type",
                    None,
                )
                or "-"
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x0 + 130,
                    rect.y1 - 4,
                ),
                self._clean_text(identifier),
                fontsize=6.0,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 135,
                    rect.y0 + 7,
                    rect.x1 - 80,
                    rect.y1 - 4,
                ),
                self._clean_text(file_name),
                fontsize=6.1,
                fontname="helv",
                color=self.COLOR_TEXT,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x1 - 75,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                self._clean_text(
                    source_type,
                    fallback="-",
                ),
                fontsize=5.8,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

            layout.advance(
                self.ROW_HEIGHT
            )

        layout.advance(
            self.GAP
        )

    def _render_characteristics(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        groups = render_context.statistical_groups

        if not groups:
            return

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT + 60.0,
            repeated_title="CARACTERÍSTICAS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="5. CARACTERÍSTICAS DISPONÍVEIS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        for index, group in enumerate(
            groups,
            start=1,
        ):
            page = layout.ensure_space(
                self.ROW_HEIGHT,
                repeated_title="CARACTERÍSTICAS",
            )

            rect = layout.full_width_rect(
                self.ROW_HEIGHT
            )

            fill = (
                self.COLOR_SURFACE
                if index % 2 == 1
                else (1, 1, 1)
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.35,
            )

            name = self._clean_text(
                getattr(
                    group,
                    "display_name",
                    None,
                ),
                fallback="Característica",
            )

            count = (
                getattr(
                    group,
                    "measurement_count",
                    None,
                )
            )

            if count is None:
                count = len(
                    getattr(
                        group,
                        "measurements",
                        [],
                    )
                    or []
                )

            status = self._group_status(
                group
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x1 - 145,
                    rect.y1 - 4,
                ),
                name,
                fontsize=6.1,
                fontname="helv",
                color=self.COLOR_TEXT,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x1 - 140,
                    rect.y0 + 7,
                    rect.x1 - 70,
                    rect.y1 - 4,
                ),
                f"{count} medição(ões)",
                fontsize=5.8,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x1 - 65,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                status,
                fontsize=5.8,
                fontname="hebo",
                color=self.COLOR_NAVY,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

            layout.advance(
                self.ROW_HEIGHT
            )

        layout.advance(
            self.GAP
        )

    def _render_images(
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

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT,
            repeated_title="IMAGENS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="6. IMAGENS ADICIONAIS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
            + self.GAP
        )

        index = 0

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

            image_height = 205.0

            block_height = (
                image_height
                + caption_height
            )

            page = layout.ensure_space(
                block_height
                + self.GAP,
                repeated_title="IMAGENS",
            )

            gap = 10.0

            if len(pair) == 1:
                rects = [
                    layout.full_width_rect(
                        block_height
                    )
                ]
            else:
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

            layout.advance(
                block_height
                + self.GAP
            )

            index += 2

    def _render_observations(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        value = (
            render_context.get_context_value(
                "custom_observations"
            )
            or render_context.get_context_value(
                "observations"
            )
        )

        if not self._has_text(
            value
        ):
            return

        height = max(
            70.0,
            min(
                150.0,
                50.0
                + len(
                    str(value)
                ) * 0.12,
            ),
        )

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT + height,
            repeated_title="OBSERVAÇÕES",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="7. OBSERVAÇÕES",
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
            fill=self.COLOR_LIGHT_BLUE,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 10,
                rect.y0 + 10,
                rect.x1 - 10,
                rect.y1 - 10,
            ),
            self._clean_text(
                value
            ),
            fontsize=6.6,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )

        layout.advance(
            height
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

    def _group_status(
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
            return "NÃO CONFORME"

        if int(
            getattr(
                group,
                "ok_count",
                0,
            )
            or 0
        ) > 0:
            return "CONFORME"

        return "—"

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