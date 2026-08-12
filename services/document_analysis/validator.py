from __future__ import annotations

from services.document_analysis.models import (
    ParsedReport,
    ValidationIssue,
    ValidationResult,
)


class DocumentValidator:
    """
    Valida a coerência dos dados extraídos.

    O objetivo não é afirmar que a medição está tecnicamente correta.

    O objetivo é avaliar se a EXTRAÇÃO parece:
    - completa;
    - coerente;
    - confiável.

    Portanto o validator não substitui revisão metrológica.
    """

    # =============================================================
    # VALIDAR
    # =============================================================

    def validate(
        self,
        report: ParsedReport,
    ) -> ValidationResult:
        result = ValidationResult(
            is_valid=True,
            confidence=1.0,
        )

        # ---------------------------------------------------------
        # DOCUMENTO
        # ---------------------------------------------------------

        self._validate_document(
            report=report,
            result=result,
        )

        # ---------------------------------------------------------
        # IDENTIFICAÇÃO
        # ---------------------------------------------------------

        self._validate_identification(
            report=report,
            result=result,
        )

        # ---------------------------------------------------------
        # RESULTADOS
        # ---------------------------------------------------------

        self._validate_characteristics(
            report=report,
            result=result,
        )

        # ---------------------------------------------------------
        # COERÊNCIA DE CONTAGENS
        # ---------------------------------------------------------

        self._validate_counts(
            report=report,
            result=result,
        )

        # ---------------------------------------------------------
        # STATUS
        # ---------------------------------------------------------

        self._validate_status_consistency(
            report=report,
            result=result,
        )

        # ---------------------------------------------------------
        # CONFIANÇA FINAL
        # ---------------------------------------------------------

        result.confidence = (
            self._calculate_confidence(
                report=report,
                validation=result,
            )
        )

        if (
            result.confidence
            < 0.45
        ):
            result.is_valid = False

            result.add_issue(
                ValidationIssue(
                    code=(
                        "LOW_EXTRACTION_CONFIDENCE"
                    ),

                    message=(
                        "A extração apresentou baixa confiança geral "
                        "e deve ser revisada antes de ser utilizada."
                    ),

                    severity="error",
                )
            )

        elif (
            result.confidence
            < 0.70
        ):
            result.add_issue(
                ValidationIssue(
                    code=(
                        "REVIEW_RECOMMENDED"
                    ),

                    message=(
                        "A extração foi concluída, mas recomenda-se "
                        "revisão dos dados identificados."
                    ),

                    severity="warning",
                )
            )

        return result

    # =============================================================
    # DOCUMENTO
    # =============================================================

    def _validate_document(
        self,
        report: ParsedReport,
        result: ValidationResult,
    ) -> None:
        if report.page_count <= 0:
            result.add_issue(
                ValidationIssue(
                    code="INVALID_PAGE_COUNT",

                    message=(
                        "O documento não possui páginas válidas."
                    ),

                    severity="error",
                )
            )

        if not report.source_type:
            result.add_issue(
                ValidationIssue(
                    code="UNKNOWN_SOURCE",

                    message=(
                        "A origem do documento não foi identificada."
                    ),

                    severity="warning",
                )
            )

    # =============================================================
    # IDENTIFICAÇÃO
    # =============================================================

    def _validate_identification(
        self,
        report: ParsedReport,
        result: ValidationResult,
    ) -> None:
        if not report.part_name:
            result.add_issue(
                ValidationIssue(
                    code="PART_NOT_FOUND",

                    message=(
                        "O nome da peça não foi identificado "
                        "automaticamente."
                    ),

                    severity="warning",

                    field="part_name",
                )
            )

        # CALYPSO normalmente possui MMC explícita.
        if (
            report.source_type
            == "CALYPSO"
            and not report.machine_name
        ):
            result.add_issue(
                ValidationIssue(
                    code="MACHINE_NOT_FOUND",

                    message=(
                        "O equipamento de medição não foi identificado "
                        "no relatório CALYPSO."
                    ),

                    severity="warning",

                    field="machine_name",
                )
            )

        # INSPECT não precisa obrigatoriamente informar máquina.
        # Portanto NÃO geramos erro nesse caso.

    # =============================================================
    # CARACTERÍSTICAS
    # =============================================================

    def _validate_characteristics(
        self,
        report: ParsedReport,
        result: ValidationResult,
    ) -> None:
        count = len(
            report.characteristics
        )

        if count == 0:
            result.add_issue(
                ValidationIssue(
                    code="NO_RESULTS_FOUND",

                    message=(
                        "Nenhum resultado técnico foi identificado "
                        "automaticamente no documento."
                    ),

                    severity="warning",
                )
            )

            return

        low_confidence = [
            item
            for item
            in report.characteristics
            if item.confidence
            < 0.55
        ]

        if low_confidence:
            result.add_issue(
                ValidationIssue(
                    code=(
                        "LOW_CONFIDENCE_RESULTS"
                    ),

                    message=(
                        f"{len(low_confidence)} resultado(s) "
                        "foram identificados com baixa confiança."
                    ),

                    severity="warning",
                )
            )

    # =============================================================
    # CONTAGENS
    # =============================================================

    def _validate_counts(
        self,
        report: ParsedReport,
        result: ValidationResult,
    ) -> None:
        expected = (
            report.measurement_count
        )

        extracted = len(
            report.characteristics
        )

        if (
            expected is None
            or expected <= 0
        ):
            return

        if extracted == 0:
            result.add_issue(
                ValidationIssue(
                    code=(
                        "MEASUREMENT_COUNT_WITHOUT_RESULTS"
                    ),

                    message=(
                        f"O relatório informa {expected} medição(ões), "
                        "mas nenhum resultado foi extraído."
                    ),

                    severity="warning",
                )
            )

            return

        ratio = (
            extracted
            / expected
        )

        # Importante:
        #
        # measurement_count nem sempre corresponde diretamente
        # à quantidade de linhas da tabela.
        #
        # Portanto NÃO tratamos diferença como erro automático.
        #
        # Apenas detectamos diferenças muito grandes.

        if ratio < 0.30:
            result.add_issue(
                ValidationIssue(
                    code=(
                        "POSSIBLE_INCOMPLETE_EXTRACTION"
                    ),

                    message=(
                        f"O documento informa {expected} medição(ões), "
                        f"mas apenas {extracted} resultado(s) foram "
                        "identificados. A extração pode estar incompleta."
                    ),

                    severity="warning",
                )
            )

    # =============================================================
    # STATUS
    # =============================================================

    def _validate_status_consistency(
        self,
        report: ParsedReport,
        result: ValidationResult,
    ) -> None:
        expected_out = (
            report.out_of_tolerance_count
        )

        if (
            expected_out is None
            or expected_out < 0
        ):
            return

        known_status = [
            item
            for item
            in report.characteristics
            if item.status
            in (
                "OK",
                "OUT",
            )
        ]

        if not known_status:
            return

        extracted_out = sum(
            1
            for item
            in known_status
            if item.status
            == "OUT"
        )

        # Não exigimos igualdade absoluta porque:
        #
        # - uma característica pode gerar mais de uma linha;
        # - o relatório pode resumir medições de outra forma;
        # - nem todo resultado permite reconstruir status.
        #
        # Só avisamos quando há diferença muito expressiva.

        if (
            expected_out > 0
            and extracted_out == 0
        ):
            result.add_issue(
                ValidationIssue(
                    code=(
                        "OUT_COUNT_CONFLICT"
                    ),

                    message=(
                        f"O documento informa {expected_out} ocorrência(s) "
                        "fora da tolerância, mas nenhuma foi reconstruída "
                        "nos resultados extraídos."
                    ),

                    severity="warning",
                )
            )

    # =============================================================
    # CONFIANÇA
    # =============================================================

    def _calculate_confidence(
        self,
        report: ParsedReport,
        validation: ValidationResult,
    ) -> float:
        score = 1.0

        # ---------------------------------------------------------
        # CAMPOS EXTRAÍDOS
        # ---------------------------------------------------------

        field_confidences = [
            field.confidence
            for field
            in report.fields.values()
            if field.found
        ]

        if field_confidences:
            average_fields = (
                sum(
                    field_confidences
                )
                / len(
                    field_confidences
                )
            )

            score = (
                score * 0.55
                + average_fields * 0.45
            )

        # ---------------------------------------------------------
        # RESULTADOS
        # ---------------------------------------------------------

        if report.characteristics:
            characteristic_confidence = (
                sum(
                    item.confidence
                    for item
                    in report.characteristics
                )
                / len(
                    report.characteristics
                )
            )

            score = (
                score * 0.60
                + characteristic_confidence
                * 0.40
            )

        else:
            score -= 0.18

        # ---------------------------------------------------------
        # ISSUES
        # ---------------------------------------------------------

        for issue in validation.issues:
            if issue.severity == "error":
                score -= 0.25

            elif issue.severity == "warning":
                score -= 0.06

        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )