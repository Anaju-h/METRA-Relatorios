from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import fitz


@dataclass(slots=True)
class PageGeometry:
    """
    Define as dimensões e margens utilizadas pelo relatório.

    Os valores padrão correspondem ao formato A4 em pontos.
    """

    width: float = 595.0
    height: float = 842.0

    margin_left: float = 34.0
    margin_right: float = 34.0
    margin_top: float = 30.0
    margin_bottom: float = 36.0

    footer_reserved: float = 24.0

    @property
    def content_width(
        self,
    ) -> float:
        """
        Retorna a largura útil disponível para o conteúdo.
        """

        return (
            self.width
            - self.margin_left
            - self.margin_right
        )

    @property
    def content_bottom(
        self,
    ) -> float:
        """
        Retorna a posição vertical máxima antes do rodapé.
        """

        return (
            self.height
            - self.margin_bottom
            - self.footer_reserved
        )


PageInitializer = Callable[
    [
        fitz.Page,
        str | None,
    ],
    float,
]


class ReportLayoutEngine:
    """
    Motor responsável pelo controle de páginas e posicionamento.

    Ele centraliza:

    - criação de páginas;
    - posição vertical atual;
    - espaço útil;
    - quebra automática;
    - reserva de altura;
    - criação de retângulos;
    - repetição de títulos em novas páginas.
    """

    def __init__(
        self,
        document: fitz.Document,
        *,
        geometry: PageGeometry | None = None,
        page_initializer: PageInitializer | None = None,
    ):
        self.document = document

        self.geometry = (
            geometry
            or PageGeometry()
        )

        self.page_initializer = (
            page_initializer
        )

        self.current_page: fitz.Page | None = None

        self.cursor_y = (
            self.geometry.margin_top
        )

        self.current_section_title: str | None = None

    # =============================================================
    # PÁGINAS
    # =============================================================

    def new_page(
        self,
        section_title: str | None = None,
    ) -> fitz.Page:
        """
        Cria uma nova página e reinicia o cursor vertical.

        Quando um inicializador é informado, ele desenha o
        cabeçalho institucional e devolve a posição inicial
        do conteúdo técnico.
        """

        page = self.document.new_page(
            width=self.geometry.width,
            height=self.geometry.height,
        )

        self.current_page = page

        self.current_section_title = (
            section_title
        )

        self.cursor_y = (
            self.geometry.margin_top
        )

        if self.page_initializer is not None:
            initialized_y = (
                self.page_initializer(
                    page,
                    section_title,
                )
            )

            self.cursor_y = max(
                self.geometry.margin_top,
                float(
                    initialized_y
                ),
            )

        return page

    def ensure_page(
        self,
    ) -> fitz.Page:
        """
        Garante que exista uma página ativa.
        """

        if self.current_page is None:
            return self.new_page()

        return self.current_page

    # =============================================================
    # ESPAÇO
    # =============================================================

    def has_space(
        self,
        required_height: float,
    ) -> bool:
        """
        Verifica se o bloco cabe na página atual.
        """

        if self.current_page is None:
            return False

        return (
            self.cursor_y
            + required_height
            <= self.geometry.content_bottom
        )

    def ensure_space(
        self,
        required_height: float,
        *,
        repeated_title: str | None = None,
    ) -> fitz.Page:
        """
        Garante que exista espaço suficiente para o próximo bloco.

        Quando não houver espaço, cria uma nova página e repete
        o título informado ou o título atual da seção.
        """

        if required_height < 0:
            raise ValueError(
                "A altura necessária não pode ser negativa."
            )

        if self.current_page is None:
            return self.new_page(
                repeated_title
            )

        if not self.has_space(
            required_height
        ):
            return self.new_page(
                repeated_title
                or self.current_section_title
            )

        return self.current_page

    def remaining_height(
        self,
    ) -> float:
        """
        Retorna a altura restante na página atual.
        """

        if self.current_page is None:
            return 0.0

        return max(
            0.0,
            (
                self.geometry.content_bottom
                - self.cursor_y
            ),
        )

    # =============================================================
    # CURSOR
    # =============================================================

    def advance(
        self,
        height: float,
    ) -> None:
        """
        Avança o cursor vertical.
        """

        if height < 0:
            raise ValueError(
                "O avanço do cursor não pode ser negativo."
            )

        self.cursor_y += height

    def reserve(
        self,
        height: float,
    ) -> float:
        """
        Reserva uma altura e retorna a posição inicial do bloco.
        """

        if height < 0:
            raise ValueError(
                "A altura reservada não pode ser negativa."
            )

        start_y = self.cursor_y

        self.cursor_y += height

        return start_y

    def move_to(
        self,
        y: float,
    ) -> None:
        """
        Move o cursor para uma posição vertical específica.
        """

        minimum_y = (
            self.geometry.margin_top
        )

        maximum_y = (
            self.geometry.content_bottom
        )

        self.cursor_y = max(
            minimum_y,
            min(
                maximum_y,
                float(
                    y
                ),
            ),
        )

    # =============================================================
    # RETÂNGULOS
    # =============================================================

    def content_rect(
        self,
        height: float,
        *,
        x_offset: float = 0.0,
        width: float | None = None,
        y: float | None = None,
    ) -> fitz.Rect:
        """
        Cria um retângulo dentro da área útil do relatório.
        """

        if height < 0:
            raise ValueError(
                "A altura do retângulo não pode ser negativa."
            )

        x0 = (
            self.geometry.margin_left
            + x_offset
        )

        resolved_width = (
            width
            if width is not None
            else (
                self.geometry.content_width
                - x_offset
            )
        )

        y0 = (
            self.cursor_y
            if y is None
            else float(
                y
            )
        )

        return fitz.Rect(
            x0,
            y0,
            x0 + resolved_width,
            y0 + height,
        )

    def full_width_rect(
        self,
        height: float,
        *,
        y: float | None = None,
    ) -> fitz.Rect:
        """
        Cria um retângulo ocupando toda a largura útil.
        """

        return self.content_rect(
            height,
            y=y,
        )

    def column_rect(
        self,
        *,
        column_index: int,
        column_count: int,
        height: float,
        gap: float = 10.0,
        y: float | None = None,
    ) -> fitz.Rect:
        """
        Cria um retângulo para layouts em colunas.

        Exemplo:
            column_index=0
            column_count=2

        retorna a primeira coluna de um layout com duas colunas.
        """

        if column_count <= 0:
            raise ValueError(
                "A quantidade de colunas deve ser maior que zero."
            )

        if (
            column_index < 0
            or column_index >= column_count
        ):
            raise ValueError(
                "O índice da coluna é inválido."
            )

        total_gap = (
            gap
            * (
                column_count - 1
            )
        )

        column_width = (
            self.geometry.content_width
            - total_gap
        ) / column_count

        x_offset = (
            column_index
            * (
                column_width
                + gap
            )
        )

        return self.content_rect(
            height,
            x_offset=x_offset,
            width=column_width,
            y=y,
        )

    # =============================================================
    # SEÇÕES
    # =============================================================

    def start_section(
        self,
        title: str,
        *,
        required_height: float = 0.0,
    ) -> fitz.Page:
        """
        Inicia uma nova seção técnica.

        O título passa a ser utilizado nas quebras de página
        seguintes enquanto a seção estiver ativa.
        """

        self.current_section_title = (
            title
        )

        return self.ensure_space(
            required_height,
            repeated_title=title,
        )

    def clear_section(
        self,
    ) -> None:
        """
        Remove o título de seção ativo.
        """

        self.current_section_title = None