"""
Motor de renderização de relatórios do METRA.

Esta camada é responsável por desacoplar o gerador de PDF
dos templates específicos, permitindo que cada tipo de
relatório tenha seu próprio renderizador.

Arquitetura:

report_engine/
│
├── report_context.py
├── layout_engine.py
├── base_renderer.py
├── template_registry.py
│
└── components/
    ├── institutional_header.py
    ├── page_footer.py
    └── section.py

Fluxo:

FinalReportGenerator
        │
        ▼
ReportTemplateRegistry
        │
        ▼
Renderer específico
        │
        ▼
Componentes reutilizáveis
"""

from services.report_engine.base_renderer import (
    BaseReportRenderer,
)

from services.report_engine.layout_engine import (
    PageGeometry,
    ReportLayoutEngine,
)

from services.report_engine.report_context import (
    ReportRenderContext,
)

from services.report_engine.template_registry import (
    ReportTemplateRegistry,
)

__all__ = [
    "BaseReportRenderer",
    "PageGeometry",
    "ReportLayoutEngine",
    "ReportRenderContext",
    "ReportTemplateRegistry",
]