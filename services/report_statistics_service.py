from __future__ import annotations

import hashlib
import math
import re
import statistics
import unicodedata
from typing import Any, Optional

from models.statistical_characteristic import (
    StatisticalCharacteristic,
    StatisticalMeasurement,
)


class ReportStatisticsService:
    """
    Consolida os resultados metrológicos para relatórios de
    peça única ou lote.

    O serviço não possui regras específicas para DuraMax,
    PRISMO, diâmetro ou cilindricidade.

    Qualquer característica numérica pode ser consolidada,
    desde que tenha sido estruturada pelo motor documental.
    """

    STATUS_OK = "OK"
    STATUS_NOK = "NOK"
    STATUS_UNKNOWN = "UNKNOWN"

    NUMBER_PRECISION = 8

    def build_statistics(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        documents = context.get(
            "documents",
            [],
        )

        extraction_pairs = context.get(
            "extractions",
            [],
        )

        document_map = {
            document.id: document
            for document in documents
            if document.id is not None
        }

        grouped: dict[
            str,
            StatisticalCharacteristic,
        ] = {}

        all_measurements: list[
            StatisticalMeasurement
        ] = []

        for extraction, characteristics in (
            extraction_pairs
        ):
            document = document_map.get(
                extraction.document_id
            )

            document_name = self._resolve_document_name(
                document=document,
                extraction=extraction,
            )

            unit_identifier = (
                self._resolve_unit_identifier(
                    document=document,
                    extraction=extraction,
                    document_name=document_name,
                )
            )

            for characteristic in characteristics:
                key = self._build_group_key(
                    characteristic
                )

                group = grouped.get(
                    key
                )

                if group is None:
                    group = (
                        StatisticalCharacteristic(
                            key=key,

                            display_name=(
                                characteristic.name
                                or "Característica"
                            ),

                            group_name=(
                                characteristic.group_name
                            ),

                            property_name=(
                                characteristic.property_name
                            ),

                            datum=(
                                characteristic.datum
                            ),

                            nominal_value=(
                                self._to_optional_float(
                                    characteristic.nominal_value
                                )
                            ),

                            lower_tolerance=(
                                self._to_optional_float(
                                    characteristic.lower_tolerance
                                )
                            ),

                            upper_tolerance=(
                                self._to_optional_float(
                                    characteristic.upper_tolerance
                                )
                            ),

                            unit=(
                                characteristic.unit
                            ),
                        )
                    )

                    grouped[
                        key
                    ] = group

                measurement = StatisticalMeasurement(
                    document_id=(
                        extraction.document_id
                    ),

                    extraction_id=(
                        extraction.id
                    ),

                    characteristic_id=(
                        characteristic.id
                    ),

                    unit_identifier=(
                        unit_identifier
                    ),

                    document_name=(
                        document_name
                    ),

                    measured_value=(
                        self._to_optional_float(
                            characteristic.measured_value
                        )
                    ),

                    deviation=(
                        self._to_optional_float(
                            characteristic.deviation
                        )
                    ),

                    status=(
                        self.normalize_status(
                            characteristic.status
                        )
                    ),

                    source_page=(
                        characteristic.source_page
                    ),
                )

                group.measurements.append(
                    measurement
                )

                all_measurements.append(
                    measurement
                )

        statistical_groups = []

        for group in grouped.values():
            self._calculate_group_statistics(
                group
            )

            statistical_groups.append(
                group
            )

        statistical_groups.sort(
            key=self._group_sort_key
        )

        overall_summary = (
            self._build_overall_summary(
                groups=statistical_groups,
                measurements=all_measurements,
                document_count=len(
                    documents
                ),
            )
        )

        chart_candidates = (
            self._select_chart_candidates(
                statistical_groups
            )
        )

        return {
            "groups":
                statistical_groups,

            "overall":
                overall_summary,

            "chart_candidates":
                chart_candidates,

            "group_count":
                len(
                    statistical_groups
                ),

            "measurement_count":
                len(
                    all_measurements
                ),
        }

    # =============================================================
    # IDENTIDADE DA CARACTERÍSTICA
    # =============================================================

    def _build_group_key(
        self,
        characteristic,
    ) -> str:
        components = [
            self._normalize_name(
                characteristic.name
            ),

            self._normalize_text(
                characteristic.group_name
            ),

            self._normalize_text(
                characteristic.property_name
            ),

            self._normalize_text(
                characteristic.datum
            ),

            self._number_signature(
                characteristic.nominal_value
            ),

            self._number_signature(
                characteristic.lower_tolerance
            ),

            self._number_signature(
                characteristic.upper_tolerance
            ),

            self._normalize_unit(
                characteristic.unit
            ),
        ]

        raw_key = "|".join(
            components
        )

        return hashlib.sha1(
            raw_key.encode(
                "utf-8"
            )
        ).hexdigest()

    def _normalize_name(
        self,
        value,
    ) -> str:
        normalized = self._normalize_text(
            value
        )

        if not normalized:
            return "CARACTERISTICA"

        # Uniformiza separadores sem remover números importantes.
        normalized = re.sub(
            r"[_/\\\-]+",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        # Uniformizações linguísticas frequentes.
        replacements = {
            "DIAMETER":
                "DIAMETRO",

            "DIAMETRE":
                "DIAMETRO",

            "DISTANCE":
                "DISTANCIA",

            "HEIGHT":
                "ALTURA",

            "FLATNESS":
                "PLANICIDADE",

            "ROUNDNESS":
                "CIRCULARIDADE",

            "CYLINDRICITY":
                "CILINDRICIDADE",

            "PERPENDICULARITY":
                "PERPENDICULARIDADE",

            "PARALLELISM":
                "PARALELISMO",

            "POSITION":
                "POSICAO",

            "RUNOUT":
                "BATIMENTO",

            "STRAIGHTNESS":
                "RETITUDE",

            "PROFILE":
                "PERFIL",
        }

        for source, destination in (
            replacements.items()
        ):
            normalized = normalized.replace(
                source,
                destination,
            )

        return normalized

    def _number_signature(
        self,
        value,
    ) -> str:
        number = self._to_optional_float(
            value
        )

        if number is None:
            return "-"

        rounded = round(
            number,
            self.NUMBER_PRECISION,
        )

        return (
            f"{rounded:.{self.NUMBER_PRECISION}f}"
        )

    # =============================================================
    # CÁLCULO ESTATÍSTICO
    # =============================================================

    def _calculate_group_statistics(
        self,
        group: StatisticalCharacteristic,
    ) -> None:
        group.count = len(
            group.measurements
        )

        values = group.numeric_values

        group.valid_numeric_count = len(
            values
        )

        group.ok_count = sum(
            1
            for measurement
            in group.measurements
            if measurement.status
            == self.STATUS_OK
        )

        group.nok_count = sum(
            1
            for measurement
            in group.measurements
            if measurement.status
            == self.STATUS_NOK
        )

        group.unknown_count = (
            group.count
            - group.ok_count
            - group.nok_count
        )

        evaluated_count = (
            group.ok_count
            + group.nok_count
        )

        if evaluated_count > 0:
            group.conformity_percentage = (
                group.ok_count
                / evaluated_count
                * 100.0
            )

        else:
            group.conformity_percentage = 0.0

        if values:
            group.minimum = min(
                values
            )

            group.maximum = max(
                values
            )

            group.mean = statistics.fmean(
                values
            )

            group.median = statistics.median(
                values
            )

            group.amplitude = (
                group.maximum
                - group.minimum
            )

            if len(
                values
            ) >= 2:
                group.standard_deviation = (
                    statistics.stdev(
                        values
                    )
                )

            else:
                group.standard_deviation = 0.0

        if (
            group.nominal_value is not None
            and group.lower_tolerance
            is not None
        ):
            group.lower_limit = (
                group.nominal_value
                + group.lower_tolerance
            )

        if (
            group.nominal_value is not None
            and group.upper_tolerance
            is not None
        ):
            group.upper_limit = (
                group.nominal_value
                + group.upper_tolerance
            )

        # Garante que os limites não fiquem invertidos em
        # relatórios com exportação incomum.
        if (
            group.lower_limit is not None
            and group.upper_limit is not None
            and group.lower_limit
            > group.upper_limit
        ):
            (
                group.lower_limit,
                group.upper_limit,
            ) = (
                group.upper_limit,
                group.lower_limit,
            )

        group.measurements.sort(
            key=self._measurement_sort_key
        )

    # =============================================================
    # RESUMO GERAL
    # =============================================================

    def _build_overall_summary(
        self,
        groups: list[
            StatisticalCharacteristic
        ],
        measurements: list[
            StatisticalMeasurement
        ],
        document_count: int,
    ) -> dict[str, Any]:
        total = len(
            measurements
        )

        ok_count = sum(
            1
            for measurement in measurements
            if measurement.status
            == self.STATUS_OK
        )

        nok_count = sum(
            1
            for measurement in measurements
            if measurement.status
            == self.STATUS_NOK
        )

        unknown_count = (
            total
            - ok_count
            - nok_count
        )

        evaluated_count = (
            ok_count
            + nok_count
        )

        conformity_percentage = (
            ok_count
            / evaluated_count
            * 100.0
            if evaluated_count > 0
            else 0.0
        )

        nonconforming_groups = sum(
            1
            for group in groups
            if group.nok_count > 0
        )

        completely_conforming_groups = sum(
            1
            for group in groups
            if (
                group.ok_count > 0
                and group.nok_count == 0
                and group.unknown_count == 0
            )
        )

        unit_identifiers = {
            measurement.unit_identifier
            for measurement in measurements
            if measurement.unit_identifier
        }

        return {
            "document_count":
                document_count,

            "unit_count":
                (
                    len(
                        unit_identifiers
                    )
                    if unit_identifiers
                    else document_count
                ),

            "group_count":
                len(
                    groups
                ),

            "measurement_count":
                total,

            "ok_count":
                ok_count,

            "nok_count":
                nok_count,

            "unknown_count":
                unknown_count,

            "evaluated_count":
                evaluated_count,

            "conformity_percentage":
                conformity_percentage,

            "nonconforming_group_count":
                nonconforming_groups,

            "conforming_group_count":
                completely_conforming_groups,

            "has_nonconformity":
                nok_count > 0,
        }

    # =============================================================
    # GRÁFICOS
    # =============================================================

    def _select_chart_candidates(
        self,
        groups: list[
            StatisticalCharacteristic
        ],
    ) -> list[
        StatisticalCharacteristic
    ]:
        """
        Prioriza automaticamente:

        1. grupos com resultados NOK;
        2. grupos com várias unidades;
        3. grupos com maior amplitude relativa;
        4. demais características numéricas.

        Nenhum nome ou tipo de medição é fixado.
        """

        candidates = [
            group
            for group in groups
            if group.valid_numeric_count > 0
        ]

        candidates.sort(
            key=lambda group: (
                0
                if group.nok_count > 0
                else 1,

                0
                if group.is_batch_characteristic
                else 1,

                -self._relative_amplitude(
                    group
                ),

                self._normalize_name(
                    group.display_name
                ),
            )
        )

        return candidates

    def _relative_amplitude(
        self,
        group: StatisticalCharacteristic,
    ) -> float:
        if group.amplitude is None:
            return 0.0

        reference_candidates = [
            abs(
                group.nominal_value
            )
            if group.nominal_value
            is not None
            else 0.0,

            abs(
                group.mean
            )
            if group.mean
            is not None
            else 0.0,

            1.0,
        ]

        reference = max(
            reference_candidates
        )

        return (
            abs(
                group.amplitude
            )
            / reference
        )

    # =============================================================
    # DOCUMENTO E UNIDADE
    # =============================================================

    def _resolve_document_name(
        self,
        document,
        extraction,
    ) -> str:
        if document is not None:
            name = str(
                getattr(
                    document,
                    "file_name",
                    "",
                )
                or ""
            ).strip()

            if name:
                return name

        if extraction.document_id is not None:
            return (
                f"Documento "
                f"{extraction.document_id}"
            )

        return "Extração legada"

    def _resolve_unit_identifier(
        self,
        document,
        extraction,
        document_name: str,
    ) -> str:
        candidates = [
            (
                getattr(
                    document,
                    "specimen_identifier",
                    None,
                )
                if document is not None
                else None
            ),

            extraction.part_number,

            self._identifier_from_filename(
                document_name
            ),

            (
                str(
                    extraction.document_id
                )
                if extraction.document_id
                is not None
                else None
            ),
        ]

        for candidate in candidates:
            clean = str(
                candidate
                or ""
            ).strip()

            if clean:
                return clean

        return "Unidade"

    def _identifier_from_filename(
        self,
        file_name: str,
    ) -> Optional[str]:
        stem = re.sub(
            r"\.[^.]+$",
            "",
            file_name,
        )

        number_matches = re.findall(
            r"\d+",
            stem,
        )

        if not number_matches:
            return None

        return number_matches[
            -1
        ]

    # =============================================================
    # ORDENAÇÃO
    # =============================================================

    def _measurement_sort_key(
        self,
        measurement: StatisticalMeasurement,
    ):
        identifier = (
            measurement.unit_identifier
        )

        numeric_match = re.search(
            r"\d+(?:[.,]\d+)?",
            identifier,
        )

        if numeric_match:
            number = float(
                numeric_match.group(
                    0
                ).replace(
                    ",",
                    ".",
                )
            )

            return (
                0,
                number,
                identifier,
            )

        return (
            1,
            0,
            identifier,
        )

    def _group_sort_key(
        self,
        group: StatisticalCharacteristic,
    ):
        return (
            self._normalize_text(
                group.group_name
            ),

            self._normalize_name(
                group.display_name
            ),

            self._number_signature(
                group.nominal_value
            ),
        )

    # =============================================================
    # STATUS
    # =============================================================

    def normalize_status(
        self,
        value,
    ) -> str:
        normalized = self._normalize_text(
            value
        )

        if normalized in {
            "OK",
            "PASS",
            "PASSED",
            "APPROVED",
            "CONFORME",
            "GREEN",
            "VERDE",
        }:
            return self.STATUS_OK

        if normalized in {
            "NOK",
            "FAIL",
            "FAILED",
            "REJECTED",
            "OUT",
            "NAO CONFORME",
            "RED",
            "VERMELHO",
        }:
            return self.STATUS_NOK

        return self.STATUS_UNKNOWN

    # =============================================================
    # HELPERS
    # =============================================================

    def _normalize_text(
        self,
        value,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            str(
                value
                or ""
            ),
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        normalized = normalized.upper()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    def _normalize_unit(
        self,
        value,
    ) -> str:
        normalized = self._normalize_text(
            value
        )

        aliases = {
            "MILLIMETER":
                "MM",

            "MILLIMETRE":
                "MM",

            "MILLIMETERS":
                "MM",

            "MICROMETER":
                "UM",

            "MICROMETRE":
                "UM",

            "ΜM":
                "UM",

            "µM":
                "UM",

            "DEG":
                "°",

            "DEGREE":
                "°",

            "DEGREES":
                "°",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    def _to_optional_float(
        self,
        value,
    ) -> Optional[float]:
        if value is None:
            return None

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        if not math.isfinite(
            number
        ):
            return None

        return number