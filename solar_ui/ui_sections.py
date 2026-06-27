from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import plotly.express as px
import streamlit as st  # type: ignore

try:
    from solar_ui.payloads import format_payback_years
except ModuleNotFoundError:
    from payloads import format_payback_years


MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def render_section_intro(title: str, description: str, tip: str | None = None) -> None:
    st.subheader(title)
    st.caption(description)
    if tip:
        st.info(tip)


def render_metadata_table(rows: list[dict[str, Any]]) -> None:
    metadata_df = pd.DataFrame(rows)
    for column in metadata_df.columns:
        metadata_df[column] = metadata_df[column].astype(str)
    st.dataframe(metadata_df, width="stretch", hide_index=True)


def render_summary_cards(forecast_data: dict[str, Any]) -> None:
    assumptions = forecast_data["financial_assumptions"]
    value_label = f"{forecast_data['yearly_estimated_value']} {assumptions['currency']}"

    metric_columns = st.columns(4)
    metric_columns[0].metric("Yearly Energy", f"{forecast_data['yearly_kwh']} kWh")
    metric_columns[1].metric("Yearly Value", value_label)
    metric_columns[2].metric(
        "Annual Savings",
        f"{forecast_data['annual_savings']} {assumptions['currency']}",
    )
    metric_columns[3].metric(
        "Simple Payback",
        format_payback_years(forecast_data.get("simple_payback_years")),
    )

    performance_columns = st.columns(4)
    performance_columns[0].metric(
        "Specific Yield",
        f"{forecast_data['specific_yield_kwh_per_kwp']} kWh/kWp",
    )
    performance_columns[1].metric(
        "Average Daily Energy",
        f"{forecast_data['avg_daily_kwh']} kWh",
    )
    performance_columns[2].metric("Forecast Year", forecast_data["forecast_year"])
    performance_columns[3].metric(
        "Model Used",
        forecast_data["model_type_used"].upper(),
    )

    reference_year = forecast_data.get("weather_reference_year")
    reference_value = "ML profile" if reference_year is None else str(reference_year)
    assumptions_columns = st.columns(3)
    assumptions_columns[0].metric("Weather Basis", reference_value)
    assumptions_columns[1].metric(
        "Tariff Assumption",
        f"{assumptions['electricity_price_per_kwh']} {assumptions['currency']}/kWh",
    )
    assumptions_columns[2].metric(
        "System CAPEX",
        f"{assumptions['system_capex']} {assumptions['currency']}",
    )


def render_overview_tab(forecast_data: dict[str, Any]) -> None:
    render_summary_cards(forecast_data)

    if forecast_data.get("fallback_reason"):
        st.warning(forecast_data["fallback_reason"])

    monthly_df = pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Energy (kWh)": forecast_data["monthly_kwh"],
            "Estimated Value": forecast_data["monthly_estimated_value"],
        }
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        energy_chart = px.bar(
            monthly_df,
            x="Month",
            y="Energy (kWh)",
            title="Monthly Energy Forecast",
            color="Energy (kWh)",
            color_continuous_scale="YlOrBr",
        )
        energy_chart.update_layout(coloraxis_showscale=False)
        st.plotly_chart(energy_chart, width="stretch")

    with chart_columns[1]:
        value_chart = px.line(
            monthly_df,
            x="Month",
            y="Estimated Value",
            markers=True,
            title="Monthly Estimated Financial Value",
        )
        value_chart.update_layout(hovermode="x unified")
        st.plotly_chart(value_chart, width="stretch")

    with st.expander("Forecast Metadata and Assumptions", expanded=False):
        metadata_rows = [
            {"Field": "Requested model", "Value": forecast_data["model_type_requested"]},
            {"Field": "Model used", "Value": forecast_data["model_type_used"]},
            {"Field": "Forecast year", "Value": forecast_data["forecast_year"]},
            {
                "Field": "Archived weather reference year",
                "Value": forecast_data.get("weather_reference_year") or "Not used",
            },
            {
                "Field": "ML training years",
                "Value": ", ".join(map(str, forecast_data.get("training_years_used", [])))
                or "Not used",
            },
            {
                "Field": "Tariff assumption",
                "Value": (
                    f"{forecast_data['financial_assumptions']['electricity_price_per_kwh']} "
                    f"{forecast_data['financial_assumptions']['currency']}/kWh"
                ),
            },
            {
                "Field": "System CAPEX",
                "Value": (
                    f"{forecast_data['financial_assumptions']['system_capex']} "
                    f"{forecast_data['financial_assumptions']['currency']}"
                ),
            },
            {
                "Field": "Annual savings assumption",
                "Value": forecast_data["financial_assumptions"]["annual_savings_basis"],
            },
            {
                "Field": "Payback assumption",
                "Value": forecast_data["financial_assumptions"]["payback_basis"],
            },
        ]
        render_metadata_table(metadata_rows)

        if forecast_data.get("ml_metadata"):
            st.markdown("**ML training diagnostics**")
            st.json(forecast_data["ml_metadata"])


def render_daily_tab(daily_data: dict[str, Any]) -> None:
    assumptions = daily_data["financial_assumptions"]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Daily Energy", f"{daily_data['daily_kwh']} kWh")
    metric_columns[1].metric(
        "Estimated Daily Value",
        f"{daily_data['estimated_daily_value']} {assumptions['currency']}",
    )
    metric_columns[2].metric("Average Power", f"{daily_data['avg_kw']} kW")
    metric_columns[3].metric("System Loss Factor", daily_data["system_loss_factor"])

    if daily_data.get("hourly_time"):
        time_labels = [
            timestamp.split("T")[1][:5] if "T" in timestamp else timestamp
            for timestamp in daily_data["hourly_time"]
        ]
    else:
        time_labels = [f"{hour:02d}:00" for hour in range(len(daily_data["hourly_ac_kw"]))]

    daily_df = pd.DataFrame({"Time": time_labels, "AC Power (kW)": daily_data["hourly_ac_kw"]})
    power_chart = px.line(
        daily_df,
        x="Time",
        y="AC Power (kW)",
        title=f"Hourly Production ({daily_data.get('timezone', 'UTC')})",
        markers=True,
    )
    power_chart.update_layout(hovermode="x unified")
    st.plotly_chart(power_chart, width="stretch")

    with st.expander("Daily Simulation Details", expanded=False):
        st.caption(
            f"Tariff: {assumptions['electricity_price_per_kwh']} {assumptions['currency']}/kWh | "
            f"System CAPEX: {assumptions['system_capex']} {assumptions['currency']}"
        )
        st.dataframe(daily_df, width="stretch", hide_index=True)


def render_last_run_summary(last_run_payload: Mapping[str, Any]) -> None:
    run_rows = [
        {"Parameter": "Panel Area (m²)", "Value": str(last_run_payload["panel_area"])},
        {
            "Parameter": "Inverter AC Capacity (kW)",
            "Value": str(last_run_payload["ac_capacity_kw"]),
        },
        {"Parameter": "System CAPEX", "Value": str(last_run_payload["system_capex"])},
        {"Parameter": "Panel Efficiency", "Value": str(last_run_payload["panel_efficiency"])},
        {"Parameter": "Tilt (°)", "Value": str(last_run_payload["tilt"])},
        {"Parameter": "Model Type", "Value": str(last_run_payload["model_type"])},
    ]
    st.caption("Displayed results are based on the last executed forecast payload.")
    st.dataframe(pd.DataFrame(run_rows), width="stretch", hide_index=True)


def render_last_benchmark_summary(last_benchmark_payload: Mapping[str, Any]) -> None:
    run_rows = [
        {"Parameter": "Benchmark End Year", "Value": str(last_benchmark_payload["year"])},
        {
            "Parameter": "Benchmark Window (years)",
            "Value": str(last_benchmark_payload["benchmark_years"]),
        },
        {"Parameter": "Panel Area (m²)", "Value": str(last_benchmark_payload["panel_area"])},
        {
            "Parameter": "Inverter AC Capacity (kW)",
            "Value": str(last_benchmark_payload["ac_capacity_kw"]),
        },
        {
            "Parameter": "ML Training Window",
            "Value": str(last_benchmark_payload["training_years"]),
        },
    ]
    st.caption("Displayed benchmark results are based on the last executed benchmark payload.")
    st.dataframe(pd.DataFrame(run_rows), width="stretch", hide_index=True)


