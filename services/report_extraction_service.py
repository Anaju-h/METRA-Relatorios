from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.characteristic import Characteristic
from models.document_draft import DocumentDraft
from models.extracted_report import ExtractedReport
from models.project_draft import ProjectDraft

from repositories.characteristic_repository import (
    CharacteristicRepository,
)
from repositories.extraction_repository import (
    ExtractionRepository,
)

from services.document_analysis.analyzer import (
    DocumentAnalyzer,
)
from services.document_analysis.profiles.calypso import (
    CalypsoProfile,
)
from services.pdf_service import PDFService


class ReportExtractionService:
    """
    Integra o motor documental com a aplicação.

    Estrutura:

        Projeto
            └── Documento
                    └── Extração
                            └── Características

    Cada documento possui sua própria extração.
    Um projeto pode possuir vários documentos.
    """

    def __init__(self):
        self.pdf_service = PDFService()

        self.document_analyzer = (
            DocumentAnalyzer()
        )

        self.extraction_repository = (
            ExtractionRepository()
        )

        self.characteristic_repository = (
            CharacteristicRepository()
        )

    # =============================================================
    # ANÁLISE PRÉVIA DE UM ARQUIVO
    # =============================================================

    def analyze_file(
        self,
        file_path: str,
    ) -> ProjectDraft:
        """
        Analisa um PDF antes da criação definitiva do projeto.

        Esse método representa a análise individual de um documento.
        Mesmo quando vários PDFs formam um lote, cada arquivo é
        analisado separadamente por este método.

        A consolidação do lote é feita posteriormente pelo
        BatchAnalysisService.
        """

        path = Path(
            file_path
        )

        self._validate_pdf_path(
            path
        )

        parsed = (
            self.document_analyzer
            .analyze(
                path
            )
        )

        (
            equipment,
            equipment_origin,
        ) = self._resolve_parsed_equipment(
            parsed
        )

        suggested_template = (
            self.suggest_template(
                source_type=(
                    parsed.source_type
                ),

                equipment=(
                    equipment
                ),

                analysis_type=getattr(
                    parsed,
                    "analysis_type",
                    None,
                ),
            )
        )

        suggested_name = (
            self.suggest_project_name(
                part_name=(
                    parsed.part_name
                ),

                template=(
                    suggested_template
                ),
            )
        )

        warnings = self._build_warnings(
            parsed=parsed,
            equipment=equipment,
            equipment_origin=(
                equipment_origin
            ),
        )

        self._register_equipment_provenance(
            parsed=parsed,
            equipment=equipment,
            equipment_origin=(
                equipment_origin
            ),
        )

        return ProjectDraft(
            # Cada arquivo é analisado individualmente.
            # O BatchAnalysisService transforma depois o conjunto
            # em process_type="batch", quando necessário.
            process_type="single_piece",

            source_path=str(
                path
            ),

            source_type=(
                parsed.source_type
            ),

            base_part_name=(
                parsed.part_name
            ),

            part_name=(
                parsed.part_name
            ),

            detected_part_names=(
                [parsed.part_name]
                if parsed.part_name
                else []
            ),

            equipment=(
                equipment
            ),

            equipments=(
                [equipment]
                if equipment
                else []
            ),

            machine_number=(
                parsed.machine_number
            ),

            operator=(
                parsed.operator
            ),

            measurement_datetime=(
                parsed.measurement_datetime
            ),

            software_name=(
                parsed.software_name
            ),

            software_version=(
                parsed.software_version
            ),

            measurement_count=(
                parsed.measurement_count
            ),

            out_of_tolerance_count=(
                parsed.out_of_tolerance_count
            ),

            measurement_duration=(
                parsed.measurement_duration
            ),

            suggested_template=(
                suggested_template
            ),

            suggested_project_name=(
                suggested_name
            ),

            characteristics_count=len(
                parsed.characteristics
            ),

            parsed_report=(
                parsed
            ),

            warnings=warnings,
        )

    # =============================================================
    # ANALISAR DOCUMENTO JÁ SALVO
    # =============================================================

    def analyze_document(
        self,
        project_id: int,
        document_id: int,
    ) -> tuple[
        ExtractedReport,
        list[Characteristic],
    ]:
        """
        Analisa um ProjectDocument que já foi registrado no banco.
        """

        document_path = (
            self.pdf_service
            .get_document_path(
                document_id
            )
        )

        try:
            self.pdf_service.update_document_analysis(
                document_id=document_id,
                status="Analisando",
                message=None,
            )

            parsed = (
                self.document_analyzer
                .analyze(
                    document_path
                )
            )

            result = self.persist_analysis(
                project_id=project_id,
                document_id=document_id,
                parsed=parsed,
            )

            self.pdf_service.update_document_analysis(
                document_id=document_id,

                status="Concluído",

                source_type=(
                    parsed.source_type
                ),

                page_count=(
                    parsed.page_count
                ),

                message=None,
            )

            return result

        except Exception as error:
            self.pdf_service.update_document_analysis(
                document_id=document_id,

                status="Falha",

                message=str(
                    error
                ),
            )

            raise

    # =============================================================
    # ANALISAR TODOS OS DOCUMENTOS DO PROJETO
    # =============================================================

    def analyze_project_documents(
        self,
        project_id: int,
    ) -> tuple[
        list[
            tuple[
                ExtractedReport,
                list[Characteristic],
            ]
        ],
        list[dict],
    ]:
        documents = (
            self.pdf_service
            .get_project_documents(
                project_id
            )
        )

        if not documents:
            raise FileNotFoundError(
                (
                    "O projeto ainda não possui "
                    "documentos originais."
                )
            )

        results = []
        failures = []

        for document in documents:
            if document.id is None:
                continue

            try:
                result = (
                    self.analyze_document(
                        project_id=project_id,
                        document_id=document.id,
                    )
                )

                results.append(
                    result
                )

            except Exception as error:
                failures.append(
                    {
                        "document_id":
                            document.id,

                        "file_name":
                            document.file_name,

                        "error":
                            str(error),
                    }
                )

        return (
            results,
            failures,
        )

    # =============================================================
    # COMPATIBILIDADE — ANALISAR PROJETO
    # =============================================================

    def analyze_project(
        self,
        project_id: int,
        report_id: str | None = None,
    ) -> tuple[
        ExtractedReport,
        list[Characteristic],
    ]:
        """
        Mantém compatibilidade com telas antigas.

        Analisa o primeiro documento ativo do projeto.

        Para projetos antigos, ainda pode utilizar o PDF salvo em:

            original/relatorio_original.pdf
        """

        documents = (
            self.pdf_service
            .get_project_documents(
                project_id
            )
        )

        if documents:
            first_document = (
                documents[0]
            )

            if first_document.id is None:
                raise ValueError(
                    (
                        "O documento principal não possui "
                        "identificador válido."
                    )
                )

            return self.analyze_document(
                project_id=project_id,

                document_id=(
                    first_document.id
                ),
            )

        if not report_id:
            raise FileNotFoundError(
                (
                    "O projeto ainda não possui "
                    "relatório original."
                )
            )

        legacy_path = (
            self.pdf_service
            .get_pdf_path(
                report_id
            )
        )

        if not legacy_path.exists():
            raise FileNotFoundError(
                (
                    "O projeto ainda não possui "
                    "relatório original."
                )
            )

        parsed = (
            self.document_analyzer
            .analyze(
                legacy_path
            )
        )

        return self.persist_analysis(
            project_id=project_id,
            document_id=None,
            parsed=parsed,
        )

    # =============================================================
    # PERSISTIR PROJECT DRAFT INDIVIDUAL
    # =============================================================

    def persist_draft(
        self,
        project_id: int,
        draft: ProjectDraft,
        document_id: int | None = None,
    ) -> tuple[
        ExtractedReport,
        list[Characteristic],
    ]:
        if draft.parsed_report is None:
            raise ValueError(
                (
                    "O rascunho não possui "
                    "uma análise para salvar."
                )
            )

        return self.persist_analysis(
            project_id=project_id,
            document_id=document_id,
            parsed=draft.parsed_report,
        )

    # =============================================================
    # PERSISTIR DOCUMENT DRAFT
    # =============================================================

    def persist_document_draft(
        self,
        project_id: int,
        document_id: int,
        draft: DocumentDraft,
    ) -> tuple[
        ExtractedReport,
        list[Characteristic],
    ]:
        if draft.parsed_report is None:
            raise ValueError(
                (
                    f"O documento '{draft.file_name}' "
                    "não possui uma análise para salvar."
                )
            )

        result = self.persist_analysis(
            project_id=project_id,
            document_id=document_id,
            parsed=draft.parsed_report,
        )

        self.pdf_service.update_document_analysis(
            document_id=document_id,

            status="Concluído",

            source_type=(
                draft.source_type
                or "UNKNOWN"
            ),

            page_count=getattr(
                draft.parsed_report,
                "page_count",
                None,
            ),

            message=None,
        )

        return result

    # =============================================================
    # PERSISTIR ANÁLISE
    # =============================================================

    def persist_analysis(
        self,
        project_id: int,
        parsed,
        document_id: int | None = None,
    ) -> tuple[
        ExtractedReport,
        list[Characteristic],
    ]:
        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        if document_id is not None:
            existing = (
                self.extraction_repository
                .find_by_document_id(
                    document_id
                )
            )

        else:
            existing = (
                self._find_legacy_extraction(
                    project_id
                )
            )

        (
            resolved_equipment,
            equipment_origin,
        ) = self._resolve_parsed_equipment(
            parsed
        )

        self._register_equipment_provenance(
            parsed=parsed,

            equipment=(
                resolved_equipment
            ),

            equipment_origin=(
                equipment_origin
            ),
        )

        extraction_confidence = (
            self._get_extraction_confidence(
                parsed
            )
        )

        warnings_json = json.dumps(
            list(
                getattr(
                    parsed,
                    "warnings",
                    [],
                )
                or []
            ),
            ensure_ascii=False,
        )

        extraction = ExtractedReport(
            id=(
                existing.id
                if existing
                else None
            ),

            project_id=project_id,

            document_id=document_id,

            source_type=(
                parsed.source_type
            ),

            document_title=getattr(
                parsed,
                "document_title",
                None,
            ),

            analysis_type=getattr(
                parsed,
                "analysis_type",
                None,
            ),

            part_name=(
                parsed.part_name
            ),

            part_number=(
                parsed.part_number
            ),

            machine_name=(
                resolved_equipment
            ),

            machine_number=(
                parsed.machine_number
            ),

            equipment_origin=(
                equipment_origin
            ),

            operator=(
                parsed.operator
            ),

            measurement_datetime=(
                parsed.measurement_datetime
            ),

            measurement_count=(
                parsed.measurement_count
            ),

            out_of_tolerance_count=(
                parsed.out_of_tolerance_count
            ),

            measurement_duration=(
                parsed.measurement_duration
            ),

            software_name=(
                parsed.software_name
            ),

            software_version=(
                parsed.software_version
            ),

            alignment=getattr(
                parsed,
                "alignment",
                None,
            ),

            length_unit=getattr(
                parsed,
                "length_unit",
                None,
            ),

            page_count=(
                parsed.page_count
            ),

            extraction_confidence=(
                extraction_confidence
            ),

            warnings_json=(
                warnings_json
            ),

            reviewed=(
                existing.reviewed
                if existing
                else False
            ),

            created_at=(
                existing.created_at
                if existing
                else now
            ),

            updated_at=now,
        )

        extraction = (
            self.extraction_repository
            .save(
                extraction
            )
        )

        if extraction.id is None:
            raise RuntimeError(
                (
                    "Não foi possível salvar "
                    "a extração documental."
                )
            )

        saved_characteristics = (
            self._replace_characteristics(
                project_id=project_id,

                extraction_id=(
                    extraction.id
                ),

                parsed_characteristics=(
                    parsed.characteristics
                ),

                timestamp=now,
            )
        )

        return (
            extraction,
            saved_characteristics,
        )

    # =============================================================
    # SUBSTITUIR CARACTERÍSTICAS
    # =============================================================

    def _replace_characteristics(
        self,
        project_id: int,
        extraction_id: int,
        parsed_characteristics,
        timestamp: str,
    ) -> list[Characteristic]:
        self.characteristic_repository.delete_by_extraction_id(
            extraction_id
        )

        saved = []

        for parsed_characteristic in (
            parsed_characteristics
            or []
        ):
            extra_data = getattr(
                parsed_characteristic,
                "extra_data",
                None,
            )

            if extra_data is not None:
                extra_data_json = (
                    json.dumps(
                        extra_data,
                        ensure_ascii=False,
                    )
                )

            else:
                extra_data_json = None

            characteristic = Characteristic(
                project_id=project_id,

                extraction_id=(
                    extraction_id
                ),

                origin="EXTRACTED",

                name=(
                    parsed_characteristic.name
                ),

                group_name=getattr(
                    parsed_characteristic,
                    "group_name",
                    None,
                ),

                datum=getattr(
                    parsed_characteristic,
                    "datum",
                    None,
                ),

                property_name=getattr(
                    parsed_characteristic,
                    "property_name",
                    None,
                ),

                measured_value=getattr(
                    parsed_characteristic,
                    "measured_value",
                    None,
                ),

                nominal_value=getattr(
                    parsed_characteristic,
                    "nominal_value",
                    None,
                ),

                upper_tolerance=getattr(
                    parsed_characteristic,
                    "upper_tolerance",
                    None,
                ),

                lower_tolerance=getattr(
                    parsed_characteristic,
                    "lower_tolerance",
                    None,
                ),

                deviation=getattr(
                    parsed_characteristic,
                    "deviation",
                    None,
                ),

                unit=getattr(
                    parsed_characteristic,
                    "unit",
                    None,
                ),

                status=getattr(
                    parsed_characteristic,
                    "status",
                    "UNKNOWN",
                ),

                check_value=getattr(
                    parsed_characteristic,
                    "check_value",
                    None,
                ),

                out_value=getattr(
                    parsed_characteristic,
                    "out_value",
                    None,
                ),

                confidence=float(
                    getattr(
                        parsed_characteristic,
                        "confidence",
                        0.0,
                    )
                    or 0.0
                ),

                extraction_method=getattr(
                    parsed_characteristic,
                    "extraction_method",
                    None,
                ),

                source_page=getattr(
                    parsed_characteristic,
                    "source_page",
                    None,
                ),

                raw_text=getattr(
                    parsed_characteristic,
                    "raw_text",
                    None,
                ),

                extra_data_json=(
                    extra_data_json
                ),

                created_at=(
                    timestamp
                ),

                updated_at=(
                    timestamp
                ),
            )

            saved_characteristic = (
                self.characteristic_repository
                .create(
                    characteristic
                )
            )

            saved.append(
                saved_characteristic
            )

        return saved

    # =============================================================
    # CARREGAR EXTRAÇÃO PRINCIPAL
    # =============================================================

    def get_project_extraction(
        self,
        project_id: int,
    ) -> tuple[
        ExtractedReport | None,
        list[Characteristic],
    ]:
        """
        Compatibilidade com telas que ainda exibem somente
        a primeira extração do projeto.
        """

        extraction = (
            self.extraction_repository
            .find_by_project_id(
                project_id
            )
        )

        if (
            extraction is None
            or extraction.id is None
        ):
            return (
                None,
                [],
            )

        characteristics = (
            self.characteristic_repository
            .find_by_extraction_id(
                extraction.id
            )
        )

        return (
            extraction,
            characteristics,
        )

    # =============================================================
    # CARREGAR TODAS AS EXTRAÇÕES
    # =============================================================

    def get_project_extractions(
        self,
        project_id: int,
    ) -> list[
        tuple[
            ExtractedReport,
            list[Characteristic],
        ]
    ]:
        extractions = (
            self.extraction_repository
            .find_all_by_project_id(
                project_id
            )
        )

        result = []

        for extraction in extractions:
            if extraction.id is None:
                continue

            characteristics = (
                self.characteristic_repository
                .find_by_extraction_id(
                    extraction.id
                )
            )

            result.append(
                (
                    extraction,
                    characteristics,
                )
            )

        return result

    # =============================================================
    # CARREGAR EXTRAÇÃO DE UM DOCUMENTO
    # =============================================================

    def get_document_extraction(
        self,
        document_id: int,
    ) -> tuple[
        ExtractedReport | None,
        list[Characteristic],
    ]:
        extraction = (
            self.extraction_repository
            .find_by_document_id(
                document_id
            )
        )

        if (
            extraction is None
            or extraction.id is None
        ):
            return (
                None,
                [],
            )

        characteristics = (
            self.characteristic_repository
            .find_by_extraction_id(
                extraction.id
            )
        )

        return (
            extraction,
            characteristics,
        )

    # =============================================================
    # REVISÃO
    # =============================================================

    def save_review(
        self,
        extraction: ExtractedReport,
        characteristics: list[
            Characteristic
        ],
    ) -> None:
        now = (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )

        extraction.reviewed = True
        extraction.updated_at = now

        self.extraction_repository.save(
            extraction
        )

        for characteristic in characteristics:
            characteristic.updated_at = now

            self.characteristic_repository.update(
                characteristic
            )

    # =============================================================
    # EQUIPAMENTO
    # =============================================================

    def _resolve_parsed_equipment(
        self,
        parsed,
    ) -> tuple[
        str | None,
        str,
    ]:
        extracted_equipment = (
            self.normalize_equipment(
                source_type=(
                    parsed.source_type
                ),

                machine_name=(
                    parsed.machine_name
                ),
            )
        )

        return self.resolve_equipment(
            source_type=(
                parsed.source_type
            ),

            analysis_type=getattr(
                parsed,
                "analysis_type",
                None,
            ),

            extracted_equipment=(
                extracted_equipment
            ),
        )

    def resolve_equipment(
        self,
        source_type: str,
        analysis_type: str | None,
        extracted_equipment: str | None,
    ) -> tuple[
        str | None,
        str,
    ]:
        if extracted_equipment:
            return (
                extracted_equipment,
                "document",
            )

        normalized_source = (
            source_type
            or ""
        ).upper()

        normalized_analysis = (
            analysis_type
            or ""
        ).upper()

        if (
            normalized_source
            == "ZEISS_INSPECT"
            and "VOLUM"
            in normalized_analysis
        ):
            return (
                "ZEISS Bosello Max",
                "business_rule_inference",
            )

        return (
            None,
            "unknown",
        )

    def normalize_equipment(
        self,
        source_type: str,
        machine_name: str | None,
    ) -> str | None:
        if not machine_name:
            return None

        if source_type == "CALYPSO":
            return (
                CalypsoProfile
                .normalize_equipment(
                    machine_name
                )
            )

        return machine_name.strip()

    # =============================================================
    # TEMPLATE
    # =============================================================

    def suggest_template(
        self,
        source_type: str,
        equipment: str | None,
        analysis_type: str | None = None,
    ) -> str:
        equipment_upper = (
            equipment
            or ""
        ).upper()

        analysis_upper = (
            analysis_type
            or ""
        ).upper()

        if "BOSELLO" in equipment_upper:
            return (
                "Tomografia Computadorizada"
            )

        if (
            "ATOS" in equipment_upper
            or "T-SCAN" in equipment_upper
        ):
            return (
                "Escaneamento 3D"
            )

        if "O-INSPECT" in equipment_upper:
            return (
                "Inspeção Multissensor"
            )

        if (
            "PRISMO" in equipment_upper
            or "DURAMAX" in equipment_upper
        ):
            return (
                "Inspeção Dimensional"
            )

        if source_type == "ZEISS_INSPECT":
            if "VOLUM" in analysis_upper:
                return (
                    "Tomografia Computadorizada"
                )

            if "SUPERF" in analysis_upper:
                return (
                    "Escaneamento 3D"
                )

            return (
                "Relatório Geral"
            )

        if source_type == "CALYPSO":
            return (
                "Inspeção Dimensional"
            )

        return (
            "Relatório Geral"
        )

    # =============================================================
    # NOME SUGERIDO
    # =============================================================

    def suggest_project_name(
        self,
        part_name: str | None,
        template: str,
    ) -> str:
        prefix_map = {
            "Inspeção Dimensional":
                "Inspeção",

            "Inspeção Multissensor":
                "Inspeção multissensor",

            "Escaneamento 3D":
                "Escaneamento 3D",

            "Tomografia Computadorizada":
                "Tomografia",

            "Engenharia Reversa":
                "Engenharia reversa",

            "Relatório Geral":
                "Relatório",
        }

        prefix = prefix_map.get(
            template,
            "Relatório",
        )

        if part_name:
            return (
                f"{prefix} — {part_name}"
            )

        return prefix

    # =============================================================
    # AVISOS
    # =============================================================

    def _build_warnings(
        self,
        parsed,
        equipment: str | None,
        equipment_origin: str,
    ) -> list[str]:
        warnings = list(
            getattr(
                parsed,
                "warnings",
                [],
            )
            or []
        )

        if not parsed.part_name:
            self._append_warning_once(
                warnings,
                (
                    "Nome da peça não identificado "
                    "automaticamente."
                ),
            )

        if not equipment:
            self._append_warning_once(
                warnings,
                (
                    "Equipamento não identificado "
                    "automaticamente."
                ),
            )

        if (
            equipment
            and equipment_origin
            == "business_rule_inference"
        ):
            self._append_warning_once(
                warnings,
                (
                    "Equipamento sugerido pelo sistema "
                    "com base no tipo de análise."
                ),
            )

        if not parsed.characteristics:
            self._append_warning_once(
                warnings,
                (
                    "Nenhum resultado técnico "
                    "foi identificado."
                ),
            )

        return warnings

    def _append_warning_once(
        self,
        warnings: list[str],
        message: str,
    ) -> None:
        if message not in warnings:
            warnings.append(
                message
            )

    # =============================================================
    # PROVENIÊNCIA
    # =============================================================

    def _register_equipment_provenance(
        self,
        parsed,
        equipment: str | None,
        equipment_origin: str,
    ) -> None:
        extra_data = getattr(
            parsed,
            "extra_data",
            None,
        )

        if extra_data is None:
            return

        extra_data[
            "resolved_equipment"
        ] = equipment

        extra_data[
            "equipment_origin"
        ] = equipment_origin

    # =============================================================
    # CONFIANÇA
    # =============================================================

    def _get_extraction_confidence(
        self,
        parsed,
    ) -> float | None:
        validation = getattr(
            parsed,
            "validation",
            None,
        )

        if validation is not None:
            confidence = getattr(
                validation,
                "confidence",
                None,
            )

            if confidence is not None:
                return float(
                    confidence
                )

        extra_data = getattr(
            parsed,
            "extra_data",
            {},
        )

        confidence = extra_data.get(
            "source_detection_confidence"
        )

        if confidence is None:
            return None

        return float(
            confidence
        )

    # =============================================================
    # EXTRAÇÃO LEGADA
    # =============================================================

    def _find_legacy_extraction(
        self,
        project_id: int,
    ) -> Optional[ExtractedReport]:
        extractions = (
            self.extraction_repository
            .find_all_by_project_id(
                project_id
            )
        )

        for extraction in extractions:
            if extraction.document_id is None:
                return extraction

        return None

    # =============================================================
    # VALIDAÇÃO DO PDF
    # =============================================================

    def _validate_pdf_path(
        self,
        path: Path,
    ) -> None:
        if not path.exists():
            raise FileNotFoundError(
                "O arquivo selecionado não foi encontrado."
            )

        if not path.is_file():
            raise ValueError(
                (
                    "O caminho selecionado não corresponde "
                    "a um arquivo."
                )
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "Selecione um arquivo PDF."
            )

        if path.stat().st_size <= 0:
            raise ValueError(
                "O arquivo selecionado está vazio."
            )