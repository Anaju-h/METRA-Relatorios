from __future__ import annotations


class InspectProfile:
    """
    Perfil documental para relatórios ZEISS INSPECT.

    O perfil representa o software/família documental,
    não o equipamento físico utilizado.
    """

    SOURCE_TYPE = "ZEISS_INSPECT"

    DISPLAY_NAME = "ZEISS INSPECT"

    # =============================================================
    # IDENTIFICAÇÃO
    # =============================================================

    SOURCE_MARKERS = (
        "GENERATED WITH ZEISS INSPECT",
        "ZEISS INSPECT",
        "GOM INSPECT",

        # Variação observada na extração textual real
        # do documento recebido:
        "ZEISS INSP EC T",
    )

    SUPPORTING_MARKERS = (
        "ELEMENT",
        "DATUM",
        "PROPERTY",

        "NOMINAL",
        "ACTUAL",

        "TOL -",
        "TOL +",

        "DEV",
        "CHECK",
        "OUT",

        "ALIGNMENT",
        "ALINHAMENTO",

        "DEFEITO DO VOLUME",
    )

    # =============================================================
    # CAMPOS
    # =============================================================

    FIELD_ANCHORS = {
        "document_title": (
            "Título",
            "Titulo",
            "Project",
            "Projeto",
        ),

        "part_name": (
            "Nome da peça",
            "Nome da peca",
            "Peça",
            "Peca",
            "Part",
            "Component",
        ),

        "operator": (
            "Operador",
            "Operator",
            "Created by",
            "Measured by",
        ),

        "measurement_datetime": (
            "Data/Hora",
            "Data / Hora",
            "Date/Time",
            "Date",
        ),

        "alignment": (
            "Alinhamento",
            "Alignment",
        ),

        "length_unit": (
            "Unidade de comprimento",
            "Length unit",
        ),
    }

    FIELD_EXCLUSIONS = {}

    # =============================================================
    # TABELA
    # =============================================================

    TABLE_HEADERS = {
        "name": (
            "Element",
            "Elemento",
        ),

        "datum": (
            "Datum",
        ),

        "property_name": (
            "Property",
            "Propriedade",
        ),

        "nominal_value": (
            "Nominal",
        ),

        "measured_value": (
            "Actual",
            "Atual",
        ),

        "lower_tolerance": (
            "Tol -",
            "Tol-",
        ),

        "upper_tolerance": (
            "Tol +",
            "Tol+",
        ),

        "deviation": (
            "Dev",
            "Deviation",
            "Desvio",
        ),

        "check_value": (
            "Check",
            "Verificar",
        ),

        "out_value": (
            "Out",
        ),
    }

    # =============================================================
    # ANÁLISE
    # =============================================================

    VOLUME_ANALYSIS_MARKERS = (
        "DEFEITO DO VOLUME",
        "VOLUME DEFECT",
        "V_ALL",
        ".VP.",
    )

    SURFACE_ANALYSIS_MARKERS = (
        "SURFACE DEVIATION",
        "SURFACE",
        "SUPERFÍCIE",
        "SUPERFICIE",
    )

    # =============================================================
    # SOFTWARE
    # =============================================================

    SOFTWARE_NAME = (
        "ZEISS INSPECT"
    )

    SOFTWARE_VERSION_PATTERNS = (
        r"GENERATED\s+WITH\s+ZEISS\s+INSPECT\s+(\d{4})",

        # Forma real extraída:
        #
        # Generated with ZEISS INSP EC T 2025
        r"GENERATED\s+WITH\s+ZEISS\s+"
        r"INSP\s*EC\s*T\s+(\d{4})",

        r"ZEISS\s+INSPECT\s+(\d{4})",

        r"ZEISS\s+INSPECT\s+"
        r"(\d+\.\d+(?:\.\d+)?)",
    )

    # =============================================================
    # UNIDADES
    # =============================================================

    UNIT_ALIASES = {
        "mm": "mm",
        "cm": "cm",
        "m": "m",

        "µm": "µm",
        "um": "µm",

        "mm³": "mm³",
        "mm3": "mm³",

        "cm³": "cm³",
        "cm3": "cm³",

        "°": "°",
        "deg": "°",
    }

    # =============================================================
    # GETTERS
    # =============================================================

    @classmethod
    def get_field_anchors(
        cls,
        field_name: str,
    ) -> tuple[str, ...]:
        return cls.FIELD_ANCHORS.get(
            field_name,
            tuple(),
        )

    @classmethod
    def get_field_exclusions(
        cls,
        field_name: str,
    ) -> tuple[str, ...]:
        return cls.FIELD_EXCLUSIONS.get(
            field_name,
            tuple(),
        )

    @classmethod
    def get_table_headers(
        cls,
        column_name: str,
    ) -> tuple[str, ...]:
        return cls.TABLE_HEADERS.get(
            column_name,
            tuple(),
        )

    # =============================================================
    # UNIDADE
    # =============================================================

    @classmethod
    def normalize_unit(
        cls,
        value: str | None,
    ) -> str | None:
        if not value:
            return None

        clean = (
            value.strip()
        )

        return cls.UNIT_ALIASES.get(
            clean.lower(),
            clean,
        )

    # =============================================================
    # TIPO DE ANÁLISE
    # =============================================================

    @classmethod
    def detect_analysis_type(
        cls,
        text: str,
    ) -> str | None:
        if not text:
            return None

        normalized = (
            text.upper()
        )

        if any(
            marker
            in normalized

            for marker in (
                cls.VOLUME_ANALYSIS_MARKERS
            )
        ):
            return (
                "Análise volumétrica"
            )

        if any(
            marker
            in normalized

            for marker in (
                cls.SURFACE_ANALYSIS_MARKERS
            )
        ):
            return (
                "Análise de superfície"
            )

        return None