from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from models.project import Project
from models.report_version import ReportVersion
from repositories.report_version_repository import ReportVersionRepository
from services.project_service import ProjectService


class ReportVersionService:
    """Controla emissões oficiais e evolução das versões do relatório."""

    VERSION_PATTERN = re.compile(
        r"^V(?P<major>\d+)\.(?P<minor>\d+)$",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.repository = ReportVersionRepository()
        self.project_service = ProjectService()

    def get_project_versions(
        self,
        project_id: int,
    ) -> list[ReportVersion]:
        if project_id is None:
            return []

        return self.repository.find_by_project_id(
            project_id
        )

    def get_latest_emission(
        self,
        project_id: int,
    ) -> ReportVersion | None:
        if project_id is None:
            return None

        return self.repository.find_latest_by_project_id(
            project_id
        )

    def normalize_version(
        self,
        value: Any,
    ) -> str:
        text = str(
            value or ""
        ).strip().upper()

        if not text:
            return "V1.0"

        if not text.startswith("V"):
            text = f"V{text}"

        match = self.VERSION_PATTERN.match(
            text
        )

        if match is None:
            raise ValueError(
                "Versão inválida. Use o formato V1.0, V1.1, V2.0 etc."
            )

        major = int(
            match.group("major")
        )
        minor = int(
            match.group("minor")
        )

        return f"V{major}.{minor}"

    def next_version(
        self,
        current_version: str,
    ) -> str:
        normalized = self.normalize_version(
            current_version
        )

        match = self.VERSION_PATTERN.match(
            normalized
        )

        if match is None:
            raise ValueError(
                "Não foi possível calcular a próxima versão."
            )

        major = int(
            match.group("major")
        )
        minor = int(
            match.group("minor")
        )

        return f"V{major}.{minor + 1}"

    def register_emission(
        self,
        *,
        project: Project,
        version: str,
        file_path: str | Path,
        technical_control: Any = None,
    ) -> ReportVersion:
        if project.id is None:
            raise ValueError(
                "O processo não possui um identificador válido."
            )

        normalized_version = self.normalize_version(
            version
        )

        current_working_version = self.normalize_version(
            project.version
        )

        if normalized_version != current_working_version:
            raise ValueError(
                "A versão da pré-visualização não corresponde "
                "à versão de trabalho atual do processo."
            )

        existing = self.repository.find_by_project_and_version(
            project.id,
            normalized_version,
        )

        if existing is not None:
            raise ValueError(
                f"A versão {normalized_version} já possui "
                "uma emissão oficial registrada."
            )

        path = Path(
            file_path
        )

        if not path.exists() or not path.is_file():
            raise FileNotFoundError(
                "O arquivo definitivo da emissão não foi encontrado."
            )

        prepared_by = None
        reviewed_by = None

        if technical_control is not None:
            prepared_by = self._optional_text(
                getattr(
                    technical_control,
                    "prepared_by",
                    None,
                )
            )
            reviewed_by = self._optional_text(
                getattr(
                    technical_control,
                    "reviewed_by",
                    None,
                )
            )

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        report_version = ReportVersion(
            project_id=project.id,
            version=normalized_version,
            file_path=str(
                path.resolve()
            ),
            file_name=path.name,
            status="Emitido",
            created_by=prepared_by,
            reviewed_by=reviewed_by,
            created_at=now,
        )

        saved_version = self.repository.create(
            report_version
        )

        previous_project_version = project.version
        next_working_version = self.next_version(
            normalized_version
        )

        try:
            project.version = next_working_version
            self.project_service.update_project(
                project
            )

        except Exception:
            project.version = previous_project_version
            self.repository.delete(
                saved_version.id
            )
            raise

        return saved_version

    def _optional_text(
        self,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        text = str(
            value
        ).strip()

        return text or None