def render_accuracy_tab(accuracy_data: dict[str, Any]) -> None:
    assumptions = accuracy_data["financial_assumptions"]
    delta_percent = 0.0
    if accuracy_data["actual_yearly_kwh"] != 0:
        delta_percent = round(
            100
            * (
                accuracy_data["predicted_yearly_kwh"]
                - accuracy_data["actual_yearly_kwh"]
            )
            / accuracy_data["actual_yearly_kwh"],
            2,
        )

    metrics = st.columns(4)
    metrics[0].metric("Monthly MAPE", f"{accuracy_data['mape_percent']}%")
    metrics[1].metric("Yearly MAPE", f"{accuracy_data['yearly_mape_percent']}%")
    metrics[2].metric("Quality", accuracy_data["quality"])
    metrics[3].metric("Energy Bias", f"{delta_percent:+.2f}%")

    monthly_df = pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Predicted Energy (kWh)": accuracy_data["predicted_monthly_kwh"],
            "Actual Energy (kWh)": accuracy_data["actual_monthly_kwh"],
        }
    )
    monthly_long = monthly_df.melt(
        id_vars="Month",
        value_vars=["Predicted Energy (kWh)", "Actual Energy (kWh)"],
        var_name="Series",
        value_name="Energy (kWh)",
    )
    energy_chart = px.bar(
        monthly_long,
        x="Month",
        y="Energy (kWh)",
        color="Series",
        barmode="group",
        title="Predicted vs Actual Monthly Energy",
    )
    st.plotly_chart(energy_chart, width="stretch")

    value_df = pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Predicted Value": accuracy_data["predicted_monthly_estimated_value"],
            "Actual Value": accuracy_data["actual_monthly_estimated_value"],
        }
    )
    value_long = value_df.melt(
        id_vars="Month",
        value_vars=["Predicted Value", "Actual Value"],
        var_name="Series",
        value_name=f"Value ({assumptions['currency']})",
    )
    value_chart = px.line(
        value_long,
        x="Month",
        y=f"Value ({assumptions['currency']})",
        color="Series",
        markers=True,
        title="Predicted vs Actual Monthly Value",
    )
    value_chart.update_layout(hovermode="x unified")
    st.plotly_chart(value_chart, width="stretch")

    if accuracy_data.get("fallback_reason"):
        st.warning(accuracy_data["fallback_reason"])

    with st.expander("Backtest Metadata", expanded=False):
        metadata_rows = [
            {"Field": "Evaluation year", "Value": accuracy_data["year"]},
            {"Field": "Requested model", "Value": accuracy_data["model_type_requested"]},
            {"Field": "Model used", "Value": accuracy_data["model_type_used"]},
            {
                "Field": "Weather reference year",
                "Value": accuracy_data.get("weather_reference_year") or "ML profile",
            },
            {
                "Field": "ML training years",
                "Value": ", ".join(map(str, accuracy_data.get("training_years_used", [])))
                or "Not used",
            },
            {
                "Field": "Predicted annual savings",
                "Value": (
                    f"{accuracy_data['predicted_annual_savings']} "
                    f"{accuracy_data['financial_assumptions']['currency']}"
                ),
            },
            {
                "Field": "Predicted simple payback",
                "Value": format_payback_years(accuracy_data.get("predicted_simple_payback_years")),
            },
            {
                "Field": "System CAPEX",
                "Value": (
                    f"{accuracy_data['financial_assumptions']['system_capex']} "
                    f"{accuracy_data['financial_assumptions']['currency']}"
                ),
            },
        ]
        render_metadata_table(metadata_rows)

        if accuracy_data.get("ml_metadata"):
            st.markdown("**ML diagnostics**")
            st.json(accuracy_data["ml_metadata"])


