from __future__ import annotations

from typing import Any

import fitz

from services.report_engine.layout_engine import (
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class TomographyTechnicalControlPage:
    """
    Página final do relatório de tomografia industrial.

    Reúne:
    - conclusão técnica;
    - limitações da análise;
    - observações finais;
    - elaboração e revisão;
    - aprovação;
    - assinaturas.
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

    COLOR_OK = (
        0.080,
        0.500,
        0.275,
    )

    COLOR_OK_BG = (
        0.910,
        0.975,
        0.935,
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

    COLOR_NOK = (
        0.760,
        0.160,
        0.120,
    )

    COLOR_NOK_BG = (
        0.995,
        0.920,
        0.905,
    )

    SECTION_TITLE_HEIGHT = 28.0
    ROW_HEIGHT = 27.0
    GAP = 10.0

    def render(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        self._draw_conclusion(
            layout=layout,
            render_context=render_context,
        )

        self._draw_limitations(
            layout=layout,
            render_context=render_context,
        )

        self._draw_technical_control(
            layout=layout,
            render_context=render_context,
        )

        self._draw_signatures(
            layout=layout,
            render_context=render_context,
        )

    # =============================================================
    # CONCLUSÃO
    # =============================================================

    def _draw_conclusion(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        findings = render_context.findings

        high_count = 0
        medium_count = 0

        for finding in findings:
            severity = self._finding_value(
                finding,
                "severity",
                "gravity",
                "level",
                fallback="",
            ).upper()

            if (
                "ALTA" in severity
                or "HIGH" in severity
                or "CRÍT" in severity
                or "CRIT" in severity
            ):
                high_count += 1

            elif (
                "MÉD" in severity
                or "MED" in severity
                or "MODER" in severity
            ):
                medium_count += 1

        explicit_conclusion = (
            render_context.get_context_value(
                "tomography_conclusion"
            )
        )

        if high_count > 0:
            title = (
                "CONCLUSÃO: ACHADOS CRÍTICOS IDENTIFICADOS"
            )

            default_message = (
                f"Foram identificados {high_count} achado(s) "
                "de alta severidade. Recomenda-se avaliação "
                "técnica específica antes da liberação da peça."
            )

            accent = self.COLOR_NOK
            background = self.COLOR_NOK_BG

        elif medium_count > 0:
            title = (
                "CONCLUSÃO: ACHADOS RELEVANTES IDENTIFICADOS"
            )

            default_message = (
                f"Foram identificados {medium_count} achado(s) "
                "de severidade média. Recomenda-se análise "
                "conjunta com os critérios de aceitação aplicáveis."
            )

            accent = self.COLOR_WARNING
            background = self.COLOR_WARNING_BG

        elif findings:
            title = (
                "CONCLUSÃO: ACHADOS REGISTRADOS"
            )

            default_message = (
                "A inspeção tomográfica identificou achados "
                "registrados neste relatório. A avaliação final "
                "deve considerar os critérios técnicos aplicáveis."
            )

            accent = self.COLOR_WARNING
            background = self.COLOR_WARNING_BG

        else:
            title = (
                "CONCLUSÃO TÉCNICA"
            )

            default_message = (
                "As evidências e informações da inspeção tomográfica "
                "estão consolidadas neste relatório e devem ser "
                "interpretadas em conjunto com os dados de aquisição "
                "e o relatório original anexado."
            )

            accent = self.COLOR_NAVY
            background = self.COLOR_SURFACE

        conclusion = self._clean_text(
            explicit_conclusion,
            fallback=default_message,
        )

        estimated_height = self._text_block_height(
            conclusion,
            minimum=78.0,
            maximum=145.0,
        )

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + estimated_height,
            repeated_title="CONCLUSÃO TÉCNICA",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="7. CONCLUSÃO TÉCNICA",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        rect = layout.full_width_rect(
            estimated_height
        )

        page.draw_rect(
            rect,
            color=accent,
            fill=background,
            width=0.8,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 10,
                rect.y0 + 9,
                rect.x1 - 10,
                rect.y0 + 25,
            ),
            title,
            fontsize=7.7,
            fontname="hebo",
            color=accent,
        )

        page.insert_textbox(
            fitz.Rect(
                rect.x0 + 10,
                rect.y0 + 31,
                rect.x1 - 10,
                rect.y1 - 9,
            ),
            conclusion,
            fontsize=6.7,
            fontname="helv",
            color=self.COLOR_TEXT,
            lineheight=1.15,
        )

        layout.advance(
            estimated_height
            + self.GAP
        )

    # =============================================================
    # LIMITAÇÕES
    # =============================================================

    def _draw_limitations(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        limitations = (
            render_context.get_context_value(
                "tomography_limitations"
            )
        )

        if not self._has_text(
            limitations
        ):
            limitations = (
                render_context.get_context_value(
                    "inspection_limitations"
                )
            )

        notes = render_context.tomography_notes

        items = []

        if self._has_text(
            limitations
        ):
            items.append(
                (
                    "Limitações da análise",
                    limitations,
                )
            )

        if self._has_text(
            notes
        ):
            items.append(
                (
                    "Observações finais",
                    notes,
                )
            )

        if not items:
            return

        page = layout.ensure_space(
            self.SECTION_TITLE_HEIGHT
            + 72.0,
            repeated_title="LIMITAÇÕES E OBSERVAÇÕES",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="8. LIMITAÇÕES E OBSERVAÇÕES",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        for label, value in items:
            height = self._text_block_height(
                value,
                minimum=62.0,
                maximum=130.0,
            )

            page = layout.ensure_space(
                height,
                repeated_title="LIMITAÇÕES E OBSERVAÇÕES",
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
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y0 + 21,
                ),
                label,
                fontsize=6.3,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 24,
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
                height
                + self.GAP
            )

    # =============================================================
    # CONTROLE TÉCNICO
    # =============================================================

    def _draw_technical_control(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        control = (
            render_context.technical_control
        )

        if control is None:
            return

        values = [
            (
                "Situação",
                getattr(
                    control,
                    "status",
                    None,
                ),
            ),
            (
                "Responsável pela elaboração",
                getattr(
                    control,
                    "prepared_by",
                    None,
                ),
            ),
            (
                "Data da elaboração",
                getattr(
                    control,
                    "prepared_at",
                    None,
                ),
            ),
            (
                "Responsável pela revisão",
                getattr(
                    control,
                    "reviewed_by",
                    None,
                ),
            ),
            (
                "Data da revisão",
                getattr(
                    control,
                    "reviewed_at",
                    None,
                ),
            ),
        ]

        values = [
            (
                label,
                value,
            )
            for label, value in values
            if self._has_text(
                value
            )
        ]

        if not values:
            return

        required = (
            self.SECTION_TITLE_HEIGHT
            + len(values)
            * self.ROW_HEIGHT
        )

        page = layout.ensure_space(
            required,
            repeated_title="CONTROLE TÉCNICO",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="9. CONTROLE TÉCNICO",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        label_width = (
            layout.geometry.content_width
            * 0.38
        )

        for index, (
            label,
            value,
        ) in enumerate(values):
            rect = layout.full_width_rect(
                self.ROW_HEIGHT
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
                    rect.x0
                    + label_width,
                    rect.y1 - 4,
                ),
                label,
                fontsize=6.1,
                fontname="hebo",
                color=self.COLOR_NAVY,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0
                    + label_width,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y1 - 4,
                ),
                self._clean_text(
                    value
                ),
                fontsize=6.4,
                fontname="helv",
                color=self.COLOR_TEXT,
            )

            layout.advance(
                self.ROW_HEIGHT
            )

        layout.advance(
            self.GAP
        )

    # =============================================================
    # ASSINATURAS
    # =============================================================

    def _draw_signatures(
        self,
        *,
        layout: ReportLayoutEngine,
        render_context: ReportRenderContext,
    ) -> None:
        control = (
            render_context.technical_control
        )

        prepared_by = (
            getattr(
                control,
                "prepared_by",
                None,
            )
            if control is not None
            else None
        )

        reviewed_by = (
            getattr(
                control,
                "reviewed_by",
                None,
            )
            if control is not None
            else None
        )

        height = 92.0

        page = layout.ensure_space(
            height,
            repeated_title="RESPONSABILIDADES",
        )

        self._draw_section_title(
            page=page,
            layout=layout,
            title="10. RESPONSABILIDADES",
        )

        layout.advance(
            self.SECTION_TITLE_HEIGHT
        )

        box_height = 62.0
        gap = 12.0

        box_width = (
            layout.geometry.content_width
            - gap
        ) / 2

        y = layout.cursor_y

        entries = [
            (
                "Responsável técnico",
                prepared_by,
            ),
            (
                "Revisão / aprovação",
                reviewed_by,
            ),
        ]

        for index, (
            label,
            person,
        ) in enumerate(entries):
            x = (
                layout.geometry.margin_left
                + index
                * (
                    box_width
                    + gap
                )
            )

            rect = fitz.Rect(
                x,
                y,
                x + box_width,
                y + box_height,
            )

            page.draw_rect(
                rect,
                color=self.COLOR_BORDER,
                fill=(
                    1,
                    1,
                    1,
                ),
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 8,
                    rect.y0 + 7,
                    rect.x1 - 8,
                    rect.y0 + 20,
                ),
                self._clean_text(
                    person,
                    fallback=label,
                ),
                fontsize=6.3,
                fontname="hebo",
                color=self.COLOR_NAVY,
                align=fitz.TEXT_ALIGN_CENTER,
            )

            line_y = (
                rect.y1 - 20
            )

            page.draw_line(
                fitz.Point(
                    rect.x0 + 18,
                    line_y,
                ),
                fitz.Point(
                    rect.x1 - 18,
                    line_y,
                ),
                color=self.COLOR_BORDER,
                width=0.5,
            )

            page.insert_textbox(
                fitz.Rect(
                    rect.x0 + 5,
                    line_y + 4,
                    rect.x1 - 5,
                    rect.y1 - 3,
                ),
                label,
                fontsize=5.5,
                fontname="helv",
                color=self.COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        layout.advance(
            box_height
        )

    # =============================================================
    # TÍTULO
    # =============================================================

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
            color=(
                1,
                1,
                1,
            ),
        )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

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