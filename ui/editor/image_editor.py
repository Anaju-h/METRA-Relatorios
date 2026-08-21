from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QPixmap,
)
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from models.project_image import ProjectImage
from services.annotation_service import (
    AnnotationService,
)
from ui.editor.graphics_scene import (
    AnnotationScene,
    DEFAULT_COLOR,
    normalized_color,
)


class ImageEditor(QWidget):
    back_requested = Signal()

    PRESET_COLORS = [
        (
            "Vermelho",
            "#EB2323",
        ),
        (
            "Azul",
            "#0067B1",
        ),
        (
            "Amarelo",
            "#FFD600",
        ),
        (
            "Verde",
            "#1D9A55",
        ),
        (
            "Branco",
            "#FFFFFF",
        ),
        (
            "Preto",
            "#111111",
        ),
    ]

    def __init__(self):
        super().__init__()

        self.current_image: (
            ProjectImage
            | None
        ) = None

        self.annotation_service = (
            AnnotationService()
        )

        self.scene = AnnotationScene()

        self.tool_buttons = {}

        self.color_buttons = {}

        self.updating_properties = False

        self.current_color = DEFAULT_COLOR

        self.zoom_factor = 1.0

        self.build_ui()

        self.scene.tool_changed.connect(
            self.update_active_tool
        )

        self.scene.selectionChanged.connect(
            self.update_properties_panel
        )

        self.scene.history_changed.connect(
            self.update_history_buttons
        )

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            40,
            24,
            40,
            28,
        )

        root_layout.setSpacing(
            12
        )

        # ---------------------------------------------------------
        # TOPO
        # ---------------------------------------------------------

        top_layout = QHBoxLayout()

        self.back_button = QPushButton(
            "← Imagens"
        )

        self.back_button.setObjectName(
            "backButton"
        )

        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        top_layout.addWidget(
            self.back_button
        )

        top_layout.addStretch()

        self.undo_button = QPushButton(
            "Desfazer"
        )

        self.undo_button.setObjectName(
            "secondaryButton"
        )

        self.undo_button.setMinimumHeight(
            42
        )

        self.undo_button.clicked.connect(
            self.scene.undo
        )

        self.redo_button = QPushButton(
            "Refazer"
        )

        self.redo_button.setObjectName(
            "secondaryButton"
        )

        self.redo_button.setMinimumHeight(
            42
        )

        self.redo_button.clicked.connect(
            self.scene.redo
        )

        self.save_button = QPushButton(
            "Salvar marcações"
        )

        self.save_button.setObjectName(
            "primaryButton"
        )

        self.save_button.setMinimumHeight(
            42
        )

        self.save_button.clicked.connect(
            self.save_annotations
        )

        top_layout.addWidget(
            self.undo_button
        )

        top_layout.addWidget(
            self.redo_button
        )

        top_layout.addWidget(
            self.save_button
        )

        root_layout.addLayout(
            top_layout
        )

        self.title = QLabel(
            "Editor de marcações"
        )

        self.title.setObjectName(
            "pageTitle"
        )

        self.subtitle = QLabel(
            "-"
        )

        self.subtitle.setObjectName(
            "projectMeta"
        )

        root_layout.addWidget(
            self.title
        )

        root_layout.addWidget(
            self.subtitle
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(
            14
        )

        # =========================================================
        # LATERAL
        # =========================================================

        sidebar_scroll = QScrollArea()

        sidebar_scroll.setWidgetResizable(
            True
        )

        sidebar_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        sidebar_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        sidebar_scroll.setFixedWidth(
            250
        )

        sidebar = QFrame()

        sidebar.setObjectName(
            "dashboardCard"
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            14,
            16,
            14,
            16,
        )

        sidebar_layout.setSpacing(
            9
        )

        tools_title = QLabel(
            "Ferramentas"
        )

        tools_title.setObjectName(
            "cardTitle"
        )

        sidebar_layout.addWidget(
            tools_title
        )

        tools = [
            (
                "Seleção",
                AnnotationScene.TOOL_SELECT,
            ),
            (
                "Retângulo",
                AnnotationScene.TOOL_RECTANGLE,
            ),
            (
                "Círculo",
                AnnotationScene.TOOL_CIRCLE,
            ),
            (
                "Linha",
                AnnotationScene.TOOL_LINE,
            ),
            (
                "Seta",
                AnnotationScene.TOOL_ARROW,
            ),
            (
                "Texto",
                AnnotationScene.TOOL_TEXT,
            ),
            (
                "Marcador numerado",
                AnnotationScene.TOOL_MARKER,
            ),
        ]

        for text, tool in tools:
            button = QPushButton(
                text
            )

            button.setCheckable(
                True
            )

            button.setObjectName(
                "secondaryButton"
            )

            button.setMinimumHeight(
                42
            )

            button.clicked.connect(
                lambda checked=False,
                selected_tool=tool:
                self.scene.set_tool(
                    selected_tool
                )
            )

            self.tool_buttons[
                tool
            ] = button

            sidebar_layout.addWidget(
                button
            )

        shortcut_hint = QLabel(
            "Esc: seleção\n"
            "Delete: excluir\n"
            "Ctrl+Z: desfazer\n"
            "Ctrl+Y: refazer"
        )

        shortcut_hint.setObjectName(
            "cardDescription"
        )

        sidebar_layout.addWidget(
            shortcut_hint
        )

        separator = QFrame()

        separator.setFrameShape(
            QFrame.Shape.HLine
        )

        sidebar_layout.addWidget(
            separator
        )

        # ---------------------------------------------------------
        # COR
        # ---------------------------------------------------------

        color_title = QLabel(
            "Cor da marcação"
        )

        color_title.setObjectName(
            "cardTitle"
        )

        sidebar_layout.addWidget(
            color_title
        )

        colors_grid = QGridLayout()

        colors_grid.setSpacing(
            6
        )

        for index, (
            color_name,
            color_value,
        ) in enumerate(
            self.PRESET_COLORS
        ):
            button = QPushButton()

            button.setToolTip(
                color_name
            )

            button.setFixedSize(
                42,
                34,
            )

            button.setCheckable(
                True
            )

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color_value};
                    border: 2px solid #D0D8E1;
                    border-radius: 6px;
                }}

                QPushButton:checked {{
                    border: 3px solid #0067B1;
                }}
                """
            )

            button.clicked.connect(
                lambda checked=False,
                selected_color=color_value:
                self.apply_color(
                    selected_color
                )
            )

            self.color_buttons[
                color_value.upper()
            ] = button

            colors_grid.addWidget(
                button,
                index // 3,
                index % 3,
            )

        sidebar_layout.addLayout(
            colors_grid
        )

        self.custom_color_button = QPushButton(
            "Escolher outra cor..."
        )

        self.custom_color_button.setObjectName(
            "secondaryButton"
        )

        self.custom_color_button.setMinimumHeight(
            38
        )

        self.custom_color_button.clicked.connect(
            self.choose_custom_color
        )

        sidebar_layout.addWidget(
            self.custom_color_button
        )

        # ---------------------------------------------------------
        # PROPRIEDADES
        # ---------------------------------------------------------

        properties_title = QLabel(
            "Propriedades"
        )

        properties_title.setObjectName(
            "cardTitle"
        )

        sidebar_layout.addWidget(
            properties_title
        )

        self.selection_type_label = QLabel(
            "Nenhuma marcação selecionada"
        )

        self.selection_type_label.setObjectName(
            "cardDescription"
        )

        sidebar_layout.addWidget(
            self.selection_type_label
        )

        self.content_input = QLineEdit()

        self.content_input.setPlaceholderText(
            "Conteúdo"
        )

        self.content_input.setMinimumHeight(
            38
        )

        self.content_input.editingFinished.connect(
            self.apply_text_content
        )

        sidebar_layout.addWidget(
            self.content_input
        )

        self.font_size_input = QSpinBox()

        self.font_size_input.setRange(
            8,
            96,
        )

        self.font_size_input.setValue(
            18
        )

        self.font_size_input.setPrefix(
            "Texto: "
        )

        self.font_size_input.valueChanged.connect(
            self.apply_font_size
        )

        sidebar_layout.addWidget(
            self.font_size_input
        )

        self.stroke_width_input = QSpinBox()

        self.stroke_width_input.setRange(
            1,
            20,
        )

        self.stroke_width_input.setValue(
            3
        )

        self.stroke_width_input.setPrefix(
            "Espessura: "
        )

        self.stroke_width_input.valueChanged.connect(
            self.apply_stroke_width
        )

        sidebar_layout.addWidget(
            self.stroke_width_input
        )

        self.delete_button = QPushButton(
            "Excluir selecionado"
        )

        self.delete_button.setObjectName(
            "dangerButton"
        )

        self.delete_button.clicked.connect(
            self.scene.delete_selected
        )

        self.clear_button = QPushButton(
            "Limpar marcações"
        )

        self.clear_button.setObjectName(
            "secondaryButton"
        )

        self.clear_button.clicked.connect(
            self.confirm_clear_annotations
        )

        sidebar_layout.addWidget(
            self.delete_button
        )

        sidebar_layout.addWidget(
            self.clear_button
        )

        sidebar_layout.addStretch()

        sidebar_scroll.setWidget(
            sidebar
        )

        content_layout.addWidget(
            sidebar_scroll
        )

        # =========================================================
        # VIEWER
        # =========================================================

        viewer_container = QFrame()

        viewer_container.setObjectName(
            "dashboardCard"
        )

        viewer_layout = QVBoxLayout(
            viewer_container
        )

        viewer_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        zoom_layout = QHBoxLayout()

        zoom_layout.addStretch()

        zoom_out_button = QPushButton(
            "−"
        )

        # Estilo local para garantir que o símbolo de zoom permaneça
        # visível independentemente das regras globais do app.qss.
        zoom_out_button.setObjectName(
            "zoomButton"
        )

        zoom_out_button.setFixedSize(
            42,
            38,
        )

        zoom_out_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FFFFFF;
                color: #005AA9;
                border: 1px solid #B9CCE0;
                border-radius: 7px;
                font-family: "Segoe UI";
                font-size: 18px;
                font-weight: 600;
                padding: 0px;
            }

            QPushButton:hover {
                background-color: #EEF6FC;
                border-color: #0077C8;
            }

            QPushButton:pressed {
                background-color: #DCECF8;
            }

            QPushButton:disabled {
                background-color: #F4F6F8;
                color: #A8B3BE;
                border-color: #D7DEE5;
            }
            """
        )

        zoom_out_button.clicked.connect(
            self.zoom_out
        )

        self.zoom_label = QLabel(
            "100%"
        )

        self.zoom_label.setMinimumWidth(
            55
        )

        self.zoom_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        zoom_in_button = QPushButton(
            "+"
        )

        # Mesmo padrão visual do botão de redução de zoom.
        zoom_in_button.setObjectName(
            "zoomButton"
        )

        zoom_in_button.setFixedSize(
            42,
            38,
        )

        zoom_in_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FFFFFF;
                color: #005AA9;
                border: 1px solid #B9CCE0;
                border-radius: 7px;
                font-family: "Segoe UI";
                font-size: 18px;
                font-weight: 600;
                padding: 0px;
            }

            QPushButton:hover {
                background-color: #EEF6FC;
                border-color: #0077C8;
            }

            QPushButton:pressed {
                background-color: #DCECF8;
            }

            QPushButton:disabled {
                background-color: #F4F6F8;
                color: #A8B3BE;
                border-color: #D7DEE5;
            }
            """
        )

        zoom_in_button.clicked.connect(
            self.zoom_in
        )

        fit_button = QPushButton(
            "Ajustar à tela"
        )

        fit_button.setObjectName(
            "secondaryButton"
        )

        fit_button.setMinimumHeight(
            38
        )

        fit_button.clicked.connect(
            self.fit_image
        )

        zoom_layout.addWidget(
            zoom_out_button
        )

        zoom_layout.addWidget(
            self.zoom_label
        )

        zoom_layout.addWidget(
            zoom_in_button
        )

        zoom_layout.addWidget(
            fit_button
        )

        viewer_layout.addLayout(
            zoom_layout
        )

        self.view = QGraphicsView(
            self.scene
        )

        self.view.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self.view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.view.setMinimumWidth(
            520
        )

        self.view.setMinimumHeight(
            420
        )

        viewer_layout.addWidget(
            self.view,
            1,
        )

        content_layout.addWidget(
            viewer_container,
            1,
        )

        root_layout.addLayout(
            content_layout,
            1,
        )

        self.apply_color(
            DEFAULT_COLOR,
            register_history=False,
        )

        self.update_active_tool(
            AnnotationScene.TOOL_SELECT
        )

        self.update_history_buttons(
            False,
            False,
        )

        self.update_properties_panel()

    # =============================================================
    # FERRAMENTAS E COR
    # =============================================================

    def update_active_tool(
        self,
        tool: str,
    ) -> None:
        for tool_name, button in (
            self.tool_buttons.items()
        ):
            button.setChecked(
                tool_name == tool
            )

    def choose_custom_color(
        self,
    ) -> None:
        selected = QColorDialog.getColor(
            normalized_color(
                self.current_color
            ),
            self,
            "Escolher cor da marcação",
        )

        if not selected.isValid():
            return

        self.apply_color(
            selected.name()
        )

    def apply_color(
        self,
        color: str,
        register_history: bool = True,
    ) -> None:
        normalized = (
            normalized_color(
                color
            )
            .name()
            .upper()
        )

        self.current_color = normalized

        self.scene.set_default_color(
            normalized
        )

        for color_value, button in (
            self.color_buttons.items()
        ):
            button.setChecked(
                color_value
                == normalized
            )

        item = self.get_selected_annotation()

        if item is None:
            return

        if register_history:
            self.scene.save_history_state()

        item.setData(
            4,
            normalized,
        )

        annotation_type = str(
            item.data(0)
        )

        if annotation_type in {
            "rectangle",
            "circle",
            "line",
            "arrow",
        }:
            item.setPen(
                self.scene.create_pen(
                    float(
                        item.data(3)
                        or 3.0
                    ),
                    normalized,
                )
            )

            if hasattr(
                item,
                "update_path",
            ):
                item.update_path()

        elif annotation_type in {
            "text",
            "marker",
        }:
            item.setBrush(
                normalized_color(
                    normalized
                )
            )

        item.update()

        self.scene.finalize_change()

    # =============================================================
    # IMAGEM
    # =============================================================

    def set_image(
        self,
        image: ProjectImage,
    ) -> None:
        self.current_image = image

        self.subtitle.setText(
            image.file_name
        )

        self.scene.clear()

        self.scene.annotation_items = []

        self.scene.next_marker_index = 1

        pixmap = QPixmap(
            image.file_path
        )

        if pixmap.isNull():
            QMessageBox.critical(
                self,
                "Erro ao abrir imagem",
                (
                    "Não foi possível carregar "
                    "a imagem selecionada."
                ),
            )

            return

        pixmap_item = QGraphicsPixmapItem(
            pixmap
        )

        pixmap_item.setZValue(
            -100
        )

        self.scene.addItem(
            pixmap_item
        )

        self.scene.set_background_item(
            pixmap_item
        )

        self.load_annotations()

        self.scene.reset_history()

        self.fit_image()

        self.view.setFocus()

    def load_annotations(
        self,
    ) -> None:
        if (
            self.current_image is None
            or self.current_image.id is None
        ):
            return

        annotations = (
            self.annotation_service
            .get_annotations(
                self.current_image.id
            )
        )

        for annotation in annotations:
            self.scene.add_annotation_from_data(
                {
                    "annotation_type":
                        annotation.annotation_type,

                    "x":
                        annotation.x,

                    "y":
                        annotation.y,

                    "width":
                        annotation.width,

                    "height":
                        annotation.height,

                    "end_x":
                        annotation.end_x,

                    "end_y":
                        annotation.end_y,

                    "text":
                        annotation.text,

                    "marker_text":
                        annotation.marker_text,

                    "font_size":
                        annotation.font_size,

                    "stroke_width":
                        annotation.stroke_width,

                    "color":
                        annotation.color,
                }
            )

        self.scene.recalculate_next_marker()

    # =============================================================
    # SELEÇÃO E PROPRIEDADES
    # =============================================================

    def get_selected_annotation(
        self,
    ):
        selected = [
            item
            for item in self.scene.selectedItems()
            if item in self.scene.annotation_items
        ]

        if len(selected) != 1:
            return None

        return selected[0]

    def update_properties_panel(
        self,
    ) -> None:
        item = self.get_selected_annotation()

        self.updating_properties = True

        try:
            if item is None:
                self.selection_type_label.setText(
                    "Nenhuma marcação selecionada"
                )

                self.content_input.clear()

                self.content_input.setEnabled(
                    False
                )

                self.font_size_input.setEnabled(
                    False
                )

                self.stroke_width_input.setEnabled(
                    False
                )

                self.delete_button.setEnabled(
                    False
                )

                return

            annotation_type = str(
                item.data(0)
            )

            names = {
                "rectangle":
                    "Retângulo",

                "circle":
                    "Círculo",

                "line":
                    "Linha",

                "arrow":
                    "Seta",

                "text":
                    "Texto",

                "marker":
                    "Marcador",
            }

            self.selection_type_label.setText(
                names.get(
                    annotation_type,
                    "Marcação",
                )
            )

            self.delete_button.setEnabled(
                True
            )

            text_type = (
                annotation_type
                in {
                    "text",
                    "marker",
                }
            )

            shape_type = (
                annotation_type
                in {
                    "rectangle",
                    "circle",
                    "line",
                    "arrow",
                }
            )

            self.content_input.setEnabled(
                text_type
            )

            self.font_size_input.setEnabled(
                text_type
            )

            self.stroke_width_input.setEnabled(
                shape_type
            )

            if text_type:
                self.content_input.setText(
                    item.text()
                )

                self.font_size_input.setValue(
                    int(
                        item.data(2)
                        or 18
                    )
                )

            else:
                self.content_input.clear()

            if shape_type:
                self.stroke_width_input.setValue(
                    int(
                        round(
                            float(
                                item.data(3)
                                or 3.0
                            )
                        )
                    )
                )

            selected_color = str(
                item.data(4)
                or DEFAULT_COLOR
            )

            self.current_color = (
                normalized_color(
                    selected_color
                )
                .name()
                .upper()
            )

            self.scene.set_default_color(
                self.current_color
            )

            for color_value, button in (
                self.color_buttons.items()
            ):
                button.setChecked(
                    color_value
                    == self.current_color
                )

        finally:
            self.updating_properties = False

    def apply_text_content(
        self,
    ) -> None:
        if self.updating_properties:
            return

        item = self.get_selected_annotation()

        if item is None:
            return

        value = (
            self.content_input
            .text()
            .strip()
        )

        if not value:
            return

        self.scene.save_history_state()

        item.setText(
            value
        )

        if item.data(0) == "marker":
            item.setData(
                1,
                value,
            )

            self.scene.recalculate_next_marker()

        self.scene.finalize_change()

    def apply_font_size(
        self,
        value: int,
    ) -> None:
        if self.updating_properties:
            return

        self.scene.set_default_font_size(
            value
        )

        item = self.get_selected_annotation()

        if item is None:
            return

        if item.data(0) not in {
            "text",
            "marker",
        }:
            return

        self.scene.save_history_state()

        font = item.font()

        font.setPointSize(
            value
        )

        font.setBold(
            item.data(0)
            == "marker"
        )

        item.setFont(
            font
        )

        item.setData(
            2,
            value,
        )

        self.scene.finalize_change()

    def apply_stroke_width(
        self,
        value: int,
    ) -> None:
        if self.updating_properties:
            return

        self.scene.set_default_stroke_width(
            value
        )

        item = self.get_selected_annotation()

        if item is None:
            return

        if item.data(0) not in {
            "rectangle",
            "circle",
            "line",
            "arrow",
        }:
            return

        self.scene.save_history_state()

        item.prepareGeometryChange()

        item.setData(
            3,
            float(
                value
            ),
        )

        item.setPen(
            self.scene.create_pen(
                float(
                    value
                ),
                str(
                    item.data(4)
                    or self.current_color
                ),
            )
        )

        if hasattr(
            item,
            "update_path",
        ):
            item.update_path()

        item.update()

        self.scene.finalize_change()

    # =============================================================
    # LIMPAR
    # =============================================================

    def confirm_clear_annotations(
        self,
    ) -> None:
        if not self.scene.annotation_items:
            return

        response = QMessageBox.question(
            self,
            "Limpar marcações",
            (
                "Deseja remover todas as marcações "
                "da imagem atual?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if (
            response
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.scene.clear_annotations()

    # =============================================================
    # ZOOM
    # =============================================================

    def fit_image(
        self,
    ) -> None:
        if self.scene.sceneRect().isNull():
            return

        self.view.fitInView(
            self.scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

        self.zoom_factor = 1.0

        self.update_zoom_label()

    def zoom_in(
        self,
    ) -> None:
        if self.zoom_factor >= 5.0:
            return

        self.view.scale(
            1.20,
            1.20,
        )

        self.zoom_factor *= 1.20

        self.update_zoom_label()

    def zoom_out(
        self,
    ) -> None:
        if self.zoom_factor <= 0.20:
            return

        self.view.scale(
            1 / 1.20,
            1 / 1.20,
        )

        self.zoom_factor /= 1.20

        self.update_zoom_label()

    def update_zoom_label(
        self,
    ) -> None:
        self.zoom_label.setText(
            f"{self.zoom_factor * 100:.0f}%"
        )

    # =============================================================
    # HISTÓRICO
    # =============================================================

    def update_history_buttons(
        self,
        can_undo: bool,
        can_redo: bool,
    ) -> None:
        self.undo_button.setEnabled(
            can_undo
        )

        self.redo_button.setEnabled(
            can_redo
        )

    # =============================================================
    # SALVAR
    # =============================================================

    def save_annotations(
        self,
    ) -> None:
        if (
            self.current_image is None
            or self.current_image.id is None
        ):
            return

        data = (
            self.scene
            .serialize_annotations()
        )

        try:
            self.annotation_service.save_annotations(
                image_id=(
                    self.current_image.id
                ),
                annotations_data=data,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar marcações",
                str(
                    error
                ),
            )

            return

        self.scene.reset_history()

        QMessageBox.information(
            self,
            "Marcações salvas",
            (
                f"{len(data)} marcação(ões) "
                "salva(s) com sucesso."
            ),
        )