def render_benchmark_tab(benchmark_data: dict[str, Any]) -> None:
    st.info(benchmark_data["reference_note"])

    explanation_columns = st.columns(len(benchmark_data["approaches"]))
    for index, approach in enumerate(benchmark_data["approaches"]):
        explanation_columns[index].markdown(f"**{approach['label']}**")
        explanation_columns[index].caption(approach["description"])

    summary_rows = []
    metric_chart_rows: list[dict[str, Any]] = []
    yearly_chart_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []

    actual_series = benchmark_data["approaches"][0]["yearly_results"]
    for result in actual_series:
        yearly_chart_rows.append(
            {
                "Year": result["year"],
                "Series": "Actual reference",
                "Yearly Energy (kWh)": result["actual_yearly_kwh"],
            }
        )

    for approach in benchmark_data["approaches"]:
        metrics = approach["metrics"]
        fallback_years = ", ".join(map(str, approach["fallback_years"])) or "None"
        summary_rows.append(
            {
                "Approach": approach["label"],
                "Monthly MAPE (%)": metrics["monthly_mape_percent"],
                "Monthly MAE (kWh)": metrics["monthly_mae_kwh"],
                "Yearly MAPE (%)": metrics["yearly_mape_percent"],
                "Yearly MAE (kWh)": metrics["yearly_mae_kwh"],
                "Bias (%)": metrics["bias_percent"],
                "Bias (kWh/year)": metrics["bias_kwh"],
                "Fallback Years": fallback_years,
            }
        )
        metric_chart_rows.extend(
            [
                {
                    "Approach": approach["label"],
                    "Metric": "Monthly MAPE (%)",
                    "Value": metrics["monthly_mape_percent"],
                },
                {
                    "Approach": approach["label"],
                    "Metric": "Yearly MAPE (%)",
                    "Value": metrics["yearly_mape_percent"],
                },
                {
                    "Approach": approach["label"],
                    "Metric": "Bias (%)",
                    "Value": metrics["bias_percent"],
                },
            ]
        )
        for result in approach["yearly_results"]:
            yearly_chart_rows.append(
                {
                    "Year": result["year"],
                    "Series": approach["label"],
                    "Yearly Energy (kWh)": result["predicted_yearly_kwh"],
                }
            )
            detail_rows.append(
                {
                    "Approach": approach["label"],
                    "Year": result["year"],
                    "Actual Energy (kWh)": result["actual_yearly_kwh"],
                    "Predicted Energy (kWh)": result["predicted_yearly_kwh"],
                    "Yearly MAPE (%)": result["yearly_mape_percent"],
                    "Bias (kWh)": result["yearly_bias_kwh"],
                    "Model Used": result["model_type_used"],
                    "Reference Year": result["weather_reference_year"] or "Climatology / ML",
                    "Fallback": result["fallback_reason"] or "",
                }
            )

    best_yearly = min(summary_rows, key=lambda row: row["Yearly MAPE (%)"])
    best_monthly = min(summary_rows, key=lambda row: row["Monthly MAPE (%)"])
    lowest_bias = min(summary_rows, key=lambda row: abs(row["Bias (%)"]))

    summary_cards = st.columns(3)
    summary_cards[0].metric(
        "Best Yearly Fit",
        best_yearly["Approach"],
        f"{best_yearly['Yearly MAPE (%)']}% yearly MAPE",
    )
    summary_cards[1].metric(
        "Best Monthly Fit",
        best_monthly["Approach"],
        f"{best_monthly['Monthly MAPE (%)']}% monthly MAPE",
    )
    summary_cards[2].metric(
        "Lowest Bias",
        lowest_bias["Approach"],
        f"{lowest_bias['Bias (%)']}% bias",
    )

    st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        yearly_chart = px.line(
            pd.DataFrame(yearly_chart_rows),
            x="Year",
            y="Yearly Energy (kWh)",
            color="Series",
            markers=True,
            title="Historical Benchmark: Actual Reference vs Forecasted Energy",
        )
        yearly_chart.update_layout(hovermode="x unified")
        st.plotly_chart(yearly_chart, width="stretch")

    with chart_columns[1]:
        metric_chart = px.bar(
            pd.DataFrame(metric_chart_rows),
            x="Approach",
            y="Value",
            color="Metric",
            barmode="group",
            title="Benchmark Error Profile",
        )
        st.plotly_chart(metric_chart, width="stretch")

    with st.expander("Year-by-Year Benchmark Details", expanded=False):
        st.dataframe(pd.DataFrame(detail_rows), width="stretch", hide_index=True)


