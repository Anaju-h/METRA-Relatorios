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


class AdditionalSectionsPage:
    """
    Renderiza seções técnicas adicionais compartilhadas por todos
    os templates do METRA.

    Cada seção pode conter:
    - título;
    - conteúdo textual;
    - imagens vinculadas.

    Se não houver nenhuma seção adicional, nada é renderizado.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)

    SECTION_TITLE_HEIGHT = 28.0
    GAP = 10.0

    def has_content(
        self,
        render_context: ReportRenderContext,
    ) -> bool:
        sections = (
            render_context.get_context_value(
                "custom_sections",
                [],
            )
            or []
        )

        if not isinstance(
            sections,
            list,
        ):
            return False

        return any(
            isinstance(section, dict)
            and self._section_has_content(section)
            for section in sections
        )

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        sections = (
            render_context.get_context_value(
                "custom_sections",
                [],
            )
            or []
        )

        if not isinstance(
            sections,
            list,
        ):
            return

        for section in sections:
            if not isinstance(
                section,
                dict,
            ):
                continue

            if not self._section_has_content(
                section
            ):
                continue

            self._render_section(
                layout=layout,
                render_context=render_context,
                section=section,
            )

    def _section_has_content(
        self,
        section: dict[str, Any],
    ) -> bool:
        return bool(
            self._has_text(
                section.get("title")
            )
            or self._has_text(
                section.get("content")
            )
            or section.get(
                "image_ids"
            )
        )

    def _render_section(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
        section: dict[str, Any],
    ) -> None:
        title = self._clean_text(
            section.get(
                "title"
            ),
            fallback="SEÇÃO ADICIONAL",
        ).upper()

        content = self._optional_text(
            section.get(
                "content"
            )
        )

        image_ids = {
            int(value)
            for value in section.get(
                "image_ids",
                [],
            )
            if str(value).isdigit()
        }

        prepared_images = [
            (
                image,
                image_path,
            )
            for (
                image,
                image_path,
            ) in render_context.get_report_images()
            if (
                getattr(
                    image,
                    "id",
                    None,
                )
                in image_ids
            )
        ]

        text_height = (
            self._estimate_text_height(
                content
            )
            if content
            else 0.0
        )

        first_image_height = (
            self._estimate_image_row_height(
                prepared_images[:2]
            )
            if prepared_images
            else 0.0
        )

        first_required = (
            self.SECTION_TITLE_HEIGHT
            + text_height
            + (
                self.GAP
                if text_height
                and first_image_height
                else 0.0
            )
            + first_image_height
            + self.GAP
        )

        page = layout.ensure_space(
            max(
                self.SECTION_TITLE_HEIGHT
                + 40.0,
                first_required,
            ),
            repeated_title=title,
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title=title,
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        if content:
            self._draw_text(
                layout=layout,
                content=content,
                repeated_title=title,
            )

        if (
            content
            and prepared_images
        ):
            layout.advance(
                self.GAP
            )

        if prepared_images:
            self._draw_images(
                layout=layout,
                images=prepared_images,
                repeated_title=title,
            )

        layout.advance(
            self.GAP
        )

    def _draw_text(
        self,
        *,
        layout: ReportLayoutEngine,
        content: str,
        repeated_title: str,
    ) -> None:
        paragraphs = [
            paragraph.strip()
            for paragraph in str(
                content
            ).replace(
                "\r\n",
                "\n",
            ).split(
                "\n"
            )
            if paragraph.strip()
        ]

        for paragraph in paragraphs:
            height = self._estimate_text_height(
                paragraph
            )

            page = layout.ensure_space(
                height,
                repeated_title=repeated_title,
            )

            rect = layout.full_width_rect(
                height
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 3,
                    rect.y0 + 5,
                    rect.x1 - 3,
                    rect.y1 - 4,
                ),
                paragraph,
                fontsize=7.2,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.22,
                align=fitz.TEXT_ALIGN_JUSTIFY,
            )

            layout.advance(
                height
            )

    def _draw_images(
        self,
        *,
        layout: ReportLayoutEngine,
        images: list[tuple[Any, Path]],
        repeated_title: str,
    ) -> None:
        index = 0

        while index < len(
            images
        ):
            pair = images[
                index:index + 2
            ]

            row_height = (
                self._estimate_image_row_height(
                    pair
                )
            )

            page = layout.ensure_space(
                row_height,
                repeated_title=repeated_title,
            )

            gap = 10.0

            if len(pair) == 1:
                rects = [
                    layout.full_width_rect(
                        row_height
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
                        y + row_height,
                    ),
                    fitz.Rect(
                        layout.geometry.margin_left
                        + card_width
                        + gap,
                        y,
                        layout.geometry.margin_left
                        + 2 * card_width
                        + gap,
                        y + row_height,
                    ),
                ]

            for (
                image,
                image_path,
            ), rect in zip(
                pair,
                rects,
            ):
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

                page.draw_rect(
                    rect,
                    color=self.COLOR_BORDER,
                    fill=self.COLOR_SURFACE,
                    width=0.5,
                )

                image_rect = fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 8,
                    rect.x1 - 8,
                    (
                        rect.y1
                        - caption_height
                        - 7
                        if caption
                        else rect.y1 - 8
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
                            rect.x0 + 8,
                            rect.y1
                            - caption_height,
                            rect.x1 - 8,
                            rect.y1 - 5,
                        ),
                        caption,
                        fontsize=5.8,
                        fontname="helv",
                        color=self.COLOR_MUTED,
                        align=fitz.TEXT_ALIGN_CENTER,
                        lineheight=1.10,
                    )

            layout.advance(
                row_height
                + self.GAP
            )

            index += 2

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

    def _estimate_text_height(
        self,
        content: str | None,
    ) -> float:
        if not content:
            return 0.0

        clean = " ".join(
            str(content).split()
        )

        estimated_lines = max(
            1,
            (len(clean) // 105)
            + 1,
        )

        return max(
            28.0,
            min(
                230.0,
                16.0
                + estimated_lines
                * 11.0,
            ),
        )

    def _estimate_image_row_height(
        self,
        images: list[tuple[Any, Path]],
    ) -> float:
        if not images:
            return 0.0

        caption_height = max(
            (
                self._estimate_caption_height(
                    self._optional_text(
                        getattr(
                            image,
                            "caption",
                            None,
                        )
                    )
                )
                if self._optional_text(
                    getattr(
                        image,
                        "caption",
                        None,
                    )
                )
                else 0.0
            )
            for image, _ in images
        )

        return (
            205.0
            + caption_height
        )

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