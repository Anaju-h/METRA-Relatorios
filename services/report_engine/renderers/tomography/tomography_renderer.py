from __future__ import annotations

from pathlib import Path

from services.report_engine.base_renderer import BaseReportRenderer
from services.report_engine.renderers.tomography.analysis_page import TomographyAnalysisPage
from services.report_engine.renderers.tomography.cover_page import TomographyCoverPage
from services.report_engine.renderers.tomography.findings_page import TomographyFindingsPage
from services.report_engine.renderers.tomography.technical_control_page import TomographyTechnicalControlPage
from services.report_templates.template_catalog import TOMOGRAFIA_INDUSTRIAL


class TomographyRenderer(BaseReportRenderer):
    """Renderizador consolidado do relatório de tomografia industrial."""

    template_code = TOMOGRAFIA_INDUSTRIAL
    report_title = "RELATÓRIO TÉCNICO DE TOMOGRAFIA INDUSTRIAL"

    def __init__(self, *, base_dir: Path):
        super().__init__(base_dir=base_dir)
        self.cover_page = TomographyCoverPage(base_dir=base_dir)
        self.analysis_page = TomographyAnalysisPage()
        self.findings_page = TomographyFindingsPage()
        self.technical_control_page = TomographyTechnicalControlPage()

    def render_document(self) -> None:
        if self.layout is None:
            raise RuntimeError("O motor de layout não foi inicializado.")
        if self.render_context is None:
            raise RuntimeError("O contexto do relatório não foi definido.")

        self.cover_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )

        if self._analysis_enabled():
            self.analysis_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )

        if self._findings_enabled():
            self.findings_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )

        if self.section_enabled("technical_control"):
            self.technical_control_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )

    def _analysis_enabled(self) -> bool:
        return any(
            self.section_enabled(key)
            for key in (
                "measurement",
                "documents",
                "images",
                "observations",
            )
        )

    def _findings_enabled(self) -> bool:
        if self.render_context is None:
            return False
        return bool(self.render_context.findings) or self.section_enabled(
            "observations"
        )