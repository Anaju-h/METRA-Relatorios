from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import fitz

from services.report_engine.components.institutional_header import (
    InstitutionalHeader,
)
from services.report_engine.components.page_footer import (
    PageFooter,
)
from services.report_engine.layout_engine import (
    PageGeometry,
    ReportLayoutEngine,
)
from services.report_engine.report_context import (
    ReportRenderContext,
)


class BaseReportRenderer(ABC):
    """
    Classe-base de todos os renderizadores de relatório do METRA.

    Cada template específico herda desta classe e implementa
    apenas a ordem e o conteúdo das seções técnicas.
    """

    template_code: str = "PERSONALIZADO"

    report_title: str = (
        "RELATÓRIO TÉCNICO"
    )

    def __init__(
        self,
        *,
        base_dir: Path,
    ):
        self.base_dir = base_dir

        self.document: fitz.Document | None = None

        self.layout: ReportLayoutEngine | None = None

        self.render_context: (
            ReportRenderContext
            | None
        ) = None

        self.geometry = PageGeometry()

        self.header = InstitutionalHeader(
            base_dir=base_dir
        )

        self.footer = PageFooter()

    # =============================================================
    # RENDERIZAÇÃO PRINCIPAL
    # =============================================================

    def render(
        self,
        document: fitz.Document,
        render_context: ReportRenderContext,
    ) -> None:
        """
        Executa o fluxo completo do template.

        A versão continua existindo internamente no projeto mesmo
        quando não é exibida no documento entregue.
        """

        self.document = document

        self.render_context = render_context

        self.layout = ReportLayoutEngine(
            document=document,
            geometry=self.geometry,
            page_initializer=(
                self._initialize_page
            ),
        )

        self.layout.new_page()

        self.render_document()

        self.footer.apply(
            document=document,
            report_id=(
                self.project.report_id
            ),
            version=(
                self.project.version
                or "V1.0"
            ),
            show_version=(
                self.section_enabled(
                    "show_version"
                )
            ),
            page_width=(
                self.geometry.width
            ),
            page_height=(
                self.geometry.height
            ),
            margin_left=(
                self.geometry.margin_left
            ),
            margin_right=(
                self.geometry.margin_right
            ),
        )

    @abstractmethod
    def render_document(
        self,
    ) -> None:
        """
        Implementa o conteúdo específico do template.
        """

        raise NotImplementedError

    # =============================================================
    # INICIALIZAÇÃO DE PÁGINA
    # =============================================================

    def _initialize_page(
        self,
        page: fitz.Page,
        section_title: str | None,
    ) -> float:
        """
        Desenha o cabeçalho institucional de cada página.
        """

        report_title = self.report_title

        if section_title:
            report_title = (
                f"{report_title} · "
                f"{section_title}"
            )

        return self.header.draw(
            page=page,
            x0=(
                self.geometry.margin_left
            ),
            x1=(
                self.geometry.width
                - self.geometry.margin_right
            ),
            y=(
                self.geometry.margin_top
            ),
            report_title=report_title,
        )

    # =============================================================
    # ACESSO SEGURO
    # =============================================================

    @property
    def current_page(
        self,
    ) -> fitz.Page:
        if (
            self.layout is None
            or self.layout.current_page is None
        ):
            raise RuntimeError(
                "Nenhuma página está ativa no relatório."
            )

        return self.layout.current_page

    @property
    def project(
        self,
    ):
        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        return self.render_context.project

    @property
    def context(
        self,
    ) -> dict:
        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        return self.render_context.context

    @property
    def sections(
        self,
    ) -> dict[str, bool]:
        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        return self.render_context.sections

    @property
    def statistics(
        self,
    ) -> dict:
        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        return self.render_context.statistics

    @property
    def charts(
        self,
    ) -> dict:
        if self.render_context is None:
            raise RuntimeError(
                "O contexto do relatório não foi definido."
            )

        return self.render_context.charts

    # =============================================================
    # HELPERS DE CONTEXTO
    # =============================================================

    def section_enabled(
        self,
        key: str,
    ) -> bool:
        if self.render_context is None:
            return False

        return self.render_context.section_enabled(
            key
        )

    def ensure_space(
        self,
        required_height: float,
        *,
        repeated_title: str | None = None,
    ) -> fitz.Page:
        if self.layout is None:
            raise RuntimeError(
                "O motor de layout não foi inicializado."
            )

        return self.layout.ensure_space(
            required_height,
            repeated_title=repeated_title,
        )

    def advance(
        self,
        height: float,
    ) -> None:
        if self.layout is None:
            raise RuntimeError(
                "O motor de layout não foi inicializado."
            )

        self.layout.advance(
            height
        )

    # =============================================================
    # TEXTO
    # =============================================================

    def clean_text(
        self,
        value,
        *,
        fallback: str = "Não informado",
    ) -> str:
        if value is None:
            return fallback

        cleaned = " ".join(
            str(
                value
            ).split()
        )

        return (
            cleaned
            or fallback
        )

    def has_text(
        self,
        value,
    ) -> bool:
        return bool(
            str(
                value
                or ""
            ).strip()
        )