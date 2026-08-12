from __future__ import annotations

import re
import traceback
from pathlib import Path
from typing import Callable

from services.document_analysis.anchor_engine import (
    AnchorEngine,
)
from services.document_analysis.models import (
    DocumentContent,
    ExtractedField,
    ParsedReport,
)
from services.document_analysis.pdf_reader import (
    PDFReader,
)
from services.document_analysis.result_merger import (
    ResultMerger,
)
from services.document_analysis.source_detector import (
    SourceDetector,
)
from services.document_analysis.table_engine import (
    TableEngine,
)
from services.document_analysis.validator import (
    DocumentValidator,
)


class DocumentAnalyzer:
    """
    Coordenador principal do motor documental.

    Pipeline:

        PDFReader
        ↓
        SourceDetector
        ↓
        Perfil documental
        ↓
        AnchorEngine
        ↓
        Fallbacks documentais
        ↓
        TableEngine
        ↓
        ResultMerger
        ↓
        Validator
        ↓
        ParsedReport
    """

    def __init__(self):
        self.pdf_reader = PDFReader()

        self.source_detector = (
            SourceDetector()
        )

        self.anchor_engine = (
            AnchorEngine()
        )

        self.table_engine = (
            TableEngine()
        )

        self.result_merger = (
            ResultMerger()
        )

        self.validator = (
            DocumentValidator()
        )

    # =============================================================
    # API PRINCIPAL
    # =============================================================

    def analyze(
        self,
        source_path: str | Path,
    ) -> ParsedReport:
        """
        Executa o pipeline completo.

        O traceback real é impresso no terminal antes da exceção
        continuar para a interface.
        """

        try:
            return self._analyze_internal(
                source_path
            )

        except Exception:
            print(
                "\n"
                "====================================================\n"
                "ERRO NO MOTOR DOCUMENTAL\n"
                "===================================================="
            )

            print(
                f"Arquivo: {source_path}"
            )

            traceback.print_exc()

            print(
                "====================================================\n"
            )

            raise

    # =============================================================
    # PIPELINE
    # =============================================================

    def _analyze_internal(
        self,
        source_path: str | Path,
    ) -> ParsedReport:
        # ---------------------------------------------------------
        # 1. LEITURA DO PDF
        # ---------------------------------------------------------

        document = (
            self.pdf_reader.read(
                source_path
            )
        )

        # ---------------------------------------------------------
        # 2. IDENTIFICAÇÃO DA FAMÍLIA
        # ---------------------------------------------------------

        detection = (
            self.source_detector.detect(
                document
            )
        )

        if (
            detection.source_type
            == SourceDetector.UNKNOWN
            or detection.profile is None
        ):
            raise ValueError(
                (
                    "Não foi possível identificar com confiança "
                    "a família deste relatório."
                )
            )

        profile = detection.profile

        # ---------------------------------------------------------
        # 3. CAMPOS POR ÂNCORA
        # ---------------------------------------------------------

        fields = (
            self._extract_fields(
                document=document,
                profile=profile,
            )
        )

        # ---------------------------------------------------------
        # 4. FALLBACKS DOCUMENTAIS
        # ---------------------------------------------------------

        self._apply_document_fallbacks(
            document=document,
            profile=profile,
            fields=fields,
        )

        # ---------------------------------------------------------
        # 5. TABELAS / RESULTADOS
        # ---------------------------------------------------------

        table_results = (
            self.table_engine.extract(
                document=document,
                profile=profile,
            )
        )

        characteristics = (
            self.result_merger
            .merge_characteristics(
                table_results
            )
        )

        # ---------------------------------------------------------
        # 6. SOFTWARE
        # ---------------------------------------------------------

        software_name = getattr(
            profile,
            "SOFTWARE_NAME",
            None,
        )

        software_version = (
            self._extract_software_version(
                document=document,
                profile=profile,
            )
        )

        # ---------------------------------------------------------
        # 7. TIPO DE ANÁLISE
        # ---------------------------------------------------------

        analysis_type = (
            self._detect_analysis_type(
                document=document,
                profile=profile,
            )
        )

        # ---------------------------------------------------------
        # 8. RELATÓRIO PADRONIZADO
        # ---------------------------------------------------------

        report = ParsedReport(
            source_type=(
                detection.source_type
            ),

            document_title=(
                self._field_value(
                    fields,
                    "document_title",
                )
            ),

            analysis_type=(
                analysis_type
            ),

            part_name=(
                self._field_value(
                    fields,
                    "part_name",
                )
            ),

            part_number=(
                self._field_value(
                    fields,
                    "part_number",
                )
            ),

            machine_name=(
                self._field_value(
                    fields,
                    "machine_name",
                )
            ),

            machine_number=(
                self._field_value(
                    fields,
                    "machine_number",
                )
            ),

            operator=(
                self._field_value(
                    fields,
                    "operator",
                )
            ),

            measurement_datetime=(
                self._field_value(
                    fields,
                    "measurement_datetime",
                )
            ),

            measurement_count=(
                self._field_int(
                    fields,
                    "measurement_count",
                )
            ),

            out_of_tolerance_count=(
                self._field_int(
                    fields,
                    "out_of_tolerance_count",
                )
            ),

            measurement_duration=(
                self._field_value(
                    fields,
                    "measurement_duration",
                )
            ),

            software_name=(
                software_name
            ),

            software_version=(
                software_version
            ),

            alignment=(
                self._field_value(
                    fields,
                    "alignment",
                )
            ),

            length_unit=(
                self._field_value(
                    fields,
                    "length_unit",
                )
            ),

            page_count=(
                document.page_count
            ),

            characteristics=(
                characteristics
            ),

            fields=fields,

            extra_data={
                "source_detection_confidence":
                    detection.confidence,

                "source_detection_evidence":
                    detection.evidence,

                "table_strategies": [
                    {
                        "method":
                            result.method,

                        "confidence":
                            result.confidence,

                        "count":
                            len(
                                result.characteristics
                            ),

                        "warnings":
                            result.warnings,
                    }

                    for result in (
                        table_results
                    )
                ],
            },
        )

        # ---------------------------------------------------------
        # 9. NORMALIZAÇÃO
        # ---------------------------------------------------------

        report = (
            self._normalize_report(
                report=report,
                profile=profile,
            )
        )

        # ---------------------------------------------------------
        # 10. VALIDAÇÃO
        # ---------------------------------------------------------

        report.validation = (
            self.validator.validate(
                report
            )
        )

        report.warnings = [
            issue.message
            for issue
            in report.validation.issues
        ]

        return report

    # =============================================================
    # EXTRAÇÃO DOS CAMPOS
    # =============================================================

    def _extract_fields(
        self,
        document: DocumentContent,
        profile: type,
    ) -> dict[
        str,
        ExtractedField,
    ]:
        fields = {}

        field_anchors = getattr(
            profile,
            "FIELD_ANCHORS",
            {},
        )

        for (
            field_name,
            anchors,
        ) in field_anchors.items():
            exclusions = (
                self._get_exclusions(
                    profile=profile,
                    field_name=(
                        field_name
                    ),
                )
            )

            validator = (
                self._get_field_validator(
                    field_name=(
                        field_name
                    ),
                    profile=profile,
                )
            )

            scorer = (
                self._get_candidate_scorer(
                    field_name=(
                        field_name
                    ),
                    profile=profile,
                )
            )

            extracted = (
                self.anchor_engine
                .extract_field(
                    document=document,
                    anchors=anchors,
                    exclusions=(
                        exclusions
                    ),
                    validator=(
                        validator
                    ),
                    candidate_scorer=(
                        scorer
                    ),
                )
            )

            if (
                extracted.found
                and extracted.confidence
                < 0.40
            ):
                extracted.warnings.append(
                    (
                        "Valor identificado "
                        "com baixa confiança."
                    )
                )

            fields[
                field_name
            ] = extracted

        return fields

    # =============================================================
    # FALLBACKS
    # =============================================================

    def _apply_document_fallbacks(
        self,
        document: DocumentContent,
        profile: type,
        fields: dict[
            str,
            ExtractedField,
        ],
    ) -> None:
        self._fallback_equipment(
            document=document,
            profile=profile,
            fields=fields,
        )

        self._fallback_part_name(
            document=document,
            profile=profile,
            fields=fields,
        )

    # =============================================================
    # FALLBACK — EQUIPAMENTO
    # =============================================================

    def _fallback_equipment(
        self,
        document: DocumentContent,
        profile: type,
        fields: dict[
            str,
            ExtractedField,
        ],
    ) -> None:
        current = fields.get(
            "machine_name"
        )

        # Resultado forte já encontrado por âncora.
        if (
            current is not None
            and current.found
            and current.confidence
            >= 0.80
        ):
            return

        finder = getattr(
            profile,
            "find_equipment_in_text",
            None,
        )

        if finder is None:
            return

        equipment = finder(
            document.full_text
        )

        if not equipment:
            return

        fallback = ExtractedField(
            value=equipment,

            confidence=0.95,

            method=(
                "global_equipment"
            ),

            source_page=None,

            source_text=(
                equipment
            ),
        )

        if (
            current is None
            or not current.found
            or fallback.confidence
            > current.confidence
        ):
            fields[
                "machine_name"
            ] = fallback

    # =============================================================
    # FALLBACK — NOME DA PEÇA
    # =============================================================

    def _fallback_part_name(
        self,
        document: DocumentContent,
        profile: type,
        fields: dict[
            str,
            ExtractedField,
        ],
    ) -> None:
        current = fields.get(
            "part_name"
        )

        # Se o AnchorEngine encontrou um resultado realmente forte,
        # não substituímos.
        if (
            current is not None
            and current.found
            and current.confidence
            >= 0.82
            and self._validate_part_name(
                str(
                    current.value
                )
            )
        ):
            return

        finder = getattr(
            profile,
            "find_part_name_in_text",
            None,
        )

        if finder is None:
            return

        part_name = finder(
            document.full_text
        )

        if not part_name:
            return

        if not self._validate_part_name(
            part_name
        ):
            return

        fallback = ExtractedField(
            value=part_name,

            confidence=0.94,

            method=(
                "global_part_name"
            ),

            source_page=None,

            source_text=(
                part_name
            ),
        )

        if (
            current is None
            or not current.found
            or fallback.confidence
            > current.confidence
        ):
            fields[
                "part_name"
            ] = fallback

    # =============================================================
    # EXCLUSÕES
    # =============================================================

    def _get_exclusions(
        self,
        profile: type,
        field_name: str,
    ) -> tuple[str, ...]:
        getter = getattr(
            profile,
            "get_field_exclusions",
            None,
        )

        if getter is None:
            return tuple()

        return getter(
            field_name
        )

    # =============================================================
    # VALIDADORES
    # =============================================================

    def _get_field_validator(
        self,
        field_name: str,
        profile: type,
    ) -> Callable[
        [str],
        bool,
    ] | None:
        if field_name in (
            "measurement_count",
            "out_of_tolerance_count",
        ):
            return (
                self._validate_integer
            )

        if (
            field_name
            == "machine_number"
        ):
            return (
                self._validate_machine_number
            )

        if (
            field_name
            == "machine_name"
        ):
            return (
                lambda value:
                self._validate_machine_name(
                    value=value,
                    profile=profile,
                )
            )

        if (
            field_name
            == "part_name"
        ):
            return (
                self._validate_part_name
            )

        if (
            field_name
            == "measurement_datetime"
        ):
            return (
                self._validate_datetime_candidate
            )

        if field_name in (
            "operator",
            "part_number",
            "document_title",
            "alignment",
            "length_unit",
        ):
            return (
                self._validate_short_text
            )

        return None

    # =============================================================
    # SCORERS
    # =============================================================

    def _get_candidate_scorer(
        self,
        field_name: str,
        profile: type,
    ) -> Callable[
        [str],
        float,
    ] | None:
        if (
            field_name
            == "machine_name"
        ):
            return (
                lambda value:
                self._score_machine_name(
                    value=value,
                    profile=profile,
                )
            )

        if (
            field_name
            == "machine_number"
        ):
            return (
                self._score_machine_number
            )

        if (
            field_name
            == "part_name"
        ):
            return (
                self._score_part_name
            )

        if field_name in (
            "measurement_count",
            "out_of_tolerance_count",
        ):
            return (
                self._score_integer
            )

        return None

    # =============================================================
    # MACHINE NAME
    # =============================================================

    def _validate_machine_name(
        self,
        value: str,
        profile: type,
    ) -> bool:
        clean = (
            value.strip()
        )

        if not clean:
            return False

        if len(clean) > 120:
            return False

        if re.fullmatch(
            r"[\d\s\-_.]+",
            clean,
        ):
            return False

        upper = (
            clean.upper()
        )

        invalid = (
            "NÚMERO DA MMC",
            "NUMERO DA MMC",
            "OPERADOR",
            "DATA/HORA",
        )

        if any(
            item in upper
            for item in invalid
        ):
            return False

        return True

    def _score_machine_name(
        self,
        value: str,
        profile: type,
    ) -> float:
        clean = (
            value.strip()
        )

        score = 0.0

        known_checker = getattr(
            profile,
            "is_known_equipment",
            None,
        )

        if (
            known_checker
            and known_checker(
                clean
            )
        ):
            score += 42.0

        if re.search(
            r"[A-Za-zÀ-ÿ]",
            clean,
        ):
            score += 4.0

        if re.fullmatch(
            r"[\d\s\-_.]+",
            clean,
        ):
            score -= 80.0

        return score

    # =============================================================
    # MACHINE NUMBER
    # =============================================================

    def _validate_machine_number(
        self,
        value: str,
    ) -> bool:
        clean = (
            value.strip()
        )

        if not clean:
            return False

        return (
            re.search(
                r"\d",
                clean,
            )
            is not None
        )

    def _score_machine_number(
        self,
        value: str,
    ) -> float:
        clean = (
            value.strip()
        )

        digits = re.sub(
            r"\D",
            "",
            clean,
        )

        score = 0.0

        if digits:
            score += 8.0

        if len(digits) >= 5:
            score += 15.0

        if len(digits) >= 8:
            score += 8.0

        if re.fullmatch(
            r"[\d\s\-_.]+",
            clean,
        ):
            score += 15.0

        return score

    # =============================================================
    # PART NAME
    # =============================================================

    def _validate_part_name(
        self,
        value: str,
    ) -> bool:
        clean = (
            value.strip()
        )

        if not clean:
            return False

        if len(clean) > 220:
            return False

        normalized = (
            clean.upper()
            .strip()
        )

        exact_invalid = {
            "DA MMC",
            "MMC",

            "DA PEÇA",
            "DA PECA",

            "DO OPERADOR",
            "OPERADOR",

            "DATA/HORA",

            "NOME",
            "PEÇA",
            "PECA",

            "MASTER",
        }

        if (
            normalized
            in exact_invalid
        ):
            return False

        contains_invalid = (
            "NOME DA MMC",
            "NUMERO DA MMC",
            "NÚMERO DA MMC",

            "DURAÇÃO DA MEDIÇÃO",
            "DURACAO DA MEDICAO",

            "LAST 1 MEASUREMENTS",

            "APPROVAL",
        )

        if any(
            item in normalized
            for item in contains_invalid
        ):
            return False

        if not re.search(
            r"[A-Za-zÀ-ÿ]",
            clean,
        ):
            return False

        return True

    def _score_part_name(
        self,
        value: str,
    ) -> float:
        clean = (
            value.strip()
        )

        normalized = (
            clean.upper()
        )

        score = 0.0

        if (
            4
            <= len(clean)
            <= 120
        ):
            score += 8.0

        if re.search(
            r"[A-Za-zÀ-ÿ]",
            clean,
        ):
            score += 5.0

        if (
            re.search(
                r"[A-Za-zÀ-ÿ]",
                clean,
            )
            and re.search(
                r"\d",
                clean,
            )
        ):
            score += 4.0

        bad_values = (
            "DA MMC",
            "DA PECA",
            "DA PEÇA",
            "OPERADOR",
            "CALYPSO",
            "MASTER",
        )

        if normalized in (
            bad_values
        ):
            score -= 100.0

        return score

    # =============================================================
    # INTEGER
    # =============================================================

    def _validate_integer(
        self,
        value: str,
    ) -> bool:
        return (
            re.search(
                r"\d+",
                value,
            )
            is not None
        )

    def _score_integer(
        self,
        value: str,
    ) -> float:
        clean = (
            value.strip()
        )

        if re.fullmatch(
            r"\d+",
            clean,
        ):
            return 20.0

        if re.search(
            r"\d+",
            clean,
        ):
            return 4.0

        return -50.0

    # =============================================================
    # OUTROS VALIDADORES
    # =============================================================

    def _validate_datetime_candidate(
        self,
        value: str,
    ) -> bool:
        clean = (
            value.strip()
        )

        if not clean:
            return False

        return (
            re.search(
                r"\d",
                clean,
            )
            is not None
        )

    def _validate_short_text(
        self,
        value: str,
    ) -> bool:
        clean = (
            value.strip()
        )

        return (
            bool(clean)
            and len(clean)
            <= 180
        )

    # =============================================================
    # SOFTWARE VERSION
    # =============================================================

    def _extract_software_version(
        self,
        document: DocumentContent,
        profile: type,
    ) -> str | None:
        text = (
            document.full_text
        )

        patterns = getattr(
            profile,
            "SOFTWARE_VERSION_PATTERNS",
            None,
        )

        if patterns:
            for pattern in patterns:
                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE,
                )

                if not match:
                    continue

                if match.groups():
                    return (
                        match.group(1)
                    )

                return (
                    match.group()
                )

        pattern = getattr(
            profile,
            "SOFTWARE_VERSION_PATTERN",
            None,
        )

        if pattern:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                if match.groups():
                    return (
                        match.group(1)
                    )

                return (
                    match.group()
                )

        return None

    # =============================================================
    # ANALYSIS TYPE
    # =============================================================

    def _detect_analysis_type(
        self,
        document: DocumentContent,
        profile: type,
    ) -> str | None:
        detector = getattr(
            profile,
            "detect_analysis_type",
            None,
        )

        if detector is None:
            return None

        try:
            return detector(
                document.full_text
            )

        except Exception:
            return None

    # =============================================================
    # NORMALIZAÇÃO
    # =============================================================

    def _normalize_report(
        self,
        report: ParsedReport,
        profile: type,
    ) -> ParsedReport:
        normalize_equipment = getattr(
            profile,
            "normalize_equipment",
            None,
        )

        if (
            normalize_equipment
            and report.machine_name
        ):
            report.machine_name = (
                normalize_equipment(
                    report.machine_name
                )
            )

        normalize_unit = getattr(
            profile,
            "normalize_unit",
            None,
        )

        if (
            normalize_unit
            and report.length_unit
        ):
            report.length_unit = (
                normalize_unit(
                    report.length_unit
                )
            )

        return report

    # =============================================================
    # FIELD VALUES
    # =============================================================

    def _field_value(
        self,
        fields: dict[
            str,
            ExtractedField,
        ],
        field_name: str,
    ):
        field = (
            fields.get(
                field_name
            )
        )

        if (
            field is None
            or not field.found
        ):
            return None

        value = (
            field.value
        )

        if isinstance(
            value,
            str,
        ):
            value = (
                value.strip()
            )

        return value

    def _field_int(
        self,
        fields: dict[
            str,
            ExtractedField,
        ],
        field_name: str,
    ) -> int | None:
        value = (
            self._field_value(
                fields,
                field_name,
            )
        )

        if value is None:
            return None

        match = re.search(
            r"\d+",
            str(
                value
            ),
        )

        if not match:
            return None

        try:
            return int(
                match.group()
            )

        except ValueError:
            return None