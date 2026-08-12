from pathlib import Path

from services.document_analysis.analyzer import (
    DocumentAnalyzer,
)
from services.document_analysis.models import (
    ParsedCharacteristic,
    ParsedReport,
)


class CalypsoParser:
    """
    Fachada temporária de compatibilidade.

    A extração documental agora é realizada pelo DocumentAnalyzer.

    Esta classe permanece temporariamente para evitar quebra
    de partes antigas da aplicação que ainda utilizem:

        CalypsoParser().parse(...)

    Quando toda a aplicação estiver migrada para DocumentAnalyzer,
    este arquivo poderá ser removido.
    """

    def __init__(self):
        self.document_analyzer = (
            DocumentAnalyzer()
        )

    def parse(
        self,
        pdf_path: str | Path,
    ) -> ParsedReport:
        report = (
            self.document_analyzer
            .analyze(
                pdf_path
            )
        )

        if (
            report.source_type
            != "CALYPSO"
        ):
            raise ValueError(
                (
                    "O documento informado não foi identificado "
                    "como relatório CALYPSO."
                )
            )

        return report


__all__ = [
    "CalypsoParser",
    "ParsedCharacteristic",
    "ParsedReport",
]