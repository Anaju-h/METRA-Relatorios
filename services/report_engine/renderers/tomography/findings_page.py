from __future__ import annotations

from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class TomographyFindingsPage:
    """
    Página dedicada aos achados da inspeção tomográfica.

    Exibe:
    - quantidade total de achados;
    - severidade;
    - região afetada;
    - descrição;
    - interpretação técnica;
    - recomendações quando existirem.
    """

    COLOR_NAVY = (0.025, 0.110, 0.215)
    COLOR_TEXT = (0.070, 0.100, 0.135)
    COLOR_MUTED = (0.360, 0.410, 0.470)
    COLOR_BORDER = (0.790, 0.825, 0.860)
    COLOR_SURFACE = (0.975, 0.982, 0.988)
    COLOR_LIGHT_BLUE = (0.925, 0.960, 0.987)

    COLOR_OK = (0.080, 0.500, 0.275)
    COLOR_OK_BG = (0.910, 0.975, 0.935)

    COLOR_WARNING = (0.800, 0.430, 0.000)
    COLOR_WARNING_BG = (1.000, 0.965, 0.870)

    COLOR_NOK = (0.760, 0.160, 0.120)
    COLOR_NOK_BG = (0.995, 0.920, 0.905)

    SECTION_TITLE_HEIGHT = 28.0
    CARD_HEADER_HEIGHT = 28.0
    CARD_BODY_HEIGHT = 92.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        findings = render_context.findings

        self._draw_summary(
            layout=layout,
            findings=findings,
        )

        if not findings:
            self._draw_interpretation(
                layout=layout,
                render_context=render_context,
            )
            return

        for index, finding in enumerate(
            findings,
            start=1,
        ):
            self._draw_finding_card(
                layout=layout,
                finding=finding,
                index=index,
            )

        self._draw_interpretation(
            layout=layout,
            render_context=render_context,
        )

    def _draw_summary(
        self,
        *,
        layout: ReportLayoutEngine,
        findings: list[Any],
    ) -> None:
        page = layout.ensure_space(
            108.0,
            repeated_title="ACHADOS TOMOGRÁFICOS",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="4. ACHADOS TOMOGRÁFICOS",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        severity_counts = {
            "BAIXA": 0,
            "MÉDIA": 0,
            "ALTA": 0,
        }

        for finding in findings:
            severity = self._severity_code(
                finding
            )
            severity_counts[severity] = (
                severity_counts.get(
                    severity,
                    0,
                )
                + 1
            )

        indicators = [
            (
                "Total",
                len(findings),
                self.COLOR_LIGHT_BLUE,
                self.COLOR_NAVY,
            ),
            (
                "Baixa",
                severity_counts.get(
                    "BAIXA",
                    0,
                ),
                self.COLOR_OK_BG,
                self.COLOR_OK,
            ),
            (
                "Média",
                severity_counts.get(
                    "MÉDIA",
                    0,
                ),
                self.COLOR_WARNING_BG,
                self.COLOR_WARNING,
            ),
            (
                "Alta",
                severity_counts.get(
                    "ALTA",
                    0,
                ),
                self.COLOR_NOK_BG,
                self.COLOR_NOK,
            ),
        ]

        gap = 8.0
        card_height = 66.0

        card_width = (
            layout.geometry.content_width
            - gap
            * (
                len(indicators) - 1
            )
        ) / len(indicators)

        for index, (
            label,
            value,
            background,
            accent,
        ) in enumerate(indicators):
            x = (
                layout.geometry.margin_left
                + index
                * (
                    card_width + gap
                )
            )

            rect = fitz.Rect(
                x,
                layout.cursor_y,
                x + card_width,
                layout.cursor_y
                + card_height,
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
                    rect.y0 + 7,
                    rect.x1 - 4,
                    rect.y0 + 21,
                ),
                label,
                fontsize=5.7,
                fontname="hebo",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 4,
                    rect.y0 + 27,
                    rect.x1 - 4,
                    rect.y1 - 7,
                ),
                str(value),
                fontsize=12.0,
                fontname="hebo",
                color=accent,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            card_height + self.GAP
        )

    def _draw_finding_card(
        self,
        *,
        layout: ReportLayoutEngine,
        finding: Any,
        index: int,
    ) -> None:
        required = (
            self.CARD_HEADER_HEIGHT
            + self.CARD_BODY_HEIGHT
            + self.GAP
        )

        page = layout.ensure_space(
            required,
            repeated_title="ACHADOS TOMOGRÁFICOS",
        )

        if (
            layout.cursor_y
            <= layout.geometry.margin_top + 92
        ):
            self._draw_section_title(
                page=page,
                layout=layout,
                title="4. ACHADOS TOMOGRÁFICOS",
            )
            layout.advance(
                self.SECTION_TITLE_HEIGHT
                + self.GAP
            )

        severity = self._severity_code(
            finding
        )

        accent, background = (
            self._severity_style(
                severity
            )
        )

        header_rect = layout.full_width_rect(
            self.CARD_HEADER_HEIGHT
        )

        page.draw_rect(
            header_rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_LIGHT_BLUE,
            width=0.5,
        )

        finding_type = self._finding_value(
            finding,
            "type",
            "finding_type",
            "name",
            fallback="Achado",
        )

        region = self._finding_value(
            finding,
            "region",
            "location",
            "area",
            fallback="",
        )

        page.insert_textbox(
            fitz.Rect(
                header_rect.x0 + 8,
                header_rect.y0 + 7,
                header_rect.x1 - 110,
                header_rect.y1 - 4,
            ),
            (
                f"{index:02d}. "
                f"{finding_type}"
                " · "
                f"{region}"
            ),
            fontsize=6.8,
            fontname="hebo",
            color=self.COLOR_NAVY,
        )

        severity_rect = fitz.Rect(
            header_rect.x1 - 96,
            header_rect.y0 + 5,
            header_rect.x1 - 8,
            header_rect.y1 - 5,
        )

        page.draw_rect(
            severity_rect,
            color=accent,
            fill=background,
            width=0.6,
        )

        page.insert_textbox(
            severity_rect,
            severity or "ACHADO",
            fontsize=5.8,
            fontname="hebo",
            color=accent,
            align=fitz.TEXT_ALIGN_CENTER,
        )

        layout.advance(
            self.CARD_HEADER_HEIGHT
        )

        body_rect = layout.full_width_rect(
            self.CARD_BODY_HEIGHT
        )

        page.draw_rect(
            body_rect,
            color=self.COLOR_BORDER,
            fill=(1, 1, 1),
            width=0.4,
        )

        description = self._finding_value(
            finding,
            "description",
            "details",
            "observation",
            "notes",
            fallback="",
        )

        size = self._finding_value(
            finding,
            "size",
            "dimension",
            "diameter",
            fallback="—",
        )

        reference = self._finding_value(
            finding,
            "reference",
            "reference_id",
            "marker",
            fallback="—",
        )

        status = self._finding_value(
            finding,
            "status",
            "classification",
            fallback="—",
        )

        left_width = (
            body_rect.width
            * 0.31
        )

        labels = [
            (
                "Dimensão / tamanho",
                size,
            ),
            (
                "Referência",
                reference,
            ),
            (
                "Classificação",
                status,
            ),
        ]

        row_height = (
            body_rect.height
            / len(labels)
        )

        for row_index, (
            label,
            value,
        ) in enumerate(labels):
            y0 = (
                body_rect.y0
                + row_index
                * row_height
            )

            cell = fitz.Rect(
                body_rect.x0,
                y0,
                body_rect.x0 + left_width,
                y0 + row_height,
            )

            fill = (
                self.COLOR_SURFACE
                if row_index % 2 == 0
                else (1, 1, 1)
            )

            page.draw_rect(
                cell,
                color=self.COLOR_BORDER,
                fill=fill,
                width=0.3,
            )

            label_width = (
                cell.width
                * 0.56
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + 6,
                    cell.y0 + 7,
                    cell.x0 + label_width,
                    cell.y1 - 4,
                ),
                label,
                fontsize=5.4,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    cell.x0 + label_width,
                    cell.y0 + 7,
                    cell.x1 - 6,
                    cell.y1 - 4,
                ),
                value,
                fontsize=5.6,
                fontname="helv",
                color=self.COLOR_TEXT,
                align=fitz.TEXT_ALIGN_RIGHT,
            )

        description_rect = fitz.Rect(
            body_rect.x0 + left_width + 8,
            body_rect.y0 + 8,
            body_rect.x1 - 8,
            body_rect.y1 - 8,
        )

        page.insert_textbox(
            description_rect,
            description,
            fontsize=6.4,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )

        layout.advance(
            self.CARD_BODY_HEIGHT
            + self.GAP
        )

    def _draw_interpretation(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        interpretation = (
            render_context.get_context_value(
                "tomography_interpretation"
            )
        )

        recommendation = (
            render_context.get_context_value(
                "tomography_recommendation"
            )
        )

        if (
            not self._has_text(
                interpretation
            )
            and not self._has_text(
                recommendation
            )
        ):
            return

        page = layout.ensure_space(
            120.0,
            repeated_title="INTERPRETAÇÃO TÉCNICA",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="5. INTERPRETAÇÃO TÉCNICA",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        items = []

        if self._has_text(
            interpretation
        ):
            items.append(
                (
                    "Interpretação",
                    interpretation,
                    self.COLOR_LIGHT_BLUE,
                    self.COLOR_NAVY,
                )
            )

        if self._has_text(
            recommendation
        ):
            items.append(
                (
                    "Recomendação",
                    recommendation,
                    self.COLOR_WARNING_BG,
                    self.COLOR_WARNING,
                )
            )

        for label, value, fill, accent in items:
            height = 62.0

            page = layout.ensure_space(
                height,
                repeated_title="INTERPRETAÇÃO TÉCNICA",
            )

            rect = layout.full_width_rect(
                height
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=fill,
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
                fontsize=6.3,
                fontname="hebo",
                color=accent,
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
                fontsize=6.4,
                fontname="helv",
                color=self.COLOR_TEXT,
                lineheight=1.15,
            )

            layout.advance(
                height + self.GAP
            )

    def _draw_empty_state(
        self,
        *,
        layout: ReportLayoutEngine,
    ) -> None:
        page = layout.ensure_space(
            74.0,
            repeated_title="ACHADOS TOMOGRÁFICOS",
        )

        rect = layout.full_width_rect(
            64.0
        )

        page.draw_rect(
            rect,
            color=self.COLOR_BORDER,
            fill=self.COLOR_OK_BG,
            width=0.5,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 12,
                rect.y0 + 14,
                rect.x1 - 12,
                rect.y1 - 10,
            ),
            (
                "Nenhum achado técnico foi registrado "
                "para esta inspeção tomográfica."
            ),
            fontsize=7.0,
            fontname="helv",
            color=self.COLOR_OK,
            align=fitz.TEXT_ALIGN_CENTER,
        )

        layout.advance(
            64.0
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

    def _finding_value(
        self,
        finding: Any,
        *keys: str,
        fallback: str = "Não informado",
    ) -> str:
        if isinstance(
            finding,
            dict,
        ):
            for key in keys:
                value = finding.get(
                    key
                )

                if self._has_text(
                    value
                ):
                    return self._clean_text(
                        value
                    )

        for key in keys:
            value = getattr(
                finding,
                key,
                None,
            )

            if self._has_text(
                value
            ):
                return self._clean_text(
                    value
                )

        return fallback

    def _severity_code(
        self,
        finding: Any,
    ) -> str:
        raw = self._finding_value(
            finding,
            "severity",
            "gravity",
            "level",
            fallback="",
        ).upper()

        if (
            "ALTA" in raw
            or "HIGH" in raw
            or "CRÍT" in raw
            or "CRIT" in raw
        ):
            return "ALTA"

        if (
            "MÉD" in raw
            or "MED" in raw
            or "MODER" in raw
        ):
            return "MÉDIA"

        if (
            "BAIX" in raw
            or "LOW" in raw
            or "LEVE" in raw
        ):
            return "BAIXA"

        return ""

    def _severity_style(
        self,
        severity: str,
    ) -> tuple[
        tuple[float, float, float],
        tuple[float, float, float],
    ]:
        if severity == "ALTA":
            return (
                self.COLOR_NOK,
                self.COLOR_NOK_BG,
            )

        if severity == "MÉDIA":
            return (
                self.COLOR_WARNING,
                self.COLOR_WARNING_BG,
            )

        if severity == "BAIXA":
            return (
                self.COLOR_OK,
                self.COLOR_OK_BG,
            )

        return (
            self.COLOR_NAVY,
            self.COLOR_LIGHT_BLUE,
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