from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Annotation:
    """
    Representa uma marcação criada sobre uma imagem.

    Tipos suportados:

    - rectangle
    - circle
    - line
    - arrow
    - text
    - marker

    Formas:
        x, y, width e height.

    Linhas e setas:
        x e y representam o ponto inicial.
        end_x e end_y representam o ponto final.

    Texto:
        utiliza o campo text.

    Marcador numerado:
        utiliza o campo marker_text.
    """

    image_id: int

    annotation_type: str

    x: float
    y: float

    width: float = 0.0
    height: float = 0.0

    end_x: Optional[float] = None
    end_y: Optional[float] = None

    text: Optional[str] = None
    marker_text: Optional[str] = None

    font_size: int = 18

    stroke_width: float = 3.0

    # Cor em formato hexadecimal.
    #
    # Exemplos:
    # #EB2323
    # #0067B1
    # #FFFFFF
    color: str = "#EB2323"

    id: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None