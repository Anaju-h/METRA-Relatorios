from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Optional

from models.document_draft import DocumentDraft
from models.project_draft import ProjectDraft

from services.report_extraction_service import (
    ReportExtractionService,
)


class BatchAnalysisService:
    """
    Analisa um ou vários relatórios antes da criação do processo.

    Cada PDF continua sendo analisado individualmente pelo
    ReportExtractionService.

    Depois da extração, o METRA determina automaticamente se os
    documentos representam:

    - uma única peça física;
    - um lote de unidades do mesmo modelo.

    A decisão utiliza principalmente os nomes das peças e os
    identificadores individuais encontrados nos relatórios.
    """

    VALID_PROCESS_TYPES = {
        "single_piece",
        "batch",
    }

    def __init__(self):
        self.extraction_service = (
            ReportExtractionService()
        )

    # =============================================================
    # ANALISAR ARQUIVOS
    # =============================================================

    def analyze_files(
        self,
        source_paths: list[str],
        process_type: str | None = None,
        project_mode: str | None = None,
    ) -> ProjectDraft:
        clean_paths = self._normalize_paths(
            source_paths
        )

        if not clean_paths:
            raise ValueError(
                "Nenhum relatório foi selecionado."
            )

        requested_process_type = (
            process_type
            or self._convert_legacy_mode(
                project_mode
            )
        )

        if (
            requested_process_type is not None
            and requested_process_type
            not in self.VALID_PROCESS_TYPES
        ):
            raise ValueError(
                "Tipo de processo inválido."
            )

        documents: list[DocumentDraft] = []

        for order, source_path in enumerate(
            clean_paths,
            start=1,
        ):
            document = self._analyze_document(
                source_path=source_path,
                document_order=order,
            )

            documents.append(
                document
            )

        resolved_process_type = (
            requested_process_type
            or self._detect_process_type(
                documents
            )
        )

        project_draft = self._consolidate_documents(
            documents=documents,
            process_type=resolved_process_type,
        )

        project_draft.sync_legacy_fields()

        return project_draft

    # =============================================================
    # DETECÇÃO AUTOMÁTICA DO MODO
    # =============================================================

    def _detect_process_type(
        self,
        documents: list[DocumentDraft],
    ) -> str:
        """
        Determina automaticamente se os documentos representam
        uma peça única ou um lote.

        Regras principais:

        1. Um único documento -> peça única.

        2. Vários documentos com o mesmo nome completo de peça
           -> peça única.

        3. Vários documentos cujos nomes possuem a mesma base,
           mas identificadores finais diferentes
           -> lote.

        4. Quando a extração do nome não é suficiente, identificadores
           distintos encontrados nos documentos são usados como apoio.

        Em situações ambíguas, a opção conservadora é peça única.
        A revisão humana continua disponível na etapa seguinte.
        """

        analyzed = [
            document
            for document in documents
            if document.analyzed
        ]

        if len(analyzed) <= 1:
            return "single_piece"

        valid_names = [
            document.part_name.strip()
            for document in analyzed
            if document.part_name
            and document.part_name.strip()
        ]

        # ---------------------------------------------------------
        # NOMES COMPLETAMENTE IGUAIS
        # ---------------------------------------------------------

        if valid_names:
            normalized_names = {
                self._normalize_text(
                    name
                )
                for name in valid_names
            }

            if len(normalized_names) == 1:
                return "single_piece"

        # ---------------------------------------------------------
        # MESMA BASE + IDENTIFICADORES DIFERENTES
        # ---------------------------------------------------------

        if len(valid_names) >= 2:
            base_names = [
                self._remove_trailing_identifier(
                    name
                )
                for name in valid_names
            ]

            normalized_bases = {
                self._normalize_text(
                    base
                )
                for base in base_names
                if base
            }

            identifiers = [
                self._extract_trailing_identifier(
                    name
                )
                for name in valid_names
            ]

            valid_identifiers = self._unique_strings(
                [
                    identifier
                    for identifier in identifiers
                    if identifier
                ]
            )

            if (
                len(normalized_bases) == 1
                and len(valid_identifiers) >= 2
            ):
                return "batch"

        # ---------------------------------------------------------
        # IDENTIFICADORES DOS DOCUMENTOS
        # ---------------------------------------------------------

        document_identifiers = (
            self._unique_strings(
                [
                    document.specimen_identifier
                    for document in analyzed
                    if document.specimen_identifier
                ]
            )
        )

        if len(document_identifiers) >= 2:
            base_candidates = [
                self._remove_trailing_identifier(
                    document.part_name
                )
                for document in analyzed
                if document.part_name
            ]

            normalized_candidates = {
                self._normalize_text(
                    value
                )
                for value in base_candidates
                if value
            }

            if len(normalized_candidates) == 1:
                return "batch"

        # ---------------------------------------------------------
        # CASO AMBÍGUO
        # ---------------------------------------------------------

        return "single_piece"

    # =============================================================
    # ANALISAR UM DOCUMENTO
    # =============================================================

    def _analyze_document(
        self,
        source_path: str,
        document_order: int,
    ) -> DocumentDraft:
        path = Path(
            source_path
        )

        document = DocumentDraft(
            source_path=str(
                path
            ),
            file_name=path.name,
            document_order=document_order,
            specimen_identifier=(
                self._suggest_identifier_from_file_name(
                    path
                )
            ),
            analysis_status="Analisando",
        )

        try:
            extracted = (
                self.extraction_service
                .analyze_file(
                    str(path)
                )
            )

        except Exception as error:
            document.analysis_status = "Falha"

            document.analysis_error = str(
                error
            )

            document.warnings.append(
                "Não foi possível realizar a extração automática."
            )

            return document

        document.source_type = (
            extracted.source_type
        )

        document.part_name = (
            extracted.part_name
        )

        document.equipment = (
            extracted.equipment
        )

        document.machine_number = (
            extracted.machine_number
        )

        document.operator = (
            extracted.operator
        )

        document.measurement_datetime = (
            extracted.measurement_datetime
        )

        document.software_name = (
            extracted.software_name
        )

        document.software_version = (
            extracted.software_version
        )

        document.measurement_count = (
            extracted.measurement_count
        )

        document.out_of_tolerance_count = (
            extracted.out_of_tolerance_count
        )

        document.measurement_duration = (
            extracted.measurement_duration
        )

        document.suggested_template = (
            extracted.suggested_template
        )

        document.characteristics_count = (
            extracted.characteristics_count
        )

        document.parsed_report = (
            extracted.parsed_report
        )

        document.warnings = list(
            extracted.warnings
            or []
        )

        extracted_identifier = (
            self._extract_trailing_identifier(
                document.part_name
            )
        )

        if extracted_identifier:
            document.specimen_identifier = (
                extracted_identifier
            )

        elif not document.specimen_identifier:
            document.specimen_identifier = (
                f"{document_order:02d}"
            )

        document.analysis_status = "Concluído"

        return document

    # =============================================================
    # CONSOLIDAÇÃO
    # =============================================================

    def _consolidate_documents(
        self,
        documents: list[DocumentDraft],
        process_type: str,
    ) -> ProjectDraft:
        analyzed = [
            document
            for document in documents
            if document.analyzed
        ]

        failed = [
            document
            for document in documents
            if document.failed
        ]

        detected_part_names = (
            self._unique_original_values(
                document.part_name
                for document in analyzed
            )
        )

        (
            base_part_name,
            specimen_identifiers,
            part_compatibility,
        ) = self._resolve_part_information(
            documents=analyzed,
            process_type=process_type,
        )

        equipments = (
            self._unique_original_values(
                document.equipment
                for document in analyzed
            )
        )

        equipment = (
            equipments[0]
            if len(equipments) == 1
            else self._most_common_text(
                document.equipment
                for document in analyzed
            )
        )

        machine_number = self._most_common_text(
            document.machine_number
            for document in analyzed
        )

        operator = self._most_common_text(
            document.operator
            for document in analyzed
        )

        source_type = self._most_common_text(
            document.source_type
            for document in analyzed
        )

        software_name = self._most_common_text(
            document.software_name
            for document in analyzed
        )

        software_version = self._most_common_text(
            document.software_version
            for document in analyzed
        )

        suggested_template = (
            self._most_common_text(
                document.suggested_template
                for document in analyzed
            )
            or "Relatório Geral"
        )

        measurement_count = self._sum_optional_int(
            document.measurement_count
            for document in analyzed
        )

        out_of_tolerance_count = (
            self._sum_optional_int(
                document.out_of_tolerance_count
                for document in analyzed
            )
        )

        characteristics_count = sum(
            document.characteristics_count
            for document in analyzed
        )

        warnings = self._build_warnings(
            documents=documents,
            analyzed=analyzed,
            failed=failed,
            process_type=process_type,
            base_part_name=base_part_name,
            part_compatibility=part_compatibility,
            equipments=equipments,
        )

        suggested_project_name = (
            self._suggest_project_name(
                part_name=base_part_name,
                template=suggested_template,
                process_type=process_type,
            )
        )

        # Para lote, a quantidade representa unidades distintas.
        # Se não houver identificadores confiáveis, utiliza-se a
        # quantidade de documentos analisados como fallback.
        if process_type == "batch":
            specimen_count = (
                len(specimen_identifiers)
                if specimen_identifiers
                else len(analyzed)
            )
        else:
            specimen_count = (
                1
                if analyzed
                else 0
            )

        draft = ProjectDraft(
            process_type=process_type,
            documents=documents,
            source_type=source_type,
            base_part_name=base_part_name,
            part_name=base_part_name,
            detected_part_names=(
                detected_part_names
            ),
            specimen_identifiers=(
                specimen_identifiers
            ),
            specimen_count=specimen_count,
            equipment=equipment,
            equipments=equipments,
            machine_number=machine_number,
            operator=operator,
            measurement_datetime=(
                analyzed[0].measurement_datetime
                if len(analyzed) == 1
                else None
            ),
            software_name=software_name,
            software_version=software_version,
            measurement_count=measurement_count,
            out_of_tolerance_count=(
                out_of_tolerance_count
            ),
            measurement_duration=(
                analyzed[0].measurement_duration
                if len(analyzed) == 1
                else None
            ),
            suggested_template=(
                suggested_template
            ),
            suggested_project_name=(
                suggested_project_name
            ),
            characteristics_count=(
                characteristics_count
            ),
            part_compatibility=(
                part_compatibility
            ),
            warnings=warnings,
        )

        return draft

    # =============================================================
    # IDENTIFICAÇÃO DO NOME-BASE
    # =============================================================

    def _resolve_part_information(
        self,
        documents: list[DocumentDraft],
        process_type: str,
    ) -> tuple[
        Optional[str],
        list[str],
        str,
    ]:
        valid_names = [
            document.part_name.strip()
            for document in documents
            if document.part_name
            and document.part_name.strip()
        ]

        if not valid_names:
            return (
                None,
                [],
                "variation",
            )

        if process_type == "single_piece":
            return self._resolve_single_piece_names(
                valid_names
            )

        return self._resolve_batch_names(
            valid_names
        )

    def _resolve_single_piece_names(
        self,
        names: list[str],
    ) -> tuple[
        Optional[str],
        list[str],
        str,
    ]:
        normalized_names = {
            self._normalize_text(
                name
            )
            for name in names
        }

        if len(normalized_names) == 1:
            return (
                names[0],
                [],
                "compatible",
            )

        base_names = [
            self._remove_trailing_identifier(
                name
            )
            for name in names
        ]

        normalized_bases = {
            self._normalize_text(
                base
            )
            for base in base_names
            if base
        }

        if len(normalized_bases) == 1:
            return (
                base_names[0],
                self._collect_trailing_identifiers(
                    names
                ),
                "variation",
            )

        return (
            self._most_common_text(
                names
            ),
            [],
            "incompatible",
        )

    def _resolve_batch_names(
        self,
        names: list[str],
    ) -> tuple[
        Optional[str],
        list[str],
        str,
    ]:
        analyzed_names = []

        for name in names:
            base_name = (
                self._remove_trailing_identifier(
                    name
                )
            )

            identifier = (
                self._extract_trailing_identifier(
                    name
                )
            )

            analyzed_names.append(
                (
                    name,
                    base_name,
                    identifier,
                )
            )

        normalized_bases = [
            self._normalize_text(
                base_name
            )
            for (
                _,
                base_name,
                _,
            ) in analyzed_names
            if base_name
        ]

        if not normalized_bases:
            return (
                self._most_common_text(
                    names
                ),
                [],
                "variation",
            )

        counts = Counter(
            normalized_bases
        )

        main_normalized_base = max(
            counts,
            key=lambda value: (
                counts[value],
                len(value),
            ),
        )

        base_part_name = next(
            base_name
            for (
                _,
                base_name,
                _,
            ) in analyzed_names
            if (
                self._normalize_text(
                    base_name
                )
                == main_normalized_base
            )
        )

        identifiers = []
        incompatible_count = 0

        for (
            _,
            base_name,
            identifier,
        ) in analyzed_names:
            normalized_base = (
                self._normalize_text(
                    base_name
                )
            )

            similarity = (
                self._token_similarity(
                    main_normalized_base,
                    normalized_base,
                )
            )

            if similarity < 0.50:
                incompatible_count += 1

            if identifier:
                identifiers.append(
                    identifier
                )

        identifiers = self._unique_strings(
            identifiers
        )

        if incompatible_count > 0:
            compatibility = "incompatible"

        elif len(counts) > 1:
            compatibility = "variation"

        else:
            compatibility = "compatible"

        return (
            base_part_name,
            identifiers,
            compatibility,
        )

    # =============================================================
    # AVISOS
    # =============================================================

    def _build_warnings(
        self,
        documents: list[DocumentDraft],
        analyzed: list[DocumentDraft],
        failed: list[DocumentDraft],
        process_type: str,
        base_part_name: Optional[str],
        part_compatibility: str,
        equipments: list[str],
    ) -> list[str]:
        warnings: list[str] = []

        if failed:
            warnings.append(
                (
                    f"{len(failed)} de {len(documents)} documento(s) "
                    "não puderam ser analisados automaticamente."
                )
            )

        if not analyzed:
            warnings.append(
                "Nenhum documento foi analisado automaticamente."
            )
            return warnings

        if not base_part_name:
            warnings.append(
                "O nome da peça não foi identificado nos documentos."
            )

        if (
            process_type == "single_piece"
            and part_compatibility == "variation"
        ):
            warnings.append(
                (
                    "Foram encontradas variações no nome da peça. "
                    "Confirme se todos os relatórios pertencem à "
                    "mesma peça física."
                )
            )

        if part_compatibility == "incompatible":
            warnings.append(
                (
                    "Os documentos parecem pertencer a peças "
                    "diferentes. Revise os arquivos antes de criar "
                    "o processo."
                )
            )

        if len(equipments) > 1:
            warnings.append(
                (
                    "Foram identificados equipamentos diferentes "
                    "entre os documentos."
                )
            )

        source_values = self._distinct_text_values(
            document.source_type
            for document in analyzed
        )

        if len(source_values) > 1:
            warnings.append(
                (
                    "O processo contém relatórios de famílias "
                    "documentais diferentes."
                )
            )

        characteristic_counts = {
            document.characteristics_count
            for document in analyzed
            if document.characteristics_count > 0
        }

        if len(characteristic_counts) > 1:
            warnings.append(
                (
                    "Os documentos possuem quantidades diferentes "
                    "de características."
                )
            )

        if all(
            document.characteristics_count == 0
            for document in analyzed
        ):
            warnings.append(
                (
                    "Nenhuma característica detalhada foi extraída. "
                    "Os dados gerais dos relatórios foram identificados."
                )
            )

        return warnings

    # =============================================================
    # NOME SUGERIDO
    # =============================================================

    def _suggest_project_name(
        self,
        part_name: Optional[str],
        template: str,
        process_type: str,
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

        if process_type == "batch":
            prefix = "Inspeção em lote"

        if part_name:
            return (
                f"{prefix} — {part_name}"
            )

        return prefix

    # =============================================================
    # IDENTIFICADORES
    # =============================================================

    def _suggest_identifier_from_file_name(
        self,
        path: Path,
    ) -> Optional[str]:
        match = re.search(
            r"(\d+)(?!.*\d)",
            path.stem,
        )

        if not match:
            return None

        return match.group(1)

    def _extract_trailing_identifier(
        self,
        value: Optional[str],
    ) -> Optional[str]:
        if not value:
            return None

        clean = value.strip()

        patterns = (
            r"(?:PECA|PEÇA|AMOSTRA|UNIDADE|PARTE|ITEM)\s*[-_:]?\s*(\d+)$",
            r"[-_/#]\s*(\d+)$",
            r"\s+(\d+)$",
        )

        normalized = self._remove_accents(
            clean
        ).upper()

        for pattern in patterns:
            match = re.search(
                pattern,
                normalized,
            )

            if match:
                return match.group(1)

        return None

    def _remove_trailing_identifier(
        self,
        value: str,
    ) -> str:
        clean = " ".join(
            value.strip().split()
        )

        patterns = (
            r"\s+(?:PECA|PEÇA|AMOSTRA|UNIDADE|PARTE|ITEM)"
            r"\s*[-_:]?\s*\d+$",
            r"\s*[-_/#]\s*\d+$",
            r"\s+\d+$",
        )

        result = clean

        for pattern in patterns:
            result = re.sub(
                pattern,
                "",
                result,
                flags=re.IGNORECASE,
            ).strip()

        return result or clean

    def _collect_trailing_identifiers(
        self,
        names: list[str],
    ) -> list[str]:
        identifiers = []

        for name in names:
            identifier = (
                self._extract_trailing_identifier(
                    name
                )
            )

            if identifier:
                identifiers.append(
                    identifier
                )

        return self._unique_strings(
            identifiers
        )

    # =============================================================
    # COMPATIBILIDADE TEXTUAL
    # =============================================================

    def _token_similarity(
        self,
        first: str,
        second: str,
    ) -> float:
        first_tokens = set(
            first.split()
        )

        second_tokens = set(
            second.split()
        )

        if not first_tokens or not second_tokens:
            return 0.0

        intersection = (
            first_tokens
            & second_tokens
        )

        union = (
            first_tokens
            | second_tokens
        )

        return (
            len(intersection)
            / len(union)
        )

    # =============================================================
    # HELPERS
    # =============================================================

    def _convert_legacy_mode(
        self,
        project_mode: Optional[str],
    ) -> Optional[str]:
        if project_mode == "package":
            return "batch"

        if project_mode == "individual":
            return "single_piece"

        if project_mode in self.VALID_PROCESS_TYPES:
            return project_mode

        return None

    def _normalize_paths(
        self,
        source_paths: list[str],
    ) -> list[str]:
        result = []
        seen = set()

        for source_path in (
            source_paths
            or []
        ):
            path = Path(
                source_path
            )

            key = str(
                path.resolve()
            ).lower()

            if key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                str(path)
            )

        return result

    def _most_common_text(
        self,
        values: Iterable[
            Optional[str]
        ],
    ) -> Optional[str]:
        original_by_key = {}
        normalized_values = []

        for value in values:
            if not value:
                continue

            clean = value.strip()

            if not clean:
                continue

            key = self._normalize_text(
                clean
            )

            if not key:
                continue

            normalized_values.append(
                key
            )

            original_by_key.setdefault(
                key,
                clean,
            )

        if not normalized_values:
            return None

        counts = Counter(
            normalized_values
        )

        best_key = max(
            counts,
            key=lambda key: (
                counts[key],
                len(key),
            ),
        )

        return original_by_key[
            best_key
        ]

    def _unique_original_values(
        self,
        values: Iterable[
            Optional[str]
        ],
    ) -> list[str]:
        result = []
        seen = set()

        for value in values:
            if not value:
                continue

            clean = value.strip()

            if not clean:
                continue

            normalized = self._normalize_text(
                clean
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            result.append(
                clean
            )

        return result

    def _distinct_text_values(
        self,
        values: Iterable[
            Optional[str]
        ],
    ) -> set[str]:
        return {
            self._normalize_text(
                value
            )
            for value in values
            if value
            and self._normalize_text(
                value
            )
        }

    def _sum_optional_int(
        self,
        values: Iterable[
            Optional[int]
        ],
    ) -> Optional[int]:
        valid_values = [
            value
            for value in values
            if value is not None
        ]

        if not valid_values:
            return None

        return sum(
            valid_values
        )

    def _unique_strings(
        self,
        values: list[str],
    ) -> list[str]:
        result = []
        seen = set()

        for value in values:
            key = value.strip().lower()

            if not key or key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                value.strip()
            )

        return result

    def _normalize_text(
        self,
        value: str,
    ) -> str:
        normalized = self._remove_accents(
            value or ""
        )

        normalized = re.sub(
            r"[^A-Za-z0-9]+",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return (
            normalized
            .strip()
            .lower()
        )

    def _remove_accents(
        self,
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            value or "",
        )

        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )