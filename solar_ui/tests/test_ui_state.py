import sys
import types


if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = types.SimpleNamespace(session_state={})

from solar_ui.ui_state import (
    build_scenario_table,
    duplicate_scenario_request,
    remove_scenario_request,
    upsert_scenario_request,
)


BASE_SCENARIO = {
    "name": "Base Variant",
    "payload": {
        "panel_area": 80.0,
        "tilt": 30,
        "ac_capacity_kw": 15.0,
        "system_capex": 60000.0,
        "cleanliness": "normal",
        "shading": "low",
    },
}


def test_upsert_scenario_request_adds_new_scenario():
    updated = upsert_scenario_request(
        [],
        name=BASE_SCENARIO["name"],
        payload=BASE_SCENARIO["payload"],
        editing_index=None,
    )

    assert updated == [BASE_SCENARIO]


def test_upsert_scenario_request_updates_existing_scenario():
    updated = upsert_scenario_request(
        [BASE_SCENARIO],
        name="Updated Variant",
        payload={**BASE_SCENARIO["payload"], "panel_area": 95.0},
        editing_index=0,
    )

    assert updated == [
        {
            "name": "Updated Variant",
            "payload": {
                "panel_area": 95.0,
                "tilt": 30,
                "ac_capacity_kw": 15.0,
                "system_capex": 60000.0,
                "cleanliness": "normal",
                "shading": "low",
            },
        }
    ]


def test_duplicate_and_remove_scenario_request_manage_saved_list():
    duplicated = duplicate_scenario_request([BASE_SCENARIO], 0)

    assert len(duplicated) == 2
    assert duplicated[1]["name"] == "Base Variant Copy"

    remaining = remove_scenario_request(duplicated, 0)

    assert remaining == [duplicated[1]]


def test_build_scenario_table_includes_design_and_loss_columns():
    table = build_scenario_table([BASE_SCENARIO])

    assert table.to_dict(orient="records") == [
        {
            "Scenario": "Base Variant",
            "Panel Area (m²)": 80.0,
            "Tilt (°)": 30,
            "AC Capacity (kW)": 15.0,
            "System CAPEX": 60000.0,
            "Cleanliness": "normal",
            "Shading": "low",
        }
    ]
