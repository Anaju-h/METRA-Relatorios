from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from services.document_analysis.calypso_row_interpreter import (
    CalypsoRowInterpreter,
)
from services.document_analysis.inspect_row_interpreter import (
    InspectRowInterpreter,
)
from services.document_analysis.models import (
    DocumentContent,
    DocumentPage,
    ParsedCharacteristic,
)
from services.document_analysis.table_builder import (
    BuiltTable,
    SpatialTableBuilder,
)


@dataclass
class TableExtractionResult:
    """
    Resultado produzido por uma estratégia de extração.

    Esta estrutura é mantida para preservar a compatibilidade
    com o ResultMerger e o DocumentAnalyzer.
    """

    characteristics: list[
        ParsedCharacteristic
    ] = field(
        default_factory=list
    )

    confidence: float = 0.0

    method: str = "unknown"

    warnings: list[str] = field(
        default_factory=list
    )


class TableEngine:
    """
    Motor de interpretação de tabelas técnicas.

    Estratégias executadas:

    1. espacial V2:
       reconstrói linhas, colunas e células pelas coordenadas.

    2. textual de compatibilidade:
       preserva uma leitura conservadora para documentos em que
       o PDF já entrega toda a tabela em linhas estruturadas.

    As duas estratégias são devolvidas separadamente para que o
    ResultMerger combine e elimine duplicações.
    """

    def __init__(self):
        self.table_builder = (
            SpatialTableBuilder()
        )

        self.calypso_interpreter = (
            CalypsoRowInterpreter()
        )

        self.inspect_interpreter = (
            InspectRowInterpreter()
        )

    # =============================================================
    # EXTRAÇÃO PÚBLICA
    # =============================================================

    def extract(
        self,
        document: DocumentContent,
        profile: type,
    ) -> list[TableExtractionResult]:
        spatial_result = (
            self._extract_spatial_v2(
                document=document,
                profile=profile,
            )
        )

        text_result = (
            self._extract_text_fallback(
                document=document,
                profile=profile,
            )
        )

        return [
            spatial_result,
            text_result,
        ]

    # =============================================================
    # ESTRATÉGIA ESPACIAL V2
    # =============================================================

    def _extract_spatial_v2(
        self,
        document: DocumentContent,
        profile: type,
    ) -> TableExtractionResult:
        characteristics = []

        warnings = []

        table_confidences = []

        table_count = 0

        source_type = str(
            getattr(
                profile,
                "SOURCE_TYPE",
                "",
            )
            or ""
        ).upper()

        for page in document.pages:
            try:
                tables = (
                    self.table_builder
                    .build(
                        page=page,
                        profile=profile,
                    )
                )

            except Exception as error:
                warnings.append(
                    (
                        f"Página {page.number}: "
                        "falha na reconstrução espacial: "
                        f"{error}"
                    )
                )

                continue

            table_count += len(
                tables
            )

            for table in tables:
                table_confidences.append(
                    table.confidence
                )

                table_items = (
                    self._interpret_table(
                        table=table,
                        profile=profile,
                        source_type=source_type,
                    )
                )

                characteristics.extend(
                    table_items
                )

                warnings.extend(
                    table.warnings
                )

        characteristics = self._deduplicate(
            characteristics
        )

        if table_count == 0:
            warnings.append(
                (
                    "Nenhuma tabela com cabeçalhos reconhecíveis "
                    "foi reconstruída pela estratégia espacial V2."
                )
            )

        if not characteristics:
            return TableExtractionResult(
                characteristics=[],

                confidence=0.0,

                method="table_spatial_v2",

                warnings=warnings,
            )

        if table_confidences:
            average_table_confidence = (
                sum(
                    table_confidences
                )
                / len(
                    table_confidences
                )
            )

        else:
            average_table_confidence = (
                0.70
            )

        volume_bonus = min(
            0.10,
            len(characteristics)
            * 0.005,
        )

        confidence = min(
            0.98,
            max(
                0.70,
                average_table_confidence
                + volume_bonus,
            ),
        )

        return TableExtractionResult(
            characteristics=characteristics,

            confidence=confidence,

            method="table_spatial_v2",

            warnings=warnings,
        )

    def _interpret_table(
        self,
        table: BuiltTable,
        profile: type,
        source_type: str,
    ) -> list[ParsedCharacteristic]:
        result = []

        current_group = None

        for row in table.rows:
            possible_group = (
                self._detect_group(
                    text=row.source_text,
                    profile=profile,
                    source_type=source_type,
                )
            )

            if possible_group:
                current_group = possible_group

                continue

            if source_type == "CALYPSO":
                item = (
                    self.calypso_interpreter
                    .interpret(
                        row=row,
                        profile=profile,
                        group_name=current_group,
                    )
                )

            elif source_type == "ZEISS_INSPECT":
                item = (
                    self.inspect_interpreter
                    .interpret(
                        row=row,
                        profile=profile,
                        group_name=current_group,
                    )
                )

            else:
                item = None

            if item is not None:
                result.append(
                    item
                )

        return result

    def _detect_group(
        self,
        text: str,
        profile: type,
        source_type: str,
    ) -> str | None:
        if source_type == "CALYPSO":
            return (
                self.calypso_interpreter
                .detect_group(
                    text=text,
                    profile=profile,
                )
            )

        if source_type == "ZEISS_INSPECT":
            return (
                self.inspect_interpreter
                .detect_group(
                    text=text,
                    profile=profile,
                )
            )

        return None

    # =============================================================
    # FALLBACK TEXTUAL
    # =============================================================

    def _extract_text_fallback(
        self,
        document: DocumentContent,
        profile: type,
    ) -> TableExtractionResult:
        source_type = str(
            getattr(
                profile,
                "SOURCE_TYPE",
                "",
            )
            or ""
        ).upper()

        characteristics = []

        for page in document.pages:
            lines = self._clean_lines(
                page.text
            )

            if source_type == "CALYPSO":
                page_items = (
                    self._parse_calypso_text_page(
                        lines=lines,
                        page_number=page.number,
                        profile=profile,
                    )
                )

            elif source_type == "ZEISS_INSPECT":
                page_items = (
                    self._parse_inspect_text_page(
                        lines=lines,
                        page_number=page.number,
                        profile=profile,
                    )
                )

            else:
                page_items = []

            characteristics.extend(
                page_items
            )

        characteristics = self._deduplicate(
            characteristics
        )

        if not characteristics:
            return TableExtractionResult(
                characteristics=[],

                confidence=0.0,

                method="table_text_fallback",

                warnings=[
                    (
                        "Nenhuma característica foi identificada "
                        "pela estratégia textual de compatibilidade."
                    )
                ],
            )

        confidence = min(
            0.90,
            0.62
            + len(characteristics)
            * 0.008,
        )

        return TableExtractionResult(
            characteristics=characteristics,

            confidence=confidence,

            method="table_text_fallback",
        )

    # =============================================================
    # CALYPSO TEXTUAL
    # =============================================================

    def _parse_calypso_text_page(
        self,
        lines: list[str],
        page_number: int,
        profile: type,
    ) -> list[ParsedCharacteristic]:
        result = []

        current_group = None

        for line in lines:
            detected_group = (
                self.calypso_interpreter
                .detect_group(
                    text=line,
                    profile=profile,
                )
            )

            if detected_group:
                current_group = detected_group

                continue

            if self._should_ignore_line(
                line=line,
                profile=profile,
            ):
                continue

            item = self._parse_calypso_text_line(
                line=line,
                page_number=page_number,
                profile=profile,
                group_name=current_group,
            )

            if item:
                result.append(
                    item
                )

        return result

    def _parse_calypso_text_line(
        self,
        line: str,
        page_number: int,
        profile: type,
        group_name: str | None,
    ) -> Optional[ParsedCharacteristic]:
        number_pattern = (
            r"[+-]?\d+(?:[.,]\d+)?"
        )

        unit_pattern = (
            r"(?:"
            r"mm|cm|m|"
            r"µm|um|"
            r"inch|in|"
            r"µinch|uinch|"
            r"°|deg"
            r")"
        )

        pattern = re.compile(
            (
                r"^"
                r"(?P<name>.+?)"
                r"\s+"
                r"(?P<measured>"
                + number_pattern
                + r")"
                r"\s*"
                r"(?P<unit>"
                + unit_pattern
                + r")?"
                r"\s+"
                r"(?P<rest>.+)"
                r"$"
            ),
            re.IGNORECASE,
        )

        match = pattern.match(
            line.strip()
        )

        if not match:
            return None

        name = " ".join(
            match.group(
                "name"
            ).split()
        )

        if not self._valid_text_name(
            name,
            profile,
        ):
            return None

        measured = self._parse_float(
            match.group(
                "measured"
            )
        )

        unit = match.group(
            "unit"
        )

        if unit:
            normalize_unit = getattr(
                profile,
                "normalize_unit",
                None,
            )

            if normalize_unit:
                unit = normalize_unit(
                    unit
                )

        numbers = [
            self._parse_float(
                number
            )
            for number in re.findall(
                number_pattern,
                match.group(
                    "rest"
                ),
            )
        ]

        numbers = [
            number
            for number in numbers
            if number is not None
        ]

        if (
            measured is None
            or not numbers
        ):
            return None

        nominal = numbers[0]

        upper = None
        lower = None
        deviation = None

        remaining = numbers[
            1:
        ]

        if len(remaining) >= 3:
            upper = remaining[0]
            lower = remaining[1]
            deviation = remaining[-1]

        elif len(remaining) == 2:
            upper = remaining[0]
            deviation = remaining[1]

        elif len(remaining) == 1:
            deviation = remaining[0]

        if (
            deviation is None
            and nominal is not None
        ):
            deviation = (
                measured
                - nominal
            )

        status = self._calculate_status(
            measured_value=measured,
            nominal_value=nominal,
            upper_tolerance=upper,
            lower_tolerance=lower,
        )

        return ParsedCharacteristic(
            name=name,

            group_name=(
                group_name
                or self._infer_calypso_group(
                    name=name,
                    profile=profile,
                )
            ),

            measured_value=measured,

            nominal_value=nominal,

            upper_tolerance=upper,

            lower_tolerance=lower,

            deviation=deviation,

            unit=unit,

            status=status,

            source_page=page_number,

            raw_text=line,

            confidence=0.78,

            extraction_method=(
                "table_text_fallback"
            ),
        )

    # =============================================================
    # INSPECT TEXTUAL
    # =============================================================

    def _parse_inspect_text_page(
        self,
        lines: list[str],
        page_number: int,
        profile: type,
    ) -> list[ParsedCharacteristic]:
        result = []

        for line in lines:
            if self._should_ignore_line(
                line=line,
                profile=profile,
            ):
                continue

            match = re.match(
                (
                    r"^(?P<name>.+?\.Vp\.\d+)"
                    r"\s+"
                    r"(?P<property>Vp)"
                    r"\s+"
                    r"(?P<value>[+-]?\d+(?:[.,]\d+)?)"
                    r"$"
                ),
                line.strip(),
                re.IGNORECASE,
            )

            if not match:
                continue

            value = self._parse_float(
                match.group(
                    "value"
                )
            )

            result.append(
                ParsedCharacteristic(
                    name=match.group(
                        "name"
                    ).strip(),

                    property_name=match.group(
                        "property"
                    ),

                    deviation=value,

                    status="UNKNOWN",

                    source_page=page_number,

                    raw_text=line,

                    confidence=0.75,

                    extraction_method=(
                        "table_text_fallback"
                    ),
                )
            )

        return result

    # =============================================================
    # STATUS
    # =============================================================

    def _calculate_status(
        self,
        measured_value: float | None,
        nominal_value: float | None,
        upper_tolerance: float | None,
        lower_tolerance: float | None,
    ) -> str:
        if (
            measured_value is None
            or nominal_value is None
            or upper_tolerance is None
            or lower_tolerance is None
        ):
            return "UNKNOWN"

        lower_limit = (
            nominal_value
            + lower_tolerance
        )

        upper_limit = (
            nominal_value
            + upper_tolerance
        )

        minimum = min(
            lower_limit,
            upper_limit,
        )

        maximum = max(
            lower_limit,
            upper_limit,
        )

        if (
            minimum
            <= measured_value
            <= maximum
        ):
            return "OK"

        return "NOK"

    # =============================================================
    # HELPERS
    # =============================================================

    def _infer_calypso_group(
        self,
        name: str,
        profile: type,
    ) -> str | None:
        normalized = self._normalize(
            name
        )

        mapping = (
            (
                (
                    "DIAMETRO",
                    "DIAMETER",
                    "RAIO",
                ),
                "DIÂMETROS",
            ),
            (
                (
                    "DISTANCIA",
                    "DISTANCE",
                    "ALTURA",
                    "COMPRIMENTO",
                ),
                "DISTÂNCIAS",
            ),
            (
                (
                    "PLANIC",
                    "FLATNESS",
                ),
                "PLANICIDADES",
            ),
            (
                (
                    "CIRCULAR",
                    "ROUNDNESS",
                ),
                "CIRCULARIDADES",
            ),
            (
                (
                    "POSICAO",
                    "POSITION",
                ),
                "POSIÇÕES",
            ),
            (
                (
                    "PERPENDICULAR",
                ),
                "PERPENDICULARIDADES",
            ),
            (
                (
                    "PARALEL",
                ),
                "PARALELISMOS",
            ),
        )

        groups = {
            self._normalize(
                group
            ): group
            for group in getattr(
                profile,
                "GROUP_NAMES",
                tuple(),
            )
        }

        for terms, group in mapping:
            if any(
                term in normalized
                for term in terms
            ):
                return groups.get(
                    self._normalize(
                        group
                    ),
                    group,
                )

        return None

    def _valid_text_name(
        self,
        name: str,
        profile: type,
    ) -> bool:
        if not name:
            return False

        normalized = self._normalize(
            name
        )

        if len(normalized) < 2:
            return False

        if re.fullmatch(
            r"[\d.,+\-/%\s]+",
            normalized,
        ):
            return False

        blocked = {
            "NAME",
            "NOME",
            "MEASURED VALUE",
            "NOMINAL VALUE",
            "MEASURED",
            "NOMINAL",
        }

        if normalized in blocked:
            return False

        return not self._should_ignore_line(
            line=name,
            profile=profile,
        )

    def _should_ignore_line(
        self,
        line: str,
        profile: type,
    ) -> bool:
        normalized = self._normalize(
            line
        )

        for prefix in getattr(
            profile,
            "CHARACTERISTIC_IGNORE_PREFIXES",
            tuple(),
        ):
            if normalized.startswith(
                self._normalize(
                    prefix
                )
            ):
                return True

        return False

    def _parse_float(
        self,
        value,
    ) -> float | None:
        if value is None:
            return None

        clean = str(
            value
        ).strip()

        match = re.search(
            r"[+-]?\d+(?:[.,]\d+)?",
            clean.replace(
                " ",
                "",
            ),
        )

        if not match:
            return None

        number = match.group(
            0
        )

        if (
            "," in number
            and "." in number
        ):
            if number.rfind(
                ","
            ) > number.rfind(
                "."
            ):
                number = (
                    number.replace(
                        ".",
                        "",
                    )
                    .replace(
                        ",",
                        ".",
                    )
                )

            else:
                number = number.replace(
                    ",",
                    "",
                )

        else:
            number = number.replace(
                ",",
                ".",
            )

        try:
            return float(
                number
            )

        except ValueError:
            return None

    def _clean_lines(
        self,
        text: str,
    ) -> list[str]:
        result = []

        for raw_line in str(
            text
            or ""
        ).splitlines():
            line = re.sub(
                r"[ \t]+",
                " ",
                raw_line,
            ).strip()

            if line:
                result.append(
                    line
                )

        return result

    def _normalize(
        self,
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            value
            or "",
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        normalized = normalized.replace(
            "\u00A0",
            " ",
        )

        return " ".join(
            normalized.upper().split()
        )

    # =============================================================
    # DEDUPLICAÇÃO
    # =============================================================

    def _deduplicate(
        self,
        items: list[ParsedCharacteristic],
    ) -> list[ParsedCharacteristic]:
        result = []

        seen = set()

        for item in items:
            key = (
                item.source_page,

                self._normalize(
                    item.name
                ),

                item.measured_value,

                item.nominal_value,

                item.upper_tolerance,

                item.lower_tolerance,

                item.deviation,

                self._normalize(
                    item.property_name
                    or ""
                ),
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                item
            )

        return result