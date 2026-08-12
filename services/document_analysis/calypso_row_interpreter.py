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


class CalypsoRowInterpreter:
    """
    Converte uma linha espacial reconstruída em uma característica
    metrológica do CALYPSO.

    O interpretador não trabalha diretamente com coordenadas.
    Ele recebe células já separadas pelo SpatialTableBuilder.
    """

    NUMBER_PATTERN = re.compile(
        r"[+-]?\d+(?:[.,]\d+)?"
    )

    UNIT_PATTERN = re.compile(
        (
            r"(?i)"
            r"(?:"
            r"mm|cm|m|"
            r"µm|um|"
            r"inch|in|"
            r"µinch|uinch|"
            r"°|deg"
            r")"
        )
    )

    def interpret(
        self,
        row: BuiltRow,
        profile: type,
        group_name: str | None = None,
    ) -> Optional[ParsedCharacteristic]:
        values = row.values

        name = self._clean_name(
            values.get(
                "name",
                "",
            )
        )

        if not self._valid_name(
            name,
            profile,
        ):
            return None

        measured_text = values.get(
            "measured_value",
            "",
        )

        nominal_text = values.get(
            "nominal_value",
            "",
        )

        measured_value = self._parse_float(
            measured_text
        )

        nominal_value = self._parse_float(
            nominal_text
        )

        # Para considerarmos uma linha uma característica real,
        # precisamos de pelo menos valor medido e valor nominal.
        if (
            measured_value is None
            or nominal_value is None
        ):
            return None

        upper_tolerance = self._parse_float(
            values.get(
                "upper_tolerance",
                "",
            )
        )

        lower_tolerance = self._parse_float(
            values.get(
                "lower_tolerance",
                "",
            )
        )

        deviation = self._parse_float(
            values.get(
                "deviation",
                "",
            )
        )

        # Alguns relatórios não possuem uma coluna separada para
        # desvio. Nesse caso, calculamos somente quando possível.
        if (
            deviation is None
            and measured_value is not None
            and nominal_value is not None
        ):
            deviation = (
                measured_value
                - nominal_value
            )

        unit = self._resolve_unit(
            values=values,
            source_text=row.source_text,
            profile=profile,
        )

        status = self._calculate_status(
            measured_value=measured_value,
            nominal_value=nominal_value,
            upper_tolerance=upper_tolerance,
            lower_tolerance=lower_tolerance,
        )

        resolved_group = (
            group_name
            or self._infer_group_from_name(
                name,
                profile,
            )
        )

        return ParsedCharacteristic(
            name=name,

            group_name=resolved_group,

            measured_value=measured_value,

            nominal_value=nominal_value,

            upper_tolerance=upper_tolerance,

            lower_tolerance=lower_tolerance,

            deviation=deviation,

            unit=unit,

            status=status,

            source_page=row.page_number,

            raw_text=row.source_text,

            confidence=max(
                0.70,
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

        groups = getattr(
            profile,
            "GROUP_NAMES",
            tuple(),
        )

        for group in groups:
            if normalized == self._normalize(
                group
            ):
                return group

        return None

    def _infer_group_from_name(
        self,
        name: str,
        profile: type,
    ) -> str | None:
        normalized = self._normalize(
            name
        )

        rules = (
            (
                (
                    "DIAMETRO",
                    "DIAMETER",
                    "RAIO",
                    "RADIUS",
                ),
                "DIÂMETROS",
            ),
            (
                (
                    "DISTANCIA",
                    "DISTANCE",
                    "ALTURA",
                    "HEIGHT",
                    "COMPRIMENTO",
                    "LENGTH",
                ),
                "DISTÂNCIAS",
            ),
            (
                (
                    "PERPENDICULAR",
                    "PERPENDICULARITY",
                ),
                "PERPENDICULARIDADES",
            ),
            (
                (
                    "PARALEL",
                    "PARALLEL",
                ),
                "PARALELISMOS",
            ),
            (
                (
                    "CILINDRIC",
                    "CYLINDRIC",
                ),
                "CILINDRICIDADES",
            ),
            (
                (
                    "CONCENTRIC",
                ),
                "CONCENTRICIDADES",
            ),
            (
                (
                    "COAXIAL",
                ),
                "COAXIALIDADES",
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
                    "ANGULO",
                    "ANGLE",
                ),
                "ÂNGULOS",
            ),
            (
                (
                    "RETITUDE",
                    "STRAIGHTNESS",
                ),
                "RETITUDES",
            ),
            (
                (
                    "BATIMENTO",
                    "RUNOUT",
                ),
                "BATIMENTOS",
            ),
            (
                (
                    "SIMETRIA",
                    "SYMMETRY",
                ),
                "SIMETRIAS",
            ),
            (
                (
                    "INCLINACAO",
                    "ANGULARITY",
                ),
                "INCLINAÇÕES",
            ),
            (
                (
                    "COORDENADA",
                    "COORDINATE",
                    " X",
                    " Y",
                    " Z",
                ),
                "COORDENADAS",
            ),
            (
                (
                    "PERFIL",
                    "PROFILE",
                ),
                "PERFIS",
            ),
        )

        available_groups = {
            self._normalize(
                group
            ): group
            for group in getattr(
                profile,
                "GROUP_NAMES",
                tuple(),
            )
        }

        for terms, suggested_group in rules:
            if not any(
                term in normalized
                for term in terms
            ):
                continue

            normalized_suggestion = (
                self._normalize(
                    suggested_group
                )
            )

            return available_groups.get(
                normalized_suggestion,
                suggested_group,
            )

        return None

    # =============================================================
    # UNIDADE
    # =============================================================

    def _resolve_unit(
        self,
        values: dict[str, str],
        source_text: str,
        profile: type,
    ) -> str | None:
        candidates = (
            values.get(
                "unit",
                "",
            ),
            values.get(
                "measured_value",
                "",
            ),
            source_text,
        )

        detected = None

        for candidate in candidates:
            match = self.UNIT_PATTERN.search(
                str(
                    candidate
                    or ""
                )
            )

            if match:
                detected = match.group(
                    0
                )

                break

        if not detected:
            return None

        normalize_unit = getattr(
            profile,
            "normalize_unit",
            None,
        )

        if normalize_unit:
            return normalize_unit(
                detected
            )

        return detected

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
            "NAME",
            "NOME",
            "CHARACTERISTIC",
            "CARACTERISTICA",
            "MEASURED VALUE",
            "NOMINAL VALUE",
            "MEASURED",
            "NOMINAL",
            "ACTUAL",
            "TARGET",
        }

        if normalized in blocked:
            return False

        ignore_prefixes = getattr(
            profile,
            "CHARACTERISTIC_IGNORE_PREFIXES",
            tuple(),
        )

        for prefix in ignore_prefixes:
            if normalized.startswith(
                self._normalize(
                    prefix
                )
            ):
                return False

        return True

    # =============================================================
    # NÚMEROS
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

        number = self._normalize_decimal(
            number
        )

        try:
            return float(
                number
            )

        except ValueError:
            return None

    def _normalize_decimal(
        self,
        value: str,
    ) -> str:
        value = value.strip()

        if (
            "," in value
            and "." in value
        ):
            last_comma = value.rfind(
                ","
            )

            last_dot = value.rfind(
                "."
            )

            if last_comma > last_dot:
                value = (
                    value.replace(
                        ".",
                        "",
                    )
                    .replace(
                        ",",
                        ".",
                    )
                )

            else:
                value = value.replace(
                    ",",
                    "",
                )

            return value

        return value.replace(
            ",",
            ".",
        )

    # =============================================================
    # TEXTO
    # =============================================================

    def _clean_name(
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