from __future__ import annotations

from typing import Any

from models.project import Project
from repositories.characteristic_repository import (
    CharacteristicRepository,
)

from services.image_service import (
    ImageService,
)
from services.measurement_service import (
    MeasurementService,
)
from services.pdf_service import (
    PDFService,
)
from services.report_extraction_service import (
    ReportExtractionService,
)
from services.technical_control_service import (
    TechnicalControlService,
)


class FinalReportService:
    """
    Consolida os dados necessários para preparar
    o relatório técnico geral da peça ou do lote.

    Para processos em lote, o resultado continua sendo
    um único relatório consolidado.
    """

    STATUS_OK = "OK"
    STATUS_NOK = "NOK"
    STATUS_UNKNOWN = "UNKNOWN"

    def __init__(self):
        self.pdf_service = (
            PDFService()
        )

        self.extraction_service = (
            ReportExtractionService()
        )

        self.measurement_service = (
            MeasurementService()
        )

        self.image_service = (
            ImageService()
        )

        self.technical_control_service = (
            TechnicalControlService()
        )

        self.characteristic_repository = (
            CharacteristicRepository()
        )

    # =============================================================
    # CONTEXTO COMPLETO
    # =============================================================

    def get_report_context(
        self,
        project: Project,
    ) -> dict[str, Any]:
        if project.id is None:
            raise ValueError(
                (
                    "O processo não possui "
                    "um identificador válido."
                )
            )

        documents = (
            self.pdf_service
            .get_project_documents(
                project.id
            )
        )

        extraction_pairs = (
            self.extraction_service
            .get_project_extractions(
                project.id
            )
        )

        measurement = (
            self.measurement_service
            .get_measurement(
                project.id
            )
        )

        images = (
            self.image_service
            .get_project_images(
                project.id
            )
        )

        primary_image = (
            self.image_service
            .get_primary_image(
                project.id
            )
        )

        technical_control = (
            self.technical_control_service
            .get_control(
                project.id
            )
        )

        characteristics = (
            self.characteristic_repository
            .find_by_project_id(
                project.id
            )
        )

        document_summary = (
            self._build_document_summary(
                documents
            )
        )

        characteristic_summary = (
            self._build_characteristic_summary(
                characteristics
            )
        )

        measurement_summary = (
            self._build_measurement_summary(
                measurement
            )
        )

        image_summary = (
            self._build_image_summary(
                images=images,
                primary_image=primary_image,
            )
        )

        control_summary = (
            self._build_control_summary(
                technical_control
            )
        )

        is_batch = (
            len(
                documents
            ) > 1
        )

        validation_items = [
            self._build_validation_item(
                key="documents",

                title="Documentos de origem",

                available=(
                    document_summary[
                        "total"
                    ] > 0
                ),

                complete=(
                    document_summary[
                        "total"
                    ] > 0
                    and document_summary[
                        "analyzed"
                    ]
                    == document_summary[
                        "total"
                    ]
                ),

                success_message=(
                    f"{document_summary['total']} "
                    "documento(s) adicionado(s) "
                    "e analisado(s)."
                ),

                pending_message=(
                    self._document_pending_message(
                        document_summary
                    )
                ),

                required=False,
            ),

            self._build_validation_item(
                key="characteristics",

                title=(
                    "Características metrológicas"
                ),

                available=(
                    characteristic_summary[
                        "total"
                    ] > 0
                ),

                complete=(
                    characteristic_summary[
                        "total"
                    ] > 0
                ),

                success_message=(
                    f"{characteristic_summary['total']} "
                    "característica(s) estruturada(s)."
                ),

                pending_message=(
                    "Nenhuma característica foi cadastrada "
                    "ou identificada no processo."
                ),

                required=False,
            ),

            self._build_validation_item(
                key="measurement",

                title="Informações da medição",

                available=(
                    measurement is not None
                ),

                complete=(
                    measurement_summary[
                        "complete"
                    ]
                ),

                success_message=(
                    "Os dados principais da medição "
                    "foram preenchidos."
                ),

                pending_message=(
                    measurement_summary[
                        "pending_message"
                    ]
                ),

                required=False,
            ),

            self._build_validation_item(
                key="images",

                title="Imagens técnicas",

                available=(
                    image_summary[
                        "total"
                    ] > 0
                ),

                complete=(
                    image_summary[
                        "total"
                    ] > 0
                ),

                success_message=(
                    f"{image_summary['total']} imagem(ns) "
                    "disponível(is) para o relatório."
                ),

                pending_message=(
                    "Nenhuma imagem técnica "
                    "foi adicionada."
                ),

                required=False,
            ),

            self._build_validation_item(
                key="primary_image",

                title=(
                    "Imagem principal da peça/lote"
                ),

                available=(
                    primary_image is not None
                ),

                complete=(
                    primary_image is not None
                ),

                success_message=(
                    "A imagem principal da visão geral "
                    "foi definida."
                ),

                pending_message=(
                    "Selecione uma imagem para representar "
                    "a peça ou o lote na primeira página."
                ),

                required=False,
            ),

            self._build_validation_item(
                key="technical_control",

                title="Controle técnico",

                available=(
                    technical_control is not None
                ),

                complete=(
                    control_summary[
                        "complete"
                    ]
                ),

                success_message=(
                    control_summary[
                        "success_message"
                    ]
                ),

                pending_message=(
                    control_summary[
                        "pending_message"
                    ]
                ),

                required=True,
            ),
        ]

        blocking_items = [
            item
            for item in validation_items
            if (
                item[
                    "required"
                ]
                and not item[
                    "complete"
                ]
            )
        ]

        warning_items = [
            item
            for item in validation_items
            if (
                not item[
                    "required"
                ]
                and not item[
                    "complete"
                ]
            )
        ]

        has_observations = (
            self._has_observations(
                measurement=measurement,
                technical_control=(
                    technical_control
                ),
            )
        )

        available_sections = {
            "cover":
                False,

            "process_summary":
                True,

            "documents":
                bool(
                    documents
                ),

            "measurement":
                measurement is not None,

            "characteristics":
                bool(
                    characteristics
                ),

            "images":
                bool(
                    images
                ),

            "technical_control":
                technical_control is not None,

            "observations":
                has_observations,
        }

        default_sections = {
            "cover":
                False,

            "process_summary":
                True,

            "documents":
                bool(
                    documents
                ),

            "measurement":
                measurement is not None,

            "characteristics":
                bool(
                    characteristics
                ),

            "images":
                bool(
                    images
                ),

            "technical_control":
                technical_control is not None,

            "observations":
                has_observations,
        }

        return {
            "project":
                project,

            "is_batch":
                is_batch,

            "report_scope":
                (
                    "lote"
                    if is_batch
                    else "peça única"
                ),

            "documents":
                documents,

            "extractions":
                extraction_pairs,

            "characteristics":
                characteristics,

            "measurement":
                measurement,

            "images":
                images,

            "primary_image":
                primary_image,

            "technical_control":
                technical_control,

            "document_summary":
                document_summary,

            "characteristic_summary":
                characteristic_summary,

            "measurement_summary":
                measurement_summary,

            "image_summary":
                image_summary,

            "control_summary":
                control_summary,

            "validation_items":
                validation_items,

            "blocking_items":
                blocking_items,

            "warning_items":
                warning_items,

            "available_sections":
                available_sections,

            "default_sections":
                default_sections,

            # A pré-visualização nunca é bloqueada pela ausência
            # de módulos opcionais. O relatório usa apenas o conteúdo
            # que estiver disponível no processo.
            "can_preview":
                True,

            # A emissão/exportação oficial exige exclusivamente
            # a aprovação válida do Controle Técnico.
            "can_export":
                bool(
                    control_summary[
                        "complete"
                    ]
                ),

            # Compatibilidade temporária com pontos antigos do sistema.
            # Representa capacidade de gerar a prévia, não de exportar.
            "can_generate":
                True,
        }

    # =============================================================
    # DOCUMENTOS
    # =============================================================

    def _build_document_summary(
        self,
        documents,
    ) -> dict[str, Any]:
        total = len(
            documents
        )

        analyzed = 0
        failed = 0
        pending = 0
        pages = 0

        source_types: list[
            str
        ] = []

        unit_identifiers: list[
            str
        ] = []

        for document in documents:
            status = str(
                getattr(
                    document,
                    "analysis_status",
                    "",
                )
                or ""
            ).strip().lower()

            if status in {
                "concluído",
                "concluido",
                "analisado",
            }:
                analyzed += 1

            elif status == "falha":
                failed += 1

            else:
                pending += 1

            pages += int(
                getattr(
                    document,
                    "page_count",
                    0,
                )
                or 0
            )

            source_type = str(
                getattr(
                    document,
                    "source_type",
                    "",
                )
                or ""
            ).strip()

            if (
                source_type
                and source_type.upper()
                != "UNKNOWN"
                and source_type
                not in source_types
            ):
                source_types.append(
                    source_type
                )

            identifier = str(
                getattr(
                    document,
                    "specimen_identifier",
                    "",
                )
                or ""
            ).strip()

            if (
                identifier
                and identifier
                not in unit_identifiers
            ):
                unit_identifiers.append(
                    identifier
                )

        return {
            "total":
                total,

            "analyzed":
                analyzed,

            "failed":
                failed,

            "pending":
                pending,

            "pages":
                pages,

            "source_types":
                source_types,

            "unit_count":
                len(
                    unit_identifiers
                )
                if unit_identifiers
                else total,

            "unit_identifiers":
                unit_identifiers,
        }

    def _document_pending_message(
        self,
        summary: dict[str, Any],
    ) -> str:
        if summary[
            "total"
        ] == 0:
            return (
                "Nenhum documento foi "
                "adicionado ao processo."
            )

        parts = []

        if summary[
            "pending"
        ] > 0:
            parts.append(
                (
                    f"{summary['pending']} "
                    "documento(s) pendente(s)"
                )
            )

        if summary[
            "failed"
        ] > 0:
            parts.append(
                (
                    f"{summary['failed']} "
                    "documento(s) com falha"
                )
            )

        if not parts:
            return (
                "Os documentos ainda não foram "
                "completamente analisados."
            )

        return " · ".join(
            parts
        )

    # =============================================================
    # CARACTERÍSTICAS
    # =============================================================

    def _build_characteristic_summary(
        self,
        characteristics,
    ) -> dict[str, Any]:
        total = len(
            characteristics
        )

        ok = 0
        nok = 0
        unknown = 0

        groups: list[str] = []
        units: list[str] = []

        for characteristic in characteristics:
            status = (
                self._normalize_status(
                    characteristic.status
                )
            )

            if status == self.STATUS_OK:
                ok += 1

            elif status == self.STATUS_NOK:
                nok += 1

            else:
                unknown += 1

            group = str(
                characteristic.group_name
                or ""
            ).strip()

            if (
                group
                and group not in groups
            ):
                groups.append(
                    group
                )

            unit = str(
                characteristic.unit
                or ""
            ).strip()

            if (
                unit
                and unit not in units
            ):
                units.append(
                    unit
                )

        conformity_percentage = (
            (
                ok / total
            ) * 100.0
            if total > 0
            else 0.0
        )

        return {
            "total":
                total,

            "ok":
                ok,

            "nok":
                nok,

            "unknown":
                unknown,

            "groups":
                groups,

            "units":
                units,

            "conformity_percentage":
                conformity_percentage,
        }

    # =============================================================
    # MEDIÇÃO
    # =============================================================

    def _build_measurement_summary(
        self,
        measurement,
    ) -> dict[str, Any]:
        if measurement is None:
            return {
                "complete":
                    False,

                "filled_fields":
                    0,

                "total_fields":
                    8,

                "pending_message":
                    (
                        "As informações da medição "
                        "ainda não foram preenchidas."
                    ),
            }

        relevant_values = [
            measurement.responsible,
            measurement.measurement_datetime,
            measurement.drawing_reference,
            measurement.alignment,
            measurement.fixture,
            measurement.machine_details,
            measurement.accessories,
            measurement.special_instructions,
        ]

        filled_fields = sum(
            1
            for value in relevant_values
            if str(
                value
                or ""
            ).strip()
        )

        complete = filled_fields > 0

        if complete:
            pending_message = (
                f"{filled_fields} informação(ões) de medição "
                "disponível(is) para o relatório."
            )
        else:
            pending_message = (
                "Nenhuma informação de medição foi preenchida. "
                "Isso não impede a geração do relatório."
            )

        return {
            "complete":
                complete,

            "filled_fields":
                filled_fields,

            "total_fields":
                len(
                    relevant_values
                ),

            "pending_message":
                pending_message,
        }

    # =============================================================
    # IMAGENS
    # =============================================================

    def _build_image_summary(
        self,
        images,
        primary_image,
    ) -> dict[str, Any]:
        total = len(
            images
        )

        with_caption = sum(
            1
            for image in images
            if str(
                image.caption
                or ""
            ).strip()
        )

        image_types: list[
            str
        ] = []

        for image in images:
            image_type = str(
                image.image_type
                or ""
            ).strip()

            if (
                image_type
                and image_type
                not in image_types
            ):
                image_types.append(
                    image_type
                )

        return {
            "total":
                total,

            "with_caption":
                with_caption,

            "without_caption":
                total
                - with_caption,

            "image_types":
                image_types,

            "has_primary":
                primary_image
                is not None,

            "primary_image_id":
                (
                    primary_image.id
                    if primary_image
                    is not None
                    else None
                ),

            "primary_image_name":
                (
                    primary_image.file_name
                    if primary_image
                    is not None
                    else None
                ),
        }

    # =============================================================
    # CONTROLE TÉCNICO
    # =============================================================

    def _build_control_summary(
        self,
        control,
    ) -> dict[str, Any]:
        if control is None:
            return {
                "complete":
                    False,

                "status":
                    "Não iniciado",

                "success_message":
                    "",

                "pending_message":
                    (
                        "O controle técnico ainda "
                        "não foi preenchido."
                    ),
            }

        status = str(
            control.status
            or "Em elaboração"
        ).strip()

        has_prepared_by = bool(
            str(
                control.prepared_by
                or ""
            ).strip()
        )

        has_reviewed_by = bool(
            str(
                control.reviewed_by
                or ""
            ).strip()
        )

        complete = (
            status == "Aprovado"
            and has_prepared_by
            and has_reviewed_by
        )

        if complete:
            success_message = (
                "Relatório aprovado por "
                f"{control.reviewed_by}."
            )

            pending_message = ""

        elif not has_prepared_by:
            success_message = ""

            pending_message = (
                "Informe o responsável "
                "pela elaboração."
            )

        elif status == "Em elaboração":
            success_message = ""

            pending_message = (
                "O relatório ainda está "
                "em elaboração."
            )

        elif status == "Aguardando revisão":
            success_message = ""

            pending_message = (
                "O relatório está aguardando "
                "revisão técnica."
            )

        elif status == "Revisado":
            success_message = ""

            pending_message = (
                "O relatório foi revisado, "
                "mas ainda não foi aprovado."
            )

        elif not has_reviewed_by:
            success_message = ""

            pending_message = (
                "Informe o responsável pela "
                "revisão ou aprovação."
            )

        else:
            success_message = ""

            pending_message = (
                "Conclua o controle técnico "
                "antes da emissão."
            )

        return {
            "complete":
                complete,

            "status":
                status,

            "prepared_by":
                control.prepared_by,

            "reviewed_by":
                control.reviewed_by,

            "success_message":
                success_message,

            "pending_message":
                pending_message,
        }

    # =============================================================
    # VALIDAÇÃO
    # =============================================================

    def _build_validation_item(
        self,
        key: str,
        title: str,
        available: bool,
        complete: bool,
        success_message: str,
        pending_message: str,
        required: bool,
    ) -> dict[str, Any]:
        if complete:
            status = "complete"
            message = success_message

        elif available:
            status = "pending"
            message = pending_message

        else:
            status = "missing"
            message = pending_message

        return {
            "key":
                key,

            "title":
                title,

            "available":
                available,

            "complete":
                complete,

            "required":
                required,

            "status":
                status,

            "message":
                message,
        }

    # =============================================================
    # OBSERVAÇÕES
    # =============================================================

    def _has_observations(
        self,
        measurement,
        technical_control,
    ) -> bool:
        measurement_notes = bool(
            measurement
            and str(
                measurement.special_instructions
                or ""
            ).strip()
        )

        review_notes = bool(
            technical_control
            and str(
                technical_control.review_notes
                or ""
            ).strip()
        )

        return (
            measurement_notes
            or review_notes
        )

    # =============================================================
    # STATUS
    # =============================================================

    def _normalize_status(
        self,
        value,
    ) -> str:
        normalized = str(
            value
            or ""
        ).strip().upper()

        if normalized in {
            "OK",
            "PASS",
            "APPROVED",
            "CONFORME",
        }:
            return self.STATUS_OK

        if normalized in {
            "NOK",
            "FAIL",
            "FAILED",
            "REJECTED",
            "NÃO CONFORME",
            "NAO CONFORME",
        }:
            return self.STATUS_NOK

        return self.STATUS_UNKNOWN