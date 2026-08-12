from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from services.document_analysis.models import (
    DocumentContent,
)
from services.document_analysis.profile_registry import (
    ProfileRegistry,
)


@dataclass
class SourceDetectionResult:
    """
    Resultado da identificação da família documental.
    """

    source_type: str

    confidence: float = 0.0

    evidence: list[str] = field(
        default_factory=list
    )

    profile: type | None = None


class SourceDetector:
    """
    Detecta a família documental.

    A comparação é feita de duas formas:

    1. texto normalizado;
    2. texto compactado.

    Isso permite reconhecer casos em que o próprio PDF fragmenta
    palavras visualmente, por exemplo:

        ZEISS INSP EC T

    que semanticamente corresponde a:

        ZEISS INSPECT
    """

    UNKNOWN = "UNKNOWN"

    MIN_CONFIDENCE = 0.50

    # =============================================================
    # API
    # =============================================================

    def detect(
        self,
        document: DocumentContent,
    ) -> SourceDetectionResult:
        normalized_text = (
            self._normalize(
                document.full_text
            )
        )

        compact_text = (
            self._compact(
                document.full_text
            )
        )

        candidates = []

        for profile in (
            ProfileRegistry
            .get_all_profiles()
        ):
            result = (
                self._evaluate_profile(
                    normalized_text=(
                        normalized_text
                    ),

                    compact_text=(
                        compact_text
                    ),

                    profile=profile,
                )
            )

            candidates.append(
                result
            )

        if not candidates:
            return SourceDetectionResult(
                source_type=self.UNKNOWN,
                confidence=0.0,
            )

        best = max(
            candidates,
            key=lambda item:
                item.confidence,
        )

        if (
            best.confidence
            < self.MIN_CONFIDENCE
        ):
            return SourceDetectionResult(
                source_type=(
                    self.UNKNOWN
                ),

                confidence=(
                    best.confidence
                ),

                evidence=(
                    best.evidence
                ),

                profile=None,
            )

        return best

    # =============================================================
    # PERFIL
    # =============================================================

    def _evaluate_profile(
        self,
        normalized_text: str,
        compact_text: str,
        profile: type,
    ) -> SourceDetectionResult:
        evidence = []

        score = 0.0

        # ---------------------------------------------------------
        # MARCADORES PRINCIPAIS
        # ---------------------------------------------------------

        source_markers = getattr(
            profile,
            "SOURCE_MARKERS",
            tuple(),
        )

        strong_hits = 0

        for marker in source_markers:
            if self._contains_marker(
                normalized_text=(
                    normalized_text
                ),

                compact_text=(
                    compact_text
                ),

                marker=marker,
            ):
                strong_hits += 1

                evidence.append(
                    (
                        "Marcador principal: "
                        f"{marker}"
                    )
                )

        if strong_hits:
            score += 0.72

            if strong_hits > 1:
                score += min(
                    0.10,
                    (
                        strong_hits - 1
                    ) * 0.05,
                )

        # ---------------------------------------------------------
        # MARCADORES SECUNDÁRIOS
        # ---------------------------------------------------------

        supporting_markers = getattr(
            profile,
            "SUPPORTING_MARKERS",
            tuple(),
        )

        secondary_hits = 0

        for marker in supporting_markers:
            if self._contains_marker(
                normalized_text=(
                    normalized_text
                ),

                compact_text=(
                    compact_text
                ),

                marker=marker,
            ):
                secondary_hits += 1

                evidence.append(
                    (
                        "Estrutura compatível: "
                        f"{marker}"
                    )
                )

        score += min(
            0.24,
            secondary_hits * 0.04,
        )

        # Palavras genéricas sem marcador principal
        # não devem classificar um documento sozinhas.
        if (
            strong_hits == 0
            and secondary_hits > 0
        ):
            score = min(
                score,
                0.45,
            )

        return SourceDetectionResult(
            source_type=getattr(
                profile,
                "SOURCE_TYPE",
                self.UNKNOWN,
            ),

            confidence=min(
                1.0,
                score,
            ),

            evidence=evidence,

            profile=profile,
        )

    # =============================================================
    # COMPARAÇÃO
    # =============================================================

    def _contains_marker(
        self,
        normalized_text: str,
        compact_text: str,
        marker: str,
    ) -> bool:
        normalized_marker = (
            self._normalize(
                marker
            )
        )

        if (
            normalized_marker
            and normalized_marker
            in normalized_text
        ):
            return True

        compact_marker = (
            self._compact(
                marker
            )
        )

        if (
            compact_marker
            and compact_marker
            in compact_text
        ):
            return True

        return False

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

        value = (
            value
            .upper()
            .replace(
                "\u00A0",
                " ",
            )
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    def _compact(
        self,
        value: str,
    ) -> str:
        """
        Remove espaços e pontuação.

        Ex.:

            ZEISS INSP EC T
            ZEISS INSPECT

        tornam-se:

            ZEISSINSPECT
        """

        normalized = (
            self._normalize(
                value
            )
        )

        return re.sub(
            r"[^A-Z0-9]+",
            "",
            normalized,
        )