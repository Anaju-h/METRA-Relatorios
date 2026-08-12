from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from models.annotation import Annotation
from repositories.annotation_repository import (
    AnnotationRepository,
)
from repositories.image_repository import (
    ImageRepository,
)
from services.traceability_service import (
    TraceabilityService,
)


class AnnotationService:
    """
    Serviço responsável pela validação e persistência
    das marcações de uma imagem.

    O estado completo do editor é salvo de uma vez:

    1. valida todas as marcações;
    2. remove o estado anterior;
    3. grava o novo estado.
    """

    VALID_TYPES = {
        "rectangle",
        "circle",
        "line",
        "arrow",
        "text",
        "marker",
    }

    DEFAULT_FONT_SIZE = 18
    DEFAULT_STROKE_WIDTH = 3.0
    DEFAULT_COLOR = "#EB2323"

    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 96

    MIN_STROKE_WIDTH = 1.0
    MAX_STROKE_WIDTH = 20.0

    COLOR_PATTERN = re.compile(
        r"^#[0-9A-Fa-f]{6}$"
    )

    def __init__(self):
        self.repository = (
            AnnotationRepository()
        )

        self.image_repository = (
            ImageRepository()
        )

        self.traceability_service = (
            TraceabilityService()
        )

    # =============================================================
    # SALVAR TODAS AS MARCAÇÕES
    # =============================================================

    def save_annotations(
        self,
        image_id: int,
        annotations_data: list[dict[str, Any]],
    ) -> list[Annotation]:
        if image_id is None:
            raise ValueError(
                "Imagem inválida."
            )

        if not isinstance(
            annotations_data,
            list,
        ):
            raise ValueError(
                (
                    "As marcações devem ser "
                    "informadas em uma lista."
                )
            )

        previous_annotations = (
            self.repository
            .find_by_image_id(
                image_id
            )
        )

        previous_state = (
            self._annotation_state_from_models(
                previous_annotations
            )
        )

        normalized_annotations = []

        for index, data in enumerate(
            annotations_data,
            start=1,
        ):
            normalized = (
                self._normalize_annotation_data(
                    data=data,
                    index=index,
                )
            )

            normalized_annotations.append(
                normalized
            )

        # A exclusão só acontece depois que todas
        # as marcações foram validadas.
        self.repository.delete_by_image_id(
            image_id
        )

        saved: list[Annotation] = []

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        for data in normalized_annotations:
            annotation = Annotation(
                image_id=image_id,

                annotation_type=data[
                    "annotation_type"
                ],

                x=data[
                    "x"
                ],

                y=data[
                    "y"
                ],

                width=data[
                    "width"
                ],

                height=data[
                    "height"
                ],

                end_x=data[
                    "end_x"
                ],

                end_y=data[
                    "end_y"
                ],

                text=data[
                    "text"
                ],

                marker_text=data[
                    "marker_text"
                ],

                font_size=data[
                    "font_size"
                ],

                stroke_width=data[
                    "stroke_width"
                ],

                color=data[
                    "color"
                ],

                created_at=now,
                updated_at=now,
            )

            saved_annotation = (
                self.repository.create(
                    annotation
                )
            )

            saved.append(
                saved_annotation
            )

        new_state = (
            self._annotation_state_from_models(
                saved
            )
        )

        if previous_state != new_state:
            self._invalidate_project_approval(
                image_id=image_id,
                reason=(
                    "Marcações de uma imagem técnica "
                    "foram alteradas."
                ),
            )

        return saved

    # =============================================================
    # CARREGAR
    # =============================================================

    def get_annotations(
        self,
        image_id: int,
    ) -> list[Annotation]:
        if image_id is None:
            return []

        return self.repository.find_by_image_id(
            image_id
        )

    # =============================================================
    # CONTAR
    # =============================================================

    def count_annotations(
        self,
        image_id: int,
    ) -> int:
        if image_id is None:
            return 0

        return self.repository.count_by_image_id(
            image_id
        )

    # =============================================================
    # LIMPAR
    # =============================================================

    def clear_annotations(
        self,
        image_id: int,
    ) -> None:
        if image_id is None:
            raise ValueError(
                "Imagem inválida."
            )

        had_annotations = (
            self.repository
            .count_by_image_id(
                image_id
            )
            > 0
        )

        self.repository.delete_by_image_id(
            image_id
        )

        if had_annotations:
            self._invalidate_project_approval(
                image_id=image_id,
                reason=(
                    "Marcações de uma imagem técnica "
                    "foram removidas."
                ),
            )

    # =============================================================
    # RASTREABILIDADE
    # =============================================================

    def _invalidate_project_approval(
        self,
        *,
        image_id: int,
        reason: str,
    ) -> None:
        image = (
            self.image_repository
            .find_by_id(
                image_id
            )
        )

        if (
            image is None
            or image.project_id is None
        ):
            return

        self.traceability_service.invalidate_technical_approval(
            project_id=image.project_id,
            reason=reason,
        )

    def _annotation_state_from_models(
        self,
        annotations: list[Annotation],
    ) -> list[tuple]:
        """
        Converte o estado persistido para uma forma comparável.

        IDs e timestamps são ignorados, porque não representam
        alteração técnica do conteúdo da marcação.
        """

        return [
            (
                str(
                    annotation.annotation_type
                    or ""
                ).strip().lower(),
                round(
                    float(
                        annotation.x
                        or 0.0
                    ),
                    4,
                ),
                round(
                    float(
                        annotation.y
                        or 0.0
                    ),
                    4,
                ),
                round(
                    float(
                        annotation.width
                        or 0.0
                    ),
                    4,
                ),
                round(
                    float(
                        annotation.height
                        or 0.0
                    ),
                    4,
                ),
                (
                    round(
                        float(
                            annotation.end_x
                        ),
                        4,
                    )
                    if annotation.end_x is not None
                    else None
                ),
                (
                    round(
                        float(
                            annotation.end_y
                        ),
                        4,
                    )
                    if annotation.end_y is not None
                    else None
                ),
                (
                    str(
                        annotation.text
                        or ""
                    ).strip()
                    or None
                ),
                (
                    str(
                        annotation.marker_text
                        or ""
                    ).strip()
                    or None
                ),
                int(
                    annotation.font_size
                    or self.DEFAULT_FONT_SIZE
                ),
                round(
                    float(
                        annotation.stroke_width
                        or self.DEFAULT_STROKE_WIDTH
                    ),
                    4,
                ),
                str(
                    annotation.color
                    or self.DEFAULT_COLOR
                ).strip().upper(),
            )
            for annotation in annotations
        ]

    # =============================================================
    # NORMALIZAÇÃO
    # =============================================================

    def _normalize_annotation_data(
        self,
        data: dict[str, Any],
        index: int,
    ) -> dict[str, Any]:
        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                (
                    f"A marcação {index} possui "
                    "uma estrutura inválida."
                )
            )

        annotation_type = str(
            data.get(
                "annotation_type",
                "",
            )
        ).strip().lower()

        # Compatibilidade com marcações antigas.
        if annotation_type == "number":
            annotation_type = "marker"

        if (
            annotation_type
            not in self.VALID_TYPES
        ):
            raise ValueError(
                (
                    f"A marcação {index} possui "
                    "um tipo inválido: "
                    f"{annotation_type or 'vazio'}."
                )
            )

        x = self._to_float(
            data.get(
                "x",
                0.0,
            ),
            field_name="x",
            index=index,
        )

        y = self._to_float(
            data.get(
                "y",
                0.0,
            ),
            field_name="y",
            index=index,
        )

        width = self._to_float(
            data.get(
                "width",
                0.0,
            ),
            field_name="width",
            index=index,
        )

        height = self._to_float(
            data.get(
                "height",
                0.0,
            ),
            field_name="height",
            index=index,
        )

        end_x = self._to_optional_float(
            data.get(
                "end_x"
            ),
            field_name="end_x",
            index=index,
        )

        end_y = self._to_optional_float(
            data.get(
                "end_y"
            ),
            field_name="end_y",
            index=index,
        )

        text = self._normalize_optional_text(
            data.get(
                "text"
            )
        )

        marker_text = (
            self._normalize_optional_text(
                data.get(
                    "marker_text"
                )
            )
        )

        font_size = self._to_int(
            data.get(
                "font_size",
                self.DEFAULT_FONT_SIZE,
            ),
            field_name="font_size",
            index=index,
        )

        stroke_width = self._to_float(
            data.get(
                "stroke_width",
                self.DEFAULT_STROKE_WIDTH,
            ),
            field_name="stroke_width",
            index=index,
        )

        color = self._normalize_color(
            data.get(
                "color",
                self.DEFAULT_COLOR,
            )
        )

        font_size = max(
            self.MIN_FONT_SIZE,
            min(
                self.MAX_FONT_SIZE,
                font_size,
            ),
        )

        stroke_width = max(
            self.MIN_STROKE_WIDTH,
            min(
                self.MAX_STROKE_WIDTH,
                stroke_width,
            ),
        )

        # ---------------------------------------------------------
        # RETÂNGULO E CÍRCULO
        # ---------------------------------------------------------

        if annotation_type in {
            "rectangle",
            "circle",
        }:
            if (
                width <= 0
                or height <= 0
            ):
                raise ValueError(
                    (
                        f"A marcação {index} possui "
                        "dimensões inválidas."
                    )
                )

            end_x = None
            end_y = None

            text = None
            marker_text = None

        # ---------------------------------------------------------
        # LINHA E SETA
        # ---------------------------------------------------------

        elif annotation_type in {
            "line",
            "arrow",
        }:
            if (
                end_x is None
                or end_y is None
            ):
                raise ValueError(
                    (
                        f"A marcação {index} não "
                        "possui um ponto final."
                    )
                )

            if (
                abs(end_x - x) < 0.5
                and abs(end_y - y) < 0.5
            ):
                raise ValueError(
                    (
                        f"A marcação {index} possui "
                        "comprimento insuficiente."
                    )
                )

            width = 0.0
            height = 0.0

            text = None
            marker_text = None

        # ---------------------------------------------------------
        # TEXTO
        # ---------------------------------------------------------

        elif annotation_type == "text":
            if not text:
                text = "Texto"

            width = 0.0
            height = 0.0

            end_x = None
            end_y = None

            marker_text = None

        # ---------------------------------------------------------
        # MARCADOR
        # ---------------------------------------------------------

        elif annotation_type == "marker":
            if not marker_text:
                marker_text = "01"

            width = 0.0
            height = 0.0

            end_x = None
            end_y = None

            text = None

        return {
            "annotation_type":
                annotation_type,

            "x":
                x,

            "y":
                y,

            "width":
                width,

            "height":
                height,

            "end_x":
                end_x,

            "end_y":
                end_y,

            "text":
                text,

            "marker_text":
                marker_text,

            "font_size":
                font_size,

            "stroke_width":
                stroke_width,

            "color":
                color,
        }

    # =============================================================
    # COR
    # =============================================================

    def _normalize_color(
        self,
        value,
    ) -> str:
        if value is None:
            return self.DEFAULT_COLOR

        clean = str(
            value
        ).strip()

        if not clean:
            return self.DEFAULT_COLOR

        if not clean.startswith(
            "#"
        ):
            clean = (
                f"#{clean}"
            )

        clean = clean.upper()

        if not self.COLOR_PATTERN.fullmatch(
            clean
        ):
            return self.DEFAULT_COLOR

        return clean

    # =============================================================
    # CONVERSÕES
    # =============================================================

    def _to_float(
        self,
        value,
        field_name: str,
        index: int,
    ) -> float:
        try:
            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                (
                    f"O campo '{field_name}' da "
                    f"marcação {index} é inválido."
                )
            )

    def _to_optional_float(
        self,
        value,
        field_name: str,
        index: int,
    ) -> float | None:
        if value in (
            None,
            "",
        ):
            return None

        return self._to_float(
            value=value,
            field_name=field_name,
            index=index,
        )

    def _to_int(
        self,
        value,
        field_name: str,
        index: int,
    ) -> int:
        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                (
                    f"O campo '{field_name}' da "
                    f"marcação {index} é inválido."
                )
            )

    def _normalize_optional_text(
        self,
        value,
    ) -> str | None:
        if value is None:
            return None

        clean = str(
            value
        ).strip()

        return clean or None