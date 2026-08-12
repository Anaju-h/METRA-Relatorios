from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Callable, Optional

from services.document_analysis.models import (
    DocumentContent,
    DocumentPage,
    DocumentWord,
    ExtractedField,
)


# ================================================================
# MODELOS INTERNOS
# ================================================================


@dataclass
class AnchorOccurrence:
    """
    Ocorrência de uma âncora identificada em uma página.

    line_words:
        todas as palavras da linha em que a âncora foi encontrada.

    anchor_words:
        somente as palavras que compõem a âncora.

    line_text:
        texto completo da linha.

    Isso é importante porque, por exemplo:

        âncora = "Nome"

    pode estar na linha:

        "Nome da MMC PRISMO"

    Nesse caso o contexto completo precisa ser conhecido,
    senão "Nome" seria confundido com nome da peça.
    """

    anchor_text: str

    page_number: int

    anchor_words: list[DocumentWord]

    line_words: list[DocumentWord]

    line_text: str


@dataclass
class AnchorCandidate:
    """
    Candidato a valor para um determinado campo.
    """

    value: str

    score: float

    page_number: int

    method: str

    anchor_text: str

    source_text: str

    distance: Optional[float] = None


# ================================================================
# ENGINE
# ================================================================


class AnchorEngine:
    """
    Motor genérico de extração baseada em âncoras.

    O engine NÃO conhece CALYPSO, INSPECT, máquina ou regra de negócio.

    Ele recebe:

        anchors
        exclusions
        validator
        candidate_scorer

    e tenta localizar o melhor valor usando várias estratégias:

        1. valor inline após a âncora;
        2. palavras à direita na mesma linha;
        3. linha imediatamente abaixo;
        4. candidato próximo geometricamente;
        5. candidato dentro do mesmo bloco;
        6. combinação e score global.

    O objetivo é ser tolerante a variações de layout sem usar
    coordenadas absolutas fixas.
    """

    # -------------------------------------------------------------
    # CONFIGURAÇÃO GEOMÉTRICA
    # -------------------------------------------------------------

    SAME_LINE_Y_TOLERANCE = 6.0

    MAX_RIGHT_DISTANCE = 420.0

    MAX_BELOW_DISTANCE = 100.0

    MAX_NEAR_DISTANCE_X = 420.0
    MAX_NEAR_DISTANCE_Y = 120.0

    MAX_BLOCK_DISTANCE = 160.0

    # Distância entre palavras para considerar que pertencem
    # ao mesmo valor textual.
    WORD_GAP_LIMIT = 22.0

    # -------------------------------------------------------------
    # SCORE BASE POR ESTRATÉGIA
    # -------------------------------------------------------------

    SCORE_INLINE = 94.0
    SCORE_RIGHT = 82.0
    SCORE_BELOW = 68.0
    SCORE_SAME_BLOCK = 64.0
    SCORE_NEAR = 54.0

    # =============================================================
    # API PRINCIPAL
    # =============================================================

    def extract_field(
        self,
        document: DocumentContent,
        anchors: tuple[str, ...],
        exclusions: tuple[str, ...] = tuple(),
        validator: Callable[[str], bool] | None = None,
        candidate_scorer: Callable[[str], float] | None = None,
    ) -> ExtractedField:
        """
        Extrai o melhor valor associado a uma lista de âncoras.

        Retorna sempre ExtractedField.
        """

        if not anchors:
            return ExtractedField(
                value=None,
                confidence=0.0,
                method="anchor",
            )

        normalized_exclusions = tuple(
            self._normalize(item)
            for item in exclusions
            if item
        )

        candidates: list[AnchorCandidate] = []

        for page in document.pages:
            occurrences = self._find_anchor_occurrences(
                page=page,
                anchors=anchors,
            )

            for occurrence in occurrences:
                # -------------------------------------------------
                # CONTEXTO DA LINHA
                # -------------------------------------------------

                if self._line_is_excluded(
                    occurrence=occurrence,
                    exclusions=normalized_exclusions,
                ):
                    continue

                occurrence_candidates = (
                    self._collect_candidates(
                        page=page,
                        occurrence=occurrence,
                        anchors=anchors,
                        validator=validator,
                        candidate_scorer=candidate_scorer,
                    )
                )

                candidates.extend(
                    occurrence_candidates
                )

        if not candidates:
            return ExtractedField(
                value=None,
                confidence=0.0,
                method="anchor",
            )

        # ---------------------------------------------------------
        # REMOVER DUPLICADOS
        # ---------------------------------------------------------

        candidates = self._deduplicate_candidates(
            candidates
        )

        # ---------------------------------------------------------
        # MELHOR CANDIDATO
        # ---------------------------------------------------------

        best = max(
            candidates,
            key=lambda item: item.score,
        )

        confidence = self._score_to_confidence(
            best.score
        )

        return ExtractedField(
            value=best.value,
            confidence=confidence,
            method=best.method,
            source_page=best.page_number,
            source_text=best.source_text,
        )

    # =============================================================
    # COLETA DE CANDIDATOS
    # =============================================================

    def _collect_candidates(
        self,
        page: DocumentPage,
        occurrence: AnchorOccurrence,
        anchors: tuple[str, ...],
        validator: Callable[[str], bool] | None,
        candidate_scorer: Callable[[str], float] | None,
    ) -> list[AnchorCandidate]:
        result: list[AnchorCandidate] = []

        # ---------------------------------------------------------
        # 1. INLINE
        # ---------------------------------------------------------

        inline_value = self._extract_inline_value_from_occurrence(
            occurrence
        )

        if inline_value:
            candidate = self._build_candidate(
                value=inline_value,
                base_score=self.SCORE_INLINE,
                page_number=page.number,
                method="anchor_inline",
                occurrence=occurrence,
                anchors=anchors,
                validator=validator,
                candidate_scorer=candidate_scorer,
                distance=0.0,
            )

            if candidate:
                result.append(
                    candidate
                )

        # ---------------------------------------------------------
        # 2. DIREITA
        # ---------------------------------------------------------

        for value, distance in self._right_candidates(
            page=page,
            occurrence=occurrence,
        ):
            penalty = min(
                28.0,
                distance / 11.0,
            )

            candidate = self._build_candidate(
                value=value,
                base_score=self.SCORE_RIGHT - penalty,
                page_number=page.number,
                method="anchor_right",
                occurrence=occurrence,
                anchors=anchors,
                validator=validator,
                candidate_scorer=candidate_scorer,
                distance=distance,
            )

            if candidate:
                result.append(
                    candidate
                )

        # ---------------------------------------------------------
        # 3. ABAIXO
        # ---------------------------------------------------------

        for value, distance in self._below_candidates(
            page=page,
            occurrence=occurrence,
        ):
            penalty = min(
                24.0,
                distance / 5.5,
            )

            candidate = self._build_candidate(
                value=value,
                base_score=self.SCORE_BELOW - penalty,
                page_number=page.number,
                method="anchor_below",
                occurrence=occurrence,
                anchors=anchors,
                validator=validator,
                candidate_scorer=candidate_scorer,
                distance=distance,
            )

            if candidate:
                result.append(
                    candidate
                )

        # ---------------------------------------------------------
        # 4. MESMO BLOCO
        # ---------------------------------------------------------

        for value, distance in self._same_block_candidates(
            page=page,
            occurrence=occurrence,
        ):
            penalty = min(
                20.0,
                distance / 8.0,
            )

            candidate = self._build_candidate(
                value=value,
                base_score=(
                    self.SCORE_SAME_BLOCK
                    - penalty
                ),
                page_number=page.number,
                method="anchor_same_block",
                occurrence=occurrence,
                anchors=anchors,
                validator=validator,
                candidate_scorer=candidate_scorer,
                distance=distance,
            )

            if candidate:
                result.append(
                    candidate
                )

        # ---------------------------------------------------------
        # 5. PROXIMIDADE GEOMÉTRICA
        # ---------------------------------------------------------

        for value, distance in self._near_candidates(
            page=page,
            occurrence=occurrence,
        ):
            penalty = min(
                18.0,
                distance / 18.0,
            )

            candidate = self._build_candidate(
                value=value,
                base_score=(
                    self.SCORE_NEAR
                    - penalty
                ),
                page_number=page.number,
                method="anchor_near",
                occurrence=occurrence,
                anchors=anchors,
                validator=validator,
                candidate_scorer=candidate_scorer,
                distance=distance,
            )

            if candidate:
                result.append(
                    candidate
                )

        return result

    # =============================================================
    # CONSTRUIR CANDIDATO
    # =============================================================

    def _build_candidate(
        self,
        value: str,
        base_score: float,
        page_number: int,
        method: str,
        occurrence: AnchorOccurrence,
        anchors: tuple[str, ...],
        validator: Callable[[str], bool] | None,
        candidate_scorer: Callable[[str], float] | None,
        distance: Optional[float],
    ) -> AnchorCandidate | None:
        clean = self._clean_value(
            value
        )

        if not clean:
            return None

        # Não aceitar outro label como valor.
        if self._looks_like_anchor(
            value=clean,
            anchors=anchors,
        ):
            return None

        # Evita capturar partes residuais do próprio label.
        if self._looks_like_label_fragment(
            value=clean,
            occurrence=occurrence,
        ):
            return None

        if validator is not None:
            try:
                if not validator(clean):
                    return None

            except Exception:
                return None

        extra_score = self._extra_score(
            value=clean,
            scorer=candidate_scorer,
        )

        score = (
            base_score
            + extra_score
        )

        # Pequeno bônus por candidato textual razoável.
        score += self._generic_value_score(
            clean
        )

        return AnchorCandidate(
            value=clean,
            score=score,
            page_number=page_number,
            method=method,
            anchor_text=occurrence.anchor_text,
            source_text=occurrence.line_text,
            distance=distance,
        )

    # =============================================================
    # DETECÇÃO DAS ÂNCORAS
    # =============================================================

    def _find_anchor_occurrences(
        self,
        page: DocumentPage,
        anchors: tuple[str, ...],
    ) -> list[AnchorOccurrence]:
        occurrences: list[
            AnchorOccurrence
        ] = []

        lines = self._group_words_by_pdf_line(
            page.words
        )

        for line_words in lines:
            if not line_words:
                continue

            line_words = sorted(
                line_words,
                key=lambda word: word.x0,
            )

            line_text = " ".join(
                word.text
                for word in line_words
            ).strip()

            normalized_line = self._normalize(
                line_text
            )

            for anchor in anchors:
                normalized_anchor = (
                    self._normalize(
                        anchor
                    )
                )

                if not normalized_anchor:
                    continue

                if (
                    normalized_anchor
                    not in normalized_line
                ):
                    continue

                anchor_words = self._locate_anchor_words(
                    line_words=line_words,
                    anchor=anchor,
                )

                if not anchor_words:
                    continue

                occurrences.append(
                    AnchorOccurrence(
                        anchor_text=anchor,
                        page_number=page.number,
                        anchor_words=anchor_words,
                        line_words=line_words,
                        line_text=line_text,
                    )
                )

        # Âncoras mais específicas primeiro.
        occurrences.sort(
            key=lambda item: len(
                self._normalize(
                    item.anchor_text
                )
            ),
            reverse=True,
        )

        return occurrences

    # =============================================================
    # AGRUPAMENTO DE LINHAS
    # =============================================================

    def _group_words_by_pdf_line(
        self,
        words: list[DocumentWord],
    ) -> list[list[DocumentWord]]:
        """
        Primeiro tenta usar block_number + line_number do PyMuPDF.
        """

        grouped: dict[
            tuple[int | None, int | None],
            list[DocumentWord],
        ] = {}

        for word in words:
            key = (
                word.block_number,
                word.line_number,
            )

            grouped.setdefault(
                key,
                [],
            ).append(
                word
            )

        return list(
            grouped.values()
        )

    def _group_words_by_visual_line(
        self,
        words: list[DocumentWord],
    ) -> list[list[DocumentWord]]:
        """
        Agrupamento independente da estrutura interna do PDF.
        Usa a posição vertical das palavras.
        """

        sorted_words = sorted(
            words,
            key=lambda word: (
                word.center_y,
                word.x0,
            ),
        )

        lines: list[
            list[DocumentWord]
        ] = []

        current_line: list[
            DocumentWord
        ] = []

        current_y: float | None = None

        for word in sorted_words:
            if current_y is None:
                current_line = [
                    word
                ]

                current_y = word.center_y

                continue

            if abs(
                word.center_y
                - current_y
            ) <= self.SAME_LINE_Y_TOLERANCE:
                current_line.append(
                    word
                )

                current_y = (
                    sum(
                        item.center_y
                        for item
                        in current_line
                    )
                    / len(
                        current_line
                    )
                )

            else:
                lines.append(
                    sorted(
                        current_line,
                        key=lambda item:
                            item.x0,
                    )
                )

                current_line = [
                    word
                ]

                current_y = word.center_y

        if current_line:
            lines.append(
                sorted(
                    current_line,
                    key=lambda item:
                        item.x0,
                )
            )

        return lines

    # =============================================================
    # LOCALIZAR PALAVRAS DA ÂNCORA
    # =============================================================

    def _locate_anchor_words(
        self,
        line_words: list[DocumentWord],
        anchor: str,
    ) -> list[DocumentWord]:
        anchor_parts = (
            self._normalize(
                anchor
            )
            .split()
        )

        if not anchor_parts:
            return []

        word_norms = [
            self._normalize(
                word.text
            )
            for word in line_words
        ]

        size = len(
            anchor_parts
        )

        for start in range(
            len(word_norms)
            - size
            + 1
        ):
            fragment = (
                word_norms[
                    start:
                    start + size
                ]
            )

            if fragment == anchor_parts:
                return (
                    line_words[
                        start:
                        start + size
                    ]
                )

        return []

    # =============================================================
    # EXCLUSÕES PELO CONTEXTO
    # =============================================================

    def _line_is_excluded(
        self,
        occurrence: AnchorOccurrence,
        exclusions: tuple[str, ...],
    ) -> bool:
        if not exclusions:
            return False

        normalized_line = self._normalize(
            occurrence.line_text
        )

        for exclusion in exclusions:
            if (
                exclusion
                and exclusion
                in normalized_line
            ):
                return True

        return False

    # =============================================================
    # INLINE
    # =============================================================

    def _extract_inline_value_from_occurrence(
        self,
        occurrence: AnchorOccurrence,
    ) -> str | None:
        """
        Extrai o que está depois das palavras da âncora
        dentro da própria linha estrutural.
        """

        anchor_words = (
            occurrence.anchor_words
        )

        line_words = (
            occurrence.line_words
        )

        if not anchor_words:
            return None

        last_anchor_word = (
            anchor_words[-1]
        )

        remaining = [
            word
            for word in line_words
            if word.x0
            > last_anchor_word.x1 - 1
            and word not in anchor_words
        ]

        if not remaining:
            return None

        remaining.sort(
            key=lambda word: word.x0
        )

        groups = self._group_neighbor_words(
            remaining
        )

        if not groups:
            return None

        return " ".join(
            word.text
            for word in groups[0]
        ).strip()

    # =============================================================
    # À DIREITA
    # =============================================================

    def _right_candidates(
        self,
        page: DocumentPage,
        occurrence: AnchorOccurrence,
    ) -> list[tuple[str, float]]:
        anchor_words = (
            occurrence.anchor_words
        )

        anchor_right = max(
            word.x1
            for word in anchor_words
        )

        anchor_center_y = (
            sum(
                word.center_y
                for word in anchor_words
            )
            / len(
                anchor_words
            )
        )

        words = []

        for word in page.words:
            if word in anchor_words:
                continue

            y_distance = abs(
                word.center_y
                - anchor_center_y
            )

            if (
                y_distance
                > self.SAME_LINE_Y_TOLERANCE
            ):
                continue

            x_distance = (
                word.x0
                - anchor_right
            )

            if x_distance < -1:
                continue

            if (
                x_distance
                > self.MAX_RIGHT_DISTANCE
            ):
                continue

            words.append(
                word
            )

        if not words:
            return []

        words.sort(
            key=lambda word: word.x0
        )

        groups = self._group_neighbor_words(
            words
        )

        result = []

        for group in groups:
            if not group:
                continue

            value = " ".join(
                word.text
                for word in group
            ).strip()

            distance = max(
                0.0,
                group[0].x0
                - anchor_right,
            )

            result.append(
                (
                    value,
                    distance,
                )
            )

        return result

    # =============================================================
    # ABAIXO
    # =============================================================

    def _below_candidates(
        self,
        page: DocumentPage,
        occurrence: AnchorOccurrence,
    ) -> list[tuple[str, float]]:
        anchor_words = (
            occurrence.anchor_words
        )

        anchor_left = min(
            word.x0
            for word in anchor_words
        )

        anchor_right = max(
            word.x1
            for word in anchor_words
        )

        anchor_bottom = max(
            word.y1
            for word in anchor_words
        )

        visual_lines = (
            self._group_words_by_visual_line(
                page.words
            )
        )

        candidates = []

        for line_words in visual_lines:
            if not line_words:
                continue

            # Não usar a mesma linha da âncora.
            if any(
                word in anchor_words
                for word in line_words
            ):
                continue

            line_top = min(
                word.y0
                for word in line_words
            )

            vertical_distance = (
                line_top
                - anchor_bottom
            )

            if (
                vertical_distance <= 0
                or vertical_distance
                > self.MAX_BELOW_DISTANCE
            ):
                continue

            line_left = min(
                word.x0
                for word in line_words
            )

            line_right = max(
                word.x1
                for word in line_words
            )

            # Precisa haver proximidade horizontal.
            overlaps_anchor = (
                line_right
                >= anchor_left - 30
                and line_left
                <= anchor_right + 320
            )

            if not overlaps_anchor:
                continue

            value_words = self._prefer_words_near_anchor_x(
                words=line_words,
                anchor_left=anchor_left,
                anchor_right=anchor_right,
            )

            if not value_words:
                continue

            value = " ".join(
                word.text
                for word in value_words
            ).strip()

            if not value:
                continue

            candidates.append(
                (
                    value,
                    vertical_distance,
                )
            )

        candidates.sort(
            key=lambda item: item[1]
        )

        return candidates[:6]

    # =============================================================
    # MESMO BLOCO
    # =============================================================

    def _same_block_candidates(
        self,
        page: DocumentPage,
        occurrence: AnchorOccurrence,
    ) -> list[tuple[str, float]]:
        block_numbers = {
            word.block_number
            for word in occurrence.anchor_words
            if word.block_number
            is not None
        }

        if not block_numbers:
            return []

        anchor_right = max(
            word.x1
            for word in occurrence.anchor_words
        )

        anchor_bottom = max(
            word.y1
            for word in occurrence.anchor_words
        )

        candidates = []

        for block_number in block_numbers:
            block_words = [
                word
                for word in page.words
                if (
                    word.block_number
                    == block_number
                    and word
                    not in occurrence.anchor_words
                )
            ]

            if not block_words:
                continue

            visual_lines = (
                self._group_words_by_visual_line(
                    block_words
                )
            )

            for line_words in visual_lines:
                if not line_words:
                    continue

                # Não capturar palavras que são claramente
                # anteriores à âncora.
                if max(
                    word.x1
                    for word in line_words
                ) < min(
                    word.x0
                    for word
                    in occurrence.anchor_words
                ):
                    continue

                value = " ".join(
                    word.text
                    for word in line_words
                ).strip()

                if not value:
                    continue

                x = min(
                    word.x0
                    for word in line_words
                )

                y = min(
                    word.y0
                    for word in line_words
                )

                distance = (
                    abs(
                        x - anchor_right
                    )
                    + abs(
                        y - anchor_bottom
                    )
                )

                if (
                    distance
                    > self.MAX_BLOCK_DISTANCE
                ):
                    continue

                candidates.append(
                    (
                        value,
                        distance,
                    )
                )

        candidates.sort(
            key=lambda item: item[1]
        )

        return candidates[:6]

    # =============================================================
    # PROXIMIDADE GEOMÉTRICA
    # =============================================================

    def _near_candidates(
        self,
        page: DocumentPage,
        occurrence: AnchorOccurrence,
    ) -> list[tuple[str, float]]:
        anchor_left = min(
            word.x0
            for word in occurrence.anchor_words
        )

        anchor_right = max(
            word.x1
            for word in occurrence.anchor_words
        )

        anchor_top = min(
            word.y0
            for word in occurrence.anchor_words
        )

        anchor_bottom = max(
            word.y1
            for word in occurrence.anchor_words
        )

        anchor_center_x = (
            anchor_left
            + anchor_right
        ) / 2

        anchor_center_y = (
            anchor_top
            + anchor_bottom
        ) / 2

        lines = self._group_words_by_visual_line(
            page.words
        )

        candidates = []

        for line_words in lines:
            if any(
                word
                in occurrence.anchor_words
                for word in line_words
            ):
                continue

            line_left = min(
                word.x0
                for word in line_words
            )

            line_right = max(
                word.x1
                for word in line_words
            )

            line_top = min(
                word.y0
                for word in line_words
            )

            line_bottom = max(
                word.y1
                for word in line_words
            )

            line_center_x = (
                line_left
                + line_right
            ) / 2

            line_center_y = (
                line_top
                + line_bottom
            ) / 2

            dx = abs(
                line_center_x
                - anchor_center_x
            )

            dy = abs(
                line_center_y
                - anchor_center_y
            )

            if dx > self.MAX_NEAR_DISTANCE_X:
                continue

            if dy > self.MAX_NEAR_DISTANCE_Y:
                continue

            # Evita elementos muito acima do label,
            # a menos que estejam claramente à direita.
            if (
                line_bottom
                < anchor_top - 15
                and line_left
                < anchor_right
            ):
                continue

            distance = (
                dx
                + dy * 1.6
            )

            value = " ".join(
                word.text
                for word in line_words
            ).strip()

            if not value:
                continue

            candidates.append(
                (
                    value,
                    distance,
                )
            )

        candidates.sort(
            key=lambda item: item[1]
        )

        return candidates[:8]

    # =============================================================
    # PALAVRAS PRÓXIMAS
    # =============================================================

    def _group_neighbor_words(
        self,
        words: list[DocumentWord],
    ) -> list[list[DocumentWord]]:
        if not words:
            return []

        words = sorted(
            words,
            key=lambda word: word.x0,
        )

        groups = []

        current = [
            words[0]
        ]

        previous = words[0]

        for word in words[1:]:
            gap = (
                word.x0
                - previous.x1
            )

            same_visual_line = (
                abs(
                    word.center_y
                    - previous.center_y
                )
                <= self.SAME_LINE_Y_TOLERANCE
            )

            if (
                gap <= self.WORD_GAP_LIMIT
                and same_visual_line
            ):
                current.append(
                    word
                )

            else:
                groups.append(
                    current
                )

                current = [
                    word
                ]

            previous = word

        if current:
            groups.append(
                current
            )

        return groups

    # =============================================================
    # FILTRAR PALAVRAS ABAIXO
    # =============================================================

    def _prefer_words_near_anchor_x(
        self,
        words: list[DocumentWord],
        anchor_left: float,
        anchor_right: float,
    ) -> list[DocumentWord]:
        """
        Quando a linha abaixo contém vários campos,
        tenta pegar a região mais próxima horizontalmente
        da âncora.
        """

        if not words:
            return []

        groups = self._group_neighbor_words(
            words
        )

        if not groups:
            return []

        scored = []

        anchor_center = (
            anchor_left
            + anchor_right
        ) / 2

        for group in groups:
            group_left = min(
                word.x0
                for word in group
            )

            group_right = max(
                word.x1
                for word in group
            )

            group_center = (
                group_left
                + group_right
            ) / 2

            distance = abs(
                group_center
                - anchor_center
            )

            scored.append(
                (
                    distance,
                    group,
                )
            )

        scored.sort(
            key=lambda item: item[0]
        )

        return scored[0][1]

    # =============================================================
    # DETECTAR OUTRO LABEL
    # =============================================================

    def _looks_like_anchor(
        self,
        value: str,
        anchors: tuple[str, ...],
    ) -> bool:
        normalized = self._normalize(
            value
        )

        for anchor in anchors:
            anchor_norm = self._normalize(
                anchor
            )

            if not anchor_norm:
                continue

            if normalized == anchor_norm:
                return True

        return False

    def _looks_like_label_fragment(
        self,
        value: str,
        occurrence: AnchorOccurrence,
    ) -> bool:
        """
        Evita casos como:

            âncora = Nome
            linha = Nome da MMC

        candidato = "da MMC"

        O valor é claramente continuação do próprio label.
        """

        normalized_value = self._normalize(
            value
        )

        normalized_line = self._normalize(
            occurrence.line_text
        )

        normalized_anchor = self._normalize(
            occurrence.anchor_text
        )

        if not normalized_value:
            return True

        # ---------------------------------------------------------
        # Padrões típicos de continuação de label
        # ---------------------------------------------------------

        label_fragments = {
            "DA MMC",
            "DO MMC",
            "DA PECA",
            "DA PEÇA",
            "DO OPERADOR",
            "DA MEDICAO",
            "DA MEDIÇÃO",
        }

        if normalized_value in label_fragments:
            return True

        # ---------------------------------------------------------
        # Se anchor + candidato forma expressão típica
        # conhecida como um label completo.
        # ---------------------------------------------------------

        composed = (
            f"{normalized_anchor} "
            f"{normalized_value}"
        ).strip()

        common_labels = {
            "NOME DA MMC",
            "NUMERO DA MMC",
            "NÚMERO DA MMC",
            "NOME DA PECA",
            "NOME DA PEÇA",
            "NUMERO DA PECA",
            "NÚMERO DA PEÇA",
        }

        common_labels = {
            self._normalize(item)
            for item in common_labels
        }

        if composed in common_labels:
            return True

        # ---------------------------------------------------------
        # Se a linha inteira é basicamente o label composto.
        # ---------------------------------------------------------

        if (
            composed
            == normalized_line
            and len(
                normalized_value.split()
            ) <= 3
        ):
            return True

        return False

    # =============================================================
    # SCORE GENÉRICO
    # =============================================================

    def _generic_value_score(
        self,
        value: str,
    ) -> float:
        """
        Pequenos ajustes genéricos que não dependem do campo.
        """

        score = 0.0

        clean = value.strip()

        if not clean:
            return -100.0

        # Textos absurdamente longos provavelmente são bloco inteiro.
        if len(clean) > 180:
            score -= 25.0

        elif len(clean) <= 80:
            score += 3.0

        # Uma linha inteira cheia de labels costuma ser ruim.
        label_words = (
            "NOME",
            "OPERADOR",
            "DATA/HORA",
            "NOMINAL",
            "MEDIDO",
            "MEASURED",
            "TOL",
        )

        upper = self._normalize(
            clean
        )

        label_hits = sum(
            1
            for item in label_words
            if item in upper
        )

        if label_hits >= 3:
            score -= 15.0

        return score

    # =============================================================
    # SCORE ESPECÍFICO
    # =============================================================

    def _extra_score(
        self,
        value: str,
        scorer: Callable[
            [str],
            float,
        ]
        | None,
    ) -> float:
        if scorer is None:
            return 0.0

        try:
            return float(
                scorer(
                    value
                )
            )

        except Exception:
            return 0.0

    # =============================================================
    # DEDUPLICAÇÃO
    # =============================================================

    def _deduplicate_candidates(
        self,
        candidates: list[
            AnchorCandidate
        ],
    ) -> list[
        AnchorCandidate
    ]:
        """
        Mantém uma ocorrência por:

            valor normalizado + página

        escolhendo o maior score.
        """

        best_by_key: dict[
            tuple[str, int],
            AnchorCandidate,
        ] = {}

        for candidate in candidates:
            key = (
                self._normalize(
                    candidate.value
                ),
                candidate.page_number,
            )

            existing = (
                best_by_key.get(
                    key
                )
            )

            if (
                existing is None
                or candidate.score
                > existing.score
            ):
                best_by_key[
                    key
                ] = candidate

        return list(
            best_by_key.values()
        )

    # =============================================================
    # LIMPEZA
    # =============================================================

    def _clean_value(
        self,
        value: str,
    ) -> str:
        clean = (
            value
            .replace(
                "\u00A0",
                " ",
            )
            .strip()
        )

        # Remove separadores comuns no começo/fim.
        clean = re.sub(
            r"^[\s:;=\-–—]+",
            "",
            clean,
        )

        clean = re.sub(
            r"[\s:;=\-–—]+$",
            "",
            clean,
        )

        clean = re.sub(
            r"[ \t]+",
            " ",
            clean,
        )

        return clean.strip()

    # =============================================================
    # CONFIANÇA
    # =============================================================

    def _score_to_confidence(
        self,
        score: float,
    ) -> float:
        """
        Converte score aberto em confiança 0..1.

        Scores >= 100 são considerados confiança máxima.
        """

        return max(
            0.0,
            min(
                1.0,
                score / 100.0,
            ),
        )

    # =============================================================
    # NORMALIZAÇÃO
    # =============================================================

    def _normalize(
        self,
        value: str,
    ) -> str:
        value = unicodedata.normalize(
            "NFKD",
            value or "",
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