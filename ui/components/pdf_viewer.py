from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Callable

import fitz

from PySide6.QtCore import (
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QImage,
    QMouseEvent,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


RenderCallback = Callable[[int, float], bytes | QPixmap]


class PdfScrollArea(QScrollArea):
    """
    Área de rolagem principal com Ctrl + roda do mouse para zoom.
    """

    zoom_step_requested = Signal(int)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            direction = 1 if event.angleDelta().y() > 0 else -1
            self.zoom_step_requested.emit(direction)
            event.accept()
            return

        super().wheelEvent(event)


class PdfThumbnailCard(QFrame):
    """
    Card clicável de miniatura.

    Não utiliza QListWidget. Assim, largura, altura, alinhamento e
    seleção ficam totalmente sob controle do componente.
    """

    clicked = Signal(int)

    def __init__(
        self,
        page_index: int,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.page_index = page_index

        self.setObjectName("pdfThumbnailCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(228)
        self.setMinimumHeight(276)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setObjectName("pdfThumbnailImage")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(198, 238)

        self.page_label = QLabel(f"Página {page_index + 1}")
        self.page_label.setObjectName("pdfThumbnailPageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(
            self.image_label,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )
        layout.addWidget(self.page_label)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_index)
            event.accept()
            return

        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)

        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class PdfViewer(QWidget):
    """
    Visualizador universal de PDF com layout profissional.

    Recursos mantidos:
    - arquivo PDF ou provedor externo;
    - cache de páginas;
    - miniaturas;
    - ajuste à página;
    - ajuste à largura;
    - zoom manual;
    - Ctrl + roda do mouse;
    - navegação entre páginas.
    """

    page_changed = Signal(int)
    zoom_changed = Signal(int)
    document_loaded = Signal(str)

    FIT_PAGE = "page"
    FIT_WIDTH = "width"
    MANUAL = "manual"

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.pdf_path: Path | None = None
        self.document: fitz.Document | None = None
        self.render_callback: RenderCallback | None = None

        self.document_name = "Nenhum PDF carregado"
        self.total_pages = 0
        self.current_page_index = 0

        self.fit_mode = self.FIT_PAGE
        self.zoom_percent = 100
        self.current_display_zoom = 100

        self.thumbnail_width = 198

        self.thumbnail_cards: list[
            PdfThumbnailCard
        ] = []

        self._base_page_sizes: dict[
            int,
            QSize,
        ] = {}

        self._page_cache: OrderedDict[
            tuple[int, int],
            QPixmap,
        ] = OrderedDict()

        self._thumbnail_cache: dict[
            int,
            QPixmap,
        ] = {}

        self._cache_limit = 20

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(90)
        self._resize_timer.timeout.connect(
            self._render_after_resize
        )

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---------------------------------------------------------
        # LATERAL DE MINIATURAS
        # ---------------------------------------------------------

        self.sidebar = QFrame()
        self.sidebar.setObjectName("pdfSidebar")
        self.sidebar.setFixedWidth(272)
        self.sidebar.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(
            14,
            14,
            14,
            12,
        )
        sidebar_layout.setSpacing(10)

        report_label = QLabel("RELATÓRIO")
        report_label.setObjectName(
            "pdfSidebarSectionTitle"
        )

        self.file_name_label = QLabel(
            self.document_name
        )
        self.file_name_label.setObjectName(
            "pdfDocumentName"
        )
        self.file_name_label.setWordWrap(True)
        self.file_name_label.setMaximumHeight(62)

        self.page_count_label = QLabel("0 páginas")
        self.page_count_label.setObjectName(
            "pdfDocumentMeta"
        )

        sidebar_layout.addWidget(report_label)
        sidebar_layout.addWidget(
            self.file_name_label
        )
        sidebar_layout.addWidget(
            self.page_count_label
        )

        separator = QFrame()
        separator.setObjectName(
            "pdfSidebarSeparator"
        )
        separator.setFixedHeight(1)

        sidebar_layout.addWidget(separator)

        pages_label = QLabel("PÁGINAS")
        pages_label.setObjectName(
            "pdfSidebarSectionTitle"
        )

        sidebar_layout.addWidget(pages_label)

        self.thumbnails_scroll = QScrollArea()
        self.thumbnails_scroll.setObjectName(
            "pdfThumbnailsScroll"
        )
        self.thumbnails_scroll.setWidgetResizable(True)
        self.thumbnails_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        self.thumbnails_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.thumbnails_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.thumbnails_container = QWidget()
        self.thumbnails_container.setObjectName(
            "pdfThumbnailsContainer"
        )

        self.thumbnails_layout = QVBoxLayout(
            self.thumbnails_container
        )
        self.thumbnails_layout.setContentsMargins(
            0,
            0,
            4,
            0,
        )
        self.thumbnails_layout.setSpacing(10)
        self.thumbnails_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.thumbnails_scroll.setWidget(
            self.thumbnails_container
        )

        sidebar_layout.addWidget(
            self.thumbnails_scroll,
            1,
        )

        self.sidebar_page_indicator = QLabel("0 / 0")
        self.sidebar_page_indicator.setObjectName(
            "pdfPageIndicator"
        )
        self.sidebar_page_indicator.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        sidebar_layout.addWidget(
            self.sidebar_page_indicator
        )

        root_layout.addWidget(self.sidebar)

        # ---------------------------------------------------------
        # ÁREA PRINCIPAL
        # ---------------------------------------------------------

        self.viewer_frame = QFrame()
        self.viewer_frame.setObjectName(
            "pdfViewerCard"
        )
        self.viewer_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        viewer_layout = QVBoxLayout(
            self.viewer_frame
        )
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)

        # ---------------------------------------------------------
        # TOOLBAR
        # ---------------------------------------------------------

        self.toolbar = QFrame()
        self.toolbar.setObjectName("pdfToolbar")
        self.toolbar.setFixedHeight(54)

        toolbar_layout = QHBoxLayout(
            self.toolbar
        )
        toolbar_layout.setContentsMargins(
            14,
            8,
            14,
            8,
        )
        toolbar_layout.setSpacing(8)

        self.previous_button = self._create_toolbar_button(
            "←",
            "Página anterior",
            self.previous_page,
        )

        self.current_page_label = QLabel("0 / 0")
        self.current_page_label.setObjectName(
            "pdfToolbarValue"
        )
        self.current_page_label.setMinimumWidth(68)
        self.current_page_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.next_button = self._create_toolbar_button(
            "→",
            "Próxima página",
            self.next_page,
        )

        self.fit_page_button = QPushButton(
            "Ajustar à página"
        )
        self.fit_page_button.setObjectName(
            "pdfToolbarAction"
        )
        self.fit_page_button.setMinimumHeight(34)
        self.fit_page_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.fit_page_button.clicked.connect(
            self.fit_to_page
        )

        self.fit_width_button = QPushButton(
            "Ajustar à largura"
        )
        self.fit_width_button.setObjectName(
            "pdfToolbarAction"
        )
        self.fit_width_button.setMinimumHeight(34)
        self.fit_width_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.fit_width_button.clicked.connect(
            self.fit_to_width
        )

        self.zoom_out_button = self._create_toolbar_button(
            "−",
            "Diminuir zoom",
            self.zoom_out,
        )

        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName(
            "pdfToolbarValue"
        )
        self.zoom_label.setMinimumWidth(58)
        self.zoom_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.zoom_in_button = self._create_toolbar_button(
            "+",
            "Aumentar zoom",
            self.zoom_in,
        )

        toolbar_layout.addWidget(
            self.previous_button
        )
        toolbar_layout.addWidget(
            self.current_page_label
        )
        toolbar_layout.addWidget(
            self.next_button
        )

        self._add_toolbar_separator(
            toolbar_layout
        )

        toolbar_layout.addWidget(
            self.fit_page_button
        )
        toolbar_layout.addWidget(
            self.fit_width_button
        )

        self._add_toolbar_separator(
            toolbar_layout
        )

        toolbar_layout.addWidget(
            self.zoom_out_button
        )
        toolbar_layout.addWidget(
            self.zoom_label
        )
        toolbar_layout.addWidget(
            self.zoom_in_button
        )

        toolbar_layout.addStretch(1)

        viewer_layout.addWidget(self.toolbar)

        # ---------------------------------------------------------
        # PÁGINA
        # ---------------------------------------------------------

        self.page_scroll = PdfScrollArea()
        self.page_scroll.setObjectName(
            "pdfPageScroll"
        )
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.page_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        self.page_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.page_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.page_scroll.zoom_step_requested.connect(
            self._ctrl_wheel_zoom
        )

        self.page_container = QWidget()
        self.page_container.setObjectName(
            "pdfPageContainer"
        )

        page_layout = QVBoxLayout(
            self.page_container
        )
        page_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )
        page_layout.setSpacing(0)
        page_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.page_label = QLabel(
            "Nenhum documento carregado"
        )
        self.page_label.setObjectName(
            "pdfPageImage"
        )
        self.page_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.page_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        page_layout.addWidget(
            self.page_label,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        self.page_scroll.setWidget(
            self.page_container
        )

        viewer_layout.addWidget(
            self.page_scroll,
            1,
        )

        root_layout.addWidget(
            self.viewer_frame,
            1,
        )

        self.update_navigation_state()

    def _create_toolbar_button(
        self,
        text: str,
        tooltip: str,
        callback,
    ) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("pdfToolbarButton")
        button.setFixedSize(36, 34)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)

        return button

    def _add_toolbar_separator(
        self,
        layout: QHBoxLayout,
    ) -> None:
        separator = QFrame()
        separator.setObjectName(
            "pdfToolbarSeparator"
        )
        separator.setFixedSize(1, 28)

        layout.addWidget(separator)

    # =============================================================
    # FONTES DE DOCUMENTO
    # =============================================================

    def set_pdf(
        self,
        pdf_path: str | Path,
    ) -> None:
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                "O arquivo PDF não foi encontrado."
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "O arquivo informado não é um PDF."
            )

        self.close_document()

        self.pdf_path = path
        self.document = fitz.open(str(path))
        self.render_callback = None

        self.document_name = path.name
        self.total_pages = self.document.page_count

        self._finish_document_load(str(path))

    def set_document_source(
        self,
        *,
        document_name: str,
        page_count: int,
        render_callback: RenderCallback,
        source_id: str = "",
    ) -> None:
        if page_count < 0:
            raise ValueError(
                "A quantidade de páginas não pode ser negativa."
            )

        self.close_document()

        self.render_callback = render_callback
        self.document_name = (
            document_name
            or "Documento PDF"
        )
        self.total_pages = int(page_count)

        self._finish_document_load(
            source_id
            or self.document_name
        )

    def _finish_document_load(
        self,
        emitted_source: str,
    ) -> None:
        self.current_page_index = 0
        self.fit_mode = self.FIT_PAGE
        self.zoom_percent = 100
        self.current_display_zoom = 100

        self.file_name_label.setText(
            self.document_name
        )
        self.page_count_label.setText(
            (
                f"{self.total_pages} página"
                if self.total_pages == 1
                else f"{self.total_pages} páginas"
            )
        )

        self.populate_thumbnails()

        if self.total_pages > 0:
            self.select_page(0)
            QTimer.singleShot(
                0,
                self.render_current_page,
            )

        self.update_navigation_state()
        self.document_loaded.emit(
            emitted_source
        )

    # =============================================================
    # MINIATURAS
    # =============================================================

    def populate_thumbnails(self) -> None:
        self._clear_layout(
            self.thumbnails_layout
        )

        self.thumbnail_cards = []

        for page_index in range(
            self.total_pages
        ):
            card = PdfThumbnailCard(
                page_index
            )
            card.clicked.connect(
                self.select_page
            )

            self.thumbnail_cards.append(card)
            self.thumbnails_layout.addWidget(card)

        self.thumbnails_layout.addStretch(1)

        for page_index in range(
            self.total_pages
        ):
            QTimer.singleShot(
                page_index * 8,
                lambda index=page_index:
                    self.load_thumbnail(index),
            )

    def load_thumbnail(
        self,
        page_index: int,
    ) -> None:
        if not self._valid_page(page_index):
            return

        if page_index in self._thumbnail_cache:
            thumbnail = self._thumbnail_cache[
                page_index
            ]
        else:
            page_size = self._get_base_page_size(
                page_index
            )

            if page_size.width() <= 0:
                return

            scale = (
                self.thumbnail_width
                / page_size.width()
            )

            thumbnail = self._render_page_pixmap(
                page_index,
                scale,
            )

            if thumbnail.isNull():
                return

            self._thumbnail_cache[
                page_index
            ] = thumbnail

        if page_index >= len(
            self.thumbnail_cards
        ):
            return

        card = self.thumbnail_cards[
            page_index
        ]

        fitted = thumbnail.scaled(
            card.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        card.image_label.setPixmap(fitted)

    # =============================================================
    # NAVEGAÇÃO
    # =============================================================

    def select_page(
        self,
        page_index: int,
    ) -> None:
        if not self._valid_page(page_index):
            return

        self.current_page_index = page_index

        for index, card in enumerate(
            self.thumbnail_cards
        ):
            card.set_selected(
                index == page_index
            )

        self.render_current_page(
            reset_scroll=True
        )

        self.update_navigation_state()
        self.page_changed.emit(page_index)

    def previous_page(self) -> None:
        if self.current_page_index <= 0:
            return

        self.select_page(
            self.current_page_index - 1
        )

    def next_page(self) -> None:
        if (
            self.current_page_index
            >= self.total_pages - 1
        ):
            return

        self.select_page(
            self.current_page_index + 1
        )

    # =============================================================
    # RENDERIZAÇÃO
    # =============================================================

    def render_current_page(
        self,
        reset_scroll: bool = False,
    ) -> None:
        if not self._valid_page(
            self.current_page_index
        ):
            self.page_label.clear()
            self.page_label.setText(
                "Nenhum documento carregado"
            )
            return

        scale = self.calculate_render_scale(
            self.current_page_index
        )

        pixmap = self._render_page_pixmap(
            self.current_page_index,
            scale,
        )

        if pixmap.isNull():
            self.page_label.clear()
            self.page_label.setText(
                "Não foi possível renderizar esta página."
            )
            return

        self.page_label.setPixmap(pixmap)
        self.page_label.resize(pixmap.size())
        self.page_label.setMinimumSize(
            pixmap.size()
        )

        self.page_container.setMinimumSize(
            pixmap.width() + 24,
            pixmap.height() + 24,
        )

        calculated_zoom = max(
            1,
            int(round(scale * 100)),
        )

        self.current_display_zoom = calculated_zoom
        self.zoom_label.setText(
            f"{calculated_zoom}%"
        )

        page_text = (
            f"{self.current_page_index + 1} "
            f"/ {self.total_pages}"
        )

        self.current_page_label.setText(
            page_text
        )
        self.sidebar_page_indicator.setText(
            page_text
        )

        if reset_scroll:
            self.page_scroll.verticalScrollBar().setValue(0)
            self.page_scroll.horizontalScrollBar().setValue(0)

        self.zoom_changed.emit(calculated_zoom)

    def calculate_render_scale(
        self,
        page_index: int,
    ) -> float:
        viewport = self.page_scroll.viewport()

        available_width = max(
            180,
            viewport.width() - 30,
        )
        available_height = max(
            180,
            viewport.height() - 30,
        )

        page_size = self._get_base_page_size(
            page_index
        )

        page_width = max(
            1,
            page_size.width(),
        )
        page_height = max(
            1,
            page_size.height(),
        )

        if self.fit_mode == self.FIT_PAGE:
            return max(
                0.20,
                min(
                    available_width / page_width,
                    available_height / page_height,
                ),
            )

        if self.fit_mode == self.FIT_WIDTH:
            return max(
                0.20,
                available_width / page_width,
            )

        return max(
            0.25,
            self.zoom_percent / 100.0,
        )

    def _render_page_pixmap(
        self,
        page_index: int,
        scale: float,
    ) -> QPixmap:
        scale_key = max(
            1,
            int(round(scale * 1000)),
        )

        cache_key = (
            page_index,
            scale_key,
        )

        cached = self._page_cache.get(
            cache_key
        )

        if cached is not None:
            self._page_cache.move_to_end(
                cache_key
            )
            return cached

        pixmap = QPixmap()

        if self.document is not None:
            page = self.document[
                page_index
            ]

            fitz_pixmap = page.get_pixmap(
                matrix=fitz.Matrix(
                    scale,
                    scale,
                ),
                alpha=False,
            )

            pixmap = self._fitz_pixmap_to_qpixmap(
                fitz_pixmap
            )

        elif self.render_callback is not None:
            rendered = self.render_callback(
                page_index,
                scale,
            )

            if isinstance(
                rendered,
                QPixmap,
            ):
                pixmap = rendered
            else:
                pixmap.loadFromData(
                    rendered,
                    "PNG",
                )

        if not pixmap.isNull():
            self._page_cache[
                cache_key
            ] = pixmap

            self._page_cache.move_to_end(
                cache_key
            )

            self._trim_cache()

        return pixmap

    def _get_base_page_size(
        self,
        page_index: int,
    ) -> QSize:
        cached = self._base_page_sizes.get(
            page_index
        )

        if cached is not None:
            return cached

        if self.document is not None:
            rect = self.document[
                page_index
            ].rect

            size = QSize(
                max(
                    1,
                    int(round(rect.width)),
                ),
                max(
                    1,
                    int(round(rect.height)),
                ),
            )
        else:
            pixmap = self._render_page_pixmap(
                page_index,
                1.0,
            )
            size = pixmap.size()

        self._base_page_sizes[
            page_index
        ] = size

        return size

    def _trim_cache(self) -> None:
        while (
            len(self._page_cache)
            > self._cache_limit
        ):
            self._page_cache.popitem(
                last=False
            )

    # =============================================================
    # ZOOM
    # =============================================================

    def fit_to_page(self) -> None:
        if not self.has_document():
            return

        self.fit_mode = self.FIT_PAGE
        self.render_current_page()

    def fit_to_width(self) -> None:
        if not self.has_document():
            return

        self.fit_mode = self.FIT_WIDTH
        self.render_current_page()

    def set_manual_zoom(
        self,
        value: int,
    ) -> None:
        if not self.has_document():
            return

        self.fit_mode = self.MANUAL
        self.zoom_percent = int(value)
        self.render_current_page()

    def zoom_in(self) -> None:
        if not self.has_document():
            return

        base_zoom = (
            self.zoom_percent
            if self.fit_mode == self.MANUAL
            else self.current_display_zoom
        )

        self._set_zoom_value(
            base_zoom + 10
        )

    def zoom_out(self) -> None:
        if not self.has_document():
            return

        base_zoom = (
            self.zoom_percent
            if self.fit_mode == self.MANUAL
            else self.current_display_zoom
        )

        self._set_zoom_value(
            base_zoom - 10
        )

    def _ctrl_wheel_zoom(
        self,
        direction: int,
    ) -> None:
        if direction > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _set_zoom_value(
        self,
        value: int,
    ) -> None:
        value = max(
            25,
            min(
                300,
                int(value),
            ),
        )

        self.fit_mode = self.MANUAL
        self.zoom_percent = value

        self.render_current_page()

    # =============================================================
    # REDIMENSIONAMENTO
    # =============================================================

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        if (
            self.has_document()
            and self.fit_mode
            in {
                self.FIT_PAGE,
                self.FIT_WIDTH,
            }
        ):
            self._resize_timer.start()

    def showEvent(self, event) -> None:
        super().showEvent(event)

        if self.has_document():
            QTimer.singleShot(
                0,
                self.render_current_page,
            )

    def _render_after_resize(self) -> None:
        if (
            self.has_document()
            and self.fit_mode
            in {
                self.FIT_PAGE,
                self.FIT_WIDTH,
            }
        ):
            self.render_current_page()

    # =============================================================
    # ESTADO E LIMPEZA
    # =============================================================

    def has_document(self) -> bool:
        return (
            self.total_pages > 0
            and (
                self.document is not None
                or self.render_callback is not None
            )
        )

    def update_navigation_state(self) -> None:
        has_document = self.has_document()

        self.previous_button.setEnabled(
            has_document
            and self.current_page_index > 0
        )

        self.next_button.setEnabled(
            has_document
            and self.current_page_index
            < self.total_pages - 1
        )

        self.fit_page_button.setEnabled(
            has_document
        )
        self.fit_width_button.setEnabled(
            has_document
        )
        self.zoom_in_button.setEnabled(
            has_document
        )
        self.zoom_out_button.setEnabled(
            has_document
        )

        if not has_document:
            self.current_page_label.setText(
                "0 / 0"
            )
            self.sidebar_page_indicator.setText(
                "0 / 0"
            )
            self.zoom_label.setText("100%")

    def close_document(self) -> None:
        if self.document is not None:
            self.document.close()

        self.document = None
        self.pdf_path = None
        self.render_callback = None

        self.document_name = (
            "Nenhum PDF carregado"
        )
        self.total_pages = 0
        self.current_page_index = 0

        self._page_cache.clear()
        self._thumbnail_cache.clear()
        self._base_page_sizes.clear()

        self._clear_layout(
            self.thumbnails_layout
        )
        self.thumbnail_cards = []

        self.page_label.clear()
        self.page_label.setText(
            "Nenhum documento carregado"
        )
        self.page_label.setMinimumSize(
            QSize(0, 0)
        )
        self.page_label.adjustSize()

        self.page_container.setMinimumSize(
            QSize(0, 0)
        )

        self.file_name_label.setText(
            self.document_name
        )
        self.page_count_label.setText(
            "0 páginas"
        )

        self.update_navigation_state()

    def clear(self) -> None:
        self.close_document()

    def _valid_page(
        self,
        page_index: int,
    ) -> bool:
        return (
            self.has_document()
            and 0
            <= page_index
            < self.total_pages
        )

    def _clear_layout(
        self,
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(
                    child_layout
                )

    # =============================================================
    # CONVERSÃO
    # =============================================================

    def _fitz_pixmap_to_qpixmap(
        self,
        pixmap: fitz.Pixmap,
    ) -> QPixmap:
        image_format = (
            QImage.Format.Format_RGBA8888
            if pixmap.alpha
            else QImage.Format.Format_RGB888
        )

        image = QImage(
            pixmap.samples,
            pixmap.width,
            pixmap.height,
            pixmap.stride,
            image_format,
        )

        return QPixmap.fromImage(
            image.copy()
        )