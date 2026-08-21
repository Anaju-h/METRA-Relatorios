from __future__ import annotations

from datetime import datetime
from typing import Any
import re

import fitz

from services.report_engine.layout_engine import ReportLayoutEngine
from services.report_engine.report_context import ReportRenderContext


class DimensionalBatchMeasurementPage:
    """
    Condições técnicas da medição dimensional em lote.

    Somente informações efetivamente disponíveis são apresentadas.
    A ausência de campos opcionais nunca impede a geração do relatório.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)

    SECTION_TITLE_HEIGHT = 28.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        measurement = (
            render_context.measurement
        )

        if measurement is None:
            return

        fields = self._build_fields(
            render_context=render_context,
            measurement=measurement,
        )

        if not fields:
            return

        self._draw_section_title(
            layout=layout,
        )

        for label, value in fields:
            self._draw_field(
                layout=layout,
                label=label,
                value=value,
            )

    # =============================================================
    # DADOS
    # =============================================================

    def _build_fields(
        self,
        *,
        render_context: ReportRenderContext,
        measurement: Any,
    ) -> list[tuple[str, str]]:
        candidates = [
            (
                "Responsável pela medição",
                getattr(
                    measurement,
                    "responsible",
                    None,
                ),
            ),
            (
                "Data / hora da medição",
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
            (
                "Equipamento e configuração",
                self._format_equipment_configuration(
                    render_context=render_context,
                    measurement=measurement,
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
                "Sensores / tecnologias",
                getattr(
                    measurement,
                    "sensors",
                    None,
                ),
            ),
            (
                "Instruções / observações especiais",
                getattr(
                    measurement,
                    "special_instructions",
                    None,
                ),
            ),
        ]

        result: list[tuple[str, str]] = []

        for label, value in candidates:
            cleaned = self._format_field_value(
                value
            )

            if cleaned:
                result.append(
                    (
                        label,
                        cleaned,
                    )
                )

        return result

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
            repeated_title=(
                "CONDIÇÕES DA MEDIÇÃO"
            ),
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
            "3. CONDIÇÕES DA MEDIÇÃO",
            fontsize=7.3,
            fontname="hebo",
            color=(1, 1, 1),
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
            + self.GAP
        )

    # =============================================================
    # CAMPOS
    # =============================================================

    def _draw_field(
        self,
        *,
        layout: ReportLayoutEngine,
        label: str,
        value: str,
    ) -> None:
        height = self._estimate_field_height(
            value
        )

        page = layout.ensure_space(
            height + 4.0,
            repeated_title=(
                "CONDIÇÕES DA MEDIÇÃO"
            ),
        )

        rect = layout.full_width_rect(
            height
        )

        label_width = (
            rect.width * 0.27
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.4,
        )

        label_rect = fitz.Rect(
            rect.x0,
            rect.y0,
            rect.x0 + label_width,
            rect.y1,
        )

        page.draw_rect(
            label_rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_SURFACE,
            width=0.4,
        )

        page.insert_textbox(
            fitz.Rect(
                label_rect.x0 + 8,
                label_rect.y0 + 7,
                label_rect.x1 - 7,
                label_rect.y1 - 5,
            ),
            label,
            fontsize=6.1,
            fontname="hebo",
            color=self.COLOR_NAVY,
            lineheight=1.10,
        )

        page.insert_textbox(
            fitz.Rect(
                label_rect.x1 + 8,
                rect.y0 + 7,
                rect.x1 - 8,
                rect.y1 - 5,
            ),
            value,
            fontsize=6.3,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )

        layout.advance(
            height + 4.0
        )

    # =============================================================
    # HELPERS
    # =============================================================

    def _estimate_field_height(
        self,
        value: str,
    ) -> float:
        line_count = max(
            1,
            (
                len(value) + 92
            )
            // 93,
        )

        return min(
            82.0,
            max(
                30.0,
                18.0
                + line_count
                * 9.0,
            ),
        )

    def _format_equipment_configuration(
        self,
        *,
        render_context: ReportRenderContext,
        measurement: Any,
    ) -> str | None:
        """
        Apresenta somente informações úteis sobre o equipamento.

        Evita expor no PDF textos brutos extraídos do CALYPSO,
        nomes internos de rotina e separadores inválidos como "?".
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

        # Normaliza separadores problemáticos vindos de extrações antigas.
        cleaned = cleaned.replace(
            " ? ",
            " · ",
        )
        cleaned = cleaned.replace(
            " | ",
            " · ",
        )
        cleaned = cleaned.replace(
            "|",
            " · ",
        )

        # Remove nomes internos de execução/rotina quando aparecerem.
        cleaned = re.sub(
            r"\bRun\b.*?(?=(?:identifica[cç][aã]o|n[uú]mero|CALYPSO|$))",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*[·]\s*",
            " · ",
            cleaned,
        )
        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip(" ·|")

        machine_id_match = re.search(
            r"(?:identifica[cç][aã]o|n[uú]mero(?:\s+da\s+MMC)?)"
            r"\s*[:\-]?\s*([A-Za-z0-9._-]+)",
            cleaned,
            flags=re.IGNORECASE,
        )

        machine_id = (
            machine_id_match.group(1)
            if machine_id_match
            else None
        )

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

        parts: list[str] = []

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

        # Se nada estruturado for identificado, prioriza o equipamento
        # cadastrado no processo em vez do texto bruto extraído.
        if project_equipment:
            return project_equipment

        first_part = cleaned.split(
            " · "
        )[0].strip()

        return (
            first_part
            or None
        )

    def _format_field_value(
        self,
        value: Any,
    ) -> str | None:
        """
        Formata valores para apresentação ao cliente.

        Listas deixam de aparecer como representação Python
        (ex.: ['Apalpação']) e passam a ser texto natural.
        """
        if value is None:
            return None

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
            items = [
                self._optional_text(
                    item
                )
                for item in value
            ]

            items = [
                item
                for item in items
                if item
            ]

            return (
                ", ".join(items)
                or None
            )

        cleaned = self._optional_text(
            value
        )

        if not cleaned:
            return None

        # Alguns dados antigos podem ter sido persistidos como string
        # representando lista, por exemplo "['Apalpação']".
        if (
            cleaned.startswith("[")
            and cleaned.endswith("]")
        ):
            inner = cleaned[
                1:-1
            ].strip()

            if inner:
                parts = [
                    part.strip(
                        " '\""
                    )
                    for part in inner.split(",")
                    if part.strip(
                        " '\""
                    )
                ]

                if parts:
                    return ", ".join(
                        parts
                    )

        return cleaned

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