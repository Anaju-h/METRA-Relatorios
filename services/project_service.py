from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from models.project import Project
from repositories.project_repository import (
    ProjectRepository,
)
from repositories.report_version_repository import (
    ReportVersionRepository,
)
from repositories.technical_control_repository import (
    TechnicalControlRepository,
)
from services.report_templates.template_catalog import (
    get_template_definition,
    suggest_template_code,
)
from utils.ids import generate_report_id


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"


class ProjectService:
    STATUS_EDITING = "Em edição"
    STATUS_COMPLETED = "Concluído"
    STATUS_EXCLUDED = "Excluído"

    def __init__(self):
        self.repository = (
            ProjectRepository()
        )

        self.report_version_repository = (
            ReportVersionRepository()
        )

        self.technical_control_repository = (
            TechnicalControlRepository()
        )

    def create_project(
        self,
        data: dict[str, Any],
    ) -> Project:
        name = str(
            data.get("name", "")
        ).strip()

        part_name = str(
            data.get("part_name", "")
        ).strip()

        inspection_type = str(
            data.get(
                "inspection_type",
                "Inspeção dimensional",
            )
        ).strip()

        analysis_mode = str(
            data.get(
                "analysis_mode",
                "Peça única",
            )
        ).strip()

        equipment = self._optional_text(
            data.get("equipment")
        )

        technology = self._optional_text(
            data.get("technology")
        )

        quantity = self._normalize_quantity(
            data.get("quantity", 1)
        )

        template = str(
            data.get("template", "")
        ).strip()

        if not name:
            raise ValueError(
                "Informe o nome do processo."
            )

        if not inspection_type:
            raise ValueError(
                "Selecione o tipo de inspeção."
            )

        if not analysis_mode:
            raise ValueError(
                "Selecione o modo da análise."
            )

        if not template:
            template = suggest_template_code(
                inspection_type=inspection_type,
                analysis_mode=analysis_mode,
                quantity=quantity,
                equipment=equipment,
            )

        template_definition = (
            get_template_definition(
                template
            )
        )

        if not part_name:
            part_name = "Não informado"

        report_id = generate_report_id()

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        project = Project(
            report_id=report_id,
            name=name,
            template=template,
            inspection_type=inspection_type,
            analysis_mode=analysis_mode,
            quantity=quantity,
            technology=technology,
            template_version=template_definition.version,
            part_name=part_name,
            part_code=self._optional_text(
                data.get("part_code")
            ),
            client=self._optional_text(
                data.get("client")
            ),
            equipment=equipment,
            description=self._optional_text(
                data.get("description")
            ),
            status=self.STATUS_EDITING,
            version="V1.0",
            created_at=now,
            updated_at=now,
        )

        project = self.repository.create(
            project
        )

        self.create_project_directories(
            project.report_id
        )

        return project

    def update_project(
        self,
        project: Project,
    ) -> Project:
        get_template_definition(
            project.template
        )

        project.quantity = (
            self._normalize_quantity(
                project.quantity
            )
        )

        project.updated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        return self.repository.update(
            project
        )

    def get_project(
        self,
        report_id: str,
    ) -> Optional[Project]:
        return self.repository.find_by_report_id(
            report_id
        )

    def get_recent_projects(
        self,
        limit: int = 6,
    ) -> list[Project]:
        return self.repository.find_recent(
            limit
        )

    def get_all_projects(
        self,
    ) -> list[Project]:
        return self.repository.find_all()

    # =============================================================
    # STATUS DO PROCESSO
    # =============================================================

    def complete_project(
        self,
        project: Project,
    ) -> Project:
        if project.id is None:
            raise ValueError(
                "O processo não possui identificador válido."
            )

        if project.status == self.STATUS_COMPLETED:
            return project

        if project.status == self.STATUS_EXCLUDED:
            raise ValueError(
                "Um processo excluído não pode ser concluído."
            )

        emission_count = (
            self.report_version_repository
            .count_by_project_id(
                project.id
            )
        )

        if emission_count <= 0:
            raise ValueError(
                (
                    "O processo só pode ser concluído após "
                    "a emissão oficial de pelo menos uma versão "
                    "do relatório."
                )
            )

        technical_control = (
            self.technical_control_repository
            .find_by_project_id(
                project.id
            )
        )

        if (
            technical_control is None
            or technical_control.status != "Aprovado"
        ):
            raise ValueError(
                (
                    "O controle técnico precisa estar aprovado "
                    "antes da conclusão do processo."
                )
            )

        project.status = (
            self.STATUS_COMPLETED
        )

        project.updated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.repository.update_status(
            project_id=project.id,
            status=project.status,
            updated_at=project.updated_at,
        )

        return project

    def reopen_project(
        self,
        project: Project,
    ) -> Project:
        if project.id is None:
            raise ValueError(
                "O processo não possui identificador válido."
            )

        if project.status == self.STATUS_EXCLUDED:
            raise ValueError(
                "Um processo excluído não pode ser reaberto."
            )

        if project.status == self.STATUS_EDITING:
            return project

        project.status = (
            self.STATUS_EDITING
        )

        project.updated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.repository.update_status(
            project_id=project.id,
            status=project.status,
            updated_at=project.updated_at,
        )

        return project

    def delete_project(
        self,
        project: Project,
    ) -> None:
        """
        Exclusão lógica.

        Banco, arquivos, versões e evidências permanecem preservados
        para rastreabilidade. O processo deixa apenas de aparecer nas
        consultas normais da aplicação.
        """

        if project.id is None:
            raise ValueError(
                "O processo não possui identificador válido."
            )

        if project.status == self.STATUS_EXCLUDED:
            return

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        self.repository.soft_delete(
            project_id=project.id,
            updated_at=now,
        )

        project.status = (
            self.STATUS_EXCLUDED
        )

        project.updated_at = now

    def suggest_template(
        self,
        *,
        inspection_type: str,
        analysis_mode: str,
        quantity: int,
        equipment: str | None = None,
    ) -> str:
        return suggest_template_code(
            inspection_type=inspection_type,
            analysis_mode=analysis_mode,
            quantity=self._normalize_quantity(
                quantity
            ),
            equipment=equipment,
        )

    def create_project_directories(
        self,
        report_id: str,
    ) -> None:
        project_dir = (
            PROJECTS_DIR
            / report_id
        )

        directories = [
            project_dir,
            project_dir / "original",
            project_dir / "images",
            project_dir / "attachments",
            project_dir / "generated",
            project_dir / "previews",
            project_dir / "exports",
            project_dir / "cache",
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    def _normalize_quantity(
        self,
        value: Any,
    ) -> int:
        try:
            quantity = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Informe uma quantidade válida."
            ) from error

        if quantity < 1:
            raise ValueError(
                "A quantidade deve ser maior que zero."
            )

        return quantity

    def _optional_text(
        self,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        clean_value = str(
            value
        ).strip()

        if not clean_value:
            return None

        return clean_value