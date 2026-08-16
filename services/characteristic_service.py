from __future__ import annotations

from datetime import datetime
from typing import Any

from models.characteristic import Characteristic
from models.project import Project
from repositories.characteristic_repository import CharacteristicRepository
from services.pdf_service import PDFService
from services.report_extraction_service import ReportExtractionService
from services.traceability_service import TraceabilityService


class CharacteristicService:
    STATUS_OK = "OK"
    STATUS_NOK = "NOK"
    STATUS_UNKNOWN = "UNKNOWN"

    def __init__(self):
        self.pdf_service = PDFService()
        self.extraction_service = ReportExtractionService()
        self.characteristic_repository = CharacteristicRepository()
        self.traceability_service = TraceabilityService()

    def get_project_context(
        self,
        project: Project,
    ) -> dict[str, Any]:
        if project.id is None:
            raise ValueError(
                "O processo não possui um identificador válido."
            )

        documents = self.pdf_service.get_project_documents(
            project.id
        )

        document_map = {
            document.id: document
            for document in documents
            if document.id is not None
        }

        extraction_pairs = (
            self.extraction_service.get_project_extractions(
                project.id
            )
        )

        extraction_map: dict[int, dict[str, Any]] = {}
        extraction_summaries: list[dict[str, Any]] = []

        for extraction, extracted_characteristics in extraction_pairs:
            if extraction.id is None:
                continue

            document = document_map.get(
                extraction.document_id
            )

            document_name = self._get_document_name(
                document=document,
                extraction=extraction,
            )

            specimen_identifier = (
                getattr(document, "specimen_identifier", None)
                if document is not None
                else None
            )

            extraction_map[extraction.id] = {
                "extraction": extraction,
                "document_name": document_name,
                "specimen_identifier": specimen_identifier,
            }

            extraction_summaries.append(
                {
                    "extraction_id": extraction.id,
                    "document_id": extraction.document_id,
                    "document_name": document_name,
                    "specimen_identifier": specimen_identifier,
                    "part_name": extraction.part_name,
                    "part_number": extraction.part_number,
                    "source_type": extraction.source_type,
                    "machine_name": extraction.machine_name,
                    "machine_number": extraction.machine_number,
                    "measurement_datetime": extraction.measurement_datetime,
                    "characteristics_count": len(
                        extracted_characteristics
                    ),
                }
            )

        characteristics = (
            self.characteristic_repository.find_by_project_id(
                project.id
            )
        )

        rows: list[dict[str, Any]] = []

        for sequence, characteristic in enumerate(
            characteristics,
            start=1,
        ):
            metadata = extraction_map.get(
                characteristic.extraction_id
                if characteristic.extraction_id is not None
                else -1
            )

            if metadata is not None:
                extraction = metadata["extraction"]
                document_name = metadata["document_name"]
                specimen_identifier = metadata["specimen_identifier"]
                source_type = extraction.source_type
                machine_name = extraction.machine_name
                machine_number = extraction.machine_number
                measurement_datetime = extraction.measurement_datetime
            else:
                document_name = "Cadastro manual"
                specimen_identifier = None
                source_type = "MANUAL"
                machine_name = None
                machine_number = None
                measurement_datetime = None

            normalized_status = self.normalize_status(
                characteristic.status
            )

            rows.append(
                {
                    "sequence": sequence,
                    "project_id": characteristic.project_id,
                    "extraction_id": characteristic.extraction_id,
                    "origin": (
                        "MANUAL"
                        if characteristic.is_manual
                        else "EXTRACTED"
                    ),
                    "origin_label": (
                        "Manual"
                        if characteristic.is_manual
                        else "Extraída"
                    ),
                    "document_name": document_name,
                    "specimen_identifier": specimen_identifier,
                    "source_type": source_type,
                    "machine_name": machine_name,
                    "machine_number": machine_number,
                    "measurement_datetime": measurement_datetime,
                    "characteristic": characteristic,
                    "characteristic_id": characteristic.id,
                    "name": characteristic.name,
                    "group_name": characteristic.group_name,
                    "datum": characteristic.datum,
                    "property_name": characteristic.property_name,
                    "nominal_value": characteristic.nominal_value,
                    "measured_value": characteristic.measured_value,
                    "lower_tolerance": characteristic.lower_tolerance,
                    "upper_tolerance": characteristic.upper_tolerance,
                    "deviation": characteristic.deviation,
                    "unit": characteristic.unit,
                    "status": normalized_status,
                    "status_label": self.get_status_label(
                        normalized_status
                    ),
                    "check_value": characteristic.check_value,
                    "out_value": characteristic.out_value,
                    "confidence": characteristic.confidence,
                    "extraction_method": characteristic.extraction_method,
                    "source_page": characteristic.source_page,
                    "raw_text": characteristic.raw_text,
                    "extra_data_json": characteristic.extra_data_json,
                }
            )

        return {
            "project": project,
            "summary": self._build_summary(
                rows=rows,
                document_count=len(documents),
                extraction_count=len(extraction_pairs),
            ),
            "rows": rows,
            "documents": extraction_summaries,
            "filters": self._build_filters(rows),
        }

    def create_manual_characteristic(
        self,
        project: Project,
        data: dict[str, Any],
    ) -> Characteristic:
        if project.id is None:
            raise ValueError(
                "O processo não possui um identificador válido."
            )

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        characteristic = Characteristic(
            project_id=project.id,
            extraction_id=None,
            origin="MANUAL",
            name="Temporária",
            confidence=1.0,
            extraction_method="MANUAL",
            created_at=now,
            updated_at=now,
        )

        self._apply_editable_data(
            characteristic,
            data,
        )

        self.characteristic_repository.create(
            characteristic
        )

        self.traceability_service.invalidate_technical_approval(
            project_id=project.id,
            reason="Uma característica foi adicionada manualmente.",
        )

        return characteristic

    def update_characteristic(
        self,
        characteristic: Characteristic,
        data: dict[str, Any],
    ) -> Characteristic:
        if characteristic.id is None:
            raise ValueError(
                "A característica selecionada é inválida."
            )

        previous_state = self._characteristic_state(
            characteristic
        )

        self._apply_editable_data(
            characteristic,
            data,
        )

        new_state = self._characteristic_state(
            characteristic
        )

        characteristic.updated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.characteristic_repository.update(
            characteristic
        )

        if previous_state != new_state:
            self.traceability_service.invalidate_technical_approval(
                project_id=characteristic.project_id,
                reason="Uma característica dimensional foi alterada.",
            )

        return characteristic

    def delete_manual_characteristic(
        self,
        characteristic: Characteristic,
    ) -> None:
        if characteristic.id is None:
            raise ValueError(
                "A característica selecionada é inválida."
            )

        if not characteristic.is_manual:
            raise ValueError(
                "Características extraídas não podem ser excluídas manualmente nesta tela."
            )

        self.characteristic_repository.delete(
            characteristic.id
        )

        self.traceability_service.invalidate_technical_approval(
            project_id=characteristic.project_id,
            reason="Uma característica manual foi removida.",
        )

    def _apply_editable_data(
        self,
        characteristic: Characteristic,
        data: dict[str, Any],
    ) -> None:
        name = self._normalize_optional_text(
            data.get("name")
        )

        if not name:
            raise ValueError(
                "Informe o nome da característica."
            )

        characteristic.name = name
        characteristic.group_name = self._normalize_optional_text(
            data.get("group_name")
        )
        characteristic.nominal_value = self._to_optional_float(
            data.get("nominal_value"),
            "Valor nominal",
        )
        characteristic.measured_value = self._to_optional_float(
            data.get("measured_value"),
            "Valor medido",
        )
        characteristic.lower_tolerance = self._to_optional_float(
            data.get("lower_tolerance"),
            "Tolerância inferior",
        )
        characteristic.upper_tolerance = self._to_optional_float(
            data.get("upper_tolerance"),
            "Tolerância superior",
        )
        characteristic.unit = self._normalize_optional_text(
            data.get("unit")
        )

        deviation_value = data.get("deviation")

        if (
            deviation_value in {None, ""}
            and characteristic.nominal_value is not None
            and characteristic.measured_value is not None
        ):
            characteristic.deviation = (
                characteristic.measured_value
                - characteristic.nominal_value
            )
        else:
            characteristic.deviation = self._to_optional_float(
                deviation_value,
                "Desvio",
            )

        requested_status = self.normalize_status(
            data.get("status")
        )

        automatic_status = self._calculate_status(
            characteristic
        )

        characteristic.status = (
            automatic_status
            if automatic_status is not None
            else requested_status
        )

    def _calculate_status(
        self,
        characteristic: Characteristic,
    ) -> str | None:
        measured = characteristic.measured_value
        nominal = characteristic.nominal_value
        lower = characteristic.lower_tolerance
        upper = characteristic.upper_tolerance

        if measured is None:
            return None

        if (
            nominal is not None
            and lower is not None
            and upper is not None
        ):
            minimum = nominal + lower
            maximum = nominal + upper

            return (
                self.STATUS_OK
                if minimum <= measured <= maximum
                else self.STATUS_NOK
            )

        return None

    def _characteristic_state(
        self,
        characteristic: Characteristic,
    ) -> tuple:
        return (
            self._normalize_optional_text(characteristic.name),
            self._normalize_optional_text(characteristic.group_name),
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
            self._normalize_optional_text(characteristic.unit),
            self.normalize_status(characteristic.status),
        )

    def _normalize_float_for_comparison(
        self,
        value,
    ) -> float | None:
        if value is None:
            return None

        try:
            return round(float(value), 10)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def _build_summary(
        self,
        rows: list[dict[str, Any]],
        document_count: int,
        extraction_count: int,
    ) -> dict[str, int]:
        total = len(rows)

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

        manual_count = sum(
            1
            for row in rows
            if row["origin"] == "MANUAL"
        )

        return {
            "total": total,
            "ok": ok_count,
            "nok": nok_count,
            "unknown": total - ok_count - nok_count,
            "manual": manual_count,
            "documents": document_count,
            "extractions": extraction_count,
        }

    def _build_filters(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        return {
            "documents": self._unique_values(
                row["document_name"]
                for row in rows
                if row["origin"] == "EXTRACTED"
            ),
            "groups": self._unique_values(
                row["group_name"]
                for row in rows
            ),
        }

    def normalize_status(
        self,
        value,
    ) -> str:
        clean = str(
            value or ""
        ).strip().upper().replace(
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
        normalized = self.normalize_status(status)

        if normalized == self.STATUS_OK:
            return "Dentro da tolerância"

        if normalized == self.STATUS_NOK:
            return "Fora da tolerância"

        return "Não avaliada"

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
                return str(file_name)

        if extraction.document_id is not None:
            return f"Documento {extraction.document_id}"

        return "Extração legada"

    def _unique_values(
        self,
        values,
    ) -> list[str]:
        result = []

        for value in values:
            normalized = self._normalize_optional_text(
                value
            )

            if (
                normalized
                and normalized not in result
            ):
                result.append(normalized)

        return result

    def _normalize_optional_text(
        self,
        value,
    ) -> str | None:
        if value is None:
            return None

        clean = str(value).strip()

        return clean or None

    def _to_optional_float(
        self,
        value,
        field_name: str,
    ) -> float | None:
        if value in {None, ""}:
            return None

        clean = str(value).strip()

        if not clean:
            return None

        clean = clean.replace(",", ".")

        try:
            return float(clean)

        except ValueError as error:
            raise ValueError(
                f"O campo '{field_name}' deve conter um número válido."
            ) from error