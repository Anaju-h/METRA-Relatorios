from __future__ import annotations

import re
import unicodedata
from typing import Optional

from services.document_analysis.models import (
    ParsedCharacteristic,
)
from services.document_analysis.table_builder import (
    BuiltRow,
)


class InspectRowInterpreter:
    """
    Converte linhas espaciais reconstruídas de relatórios
    ZEISS INSPECT em características estruturadas.
    """

    NUMBER_PATTERN = re.compile(
        r"[+-]?\d+(?:[.,]\d+)?"
    )

    def interpret(
        self,
        row: BuiltRow,
        profile: type,
        group_name: str | None = None,
    ) -> Optional[ParsedCharacteristic]:
        values = row.values

        name = self._clean_text(
            values.get(
                "name",
                "",
            )
            or values.get(
                "element",
                "",
            )
        )

        if not self._valid_name(
            name,
            profile,
        ):
            return None

        property_name = self._clean_optional(
            values.get(
                "property_name",
                "",
            )
            or values.get(
                "property",
                "",
            )
        )

        datum = self._clean_optional(
            values.get(
                "datum",
                "",
            )
        )

        measured = self._parse_float(
            values.get(
                "measured_value",
                "",
            )
            or values.get(
                "actual_value",
                "",
            )
            or values.get(
                "actual",
                "",
            )
        )

        nominal = self._parse_float(
            values.get(
                "nominal_value",
                "",
            )
            or values.get(
                "nominal",
                "",
            )
        )

        lower = self._parse_float(
            values.get(
                "lower_tolerance",
                "",
            )
        )

        upper = self._parse_float(
            values.get(
                "upper_tolerance",
                "",
            )
        )

        deviation = self._parse_float(
            values.get(
                "deviation",
                "",
            )
        )

        # Alguns relatórios INSPECT trazem somente desvio.
        if (
            measured is None
            and deviation is None
        ):
            return None

        if (
            deviation is None
            and measured is not None
            and nominal is not None
        ):
            deviation = (
                measured
                - nominal
            )

        check_value = self._clean_optional(
            values.get(
                "check_value",
                "",
            )
            or values.get(
                "check",
                "",
            )
        )

        out_value = self._clean_optional(
            values.get(
                "out_value",
                "",
            )
            or values.get(
                "out",
                "",
            )
        )

        status = self._calculate_status(
            measured_value=measured,
            nominal_value=nominal,
            lower_tolerance=lower,
            upper_tolerance=upper,
            out_value=out_value,
            check_value=check_value,
        )

        unit = self._clean_optional(
            values.get(
                "unit",
                "",
            )
        )

        return ParsedCharacteristic(
            name=name,

            group_name=group_name,

            datum=datum,

            property_name=property_name,

            measured_value=measured,

            nominal_value=nominal,

            upper_tolerance=upper,

            lower_tolerance=lower,

            deviation=deviation,

            unit=unit,

            status=status,

            check_value=check_value,

            out_value=out_value,

            source_page=row.page_number,

            raw_text=row.source_text,

            confidence=max(
                0.68,
                min(
                    0.97,
                    row.confidence,
                ),
            ),

            extraction_method=(
                "table_spatial_v2"
            ),
        )

    # =============================================================
    # GRUPO
    # =============================================================

    def detect_group(
        self,
        text: str,
        profile: type,
    ) -> str | None:
        normalized = self._normalize(
            text
        )

        for group in getattr(
            profile,
            "GROUP_NAMES",
            tuple(),
        ):
            if normalized == self._normalize(
                group
            ):
                return group

        return None

    # =============================================================
    # STATUS
    # =============================================================

    def _calculate_status(
        self,
        measured_value: float | None,
        nominal_value: float | None,
        lower_tolerance: float | None,
        upper_tolerance: float | None,
        out_value: str | None,
        check_value: str | None,
    ) -> str:
        normalized_out = self._normalize(
            out_value
            or ""
        )

        if normalized_out in {
            "YES",
            "SIM",
            "TRUE",
            "1",
            "OUT",
            "NOK",
            "FAIL",
            "FAILED",
            "RED",
            "VERMELHO",
        }:
            return "NOK"

        if normalized_out in {
            "NO",
            "NAO",
            "NÃO",
            "FALSE",
            "0",
            "OK",
            "PASS",
            "GREEN",
            "VERDE",
        }:
            return "OK"

        normalized_check = self._normalize(
            check_value
            or ""
        )

        if normalized_check in {
            "OK",
            "PASS",
            "PASSED",
            "CONFORME",
            "GREEN",
            "VERDE",
        }:
            return "OK"

        if normalized_check in {
            "NOK",
            "FAIL",
            "FAILED",
            "OUT",
            "NAO CONFORME",
            "NÃO CONFORME",
            "RED",
            "VERMELHO",
        }:
            return "NOK"

        if (
            measured_value is None
            or nominal_value is None
            or lower_tolerance is None
            or upper_tolerance is None
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
    # VALIDAÇÃO
    # =============================================================

    def _valid_name(
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
            "ELEMENT",
            "ELEMENTO",
            "NAME",
            "NOME",
            "PROPERTY",
            "PROPRIEDADE",
            "DATUM",
            "ACTUAL",
            "NOMINAL",
            "DEVIATION",
            "DESVIO",
        }

        if normalized in blocked:
            return False

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
                return False

        return True

    # =============================================================
    # NÚMERO
    # =============================================================

    def _parse_float(
        self,
        value,
    ) -> float | None:
        if value is None:
            return None

        clean = str(
            value
        ).strip()

        if not clean:
            return None

        match = self.NUMBER_PATTERN.search(
            clean.replace(
                " ",
                "",
            )
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

    # =============================================================
    # TEXTO
    # =============================================================

    def _clean_text(
        self,
        value: str,
    ) -> str:
        return " ".join(
            str(
                value
                or ""
            ).split()
        ).strip(
            " |;:"
        )

    def _clean_optional(
        self,
        value: str,
    ) -> str | None:
        cleaned = self._clean_text(
            value
        )

        return cleaned or None

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

        return " ".join(
            normalized.upper().split()
        )