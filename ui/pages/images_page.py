from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QMimeData,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QPixmap,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from models.project_image import ProjectImage
from services.image_service import (
    ImageService,
)
from ui.components.page_header import PageHeader
from ui.components.section_header import SectionHeader


# =================================================================
# ÁREA DE ARRASTAR E SOLTAR
# =================================================================


class ImageDropArea(QFrame):
    files_dropped = Signal(
        list
    )

    ALLOWED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    def __init__(self):
        super().__init__()

        self.setObjectName("imageDropArea")
        self.setAcceptDrops(True)

        self.setMinimumHeight(185)
        self.setMaximumHeight(185)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            35,
            22,
            35,
            22,
        )

        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel("JPG • PNG")
        badge.setObjectName("uploadBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Arraste uma ou mais imagens")
        title.setObjectName("uploadTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(
            "Solte fotografias, imagens CAD, renders\n"
            "ou registros do setup para adicioná-los ao processo."
        )

        description.setObjectName("uploadDescription")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        layout.addStretch()

        layout.addWidget(
            badge,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        layout.addWidget(
            title,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        layout.addWidget(
            description,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        layout.addStretch()

    def dragEnterEvent(
        self,
        event: QDragEnterEvent,
    ) -> None:
        if self._contains_valid_images(
            event.mimeData()
        ):
            event.acceptProposedAction()

            self.setProperty(
                "dragActive",
                True,
            )

            self.style().unpolish(
                self
            )

            self.style().polish(
                self
            )

            return

        event.ignore()

    def dragLeaveEvent(
        self,
        event,
    ) -> None:
        self._reset_drag_style()

        super().dragLeaveEvent(
            event
        )

    def dropEvent(
        self,
        event: QDropEvent,
    ) -> None:
        paths = self._extract_image_paths(
            event.mimeData()
        )

        self._reset_drag_style()

        if not paths:
            event.ignore()

            return

        event.acceptProposedAction()

        self.files_dropped.emit(
            paths
        )

    def _contains_valid_images(
        self,
        mime_data: QMimeData,
    ) -> bool:
        return bool(
            self._extract_image_paths(
                mime_data
            )
        )

    def _extract_image_paths(
        self,
        mime_data: QMimeData,
    ) -> list[str]:
        if not mime_data.hasUrls():
            return []

        result = []

        for url in mime_data.urls():
            if not url.isLocalFile():
                continue

            path = Path(
                url.toLocalFile()
            )

            if (
                path.is_file()
                and path.suffix.lower()
                in self.ALLOWED_EXTENSIONS
            ):
                result.append(
                    str(
                        path
                    )
                )

        return result

    def _reset_drag_style(
        self,
    ) -> None:
        self.setProperty(
            "dragActive",
            False,
        )

        self.style().unpolish(
            self
        )

        self.style().polish(
            self
        )


# =================================================================
# PÁGINA DE IMAGENS
# =================================================================


class ImagesPage(QWidget):
    back_requested = Signal()

    edit_image_requested = Signal(
        object
    )

    IMAGE_TYPES = [
        "Fotografia",
        "Setup de medição",
        "Fixação",
        "CAD",
        "Render",
        "Detalhe técnico",
        "Evidência de não conformidade",
        "Outro",
    ]

    def __init__(self):
        super().__init__()

        self.current_project: (
            Project
            | None
        ) = None

        self.image_service = (
            ImageService()
        )

        self.current_images: list[
            ProjectImage
        ] = []

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setObjectName("pageBackground")

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(34, 22, 34, 34)

        content = QWidget()
        content.setObjectName("pageContent")
        content.setMaximumWidth(1320)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        # ---------------------------------------------------------
        # CABEÇALHO
        # ---------------------------------------------------------

        self.page_header = PageHeader(
            title="Imagens do processo",
            subtitle=(
                "Organize fotografias, imagens CAD, renders e "
                "registros do setup utilizados no relatório."
            ),
            metadata="-",
            back_text="← Visão geral",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.add_button = QPushButton("+ Selecionar imagens")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setMinimumHeight(40)
        self.add_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.add_button.clicked.connect(self.select_images)

        self.page_header.add_action(self.add_button)
        content_layout.addWidget(self.page_header)

        # ---------------------------------------------------------
        # RESUMO
        # ---------------------------------------------------------

        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)

        self.primary_summary_card = QFrame()
        self.primary_summary_card.setObjectName("imageSummaryCard")

        primary_summary_layout = QHBoxLayout(
            self.primary_summary_card
        )
        primary_summary_layout.setContentsMargins(
            18, 14, 18, 14
        )
        primary_summary_layout.setSpacing(14)

        primary_text_layout = QVBoxLayout()
        primary_text_layout.setSpacing(3)

        primary_title = QLabel("Imagem principal")
        primary_title.setObjectName("cardTitle")

        self.primary_description = QLabel(
            "Nenhuma imagem principal foi definida."
        )
        self.primary_description.setObjectName("cardDescription")
        self.primary_description.setWordWrap(True)

        primary_text_layout.addWidget(primary_title)
        primary_text_layout.addWidget(
            self.primary_description
        )

        self.primary_status_label = QLabel("Não definida")
        self.primary_status_label.setObjectName(
            "statusBadgeWarning"
        )

        primary_summary_layout.addLayout(
            primary_text_layout,
            1,
        )
        primary_summary_layout.addWidget(
            self.primary_status_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        self.images_count_label = QLabel("0 imagens")
        self.images_count_label.setObjectName("imageCountCard")
        self.images_count_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.images_count_label.setMinimumWidth(180)

        summary_row.addWidget(
            self.primary_summary_card,
            1,
        )
        summary_row.addWidget(
            self.images_count_label,
            0,
        )

        content_layout.addLayout(summary_row)

        # ---------------------------------------------------------
        # IMPORTAÇÃO
        # ---------------------------------------------------------

        self.drop_area = ImageDropArea()

        self.drop_area.setMinimumHeight(185)
        self.drop_area.setMaximumHeight(185)

        self.drop_area.files_dropped.connect(
        self.import_image_paths
        )

        content_layout.addWidget(self.drop_area)

        # ---------------------------------------------------------
        # GALERIA
        # ---------------------------------------------------------

        gallery_header = SectionHeader(
            title="Galeria do processo",
            description=(
                "A ordem abaixo será usada no relatório. "
                "A imagem principal aparece destacada."
            ),
        )

        content_layout.addWidget(gallery_header)

        self.empty_card = QFrame()
        self.empty_card.setObjectName("uploadCard")

        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setContentsMargins(30, 30, 30, 30)
        empty_layout.setSpacing(8)
        empty_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        empty_title = QLabel("Nenhuma imagem adicionada")
        empty_title.setObjectName("uploadTitle")

        empty_description = QLabel(
            "Selecione arquivos ou arraste imagens para a área acima."
        )
        empty_description.setObjectName("uploadDescription")
        empty_description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_description)

        content_layout.addWidget(self.empty_card)

        self.gallery_widget = QWidget()

        self.gallery_layout = QGridLayout(
            self.gallery_widget
        )
        self.gallery_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_layout.setHorizontalSpacing(14)
        self.gallery_layout.setVerticalSpacing(14)

        content_layout.addWidget(self.gallery_widget)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(content, 12)
        row.addStretch(1)

        scroll_layout.addLayout(row)
        scroll_layout.addSpacing(16)

        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area)

    # =============================================================
    # PROJETO
    # =============================================================

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = project

        self.page_header.set_metadata(
            f"{project.report_id} · {project.name}"
        )

        self.load_images()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # =============================================================
    # SELECIONAR IMAGENS
    # =============================================================

    def select_images(
        self,
    ) -> None:
        if not self._has_valid_project():
            return

        file_paths, _ = (
            QFileDialog.getOpenFileNames(
                self,
                "Selecionar imagens",
                "",
                (
                    "Imagens (*.jpg *.jpeg *.png);;"
                    "JPEG (*.jpg *.jpeg);;"
                    "PNG (*.png)"
                ),
            )
        )

        if not file_paths:
            return

        self.import_image_paths(
            file_paths
        )

    # =============================================================
    # IMPORTAR
    # =============================================================

    def import_image_paths(
        self,
        file_paths: list[str],
    ) -> None:
        if not self._has_valid_project():
            return

        try:
            imported = (
                self.image_service
                .import_images(
                    project_id=(
                        self.current_project.id
                    ),

                    report_id=(
                        self.current_project.report_id
                    ),

                    source_paths=(
                        file_paths
                    ),
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao importar imagens",
                (
                    "Não foi possível adicionar "
                    "as imagens.\n\n"
                    f"Detalhes: {error}"
                ),
            )

            return

        self.load_images()

        if imported:
            QMessageBox.information(
                self,
                "Imagens adicionadas",
                (
                    f"{len(imported)} imagem(ns) "
                    "adicionada(s) ao processo."
                ),
            )

    # =============================================================
    # CARREGAR GALERIA
    # =============================================================

    def load_images(
        self,
    ) -> None:
        self.clear_gallery()

        if not self._has_valid_project():
            self.current_images = []

            self.empty_card.show()

            self.gallery_widget.hide()

            self.update_images_count()

            self.update_primary_summary()

            return

        try:
            self.current_images = (
                self.image_service
                .get_project_images(
                    self.current_project.id
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao carregar imagens",
                str(
                    error
                ),
            )

            self.current_images = []

        self.update_images_count()

        self.update_primary_summary()

        if not self.current_images:
            self.empty_card.show()

            self.gallery_widget.hide()

            return

        self.empty_card.hide()

        self.gallery_widget.show()

        for index, image in enumerate(
            self.current_images
        ):
            row = index // 2
            column = index % 2

            card = self.create_image_card(
                image=image,
                index=index,
                total_images=len(
                    self.current_images
                ),
            )

            self.gallery_layout.addWidget(
                card,
                row,
                column,
            )

        self.gallery_layout.setColumnStretch(
            0,
            1,
        )

        self.gallery_layout.setColumnStretch(
            1,
            1,
        )

    # =============================================================
    # CARD
    # =============================================================

    def create_image_card(
        self,
        image: ProjectImage,
        index: int,
        total_images: int,
    ) -> QFrame:
        card = QFrame()

        card.setObjectName(
            (
                "primaryImageCard"
                if image.is_primary
                else "imageCard"
            )
        )

        card.setProperty(
            "primary",
            image.is_primary,
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        layout.setSpacing(
            11
        )

        # ---------------------------------------------------------
        # TOPO DO CARD
        # ---------------------------------------------------------

        top_layout = QHBoxLayout()

        position_label = QLabel(
            f"Imagem {index + 1:02d}"
        )

        position_label.setObjectName(
            "documentOrder"
        )

        top_layout.addWidget(
            position_label
        )

        if image.is_primary:
            primary_badge = QLabel(
                "Imagem principal"
            )

            primary_badge.setObjectName(
                "statusBadgeSuccess"
            )

            top_layout.addWidget(
                primary_badge
            )

        top_layout.addStretch()

        order_buttons = QHBoxLayout()

        order_buttons.setSpacing(
            6
        )

        move_left_button = QPushButton(
            "↑"
        )

        move_left_button.setToolTip(
            "Mover imagem para cima na ordem do relatório"
        )

        move_left_button.setObjectName(
            "imageOrderButton"
        )

        order_button_style = """
        QPushButton#imageOrderButton {
            background: #FFFFFF;
            border: 1px solid #B8C9D8;
            border-radius: 7px;
            color: #075EA8;
            font-size: 18px;
            font-weight: 700;
        }
        QPushButton#imageOrderButton:hover {
            background: #F2F8FD;
            border-color: #0B78C4;
        }
        QPushButton#imageOrderButton:pressed {
            background: #E5F1FA;
        }
        QPushButton#imageOrderButton:disabled {
            background: #F4F6F8;
            border-color: #D6DEE5;
            color: #9AA8B5;
        }
        """

        move_left_button.setFixedSize(
            38,
            34,
        )

        move_left_button.setStyleSheet(order_button_style)

        move_left_button.setEnabled(
            index > 0
        )

        move_left_button.clicked.connect(
            lambda checked=False,
            selected_image=image:
            self.move_image(
                selected_image,
                -1,
            )
        )

        move_right_button = QPushButton(
            "↓"
        )

        move_right_button.setToolTip(
            "Mover imagem para baixo na ordem do relatório"
        )

        move_right_button.setObjectName(
            "imageOrderButton"
        )

        move_right_button.setFixedSize(
            38,
            34,
        )

        move_right_button.setStyleSheet(order_button_style)

        move_right_button.setEnabled(
            index
            < total_images - 1
        )

        move_right_button.clicked.connect(
            lambda checked=False,
            selected_image=image:
            self.move_image(
                selected_image,
                1,
            )
        )

        order_buttons.addWidget(
            move_left_button
        )

        order_buttons.addWidget(
            move_right_button
        )

        top_layout.addLayout(
            order_buttons
        )

        layout.addLayout(
            top_layout
        )

        # ---------------------------------------------------------
        # PREVIEW
        # ---------------------------------------------------------

        preview = QLabel()

        preview.setObjectName(
            "imagePreview"
        )

        preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        preview.setMinimumHeight(
            230
        )

        preview.setMaximumHeight(
            230
        )

        pixmap = QPixmap(
            image.file_path
        )

        if not pixmap.isNull():
            scaled = pixmap.scaled(
                500,
                220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            preview.setPixmap(
                scaled
            )

        else:
            preview.setText(
                "Imagem indisponível"
            )

        layout.addWidget(
            preview
        )

        # ---------------------------------------------------------
        # NOME
        # ---------------------------------------------------------

        file_name = QLabel(
            image.file_name
        )

        file_name.setObjectName(
            "cardTitle"
        )

        file_name.setWordWrap(
            True
        )

        layout.addWidget(
            file_name
        )

        # ---------------------------------------------------------
        # SELEÇÃO PRINCIPAL
        # ---------------------------------------------------------

        primary_frame = QFrame()

        primary_frame.setObjectName(
            "primaryImageOption"
        )

        primary_layout = QVBoxLayout(
            primary_frame
        )

        primary_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        primary_layout.setSpacing(
            4
        )

        primary_checkbox = QCheckBox(
            "Usar como imagem principal da peça/lote"
        )

        primary_checkbox.setChecked(
            image.is_primary
        )

        primary_checkbox.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        primary_checkbox.toggled.connect(
            lambda checked,
            selected_image=image:
            self.change_primary_image(
                selected_image,
                checked,
            )
        )

        primary_help = QLabel(
            (
                "Esta imagem será utilizada na primeira página "
                "do relatório técnico consolidado."
            )
        )

        primary_help.setObjectName(
            "cardDescription"
        )

        primary_help.setWordWrap(
            True
        )

        primary_layout.addWidget(
            primary_checkbox
        )

        primary_layout.addWidget(
            primary_help
        )

        layout.addWidget(
            primary_frame
        )

        # ---------------------------------------------------------
        # TIPO
        # ---------------------------------------------------------

        type_label = QLabel(
            "Tipo de imagem"
        )

        type_label.setObjectName(
            "dataLabel"
        )

        type_input = QComboBox()

        type_input.addItems(
            self.IMAGE_TYPES
        )

        current_type = (
            image.image_type
            or "Fotografia"
        )

        if (
            current_type
            not in self.IMAGE_TYPES
        ):
            type_input.addItem(
                current_type
            )

        type_input.setCurrentText(
            current_type
        )

        type_input.setMinimumHeight(
            40
        )

        layout.addWidget(
            type_label
        )

        layout.addWidget(
            type_input
        )

        # ---------------------------------------------------------
        # LEGENDA
        # ---------------------------------------------------------

        caption_label = QLabel(
            "Legenda no relatório (opcional)"
        )

        caption_label.setObjectName(
            "dataLabel"
        )

        caption_help = QLabel(
            (
                "Este texto será exibido abaixo da imagem no PDF. "
                "Se ficar vazio, a imagem será mostrada sem legenda."
            )
        )

        caption_help.setObjectName(
            "cardDescription"
        )

        caption_help.setWordWrap(
            True
        )

        caption_input = QTextEdit()

        caption_input.setPlaceholderText(
            (
                "Ex.: Peça posicionada na ZEISS PRISMO "
                "durante a medição dimensional."
            )
        )

        caption_input.setPlainText(
            image.caption
            or ""
        )

        caption_input.setMinimumHeight(
            72
        )

        caption_input.setMaximumHeight(
            88
        )

        caption_preview = QLabel()

        caption_preview.setObjectName(
            "cardDescription"
        )

        caption_preview.setWordWrap(
            True
        )

        caption_preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        def update_caption_preview() -> None:
            value = " ".join(
                caption_input
                .toPlainText()
                .split()
            )

            if value:
                caption_preview.setText(
                    f"Prévia da legenda: {value}"
                )
            else:
                caption_preview.setText(
                    "Sem legenda no relatório."
                )

        caption_input.textChanged.connect(
            update_caption_preview
        )

        update_caption_preview()

        layout.addWidget(
            caption_label
        )

        layout.addWidget(
            caption_help
        )

        layout.addWidget(
            caption_input
        )

        layout.addWidget(
            caption_preview
        )

        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        actions = QHBoxLayout()

        actions.setSpacing(
            6
        )

        save_button = QPushButton(
            "Salvar tipo e legenda"
        )

        save_button.setObjectName(
            "saveImageMetadataButton"
        )

        save_button.setFixedSize(
            210,
            40,
        )

        save_button.setStyleSheet(
            """
            QPushButton#saveImageMetadataButton {
                background: #FFFFFF;
                border: 1px solid #AFC6D9;
                border-radius: 7px;
                color: #073B66;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton#saveImageMetadataButton:hover {
                background: #F3F8FC;
                border-color: #6E9EC2;
            }

            QPushButton#saveImageMetadataButton:pressed {
                background: #E8F2F9;
            }
            """
        )

        save_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        save_button.clicked.connect(
            lambda checked=False,
            selected_image=image,
            selected_type=type_input,
            selected_caption=caption_input:
            self.save_image_metadata(
                selected_image,
                selected_type,
                selected_caption,
            )
        )

        edit_button = QPushButton(
            "Editar marcações"
        )

        edit_button.setObjectName(
            "editImageMarksButton"
        )

        edit_button.setFixedSize(
            145,
            40,
        )

        edit_button.setStyleSheet(
            """
            QPushButton#editImageMarksButton {
                background: #0B78C8;
                border: 1px solid #0B78C8;
                border-radius: 7px;
                color: #FFFFFF;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton#editImageMarksButton:hover {
                background: #086DB6;
                border-color: #086DB6;
            }

            QPushButton#editImageMarksButton:pressed {
                background: #075F9E;
                border-color: #075F9E;
            }
            """
        )

        edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        edit_button.clicked.connect(
            lambda checked=False,
            selected_image=image:
            self.edit_image_requested.emit(
                selected_image
            )
        )

        delete_button = QPushButton(
            "Excluir"
        )

        delete_button.setObjectName(
            "deleteImageButton"
        )

        delete_button.setFixedSize(
            90,
            40,
        )

        delete_button.setStyleSheet(
            """
            QPushButton#deleteImageButton {
                background: #FFFFFF;
                border: 1px solid #D9A3A3;
                border-radius: 7px;
                color: #A51D1D;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton#deleteImageButton:hover {
                background: #FFF4F4;
                border-color: #C94C4C;
            }

            QPushButton#deleteImageButton:pressed {
                background: #FDE7E7;
            }
            """
        )

        delete_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        delete_button.clicked.connect(
            lambda checked=False,
            selected_image=image:
            self.delete_image(
                selected_image
            )
        )

        actions.addWidget(
            save_button
        )

        actions.addWidget(
            edit_button
        )

        actions.addWidget(
            delete_button
        )

        actions.addStretch()

        layout.addLayout(
            actions
        )

        return card

    # =============================================================
    # IMAGEM PRINCIPAL
    # =============================================================

    def change_primary_image(
        self,
        image: ProjectImage,
        checked: bool,
    ) -> None:
        if (
            image.id is None
            or not self._has_valid_project()
        ):
            return

        try:
            if checked:
                self.image_service.set_primary_image(
                    project_id=(
                        self.current_project.id
                    ),
                    image_id=image.id,
                )

            elif image.is_primary:
                self.image_service.clear_primary_image(
                    self.current_project.id
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao definir imagem principal",
                (
                    "Não foi possível alterar a imagem "
                    "principal da peça ou do lote.\n\n"
                    f"Detalhes: {error}"
                ),
            )

            self.load_images()

            return

        self.load_images()

    def update_primary_summary(
        self,
    ) -> None:
        primary_image = next(
            (
                image
                for image in self.current_images
                if image.is_primary
            ),
            None,
        )

        if primary_image is None:
            self.primary_description.setText(
                (
                    "Nenhuma imagem principal foi definida. "
                    "Escolha uma imagem da galeria para representar "
                    "a peça ou o lote na primeira página."
                )
            )

            self.primary_status_label.setText(
                "Não definida"
            )

            self.primary_status_label.setObjectName(
                "statusBadgeWarning"
            )

        else:
            description = (
                primary_image.caption
                or primary_image.file_name
                or "Imagem principal selecionada"
            )

            self.primary_description.setText(
                (
                    f"{description}\n"
                    "Esta imagem será utilizada na visão geral "
                    "do relatório técnico."
                )
            )

            self.primary_status_label.setText(
                "Definida"
            )

            self.primary_status_label.setObjectName(
                "statusBadgeSuccess"
            )

        self.primary_status_label.style().unpolish(
            self.primary_status_label
        )

        self.primary_status_label.style().polish(
            self.primary_status_label
        )

    # =============================================================
    # SALVAR METADADOS
    # =============================================================

    def save_image_metadata(
        self,
        image: ProjectImage,
        type_input: QComboBox,
        caption_input: QTextEdit,
    ) -> None:
        if image.id is None:
            return

        try:
            updated_image = (
                self.image_service
                .update_image(
                    image_id=image.id,

                    image_type=(
                        type_input.currentText()
                    ),

                    caption=(
                        caption_input.toPlainText()
                    ),
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar imagem",
                (
                    "Não foi possível salvar "
                    "as informações.\n\n"
                    f"Detalhes: {error}"
                ),
            )

            return

        image.image_type = (
            updated_image.image_type
        )

        image.caption = (
            updated_image.caption
        )

        QMessageBox.information(
            self,
            "Imagem atualizada",
            (
                "O tipo e a legenda da imagem foram salvos. "
                "A legenda será usada abaixo da foto no relatório."
            ),
        )

        self.load_images()

    # =============================================================
    # MOVER
    # =============================================================

    def move_image(
        self,
        image: ProjectImage,
        direction: int,
    ) -> None:
        if (
            image.id is None
            or self.current_project is None
            or self.current_project.id is None
        ):
            return

        try:
            self.image_service.move_image(
                project_id=(
                    self.current_project.id
                ),

                image_id=image.id,

                direction=direction,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao ordenar imagens",
                str(
                    error
                ),
            )

            return

        self.load_images()

    # =============================================================
    # EXCLUIR
    # =============================================================

    def delete_image(
        self,
        image: ProjectImage,
    ) -> None:
        if image.id is None:
            return

        message = (
            "Deseja realmente excluir esta imagem "
            "e todas as marcações associadas?"
        )

        if image.is_primary:
            message += (
                "\n\nEsta é a imagem principal da peça/lote. "
                "Após a exclusão, outra imagem deverá ser escolhida."
            )

        result = QMessageBox.question(
            self,
            "Excluir imagem",
            message,
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if (
            result
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            self.image_service.delete_image(
                image
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao excluir imagem",
                str(
                    error
                ),
            )

            return

        self.load_images()

    # =============================================================
    # CONTADOR
    # =============================================================

    def update_images_count(
        self,
    ) -> None:
        count = len(
            self.current_images
        )

        primary_count = sum(
            1
            for image in self.current_images
            if image.is_primary
        )

        if count == 1:
            text = "1 imagem"

        else:
            text = (
                f"{count} imagens"
            )

        if primary_count:
            text += (
                " · imagem principal definida"
            )

        self.images_count_label.setText(
            text
        )

    # =============================================================
    # HELPERS
    # =============================================================

    def _has_valid_project(
        self,
    ) -> bool:
        return (
            self.current_project
            is not None
            and self.current_project.id
            is not None
        )

    def clear_gallery(
        self,
    ) -> None:
        while (
            self.gallery_layout.count()
        ):
            item = (
                self.gallery_layout
                .takeAt(
                    0
                )
            )

            widget = item.widget()

            child_layout = item.layout()

            if widget is not None:
                widget.setParent(
                    None
                )

                widget.deleteLater()

            elif child_layout is not None:
                self._clear_child_layout(
                    child_layout
                )

    def _clear_child_layout(
        self,
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(
                0
            )

            widget = item.widget()

            child_layout = item.layout()

            if widget is not None:
                widget.setParent(
                    None
                )

                widget.deleteLater()

            elif child_layout is not None:
                self._clear_child_layout(
                    child_layout
                )