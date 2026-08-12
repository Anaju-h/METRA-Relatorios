from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import fitz

from models.project import Project
from services.report_chart_service import ReportChartService
from services.report_engine.report_context import ReportRenderContext
from services.report_engine.template_registry import ReportTemplateRegistry
from services.report_statistics_service import ReportStatisticsService
from services.report_templates.template_catalog import (
    DIMENSIONAL_INDIVIDUAL,
    DIMENSIONAL_LOTE,
    PERSONALIZADO,
    TOMOGRAFIA_INDUSTRIAL,
)


BASE_DIR = Path(__file__).resolve().parent.parent


class FinalReportGenerator:
    """
    Orquestra a geração do relatório técnico final.

    O conteúdo METRA é renderizado primeiro. Para templates que exigem
    rastreabilidade documental, os PDFs de origem são anexados ao final
    do mesmo documento.
    """

    TEMPLATES_WITH_SOURCE_APPENDIX = {
        DIMENSIONAL_INDIVIDUAL,
        DIMENSIONAL_LOTE,
        TOMOGRAFIA_INDUSTRIAL,
        PERSONALIZADO,
    }

    def __init__(self) -> None:
        self.statistics_service = ReportStatisticsService()
        self.chart_service = ReportChartService()
        self.template_registry = ReportTemplateRegistry()

    def generate(
        self,
        project: Project,
        context: dict[str, Any],
        sections: dict[str, bool],
        output_path: str | Path,
    ) -> Path:
        if project.id is None:
            raise ValueError(
                "O processo não possui um identificador válido."
            )

        destination = self._prepare_destination(
            output_path
        )

        statistics = (
            self.statistics_service
            .build_statistics(
                context
            )
        )

        temporary_directory = Path(
            tempfile.mkdtemp(
                prefix="metra_report_"
            )
        )

        document: fitz.Document | None = None

        try:
            charts = (
                self.chart_service
                .generate_charts(
                    statistics=statistics,
                    output_directory=temporary_directory,
                    maximum_characteristic_charts=8,
                )
            )

            render_context = ReportRenderContext(
                project=project,
                context=context,
                sections=sections,
                statistics=statistics,
                charts=charts,
                temporary_directory=temporary_directory,
                output_path=destination,
            )

            renderer = (
                self.template_registry
                .create(
                    render_context.template_code,
                    base_dir=BASE_DIR,
                )
            )

            document = fitz.open()

            renderer.render(
                document=document,
                render_context=render_context,
            )

            self._append_source_documents(
                document=document,
                render_context=render_context,
            )

            self._apply_metadata(
                document=document,
                project=project,
            )

            if destination.exists():
                destination.unlink()

            document.save(
                str(
                    destination
                ),
                garbage=4,
                deflate=True,
                clean=True,
            )

            return destination

        finally:
            if document is not None:
                document.close()

            if temporary_directory.exists():
                shutil.rmtree(
                    temporary_directory,
                    ignore_errors=True,
                )

    # =============================================================
    # ANEXOS DE ORIGEM
    # =============================================================

    def _append_source_documents(
        self,
        *,
        document: fitz.Document,
        render_context: ReportRenderContext,
    ) -> None:
        if (
            render_context.template_code
            not in self.TEMPLATES_WITH_SOURCE_APPENDIX
        ):
            return

        source_documents = (
            self._resolve_source_document_paths(
                render_context
            )
        )

        if not source_documents:
            return

        for source_path in source_documents:
            source_document: fitz.Document | None = None

            try:
                source_document = fitz.open(
                    source_path
                )

                if source_document.page_count <= 0:
                    continue

                document.insert_pdf(
                    source_document
                )

            except Exception:
                # O relatório METRA não deve deixar de ser gerado
                # caso um anexo físico esteja temporariamente
                # indisponível ou corrompido.
                continue

            finally:
                if source_document is not None:
                    source_document.close()

    def _resolve_source_document_paths(
        self,
        render_context: ReportRenderContext,
    ) -> list[Path]:
        resolved: list[Path] = []

        seen: set[str] = set()

        for source in render_context.documents:
            raw_path = getattr(
                source,
                "file_path",
                None,
            )

            if not raw_path:
                continue

            path = Path(
                str(
                    raw_path
                )
            )

            if (
                not path.exists()
                or not path.is_file()
                or path.suffix.lower() != ".pdf"
            ):
                continue

            key = str(
                path.resolve()
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            resolved.append(
                path
            )

        return resolved

    # =============================================================
    # DESTINO
    # =============================================================

    def _prepare_destination(
        self,
        output_path: str | Path,
    ) -> Path:
        destination = Path(
            output_path
        )

        if destination.suffix.lower() != ".pdf":
            destination = destination.with_suffix(
                ".pdf"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        return destination

    # =============================================================
    # METADADOS
    # =============================================================

    def _apply_metadata(
        self,
        *,
        document: fitz.Document,
        project: Project,
    ) -> None:
        document.set_metadata(
            {
                "title":
                    (
                        f"{project.report_id} - "
                        f"{project.name}"
                    ),

                "author":
                    (
                        "Centro de Excelência "
                        "em Metrologia"
                    ),

                "subject":
                    (
                        "Relatório técnico consolidado "
                        "de metrologia"
                    ),

                "keywords":
                    (
                        "metrologia, inspeção, estatística, "
                        "ZEISS, SENAI"
                    ),

                "creator":
                    (
                        "METRA — Sistema Inteligente de "
                        "Pós-processamento de Relatórios"
                    ),
            }
        )