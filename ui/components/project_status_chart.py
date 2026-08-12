from __future__ import annotations

from collections import Counter

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


class ProjectStatusChart(QWidget):
    """
    Gráfico de rosca leve, desenhado com QPainter.

    O gráfico considera apenas os estados operacionais principais
    do METRA:

    - Em edição
    - Concluídos
    """

    EDITING_COLOR = "#F07C00"
    COMPLETED_COLOR = "#006CB7"

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.values = {
            "Em edição": 0,
            "Concluídos": 0,
        }

        self.setMinimumSize(
            250,
            180,
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_projects(
        self,
        projects,
    ) -> None:
        counter = Counter()

        for project in projects:
            status = str(
                getattr(
                    project,
                    "status",
                    "",
                )
                or ""
            ).strip().lower()

            if status in {
                "concluído",
                "concluido",
            }:
                counter[
                    "Concluídos"
                ] += 1

            elif status in {
                "em edição",
                "em edicao",
            }:
                counter[
                    "Em edição"
                ] += 1

        self.values = {
            "Em edição":
                counter[
                    "Em edição"
                ],

            "Concluídos":
                counter[
                    "Concluídos"
                ],
        }

        self.update()

    def paintEvent(
        self,
        event,
    ) -> None:
        super().paintEvent(
            event
        )

        painter = QPainter(
            self
        )
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        total = sum(
            self.values.values()
        )

        side = (
            min(
                self.width(),
                self.height(),
            )
            - 38
        )

        side = max(
            80,
            side,
        )

        chart_rect = QRectF(
            18,
            (
                self.height()
                - side
            )
            / 2,
            side,
            side,
        )

        pen_width = max(
            14,
            int(
                side
                * 0.12
            ),
        )

        base_pen = QPen(
            QColor(
                "#E7EDF3"
            ),
            pen_width,
        )

        base_pen.setCapStyle(
            Qt.PenCapStyle.FlatCap
        )

        painter.setPen(
            base_pen
        )

        painter.drawArc(
            chart_rect,
            0,
            360 * 16,
        )

        colors = [
            QColor(
                self.EDITING_COLOR
            ),
            QColor(
                self.COMPLETED_COLOR
            ),
        ]

        start_angle = (
            90
            * 16
        )

        if total > 0:
            for index, value in enumerate(
                self.values.values()
            ):
                if value <= 0:
                    continue

                span = -int(
                    (
                        value
                        / total
                    )
                    * 360
                    * 16
                )

                pen = QPen(
                    colors[index],
                    pen_width,
                )

                pen.setCapStyle(
                    Qt.PenCapStyle.FlatCap
                )

                painter.setPen(
                    pen
                )

                painter.drawArc(
                    chart_rect,
                    start_angle,
                    span,
                )

                start_angle += (
                    span
                )

        painter.setPen(
            QColor(
                "#08233E"
            )
        )

        font = QFont(
            "Segoe UI"
        )
        font.setBold(
            True
        )
        font.setPointSize(
            max(
                14,
                int(
                    side
                    * 0.10
                ),
            )
        )

        painter.setFont(
            font
        )

        painter.drawText(
            chart_rect,
            Qt.AlignmentFlag.AlignCenter,
            str(
                total
            ),
        )

        painter.setPen(
            QColor(
                "#667A8E"
            )
        )

        label_font = QFont(
            "Segoe UI"
        )
        label_font.setPointSize(
            9
        )

        painter.setFont(
            label_font
        )

        label_rect = QRectF(
            chart_rect.left(),
            (
                chart_rect.center().y()
                + 18
            ),
            chart_rect.width(),
            24,
        )

        painter.drawText(
            label_rect,
            (
                Qt.AlignmentFlag.AlignHCenter
                | Qt.AlignmentFlag.AlignTop
            ),
            "projetos",
        )