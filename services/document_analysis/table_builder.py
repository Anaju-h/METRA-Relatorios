from __future__ import annotations

import statistics
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Optional

from services.document_analysis.models import (
    DocumentPage,
    DocumentWord,
)


# =================================================================
# MODELOS ESPACIAIS
# =================================================================


@dataclass
class SpatialLine:
    """
    Linha visual reconstruída a partir das coordenadas das palavras.
    """

    words: list[DocumentWord] = field(
        default_factory=list
    )

    y_center: float = 0.0

    x0: float = 0.0
    x1: float = 0.0

    y0: float = 0.0
    y1: float = 0.0

    text: str = ""

    @property
    def height(self) -> float:
        return max(
            0.0,
            self.y1 - self.y0,
        )


@dataclass
class BuiltColumn:
    """
    Coluna reconstruída da tabela.

    left_boundary e right_boundary representam os limites usados
    para associar palavras às células.
    """

    field_name: str

    header_text: str

    x_center: float

    x0: float
    x1: float

    left_boundary: float = 0.0
    right_boundary: float = 0.0

    header_y: float = 0.0


@dataclass
class BuiltCell:
    """
    Célula reconstruída de uma linha.
    """

    field_name: str

    text: str

    words: list[DocumentWord] = field(
        default_factory=list
    )

    x0: Optional[float] = None
    x1: Optional[float] = None

    y0: Optional[float] = None
    y1: Optional[float] = None


@dataclass
class BuiltRow:
    """
    Linha tabular já separada por colunas.
    """

    cells: dict[str, BuiltCell] = field(
        default_factory=dict
    )

    source_words: list[DocumentWord] = field(
        default_factory=list
    )

    source_text: str = ""

    y_center: float = 0.0

    page_number: int = 0

    confidence: float = 0.0

    @property
    def values(self) -> dict[str, str]:
        return {
            field_name: cell.text
            for field_name, cell in self.cells.items()
        }

    def get(
        self,
        field_name: str,
        default: str = "",
    ) -> str:
        cell = self.cells.get(
            field_name
        )

        if cell is None:
            return default

        return cell.text


@dataclass
class BuiltTable:
    """
    Tabela reconstruída em uma página.
    """

    page_number: int

    columns: list[BuiltColumn] = field(
        default_factory=list
    )

    rows: list[BuiltRow] = field(
        default_factory=list
    )

    header_text: str = ""

    header_y: float = 0.0

    start_y: float = 0.0
    end_y: float = 0.0

    confidence: float = 0.0

    warnings: list[str] = field(
        default_factory=list
    )


# =================================================================
# CONSTRUTOR
# =================================================================


