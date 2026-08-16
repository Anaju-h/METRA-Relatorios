from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from models.measurement import Measurement

from repositories.measurement_repository import (
    MeasurementRepository,
)

from services.pdf_service import PDFService

from services.report_extraction_service import (
    ReportExtractionService,
)

from services.traceability_service import (
    TraceabilityService,
)


class MeasurementService:
    """
    Serviço das informações gerais da medição.

    Responsabilidades:

    - salvar os dados gerais do processo;
    - carregar os dados já revisados manualmente;
    - consolidar informações extraídas dos PDFs;
    - preservar informações individuais de cada documento;
    - impedir que valores genéricos sejam tratados como responsáveis;
    - diferenciar peça única de lote.
    """

    SENSOR_PROBE = "Apalpação"
    SENSOR_OPTICAL = "Sensor óptico"
    SENSOR_DOTSCAN = "DotScan"
    SENSOR_LINESCAN = "LineScan"
    SENSOR_CT = "Tomografia computadorizada"
    SENSOR_SCAN_3D = "Escaneamento 3D"

    GENERIC_OPERATORS = {
        "MASTER",
        "ADMIN",
        "ADMINISTRATOR",
        "USUARIO",
        "USUÁRIO",
        "USER",
        "OPERATOR",
        "OPERADOR",
        "DEFAULT",
        "PADRAO",
        "PADRÃO",
        "UNKNOWN",
        "DESCONHECIDO",
        "N/A",
        "NA",
        "NONE",
        "-",
    }

    def __init__(self):
        self.repository = (
            MeasurementRepository()
        )

        self.extraction_service = (
            ReportExtractionService()
        )

        self.pdf_service = (
            PDFService()
        )

        self.traceability_service = (
            TraceabilityService()
        )

    # =============================================================
    # SALVAR
    # =============================================================

    def save_measurement(
        self,
        project_id: int,
        data: dict[str, Any],
    ) -> Measurement:
        if project_id is None:
            raise ValueError(
                (
                    "O processo não possui "
                    "um identificador válido."
                )
            )

        responsible = self._normalize_optional_text(
            data.get(
                "responsible"
            )
        )

        sensors = self._normalize_sensors(
            data.get(
                "sensors",
                [],
            )
        )

        sensors_json = json.dumps(
            sensors,
            ensure_ascii=False,
        )

        measurement_datetime = (
            self._normalize_optional_text(
                data.get(
                    "measurement_datetime"
                )
            )
        )

        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        existing = (
            self.repository
            .find_by_project_id(
                project_id
            )
        )

        measurement = Measurement(
            project_id=project_id,

            responsible=responsible,

            measurement_datetime=(
                measurement_datetime
            ),

            drawing_reference=(
                self._normalize_optional_text(
                    data.get(
                        "drawing_reference"
                    )
                )
            ),

            alignment=(
                self._normalize_optional_text(
                    data.get(
                        "alignment"
                    )
                )
            ),

            fixture=(
                self._normalize_optional_text(
                    data.get(
                        "fixture"
                    )
                )
            ),

            machine_details=(
                self._normalize_optional_text(
                    data.get(
                        "machine_details"
                    )
                )
            ),

            accessories=(
                self._normalize_optional_text(
                    data.get(
                        "accessories"
                    )
                )
            ),

            sensors=sensors_json,

            special_instructions=(
                self._normalize_optional_text(
                    data.get(
                        "special_instructions"
                    )
                )
            ),

            created_at=(
                existing.created_at
                if existing
                else now
            ),

            updated_at=now,
        )

        previous_state = (
            self._measurement_state(
                existing
            )
        )

        new_state = (
            self._measurement_state(
                measurement
            )
        )

        saved_measurement = (
            self.repository.save(
                measurement
            )
        )

        if previous_state != new_state:
            self.traceability_service.invalidate_technical_approval(
                project_id=project_id,
                reason=(
                    "As informações gerais da medição "
                    "foram alteradas."
                ),
            )

        return saved_measurement

    # =============================================================
    # CARREGAR MEDIÇÃO SALVA
    # =============================================================

    def get_measurement(
        self,
        project_id: int,
    ) -> Optional[Measurement]:
        if project_id is None:
            return None

        return (
            self.repository
            .find_by_project_id(
                project_id
            )
        )

    # =============================================================
    # SENSORES SALVOS
    # =============================================================

    def get_sensors(
        self,
        measurement: Measurement,
    ) -> list[str]:
        if not measurement.sensors:
            return []

        try:
            result = json.loads(
                measurement.sensors
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

        if not isinstance(
            result,
            list,
        ):
            return []

        return self._normalize_sensors(
            result
        )

    # =============================================================
    # CONTEXTO COMPLETO DA TELA
    # =============================================================

    def get_measurement_context(
        self,
        project_id: int,
    ) -> dict[str, Any]:
        """
        Retorna todos os dados necessários para a tela.

        Para um processo com vários documentos:

        - equipamento e software são consolidados;
        - sensores são sugeridos;
        - data e hora permanecem por documento;
        - operador só é sugerido quando todos os documentos possuem
          o mesmo responsável válido;
        - valores genéricos, como Master, são ignorados.
        """

        if project_id is None:
            raise ValueError(
                "Processo inválido."
            )

        saved_measurement = (
            self.repository
            .find_by_project_id(
                project_id
            )
        )

        extraction_pairs = (
            self.extraction_service
            .get_project_extractions(
                project_id
            )
        )

        extractions = [
            extraction
            for extraction, _
            in extraction_pairs
        ]

        document_count = len(
            extractions
        )

        is_batch = (
            document_count > 1
        )

        individual_measurements = (
            self._build_individual_measurements(
                extractions
            )
        )

        suggestions = (
            self._build_extraction_suggestions(
                extractions=extractions,
                is_batch=is_batch,
            )
        )

        return {
            "saved_measurement":
                saved_measurement,

            "suggestions":
                suggestions,

            "individual_measurements":
                individual_measurements,

            "document_count":
                document_count,

            "is_batch":
                is_batch,

            "has_extracted_data":
                bool(extractions),
        }

    # =============================================================
    # MEDIÇÕES INDIVIDUAIS
    # =============================================================

    def _build_individual_measurements(
        self,
        extractions,
    ) -> list[dict[str, Any]]:
        result = []

        for index, extraction in enumerate(
            extractions,
            start=1,
        ):
            document = None

            if extraction.document_id is not None:
                try:
                    document = (
                        self.pdf_service
                        .document_service
                        .get_document(
                            extraction.document_id
                        )
                    )

                except Exception:
                    document = None

            file_name = None
            specimen_identifier = None

            if document is not None:
                file_name = (
                    document.file_name
                    or document.stored_name
                )

                specimen_identifier = (
                    document.specimen_identifier
                )

            valid_operator = (
                self._normalize_operator(
                    extraction.operator
                )
            )

            result.append(
                {
                    "order":
                        index,

                    "document_id":
                        extraction.document_id,

                    "file_name":
                        (
                            file_name
                            or f"Documento {index:02d}"
                        ),

                    "specimen_identifier":
                        specimen_identifier,

                    "part_name":
                        extraction.part_name,

                    "part_number":
                        extraction.part_number,

                    "measurement_datetime":
                        extraction.measurement_datetime,

                    "operator":
                        valid_operator,

                    "machine_name":
                        extraction.machine_name,

                    "machine_number":
                        extraction.machine_number,

                    "source_type":
                        extraction.source_type,
                }
            )

        return result

    # =============================================================
    # CONSOLIDAR SUGESTÕES
    # =============================================================

    def _build_extraction_suggestions(
        self,
        extractions,
        is_batch: bool,
    ) -> dict[str, Any]:
        operators_by_document = [
            self._normalize_operator(
                extraction.operator
            )
            for extraction in extractions
        ]

        valid_operators = self._unique_values(
            operators_by_document
        )

        documents_with_valid_operator = sum(
            1
            for operator
            in operators_by_document
            if operator
        )

        total_documents = len(
            extractions
        )

        all_documents_have_operator = (
            total_documents > 0
            and documents_with_valid_operator
            == total_documents
        )

        # O responsável geral só é sugerido quando todos os
        # documentos possuem exatamente o mesmo nome válido.
        responsible = None

        if (
            all_documents_have_operator
            and len(valid_operators) == 1
        ):
            responsible = (
                valid_operators[0]
            )

        measurement_datetimes = (
            self._unique_values(
                extraction.measurement_datetime
                for extraction in extractions
            )
        )

        alignments = self._unique_values(
            extraction.alignment
            for extraction in extractions
        )

        machine_names = self._unique_values(
            extraction.machine_name
            for extraction in extractions
        )

        machine_numbers = self._unique_values(
            extraction.machine_number
            for extraction in extractions
        )

        software_names = self._unique_values(
            extraction.software_name
            for extraction in extractions
        )

        software_versions = (
            self._unique_values(
                extraction.software_version
                for extraction in extractions
            )
        )

        source_types = self._unique_values(
            extraction.source_type
            for extraction in extractions
        )

        analysis_types = self._unique_values(
            extraction.analysis_type
            for extraction in extractions
        )

        conflicts = []

        # ---------------------------------------------------------
        # RESPONSÁVEL
        # ---------------------------------------------------------

        if len(valid_operators) > 1:
            conflicts.append(
                (
                    "Foram encontrados responsáveis diferentes "
                    "nos documentos: "
                    f"{' · '.join(valid_operators)}."
                )
            )

        elif (
            valid_operators
            and not all_documents_have_operator
        ):
            conflicts.append(
                (
                    "O responsável foi identificado somente em "
                    f"{documents_with_valid_operator} de "
                    f"{total_documents} documento(s). "
                    "O campo geral deve ser confirmado manualmente."
                )
            )

        # ---------------------------------------------------------
        # DATA E HORA
        # ---------------------------------------------------------

        measurement_datetime = None

        if not is_batch:
            if len(
                measurement_datetimes
            ) == 1:
                measurement_datetime = (
                    measurement_datetimes[0]
                )

        # Em lote, datas diferentes são esperadas e não são conflito.
        # Elas permanecerão na lista de medições individuais.

        # ---------------------------------------------------------
        # ALINHAMENTO
        # ---------------------------------------------------------

        alignment = None

        if len(alignments) == 1:
            alignment = alignments[0]

        elif len(alignments) > 1:
            conflicts.append(
                (
                    "Foram encontrados alinhamentos diferentes: "
                    f"{' · '.join(alignments)}."
                )
            )

        # ---------------------------------------------------------
        # EQUIPAMENTO
        # ---------------------------------------------------------

        equipment_summary = (
            self._build_equipment_summary(
                machine_names=machine_names,
                machine_numbers=machine_numbers,
            )
        )

        software_summary = (
            self._build_software_summary(
                software_names=software_names,
                software_versions=software_versions,
            )
        )

        machine_details = (
            self._build_machine_details(
                equipment_summary=equipment_summary,
                software_summary=software_summary,
            )
        )

        suggested_sensors = (
            self._suggest_sensors(
                machine_names=machine_names,
                source_types=source_types,
                analysis_types=analysis_types,
            )
        )

        return {
            "responsible":
                responsible,

            "responsible_values":
                valid_operators,

            "responsible_document_count":
                documents_with_valid_operator,

            "responsible_total_documents":
                total_documents,

            "responsible_is_complete":
                all_documents_have_operator,

            "measurement_datetime":
                measurement_datetime,

            "measurement_datetime_values":
                measurement_datetimes,

            "dates_are_individual":
                is_batch,

            "alignment":
                alignment,

            "alignment_values":
                alignments,

            "equipment_summary":
                equipment_summary,

            "machine_names":
                machine_names,

            "machine_numbers":
                machine_numbers,

            "machine_details":
                machine_details,

            "software_summary":
                software_summary,

            "software_names":
                software_names,

            "software_versions":
                software_versions,

            "suggested_sensors":
                suggested_sensors,

            "source_types":
                source_types,

            "analysis_types":
                analysis_types,

            "conflicts":
                conflicts,
        }

    # =============================================================
    # OPERADOR
    # =============================================================

    def _normalize_operator(
        self,
        value,
    ) -> str | None:
        normalized = (
            self._normalize_optional_text(
                value
            )
        )

        if not normalized:
            return None

        comparison = (
            normalized
            .strip()
            .upper()
        )

        if comparison in self.GENERIC_OPERATORS:
            return None

        # Evita valores puramente numéricos ou muito curtos.
        if comparison.isdigit():
            return None

        if len(comparison) < 3:
            return None

        return normalized

    # =============================================================
    # EQUIPAMENTO
    # =============================================================

    def _build_equipment_summary(
        self,
        machine_names: list[str],
        machine_numbers: list[str],
    ) -> str | None:
        if not machine_names:
            return None

        names_text = " · ".join(
            machine_names
        )

        if not machine_numbers:
            return names_text

        numbers_text = " · ".join(
            machine_numbers
        )

        return (
            f"{names_text}"
            f" — identificação: "
            f"{numbers_text}"
        )

    def _build_software_summary(
        self,
        software_names: list[str],
        software_versions: list[str],
    ) -> str | None:
        if not software_names:
            return None

        software_text = " · ".join(
            software_names
        )

        if not software_versions:
            return software_text

        versions_text = " · ".join(
            software_versions
        )

        return (
            f"{software_text}"
            f" — versão: "
            f"{versions_text}"
        )

    def _build_machine_details(
        self,
        equipment_summary: str | None,
        software_summary: str | None,
    ) -> str | None:
        parts = []

        if equipment_summary:
            parts.append(
                equipment_summary
            )

        if software_summary:
            parts.append(
                software_summary
            )

        if not parts:
            return None

        return " | ".join(
            parts
        )

    # =============================================================
    # SENSORES SUGERIDOS
    # =============================================================

    def _suggest_sensors(
        self,
        machine_names: list[str],
        source_types: list[str],
        analysis_types: list[str],
    ) -> list[str]:
        combined = " ".join(
            [
                *machine_names,
                *source_types,
                *analysis_types,
            ]
        ).upper()

        sensors = []

        if any(
            term in combined
            for term in (
                "DURAMAX",
                "PRISMO",
                "CALYPSO",
            )
        ):
            sensors.append(
                self.SENSOR_PROBE
            )

        if "O-INSPECT" in combined:
            sensors.append(
                self.SENSOR_OPTICAL
            )

        if "DOTSCAN" in combined:
            sensors.append(
                self.SENSOR_DOTSCAN
            )

        if "LINESCAN" in combined:
            sensors.append(
                self.SENSOR_LINESCAN
            )

        if any(
            term in combined
            for term in (
                "BOSELLO",
                "TOMOGRAF",
                "VOLUM",
                "CT",
            )
        ):
            sensors.append(
                self.SENSOR_CT
            )

        if any(
            term in combined
            for term in (
                "ATOS",
                "T-SCAN",
                "TSCAN",
                "ESCANEAMENTO 3D",
                "SUPERF",
            )
        ):
            sensors.append(
                self.SENSOR_SCAN_3D
            )

        return self._unique_values(
            sensors
        )

    # =============================================================
    # RASTREABILIDADE
    # =============================================================

    def _measurement_state(
        self,
        measurement: Measurement | None,
    ) -> tuple | None:
        """
        Retorna somente o conteúdo técnico da medição.

        IDs e timestamps são ignorados para que salvar novamente
        os mesmos dados não invalide uma aprovação existente.
        """

        if measurement is None:
            return None

        return (
            self._normalize_optional_text(
                measurement.responsible
            ),
            self._normalize_optional_text(
                measurement.measurement_datetime
            ),
            self._normalize_optional_text(
                measurement.drawing_reference
            ),
            self._normalize_optional_text(
                measurement.alignment
            ),
            self._normalize_optional_text(
                measurement.fixture
            ),
            self._normalize_optional_text(
                measurement.machine_details
            ),
            self._normalize_optional_text(
                measurement.accessories
            ),
            tuple(
                self._measurement_sensors(
                    measurement
                )
            ),
            self._normalize_optional_text(
                measurement.special_instructions
            ),
        )

    def _measurement_sensors(
        self,
        measurement: Measurement,
    ) -> list[str]:
        if not measurement.sensors:
            return []

        try:
            raw_sensors = json.loads(
                measurement.sensors
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

        return self._normalize_sensors(
            raw_sensors
        )

    # =============================================================
    # NORMALIZAÇÃO
    # =============================================================

    def _normalize_sensors(
        self,
        sensors,
    ) -> list[str]:
        if not isinstance(
            sensors,
            (
                list,
                tuple,
                set,
            ),
        ):
            return []

        normalized = []

        for sensor in sensors:
            value = str(
                sensor
            ).strip()

            if (
                value
                and value
                not in normalized
            ):
                normalized.append(
                    value
                )

        return normalized

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

        normalized = str(
            value
        ).strip()

        return normalized or None