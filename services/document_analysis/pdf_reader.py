from pathlib import Path

import fitz

from services.document_analysis.models import (
    DocumentBlock,
    DocumentContent,
    DocumentPage,
    DocumentWord,
)


class PDFReader:
    """
    Leitor físico de documentos PDF.

    Responsabilidades:
    - validar arquivo;
    - abrir PDF;
    - extrair texto;
    - extrair palavras com coordenadas;
    - extrair blocos com coordenadas;
    - retornar uma representação padronizada.

    Este componente NÃO interpreta semanticamente o conteúdo.
    """

    def read(
        self,
        source_path: str | Path,
    ) -> DocumentContent:
        path = Path(
            source_path
        )

        self._validate_path(
            path
        )

        document = fitz.open(
            path
        )

        try:
            if document.page_count <= 0:
                raise ValueError(
                    "O PDF não possui páginas."
                )

            pages = []

            for page_index in range(
                document.page_count
            ):
                page = document.load_page(
                    page_index
                )

                parsed_page = (
                    self._read_page(
                        page=page,
                        page_number=(
                            page_index + 1
                        ),
                    )
                )

                pages.append(
                    parsed_page
                )

            metadata = (
                document.metadata
                or {}
            )

            return DocumentContent(
                source_path=str(
                    path.resolve()
                ),

                file_name=path.name,

                page_count=(
                    document.page_count
                ),

                pages=pages,

                metadata=dict(
                    metadata
                ),
            )

        finally:
            document.close()

    # =============================================================
    # PÁGINA
    # =============================================================

    def _read_page(
        self,
        page,
        page_number: int,
    ) -> DocumentPage:
        rectangle = page.rect

        text = page.get_text(
            "text"
        )

        words = self._extract_words(
            page=page,
            page_number=page_number,
        )

        blocks = self._extract_blocks(
            page=page,
            page_number=page_number,
        )

        return DocumentPage(
            number=page_number,

            width=float(
                rectangle.width
            ),

            height=float(
                rectangle.height
            ),

            text=text,

            words=words,

            blocks=blocks,
        )

    # =============================================================
    # PALAVRAS
    # =============================================================

    def _extract_words(
        self,
        page,
        page_number: int,
    ) -> list[DocumentWord]:
        raw_words = page.get_text(
            "words"
        )

        result = []

        for raw_word in raw_words:
            if len(raw_word) < 5:
                continue

            text = str(
                raw_word[4]
            ).strip()

            if not text:
                continue

            block_number = (
                self._safe_int(
                    raw_word,
                    5,
                )
            )

            line_number = (
                self._safe_int(
                    raw_word,
                    6,
                )
            )

            word_number = (
                self._safe_int(
                    raw_word,
                    7,
                )
            )

            result.append(
                DocumentWord(
                    text=text,

                    x0=float(
                        raw_word[0]
                    ),

                    y0=float(
                        raw_word[1]
                    ),

                    x1=float(
                        raw_word[2]
                    ),

                    y1=float(
                        raw_word[3]
                    ),

                    page_number=(
                        page_number
                    ),

                    block_number=(
                        block_number
                    ),

                    line_number=(
                        line_number
                    ),

                    word_number=(
                        word_number
                    ),
                )
            )

        return result

    # =============================================================
    # BLOCOS
    # =============================================================

    def _extract_blocks(
        self,
        page,
        page_number: int,
    ) -> list[DocumentBlock]:
        raw_blocks = page.get_text(
            "blocks"
        )

        result = []

        for index, raw_block in enumerate(
            raw_blocks
        ):
            if len(raw_block) < 5:
                continue

            text = str(
                raw_block[4]
            ).strip()

            if not text:
                continue

            block_number = (
                self._safe_int(
                    raw_block,
                    5,
                )
            )

            if block_number is None:
                block_number = index

            result.append(
                DocumentBlock(
                    text=text,

                    x0=float(
                        raw_block[0]
                    ),

                    y0=float(
                        raw_block[1]
                    ),

                    x1=float(
                        raw_block[2]
                    ),

                    y1=float(
                        raw_block[3]
                    ),

                    page_number=(
                        page_number
                    ),

                    block_number=(
                        block_number
                    ),
                )
            )

        return result

    # =============================================================
    # VALIDAÇÃO
    # =============================================================

    def _validate_path(
        self,
        path: Path,
    ) -> None:
        if not path.exists():
            raise FileNotFoundError(
                "O arquivo selecionado não foi encontrado."
            )

        if not path.is_file():
            raise ValueError(
                "O caminho informado não corresponde a um arquivo."
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "O arquivo selecionado não é um PDF."
            )

    # =============================================================
    # HELPERS
    # =============================================================

    def _safe_int(
        self,
        values,
        index: int,
    ) -> int | None:
        if index >= len(
            values
        ):
            return None

        try:
            return int(
                values[index]
            )

        except (
            TypeError,
            ValueError,
        ):
            return None