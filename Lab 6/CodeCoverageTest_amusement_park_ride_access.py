import pytest
from amusement_park_ride_access import process_ride_admissions, inspect_safety_restraints


def make_group(patrons, ride_type="family", is_open=True, has_fast_lane=False):
    return {"is_open": is_open, "ride_type": ride_type,
            "has_fast_lane": has_fast_lane, "patrons": patrons}


def patron(height=150, health=False, child=False):
    return {"height_cm": height, "health_warning": health, "is_child": child}


def test_single_adult_family_ride():
    result = process_ride_admissions([make_group([patron()])], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


def test_invalid_input_raises():
    with pytest.raises(ValueError):
        process_ride_admissions("bad", 5.0)


def test_closed_ride_skipped():
    result = process_ride_admissions([make_group([patron()], is_open=False)], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_roller_coaster_and_water_ride_pricing():
    groups = [make_group([patron()], "roller_coaster"),
              make_group([patron(child=True)], "water_ride")]
    result = process_ride_admissions(groups, 0.0)
    assert result["total_revenue"] == 25.0 + 18.0 * 0.6


def test_unknown_ride_type_rejected():
    result = process_ride_admissions([make_group([patron()], "bumper_cars")], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_invalid_and_short_patrons_rejected():
    result = process_ride_admissions([make_group([patron(height=0), patron(height=100), patron()])], 0.0)
    assert result["total_revenue"] == 10.0


def test_health_warning_family_and_roller_coaster():
    groups = [make_group([patron(health=True), patron()], "family"),
              make_group([patron(health=True)], "roller_coaster", has_fast_lane=True)]
    result = process_ride_admissions(groups, 5.0)
    assert result["total_revenue"] == 15.0


def test_safety_audit_status():
    result = process_ride_admissions([make_group([patron(height=100)] * 5 + [patron()])], 0.0)
    assert result["status"] == "SAFETY_AUDIT"


def test_restraints_no_data_lock_and_safe():
    assert inspect_safety_restraints([]) == "NO_DATA"
    assert inspect_safety_restraints([[1, 0, 0]]) == "EMERGENCY_LOCK"
    assert inspect_safety_restraints([[1, 0, 1]]) == "SAFE"
