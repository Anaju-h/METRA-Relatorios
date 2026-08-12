from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import uuid

from PySide6.QtCore import (
    QPointF,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPolygonF,
)

from models.project_image import ProjectImage
from repositories.image_repository import (
    ImageRepository,
)
from services.annotation_service import (
    AnnotationService,
)
from services.traceability_service import (
    TraceabilityService,
)


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"


class ImageService:
    """
    Serviço responsável pelas imagens técnicas do processo.

    Funcionalidades:

    - importar imagens;
    - consultar imagens do processo;
    - editar tipo e legenda;
    - alterar ordem;
    - definir imagem principal da peça ou lote;
    - excluir imagens;
    - localizar a imagem principal do relatório;
    - preparar imagens para relatórios com as marcações aplicadas.

    As imagens originais nunca são alteradas. Para o relatório,
    quando uma imagem possui marcações, é gerada uma cópia temporária
    com as anotações desenhadas sobre a imagem original.
    """

    ALLOWED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    IMAGE_TYPES = {
        "Fotografia",
        "Imagem principal da peça/lote",
        "Setup de medição",
        "Fixação",
        "CAD",
        "Render",
        "Detalhe técnico",
        "Evidência de não conformidade",
        "Outro",
    }

    DEFAULT_ANNOTATION_COLOR = "#EB2323"

    def __init__(self):
        self.repository = (
            ImageRepository()
        )

        self.annotation_service = (
            AnnotationService()
        )

        self.traceability_service = (
            TraceabilityService()
        )

    # =============================================================
    # IMPORTAÇÃO
    # =============================================================

    def import_images(
        self,
        project_id: int,
        report_id: str,
        source_paths: list[str],
    ) -> list[ProjectImage]:
        if project_id is None:
            raise ValueError(
                "Processo inválido."
            )

        if not report_id:
            raise ValueError(
                (
                    "O processo não possui uma "
                    "identificação válida."
                )
            )

        images_dir = (
            PROJECTS_DIR
            / report_id
            / "images"
        )

        images_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        imported_images: list[
            ProjectImage
        ] = []

        next_position = (
            self.repository
            .get_next_position(
                project_id
            )
        )

        for source_path in source_paths:
            source = Path(
                source_path
            )

            if not source.exists():
                continue

            if not source.is_file():
                continue

            extension = (
                source.suffix.lower()
            )

            if (
                extension
                not in self.ALLOWED_EXTENSIONS
            ):
                continue

            unique_name = (
                f"{uuid.uuid4().hex}"
                f"{extension}"
            )

            destination = (
                images_dir
                / unique_name
            )

            shutil.copy2(
                source,
                destination,
            )

            now = (
                datetime.now()
                .isoformat(
                    timespec="seconds"
                )
            )

            image = ProjectImage(
                project_id=project_id,

                file_path=str(
                    destination
                ),

                file_name=source.name,

                image_type="Fotografia",

                caption=None,

                position=next_position,

                is_primary=False,

                created_at=now,

                updated_at=now,
            )

            image = (
                self.repository
                .create(
                    image
                )
            )

            imported_images.append(
                image
            )

            next_position += 1

        if imported_images:
            self._invalidate_project_approval(
                project_id=project_id,
                reason=(
                    "Novas imagens técnicas foram "
                    "adicionadas ao processo."
                ),
            )

        return imported_images

    # =============================================================
    # CONSULTA
    # =============================================================

    def get_project_images(
        self,
        project_id: int,
    ) -> list[ProjectImage]:
        if project_id is None:
            return []

        return (
            self.repository
            .find_by_project_id(
                project_id
            )
        )

    def get_image(
        self,
        image_id: int,
    ) -> ProjectImage | None:
        if image_id is None:
            return None

        return (
            self.repository
            .find_by_id(
                image_id
            )
        )

    def get_primary_image(
        self,
        project_id: int,
    ) -> ProjectImage | None:
        """
        Retorna a imagem escolhida para a visão geral da peça/lote.
        """

        if project_id is None:
            return None

        return (
            self.repository
            .find_primary_by_project_id(
                project_id
            )
        )

    # =============================================================
    # IMAGEM PARA RELATÓRIO
    # =============================================================

    def prepare_report_image(
        self,
        image: ProjectImage,
        output_directory: str | Path,
    ) -> Path | None:
        """
        Retorna o caminho da imagem que deve ser usada no relatório.

        Se a imagem não possui marcações, retorna o próprio arquivo
        original.

        Se possui marcações, cria uma cópia PNG temporária com todas
        as anotações aplicadas, preservando o arquivo original.
        """

        source_path = Path(
            str(
                image.file_path
                or ""
            )
        )

        if (
            not source_path.exists()
            or not source_path.is_file()
        ):
            return None

        if image.id is None:
            return source_path

        annotations = (
            self.annotation_service
            .get_annotations(
                image.id
            )
        )

        if not annotations:
            return source_path

        image_data = QImage(
            str(
                source_path
            )
        )

        if image_data.isNull():
            return source_path

        destination_directory = Path(
            output_directory
        )

        destination_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            destination_directory
            / (
                f"report_image_{image.id}_annotated.png"
            )
        )

        painter = QPainter(
            image_data
        )

        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing,
                True,
            )

            painter.setRenderHint(
                QPainter.RenderHint.TextAntialiasing,
                True,
            )

            for annotation in annotations:
                self._draw_annotation(
                    painter=painter,
                    annotation=annotation,
                )

        finally:
            painter.end()

        saved = image_data.save(
            str(
                destination
            ),
            "PNG",
        )

        if not saved:
            return source_path

        return destination

    def prepare_report_images(
        self,
        images: list[ProjectImage],
        output_directory: str | Path,
    ) -> dict[int, Path]:
        """
        Prepara várias imagens de uma vez para uso no relatório.

        O retorno é indexado pelo id da imagem.
        """

        prepared: dict[
            int,
            Path,
        ] = {}

        for image in images:
            if image.id is None:
                continue

            path = self.prepare_report_image(
                image=image,
                output_directory=output_directory,
            )

            if path is not None:
                prepared[
                    image.id
                ] = path

        return prepared

    # =============================================================
    # DESENHO DAS MARCAÇÕES
    # =============================================================

    def _draw_annotation(
        self,
        *,
        painter: QPainter,
        annotation,
    ) -> None:
        annotation_type = str(
            annotation.annotation_type
            or ""
        ).strip().lower()

        color = self._annotation_color(
            getattr(
                annotation,
                "color",
                None,
            )
        )

        stroke_width = max(
            1.0,
            float(
                getattr(
                    annotation,
                    "stroke_width",
                    3.0,
                )
                or 3.0
            ),
        )

        if annotation_type in {
            "rectangle",
            "circle",
            "line",
            "arrow",
        }:
            pen = QPen(
                color
            )

            pen.setWidthF(
                stroke_width
            )

            pen.setCapStyle(
                Qt.PenCapStyle.RoundCap
            )

            pen.setJoinStyle(
                Qt.PenJoinStyle.RoundJoin
            )

            painter.setPen(
                pen
            )

            painter.setBrush(
                Qt.BrushStyle.NoBrush
            )

        if annotation_type == "rectangle":
            painter.drawRect(
                QRectF(
                    float(
                        annotation.x
                    ),
                    float(
                        annotation.y
                    ),
                    float(
                        annotation.width
                    ),
                    float(
                        annotation.height
                    ),
                )
            )

            return

        if annotation_type == "circle":
            painter.drawEllipse(
                QRectF(
                    float(
                        annotation.x
                    ),
                    float(
                        annotation.y
                    ),
                    float(
                        annotation.width
                    ),
                    float(
                        annotation.height
                    ),
                )
            )

            return

        if annotation_type == "line":
            if (
                annotation.end_x is None
                or annotation.end_y is None
            ):
                return

            painter.drawLine(
                QPointF(
                    float(
                        annotation.x
                    ),
                    float(
                        annotation.y
                    ),
                ),
                QPointF(
                    float(
                        annotation.end_x
                    ),
                    float(
                        annotation.end_y
                    ),
                ),
            )

            return

        if annotation_type == "arrow":
            if (
                annotation.end_x is None
                or annotation.end_y is None
            ):
                return

            self._draw_arrow(
                painter=painter,
                start=QPointF(
                    float(
                        annotation.x
                    ),
                    float(
                        annotation.y
                    ),
                ),
                end=QPointF(
                    float(
                        annotation.end_x
                    ),
                    float(
                        annotation.end_y
                    ),
                ),
                color=color,
                stroke_width=stroke_width,
            )

            return

        if annotation_type in {
            "text",
            "marker",
        }:
            content = (
                annotation.text
                if annotation_type
                == "text"
                else annotation.marker_text
            )

            content = str(
                content
                or (
                    "Texto"
                    if annotation_type
                    == "text"
                    else "01"
                )
            )

            font_size = max(
                8,
                int(
                    getattr(
                        annotation,
                        "font_size",
                        18,
                    )
                    or 18
                ),
            )

            font = QFont()

            font.setPointSize(
                font_size
            )

            font.setBold(
                annotation_type
                == "marker"
            )

            painter.setFont(
                font
            )

            painter.setPen(
                color
            )

            painter.drawText(
                QPointF(
                    float(
                        annotation.x
                    ),
                    float(
                        annotation.y
                    )
                    + painter.fontMetrics().ascent(),
                ),
                content,
            )

    def _draw_arrow(
        self,
        *,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        color: QColor,
        stroke_width: float,
    ) -> None:
        dx = (
            end.x()
            - start.x()
        )

        dy = (
            end.y()
            - start.y()
        )

        length = (
            dx * dx
            + dy * dy
        ) ** 0.5

        if length <= 0:
            return

        head_length = max(
            14.0,
            min(
                30.0,
                stroke_width * 5.5,
            ),
        )

        head_half_width = max(
            6.0,
            min(
                17.0,
                stroke_width * 2.8,
            ),
        )

        direction_x = (
            dx / length
        )

        direction_y = (
            dy / length
        )

        perpendicular_x = (
            -direction_y
        )

        perpendicular_y = (
            direction_x
        )

        base_center = QPointF(
            end.x()
            - direction_x
            * head_length,
            end.y()
            - direction_y
            * head_length,
        )

        left = QPointF(
            base_center.x()
            + perpendicular_x
            * head_half_width,
            base_center.y()
            + perpendicular_y
            * head_half_width,
        )

        right = QPointF(
            base_center.x()
            - perpendicular_x
            * head_half_width,
            base_center.y()
            - perpendicular_y
            * head_half_width,
        )

        pen = QPen(
            color
        )

        pen.setWidthF(
            stroke_width
        )

        pen.setCapStyle(
            Qt.PenCapStyle.RoundCap
        )

        pen.setJoinStyle(
            Qt.PenJoinStyle.RoundJoin
        )

        painter.setPen(
            pen
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.drawLine(
            start,
            base_center,
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            color
        )

        painter.drawPolygon(
            QPolygonF(
                [
                    end,
                    left,
                    right,
                ]
            )
        )

    def _annotation_color(
        self,
        value,
    ) -> QColor:
        color = QColor(
            str(
                value
                or self.DEFAULT_ANNOTATION_COLOR
            )
        )

        if not color.isValid():
            color = QColor(
                self.DEFAULT_ANNOTATION_COLOR
            )

        return color

    # =============================================================
    # METADADOS
    # =============================================================

    def update_image(
        self,
        image_id: int,
        image_type: str,
        caption: str,
    ) -> ProjectImage:
        image = (
            self.repository
            .find_by_id(
                image_id
            )
        )

        if image is None:
            raise ValueError(
                "A imagem selecionada não foi encontrada."
            )

        normalized_type = str(
            image_type
            or ""
        ).strip()

        if not normalized_type:
            normalized_type = (
                "Fotografia"
            )

        if (
            normalized_type
            not in self.IMAGE_TYPES
        ):
            normalized_type = (
                "Outro"
            )

        normalized_caption = (
            str(
                caption
                or ""
            ).strip()
            or None
        )

        changed = (
            image.image_type != normalized_type
            or image.caption != normalized_caption
        )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        self.repository.update_metadata(
            image_id=image_id,
            image_type=normalized_type,
            caption=normalized_caption,
            updated_at=now,
        )

        image.image_type = (
            normalized_type
        )

        image.caption = (
            normalized_caption
        )

        image.updated_at = now

        if changed:
            self._invalidate_project_approval(
                project_id=image.project_id,
                reason=(
                    "Os metadados de uma imagem técnica "
                    "foram alterados."
                ),
            )

        return image

    # =============================================================
    # IMAGEM PRINCIPAL
    # =============================================================

    def set_primary_image(
        self,
        project_id: int,
        image_id: int,
    ) -> ProjectImage:
        """
        Define a imagem usada na primeira página do relatório.

        Apenas uma imagem pode permanecer como principal.
        """

        if project_id is None:
            raise ValueError(
                "Processo inválido."
            )

        if image_id is None:
            raise ValueError(
                "Imagem inválida."
            )

        image = (
            self.repository
            .find_by_id(
                image_id
            )
        )

        if image is None:
            raise ValueError(
                "A imagem selecionada não foi encontrada."
            )

        if (
            image.project_id
            != project_id
        ):
            raise ValueError(
                (
                    "A imagem selecionada não pertence "
                    "ao processo atual."
                )
            )

        current_primary = (
            self.repository
            .find_primary_by_project_id(
                project_id
            )
        )

        primary_changed = (
            current_primary is None
            or current_primary.id != image_id
        )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        self.repository.set_primary(
            project_id=project_id,
            image_id=image_id,
            updated_at=now,
        )

        image.is_primary = True
        image.updated_at = now

        if primary_changed:
            self._invalidate_project_approval(
                project_id=project_id,
                reason=(
                    "A imagem principal da peça ou lote "
                    "foi alterada."
                ),
            )

        return image

    def clear_primary_image(
        self,
        project_id: int,
    ) -> None:
        if project_id is None:
            return

        had_primary = (
            self.repository
            .find_primary_by_project_id(
                project_id
            )
            is not None
        )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        self.repository.clear_primary(
            project_id=project_id,
            updated_at=now,
        )

        if had_primary:
            self._invalidate_project_approval(
                project_id=project_id,
                reason=(
                    "A imagem principal da peça ou lote "
                    "foi removida."
                ),
            )

    # =============================================================
    # ORDENAÇÃO
    # =============================================================

    def reorder_images(
        self,
        project_id: int,
        ordered_image_ids: list[int],
    ) -> list[ProjectImage]:
        if project_id is None:
            raise ValueError(
                "Processo inválido."
            )

        images = (
            self.repository
            .find_by_project_id(
                project_id
            )
        )

        image_map = {
            image.id: image
            for image in images
            if image.id is not None
        }

        ordered_images: list[
            ProjectImage
        ] = []

        included_ids: set[int] = set()

        for image_id in ordered_image_ids:
            image = image_map.get(
                image_id
            )

            if image is None:
                continue

            ordered_images.append(
                image
            )

            included_ids.add(
                image_id
            )

        remaining_images = [
            image
            for image in images
            if (
                image.id is not None
                and image.id
                not in included_ids
            )
        ]

        remaining_images.sort(
            key=lambda image: (
                image.position,
                image.id or 0,
            )
        )

        ordered_images.extend(
            remaining_images
        )

        previous_order = [
            image.id
            for image in sorted(
                images,
                key=lambda image: (
                    image.position,
                    image.id or 0,
                ),
            )
        ]

        new_order = [
            image.id
            for image in ordered_images
        ]

        self.repository.update_positions(
            ordered_images
        )

        if previous_order != new_order:
            self._invalidate_project_approval(
                project_id=project_id,
                reason=(
                    "A ordem das imagens técnicas "
                    "foi alterada."
                ),
            )

        return ordered_images

    def move_image(
        self,
        project_id: int,
        image_id: int,
        direction: int,
    ) -> list[ProjectImage]:
        """
        Move uma imagem uma posição.

        direction:
            -1 = esquerda / acima
             1 = direita / abaixo
        """

        images = (
            self.repository
            .find_by_project_id(
                project_id
            )
        )

        images.sort(
            key=lambda image: (
                image.position,
                image.id or 0,
            )
        )

        current_index = next(
            (
                index
                for index, image
                in enumerate(
                    images
                )
                if image.id == image_id
            ),
            None,
        )

        if current_index is None:
            return images

        target_index = (
            current_index
            + direction
        )

        if (
            target_index < 0
            or target_index
            >= len(
                images
            )
        ):
            return images

        images[
            current_index
        ], images[
            target_index
        ] = (
            images[
                target_index
            ],
            images[
                current_index
            ],
        )

        self.repository.update_positions(
            images
        )

        self._invalidate_project_approval(
            project_id=project_id,
            reason=(
                "A ordem das imagens técnicas "
                "foi alterada."
            ),
        )

        return images

    # =============================================================
    # EXCLUSÃO
    # =============================================================

    def delete_image(
        self,
        image: ProjectImage,
    ) -> None:
        if image.id is None:
            return

        file_path = Path(
            image.file_path
        )

        self.repository.delete(
            image.id
        )

        self._invalidate_project_approval(
            project_id=image.project_id,
            reason=(
                "Uma imagem técnica foi removida "
                "do processo."
            ),
        )

        if file_path.exists():
            try:
                file_path.unlink()

            except OSError:
                pass

    # =============================================================
    # RASTREABILIDADE
    # =============================================================

    def _invalidate_project_approval(
        self,
        *,
        project_id: int | None,
        reason: str,
    ) -> None:
        if project_id is None:
            return

        self.traceability_service.invalidate_technical_approval(
            project_id=project_id,
            reason=reason,
        )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

    def has_primary_image(
        self,
        project_id: int,
    ) -> bool:
        return (
            self.get_primary_image(
                project_id
            )
            is not None
        )

    def get_image_types(
        self,
    ) -> list[str]:
        return sorted(
            self.IMAGE_TYPES
        )