from __future__ import annotations

from pathlib import Path

from services.report_engine.base_renderer import (
    BaseReportRenderer,
)
from services.report_engine.renderers.dimensional_individual.cover_page import (
    DimensionalIndividualCoverPage,
)
from services.report_engine.renderers.dimensional_individual.measurement_page import (
    DimensionalIndividualMeasurementPage,
)
from services.report_engine.renderers.dimensional_individual.results_page import (
    DimensionalIndividualResultsPage,
)
from services.report_engine.renderers.dimensional_individual.technical_control_page import (
    DimensionalIndividualTechnicalControlPage,
)
from services.report_templates.template_catalog import (
    DIMENSIONAL_INDIVIDUAL,
)


class DimensionalIndividualRenderer(
    BaseReportRenderer
):
    """
    Renderizador definitivo do relatório dimensional individual.

    O renderer apenas coordena os módulos existentes. A paginação
    é responsabilidade do ReportLayoutEngine e de cada seção, para
    que o conteúdo aproveite o espaço restante antes de criar uma
    nova página.

    Ordem técnica:
    - identificação e resumo;
    - resultados dimensionais e análise gráfica;
    - medição, documentos, imagens e observações;
    - conclusão e controle técnico.

    O PDF original de medição é anexado posteriormente pelo fluxo
    de geração final, após o conteúdo técnico do METRA.
    """

    template_code = (
        DIMENSIONAL_INDIVIDUAL
    )

    report_title = (
        "RELATÓRIO TÉCNICO "
        "DE INSPEÇÃO DIMENSIONAL"
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
            DimensionalIndividualCoverPage(
                base_dir=base_dir
            )
        )

        self.results_page = (
            DimensionalIndividualResultsPage()
        )

        self.measurement_page = (
            DimensionalIndividualMeasurementPage()
        )

        self.technical_control_page = (
            DimensionalIndividualTechnicalControlPage()
        )

    # =============================================================
    # DOCUMENTO
    # =============================================================

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

        self._render_cover()

        if self.section_enabled(
            "characteristics"
        ):
            self._render_results()

        if self._has_measurement_content():
            self._render_measurement_and_evidence()

        if self.section_enabled(
            "technical_control"
        ):
            self._render_technical_control()

    # =============================================================
    # CAPA / RESUMO
    # =============================================================

    def _render_cover(
        self,
    ) -> None:
        self.cover_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )

    # =============================================================
    # RESULTADOS
    # =============================================================

    def _render_results(
        self,
    ) -> None:
        """
        Não força uma nova página.

        A própria ResultsPage utiliza ensure_space(), portanto o bloco
        começa na página atual quando houver espaço suficiente e migra
        automaticamente quando necessário.
        """

        self.results_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )

    # =============================================================
    # MEDIÇÃO E EVIDÊNCIAS
    # =============================================================

    def _render_measurement_and_evidence(
        self,
    ) -> None:
        """
        Mantém o fluxo contínuo do documento.

        Informações curtas podem ocupar o espaço restante da página
        anterior; tabelas, imagens e observações quebram de página
        somente quando o LayoutEngine determinar que é necessário.
        """

        self.measurement_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )

    def _has_measurement_content(
        self,
    ) -> bool:
        return any(
            [
                self.section_enabled(
                    "measurement"
                ),
                self.section_enabled(
                    "documents"
                ),
                self.section_enabled(
                    "images"
                ),
                self.section_enabled(
                    "observations"
                ),
            ]
        )

    # =============================================================
    # CONCLUSÃO E CONTROLE
    # =============================================================

    def _render_technical_control(
        self,
    ) -> None:
        """
        Também não força uma página exclusiva.

        A conclusão pode aproveitar o espaço livre da última página
        técnica. Se o bloco não couber, ensure_space() cria a página
        seguinte automaticamente.
        """

        self.technical_control_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )