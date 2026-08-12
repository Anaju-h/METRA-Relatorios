from __future__ import annotations

from pathlib import Path

from services.report_engine.base_renderer import (
    BaseReportRenderer,
)
from services.report_engine.renderers.custom.content_page import (
    CustomContentPage,
)
from services.report_engine.renderers.custom.cover_page import (
    CustomCoverPage,
)
from services.report_engine.renderers.custom.technical_control_page import (
    CustomTechnicalControlPage,
)
from services.report_templates.template_catalog import (
    PERSONALIZADO,
)


class CustomRenderer(
    BaseReportRenderer
):
    """
    Renderizador consolidado do relatório personalizado.

    O conteúdo flui pela página atual e o ReportLayoutEngine
    cria novas páginas apenas quando realmente necessário.
    """

    template_code = PERSONALIZADO

    report_title = (
        "RELATÓRIO TÉCNICO PERSONALIZADO"
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
            CustomCoverPage(
                base_dir=base_dir
            )
        )

        self.content_page = (
            CustomContentPage()
        )

        self.technical_control_page = (
            CustomTechnicalControlPage()
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

        has_content = any(
            [
                bool(
                    self.render_context.documents
                ),
                bool(
                    self.render_context.statistical_groups
                ),
                bool(
                    self.render_context.additional_images
                ),
                bool(
                    self.render_context.get_context_value(
                        "custom_observations"
                    )
                ),
                bool(
                    self.render_context.get_context_value(
                        "observations"
                    )
                ),
            ]
        )

        if has_content:
            self.content_page.render(
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