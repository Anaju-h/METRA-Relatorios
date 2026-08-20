from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import ast
import re

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class DimensionalIndividualMeasurementPage:
    """
    Página técnica do relatório dimensional individual.

    Reúne:
    - informações da medição;
    - documentos de origem;
    - imagens técnicas adicionais;
    - observações e condições especiais.

    Campos vazios são omitidos para melhorar o aproveitamento da página.
    """

    COLOR_NAVY = (
        0.025,
        0.110,
        0.215,
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

    SECTION_TITLE_HEIGHT = 28.0
    ROW_HEIGHT = 27.0
    MIN_IMAGE_HEIGHT = 176.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        # Regra METRA: uma seção só aparece quando foi selecionada
        # e existe informação real para ser renderizada.
        if render_context.section_enabled(
            "measurement"
        ):
            self._render_measurement_information(
                layout=layout,
                render_context=render_context,
            )

        if render_context.section_enabled(
            "documents"
        ):
            self._render_source_documents(
                layout=layout,
                render_context=render_context,
            )

        if render_context.section_enabled(
            "observations"
        ):
            self._render_observations(
                layout=layout,
                render_context=render_context,
            )

    # =============================================================
    # MEDIÇÃO
    # =============================================================

    def _render_measurement_information(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        measurement = render_context.measurement

        if measurement is None:
            return

        fields = [
            (
                "Responsável pela medição",
                getattr(
                    measurement,
                    "responsible",
                    None,
                ),
            ),
            (
                "Data e hora",
                getattr(
                    measurement,
                    "measurement_datetime",
                    None,
                ),
            ),
            (
                "Referência do desenho",
                getattr(
                    measurement,
                    "drawing_reference",
                    None,
                ),
            ),
            (
                "Equipamento e configuração",
                self._format_equipment_configuration(
                    render_context=render_context,
                    measurement=measurement,
                ),
            ),
            (
                "Sensores / tecnologias",
                getattr(
                    measurement,
                    "sensors",
                    None,
                ),
            ),
            (
                "Acessórios",
                getattr(
                    measurement,
                    "accessories",
                    None,
                ),
            ),
            (
                "Alinhamento",
                getattr(
                    measurement,
                    "alignment",
                    None,
                ),
            ),
            (
                "Fixação",
                getattr(
                    measurement,
                    "fixture",
                    None,
                ),
            ),
        ]

        fields = [
            (
                label,
                value,
            )
            for label, value in fields
            if self._has_text(value)
        ]

        if not fields:
            return

        row_heights = [
            self._estimate_row_height(
                value=value,
                content_width=layout.geometry.content_width,
            )
            for _, value in fields
        ]

        estimated_height = (
            self.SECTION_TITLE_HEIGHT
            + sum(row_heights)
        )

        page = layout.ensure_space(
            estimated_height,
            repeated_title="INFORMAÇÕES DA MEDIÇÃO",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="4. INFORMAÇÕES DA MEDIÇÃO",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        self._draw_key_value_rows(
            page=page,
            layout=layout,
            values=fields,
            row_heights=row_heights,
        )

        layout.advance(
            self.GAP
        )

    # =============================================================
    # DOCUMENTOS
    # =============================================================

    def _render_source_documents(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        documents = render_context.documents

        if not documents:
            return

        title_height = self.SECTION_TITLE_HEIGHT
        header_height = 25.0
        row_height = 28.0

        required_height = (
            title_height
            + header_height
            + min(
                len(documents),
                8,
            ) * row_height
        )

        page = layout.ensure_space(
            required_height,
            repeated_title="DOCUMENTOS DE ORIGEM",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="5. DOCUMENTOS DE ORIGEM",
        )

        layout.advance(
            title_height
        )

        self._draw_document_header(
            page=page,
            layout=layout,
            height=header_height,
        )

        layout.advance(
            header_height
        )

        for index, document in enumerate(
            documents,
            start=1,
        ):
            page = layout.ensure_space(
                row_height,
                repeated_title="DOCUMENTOS DE ORIGEM",
            )

            if (
                layout.cursor_y
                <= layout.geometry.margin_top + 90
            ):
                self._draw_section_title(
                    page=page,
                    layout=layout,
                    title="5. DOCUMENTOS DE ORIGEM",
                )

                layout.advance(
                    title_height
                )

                self._draw_document_header(
                    page=page,
                    layout=layout,
                    height=header_height,
                )

                layout.advance(
                    header_height
                )

            self._draw_document_row(
                page=page,
                layout=layout,
                index=index,
                document=document,
                alternate=(
                    index % 2 == 1
                ),
                height=row_height,
            )

            layout.advance(
                row_height
            )

        layout.advance(
            self.GAP
        )

    def _draw_document_header(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        height: float,
    ) -> None:
        columns = self._document_columns(
            layout.geometry.content_width
        )

        headers = [
            "Nº",
            "Unidade",
            "Arquivo",
            "Origem",
            "Páginas",
            "Situação",
        ]

        for header, rect in zip(
            headers,
            columns,
        ):
            cell = fitz.Rect(
                layout.geometry.margin_left + rect.x0,
                layout.cursor_y,
                layout.geometry.margin_left + rect.x1,
                layout.cursor_y + height,
            )

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=self.COLOR_NAVY,
                width=0.4,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 4,
                    cell.y0 + 7,
                    cell.x1 - 4,
                    cell.y1 - 4,
                ),
                header,
                fontsize=5.6,
                fontname="hebo",
                color=(
                    1,
                    1,
                    1,
                ),
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if header == "Arquivo"
                    else fitz.TEXT_ALIGN_CENTER
                ),
            )

    def _draw_document_row(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        index: int,
        document: Any,
        alternate: bool,
        height: float,
    ) -> None:
        columns = self._document_columns(
            layout.geometry.content_width
        )

        values = [
            str(index),
            self._clean_text(
                getattr(
                    document,
                    "specimen_identifier",
                    None,
                ),
                fallback=f"Unidade {index}",
            ),
            self._clean_text(
                getattr(
                    document,
                    "file_name",
                    None,
                ),
                fallback="Documento",
            ),
            self._clean_text(
                getattr(
                    document,
                    "source_type",
                    None,
                ),
                fallback="-",
            ),
            str(
                getattr(
                    document,
                    "page_count",
                    0,
                )
                or 0
            ),
            self._clean_text(
                getattr(
                    document,
                    "analysis_status",
                    None,
                ),
                fallback="Pendente",
            ),
        ]

        fill = (
            self.COLOR_SURFACE
            if alternate
            else (
                1,
                1,
                1,
            )
        )

        for column_index, (
            value,
            rect,
        ) in enumerate(
            zip(
                values,
                columns,
            )
        ):
            cell = fitz.Rect(
                layout.geometry.margin_left + rect.x0,
                layout.cursor_y,
                layout.geometry.margin_left + rect.x1,
                layout.cursor_y + height,
            )

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.35,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 4,
                    cell.y0 + 7,
                    cell.x1 - 4,
                    cell.y1 - 4,
                ),
                value,
                fontsize=5.6,
                fontname="helv",
                color=self.COLOR_TEXT,
                align=(
                    fitz.TEXT_ALIGN_LEFT
                    if column_index == 2
                    else fitz.TEXT_ALIGN_CENTER
                ),
            )

    def _document_columns(
        self,
        content_width: float,
    ) -> list[fitz.Rect]:
        ratios = [
            0.07,
            0.15,
            0.33,
            0.16,
            0.11,
            0.18,
        ]

        columns = []

        x = 0.0

        for ratio in ratios:
            width = (
                content_width
                * ratio
            )

            columns.append(
                fitz.Rect(
                    x,
                    0,
                    x + width,
                    0,
                )
            )

            x += width

        return columns

    # =============================================================
    # IMAGENS
    # =============================================================

    def _render_technical_images(
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
            self.SECTION_TITLE_HEIGHT
            + self.MIN_IMAGE_HEIGHT,
            repeated_title="IMAGENS TÉCNICAS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="6. IMAGENS TÉCNICAS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        gap = 10.0
        card_width = (
            layout.geometry.content_width
            - gap
        ) / 2.0

        index = 0

        while index < len(
            prepared_images
        ):
            remaining = (
                len(
                    prepared_images
                )
                - index
            )

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
                205.0
                + caption_height
            )

            page = layout.ensure_space(
                block_height,
                repeated_title="IMAGENS TÉCNICAS",
            )

            if (
                layout.cursor_y
                <= layout.geometry.margin_top + 90
            ):
                self._draw_section_title(
                    page=page,
                    layout=layout,
                    title="6. IMAGENS TÉCNICAS",
                )

                layout.advance(
                    self.SECTION_TITLE_HEIGHT
                )

            if (
                remaining == 1
                and len(pair) == 1
            ):
                rects = [
                    layout.full_width_rect(
                        block_height
                    )
                ]
            else:
                start_x = (
                    layout.geometry.margin_left
                )

                rects = [
                    fitz.Rect(
                        start_x,
                        layout.cursor_y,
                        start_x + card_width,
                        layout.cursor_y + block_height,
                    ),
                    fitz.Rect(
                        start_x + card_width + gap,
                        layout.cursor_y,
                        start_x + card_width * 2 + gap,
                        layout.cursor_y + block_height,
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

            index += len(pair)

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
                self._draw_image_placeholder(
                    page=page,
                    rect=image_rect,
                    text="Não foi possível carregar esta imagem.",
                )
        else:
            self._draw_image_placeholder(
                page=page,
                rect=image_rect,
                text="Arquivo da imagem não encontrado.",
            )

        if caption:
            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 9,
                    rect.y1 - caption_height,
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
    # OBSERVAÇÕES
    # =============================================================

    def _render_observations(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        measurement = render_context.measurement

        notes = []

        if measurement is not None:
            special_instructions = getattr(
                measurement,
                "special_instructions",
                None,
            )

            if self._has_text(
                special_instructions
            ):
                notes.append(
                    (
                        "Instruções e condições especiais",
                        special_instructions,
                    )
                )

        # Notas internas do Controle Técnico, histórico de revisão,
        # invalidações de aprovação e mensagens de auditoria não são
        # conteúdo destinado ao cliente e não entram no PDF.
        if not notes:
            return

        note_heights = [
            self._estimate_note_height(
                value
            )
            for _, value in notes
        ]

        estimated_height = (
            self.SECTION_TITLE_HEIGHT
            + sum(note_heights)
            + max(
                0,
                len(notes) - 1,
            ) * self.GAP
        )

        page = layout.ensure_space(
            estimated_height,
            repeated_title="OBSERVAÇÕES TÉCNICAS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="6. OBSERVAÇÕES TÉCNICAS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        for (
            label,
            value,
        ), note_height in zip(
            notes,
            note_heights,
        ):
            page = layout.ensure_space(
                note_height,
                repeated_title="OBSERVAÇÕES TÉCNICAS",
            )

            rect = layout.full_width_rect(
                note_height
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=self.COLOR_WARNING_BG,
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y0 + 20,
                ),
                label,
                fontsize=6.4,
                fontname="hebo",
                color=self.COLOR_WARNING,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 23,
                    rect.x1 - 8,
                    rect.y1 - 7,
                ),
                self._clean_text(
                    value
                ),
                fontsize=6.5,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.15,
            )

            layout.advance(
                note_height
                + self.GAP
            )

    # =============================================================
    # AUXILIARES VISUAIS
    # =============================================================

    def _draw_key_value_rows(
        self,
        *,
        page: fitz.Page,
        layout: ReportLayoutEngine,
        values: list[
            tuple[str, Any]
        ],
        row_heights: list[float] | None = None,
    ) -> None:
        label_width = (
            layout.geometry.content_width
            * 0.35
        )

        resolved_heights = (
            row_heights
            if row_heights is not None
            else [
                self.ROW_HEIGHT
                for _ in values
            ]
        )

        for index, (
            (
                label,
                value,
            ),
            row_height,
        ) in enumerate(
            zip(
                values,
                resolved_heights,
            )
        ):
            page = layout.ensure_space(
                row_height,
                repeated_title="INFORMAÇÕES DA MEDIÇÃO",
            )

            rect = layout.full_width_rect(
                row_height
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
                rect,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.35,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x0 + label_width,
                    rect.y1 - 4,
                ),
                label,
                fontsize=6.3,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + label_width,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                self._format_field_value(
                    value
                ),
                fontsize=6.6,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.12,
            )

            layout.advance(
                row_height
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
            fontsize=7.4,
            fontname="hebo",
            color=(
                1,
                1,
                1,
            ),
        )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

    def _estimate_row_height(
        self,
        *,
        value: Any,
        content_width: float,
    ) -> float:
        text = self._format_field_value(
            value
        )

        value_width = max(
            120.0,
            content_width * 0.63,
        )

        chars_per_line = max(
            24,
            int(
                value_width / 3.2
            ),
        )

        lines = max(
            1,
            (
                len(text)
                + chars_per_line
                - 1
            )
            // chars_per_line,
        )

        return max(
            self.ROW_HEIGHT,
            17.0 + lines * 9.0,
        )

    def _estimate_caption_height(
        self,
        text: str,
    ) -> float:
        lines = max(
            1,
            (
                len(text)
                + 68
            )
            // 69,
        )

        return max(
            27.0,
            min(
                48.0,
                17.0 + lines * 9.0,
            ),
        )

    def _estimate_note_height(
        self,
        value: Any,
    ) -> float:
        text = self._clean_text(
            value
        )

        lines = max(
            1,
            (
                len(text)
                + 100
            )
            // 101,
        )

        return max(
            60.0,
            42.0 + lines * 9.5,
        )

    def _format_equipment_configuration(
        self,
        *,
        render_context: ReportRenderContext,
        measurement: Any,
    ) -> str | None:
        """
        Prioriza o equipamento cadastrado no processo e limpa detalhes
        extraídos do relatório de origem para evitar nomes de rotina,
        duplicações e textos como "Run Todas Caracteristicas".
        """
        project = getattr(
            render_context,
            "project",
            None,
        )

        project_equipment = self._optional_text(
            getattr(
                project,
                "equipment",
                None,
            )
        )

        raw_details = self._optional_text(
            getattr(
                measurement,
                "machine_details",
                None,
            )
        )

        if not raw_details:
            return project_equipment

        cleaned = raw_details

        # Remove nomes de execução/rotina que não são parte do equipamento.
        cleaned = re.sub(
            r"\bRun\b.*?(?=(?:identifica[cç][aã]o|n[uú]mero|CALYPSO|$))",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        # Normaliza separadores e caracteres vindos de extrações antigas.
        cleaned = cleaned.replace(
            " ? ",
            " · ",
        )
        cleaned = re.sub(
            r"\s*[·|]\s*",
            " · ",
            cleaned,
        )
        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip(" ·|")

        # Captura identificação/número da máquina sem duplicá-lo.
        machine_id_match = re.search(
            r"(?:identifica[cç][aã]o|n[uú]mero(?:\s+da\s+MMC)?)\s*[:\-]?\s*([A-Za-z0-9._-]+)",
            cleaned,
            flags=re.IGNORECASE,
        )
        machine_id = (
            machine_id_match.group(1)
            if machine_id_match
            else None
        )

        # Captura versão do CALYPSO quando estiver presente.
        version_match = re.search(
            r"CALYPSO.*?vers[aã]o\s*[:\-]?\s*([0-9.]+)",
            cleaned,
            flags=re.IGNORECASE,
        )
        software_version = (
            version_match.group(1)
            if version_match
            else None
        )

        parts = []

        if project_equipment:
            parts.append(
                project_equipment
            )

        if machine_id:
            parts.append(
                f"Identificação: {machine_id}"
            )

        if software_version:
            parts.append(
                f"CALYPSO {software_version}"
            )

        if parts:
            return " · ".join(
                dict.fromkeys(parts)
            )

        # Fallback: usa apenas a primeira identificação coerente,
        # evitando expor todo o texto bruto extraído.
        first_part = cleaned.split(
            " · "
        )[0].strip()

        if (
            project_equipment
            and project_equipment.lower()
            in first_part.lower()
        ):
            return project_equipment

        return (
            project_equipment
            or first_part
            or None
        )

    def _format_field_value(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "Não informado"

        if isinstance(
            value,
            datetime,
        ):
            return value.strftime(
                "%d/%m/%Y %H:%M"
            )

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            return ", ".join(
                self._clean_text(
                    item
                )
                for item in value
                if self._has_text(
                    item
                )
            ) or "Não informado"

        text = self._clean_text(
            value
        )

        # Alguns campos legados chegam do SQLite como texto de lista,
        # por exemplo: ["Apalpação", "Óptico"].
        if (
            text.startswith("[")
            and text.endswith("]")
        ):
            try:
                parsed = ast.literal_eval(
                    text
                )

                if isinstance(
                    parsed,
                    (
                        list,
                        tuple,
                        set,
                    ),
                ):
                    return ", ".join(
                        self._clean_text(
                            item
                        )
                        for item in parsed
                        if self._has_text(
                            item
                        )
                    ) or "Não informado"

            except (
                ValueError,
                SyntaxError,
            ):
                pass

        # Datas ISO vindas diretamente da persistência.
        try:
            if (
                "T" in text
                and len(text) >= 16
            ):
                parsed_date = datetime.fromisoformat(
                    text.replace(
                        "Z",
                        "+00:00",
                    )
                )

                return parsed_date.strftime(
                    "%d/%m/%Y %H:%M"
                )

        except ValueError:
            pass

        return text

    def _optional_text(
        self,
        value: Any,
    ) -> str | None:
        cleaned = " ".join(
            str(
                value or ""
            ).split()
        )

        return cleaned or None

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