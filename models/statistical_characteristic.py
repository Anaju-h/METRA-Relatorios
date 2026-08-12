from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StatisticalMeasurement:
    """
    Um valor medido pertencente a uma unidade do lote.
    """

    document_id: Optional[int]

    extraction_id: Optional[int]

    characteristic_id: Optional[int]

    unit_identifier: str
    document_name: str

    measured_value: Optional[float]

    deviation: Optional[float]

    status: str

    source_page: Optional[int] = None


@dataclass
class StatisticalCharacteristic:
    """
    Consolidação de uma mesma característica medida em uma
    ou mais unidades do lote.

    O agrupamento não depende da máquina nem de um tipo fixo
    de medição. Ele utiliza a identidade técnica da
    característica:

    - nome normalizado;
    - grupo;
    - propriedade;
    - datum;
    - valor nominal;
    - tolerâncias;
    - unidade.
    """

    key: str

    display_name: str

    group_name: Optional[str] = None
    property_name: Optional[str] = None
    datum: Optional[str] = None

    nominal_value: Optional[float] = None

    lower_tolerance: Optional[float] = None
    upper_tolerance: Optional[float] = None

    unit: Optional[str] = None

    measurements: list[
        StatisticalMeasurement
    ] = field(
        default_factory=list
    )

    count: int = 0

    valid_numeric_count: int = 0

    ok_count: int = 0
    nok_count: int = 0
    unknown_count: int = 0

    minimum: Optional[float] = None
    maximum: Optional[float] = None

    mean: Optional[float] = None
    median: Optional[float] = None

    amplitude: Optional[float] = None

    standard_deviation: Optional[float] = None

    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None

    conformity_percentage: float = 0.0

    @property
    def has_multiple_measurements(
        self,
    ) -> bool:
        return (
            self.valid_numeric_count >= 2
        )

    @property
    def has_tolerance_limits(
        self,
    ) -> bool:
        return (
            self.lower_limit is not None
            and self.upper_limit is not None
        )

    @property
    def has_nominal(
        self,
    ) -> bool:
        return self.nominal_value is not None

    @property
    def numeric_values(
        self,
    ) -> list[float]:
        return [
            float(
                measurement.measured_value
            )
            for measurement in self.measurements
            if measurement.measured_value
            is not None
        ]

    @property
    def unit_identifiers(
        self,
    ) -> list[str]:
        return [
            measurement.unit_identifier
            for measurement in self.measurements
        ]

    @property
    def is_batch_characteristic(
        self,
    ) -> bool:
        unique_units = {
            measurement.unit_identifier
            for measurement in self.measurements
        }

        return len(
            unique_units
        ) > 1   