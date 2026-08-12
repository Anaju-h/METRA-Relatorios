from dataclasses import dataclass
from typing import Optional


@dataclass
class ProjectImage:
    """
    Imagem vinculada a um processo de metrologia.

    Uma imagem pode representar:

    - fotografia da peça;
    - imagem principal da peça ou do lote;
    - setup de medição;
    - fixação;
    - CAD;
    - render;
    - detalhe técnico;
    - evidência de não conformidade.

    Cada processo pode possuir somente uma imagem principal.
    """

    project_id: int

    file_path: str
    file_name: str

    image_type: str = "Fotografia"

    caption: Optional[str] = None

    position: int = 0

    # Imagem utilizada na primeira página do relatório técnico.
    is_primary: bool = False

    id: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None