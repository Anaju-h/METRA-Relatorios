from __future__ import annotations

from datetime import datetime
from typing import Any

from models.characteristic import Characteristic
from models.project import Project

from repositories.characteristic_repository import (
    CharacteristicRepository,
)

from services.pdf_service import PDFService
from services.report_extraction_service import (
    ReportExtractionService,
)
from services.traceability_service import (
    TraceabilityService,
)


class CharacteristicService:
    """
    Organiza as características extraídas de todos os documentos
    de um processo.

    A camada mantém a seguinte relação:

        Processo
            └── Documento
                    └── Extração
                            └── Características
    """

    STATUS_OK = "OK"
    STATUS_NOK = "NOK"
    STATUS_UNKNOWN = "UNKNOWN"

    STATUS_LABELS = {
        "OK": "Dentro da tolerância",
        "PASS": "Dentro da tolerância",
        "APPROVED": "Dentro da tolerância",
        "CONFORME": "Dentro da tolerância",

        "NOK": "Fora da tolerância",
        "FAIL": "Fora da tolerância",
        "FAILED": "Fora da tolerância",
        "REJECTED": "Fora da tolerância",
        "NAO_CONFORME": "Fora da tolerância",
        "NÃO CONFORME": "Fora da tolerância",

        "UNKNOWN": "Não avaliada",
        "PENDING": "Não avaliada",
        "": "Não avaliada",
    }

    def __init__(self):
        self.pdf_service = PDFService()

        self.extraction_service = (
            ReportExtractionService()
        )

        self.characteristic_repository = (
            CharacteristicRepository()
        )

        self.traceability_service = (
            TraceabilityService()
        )

    # =============================================================
    # CONTEXTO COMPLETO DA TELA
    # =============================================================

    def get_project_context(
        self,
        project: Project,
    ) -> dict[str, Any]:
        if project.id is None:
            raise ValueError(
                "O processo não possui um identificador válido."
            )

        documents = (
            self.pdf_service
            .get_project_documents(
                project.id
            )
        )

        document_map = {
            document.id: document
            for document in documents
            if document.id is not None
        }

        extraction_pairs = (
            self.extraction_service
            .get_project_extractions(
                project.id
            )
        )

        rows: list[dict[str, Any]] = []

        extraction_summaries = []

        sequence = 1

        for extraction, characteristics in extraction_pairs:
            document = document_map.get(
                extraction.document_id
            )

            document_name = self._get_document_name(
                document=document,
                extraction=extraction,
            )

            specimen_identifier = (
                getattr(
                    document,
                    "specimen_identifier",
                    None,
                )
                if document is not None
                else None
            )

            extraction_summary = {
                "extraction_id":
                    extraction.id,

                "document_id":
                    extraction.document_id,

                "document_name":
                    document_name,

                "specimen_identifier":
                    specimen_identifier,

                "part_name":
                    extraction.part_name,

                "part_number":
                    extraction.part_number,

                "source_type":
                    extraction.source_type,

                "machine_name":
                    extraction.machine_name,

                "machine_number":
                    extraction.machine_number,

                "measurement_datetime":
                    extraction.measurement_datetime,

                "characteristics_count":
                    len(characteristics),
            }

            extraction_summaries.append(
                extraction_summary
            )

            for characteristic in characteristics:
                normalized_status = (
                    self.normalize_status(
                        characteristic.status
                    )
                )

                status_label = (
                    self.get_status_label(
                        normalized_status
                    )
                )

                row = {
                    "sequence":
                        sequence,

                    "document_id":
                        extraction.document_id,

                    "document_name":
                        document_name,

                    "specimen_identifier":
                        specimen_identifier,

                    "extraction_id":
                        extraction.id,

                    "source_type":
                        extraction.source_type,

                    "machine_name":
                        extraction.machine_name,

                    "machine_number":
                        extraction.machine_number,

                    "measurement_datetime":
                        extraction.measurement_datetime,

                    "characteristic":
                        characteristic,

                    "characteristic_id":
                        characteristic.id,

                    "name":
                        characteristic.name,

                    "group_name":
                        characteristic.group_name,

                    "datum":
                        characteristic.datum,

                    "property_name":
                        characteristic.property_name,

                    "nominal_value":
                        characteristic.nominal_value,

                    "measured_value":
                        characteristic.measured_value,

                    "lower_tolerance":
                        characteristic.lower_tolerance,

                    "upper_tolerance":
                        characteristic.upper_tolerance,

                    "deviation":
                        characteristic.deviation,

                    "unit":
                        characteristic.unit,

                    "status":
                        normalized_status,

                    "status_label":
                        status_label,

                    "check_value":
                        characteristic.check_value,

                    "out_value":
                        characteristic.out_value,

                    "confidence":
                        characteristic.confidence,

                    "extraction_method":
                        characteristic.extraction_method,

                    "source_page":
                        characteristic.source_page,

                    "raw_text":
                        characteristic.raw_text,

                    "extra_data_json":
                        characteristic.extra_data_json,
                }

                rows.append(
                    row
                )

                sequence += 1

        summary = self._build_summary(
            rows=rows,
            document_count=len(
                documents
            ),
            extraction_count=len(
                extraction_pairs
            ),
        )

        filters = self._build_filters(
            rows
        )

        return {
            "project":
                project,

            "summary":
                summary,

            "rows":
                rows,

            "documents":
                extraction_summaries,

            "filters":
                filters,
        }

    # =============================================================
    # SALVAR ALTERAÇÕES
    # =============================================================

    def update_characteristic(
        self,
        characteristic: Characteristic,
        data: dict[str, Any],
    ) -> Characteristic:
        if characteristic.id is None:
            raise ValueError(
                "A característica selecionada é inválida."
            )

        previous_state = (
            self._characteristic_state(
                characteristic
            )
        )

        name = self._normalize_optional_text(
            data.get(
                "name"
            )
        )

        if not name:
            raise ValueError(
                "Informe o nome da característica."
            )

        characteristic.name = name

        characteristic.group_name = (
            self._normalize_optional_text(
                data.get(
                    "group_name"
                )
            )
        )

        characteristic.measured_value = (
            self._to_optional_float(
                data.get(
                    "measured_value"
                ),
                "Valor medido",
            )
        )

        characteristic.nominal_value = (
            self._to_optional_float(
                data.get(
                    "nominal_value"
                ),
                "Valor nominal",
            )
        )

        characteristic.lower_tolerance = (
            self._to_optional_float(
                data.get(
                    "lower_tolerance"
                ),
                "Tolerância inferior",
            )
        )

        characteristic.upper_tolerance = (
            self._to_optional_float(
                data.get(
                    "upper_tolerance"
                ),
                "Tolerância superior",
            )
        )

        characteristic.deviation = (
            self._to_optional_float(
                data.get(
                    "deviation"
                ),
                "Desvio",
            )
        )

        characteristic.unit = (
            self._normalize_optional_text(
                data.get(
                    "unit"
                )
            )
        )

        characteristic.status = (
            self.normalize_status(
                data.get(
                    "status"
                )
            )
        )

        new_state = (
            self._characteristic_state(
                characteristic
            )
        )

        characteristic.updated_at = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        self.characteristic_repository.update(
            characteristic
        )

        if previous_state != new_state:
            project_id = (
                self._resolve_project_id(
                    characteristic.extraction_id
                )
            )

            if project_id is not None:
                self.traceability_service.invalidate_technical_approval(
                    project_id=project_id,
                    reason=(
                        "Uma característica dimensional "
                        "foi alterada."
                    ),
                )

        return characteristic

    # =============================================================
    # RASTREABILIDADE
    # =============================================================

    def _resolve_project_id(
        self,
        extraction_id: int | None,
    ) -> int | None:
        if extraction_id is None:
            return None

        extraction = (
            self.extraction_service
            .extraction_repository
            .find_by_id(
                extraction_id
            )
        )

        if extraction is None:
            return None

        return extraction.project_id

    def _characteristic_state(
        self,
        characteristic: Characteristic,
    ) -> tuple:
        """
        Retorna somente os campos técnicos editáveis.

        IDs e timestamps são ignorados para que salvar sem
        alteração não invalide uma aprovação existente.
        """

        return (
            self._normalize_optional_text(
                characteristic.name
            ),
            self._normalize_optional_text(
                characteristic.group_name
            ),
            self._normalize_float_for_comparison(
                characteristic.measured_value
            ),
            self._normalize_float_for_comparison(
                characteristic.nominal_value
            ),
            self._normalize_float_for_comparison(
                characteristic.lower_tolerance
            ),
            self._normalize_float_for_comparison(
                characteristic.upper_tolerance
            ),
            self._normalize_float_for_comparison(
                characteristic.deviation
            ),
            self._normalize_optional_text(
                characteristic.unit
            ),
            self.normalize_status(
                characteristic.status
            ),
        )

    def _normalize_float_for_comparison(
        self,
        value,
    ) -> float | None:
        if value is None:
            return None

        try:
            return round(
                float(value),
                10,
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    # =============================================================
    # RESUMO
    # =============================================================

    def _build_summary(
        self,
        rows: list[dict[str, Any]],
        document_count: int,
        extraction_count: int,
    ) -> dict[str, int]:
        total = len(
            rows
        )

        ok_count = sum(
            1
            for row in rows
            if row["status"] == self.STATUS_OK
        )

        nok_count = sum(
            1
            for row in rows
            if row["status"] == self.STATUS_NOK
        )

        unknown_count = (
            total
            - ok_count
            - nok_count
        )

        reviewed_count = sum(
            1
            for row in rows
            if (
                row["confidence"] is not None
                and float(
                    row["confidence"]
                    or 0
                ) >= 0.80
            )
        )

        return {
            "total":
                total,

            "ok":
                ok_count,

            "nok":
                nok_count,

            "unknown":
                unknown_count,

            "documents":
                document_count,

            "extractions":
                extraction_count,

            "high_confidence":
                reviewed_count,
        }

    # =============================================================
    # FILTROS
    # =============================================================

    def _build_filters(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        documents = self._unique_values(
            row["document_name"]
            for row in rows
        )

        groups = self._unique_values(
            row["group_name"]
            for row in rows
        )

        source_types = self._unique_values(
            row["source_type"]
            for row in rows
        )

        return {
            "documents":
                documents,

            "groups":
                groups,

            "source_types":
                source_types,
        }

    # =============================================================
    # STATUS
    # =============================================================

    def normalize_status(
        self,
        value,
    ) -> str:
        clean = str(
            value
            or ""
        ).strip().upper()

        clean = clean.replace(
            "-",
            "_",
        )

        if clean in {
            "OK",
            "PASS",
            "APPROVED",
            "CONFORME",
        }:
            return self.STATUS_OK

        if clean in {
            "NOK",
            "FAIL",
            "FAILED",
            "REJECTED",
            "NAO_CONFORME",
            "NÃO CONFORME",
        }:
            return self.STATUS_NOK

        return self.STATUS_UNKNOWN

    def get_status_label(
        self,
        status: str,
    ) -> str:
        normalized = self.normalize_status(
            status
        )

        if normalized == self.STATUS_OK:
            return "Dentro da tolerância"

        if normalized == self.STATUS_NOK:
            return "Fora da tolerância"

        return "Não avaliada"

    # =============================================================
    # DOCUMENTO
    # =============================================================

    def _get_document_name(
        self,
        document,
        extraction,
    ) -> str:
        if document is not None:
            file_name = getattr(
                document,
                "file_name",
                None,
            )

            if file_name:
                return str(
                    file_name
                )

        if extraction.document_id is not None:
            return (
                f"Documento {extraction.document_id}"
            )

        return "Extração legada"

    # =============================================================
    # HELPERS
    # =============================================================

    def _unique_values(
        self,
        values,
    ) -> list[str]:
        result = []

        for value in values:
            normalized = (
                self._normalize_optional_text(
                    value
                )
            )

            if (
                normalized
                and normalized
                not in result
            ):
                result.append(
                    normalized
                )

        return result

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

    def _to_optional_float(
        self,
        value,
        field_name: str,
    ) -> float | None:
        if value in {
            None,
            "",
        }:
            return None

        clean = str(
            value
        ).strip()

        if not clean:
            return None

        clean = clean.replace(
            ",",
            ".",
        )

        try:
            return float(
                clean
            )

        except ValueError:
            raise ValueError(
                (
                    f"O campo '{field_name}' deve "
                    "conter um número válido."
                )
            )