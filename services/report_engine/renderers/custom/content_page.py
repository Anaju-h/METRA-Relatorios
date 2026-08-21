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
    Conteúdo estruturado do relatório personalizado.

    As seções adicionais livres são renderizadas centralmente pelo
    BaseReportRenderer para todos os templates.

    Este componente exibe os demais blocos disponíveis no Custom:
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
        start_number: int,
    ) -> int:
        section_number = start_number

        if (
            render_context.section_enabled("documents")
            and render_context.documents
        ):
            self._render_documents(
                layout=layout,
                render_context=render_context,
                section_number=section_number,
            )
            section_number += 1

        if (
            render_context.section_enabled("characteristics")
            and render_context.statistical_groups
        ):
            self._render_characteristics(
                layout=layout,
                render_context=render_context,
                section_number=section_number,
            )
            section_number += 1

        if (
            render_context.section_enabled("images")
            and render_context.get_additional_report_images()
        ):
            self._render_images(
                layout=layout,
                render_context=render_context,
                section_number=section_number,
            )
            section_number += 1

        observations = self._collect_observations(
            render_context
        )

        if (
            render_context.section_enabled("observations")
            and observations
        ):
            self._render_observations(
                layout=layout,
                render_context=render_context,
                section_number=section_number,
                notes=observations,
            )
            section_number += 1

        return section_number

    # =============================================================
    # SEÇÕES TÉCNICAS LIVRES
    # =============================================================

    def _custom_section_has_content(
        self,
        section: dict[str, Any],
    ) -> bool:
        return bool(
            self._has_text(
                section.get(
                    "title"
                )
            )
            or self._has_text(
                section.get(
                    "content"
                )
            )
            or section.get(
                "image_ids"
            )
        )

    def _render_custom_section(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
        section: dict[str, Any],
        section_number: int,
    ) -> None:
        title = self._clean_text(
            section.get(
                "title"
            ),
            fallback=(
                "ANÁLISE TÉCNICA"
            ),
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
            self._estimate_custom_text_height(
                content
            )
            if content
            else 0.0
        )

        first_image_height = (
            self._estimate_custom_image_row_height(
                prepared_images[:2]
            )
            if prepared_images
            else 0.0
        )

        first_required = (
            self.SECTION_TITLE_HEIGHT
            + (
                text_height
                if text_height
                else 0.0
            )
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
            title=(
                f"{section_number}. "
                f"{title}"
            ),
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        if content:
            self._draw_custom_text(
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
            self._draw_custom_images(
                layout=layout,
                images=prepared_images,
                repeated_title=title,
            )

        layout.advance(
            self.GAP
        )

    def _draw_custom_text(
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

        if not paragraphs:
            return

        for paragraph in paragraphs:
            height = (
                self._estimate_custom_text_height(
                    paragraph
                )
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

    def _draw_custom_images(
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
                self._estimate_custom_image_row_height(
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

    def _estimate_custom_text_height(
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

    def _estimate_custom_image_row_height(
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

    def _render_documents(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
        section_number: int,
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
            title=f"{section_number}. DOCUMENTOS DE ORIGEM",
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
        section_number: int,
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
            title=f"{section_number}. CARACTERÍSTICAS / RESULTADOS",
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
        section_number: int,
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

            image_height = 205.0

            block_height = (
                image_height
                + caption_height
            )

            if not title_drawn:
                page = layout.ensure_space(
                    self.SECTION_TITLE_HEIGHT
                    + self.GAP
                    + block_height
                    + self.GAP,
                    repeated_title="IMAGENS",
                )

                self._draw_section_title(
                    page=page,
                    layout=layout,
                    title=f"{section_number}. IMAGENS / EVIDÊNCIAS",
                )

                layout.advance(
                    self.SECTION_TITLE_HEIGHT
                    + self.GAP
                )

                title_drawn = True
                page = layout.current_page

            else:
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
        section_number: int,
        notes: list[tuple[str, str]],
    ) -> None:
        if not notes:
            return

        note_heights = [
            self._estimate_note_height(
                value
            )
            for _, value in notes
        ]

        first_block_height = (
            self.SECTION_TITLE_HEIGHT
            + note_heights[0]
            + self.GAP
        )

        page = layout.ensure_space(
            first_block_height,
            repeated_title="OBSERVAÇÕES TÉCNICAS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title=f"{section_number}. OBSERVAÇÕES TÉCNICAS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        for index, (label, value) in enumerate(
            notes
        ):
            height = note_heights[index]

            page = layout.ensure_space(
                height,
                repeated_title="OBSERVAÇÕES TÉCNICAS",
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
                    rect.y0 + 8,
                    rect.x1 - 10,
                    rect.y0 + 20,
                ),
                label,
                fontsize=6.1,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 10,
                    rect.y0 + 22,
                    rect.x1 - 10,
                    rect.y1 - 8,
                ),
                self._clean_text(
                    value
                ),
                fontsize=6.4,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.15,
            )

            layout.advance(
                height
            )

            if index < len(notes) - 1:
                layout.advance(
                    self.GAP
                )

        layout.advance(
            self.GAP
        )

    def _estimate_note_height(
        self,
        value: Any,
    ) -> float:
        text = self._clean_text(
            value,
            fallback="",
        )

        estimated_lines = max(
            1,
            (len(text) // 105) + 1,
        )

        return max(
            58.0,
            min(
                150.0,
                38.0
                + estimated_lines * 10.0,
            ),
        )

    def _collect_observations(
        self,
        render_context: ReportRenderContext,
    ) -> list[tuple[str, str]]:
        """
        Consolida observações realmente cadastradas no processo.

        Fontes aceitas no relatório entregue ao cliente:
        - observação específica do relatório personalizado;
        - observação geral do relatório;
        - instruções/condições especiais da medição.

        Notas internas do Controle Técnico, invalidações de aprovação,
        histórico de revisão e mensagens de auditoria não são exportadas.

        Conteúdos repetidos são exibidos uma única vez.
        """
        notes: list[tuple[str, str]] = []
        seen: set[str] = set()

        def add_note(
            label: str,
            value: Any,
        ) -> None:
            cleaned = self._optional_text(
                value
            )

            if not cleaned:
                return

            normalized = " ".join(
                cleaned.lower().split()
            )

            if normalized in seen:
                return

            seen.add(
                normalized
            )
            notes.append(
                (
                    label,
                    cleaned,
                )
            )

        add_note(
            "Observações do relatório",
            render_context.get_context_value(
                "custom_observations"
            ),
        )

        add_note(
            "Observações gerais",
            render_context.get_context_value(
                "observations"
            ),
        )

        measurement = (
            render_context.measurement
        )

        if measurement is not None:
            add_note(
                "Instruções e condições especiais",
                getattr(
                    measurement,
                    "special_instructions",
                    None,
                ),
            )

        # Notas internas do Controle Técnico, histórico de revisão,
        # invalidações de aprovação e mensagens de auditoria não são
        # conteúdo destinado ao cliente. Permanecem apenas no sistema.
        return notes

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