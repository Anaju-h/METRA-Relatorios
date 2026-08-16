from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.components.page_header import (
    PageHeader,
)
from ui.components.step_indicator import (
    StepIndicator,
)
from ui.pages.new_project.pdf_drop_area import (
    PDFDropArea,
)


class ProjectDocumentsStep(QWidget):
    """
    Segunda etapa da criação do processo.

    Responsável por:
    - selecionar relatórios PDF;
    - organizar a lista de documentos;
    - solicitar a análise automática;
    - deixar o METRA identificar peça única ou lote
      a partir dos dados extraídos.
    """

    back_requested = Signal()
    cancel_requested = Signal()

    # O segundo argumento permanece string por compatibilidade
    # com o controlador atual. Uma string vazia significa:
    # "detectar automaticamente".
    analyze_requested = Signal(
        list,
        str,
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(
            parent
        )

        self.selected_paths: list[str] = []

        self.setObjectName(
            "pageBackground"
        )

        self._build_ui()
        self.refresh_documents_list()

    # =============================================================
    # INTERFACE
    # =============================================================

    def _build_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(
            True
        )
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setObjectName(
            "pageBackground"
        )

        layout = QVBoxLayout(
            scroll_content
        )
        layout.setContentsMargins(
            34,
            22,
            34,
            34,
        )
        layout.setSpacing(
            18
        )

        self.page_header = PageHeader(
            title="Relatórios do processo",
            subtitle=(
                "Adicione os relatórios que serão analisados. "
                "O METRA identificará automaticamente se os "
                "documentos representam uma peça única ou um lote."
            ),
            back_text="← Alterar forma de início",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        layout.addWidget(
            self.page_header
        )

        self.step_indicator = StepIndicator(
            [
                "Documentos",
                "Revisão",
                "Criar",
            ],
            current_step=0,
        )

        layout.addWidget(
            self.step_indicator
        )

        # ---------------------------------------------------------
        # INFORMAÇÃO SOBRE A ANÁLISE AUTOMÁTICA
        # ---------------------------------------------------------

        analysis_card = QFrame()
        analysis_card.setObjectName(
            "formCard"
        )

        analysis_layout = QVBoxLayout(
            analysis_card
        )
        analysis_layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        analysis_layout.setSpacing(
            8
        )

        analysis_title = QLabel(
            "Identificação automática do processo"
        )
        analysis_title.setObjectName(
            "formSectionTitle"
        )

        analysis_description = QLabel(
            (
                "Após a análise, o METRA compara as peças, "
                "identificadores das unidades, equipamentos e "
                "demais informações dos relatórios para sugerir "
                "o modo correto de análise e o template."
            )
        )
        analysis_description.setObjectName(
            "formSectionDescription"
        )
        analysis_description.setWordWrap(
            True
        )

        analysis_layout.addWidget(
            analysis_title
        )
        analysis_layout.addWidget(
            analysis_description
        )

        layout.addWidget(
            analysis_card
        )

        # ---------------------------------------------------------
        # ÁREA DE IMPORTAÇÃO
        # ---------------------------------------------------------

        self.drop_area = PDFDropArea()

        self.drop_area.files_dropped.connect(
            self.add_selected_files
        )

        self.drop_area.select_requested.connect(
            self.open_file_dialog
        )

        layout.addWidget(
            self.drop_area
        )

        layout.addWidget(
            self._build_documents_card()
        )

        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(
            10
        )
        actions.addStretch()

        cancel_button = QPushButton(
            "Cancelar"
        )
        cancel_button.setObjectName(
            "secondaryButton"
        )
        cancel_button.setMinimumHeight(
            44
        )
        cancel_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        cancel_button.clicked.connect(
            self.cancel_requested.emit
        )

        self.analyze_button = QPushButton(
            "Analisar documentos"
        )
        self.analyze_button.setObjectName(
            "primaryButton"
        )
        self.analyze_button.setMinimumHeight(
            44
        )
        self.analyze_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.analyze_button.clicked.connect(
            self._emit_analysis_request
        )

        actions.addWidget(
            cancel_button
        )
        actions.addWidget(
            self.analyze_button
        )

        layout.addLayout(
            actions
        )
        layout.addStretch()

        scroll_area.setWidget(
            scroll_content
        )

        root_layout.addWidget(
            scroll_area
        )

    def _build_documents_card(
        self,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName(
            "formCard"
        )

        layout = QVBoxLayout(
            card
        )
        layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        layout.setSpacing(
            14
        )

        header = QHBoxLayout()

        title = QLabel(
            "Arquivos adicionados"
        )
        title.setObjectName(
            "formSectionTitle"
        )

        self.documents_count_label = QLabel(
            "0 arquivos"
        )
        self.documents_count_label.setObjectName(
            "formSectionDescription"
        )

        add_button = QPushButton(
            "+ Adicionar"
        )
        add_button.setObjectName(
            "secondaryButton"
        )
        add_button.setMinimumHeight(
            42
        )
        add_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        add_button.clicked.connect(
            self.open_file_dialog
        )

        header.addWidget(
            title
        )
        header.addWidget(
            self.documents_count_label
        )
        header.addStretch()
        header.addWidget(
            add_button
        )

        layout.addLayout(
            header
        )

        self.documents_container = QWidget()

        self.documents_layout = QVBoxLayout(
            self.documents_container
        )
        self.documents_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.documents_layout.setSpacing(
            10
        )

        layout.addWidget(
            self.documents_container
        )

        return card

    # =============================================================
    # ARQUIVOS
    # =============================================================

    def open_file_dialog(
        self,
    ) -> None:
        file_paths, _ = (
            QFileDialog.getOpenFileNames(
                self,
                "Selecionar relatórios",
                "",
                "Arquivos PDF (*.pdf)",
            )
        )

        if file_paths:
            self.add_selected_files(
                file_paths
            )

    def add_selected_files(
        self,
        file_paths: list[str],
    ) -> None:
        existing_keys = {
            str(
                Path(path).resolve()
            ).lower()
            for path in self.selected_paths
        }

        added = 0

        for file_path in file_paths:
            path = Path(
                file_path
            )

            if (
                not path.is_file()
                or path.suffix.lower()
                != ".pdf"
            ):
                continue

            key = str(
                path.resolve()
            ).lower()

            if key in existing_keys:
                continue

            self.selected_paths.append(
                str(path)
            )

            existing_keys.add(
                key
            )

            added += 1

        if (
            added == 0
            and file_paths
        ):
            QMessageBox.information(
                self,
                "Nenhum arquivo adicionado",
                (
                    "Os arquivos selecionados já estavam "
                    "na lista ou não eram PDFs válidos."
                ),
            )

        self.refresh_documents_list()

    def remove_selected_file(
        self,
        file_path: str,
    ) -> None:
        self.selected_paths = [
            path
            for path in self.selected_paths
            if path != file_path
        ]

        self.refresh_documents_list()

    def refresh_documents_list(
        self,
    ) -> None:
        self._clear_layout(
            self.documents_layout
        )

        total = len(
            self.selected_paths
        )

        if total == 0:
            empty_label = QLabel(
                "Nenhum arquivo adicionado.\n"
                "Arraste os relatórios para a área acima "
                "ou clique em Selecionar arquivos."
            )
            empty_label.setObjectName(
                "emptyState"
            )
            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            empty_label.setWordWrap(
                True
            )

            self.documents_layout.addWidget(
                empty_label
            )

        else:
            for index, file_path in enumerate(
                self.selected_paths,
                start=1,
            ):
                self.documents_layout.addWidget(
                    self._create_file_card(
                        index=index,
                        file_path=file_path,
                    )
                )

        self.documents_count_label.setText(
            (
                f"{total} arquivo"
                if total == 1
                else f"{total} arquivos"
            )
        )

        self.analyze_button.setEnabled(
            total > 0
        )

    def _create_file_card(
        self,
        *,
        index: int,
        file_path: str,
    ) -> QFrame:
        path = Path(
            file_path
        )

        card = QFrame()
        card.setObjectName(
            "documentListCard"
        )

        layout = QHBoxLayout(
            card
        )
        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )
        layout.setSpacing(
            14
        )

        order = QLabel(
            f"{index:02d}"
        )
        order.setObjectName(
            "documentOrder"
        )

        info = QVBoxLayout()
        info.setSpacing(
            3
        )

        name = QLabel(
            path.name
        )
        name.setObjectName(
            "cardTitle"
        )
        name.setWordWrap(
            True
        )

        try:
            size_mb = (
                path.stat().st_size
                / 1024
                / 1024
            )
            metadata_text = (
                f"PDF · {size_mb:.2f} MB"
            )

        except OSError:
            metadata_text = "PDF"

        metadata = QLabel(
            metadata_text
        )
        metadata.setObjectName(
            "cardDescription"
        )

        info.addWidget(
            name
        )
        info.addWidget(
            metadata
        )

        remove_button = QPushButton(
            "Remover"
        )
        remove_button.setObjectName(
            "cardButton"
        )
        remove_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        remove_button.clicked.connect(
            (
                lambda checked=False,
                selected_path=file_path:
                self.remove_selected_file(
                    selected_path
                )
            )
        )

        layout.addWidget(
            order
        )
        layout.addLayout(
            info,
            1,
        )
        layout.addWidget(
            remove_button
        )

        return card

    # =============================================================
    # CONTROLE
    # =============================================================

    def set_analyzing(
        self,
        analyzing: bool,
    ) -> None:
        self.analyze_button.setEnabled(
            (
                not analyzing
                and bool(
                    self.selected_paths
                )
            )
        )

        self.analyze_button.setText(
            (
                "Analisando..."
                if analyzing
                else "Analisar documentos"
            )
        )

    def reset_step(
        self,
    ) -> None:
        self.selected_paths = []

        self.refresh_documents_list()

    def _emit_analysis_request(
        self,
    ) -> None:
        if not self.selected_paths:
            QMessageBox.warning(
                self,
                "Nenhum relatório",
                "Adicione ao menos um relatório PDF.",
            )
            return

        # String vazia = modo automático.
        # O BatchAnalysisService decidirá entre peça única e lote
        # depois de analisar os documentos.
        self.analyze_requested.emit(
            list(
                self.selected_paths
            ),
            "",
        )

    def _clear_layout(
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
                widget.deleteLater()

            elif child_layout is not None:
                self._clear_layout(
                    child_layout
                )