def render_comparison_tab(comparison_data: dict[str, Any]) -> None:
    if comparison_data.get("fallback_reason"):
        st.warning(comparison_data["fallback_reason"])

    assumptions = comparison_data["results"][0]["financial_assumptions"]
    monthly_chart_rows: list[dict[str, Any]] = []
    for result in comparison_data["results"]:
        scenario_label = result["scenario"]["name"]
        for month_name, monthly_value in zip(MONTH_NAMES, result["monthly_kwh"]):
            monthly_chart_rows.append(
                {"Month": month_name, "Scenario": scenario_label, "Energy (kWh)": monthly_value}
            )
    monthly_chart_df = pd.DataFrame(monthly_chart_rows)
    monthly_chart = px.line(
        monthly_chart_df,
        x="Month",
        y="Energy (kWh)",
        color="Scenario",
        markers=True,
        title="Scenario Comparison by Month",
    )
    monthly_chart.update_layout(hovermode="x unified")

    summary_rows = []
    financial_chart_rows: list[dict[str, Any]] = []
    for result in comparison_data["results"]:
        scenario_label = result["scenario"]["name"]
        summary_rows.append(
            {
                "Scenario": scenario_label,
                "Yearly Energy (kWh)": result["yearly_kwh"],
                "Energy Change (%)": result["deviation_percent"],
                "Yearly Value": result["yearly_estimated_value"],
                "Annual Savings": result["annual_savings"],
                "Simple Payback (years)": result["simple_payback_years"],
                "Payback Delta (years)": result["payback_delta_years"],
                "Value Change (%)": result["value_deviation_percent"],
            }
        )
        financial_chart_rows.append(
            {
                "Scenario": scenario_label,
                "Metric": "Yearly Value",
                "Value": result["yearly_estimated_value"],
            }
        )
        financial_chart_rows.append(
            {
                "Scenario": scenario_label,
                "Metric": "Annual Savings",
                "Value": result["annual_savings"],
            }
        )

    best_energy = max(summary_rows, key=lambda row: row["Yearly Energy (kWh)"])
    best_value = max(summary_rows, key=lambda row: row["Yearly Value"])
    viable_paybacks = [
        row for row in summary_rows if not pd.isna(row["Simple Payback (years)"])
    ]

    summary_cards = st.columns(3)
    summary_cards[0].metric(
        "Highest Energy",
        best_energy["Scenario"],
        f"{best_energy['Yearly Energy (kWh)']} kWh/year",
    )
    summary_cards[1].metric(
        "Highest Value",
        best_value["Scenario"],
        f"{best_value['Yearly Value']} {assumptions['currency']}/year",
    )
    if viable_paybacks:
        fastest_payback = min(viable_paybacks, key=lambda row: row["Simple Payback (years)"])
        summary_cards[2].metric(
            "Fastest Payback",
            fastest_payback["Scenario"],
            format_payback_years(fastest_payback["Simple Payback (years)"]),
        )
    else:
        summary_cards[2].metric("Fastest Payback", "No viable case", "CAPEX too high")

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.plotly_chart(monthly_chart, width="stretch")

    with chart_columns[1]:
        financial_chart = px.bar(
            pd.DataFrame(financial_chart_rows),
            x="Scenario",
            y="Value",
            color="Metric",
            barmode="group",
            title=f"Scenario Financial Outcome ({assumptions['currency']})",
        )
        st.plotly_chart(financial_chart, width="stretch")

    summary_df = pd.DataFrame(summary_rows)
    summary_df["Simple Payback (years)"] = summary_df["Simple Payback (years)"].apply(
        format_payback_years
    )
    summary_df["Payback Delta (years)"] = summary_df["Payback Delta (years)"].apply(
        lambda value: "N/A" if pd.isna(value) else value
    )
    st.dataframe(summary_df, width="stretch", hide_index=True)
