from __future__ import annotations

from pathlib import Path

from services.report_engine.base_renderer import (
    BaseReportRenderer,
)
from services.report_engine.renderers.dimensional_batch.cover_page import (
    DimensionalBatchCoverPage,
)
from services.report_engine.renderers.dimensional_batch.statistics_page import (
    DimensionalBatchStatisticsPage,
)
from services.report_engine.renderers.dimensional_batch.charts_page import (
    DimensionalBatchChartsPage,
)
from services.report_engine.renderers.dimensional_batch.evidence_page import (
    DimensionalBatchEvidencePage,
)
from services.report_engine.renderers.dimensional_batch.technical_control_page import (
    DimensionalBatchTechnicalControlPage,
)
from services.report_templates.template_catalog import (
    DIMENSIONAL_LOTE,
)


class DimensionalBatchRenderer(
    BaseReportRenderer
):
    """
    Renderizador consolidado do relatório dimensional em lote.

    O conteúdo flui pela página atual e o ReportLayoutEngine cria
    novas páginas apenas quando realmente necessário.
    """

    template_code = DIMENSIONAL_LOTE

    report_title = (
        "RELATÓRIO ESTATÍSTICO "
        "DE INSPEÇÃO DIMENSIONAL EM LOTE"
    )

    def __init__(
        self,
        *,
        base_dir: Path,
    ):
        super().__init__(
            base_dir=base_dir
        )

        self.cover_page = (
            DimensionalBatchCoverPage(
                base_dir=base_dir
            )
        )

        self.statistics_page = (
            DimensionalBatchStatisticsPage()
        )

        self.charts_page = (
            DimensionalBatchChartsPage()
        )

        self.evidence_page = (
            DimensionalBatchEvidencePage()
        )

        self.technical_control_page = (
            DimensionalBatchTechnicalControlPage()
        )

    def render_document(
        self,
    ) -> None:
        if self.layout is None:
            raise RuntimeError(
                "O motor de layout não foi inicializado."
            )

        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        self.cover_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )

        if self.section_enabled(
            "characteristics"
        ):
            self.statistics_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )

            self.charts_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )

        if self.section_enabled(
            "images"
        ):
            self.evidence_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )

        if self.section_enabled(
            "technical_control"
        ):
            self.technical_control_page.render(
                layout=self.layout,
                render_context=self.render_context,
            )