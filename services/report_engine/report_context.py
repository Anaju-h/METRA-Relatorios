from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from models.project import Project
from services.image_service import ImageService


@dataclass(slots=True)
class ReportRenderContext:
    """
    Contexto central utilizado pelo motor de relatórios do METRA.

    Reúne todos os dados necessários para a geração do PDF,
    evitando que projeto, estatísticas, gráficos, imagens e
    informações específicas de inspeção sejam enviados
    separadamente entre os renderizadores.
    """

    project: Project

    context: dict[str, Any]

    sections: dict[str, bool]

    statistics: dict[str, Any] = field(
        default_factory=dict
    )

    charts: dict[str, Any] = field(
        default_factory=dict
    )

    temporary_directory: Path | None = None

    output_path: Path | None = None

    # =============================================================
    # TEMPLATE
    # =============================================================

    @property
    def template_code(
        self,
    ) -> str:
        return str(
            self.project.template
            or "PERSONALIZADO"
        ).strip()

    @property
    def template_version(
        self,
    ) -> str:
        value = getattr(
            self.project,
            "template_version",
            None,
        )

        return str(
            value
            or "1.0"
        ).strip()

    # =============================================================
    # ESCOPO
    # =============================================================

    @property
    def is_batch(
        self,
    ) -> bool:
        return bool(
            self.context.get(
                "is_batch",
                False,
            )
        )

    @property
    def quantity(
        self,
    ) -> int:
        quantity = getattr(
            self.project,
            "quantity",
            1,
        )

        try:
            return max(
                1,
                int(
                    quantity
                    or 1
                ),
            )

        except (
            TypeError,
            ValueError,
        ):
            return 1

    # =============================================================
    # DOCUMENTOS
    # =============================================================

    @property
    def documents(
        self,
    ) -> list[Any]:
        return list(
            self.context.get(
                "documents",
                [],
            )
            or []
        )

    @property
    def extractions(
        self,
    ) -> list[Any]:
        return list(
            self.context.get(
                "extractions",
                [],
            )
            or []
        )

    # =============================================================
    # MEDIÇÃO
    # =============================================================

    @property
    def measurement(
        self,
    ) -> Any | None:
        return self.context.get(
            "measurement"
        )

    # =============================================================
    # IMAGENS
    # =============================================================

    @property
    def images(
        self,
    ) -> list[Any]:
        return list(
            self.context.get(
                "images",
                [],
            )
            or []
        )

    @property
    def primary_image(
        self,
    ) -> Any | None:
        return self.context.get(
            "primary_image"
        )

    @property
    def additional_images(
        self,
    ) -> list[Any]:
        primary = self.primary_image

        if primary is None:
            return self.images

        primary_id = getattr(
            primary,
            "id",
            None,
        )

        return [
            image
            for image in self.images
            if getattr(
                image,
                "id",
                None,
            )
            != primary_id
        ]

    def get_report_image_path(
        self,
        image: Any | None,
    ) -> Path | None:
        """
        Retorna a imagem pronta para inserção no relatório.

        Quando a imagem possui marcações salvas, o ImageService
        gera uma cópia temporária com as anotações aplicadas.
        A imagem original nunca é modificada.
        """

        if image is None:
            return None

        file_path = getattr(
            image,
            "file_path",
            None,
        )

        if not file_path:
            return None

        source_path = Path(
            str(
                file_path
            )
        )

        if self.temporary_directory is None:
            return (
                source_path
                if source_path.exists()
                else None
            )

        image_service = ImageService()

        return image_service.prepare_report_image(
            image=image,
            output_directory=(
                self.temporary_directory
                / "report_images"
            ),
        )

    @property
    def primary_report_image_path(
        self,
    ) -> Path | None:
        """
        Caminho da imagem principal já preparada para o relatório.
        """

        return self.get_report_image_path(
            self.primary_image
        )

    def get_additional_report_images(
        self,
    ) -> list[tuple[Any, Path]]:
        """
        Retorna todas as imagens adicionais válidas já preparadas
        para o relatório, preservando a ordem definida no processo.
        """

        prepared: list[
            tuple[Any, Path]
        ] = []

        for image in self.additional_images:
            path = self.get_report_image_path(
                image
            )

            if path is None:
                continue

            prepared.append(
                (
                    image,
                    path,
                )
            )

        return prepared

    def get_report_images(
        self,
    ) -> list[tuple[Any, Path]]:
        """
        Retorna todas as imagens do processo prontas para o relatório.
        """

        prepared: list[
            tuple[Any, Path]
        ] = []

        for image in self.images:
            path = self.get_report_image_path(
                image
            )

            if path is None:
                continue

            prepared.append(
                (
                    image,
                    path,
                )
            )

        return prepared

    # =============================================================
    # CONTROLE TÉCNICO
    # =============================================================

    @property
    def technical_control(
        self,
    ) -> Any | None:
        return self.context.get(
            "technical_control"
        )

    # =============================================================
    # RESUMOS
    # =============================================================

    @property
    def document_summary(
        self,
    ) -> dict[str, Any]:
        return dict(
            self.context.get(
                "document_summary",
                {},
            )
            or {}
        )

    @property
    def characteristic_summary(
        self,
    ) -> dict[str, Any]:
        return dict(
            self.context.get(
                "characteristic_summary",
                {},
            )
            or {}
        )

    @property
    def image_summary(
        self,
    ) -> dict[str, Any]:
        return dict(
            self.context.get(
                "image_summary",
                {},
            )
            or {}
        )

    @property
    def control_summary(
        self,
    ) -> dict[str, Any]:
        return dict(
            self.context.get(
                "control_summary",
                {},
            )
            or {}
        )

    # =============================================================
    # ESTATÍSTICAS
    # =============================================================

    @property
    def statistical_groups(
        self,
    ) -> list[Any]:
        return list(
            self.statistics.get(
                "groups",
                [],
            )
            or []
        )

    @property
    def overall_statistics(
        self,
    ) -> dict[str, Any]:
        return dict(
            self.statistics.get(
                "overall",
                {},
            )
            or {}
        )

    # =============================================================
    # GRÁFICOS
    # =============================================================

    @property
    def overall_chart(
        self,
    ) -> Path | None:
        value = self.charts.get(
            "overall_conformity"
        )

        if not value:
            return None

        return Path(value)

    @property
    def group_summary_chart(
        self,
    ) -> Path | None:
        value = self.charts.get(
            "group_summary"
        )

        if not value:
            return None

        return Path(value)

    @property
    def characteristic_charts(
        self,
    ) -> list[dict[str, Any]]:
        return list(
            self.charts.get(
                "characteristic_charts",
                [],
            )
            or []
        )

    # =============================================================
    # TOMOGRAFIA
    # =============================================================

    @property
    def tomography_parameters(
        self,
    ) -> dict[str, Any]:
        """
        Parâmetros técnicos da aquisição tomográfica.

        Exemplos:
        - tensão;
        - corrente;
        - tamanho do voxel;
        - projeções;
        - duração;
        - geometria;
        - filtro;
        - distância fonte-detector.
        """

        return dict(
            self.context.get(
                "tomography_parameters",
                {},
            )
            or {}
        )

    @property
    def tomography_images(
        self,
    ) -> dict[str, Any]:
        """
        Imagens estruturadas da análise tomográfica.

        Chaves previstas:
        - xy
        - xz
        - yz
        - render
        - outras futuras
        """

        return dict(
            self.context.get(
                "tomography_images",
                {},
            )
            or {}
        )

    @property
    def findings(
        self,
    ) -> list[Any]:
        """
        Achados técnicos identificados na tomografia.

        Cada item pode representar, por exemplo:
        - porosidade;
        - inclusão;
        - trinca;
        - vazio;
        - descontinuidade;
        - região de interesse.
        """

        value = self.context.get(
            "findings",
            [],
        )

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            tuple,
        ):
            return list(
                value
            )

        if isinstance(
            value,
            dict,
        ):
            return [
                value
            ]

        return []

    @property
    def tomography_notes(
        self,
    ) -> str | None:
        value = self.context.get(
            "tomography_notes"
        )

        if value is None:
            return None

        cleaned = " ".join(
            str(
                value
            ).split()
        )

        return (
            cleaned
            or None
        )

    @property
    def inspection_objective(
        self,
    ) -> str | None:
        """
        Objetivo técnico da inspeção.

        Procura primeiro um valor específico de tomografia e,
        depois, um objetivo genérico do processo.
        """

        candidates = [
            self.context.get(
                "tomography_objective"
            ),
            self.context.get(
                "inspection_objective"
            ),
            self.context.get(
                "objective"
            ),
        ]

        for value in candidates:
            if value is None:
                continue

            cleaned = " ".join(
                str(
                    value
                ).split()
            )

            if cleaned:
                return cleaned

        return None

    @property
    def tomography_findings_count(
        self,
    ) -> int:
        return len(
            self.findings
        )

    # =============================================================
    # ACESSO GENÉRICO
    # =============================================================

    def get_context_value(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Acesso controlado ao contexto bruto para dados que ainda
        não justificam uma propriedade própria.
        """

        return self.context.get(
            key,
            default,
        )

    # =============================================================
    # SEÇÕES
    # =============================================================

    def section_enabled(
        self,
        key: str,
    ) -> bool:
        return bool(
            self.sections.get(
                key,
                False,
            )
        )

    # =============================================================
    # CAMINHOS
    # =============================================================

    def get_temporary_path(
        self,
        file_name: str,
    ) -> Path:
        if self.temporary_directory is None:
            raise RuntimeError(
                "O diretório temporário do relatório não foi definido."
            )

        return (
            self.temporary_directory
            / file_name
        )