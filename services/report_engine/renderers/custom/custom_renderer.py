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


class CustomRenderer(BaseReportRenderer):
    """
    Renderer definitivo do template Personalizado.

    O relatório é montado como um documento técnico narrativo:
    identificação automática + seções livres + evidências vinculadas
    + conteúdo estruturado opcional + controle técnico.

    Não cria páginas ou blocos artificiais apenas para preencher espaço.
    """

    template_code = PERSONALIZADO
    report_title = "RELATÓRIO TÉCNICO PERSONALIZADO"

    def __init__(
        self,
        *,
        base_dir: Path,
    ):
        super().__init__(
            base_dir=base_dir
        )

        self.cover_page = CustomCoverPage(
            base_dir=base_dir
        )
        self.content_page = CustomContentPage()
        self.technical_control_page = (
            CustomTechnicalControlPage()
        )

    def render_document(self) -> None:
        if self.layout is None:
            raise RuntimeError(
                "O motor de layout não foi inicializado."
            )

        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        # A capa devolve o próximo número de seção disponível.
        next_section = self.cover_page.render(
            layout=self.layout,
            render_context=self.render_context,
        )

        # As seções livres do Custom entram primeiro e fluem
        # naturalmente pela página. Documentos/características/
        # observações automáticas só entram quando realmente existirem
        # e estiverem habilitados.
        next_section = self.content_page.render(
            layout=self.layout,
            render_context=self.render_context,
            start_number=next_section,
        )

        # Controle técnico continua no fluxo atual; não força página nova.
        if self.section_enabled(
            "technical_control"
        ):
            self.technical_control_page.render(
                layout=self.layout,
                render_context=self.render_context,
                start_number=next_section,
            )