from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from typing import Any, Optional

import matplotlib

matplotlib.use(
    "Agg"
)

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from models.statistical_characteristic import (
    StatisticalCharacteristic,
)


class ReportChartService:
    """
    Gera gráficos técnicos a partir do resultado estatístico.

    Nenhum gráfico depende de um nome específico de característica.
    O formato é escolhido conforme:

    - quantidade de unidades;
    - disponibilidade de nominal;
    - disponibilidade de tolerâncias;
    - quantidade de resultados;
    - status de conformidade.
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

        generated_files: list[
            Path
        ] = []

        overall = statistics.get(
            "overall",
            {},
        )

        groups: list[
            StatisticalCharacteristic
        ] = statistics.get(
            "chart_candidates",
            [],
        )

        conformity_chart = (
            output_dir
            / "conformidade_geral.png"
        )

        self.generate_overall_conformity_chart(
            overall=overall,
            output_path=conformity_chart,
        )

        generated_files.append(
            conformity_chart
        )

        group_summary_chart = (
            output_dir
            / "resumo_por_caracteristica.png"
        )

        self.generate_group_summary_chart(
            groups=groups,
            output_path=group_summary_chart,
        )

        if group_summary_chart.exists():
            generated_files.append(
                group_summary_chart
            )

        characteristic_charts = []

        for index, group in enumerate(
            groups[
                :maximum_characteristic_charts
            ],
            start=1,
        ):
            safe_name = self._safe_file_name(
                group.display_name
            )

            output_path = (
                output_dir
                / (
                    f"caracteristica_"
                    f"{index:02d}_"
                    f"{safe_name}.png"
                )
            )

            generated = (
                self.generate_characteristic_chart(
                    group=group,
                    output_path=output_path,
                )
            )

            if generated is not None:
                characteristic_charts.append(
                    {
                        "group":
                            group,

                        "path":
                            generated,
                    }
                )

                generated_files.append(
                    generated
                )

        return {
            "overall_conformity":
                conformity_chart,

            "group_summary":
                (
                    group_summary_chart
                    if group_summary_chart.exists()
                    else None
                ),

            "characteristic_charts":
                characteristic_charts,

            "all_files":
                generated_files,
        }

    # =============================================================
    # CONFORMIDADE GERAL
    # =============================================================

    def generate_overall_conformity_chart(
        self,
        overall: dict[str, Any],
        output_path: str | Path,
    ) -> Path:
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

        labels = []
        values = []
        colors = []

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
            labels = [
                "Sem resultados"
            ]

            values = [
                1
            ]

            colors = [
                self.COLOR_UNKNOWN
            ]

        figure, axes = plt.subplots(
            figsize=(
                7.0,
                3.1,
            ),
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
            autopct=(
                self._autopct
                if sum(
                    values
                ) > 0
                else None
            ),
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

        total = (
            ok_count
            + nok_count
            + unknown_count
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
            (
                "conformidade"
                if total > 0
                else "sem dados"
            ),
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
    # RESUMO POR CARACTERÍSTICA
    # =============================================================

    def generate_group_summary_chart(
        self,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: str | Path,
        maximum_groups: int = 12,
    ) -> Optional[Path]:
        destination = Path(
            output_path
        )

        selected_groups = [
            group
            for group in groups
            if group.count > 0
        ][
            :maximum_groups
        ]

        if not selected_groups:
            return None

        is_batch = any(
            bool(
                getattr(
                    group,
                    "is_batch_characteristic",
                    False,
                )
            )
            or int(
                getattr(
                    group,
                    "valid_numeric_count",
                    0,
                )
                or 0
            ) > 1
            for group in selected_groups
        )

        if is_batch:
            evaluated_results = sum(
                int(
                    getattr(
                        group,
                        "ok_count",
                        0,
                    )
                    or 0
                )
                + int(
                    getattr(
                        group,
                        "nok_count",
                        0,
                    )
                    or 0
                )
                for group in selected_groups
            )

            if evaluated_results > 0:
                return self._generate_conformity_summary_chart(
                    groups=selected_groups,
                    output_path=destination,
                )

            mean_deviation_groups = [
                group
                for group in selected_groups
                if (
                    getattr(
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
                )
            ]

            if mean_deviation_groups:
                return self._generate_batch_mean_deviation_chart(
                    groups=mean_deviation_groups,
                    output_path=destination,
                )

            return None

        tolerance_groups = [
            group
            for group in selected_groups
            if (
                group.valid_numeric_count == 1
                and group.lower_limit is not None
                and group.upper_limit is not None
                and group.upper_limit != group.lower_limit
            )
        ]

        if tolerance_groups:
            return self._generate_tolerance_position_chart(
                groups=tolerance_groups,
                output_path=destination,
            )

        deviation_groups = [
            group
            for group in selected_groups
            if (
                group.valid_numeric_count == 1
                and group.nominal_value is not None
                and self._first_numeric_value(
                    group
                ) is not None
            )
        ]

        if deviation_groups:
            return self._generate_deviation_from_nominal_chart(
                groups=deviation_groups,
                output_path=destination,
            )

        return None

    def _generate_tolerance_position_chart(
        self,
        *,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: Path,
    ) -> Optional[Path]:
        labels = []
        positions = []
        colors = []

        for group in groups:
            measured_value = self._first_numeric_value(
                group
            )

            if measured_value is None:
                continue

            lower = float(
                group.lower_limit
            )

            upper = float(
                group.upper_limit
            )

            tolerance_range = (
                upper - lower
            )

            if tolerance_range == 0:
                continue

            normalized = (
                (
                    measured_value
                    - lower
                )
                / tolerance_range
                * 100.0
            )

            labels.append(
                self._short_label(
                    group.display_name,
                    maximum_length=30,
                )
            )

            positions.append(
                normalized
            )

            status = self._first_measurement_status(
                group
            )

            colors.append(
                (
                    self.COLOR_NOK
                    if status == "NOK"
                    else (
                        self.COLOR_OK
                        if status == "OK"
                        else self.COLOR_BLUE
                    )
                )
            )

        if not positions:
            return None

        figure_height = max(
            3.2,
            len(labels) * 0.42 + 1.35,
        )

        figure, axes = plt.subplots(
            figsize=(
                8.4,
                figure_height,
            ),
            dpi=160,
        )

        figure.patch.set_facecolor(
            self.COLOR_BACKGROUND
        )

        axes.set_facecolor(
            self.COLOR_BACKGROUND
        )

        y_values = list(
            range(
                len(labels)
            )
        )

        axes.axvspan(
            0,
            100,
            color=self.COLOR_OK,
            alpha=0.07,
            zorder=0,
        )

        axes.axvline(
            0,
            color=self.COLOR_LIMIT,
            linewidth=1.1,
            linestyle=":",
            label="Limites de tolerância",
            zorder=1,
        )

        axes.axvline(
            100,
            color=self.COLOR_LIMIT,
            linewidth=1.1,
            linestyle=":",
            zorder=1,
        )

        axes.axvline(
            50,
            color=self.COLOR_NOMINAL,
            linewidth=0.9,
            linestyle="--",
            alpha=0.70,
            label="Centro da faixa",
            zorder=1,
        )

        axes.scatter(
            positions,
            y_values,
            s=64,
            c=colors,
            edgecolors=self.COLOR_BACKGROUND,
            linewidths=0.8,
            zorder=3,
        )

        axes.set_yticks(
            y_values
        )

        axes.set_yticklabels(
            labels,
            fontsize=8,
        )

        axes.invert_yaxis()

        minimum_x = min(
            -10.0,
            min(positions) - 8.0,
        )

        maximum_x = max(
            110.0,
            max(positions) + 8.0,
        )

        axes.set_xlim(
            minimum_x,
            maximum_x,
        )

        axes.set_xlabel(
            (
                "Posição do valor medido na faixa de tolerância "
                "(0% = limite inferior; 100% = limite superior)"
            ),
            fontsize=8.0,
        )

        axes.set_title(
            "Posição das características na faixa de tolerância",
            fontsize=11,
            fontweight="bold",
            color=self.COLOR_NAVY,
            pad=10,
        )

        axes.grid(
            axis="x",
            color=self.COLOR_GRID,
            linewidth=0.6,
            alpha=0.72,
        )

        axes.set_axisbelow(
            True
        )

        self._clean_axes(
            axes
        )

        handles, legend_labels = (
            axes.get_legend_handles_labels()
        )

        if handles:
            axes.legend(
                handles,
                legend_labels,
                loc="lower center",
                bbox_to_anchor=(
                    0.5,
                    -0.28,
                ),
                ncol=2,
                frameon=False,
                fontsize=7.5,
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

    def _generate_deviation_from_nominal_chart(
        self,
        *,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: Path,
    ) -> Optional[Path]:
        rows = []

        for group in groups:
            measured = self._first_numeric_value(
                group
            )

            if measured is None:
                continue

            try:
                nominal = float(
                    group.nominal_value
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            deviation = (
                measured - nominal
            )

            unit = str(
                getattr(
                    group,
                    "unit",
                    "",
                )
                or ""
            ).strip()

            rows.append(
                (
                    self._short_label(
                        group.display_name,
                        maximum_length=30,
                    ),
                    deviation,
                    unit,
                    self._first_measurement_status(
                        group
                    ),
                )
            )

        if not rows:
            return None

        units = {
            unit
            for _, _, unit, _ in rows
            if unit
        }

        if len(units) > 1:
            return None

        labels = [
            row[0]
            for row in rows
        ]

        deviations = [
            row[1]
            for row in rows
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
            for _, _, _, status in rows
        ]

        unit = next(
            iter(units),
            "",
        )

        figure_height = max(
            3.2,
            len(rows) * 0.42 + 1.30,
        )

        figure, axes = plt.subplots(
            figsize=(
                8.4,
                figure_height,
            ),
            dpi=160,
        )

        figure.patch.set_facecolor(
            self.COLOR_BACKGROUND
        )

        axes.set_facecolor(
            self.COLOR_BACKGROUND
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
            f"Desvio em relação ao nominal ({unit})"
            if unit
            else "Desvio em relação ao nominal"
        )

        axes.set_xlabel(
            axis_label,
            fontsize=8.3,
        )

        axes.set_title(
            "Desvio em relação ao valor nominal",
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
            offset = (
                4
                if value >= 0
                else -4
            )

            alignment = (
                "left"
                if value >= 0
                else "right"
            )

            axes.annotate(
                self._format_number(
                    value
                ),
                xy=(
                    value,
                    y,
                ),
                xytext=(
                    offset,
                    0,
                ),
                textcoords="offset points",
                ha=alignment,
                va="center",
                fontsize=7.5,
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

    def _generate_batch_mean_deviation_chart(
        self,
        *,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: Path,
    ) -> Optional[Path]:
        rows = []

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

            unit = str(
                getattr(
                    group,
                    "unit",
                    "",
                )
                or ""
            ).strip()

            rows.append(
                (
                    self._short_label(
                        group.display_name,
                        maximum_length=30,
                    ),
                    mean_value - nominal_value,
                    unit,
                )
            )

        if not rows:
            return None

        units = {
            unit
            for _, _, unit in rows
            if unit
        }

        # Não mistura grandezas incompatíveis no mesmo eixo.
        if len(units) > 1:
            return None

        labels = [
            label
            for label, _, _ in rows
        ]

        deviations = [
            deviation
            for _, deviation, _ in rows
        ]

        unit = next(
            iter(units),
            "",
        )

        figure_height = max(
            3.2,
            len(rows) * 0.42 + 1.35,
        )

        figure, axes = plt.subplots(
            figsize=(
                8.4,
                figure_height,
            ),
            dpi=160,
        )

        figure.patch.set_facecolor(
            self.COLOR_BACKGROUND
        )

        axes.set_facecolor(
            self.COLOR_BACKGROUND
        )

        positions = list(
            range(
                len(rows)
            )
        )

        axes.barh(
            positions,
            deviations,
            color=self.COLOR_BLUE,
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
            offset = (
                4
                if value >= 0
                else -4
            )

            alignment = (
                "left"
                if value >= 0
                else "right"
            )

            axes.annotate(
                self._format_number(
                    value
                ),
                xy=(
                    value,
                    y,
                ),
                xytext=(
                    offset,
                    0,
                ),
                textcoords="offset points",
                ha=alignment,
                va="center",
                fontsize=7.5,
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

    def _generate_conformity_summary_chart(
        self,
        *,
        groups: list[
            StatisticalCharacteristic
        ],
        output_path: Path,
    ) -> Path:
        labels = [
            self._short_label(
                group.display_name,
                maximum_length=30,
            )
            for group in groups
        ]

        ok_values = [
            group.ok_count
            for group in groups
        ]

        nok_values = [
            group.nok_count
            for group in groups
        ]

        unknown_values = [
            group.unknown_count
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

    def _first_numeric_value(
        self,
        group: StatisticalCharacteristic,
    ) -> Optional[float]:
        for measurement in group.measurements:
            if measurement.measured_value is None:
                continue

            try:
                return float(
                    measurement.measured_value
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

    def _first_measurement_status(
        self,
        group: StatisticalCharacteristic,
    ) -> str:
        for measurement in group.measurements:
            if measurement.measured_value is None:
                continue

            return str(
                measurement.status
                or ""
            ).upper()

        return ""

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

    # =============================================================
    # GRÁFICO INDIVIDUAL
    # =============================================================

    def generate_characteristic_chart(
        self,
        group: StatisticalCharacteristic,
        output_path: str | Path,
    ) -> Optional[Path]:
        values = []
        labels = []
        statuses = []

        for measurement in group.measurements:
            if measurement.measured_value is None:
                continue

            labels.append(
                measurement.unit_identifier
            )

            values.append(
                float(
                    measurement.measured_value
                )
            )

            statuses.append(
                measurement.status
            )

        if not values:
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
                len(
                    values
                ) + 1
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

        if len(
            values
        ) >= 2:
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

        if group.nominal_value is not None:
            axes.axhline(
                group.nominal_value,
                color=self.COLOR_NOMINAL,
                linewidth=1.2,
                linestyle="--",
                label=(
                    "Nominal "
                    f"({self._format_number(group.nominal_value)})"
                ),
            )

        if group.lower_limit is not None:
            axes.axhline(
                group.lower_limit,
                color=self.COLOR_LIMIT,
                linewidth=1.1,
                linestyle=":",
                label=(
                    "Limite inferior "
                    f"({self._format_number(group.lower_limit)})"
                ),
            )

        if group.upper_limit is not None:
            axes.axhline(
                group.upper_limit,
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
                if len(
                    labels
                ) > 7
                else 0
            ),
            ha=(
                "right"
                if len(
                    labels
                ) > 7
                else "center"
            ),
        )

        y_label = (
            f"Valor medido ({group.unit})"
            if group.unit
            else "Valor medido"
        )

        axes.set_ylabel(
            y_label,
            fontsize=8.5,
        )

        axes.set_xlabel(
            (
                "Unidades do lote"
                if group.is_batch_characteristic
                else "Medição"
            ),
            fontsize=8.5,
        )

        title_parts = [
            group.display_name
        ]

        if group.group_name:
            title_parts.append(
                group.group_name
            )

        axes.set_title(
            " · ".join(
                title_parts
            ),
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

        handles, legend_labels = (
            axes.get_legend_handles_labels()
        )

        if handles:
            axes.legend(
                handles,
                legend_labels,
                loc="upper center",
                bbox_to_anchor=(
                    0.5,
                    -0.22,
                ),
                ncol=min(
                    3,
                    len(
                        handles
                    ),
                ),
                frameon=False,
                fontsize=7.5,
            )

        statistics_text = self._statistics_text(
            group
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

    def _statistics_text(
        self,
        group: StatisticalCharacteristic,
    ) -> str:
        parts = [
            (
                f"n = "
                f"{group.valid_numeric_count}"
            )
        ]

        if group.mean is not None:
            parts.append(
                (
                    "média = "
                    f"{self._format_number(group.mean)}"
                )
            )

        if group.minimum is not None:
            parts.append(
                (
                    "mín. = "
                    f"{self._format_number(group.minimum)}"
                )
            )

        if group.maximum is not None:
            parts.append(
                (
                    "máx. = "
                    f"{self._format_number(group.maximum)}"
                )
            )

        if group.standard_deviation is not None:
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
        value,
    ) -> str:
        if value is None:
            return "-"

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

        return f"{number:.4f}"

    def _autopct(
        self,
        percentage: float,
    ) -> str:
        if percentage < 4.0:
            return ""

        return f"{percentage:.1f}%"

    def _short_label(
        self,
        value: str,
        maximum_length: int,
    ) -> str:
        clean = " ".join(
            str(
                value
                or "Característica"
            ).split()
        )

        if len(
            clean
        ) <= maximum_length:
            return clean

        return (
            clean[
                :maximum_length - 1
            ]
            + "…"
        )

    def _safe_file_name(
        self,
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            str(
                value
                or "caracteristica"
            ),
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        normalized = normalized.lower()

        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            normalized,
        ).strip(
            "_"
        )

        return (
            normalized[
                :55
            ]
            or "caracteristica"
        )