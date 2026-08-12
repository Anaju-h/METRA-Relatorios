from __future__ import annotations

from services.document_analysis.profiles.calypso import (
    CalypsoProfile,
)
from services.document_analysis.profiles.inspect import (
    InspectProfile,
)


class ProfileRegistry:
    """
    Registro central das famílias documentais conhecidas.

    O restante do motor pode perguntar:

        qual perfil corresponde a CALYPSO?

    sem precisar conhecer diretamente todos os módulos existentes.

    Quando uma nova família documental for adicionada,
    basta registrá-la aqui.
    """

    _profiles = {
        CalypsoProfile.SOURCE_TYPE: CalypsoProfile,
        InspectProfile.SOURCE_TYPE: InspectProfile,
    }

    # =============================================================
    # TODOS OS PERFIS
    # =============================================================

    @classmethod
    def get_all_profiles(
        cls,
    ) -> list[type]:
        return list(
            cls._profiles.values()
        )

    # =============================================================
    # PERFIL POR TIPO
    # =============================================================

    @classmethod
    def get_profile(
        cls,
        source_type: str,
    ) -> type | None:
        return cls._profiles.get(
            source_type
        )

    # =============================================================
    # VERIFICAR SUPORTE
    # =============================================================

    @classmethod
    def is_supported(
        cls,
        source_type: str,
    ) -> bool:
        return (
            source_type
            in cls._profiles
        )

    # =============================================================
    # REGISTRAR NOVO PERFIL
    # =============================================================

    @classmethod
    def register_profile(
        cls,
        profile: type,
    ) -> None:
        source_type = getattr(
            profile,
            "SOURCE_TYPE",
            None,
        )

        if not source_type:
            raise ValueError(
                "O perfil informado não possui SOURCE_TYPE."
            )

        cls._profiles[
            source_type
        ] = profile