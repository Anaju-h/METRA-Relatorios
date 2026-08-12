from __future__ import annotations

from pathlib import Path

import fitz


class InstitutionalHeader:
    """
    Cabeçalho institucional padrão do METRA.

    Todas as páginas passam por este componente,
    garantindo identidade visual consistente.
    """

    HEIGHT = 58

    COLOR_NAVY = (
        0.03,
        0.11,
        0.22,
    )

    COLOR_BLUE = (
        0.00,
        0.41,
        0.73,
    )

    COLOR_BORDER = (
        0.84,
        0.87,
        0.91,
    )

    COLOR_TEXT = (
        0.26,
        0.31,
        0.37,
    )

    def __init__(
        self,
        *,
        base_dir: Path,
    ):
        self.base_dir = base_dir

    # ==========================================================
    # DESENHO
    # ==========================================================

    def draw(
        self,
        *,
        page: fitz.Page,
        x0: float,
        x1: float,
        y: float,
        report_title: str,
    ) -> float:
        """
        Desenha o cabeçalho e devolve a posição inicial
        do conteúdo da página.
        """

        self._draw_background(
            page,
            x0,
            x1,
            y,
        )

        self._draw_logos(
            page,
            x0,
            x1,
            y,
        )

        self._draw_title(
            page,
            x0,
            x1,
            y,
            report_title,
        )

        self._draw_separator(
            page,
            x0,
            x1,
            y,
        )

        return (
            y
            + self.HEIGHT
            + 10
        )

    # ==========================================================
    # FUNDO
    # ==========================================================

    def _draw_background(
        self,
        page,
        x0,
        x1,
        y,
    ):
        page.draw_rect(
            fitz.Rect(
                x0,
                y,
                x1,
                y + self.HEIGHT,
            ),
            fill=(
                1,
                1,
                1,
            ),
            color=self.COLOR_BORDER,
            width=0.6,
        )

    # ==========================================================
    # LOGOS
    # ==========================================================

    def _draw_logos(
        self,
        page,
        x0,
        x1,
        y,
    ):
        cem = self._find_logo(
            [
                "cem.png",
                "logo_cem.png",
            ]
        )

        senai = self._find_logo(
            [
                "senai.png",
                "logo_senai.png",
            ]
        )

        if cem:
            self._insert_logo(
                page,
                cem,
                fitz.Rect(
                    x0 + 10,
                    y + 9,
                    x0 + 118,
                    y + 46,
                ),
            )

        if senai:
            self._insert_logo(
                page,
                senai,
                fitz.Rect(
                    x1 - 100,
                    y + 11,
                    x1 - 10,
                    y + 43,
                ),
            )

    # ==========================================================
    # TÍTULO
    # ==========================================================

    def _draw_title(
        self,
        page,
        x0,
        x1,
        y,
        report_title,
    ):
        page.insert_textbox(
            fitz.Rect(
                x0 + 128,
                y + 10,
                x1 - 110,
                y + 27,
            ),
            "METRA",
            fontsize=10.5,
            fontname="hebo",
            color=self.COLOR_NAVY,
            align=fitz.TEXT_ALIGN_CENTER,
        )

        page.insert_textbox(
            fitz.Rect(
                x0 + 128,
                y + 27,
                x1 - 110,
                y + 45,
            ),
            report_title,
            fontsize=7.4,
            fontname="helv",
            color=self.COLOR_TEXT,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    # ==========================================================
    # LINHA INFERIOR
    # ==========================================================

    def _draw_separator(
        self,
        page,
        x0,
        x1,
        y,
    ):
        page.draw_line(
            fitz.Point(
                x0,
                y + self.HEIGHT,
            ),
            fitz.Point(
                x1,
                y + self.HEIGHT,
            ),
            color=self.COLOR_BLUE,
            width=1.4,
        )

    # ==========================================================
    # LOGOS
    # ==========================================================

    def _find_logo(
        self,
        candidates: list[str],
    ) -> Path | None:

        folders = [
            self.base_dir / "assets" / "logos",
            self.base_dir / "assets",
            self.base_dir / "resources",
            self.base_dir / "resources" / "logos",
        ]

        for folder in folders:

            if not folder.exists():
                continue

            for name in candidates:

                file = folder / name

                if file.exists():
                    return file

        return None

    def _insert_logo(
        self,
        page,
        path,
        rect,
    ):
        try:

            page.insert_image(
                rect,
                filename=str(path),
                keep_proportion=True,
            )

        except Exception:
            pass