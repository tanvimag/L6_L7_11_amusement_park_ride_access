import pytest
from amusement_park_ride_access import process_ride_admissions, inspect_safety_restraints

# Example test case:
def test_single_adult_family_ride():
    groups = [
        {
            "is_open": True,
            "ride_type": "family",
            "has_fast_lane": False,
            "patrons": [{"height_cm": 150, "health_warning": False, "is_child": False}]
        }
    ]
    result = process_ride_admissions(groups, 5.0)
    assert result["total_revenue"] == 10.0
    assert result["status"] == "COMPLETED"

# ---------- helpers ----------
def make_group(patrons, ride_type="family", is_open=True, has_fast_lane=False):
    return {
        "is_open": is_open,
        "ride_type": ride_type,
        "has_fast_lane": has_fast_lane,
        "patrons": patrons,
    }


def patron(height=150, health=False, child=False):
    return {"height_cm": height, "health_warning": health, "is_child": child}


# ---------- process_ride_admissions: input validation ----------
def test_groups_not_a_list_raises():
    with pytest.raises(ValueError):
        process_ride_admissions("not a list", 5.0)


def test_negative_fee_raises():
    with pytest.raises(ValueError):
        process_ride_admissions([], -1.0)


# ---------- closed rides / defaults ----------
def test_closed_ride_is_skipped():
    result = process_ride_admissions([make_group([patron()], is_open=False)], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_missing_keys_use_defaults_and_skip():
    # no "is_open" key -> treated as closed
    result = process_ride_admissions([{}], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_default_ride_type_is_family():
    group = {"is_open": True, "patrons": [patron()]}  # no ride_type
    result = process_ride_admissions([group], 0.0)
    assert result["total_revenue"] == 10.0


def test_empty_groups_list():
    assert process_ride_admissions([], 5.0) == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


# ---------- ride types ----------
def test_roller_coaster_adult():
    result = process_ride_admissions([make_group([patron()], "roller_coaster")], 0.0)
    assert result == {"total_revenue": 25.0, "status": "COMPLETED"}


def test_water_ride_adult():
    result = process_ride_admissions([make_group([patron()], "water_ride")], 0.0)
    assert result == {"total_revenue": 18.0, "status": "COMPLETED"}


def test_unknown_ride_type_rejected():
    result = process_ride_admissions([make_group([patron()], "bumper_cars")], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


# ---------- patron rules ----------
def test_child_pays_sixty_percent():
    result = process_ride_admissions([make_group([patron(child=True)], "roller_coaster")], 0.0)
    assert result["total_revenue"] == 15.0
    assert result["status"] == "COMPLETED"


def test_zero_or_negative_height_rejected():
    groups = [make_group([patron(height=0), patron(height=-5), patron(height=150)])]
    result = process_ride_admissions(groups, 0.0)
    assert result["total_revenue"] == 10.0


def test_too_short_rejected():
    result = process_ride_admissions([make_group([patron(height=119)])], 0.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_exactly_120cm_allowed():
    result = process_ride_admissions([make_group([patron(height=120)])], 0.0)
    assert result["total_revenue"] == 10.0


def test_health_warning_on_family_ride_only_rejects_that_patron():
    groups = [make_group([patron(health=True), patron()], "family")]
    result = process_ride_admissions(groups, 0.0)
    assert result["total_revenue"] == 10.0
    assert result["status"] == "COMPLETED"


def test_health_warning_on_roller_coaster_voids_group():
    # first patron pays, second has a warning -> whole group total reset to 0 and loop breaks
    groups = [make_group([patron(), patron(health=True), patron()], "roller_coaster")]
    result = process_ride_admissions(groups, 0.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


# ---------- fast lane ----------
def test_fast_lane_fee_added():
    result = process_ride_admissions([make_group([patron()], has_fast_lane=True)], 5.0)
    assert result["total_revenue"] == 15.0


def test_fast_lane_fee_added_even_if_group_voided():
    groups = [make_group([patron(health=True)], "roller_coaster", has_fast_lane=True)]
    result = process_ride_admissions(groups, 5.0)
    assert result == {"total_revenue": 5.0, "status": "COMPLETED"}


# ---------- status outcomes ----------
def test_more_than_four_rejections_triggers_safety_audit():
    groups = [make_group([patron(height=100)] * 5 + [patron()])]
    result = process_ride_admissions(groups, 0.0)
    assert result == {"total_revenue": 10.0, "status": "SAFETY_AUDIT"}


def test_exactly_four_rejections_not_audit():
    groups = [make_group([patron(height=100)] * 4 + [patron()])]
    result = process_ride_admissions(groups, 0.0)
    assert result["status"] == "COMPLETED"


def test_multiple_groups_accumulate_revenue():
    groups = [
        make_group([patron()], "family"),
        make_group([patron(child=True)], "water_ride"),
    ]
    result = process_ride_admissions(groups, 0.0)
    assert result["total_revenue"] == 10.0 + 10.8


# ---------- inspect_safety_restraints ----------
def test_no_data_empty_list():
    assert inspect_safety_restraints([]) == "NO_DATA"


def test_no_data_none():
    assert inspect_safety_restraints(None) == "NO_DATA"


def test_all_latched_is_safe():
    assert inspect_safety_restraints([[1, 1, 1], [1, 1]]) == "SAFE"


def test_single_unlatched_reading_is_safe():
    assert inspect_safety_restraints([[1, 0, 1, 0, 1]]) == "SAFE"


def test_two_consecutive_unlatched_triggers_lock():
    assert inspect_safety_restraints([[1, 0, 0, 1]]) == "EMERGENCY_LOCK"


def test_streak_resets_between_sensors():
    # a trailing 0 on one stream and a leading 0 on the next must not combine
    assert inspect_safety_restraints([[1, 0], [0, 1]]) == "SAFE"


def test_lock_found_in_later_stream():
    assert inspect_safety_restraints([[1, 1], [0, 0]]) == "EMERGENCY_LOCK"


def test_empty_sensor_stream_is_safe():
    assert inspect_safety_restraints([[]]) == "SAFE"