from __future__ import annotations

from PySide6.QtCore import (
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)


class StepIndicator(QWidget):
    """
    Indicador visual das etapas de um fluxo.

    Estados:
    - etapas anteriores: concluídas;
    - etapa atual: ativa;
    - etapas seguintes: futuras.

    Exemplo:
        StepIndicator(
            [
                "Início",
                "Documentos",
                "Revisão",
                "Criar",
            ],
            current_step=2,
        )
    """

    # =============================================================
    # CORES
    # =============================================================

    COLOR_BACKGROUND = QColor(
        "#FFFFFF"
    )

    COLOR_BORDER = QColor(
        "#D9E2EC"
    )

    COLOR_BLUE = QColor(
        "#0874D1"
    )

    COLOR_BLUE_DARK = QColor(
        "#005A9C"
    )

    COLOR_NAVY = QColor(
        "#08294A"
    )

    COLOR_TEXT = QColor(
        "#102A43"
    )

    COLOR_MUTED = QColor(
        "#7B8794"
    )

    COLOR_FUTURE_BORDER = QColor(
        "#AAB7C4"
    )

    COLOR_CONNECTOR = QColor(
        "#D4DCE5"
    )

    # =============================================================
    # CONSTRUÇÃO
    # =============================================================

    def __init__(
        self,
        steps: list[str],
        current_step: int = 0,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        if not steps:
            raise ValueError(
                (
                    "O indicador precisa de "
                    "ao menos uma etapa."
                )
            )

        self.steps = list(
            steps
        )

        self.current_step = (
            self._clamp_step(
                current_step
            )
        )

        self.setObjectName(
            "stepIndicator"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setMinimumHeight(
            112
        )

        self.setMaximumHeight(
            118
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True,
        )

    # =============================================================
    # ESTADO
    # =============================================================

    def set_current_step(
        self,
        step: int,
    ) -> None:
        new_step = self._clamp_step(
            step
        )

        if (
            new_step
            == self.current_step
        ):
            return

        self.current_step = (
            new_step
        )

        self.update()

    def set_steps(
        self,
        steps: list[str],
        current_step: int = 0,
    ) -> None:
        if not steps:
            raise ValueError(
                "O indicador precisa de ao menos uma etapa."
            )

        self.steps = list(
            steps
        )

        self.current_step = self._clamp_step(
            current_step
        )

        self.updateGeometry()
        self.update()

    def _clamp_step(
        self,
        step: int,
    ) -> int:
        return max(
            0,
            min(
                int(
                    step
                ),
                len(
                    self.steps
                )
                - 1,
            ),
        )

    # =============================================================
    # DESENHO
    # =============================================================

    def paintEvent(
        self,
        event,
    ) -> None:
        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        self._draw_card(
            painter
        )

        if not self.steps:
            return

        self._draw_progress(
            painter
        )

    # =============================================================
    # CARD
    # =============================================================

    def _draw_card(
        self,
        painter: QPainter,
    ) -> None:
        card_rect = QRectF(
            1.0,
            1.0,
            self.width() - 2.0,
            self.height() - 2.0,
        )

        painter.setPen(
            QPen(
                self.COLOR_BORDER,
                1.0,
            )
        )

        painter.setBrush(
            self.COLOR_BACKGROUND
        )

        painter.drawRoundedRect(
            card_rect,
            11.0,
            11.0,
        )

    # =============================================================
    # PROGRESSO
    # =============================================================

    def _draw_progress(
        self,
        painter: QPainter,
    ) -> None:
        count = len(
            self.steps
        )

        horizontal_padding = 70.0

        available_width = max(
            1.0,
            self.width()
            - (
                horizontal_padding
                * 2
            ),
        )

        if count == 1:
            positions = [
                self.width()
                / 2.0
            ]

        else:
            interval = (
                available_width
                / (
                    count - 1
                )
            )

            positions = [
                horizontal_padding
                + (
                    interval
                    * index
                )
                for index in range(
                    count
                )
            ]

        marker_y = 42.0

        marker_radius = 18.0

        # ---------------------------------------------------------
        # CONECTORES
        # ---------------------------------------------------------

        for index in range(
            count - 1
        ):
            x1 = (
                positions[index]
                + marker_radius
                + 10
            )

            x2 = (
                positions[
                    index + 1
                ]
                - marker_radius
                - 10
            )

            connector_color = (
                self.COLOR_BLUE
                if index
                < self.current_step
                else self.COLOR_CONNECTOR
            )

            painter.setPen(
                QPen(
                    connector_color,
                    3.0,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )

            painter.drawLine(
                int(
                    x1
                ),
                int(
                    marker_y
                ),
                int(
                    x2
                ),
                int(
                    marker_y
                ),
            )

        # ---------------------------------------------------------
        # ETAPAS
        # ---------------------------------------------------------

        for index, (
            title,
            marker_x,
        ) in enumerate(
            zip(
                self.steps,
                positions,
            )
        ):
            self._draw_step(
                painter=painter,
                index=index,
                title=title,
                marker_x=marker_x,
                marker_y=marker_y,
                radius=marker_radius,
            )

    # =============================================================
    # ETAPA INDIVIDUAL
    # =============================================================

    def _draw_step(
        self,
        *,
        painter: QPainter,
        index: int,
        title: str,
        marker_x: float,
        marker_y: float,
        radius: float,
    ) -> None:
        completed = (
            index
            < self.current_step
        )

        current = (
            index
            == self.current_step
        )

        future = (
            index
            > self.current_step
        )

        marker_rect = QRectF(
            marker_x - radius,
            marker_y - radius,
            radius * 2,
            radius * 2,
        )

        # ---------------------------------------------------------
        # MARCADOR
        # ---------------------------------------------------------

        if completed:
            painter.setPen(
                QPen(
                    self.COLOR_BLUE,
                    1.5,
                )
            )

            painter.setBrush(
                self.COLOR_BLUE
            )

        elif current:
            painter.setPen(
                QPen(
                    self.COLOR_BLUE,
                    2.0,
                )
            )

            painter.setBrush(
                self.COLOR_BLUE
            )

        else:
            painter.setPen(
                QPen(
                    self.COLOR_FUTURE_BORDER,
                    1.8,
                )
            )

            painter.setBrush(
                self.COLOR_BACKGROUND
            )

        painter.drawEllipse(
            marker_rect
        )

        # ---------------------------------------------------------
        # CONTEÚDO DO MARCADOR
        # ---------------------------------------------------------

        marker_font = QFont()
        marker_font.setPixelSize(
            15
        )
        marker_font.setBold(
            True
        )

        painter.setFont(
            marker_font
        )

        if completed:
            marker_text = "✓"
            marker_color = QColor(
                "#FFFFFF"
            )

        elif current:
            marker_text = str(
                index + 1
            )
            marker_color = QColor(
                "#FFFFFF"
            )

        else:
            marker_text = str(
                index + 1
            )
            marker_color = (
                self.COLOR_NAVY
            )

        painter.setPen(
            marker_color
        )

        painter.drawText(
            marker_rect,
            Qt.AlignmentFlag.AlignCenter,
            marker_text,
        )

        # ---------------------------------------------------------
        # NOME DA ETAPA
        # ---------------------------------------------------------

        label_rect = QRectF(
            marker_x - 72,
            68,
            144,
            30,
        )

        label_font = QFont()
        label_font.setPixelSize(
            13
        )

        if (
            current
            or completed
        ):
            label_font.setBold(
                True
            )

        painter.setFont(
            label_font
        )

        if current:
            label_color = (
                self.COLOR_BLUE_DARK
            )

        elif completed:
            label_color = (
                self.COLOR_NAVY
            )

        elif future:
            label_color = (
                self.COLOR_TEXT
            )

        else:
            label_color = (
                self.COLOR_TEXT
            )

        painter.setPen(
            label_color
        )

        painter.drawText(
            label_rect,
            (
                Qt.AlignmentFlag.AlignHCenter
                | Qt.AlignmentFlag.AlignTop
            ),
            title,
        )