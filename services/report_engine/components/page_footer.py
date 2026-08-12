from __future__ import annotations

import fitz


class PageFooter:
    """
    Rodapé padrão das páginas METRA.

    Sempre exibe:
    - identificador do relatório;
    - número e total de páginas METRA.

    A versão é opcional para apresentação ao cliente, mas continua
    armazenada internamente para rastreabilidade.
    """

    COLOR_BORDER = (
        0.76,
        0.80,
        0.85,
    )

    COLOR_TEXT = (
        0.35,
        0.40,
        0.45,
    )

    LINE_OFFSET = 28.0
    TEXT_TOP_OFFSET = 5.0
    TEXT_HEIGHT = 14.0

    # =============================================================
    # APLICAÇÃO
    # =============================================================

    def apply(
        self,
        *,
        document: fitz.Document,
        report_id: str,
        version: str,
        show_version: bool,
        page_width: float,
        page_height: float,
        margin_left: float,
        margin_right: float,
    ) -> None:
        """
        Aplica o rodapé depois que todas as páginas METRA
        do template já foram criadas.
        """

        total_pages = (
            document.page_count
        )

        for page_index in range(
            total_pages
        ):
            page = document[
                page_index
            ]

            self._draw_footer(
                page=page,
                page_index=page_index,
                total_pages=total_pages,
                report_id=report_id,
                version=version,
                show_version=show_version,
                page_width=page_width,
                page_height=page_height,
                margin_left=margin_left,
                margin_right=margin_right,
            )

    # =============================================================
    # DESENHO
    # =============================================================

    def _draw_footer(
        self,
        *,
        page: fitz.Page,
        page_index: int,
        total_pages: int,
        report_id: str,
        version: str,
        show_version: bool,
        page_width: float,
        page_height: float,
        margin_left: float,
        margin_right: float,
    ) -> None:
        line_y = (
            page_height
            - self.LINE_OFFSET
        )

        self._draw_separator(
            page=page,
            line_y=line_y,
            page_width=page_width,
            margin_left=margin_left,
            margin_right=margin_right,
        )

        self._draw_report_identification(
            page=page,
            line_y=line_y,
            page_width=page_width,
            margin_left=margin_left,
            report_id=report_id,
            version=version,
            show_version=show_version,
        )

        self._draw_page_number(
            page=page,
            line_y=line_y,
            page_width=page_width,
            margin_right=margin_right,
            page_index=page_index,
            total_pages=total_pages,
        )

    # =============================================================
    # LINHA
    # =============================================================

    def _draw_separator(
        self,
        *,
        page: fitz.Page,
        line_y: float,
        page_width: float,
        margin_left: float,
        margin_right: float,
    ) -> None:
        page.draw_line(
            fitz.Point(
                margin_left,
                line_y,
            ),
            fitz.Point(
                page_width
                - margin_right,
                line_y,
            ),
            color=self.COLOR_BORDER,
            width=0.45,
        )

    # =============================================================
    # IDENTIFICAÇÃO
    # =============================================================

    def _draw_report_identification(
        self,
        *,
        page: fitz.Page,
        line_y: float,
        page_width: float,
        margin_left: float,
        report_id: str,
        version: str,
        show_version: bool,
    ) -> None:
        identification = (
            f"{report_id} · {version}"
            if show_version
            else report_id
        )

        page.insert_textbox(
            fitz.Rect(
                margin_left,
                line_y
                + self.TEXT_TOP_OFFSET,
                page_width / 2,
                line_y
                + self.TEXT_TOP_OFFSET
                + self.TEXT_HEIGHT,
            ),
            identification,
            fontsize=6.2,
            fontname="helv",
            color=self.COLOR_TEXT,
        )

    # =============================================================
    # PAGINAÇÃO
    # =============================================================

    def _draw_page_number(
        self,
        *,
        page: fitz.Page,
        line_y: float,
        page_width: float,
        margin_right: float,
        page_index: int,
        total_pages: int,
    ) -> None:
        page.insert_textbox(
            fitz.Rect(
                page_width / 2,
                line_y
                + self.TEXT_TOP_OFFSET,
                page_width
                - margin_right,
                line_y
                + self.TEXT_TOP_OFFSET
                + self.TEXT_HEIGHT,
            ),
            (
                f"Página {page_index + 1} "
                f"de {total_pages}"
            ),
            fontsize=6.2,
            fontname="helv",
            color=self.COLOR_TEXT,
            align=fitz.TEXT_ALIGN_RIGHT,
        )