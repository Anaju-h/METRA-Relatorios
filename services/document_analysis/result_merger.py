from __future__ import annotations

import unicodedata

from services.document_analysis.models import (
    ParsedCharacteristic,
)

from services.document_analysis.table_engine import (
    TableExtractionResult,
)


class ResultMerger:
    """
    Combina resultados vindos de diferentes estratégias.

    Objetivos:
    - evitar duplicação;
    - priorizar resultados mais completos;
    - preservar resultados exclusivos;
    - aumentar confiança quando estratégias independentes concordam.
    """

    # =============================================================
    # MESCLAR
    # =============================================================

    def merge_characteristics(
        self,
        results: list[
            TableExtractionResult
        ],
    ) -> list[
        ParsedCharacteristic
    ]:
        merged: list[
            ParsedCharacteristic
        ] = []

        for extraction_result in results:
            for item in (
                extraction_result
                .characteristics
            ):
                existing_index = (
                    self._find_equivalent(
                        merged,
                        item,
                    )
                )

                if existing_index is None:
                    merged.append(
                        item
                    )

                    continue

                existing = (
                    merged[
                        existing_index
                    ]
                )

                merged[
                    existing_index
                ] = self._merge_item(
                    existing,
                    item,
                )

        return merged

    # =============================================================
    # ENCONTRAR EQUIVALÊNCIA
    # =============================================================

    def _find_equivalent(
        self,
        existing_items: list[
            ParsedCharacteristic
        ],
        candidate: ParsedCharacteristic,
    ) -> int | None:
        for index, existing in enumerate(
            existing_items
        ):
            if self._equivalent(
                existing,
                candidate,
            ):
                return index

        return None

    def _equivalent(
        self,
        first: ParsedCharacteristic,
        second: ParsedCharacteristic,
    ) -> bool:
        # ---------------------------------------------------------
        # NOME
        # ---------------------------------------------------------

        first_name = (
            self._normalize(
                first.name
            )
        )

        second_name = (
            self._normalize(
                second.name
            )
        )

        if (
            not first_name
            or not second_name
            or first_name
            != second_name
        ):
            return False

        # ---------------------------------------------------------
        # PÁGINA
        # ---------------------------------------------------------

        if (
            first.source_page
            is not None
            and second.source_page
            is not None
            and first.source_page
            != second.source_page
        ):
            return False

        # ---------------------------------------------------------
        # PROPRIEDADE
        # ---------------------------------------------------------

        first_property = (
            self._normalize(
                first.property_name
                or ""
            )
        )

        second_property = (
            self._normalize(
                second.property_name
                or ""
            )
        )

        if (
            first_property
            and second_property
            and first_property
            != second_property
        ):
            return False

        # ---------------------------------------------------------
        # VALOR PRINCIPAL
        # ---------------------------------------------------------

        if (
            first.measured_value
            is not None
            and second.measured_value
            is not None
            and not self._float_close(
                first.measured_value,
                second.measured_value,
            )
        ):
            return False

        # INSPECT pode usar desvio como principal resultado.
        if (
            first.measured_value is None
            and second.measured_value is None
            and first.deviation is not None
            and second.deviation is not None
            and not self._float_close(
                first.deviation,
                second.deviation,
            )
        ):
            return False

        return True

    # =============================================================
    # MESCLAR DOIS ITENS
    # =============================================================

    def _merge_item(
        self,
        first: ParsedCharacteristic,
        second: ParsedCharacteristic,
    ) -> ParsedCharacteristic:
        # Escolhemos como base o item com maior
        # quantidade de informações preenchidas.
        first_score = (
            self._completeness_score(
                first
            )
        )

        second_score = (
            self._completeness_score(
                second
            )
        )

        if (
            second_score
            > first_score
        ):
            primary = second
            secondary = first

        else:
            primary = first
            secondary = second

        # ---------------------------------------------------------
        # CAMPOS FALTANTES
        # ---------------------------------------------------------

        primary.group_name = (
            primary.group_name
            or secondary.group_name
        )

        primary.datum = (
            primary.datum
            or secondary.datum
        )

        primary.property_name = (
            primary.property_name
            or secondary.property_name
        )

        primary.measured_value = (
            primary.measured_value
            if primary.measured_value
            is not None
            else secondary.measured_value
        )

        primary.nominal_value = (
            primary.nominal_value
            if primary.nominal_value
            is not None
            else secondary.nominal_value
        )

        primary.upper_tolerance = (
            primary.upper_tolerance
            if primary.upper_tolerance
            is not None
            else secondary.upper_tolerance
        )

        primary.lower_tolerance = (
            primary.lower_tolerance
            if primary.lower_tolerance
            is not None
            else secondary.lower_tolerance
        )

        primary.deviation = (
            primary.deviation
            if primary.deviation
            is not None
            else secondary.deviation
        )

        primary.unit = (
            primary.unit
            or secondary.unit
        )

        primary.check_value = (
            primary.check_value
            or secondary.check_value
        )

        primary.out_value = (
            primary.out_value
            or secondary.out_value
        )

        # ---------------------------------------------------------
        # STATUS
        # ---------------------------------------------------------

        if (
            primary.status
            == "UNKNOWN"
            and secondary.status
            != "UNKNOWN"
        ):
            primary.status = (
                secondary.status
            )

        # ---------------------------------------------------------
        # CONFIANÇA
        # ---------------------------------------------------------

        # Duas estratégias independentes encontrando
        # a mesma informação aumentam a confiança.
        if (
            first.extraction_method
            != second.extraction_method
        ):
            primary.confidence = min(
                1.0,
                max(
                    first.confidence,
                    second.confidence,
                )
                + 0.06,
            )

            primary.extraction_method = (
                "merged"
            )

        else:
            primary.confidence = max(
                first.confidence,
                second.confidence,
            )

        # ---------------------------------------------------------
        # RAW
        # ---------------------------------------------------------

        if (
            not primary.raw_text
            and secondary.raw_text
        ):
            primary.raw_text = (
                secondary.raw_text
            )

        # ---------------------------------------------------------
        # EXTRA DATA
        # ---------------------------------------------------------

        merged_extra = dict(
            secondary.extra_data
        )

        merged_extra.update(
            primary.extra_data
        )

        primary.extra_data = (
            merged_extra
        )

        return primary

    # =============================================================
    # COMPLETUDE
    # =============================================================

    def _completeness_score(
        self,
        item: ParsedCharacteristic,
    ) -> int:
        values = (
            item.group_name,
            item.datum,
            item.property_name,

            item.measured_value,
            item.nominal_value,

            item.upper_tolerance,
            item.lower_tolerance,

            item.deviation,

            item.unit,

            item.check_value,
            item.out_value,

            item.source_page,

            item.raw_text,
        )

        return sum(
            1
            for value in values
            if value not in (
                None,
                "",
            )
        )

    # =============================================================
    # FLOAT
    # =============================================================

    def _float_close(
        self,
        first: float,
        second: float,
    ) -> bool:
        return abs(
            first - second
        ) <= 1e-6

    # =============================================================
    # NORMALIZAÇÃO
    # =============================================================

    def _normalize(
        self,
        value: str,
    ) -> str:
        value = (
            unicodedata.normalize(
                "NFKD",
                value or "",
            )
        )

        value = "".join(
            character
            for character in value
            if not unicodedata.combining(
                character
            )
        )

        return " ".join(
            value.upper()
            .split()
        )