from __future__ import annotations

from pathlib import Path
from typing import Type

from services.report_engine.base_renderer import (
    BaseReportRenderer,
)
from services.report_engine.renderers import (
    CustomRenderer,
    DimensionalBatchRenderer,
    DimensionalIndividualRenderer,
    TomographyRenderer,
)
from services.report_templates.template_catalog import (
    DIMENSIONAL_INDIVIDUAL,
    DIMENSIONAL_LOTE,
    PERSONALIZADO,
    TOMOGRAFIA_INDUSTRIAL,
)


class ReportTemplateRegistry:
    """
    Registro central dos renderizadores oficiais do METRA.
    """

    def __init__(
        self,
    ):
        self._renderers: dict[
            str,
            Type[BaseReportRenderer],
        ] = {}

        self._register_default_renderers()

    def _register_default_renderers(
        self,
    ) -> None:
        self.register(
            DIMENSIONAL_INDIVIDUAL,
            DimensionalIndividualRenderer,
        )
        self.register(
            DIMENSIONAL_LOTE,
            DimensionalBatchRenderer,
        )
        self.register(
            TOMOGRAFIA_INDUSTRIAL,
            TomographyRenderer,
        )
        self.register(
            PERSONALIZADO,
            CustomRenderer,
        )

    def register(
        self,
        template_code: str,
        renderer_class: Type[
            BaseReportRenderer
        ],
    ) -> None:
        code = str(
            template_code
            or ""
        ).strip()

        if not code:
            raise ValueError(
                "O código do template não pode ser vazio."
            )

        if not issubclass(
            renderer_class,
            BaseReportRenderer,
        ):
            raise TypeError(
                (
                    "O renderizador precisa herdar "
                    "de BaseReportRenderer."
                )
            )

        self._renderers[
            code
        ] = renderer_class

    def resolve(
        self,
        template_code: str,
    ) -> Type[
        BaseReportRenderer
    ]:
        code = str(
            template_code
            or PERSONALIZADO
        ).strip()

        renderer_class = (
            self._renderers.get(
                code
            )
        )

        if renderer_class is not None:
            return renderer_class

        fallback_renderer = (
            self._renderers.get(
                PERSONALIZADO
            )
        )

        if fallback_renderer is not None:
            return fallback_renderer

        raise ValueError(
            (
                "Nenhum renderizador foi registrado "
                f"para o template: {code}"
            )
        )

    def create(
        self,
        template_code: str,
        *,
        base_dir: Path,
    ) -> BaseReportRenderer:
        renderer_class = self.resolve(
            template_code
        )

        return renderer_class(
            base_dir=base_dir
        )