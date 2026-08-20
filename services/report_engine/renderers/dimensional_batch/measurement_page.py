from __future__ import annotations

from typing import Any

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
                "Detalhes da máquina",
                getattr(
                    measurement,
                    "machine_details",
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
                "Sensores",
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
            cleaned = self._optional_text(
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