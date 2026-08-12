from __future__ import annotations

import re
import unicodedata
from collections import Counter


class CalypsoProfile:
    """
    Perfil documental para relatórios ZEISS CALYPSO.

    O perfil concentra o vocabulário e as variações conhecidas
    dos relatórios CALYPSO.

    Ele não depende de uma máquina específica nem de um layout
    fixo de página.
    """

    SOURCE_TYPE = "CALYPSO"
    DISPLAY_NAME = "ZEISS CALYPSO"

    # =============================================================
    # IDENTIFICAÇÃO DA FAMÍLIA
    # =============================================================

    SOURCE_MARKERS = (
        "ZEISS CALYPSO",
        "CALYPSO",
    )

    SUPPORTING_MARKERS = (
        # Cabeçalhos em português
        "NOME DA MMC",
        "NUMERO DA MMC",
        "NÚMERO DA MMC",

        # Cabeçalhos vistos em outros templates
        "MODELO MMC",
        "Nº MMC",

        # Tabelas
        "MEASURED VALUE",
        "NOMINAL VALUE",

        # Resumo
        "NUMBER MEASURED VALUES",
        "NUMBER VALUES: RED",

        "MEDIÇÕES FORA DA TOLERÂNCIA",
        "MEDICOES FORA DA TOLERANCIA",

        "DURAÇÃO DA MEDIÇÃO",
        "DURACAO DA MEDICAO",
    )

    # =============================================================
    # CAMPOS DO RELATÓRIO
    # =============================================================

    FIELD_ANCHORS = {
        # ---------------------------------------------------------
        # PEÇA
        # ---------------------------------------------------------

        "part_name": (
            # Inglês — template StandardProtocol
            "Part name",

            # Português
            "Nome da peça",
            "Nome da peca",
            "Peça",
            "Peca",

            # Alguns relatórios usam apenas Nome
            "Nome",
        ),

        # ---------------------------------------------------------
        # MÁQUINA
        # ---------------------------------------------------------

        "machine_name": (
            # Template do PDF recebido
            "Modelo MMC",

            # Outros layouts CALYPSO
            "Nome da MMC",
            "Nome MMC",

            "Máquina",
            "Maquina",
        ),

        # ---------------------------------------------------------
        # IDENTIFICAÇÃO DA MÁQUINA
        # ---------------------------------------------------------

        "machine_number": (
            # Template recebido
            "Nº MMC",
            "N° MMC",

            # Outros layouts
            "Número da MMC",
            "Numero da MMC",

            "Nº da MMC",
            "N° da MMC",

            "Identificação da MMC",
            "Identificacao da MMC",
        ),

        # ---------------------------------------------------------
        # OPERADOR
        # ---------------------------------------------------------

        "operator": (
            "Operator",
            "Operador",
            "Medido por",
            "Responsável",
            "Responsavel",
        ),

        # ---------------------------------------------------------
        # IDENTIFICAÇÃO / PARTE
        # ---------------------------------------------------------

        "part_number": (
            # Template recebido
            "Part ident",

            # Outros templates
            "Número da peça",
            "Numero da peca",

            "Nº da peça",
            "N° da peça",

            "Parte n°",
            "Parte nº",

            "Parte",
        ),

        # ---------------------------------------------------------
        # DATA / HORA
        # ---------------------------------------------------------

        "measurement_datetime": (
            # Template recebido
            "Time/Date",

            # Outros formatos
            "Date/Time",
            "Data/Hora",
            "Data / Hora",
            "Data e hora",
        ),

        # ---------------------------------------------------------
        # QUANTIDADE DE MEDIÇÕES
        # ---------------------------------------------------------

        "measurement_count": (
            # Template recebido
            "Number measured values",

            # Outros formatos
            "Número de medições",
            "Numero de medições",
            "Numero de medicoes",

            "Nº de medições",
            "N° de medições",

            "Número de medidas",
            "Numero de medidas",
        ),

        # ---------------------------------------------------------
        # FORA DA TOLERÂNCIA
        # ---------------------------------------------------------

        "out_of_tolerance_count": (
            # Template recebido
            "Number values: red",
            "Number values red",

            # Outros formatos
            "Medições fora da tolerância",
            "Medicoes fora da tolerancia",

            "Fora da tolerância",
            "Fora da tolerancia",
        ),

        # ---------------------------------------------------------
        # DURAÇÃO
        # ---------------------------------------------------------

        "measurement_duration": (
            "Duração da medição",
            "Duração da Medição",

            "Duracao da medicao",
            "Duracao da Medicao",

            "Measurement duration",

            "Duração",
            "Duracao",
        ),
    }

    # =============================================================
    # EXCLUSÕES DE CONTEXTO
    # =============================================================

    FIELD_EXCLUSIONS = {
        "part_name": (
            "Nome da MMC",
            "Nome MMC",

            "Número da MMC",
            "Numero da MMC",

            "Nome do operador",
            "Nome e contato",
        ),

        "machine_name": (
            "Número da MMC",
            "Numero da MMC",

            "Nº MMC",
            "N° MMC",

            "Nº da MMC",
            "N° da MMC",
        ),

        "part_number": (
            "Número da MMC",
            "Numero da MMC",

            "Nº MMC",
            "N° MMC",
        ),
    }

    # =============================================================
    # TABELAS
    # =============================================================

    TABLE_HEADERS = {
        "name": (
            "Name",
            "Nome",
            "Characteristic",
            "Característica",
            "Caracteristica",
        ),

        "measured_value": (
            "Measured value",
            "Measured Value",
            "Measured",

            "Actual",

            "Valor medido",
            "Medido",
        ),

        "nominal_value": (
            "Nominal value",
            "Nominal Value",
            "Nominal",

            "Target",

            "Valor nominal",
        ),

        "upper_tolerance": (
            "+Tol",
            "+ Tol",

            "Upper Tol",
            "Upper Tolerance",

            "Tol +",
        ),

        "lower_tolerance": (
            "-Tol",
            "- Tol",

            "Lower Tol",
            "Lower Tolerance",

            "Tol -",
        ),

        "deviation": (
            "+/-Desvio",
            "+/- Desvio",

            "Deviation",
            "Desvio",
            "Dev",
        ),

        "unit": (
            "Unit",
            "Unidade",
        ),
    }

    # =============================================================
    # GRUPOS DE CARACTERÍSTICAS
    # =============================================================

    GROUP_NAMES = (
        "DIAMETROS",
        "DIÂMETROS",

        "DISTANCIAS",
        "DISTÂNCIAS",

        "PERPENDICULARIDADES",
        "PARALELISMOS",

        "CILINDRICIDADES",
        "CONCENTRICIDADES",

        "PLANICIDADES",
        "CIRCULARIDADES",

        "COAXIALIDADES",

        "POSICOES",
        "POSIÇÕES",

        "ANGULOS",
        "ÂNGULOS",

        "RETITUDES",
        "BATIMENTOS",
        "SIMETRIAS",

        "INCLINACOES",
        "INCLINAÇÕES",

        "COORDENADAS",
        "PERFIS",
    )

    # =============================================================
    # EQUIPAMENTOS CONHECIDOS
    # =============================================================

    EQUIPMENT_ALIASES = {
        "ZEISS DuraMax": (
            "ZEISS DURAMAX",
            "DURAMAX HTG",
            "DURAMAX",
        ),

        "ZEISS PRISMO": (
            "ZEISS PRISMO",

            "PRISMO_USS2",
            "PRISMO USS2",

            "PRISMO",
        ),

        "ZEISS O-INSPECT": (
            "ZEISS O-INSPECT",

            "O-INSPECT",
            "O INSPECT",
            "OINSPECT",
        ),
    }

    # =============================================================
    # UNIDADES
    # =============================================================

    UNIT_ALIASES = {
        "mm": "mm",
        "cm": "cm",
        "m": "m",

        "µm": "µm",
        "um": "µm",

        "inch": "inch",
        "in": "inch",

        "µinch": "µinch",
        "uinch": "µinch",

        "°": "°",
        "deg": "°",
    }

    # =============================================================
    # LINHAS QUE NÃO SÃO CARACTERÍSTICAS
    # =============================================================

    CHARACTERISTIC_IGNORE_PREFIXES = (
        "PAGE ",
        "PÁGINA ",
        "PAGINA ",

        "PART NAME ",
        "DRAWING NUMBER ",
        "ORDER NUMBER ",
        "VARIANT ",

        "COMPANY ",
        "DEPARTMENT ",

        "MODELO MMC ",
        "Nº MMC ",
        "N° MMC ",

        "OPERATOR ",

        "LAST ",
        "APPROVAL",

        "PART IDENT ",
        "TIME/DATE ",

        "RUN ",

        "NUMBER MEASURED VALUES",
        "NUMBER VALUES: RED",

        "PEÇA:",
        "PECA:",

        "OPERADOR ",
        "DATA/HORA ",

        "CALYPSO",

        "CORNER POINTS",

        "MAX ",
        "MIN ",

        "PONTOS ",

        "TIPO DE FILTRO",
        "RAIO DA SONDA",

        "MÉTODO DE AVALIAÇÃO",
        "METODO DE AVALIACAO",

        "AJUSTE AUTOMÁTICO",
        "AJUSTE AUTOMATICO",

        "SEGMENT ",
        "VMESS",

        "TEXT EVENT",
        "TEXT",
        "EVENT",

        "N.DEF",
    )

    # =============================================================
    # SOFTWARE
    # =============================================================

    SOFTWARE_NAME = "CALYPSO"

    SOFTWARE_VERSION_PATTERN = (
        r"\b\d+\.\d+\.\d+\b"
    )

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
    # FALLBACK DO NOME DA PEÇA
    # =============================================================

    @classmethod
    def find_part_name_in_text(
        cls,
        text: str,
    ) -> str | None:
        """
        Busca o nome da peça diretamente no conteúdo textual.

        Suporta diferentes famílias reais de relatórios CALYPSO:

            Part name pistao de trabalho cargill 6

            Nome GAS GENERATOR CASE PINTADA

            Peça: GAS GENERATOR CASE PINTADA
        """

        if not text:
            return None

        candidates = []

        patterns = (
            # -----------------------------------------------------
            # Template em inglês
            # -----------------------------------------------------

            r"(?im)^\s*PART\s+NAME\s*[:\-]?\s*"
            r"([^\r\n]+)",

            # -----------------------------------------------------
            # Português explícito
            # -----------------------------------------------------

            r"(?im)^\s*NOME\s+DA\s+PEÇA\s*[:\-]?\s*"
            r"([^\r\n]+)",

            r"(?im)^\s*NOME\s+DA\s+PECA\s*[:\-]?\s*"
            r"([^\r\n]+)",

            r"(?im)^\s*PEÇA\s*:\s*"
            r"([^\r\n]+)",

            r"(?im)^\s*PECA\s*:\s*"
            r"([^\r\n]+)",

            # -----------------------------------------------------
            # Nome VALOR
            # -----------------------------------------------------

            # Não aceita:
            #
            # Nome da MMC ...
            r"(?im)^\s*NOME\s+"
            r"(?!DA\s+MMC\b)"
            r"([^\r\n]+)",
        )

        for pattern in patterns:
            for match in re.finditer(
                pattern,
                text,
            ):
                candidate = (
                    cls._clean_part_name(
                        match.group(1)
                    )
                )

                if (
                    candidate
                    and cls._valid_part_name(
                        candidate
                    )
                ):
                    candidates.append(
                        candidate
                    )

        if not candidates:
            return None

        normalized_to_original = {}
        normalized_candidates = []

        for candidate in candidates:
            key = (
                cls._normalize_key(
                    candidate
                )
            )

            if not key:
                continue

            normalized_candidates.append(
                key
            )

            normalized_to_original.setdefault(
                key,
                candidate,
            )

        if not normalized_candidates:
            return None

        counts = Counter(
            normalized_candidates
        )

        best_key = max(
            counts,
            key=lambda key: (
                counts[key],
                len(key),
            ),
        )

        return normalized_to_original[
            best_key
        ]

    # =============================================================
    # LIMPEZA DO NOME
    # =============================================================

    @classmethod
    def _clean_part_name(
        cls,
        value: str,
    ) -> str:
        value = (
            value
            .replace(
                "\u00A0",
                " ",
            )
            .strip(
                " \t:-–—"
            )
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        # Se o PyMuPDF colocar outro campo na mesma linha,
        # cortamos a partir do próximo label conhecido.
        separators = (
            " Drawing number",
            " Order number",
            " Variant",
            " Company",
            " Department",
            " Modelo MMC",
            " Nº MMC",
            " N° MMC",
            " Operator",
            " Part ident",
            " Time/Date",

            " Parte n°",
            " Parte nº",
            " Operador ",
            " Data/Hora ",
            " Page ",
        )

        for separator in separators:
            position = (
                value.lower()
                .find(
                    separator.lower()
                )
            )

            if position > 0:
                value = (
                    value[
                        :position
                    ]
                    .strip()
                )

        return value

    # =============================================================
    # VALIDAR NOME
    # =============================================================

    @classmethod
    def _valid_part_name(
        cls,
        value: str,
    ) -> bool:
        normalized = (
            cls._normalize_key(
                value
            )
        )

        if not normalized:
            return False

        blocked = {
            "da mmc",
            "mmc",

            "nome",
            "part name",

            "peca",
            "peça",

            "operator",
            "operador",

            "master",

            "drawing number",
            "order number",

            "servico oferecido por senai ib",
        }

        if normalized in blocked:
            return False

        invalid_contains = (
            "nome da mmc",
            "numero da mmc",

            "number measured values",

            "last 1 measurements",
            "approval",

            "time/date",

            "zeiss calypso",
        )

        if any(
            item in normalized
            for item in invalid_contains
        ):
            return False

        return (
            re.search(
                r"[a-z]",
                normalized,
            )
            is not None
        )

    # =============================================================
    # EQUIPAMENTO
    # =============================================================

    @classmethod
    def normalize_equipment(
        cls,
        value: str | None,
    ) -> str | None:
        if not value:
            return None

        normalized_value = (
            value.upper()
            .strip()
        )

        for (
            equipment_name,
            aliases,
        ) in cls.EQUIPMENT_ALIASES.items():

            for alias in sorted(
                aliases,
                key=len,
                reverse=True,
            ):
                if (
                    alias.upper()
                    in normalized_value
                ):
                    return equipment_name

        return value.strip()

    @classmethod
    def is_known_equipment(
        cls,
        value: str | None,
    ) -> bool:
        if not value:
            return False

        normalized = (
            value.upper()
        )

        for aliases in (
            cls.EQUIPMENT_ALIASES
            .values()
        ):
            for alias in aliases:
                if (
                    alias.upper()
                    in normalized
                ):
                    return True

        return False

    @classmethod
    def find_equipment_in_text(
        cls,
        text: str,
    ) -> str | None:
        """
        Fallback independente do layout.

        Se o documento disser explicitamente DURAMAX, PRISMO etc.,
        retornamos o equipamento mesmo que a associação espacial
        com o label tenha falhado.
        """

        if not text:
            return None

        normalized = (
            text.upper()
        )

        matches = []

        for (
            equipment,
            aliases,
        ) in cls.EQUIPMENT_ALIASES.items():

            for alias in aliases:
                if (
                    alias.upper()
                    in normalized
                ):
                    matches.append(
                        (
                            len(alias),
                            equipment,
                        )
                    )

        if not matches:
            return None

        matches.sort(
            reverse=True
        )

        return matches[0][1]

    # =============================================================
    # UNIDADES
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
    # NORMALIZAÇÃO
    # =============================================================

    @classmethod
    def _normalize_key(
        cls,
        value: str,
    ) -> str:
        value = (
            unicodedata.normalize(
                "NFKD",
                value or "",
            )
        )

        value = "".join(
            character
            for character in value
            if not unicodedata.combining(
                character
            )
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return (
            value
            .strip()
            .lower()
        )