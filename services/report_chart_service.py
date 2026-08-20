from __future__ import annotations

from pathlib import Path
import re
import textwrap
import unicodedata
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from models.statistical_characteristic import (
    StatisticalCharacteristic,
)


class ReportChartService:
    """
    Gera gráficos técnicos do METRA.

    Para relatórios em lote, o pacote padrão combina:
    - conformidade geral;
    - ocorrências por característica;
    - desvio médio quando houver um conjunto compatível;
    - até três gráficos de tendência por característica.

    Os gráficos de tendência são selecionados automaticamente,
    priorizando não conformidades e características com várias medições.
    """

    COLOR_NAVY = "#0B2748"
    COLOR_BLUE = "#0072BC"

    COLOR_OK = "#14804A"
    COLOR_NOK = "#C0392B"
    COLOR_UNKNOWN = "#8A96A3"

    COLOR_NOMINAL = "#495866"
    COLOR_LIMIT = "#C76B00"

    COLOR_GRID = "#D6DCE2"
    COLOR_BACKGROUND = "#FFFFFF"

    DEFAULT_TREND_CHARTS = 3

    def generate_charts(
        self,
        statistics: dict[str, Any],
        output_directory: str | Path,
        maximum_characteristic_charts: int = 8,
    ) -> dict[str, Any]:
        output_dir = Path(
            output_directory
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        generated_files: list[Path] = []

        overall = statistics.get(
            "overall",
            {},
        )

        groups: list[
            StatisticalCharacteristic
        ] = (
            statistics.get(
                "chart_candidates",
                [],
            )
            or []
        )

        # ---------------------------------------------------------
        # 1. CONFORMIDADE GERAL
        # ---------------------------------------------------------

        overall_path = (
            self.generate_overall_conformity_chart(
                overall=overall,
                output_path=(
                    output_dir
                    / "conformidade_geral.png"
                ),
            )
        )

        self._append_generated(
            generated_files,
            overall_path,
        )

        # ---------------------------------------------------------
        # 2. OCORRÊNCIAS POR CARACTERÍSTICA
        # ---------------------------------------------------------

        group_summary_path = None

        summary_groups = [
            group
            for group in groups
            if int(
                getattr(
                    group,
                    "count",
                    0,
                )
                or 0
            ) > 0
        ][:14]

        if summary_groups:
            group_summary_path = (
                self._generate_conformity_summary_chart(
                    groups=summary_groups,
                    output_path=(
                        output_dir
                        / "ocorrencias_por_caracteristica.png"
                    ),
                )
            )

        self._append_generated(
            generated_files,
            group_summary_path,
        )

        # ---------------------------------------------------------
        # 3. DESVIO MÉDIO
        # ---------------------------------------------------------

        mean_deviation_groups = (
            self._select_compatible_deviation_groups(
                groups
            )
        )

        mean_deviation_path = None

        if mean_deviation_groups:
            mean_deviation_path = (
                self._generate_batch_mean_deviation_chart(
                    groups=mean_deviation_groups[
                        :12
                    ],
                    output_path=(
                        output_dir
                        / "desvio_medio_por_caracteristica.png"
                    ),
                )
            )

        self._append_generated(
            generated_files,
            mean_deviation_path,
        )

        # ---------------------------------------------------------
        # 4. TENDÊNCIAS POR CARACTERÍSTICA
        # ---------------------------------------------------------

        requested_limit = int(
            maximum_characteristic_charts
            or 0
        )

        trend_limit = min(
            self.DEFAULT_TREND_CHARTS,
            (
                requested_limit
                if requested_limit > 0
                else self.DEFAULT_TREND_CHARTS
            ),
        )

        characteristic_charts: list[
            dict[str, Any]
        ] = []

        selected_trends = (
            self._select_trend_groups(
                groups,
                maximum=trend_limit,
            )
        )

        for index, group in enumerate(
            selected_trends,
            start=1,
        ):
            file_name = (
                f"tendencia_{index:02d}_"
                f"{self._safe_file_name(group.display_name)}.png"
            )

            chart_path = (
                self.generate_characteristic_chart(
                    group=group,
                    output_path=(
                        output_dir
                        / file_name
                    ),
                )
            )

            if (
                chart_path is None
                or not chart_path.exists()
            ):
                continue

            generated_files.append(
                chart_path
            )

            characteristic_charts.append(
                {
                    "key":
                        getattr(
                            group,
                            "key",
                            file_name,
                        ),

                    "title":
                        self._display_label(
                            group.display_name
                        ),

                    "description":
                        self._trend_description(
                            group
                        ),

                    "path":
                        chart_path,
                }
            )

        return {
            "overall_conformity":
                overall_path,

            "group_summary":
                group_summary_path,

            "mean_deviation":
                mean_deviation_path,

            "characteristic_charts":
                characteristic_charts,

            "all_files":
                generated_files,
        }

    # =============================================================
    # SELEÇÃO DOS GRÁFICOS
    # =============================================================

    def _select_trend_groups(
        self,
        groups: list[
            StatisticalCharacteristic
        ],
        *,
        maximum: int,
    ) -> list[
        StatisticalCharacteristic
    ]:
        if maximum <= 0:
            return []

        candidates = [
            group
            for group in groups
            if int(
                getattr(
                    group,
                    "valid_numeric_count",
                    0,
                )
                or 0
            ) >= 2
        ]

        candidates.sort(
            key=lambda group: (
                0
                if int(
                    getattr(
                        group,
                        "nok_count",
                        0,
                    )
                    or 0
                ) > 0
                else 1,

                -int(
                    getattr(
                        group,
                        "valid_numeric_count",
                        0,
                    )
                    or 0
                ),

                -self._relative_amplitude(
                    group
                ),

                self._display_label(
                    getattr(
                        group,
                        "display_name",
                        "",
                    )
                ).upper(),
            )
        )

        selected: list[
            StatisticalCharacteristic
        ] = []

        seen_keys: set[str] = set()

        for group in candidates:
            unique_key = str(
                getattr(
                    group,
                    "key",
                    "",
                )
                or self._chart_identity(
                    group
                )
            )

            if unique_key in seen_keys:
                continue

            seen_keys.add(
                unique_key
            )

            selected.append(
                group
            )

            if len(selected) >= maximum:
                break

        return selected

    def _select_compatible_deviation_groups(
        self,
        groups: list[
            StatisticalCharacteristic
        ],
    ) -> list[
        StatisticalCharacteristic
    ]:
        candidates = [
            group
            for group in groups
            if getattr(
                group,
                "mean",
                None,
            )
            is not None
            and getattr(
                group,
                "nominal_value",
                None,
            )
            is not None
        ]

        if not candidates:
            return []

        buckets: dict[
            str,
            list[StatisticalCharacteristic],
        ] = {}

        for group in candidates:
            unit_key = self._normalize_unit_for_chart(
                getattr(
                    group,
                    "unit",
                    None,
                )
            )

            buckets.setdefault(
                unit_key,
                [],
            ).append(
                group
            )

        selected_key = max(
            buckets,
            key=lambda key: len(
                buckets[key]
            ),
        )

        selected = buckets[
            selected_key
        ]

        if len(selected) < 2:
            return []

        return selected

    # =============================================================
    # CONFORMIDADE GERAL
    # =============================================================

    def generate_overall_conformity_chart(
        self,
        overall: dict[str, Any],
        output_path: str | Path,
    ) -> Optional[Path]:
        destination = Path(
            output_path
        )

        ok_count = int(
            overall.get(
                "ok_count",
                0,
            )
            or 0
        )

        nok_count = int(
            overall.get(
                "nok_count",
                0,
            )
            or 0
        )

        unknown_count = int(
            overall.get(
                "unknown_count",
                0,
            )
            or 0
        )

        labels: list[str] = []
        values: list[int] = []
        colors: list[str] = []

        if ok_count > 0:
            labels.append(
                "Conformes"
            )
            values.append(
                ok_count
            )
            colors.append(
                self.COLOR_OK
            )

        if nok_count > 0:
            labels.append(
                "Não conformes"
            )
            values.append(
                nok_count
            )
            colors.append(
                self.COLOR_NOK
            )

        if unknown_count > 0:
            labels.append(
                "Não avaliadas"
            )
            values.append(
                unknown_count
            )
            colors.append(
                self.COLOR_UNKNOWN
            )

        if not values:
            return None

        figure, axes = plt.subplots(
            figsize=(7.0, 3.1),
            dpi=160,
        )

        figure.patch.set_facecolor(
            self.COLOR_BACKGROUND
        )

        axes.set_facecolor(
            self.COLOR_BACKGROUND
        )

        wedges, _, _ = axes.pie(
            values,
            labels=None,
            colors=colors,
            startangle=90,
            counterclock=False,
            autopct=self._autopct,
            pctdistance=0.78,
            wedgeprops={
                "width":
                    0.37,

                "edgecolor":
                    self.COLOR_BACKGROUND,

                "linewidth":
                    2.0,
            },
            textprops={
                "fontsize":
                    9,

                "weight":
                    "bold",
            },
        )

        conformity = float(
            overall.get(
                "conformity_percentage",
                0.0,
            )
            or 0.0
        )

        axes.text(
            0,
            0.08,
            f"{conformity:.1f}%",
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=self.COLOR_NAVY,
        )

        axes.text(
            0,
            -0.15,
            "conformidade",
            ha="center",
            va="center",
            fontsize=8,
            color=self.COLOR_NOMINAL,
        )

        axes.legend(
            wedges,
            [
                f"{label}: {value}"
                for label, value
                in zip(
                    labels,
                    values,
                )
            ],
            loc="center left",
            bbox_to_anchor=(
                0.92,
                0.5,
            ),
            frameon=False,
            fontsize=8.5,
        )

        axes.set_title(
            "Conformidade geral dos resultados",
            fontsize=11,
            fontweight="bold",
            color=self.COLOR_NAVY,
            pad=10,
        )

        axes.axis(
            "equal"
        )

        figure.tight_layout(
            pad=0.8
        )

        figure.savefig(
            destination,
            bbox_inches="tight",
            facecolor=self.COLOR_BACKGROUND,
        )

        plt.close(
            figure
        )

        return destination

    # =============================================================
    # OCORRÊNCIAS POR CARACTERÍSTICA
    # =============================================================

    def _generate_conformity_summary_chart(
        self,
        *,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: Path,
    ) -> Path:
        labels = [
            self._wrap_label(
                group.display_name,
                width=24,
            )
            for group in groups
        ]

        ok_values = [
            int(
                getattr(
                    group,
                    "ok_count",
                    0,
                )
                or 0
            )
            for group in groups
        ]

        nok_values = [
            int(
                getattr(
                    group,
                    "nok_count",
                    0,
                )
                or 0
            )
            for group in groups
        ]

        unknown_values = [
            int(
                getattr(
                    group,
                    "unknown_count",
                    0,
                )
                or 0
            )
            for group in groups
        ]

        figure_height = max(
            3.1,
            len(groups) * 0.40 + 1.25,
        )

        figure, axes = plt.subplots(
            figsize=(
                8.4,
                figure_height,
            ),
            dpi=160,
        )

        positions = list(
            range(
                len(groups)
            )
        )

        axes.barh(
            positions,
            ok_values,
            label="Conforme",
            color=self.COLOR_OK,
        )

        axes.barh(
            positions,
            nok_values,
            left=ok_values,
            label="Não conforme",
            color=self.COLOR_NOK,
        )

        accumulated = [
            ok_value + nok_value
            for ok_value, nok_value
            in zip(
                ok_values,
                nok_values,
            )
        ]

        axes.barh(
            positions,
            unknown_values,
            left=accumulated,
            label="Não avaliada",
            color=self.COLOR_UNKNOWN,
        )

        axes.set_yticks(
            positions
        )

        axes.set_yticklabels(
            labels,
            fontsize=8,
        )

        axes.invert_yaxis()

        axes.set_xlabel(
            "Quantidade de resultados",
            fontsize=8.3,
        )

        axes.set_title(
            "Distribuição de conformidade por característica",
            fontsize=11,
            fontweight="bold",
            color=self.COLOR_NAVY,
            pad=10,
        )

        axes.grid(
            axis="x",
            color=self.COLOR_GRID,
            linewidth=0.6,
            alpha=0.8,
        )

        axes.set_axisbelow(
            True
        )

        self._clean_axes(
            axes
        )

        axes.legend(
            loc="lower center",
            bbox_to_anchor=(
                0.5,
                -0.30,
            ),
            ncol=3,
            frameon=False,
            fontsize=8,
        )

        figure.tight_layout(
            pad=1.0
        )

        figure.savefig(
            output_path,
            bbox_inches="tight",
            facecolor=self.COLOR_BACKGROUND,
        )

        plt.close(
            figure
        )

        return output_path

    # =============================================================
    # DESVIO MÉDIO
    # =============================================================

    def _generate_batch_mean_deviation_chart(
        self,
        *,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: Path,
    ) -> Optional[Path]:
        rows: list[
            tuple[str, float, str, str]
        ] = []

        for group in groups:
            try:
                mean_value = float(
                    group.mean
                )
                nominal_value = float(
                    group.nominal_value
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            unit = self._normalize_unit_for_chart(
                getattr(
                    group,
                    "unit",
                    None,
                )
            )

            rows.append(
                (
                    self._wrap_label(
                        group.display_name,
                        width=24,
                    ),

                    mean_value
                    - nominal_value,

                    unit,

                    self._group_status(
                        group
                    ),
                )
            )

        if len(rows) < 2:
            return None

        labels = [
            label
            for label, _, _, _
            in rows
        ]

        deviations = [
            deviation
            for _, deviation, _, _
            in rows
        ]

        colors = [
            (
                self.COLOR_NOK
                if status == "NOK"
                else (
                    self.COLOR_OK
                    if status == "OK"
                    else self.COLOR_BLUE
                )
            )
            for _, _, _, status
            in rows
        ]

        unit = rows[0][2]

        figure_height = max(
            3.2,
            len(rows) * 0.44 + 1.35,
        )

        figure, axes = plt.subplots(
            figsize=(
                8.4,
                figure_height,
            ),
            dpi=160,
        )

        positions = list(
            range(
                len(rows)
            )
        )

        axes.barh(
            positions,
            deviations,
            color=colors,
            height=0.52,
        )

        axes.axvline(
            0,
            color=self.COLOR_NOMINAL,
            linewidth=1.2,
            linestyle="--",
        )

        axes.set_yticks(
            positions
        )

        axes.set_yticklabels(
            labels,
            fontsize=8,
        )

        axes.invert_yaxis()

        axis_label = (
            f"Desvio da média em relação ao nominal ({unit})"
            if unit
            else "Desvio da média em relação ao nominal"
        )

        axes.set_xlabel(
            axis_label,
            fontsize=8.3,
        )

        axes.set_title(
            "Desvio médio por característica",
            fontsize=11,
            fontweight="bold",
            color=self.COLOR_NAVY,
            pad=10,
        )

        axes.grid(
            axis="x",
            color=self.COLOR_GRID,
            linewidth=0.6,
            alpha=0.75,
        )

        axes.set_axisbelow(
            True
        )

        self._clean_axes(
            axes
        )

        for y, value in zip(
            positions,
            deviations,
        ):
            axes.annotate(
                self._format_number(
                    value
                ),
                xy=(
                    value,
                    y,
                ),
                xytext=(
                    4
                    if value >= 0
                    else -4,
                    0,
                ),
                textcoords="offset points",
                ha=(
                    "left"
                    if value >= 0
                    else "right"
                ),
                va="center",
                fontsize=7.4,
                color=self.COLOR_NOMINAL,
            )

        figure.tight_layout(
            pad=1.0
        )

        figure.savefig(
            output_path,
            bbox_inches="tight",
            facecolor=self.COLOR_BACKGROUND,
        )

        plt.close(
            figure
        )

        return output_path

    # =============================================================
    # TENDÊNCIA POR CARACTERÍSTICA
    # =============================================================

    def generate_characteristic_chart(
        self,
        group: StatisticalCharacteristic,
        output_path: str | Path,
    ) -> Optional[Path]:
        values: list[float] = []
        labels: list[str] = []
        statuses: list[str] = []

        for measurement in (
            group.measurements
        ):
            if (
                measurement.measured_value
                is None
            ):
                continue

            try:
                measured_value = float(
                    measurement.measured_value
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            labels.append(
                str(
                    measurement.unit_identifier
                )
            )

            values.append(
                measured_value
            )

            statuses.append(
                str(
                    measurement.status
                    or ""
                ).upper()
            )

        if len(values) < 2:
            return None

        destination = Path(
            output_path
        )

        figure, axes = plt.subplots(
            figsize=(
                8.4,
                3.4,
            ),
            dpi=160,
        )

        x_values = list(
            range(
                1,
                len(values) + 1,
            )
        )

        point_colors = [
            (
                self.COLOR_NOK
                if status == "NOK"
                else (
                    self.COLOR_OK
                    if status == "OK"
                    else self.COLOR_UNKNOWN
                )
            )
            for status in statuses
        ]

        axes.plot(
            x_values,
            values,
            linewidth=1.4,
            color=self.COLOR_BLUE,
            alpha=0.72,
            zorder=2,
        )

        axes.scatter(
            x_values,
            values,
            s=48,
            c=point_colors,
            edgecolors=self.COLOR_BACKGROUND,
            linewidths=0.8,
            zorder=3,
        )

        if (
            group.nominal_value
            is not None
        ):
            axes.axhline(
                float(
                    group.nominal_value
                ),
                color=self.COLOR_NOMINAL,
                linewidth=1.2,
                linestyle="--",
                label=(
                    "Nominal "
                    f"({self._format_number(group.nominal_value)})"
                ),
            )

        if (
            group.lower_limit
            is not None
        ):
            axes.axhline(
                float(
                    group.lower_limit
                ),
                color=self.COLOR_LIMIT,
                linewidth=1.1,
                linestyle=":",
                label=(
                    "Limite inferior "
                    f"({self._format_number(group.lower_limit)})"
                ),
            )

        if (
            group.upper_limit
            is not None
        ):
            axes.axhline(
                float(
                    group.upper_limit
                ),
                color=self.COLOR_LIMIT,
                linewidth=1.1,
                linestyle=":",
                label=(
                    "Limite superior "
                    f"({self._format_number(group.upper_limit)})"
                ),
            )

        axes.set_xticks(
            x_values
        )

        axes.set_xticklabels(
            labels,
            fontsize=8,
            rotation=(
                35
                if len(labels) > 7
                else 0
            ),
            ha=(
                "right"
                if len(labels) > 7
                else "center"
            ),
        )

        y_label = (
            f"Valor medido ({group.unit})"
            if getattr(
                group,
                "unit",
                None,
            )
            else "Valor medido"
        )

        axes.set_ylabel(
            y_label,
            fontsize=8.5,
        )

        axes.set_xlabel(
            "Unidades do lote",
            fontsize=8.5,
        )

        axes.set_title(
            "Comportamento dos valores medidos",
            fontsize=11,
            fontweight="bold",
            color=self.COLOR_NAVY,
            pad=10,
        )

        axes.grid(
            axis="y",
            color=self.COLOR_GRID,
            linewidth=0.6,
            alpha=0.85,
        )

        axes.set_axisbelow(
            True
        )

        self._clean_axes(
            axes
        )

        handles, labels_legend = (
            axes.get_legend_handles_labels()
        )

        if handles:
            axes.legend(
                handles,
                labels_legend,
                loc="upper center",
                bbox_to_anchor=(
                    0.5,
                    -0.22,
                ),
                ncol=min(
                    3,
                    len(handles),
                ),
                frameon=False,
                fontsize=7.5,
            )

        statistics_text = (
            self._statistics_text(
                group
            )
        )

        axes.text(
            0.01,
            0.98,
            statistics_text,
            transform=axes.transAxes,
            ha="left",
            va="top",
            fontsize=7.5,
            color=self.COLOR_NOMINAL,
            bbox={
                "boxstyle":
                    "round,pad=0.35",

                "facecolor":
                    self.COLOR_BACKGROUND,

                "edgecolor":
                    self.COLOR_GRID,

                "alpha":
                    0.92,
            },
        )

        figure.tight_layout()

        figure.savefig(
            destination,
            bbox_inches="tight",
            facecolor=self.COLOR_BACKGROUND,
        )

        plt.close(
            figure
        )

        return destination

    # =============================================================
    # HELPERS
    # =============================================================

    def _append_generated(
        self,
        files: list[Path],
        path: Optional[Path],
    ) -> None:
        if (
            path is not None
            and path.exists()
        ):
            files.append(
                path
            )

    def _relative_amplitude(
        self,
        group: StatisticalCharacteristic,
    ) -> float:
        amplitude = getattr(
            group,
            "amplitude",
            None,
        )

        if amplitude is None:
            return 0.0

        references = [
            abs(
                float(
                    group.nominal_value
                )
            )
            if getattr(
                group,
                "nominal_value",
                None,
            )
            is not None
            else 0.0,

            abs(
                float(
                    group.mean
                )
            )
            if getattr(
                group,
                "mean",
                None,
            )
            is not None
            else 0.0,

            1.0,
        ]

        return (
            abs(
                float(
                    amplitude
                )
            )
            / max(
                references
            )
        )

    def _group_status(
        self,
        group: StatisticalCharacteristic,
    ) -> str:
        if int(
            getattr(
                group,
                "nok_count",
                0,
            )
            or 0
        ) > 0:
            return "NOK"

        if int(
            getattr(
                group,
                "ok_count",
                0,
            )
            or 0
        ) > 0:
            return "OK"

        return "UNKNOWN"

    def _chart_identity(
        self,
        group: StatisticalCharacteristic,
    ) -> str:
        return "|".join(
            [
                self._display_label(
                    getattr(
                        group,
                        "display_name",
                        "",
                    )
                ).upper(),

                str(
                    getattr(
                        group,
                        "nominal_value",
                        "",
                    )
                ),

                str(
                    getattr(
                        group,
                        "lower_tolerance",
                        "",
                    )
                ),

                str(
                    getattr(
                        group,
                        "upper_tolerance",
                        "",
                    )
                ),

                self._normalize_unit_for_chart(
                    getattr(
                        group,
                        "unit",
                        None,
                    )
                ),
            ]
        )

    def _normalize_unit_for_chart(
        self,
        value: Any,
    ) -> str:
        normalized = (
            unicodedata.normalize(
                "NFKD",
                str(
                    value or ""
                ),
            )
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        normalized = (
            normalized
            .strip()
            .lower()
            .replace(" ", "")
        )

        aliases = {
            "millimeter":
                "mm",

            "millimeters":
                "mm",

            "millimetre":
                "mm",

            "millimetres":
                "mm",

            "inch":
                "in",

            "inches":
                "in",

            "\"":
                "in",

            "micrometer":
                "um",

            "micrometre":
                "um",

            "µm":
                "um",

            "μm":
                "um",

            "degree":
                "°",

            "degrees":
                "°",

            "deg":
                "°",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    def _trend_description(
        self,
        group: StatisticalCharacteristic,
    ) -> str:
        count = int(
            getattr(
                group,
                "valid_numeric_count",
                0,
            )
            or 0
        )

        nok = int(
            getattr(
                group,
                "nok_count",
                0,
            )
            or 0
        )

        if nok > 0:
            return (
                f"{count} valor(es) numérico(s) avaliados; "
                f"{nok} ocorrência(s) fora da tolerância."
            )

        return (
            f"{count} valor(es) numérico(s) avaliados ao longo do lote."
        )

    def _display_label(
        self,
        value: Any,
    ) -> str:
        return " ".join(
            str(
                value
                or "Característica"
            ).split()
        )

    def _statistics_text(
        self,
        group: StatisticalCharacteristic,
    ) -> str:
        parts = [
            (
                "n = "
                f"{int(getattr(group, 'valid_numeric_count', 0) or 0)}"
            )
        ]

        if getattr(
            group,
            "mean",
            None,
        ) is not None:
            parts.append(
                (
                    "média = "
                    f"{self._format_number(group.mean)}"
                )
            )

        if getattr(
            group,
            "minimum",
            None,
        ) is not None:
            parts.append(
                (
                    "mín. = "
                    f"{self._format_number(group.minimum)}"
                )
            )

        if getattr(
            group,
            "maximum",
            None,
        ) is not None:
            parts.append(
                (
                    "máx. = "
                    f"{self._format_number(group.maximum)}"
                )
            )

        if getattr(
            group,
            "standard_deviation",
            None,
        ) is not None:
            parts.append(
                (
                    "desvio padrão = "
                    f"{self._format_number(group.standard_deviation)}"
                )
            )

        return "\n".join(
            parts
        )

    def _format_number(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return str(
                value
            )

        return (
            f"{number:.4f}"
            .replace(
                ".",
                ",",
            )
        )

    def _autopct(
        self,
        percentage: float,
    ) -> str:
        if percentage < 4.0:
            return ""

        return (
            f"{percentage:.1f}%"
        )

    def _wrap_label(
        self,
        value: Any,
        width: int = 24,
    ) -> str:
        clean = self._display_label(
            value
        )

        return "\n".join(
            textwrap.wrap(
                clean,
                width=max(
                    10,
                    width,
                ),
                break_long_words=False,
                break_on_hyphens=False,
            )
        )

    def _safe_file_name(
        self,
        value: Any,
    ) -> str:
        normalized = (
            unicodedata.normalize(
                "NFKD",
                str(
                    value
                    or "caracteristica"
                ),
            )
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        normalized = (
            normalized.lower()
        )

        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            normalized,
        ).strip(
            "_"
        )

        return (
            normalized[:55]
            or "caracteristica"
        )

    def _clean_axes(
        self,
        axes,
    ) -> None:
        axes.spines[
            "top"
        ].set_visible(
            False
        )

        axes.spines[
            "right"
        ].set_visible(
            False
        )

        axes.spines[
            "left"
        ].set_color(
            self.COLOR_GRID
        )

        axes.spines[
            "bottom"
        ].set_color(
            self.COLOR_GRID
        )