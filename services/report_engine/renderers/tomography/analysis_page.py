from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

from services.report_engine.layout_engine import ReportLayoutEngine
from services.report_engine.report_context import ReportRenderContext


class TomographyAnalysisPage:
    """Evidências visuais e observações da análise tomográfica."""

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)

    SECTION_TITLE_HEIGHT = 28.0
    IMAGE_HEIGHT = 168.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        images = self._collect_images(render_context)
        notes = self._resolve_notes(render_context)

        if not images and not notes:
            return

        if images:
            self._draw_images(
                layout=layout,
                images=images,
            )

        if notes:
            self._draw_notes(
                layout=layout,
                notes=notes,
            )

    def _draw_images(
        self,
        *,
        layout: ReportLayoutEngine,
        images: list[dict[str, Any]],
    ) -> None:
        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT,
            repeated_title="ANÁLISE TOMOGRÁFICA",
        )
        self._draw_section_title(
            page=page,
            layout=layout,
            title="3. EVIDÊNCIAS TOMOGRÁFICAS",
        )
        layout.advance(
            self.SECTION_TITLE_HEIGHT + self.GAP
        )

        for start in range(0, len(images), 2):
            row_items = images[start:start + 2]
            page = layout.ensure_space(
                self.IMAGE_HEIGHT + self.GAP,
                repeated_title="EVIDÊNCIAS TOMOGRÁFICAS",
            )

            gap = 10.0
            card_width = (
                layout.geometry.content_width
                if len(row_items) == 1
                else (
                    layout.geometry.content_width - gap
                ) / 2.0
            )

            for index, item in enumerate(row_items):
                x = (
                    layout.geometry.margin_left
                    + index * (card_width + gap)
                )
                rect = fitz.Rect(
                    x,
                    layout.cursor_y,
                    x + card_width,
                    layout.cursor_y + self.IMAGE_HEIGHT,
                )
                self._draw_image_card(
                    page=page,
                    rect=rect,
                    item=item,
                )

            layout.advance(
                self.IMAGE_HEIGHT + self.GAP
            )

    def _draw_image_card(
        self,
        *,
        page: fitz.Page,
        rect: fitz.Rect,
        item: dict[str, Any],
    ) -> None:
        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_SURFACE,
            width=0.5,
        )

        title = self._clean_text(
            item.get("title"),
            fallback="Evidência tomográfica",
        )
        title_height = 24.0

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 8,
                rect.y0 + 6,
                rect.x1 - 8,
                rect.y0 + title_height,
            ),
            title,
            fontsize=6.4,
            fontname="hebo",
            color=self.COLOR_NAVY,
            align=fitz.TEXT_ALIGN_CENTER,
        )

        image_path = item.get("path")
        if image_path is not None and image_path.exists():
            try:
                page.insert_image(
                    fitz.Rect(
                        rect.x0 + 8,
                        rect.y0 + title_height,
                        rect.x1 - 8,
                        rect.y1 - 8,
                    ),
                    filename=str(image_path),
                    keep_proportion=True,
                )
            except Exception:
                pass

    def _draw_notes(
        self,
        *,
        layout: ReportLayoutEngine,
        notes: str,
    ) -> None:
        height = self._text_height(notes)
        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT + height,
            repeated_title="OBSERVAÇÕES DA ANÁLISE",
        )
        self._draw_section_title(
            page=page,
            layout=layout,
            title="4. OBSERVAÇÕES DA ANÁLISE",
        )
        layout.advance(self.SECTION_TITLE_HEIGHT)

        rect = layout.full_width_rect(height)
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
            notes,
            fontsize=6.6,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )
        layout.advance(height + self.GAP)

    def _collect_images(
        self,
        render_context: ReportRenderContext,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        prepared_images = (
            render_context
            .get_report_images()
        )

        for image, image_path in prepared_images:
            title = (
                self._optional_text(
                    getattr(
                        image,
                        "caption",
                        None,
                    )
                )
                or self._friendly_image_type(
                    getattr(
                        image,
                        "image_type",
                        None,
                    )
                )
                or "Evidência tomográfica"
            )

            result.append(
                {
                    "title": title,
                    "path": image_path,
                }
            )

        return result

    def _resolve_notes(
        self,
        render_context: ReportRenderContext,
    ) -> str | None:
        candidates = [
            render_context.context.get("tomography_notes"),
            render_context.context.get("observations"),
            render_context.context.get("technical_observations"),
        ]

        measurement = render_context.measurement
        if measurement is not None:
            candidates.append(
                getattr(
                    measurement,
                    "special_instructions",
                    None,
                )
            )

        for value in candidates:
            text = self._optional_text(value)
            if text:
                return text

        return None

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

    def _existing_path(
        self,
        value: Any,
    ) -> Path | None:
        if not value:
            return None
        try:
            path = Path(str(value))
        except (TypeError, ValueError):
            return None
        if not path.exists() or not path.is_file():
            return None
        return path

    def _friendly_image_type(
        self,
        value: Any,
    ) -> str | None:
        text = self._optional_text(value)
        if not text:
            return None
        if text.lower() in {
            "fotografia",
            "imagem principal da peça/lote",
        }:
            return "Evidência tomográfica"
        return text

    def _text_height(self, value: Any) -> float:
        text = self._clean_text(value, fallback="")
        lines = max(
            1,
            (len(text) + 95) // 96,
        )
        return max(
            64.0,
            min(
                140.0,
                38.0 + lines * 10.0,
            ),
        )

    def _optional_text(
        self,
        value: Any,
    ) -> str | None:
        cleaned = " ".join(str(value or "").split())
        return cleaned or None

    def _clean_text(
        self,
        value: Any,
        *,
        fallback: str = "Não informado",
    ) -> str:
        cleaned = " ".join(str(value or "").split())
        return cleaned or fallback