class SpatialTableBuilder:
    """
    Reconstrói tabelas utilizando apenas posição espacial.

    O construtor não conhece CALYPSO, ZEISS INSPECT ou Bosello.

    O perfil documental fornece somente os aliases dos cabeçalhos:

        TABLE_HEADERS = {
            "name": (...),
            "measured_value": (...),
            ...
        }

    Processo:

        palavras
            ↓
        linhas visuais
            ↓
        possíveis cabeçalhos
            ↓
        colunas
            ↓
        limites horizontais
            ↓
        linhas de dados
            ↓
        células
    """

    # Diferença vertical máxima para palavras serem tratadas
    # como pertencentes à mesma linha visual.
    DEFAULT_Y_TOLERANCE = 4.5

    # Distância máxima entre partes de um cabeçalho composto,
    # proporcional à altura média das palavras.
    HEADER_GAP_FACTOR = 2.8

    # Quantidade mínima de colunas reconhecidas para considerar
    # uma linha como cabeçalho de tabela.
    MINIMUM_HEADER_COLUMNS = 3

    # Quantidade mínima de células não vazias em uma linha.
    MINIMUM_ROW_CELLS = 2

    # Margem após o cabeçalho antes da primeira linha de dados.
    HEADER_BOTTOM_MARGIN = 2.0

    # Distância vertical muito grande pode indicar o fim da tabela.
    MAX_ROW_GAP_FACTOR = 4.5

    # Número máximo de linhas vazias consecutivas antes de encerrar.
    MAX_EMPTY_LINES = 3

    def build(
        self,
        page: DocumentPage,
        profile: type,
    ) -> list[BuiltTable]:
        """
        Reconstrói todas as tabelas reconhecíveis da página.
        """

        words = self._valid_words(
            page.words
        )

        if not words:
            return []

        visual_lines = self.group_visual_lines(
            words
        )

        if not visual_lines:
            return []

        table_headers = getattr(
            profile,
            "TABLE_HEADERS",
            {},
        )

        if not table_headers:
            return []

        header_candidates = (
            self._find_header_candidates(
                lines=visual_lines,
                table_headers=table_headers,
            )
        )

        if not header_candidates:
            return []

        tables = []

        for candidate_index, (
            line_index,
            columns,
        ) in enumerate(
            header_candidates
        ):
            next_header_index = None

            if (
                candidate_index + 1
                < len(header_candidates)
            ):
                next_header_index = (
                    header_candidates[
                        candidate_index + 1
                    ][0]
                )

            table = self._build_table_from_header(
                page=page,
                lines=visual_lines,
                header_line_index=line_index,
                columns=columns,
                next_header_line_index=(
                    next_header_index
                ),
                profile=profile,
            )

            if table.rows:
                tables.append(
                    table
                )

        return self._deduplicate_tables(
            tables
        )

    # =================================================================
    # LINHAS VISUAIS
    # =================================================================

    def group_visual_lines(
        self,
        words: Iterable[DocumentWord],
    ) -> list[SpatialLine]:
        """
        Agrupa palavras pela posição Y sem depender de block_number
        ou line_number do PDF.

        Isso é importante porque diferentes exportações do CALYPSO
        podem gerar blocos internos diferentes.
        """

        valid_words = self._valid_words(
            words
        )

        if not valid_words:
            return []

        word_heights = [
            max(
                1.0,
                float(
                    word.y1 - word.y0
                ),
            )
            for word in valid_words
        ]

        median_height = statistics.median(
            word_heights
        )

        dynamic_tolerance = max(
            self.DEFAULT_Y_TOLERANCE,
            median_height * 0.42,
        )

        sorted_words = sorted(
            valid_words,
            key=lambda word: (
                word.center_y,
                word.x0,
            ),
        )

        groups: list[
            list[DocumentWord]
        ] = []

        current_group: list[
            DocumentWord
        ] = []

        current_center_y: (
            float
            | None
        ) = None

        for word in sorted_words:
            if current_center_y is None:
                current_group = [
                    word
                ]

                current_center_y = (
                    word.center_y
                )

                continue

            difference = abs(
                word.center_y
                - current_center_y
            )

            if difference <= dynamic_tolerance:
                current_group.append(
                    word
                )

                current_center_y = (
                    sum(
                        item.center_y
                        for item in current_group
                    )
                    / len(
                        current_group
                    )
                )

            else:
                groups.append(
                    current_group
                )

                current_group = [
                    word
                ]

                current_center_y = (
                    word.center_y
                )

        if current_group:
            groups.append(
                current_group
            )

        lines = [
            self._create_spatial_line(
                group
            )
            for group in groups
            if group
        ]

        return sorted(
            lines,
            key=lambda line: (
                line.y_center,
                line.x0,
            ),
        )

    def _create_spatial_line(
        self,
        words: list[DocumentWord],
    ) -> SpatialLine:
        ordered_words = sorted(
            words,
            key=lambda word:
                word.x0,
        )

        return SpatialLine(
            words=ordered_words,

            y_center=(
                sum(
                    word.center_y
                    for word in ordered_words
                )
                / len(
                    ordered_words
                )
            ),

            x0=min(
                word.x0
                for word in ordered_words
            ),

            x1=max(
                word.x1
                for word in ordered_words
            ),

            y0=min(
                word.y0
                for word in ordered_words
            ),

            y1=max(
                word.y1
                for word in ordered_words
            ),

            text=self._join_words(
                ordered_words
            ),
        )

    # =================================================================
    # CABEÇALHOS
    # =================================================================

    def _find_header_candidates(
        self,
        lines: list[SpatialLine],
        table_headers: dict[
            str,
            tuple[str, ...],
        ],
    ) -> list[
        tuple[
            int,
            list[BuiltColumn],
        ]
    ]:
        candidates = []

        for index, line in enumerate(
            lines
        ):
            columns = self._detect_columns_in_line(
                line=line,
                table_headers=table_headers,
            )

            if (
                len(columns)
                < self.MINIMUM_HEADER_COLUMNS
            ):
                continue

            candidates.append(
                (
                    index,
                    columns,
                )
            )

        return candidates

    def _detect_columns_in_line(
        self,
        line: SpatialLine,
        table_headers: dict[
            str,
            tuple[str, ...],
        ],
    ) -> list[BuiltColumn]:
        found_columns = []

        for (
            field_name,
            aliases,
        ) in table_headers.items():
            match = self._find_alias_in_words(
                words=line.words,
                aliases=aliases,
            )

            if not match:
                continue

            matched_words, matched_alias = (
                match
            )

            x0 = min(
                word.x0
                for word in matched_words
            )

            x1 = max(
                word.x1
                for word in matched_words
            )

            found_columns.append(
                BuiltColumn(
                    field_name=field_name,

                    header_text=matched_alias,

                    x_center=(
                        x0 + x1
                    ) / 2.0,

                    x0=x0,
                    x1=x1,

                    header_y=(
                        line.y_center
                    ),
                )
            )

        found_columns = self._remove_overlapping_columns(
            found_columns
        )

        found_columns.sort(
            key=lambda column:
                column.x_center
        )

        self._calculate_column_boundaries(
            found_columns,
            line=line,
        )

        return found_columns

    def _find_alias_in_words(
        self,
        words: list[DocumentWord],
        aliases: tuple[str, ...],
    ) -> Optional[
        tuple[
            list[DocumentWord],
            str,
        ]
    ]:
        if not words:
            return None

        normalized_words = [
            self._normalize(
                word.text
            )
            for word in words
        ]

        aliases_sorted = sorted(
            aliases,
            key=lambda alias:
                len(
                    self._normalize(
                        alias
                    ).split()
                ),
            reverse=True,
        )

        for alias in aliases_sorted:
            alias_parts = (
                self._normalize(
                    alias
                )
                .split()
            )

            if not alias_parts:
                continue

            alias_size = len(
                alias_parts
            )

            for start_index in range(
                len(normalized_words)
                - alias_size
                + 1
            ):
                fragment = normalized_words[
                    start_index:
                    start_index + alias_size
                ]

                if fragment != alias_parts:
                    continue

                matched_words = words[
                    start_index:
                    start_index + alias_size
                ]

                if not self._header_words_are_close(
                    matched_words
                ):
                    continue

                return (
                    matched_words,
                    alias,
                )

        return None

    def _header_words_are_close(
        self,
        words: list[DocumentWord],
    ) -> bool:
        if len(words) <= 1:
            return True

        heights = [
            max(
                1.0,
                word.y1 - word.y0,
            )
            for word in words
        ]

        average_height = sum(
            heights
        ) / len(
            heights
        )

        maximum_gap = (
            average_height
            * self.HEADER_GAP_FACTOR
        )

        ordered = sorted(
            words,
            key=lambda word:
                word.x0,
        )

        for first, second in zip(
            ordered,
            ordered[1:],
        ):
            gap = (
                second.x0
                - first.x1
            )

            if gap > maximum_gap:
                return False

        return True

    def _remove_overlapping_columns(
        self,
        columns: list[BuiltColumn],
    ) -> list[BuiltColumn]:
        """
        Evita que aliases diferentes reconheçam exatamente a mesma
        área do cabeçalho.
        """

        result: list[
            BuiltColumn
        ] = []

        for candidate in sorted(
            columns,
            key=lambda column: (
                column.x0,
                -(
                    column.x1
                    - column.x0
                ),
            ),
        ):
            overlapping_index = None

            for index, existing in enumerate(
                result
            ):
                overlap = self._horizontal_overlap_ratio(
                    candidate.x0,
                    candidate.x1,
                    existing.x0,
                    existing.x1,
                )

                if overlap >= 0.72:
                    overlapping_index = index

                    break

            if overlapping_index is None:
                result.append(
                    candidate
                )

                continue

            existing = result[
                overlapping_index
            ]

            candidate_width = (
                candidate.x1
                - candidate.x0
            )

            existing_width = (
                existing.x1
                - existing.x0
            )

            if candidate_width > existing_width:
                result[
                    overlapping_index
                ] = candidate

        return result

    def _calculate_column_boundaries(
        self,
        columns: list[BuiltColumn],
        line: SpatialLine,
    ) -> None:
        if not columns:
            return

        columns.sort(
            key=lambda column:
                column.x_center
        )

        boundaries = []

        for current, next_column in zip(
            columns,
            columns[1:],
        ):
            boundary = (
                current.x_center
                + next_column.x_center
            ) / 2.0

            boundaries.append(
                boundary
            )

        page_left = min(
            line.x0,
            columns[0].x0,
        )

        page_right = max(
            line.x1,
            columns[-1].x1,
        )

        for index, column in enumerate(
            columns
        ):
            if index == 0:
                left_boundary = (
                    page_left
                    - max(
                        12.0,
                        column.x1
                        - column.x0,
                    )
                )

            else:
                left_boundary = boundaries[
                    index - 1
                ]

            if index == len(
                columns
            ) - 1:
                right_boundary = (
                    page_right
                    + max(
                        12.0,
                        column.x1
                        - column.x0,
                    )
                )

            else:
                right_boundary = boundaries[
                    index
                ]

            column.left_boundary = (
                left_boundary
            )

            column.right_boundary = (
                right_boundary
            )

    # =================================================================
    # CONSTRUÇÃO DA TABELA
    # =================================================================

    def _build_table_from_header(
        self,
        page: DocumentPage,
        lines: list[SpatialLine],
        header_line_index: int,
        columns: list[BuiltColumn],
        next_header_line_index: Optional[int],
        profile: type,
    ) -> BuiltTable:
        header_line = lines[
            header_line_index
        ]

        table = BuiltTable(
            page_number=page.number,

            columns=columns,

            header_text=(
                header_line.text
            ),

            header_y=(
                header_line.y_center
            ),

            start_y=(
                header_line.y1
            ),

            end_y=(
                header_line.y1
            ),
        )

        candidate_lines = lines[
            header_line_index + 1:
            next_header_line_index
        ]

        average_line_height = self._average_line_height(
            candidate_lines
        )

        maximum_gap = max(
            18.0,
            average_line_height
            * self.MAX_ROW_GAP_FACTOR,
        )

        previous_data_y: (
            float
            | None
        ) = None

        empty_lines = 0

        for line in candidate_lines:
            if (
                line.y_center
                <= header_line.y1
                + self.HEADER_BOTTOM_MARGIN
            ):
                continue

            if (
                previous_data_y is not None
                and (
                    line.y_center
                    - previous_data_y
                ) > maximum_gap
            ):
                if self._looks_like_new_section(
                    line=line,
                    profile=profile,
                ):
                    break

            built_row = self._build_row(
                line=line,
                columns=columns,
                page_number=page.number,
            )

            if built_row is None:
                empty_lines += 1

                if (
                    empty_lines
                    >= self.MAX_EMPTY_LINES
                    and table.rows
                ):
                    break

                continue

            empty_lines = 0

            table.rows.append(
                built_row
            )

            previous_data_y = (
                line.y_center
            )

            table.end_y = max(
                table.end_y,
                line.y1,
            )

        table.confidence = (
            self._calculate_table_confidence(
                table
            )
        )

        if not table.rows:
            table.warnings.append(
                (
                    "O cabeçalho foi identificado, "
                    "mas nenhuma linha válida foi reconstruída."
                )
            )

        return table

    def _build_row(
        self,
        line: SpatialLine,
        columns: list[BuiltColumn],
        page_number: int,
    ) -> Optional[BuiltRow]:
        assignments: dict[
            str,
            list[DocumentWord],
        ] = {
            column.field_name: []
            for column in columns
        }

        for word in line.words:
            target_column = (
                self._find_target_column(
                    word=word,
                    columns=columns,
                )
            )

            if target_column is None:
                continue

            assignments[
                target_column.field_name
            ].append(
                word
            )

        cells = {}

        for (
            field_name,
            field_words,
        ) in assignments.items():
            ordered_words = sorted(
                field_words,
                key=lambda word:
                    word.x0,
            )

            text = self._join_words(
                ordered_words
            )

            if ordered_words:
                cell = BuiltCell(
                    field_name=field_name,

                    text=text,

                    words=ordered_words,

                    x0=min(
                        word.x0
                        for word in ordered_words
                    ),

                    x1=max(
                        word.x1
                        for word in ordered_words
                    ),

                    y0=min(
                        word.y0
                        for word in ordered_words
                    ),

                    y1=max(
                        word.y1
                        for word in ordered_words
                    ),
                )

            else:
                cell = BuiltCell(
                    field_name=field_name,

                    text="",

                    words=[],
                )

            cells[
                field_name
            ] = cell

        non_empty_count = sum(
            1
            for cell in cells.values()
            if cell.text
        )

        name_value = (
            cells.get(
                "name"
            )
        )

        has_name = bool(
            name_value
            and name_value.text
        )

        has_numeric_content = any(
            self._contains_number(
                cell.text
            )
            for field_name, cell
            in cells.items()
            if field_name != "name"
        )

        if (
            non_empty_count
            < self.MINIMUM_ROW_CELLS
        ):
            return None

        if (
            not has_name
            and not has_numeric_content
        ):
            return None

        confidence = min(
            0.98,
            0.46
            + (
                non_empty_count
                / max(
                    1,
                    len(columns),
                )
            ) * 0.48,
        )

        return BuiltRow(
            cells=cells,

            source_words=line.words,

            source_text=line.text,

            y_center=line.y_center,

            page_number=page_number,

            confidence=confidence,
        )

    def _find_target_column(
        self,
        word: DocumentWord,
        columns: list[BuiltColumn],
    ) -> Optional[BuiltColumn]:
        if not columns:
            return None

        center_x = (
            word.center_x
        )

        containing = [
            column
            for column in columns
            if (
                column.left_boundary
                <= center_x
                <= column.right_boundary
            )
        ]

        if containing:
            return min(
                containing,
                key=lambda column:
                    abs(
                        center_x
                        - column.x_center
                    ),
            )

        return min(
            columns,
            key=lambda column:
                abs(
                    center_x
                    - column.x_center
                ),
        )

    # =================================================================
    # FINAL DE TABELA
    # =================================================================

    def _looks_like_new_section(
        self,
        line: SpatialLine,
        profile: type,
    ) -> bool:
        normalized = self._normalize(
            line.text
        )

        if not normalized:
            return False

        group_names = getattr(
            profile,
            "GROUP_NAMES",
            tuple(),
        )

        normalized_groups = {
            self._normalize(
                group
            )
            for group in group_names
        }

        if normalized in normalized_groups:
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
                return True

        # Uma linha longa sem número costuma ser novo título,
        # rodapé ou bloco descritivo.
        if (
            len(normalized) > 35
            and not self._contains_number(
                normalized
            )
        ):
            return True

        return False

    # =================================================================
    # CONFIANÇA
    # =================================================================

    def _calculate_table_confidence(
        self,
        table: BuiltTable,
    ) -> float:
        if not table.columns:
            return 0.0

        header_score = min(
            1.0,
            len(table.columns) / 6.0,
        )

        if not table.rows:
            return header_score * 0.35

        row_scores = [
            row.confidence
            for row in table.rows
        ]

        average_row_score = (
            sum(
                row_scores
            )
            / len(
                row_scores
            )
        )

        volume_score = min(
            1.0,
            len(table.rows) / 8.0,
        )

        return min(
            0.99,
            (
                header_score * 0.38
                + average_row_score * 0.47
                + volume_score * 0.15
            ),
        )

    # =================================================================
    # DEDUPLICAÇÃO
    # =================================================================

    def _deduplicate_tables(
        self,
        tables: list[BuiltTable],
    ) -> list[BuiltTable]:
        result = []

        seen = set()

        for table in tables:
            column_signature = tuple(
                column.field_name
                for column in table.columns
            )

            signature = (
                table.page_number,

                round(
                    table.header_y,
                    1,
                ),

                column_signature,
            )

            if signature in seen:
                continue

            seen.add(
                signature
            )

            result.append(
                table
            )

        return result

    # =================================================================
    # HELPERS
    # =================================================================

    def _valid_words(
        self,
        words: Iterable[DocumentWord],
    ) -> list[DocumentWord]:
        result = []

        for word in words or []:
            text = str(
                word.text
                or ""
            ).strip()

            if not text:
                continue

            if (
                word.x1
                <= word.x0
                or word.y1
                <= word.y0
            ):
                continue

            result.append(
                word
            )

        return result

    def _join_words(
        self,
        words: list[DocumentWord],
    ) -> str:
        return " ".join(
            str(
                word.text
                or ""
            ).strip()
            for word in words
            if str(
                word.text
                or ""
            ).strip()
        )

    def _contains_number(
        self,
        value: str,
    ) -> bool:
        return any(
            character.isdigit()
            for character in (
                value
                or ""
            )
        )

    def _average_line_height(
        self,
        lines: list[SpatialLine],
    ) -> float:
        heights = [
            line.height
            for line in lines
            if line.height > 0
        ]

        if not heights:
            return 10.0

        return (
            sum(
                heights
            )
            / len(
                heights
            )
        )

    def _horizontal_overlap_ratio(
        self,
        first_x0: float,
        first_x1: float,
        second_x0: float,
        second_x1: float,
    ) -> float:
        overlap_start = max(
            first_x0,
            second_x0,
        )

        overlap_end = min(
            first_x1,
            second_x1,
        )

        overlap = max(
            0.0,
            overlap_end
            - overlap_start,
        )

        first_width = max(
            1.0,
            first_x1
            - first_x0,
        )

        second_width = max(
            1.0,
            second_x1
            - second_x0,
        )

        return overlap / min(
            first_width,
            second_width,
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

        normalized = (
            normalized
            .upper()
            .replace(
                "\u00A0",
                " ",
            )
        )

        return " ".join(
            normalized.split()
        )   