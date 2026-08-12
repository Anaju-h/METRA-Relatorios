from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class AppHeader(QFrame):
    """
    Cabeçalho institucional global do METRA.

    Exibe:
    - logo do Centro de Excelência em Metrologia;
    - identidade central do METRA;
    - logo do SENAI.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("appHeader")
        self.setFixedHeight(96)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self._build_ui()
        self._apply_component_style()

    # =============================================================
    # INTERFACE
    # =============================================================

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(26, 8, 26, 0)
        root_layout.setSpacing(0)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 7)
        content_layout.setSpacing(18)

        # ---------------------------------------------------------
        # ÁREA ESQUERDA — CEM
        # ---------------------------------------------------------

        left_area = QWidget()
        left_area.setObjectName("appHeaderSideArea")
        left_area.setFixedWidth(310)

        left_layout = QHBoxLayout(left_area)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.cem_logo = self._create_logo(
            "cem.png",
            maximum_width=292,
            maximum_height=67,
            fallback="CENTRO DE EXCELÊNCIA EM METROLOGIA",
        )

        left_layout.addWidget(self.cem_logo)

        # ---------------------------------------------------------
        # ÁREA CENTRAL — METRA
        # ---------------------------------------------------------

        center = QWidget()
        center.setObjectName("appHeaderCenter")
        center.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(10, 1, 10, 0)
        center_layout.setSpacing(1)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("METRA")
        self.title_label.setObjectName("appHeaderTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_accent = QFrame()
        self.title_accent.setObjectName("appHeaderTitleAccent")
        self.title_accent.setFixedSize(58, 3)

        self.subtitle_label = QLabel(
            "Sistema Inteligente de Pós-processamento de Relatórios"
        )
        self.subtitle_label.setObjectName("appHeaderSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMaximumWidth(520)

        center_layout.addStretch(1)
        center_layout.addWidget(self.title_label)
        center_layout.addWidget(
            self.title_accent,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )
        center_layout.addWidget(self.subtitle_label)
        center_layout.addStretch(1)

        # ---------------------------------------------------------
        # ÁREA DIREITA — SENAI
        # ---------------------------------------------------------

        right_area = QWidget()
        right_area.setObjectName("appHeaderSideArea")
        right_area.setFixedWidth(310)

        right_layout = QHBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.senai_logo = self._create_logo(
            "senai.png",
            maximum_width=176,
            maximum_height=52,
            fallback="SENAI",
        )

        right_layout.addWidget(self.senai_logo)

        content_layout.addWidget(left_area)
        content_layout.addWidget(center, 1)
        content_layout.addWidget(right_area)

        separator = QFrame()
        separator.setObjectName("appHeaderSeparator")
        separator.setFixedHeight(2)

        root_layout.addLayout(content_layout)
        root_layout.addWidget(separator)

    # =============================================================
    # LOGOS
    # =============================================================

    def _create_logo(
        self,
        file_name: str,
        *,
        maximum_width: int,
        maximum_height: int,
        fallback: str,
    ) -> QLabel:
        label = QLabel()
        label.setObjectName("appHeaderLogo")
        label.setFixedSize(maximum_width, maximum_height)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "logos"
            / file_name
        )

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))

            if not pixmap.isNull():
                label.setPixmap(
                    pixmap.scaled(
                        maximum_width,
                        maximum_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return label

        label.setText(fallback)
        label.setObjectName("appHeaderLogoFallback")
        return label

    # =============================================================
    # ESTILO LOCAL
    # =============================================================

    def _apply_component_style(self) -> None:
        self.setStyleSheet(
            """
            QFrame#appHeader {
                background-color: #FCFDFE;
                border: none;
                border-bottom: 1px solid #D8E3EC;
            }

            QWidget#appHeaderCenter,
            QWidget#appHeaderSideArea {
                background-color: transparent;
                border: none;
            }

            QLabel#appHeaderTitle {
                background-color: transparent;
                color: #0A4F88;
                border: none;
                font-family: "Bahnschrift SemiBold", "Segoe UI Semibold";
                font-size: 35px;
                font-weight: 700;
                letter-spacing: 3px;
            }

            QFrame#appHeaderTitleAccent {
                background-color: #F07C00;
                border: none;
                border-radius: 1px;
            }

            QLabel#appHeaderSubtitle {
                background-color: transparent;
                color: #49637B;
                border: none;
                font-family: "Segoe UI";
                font-size: 11px;
                font-weight: 500;
            }

            QLabel#appHeaderLogo {
                background-color: transparent;
                border: none;
            }

            QLabel#appHeaderLogoFallback {
                background-color: transparent;
                color: #173A5E;
                border: none;
                font-size: 12px;
                font-weight: 700;
            }

            QFrame#appHeaderSeparator {
                background-color: #0873C5;
                border: none;
            }
            """
        )