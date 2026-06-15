import pytest

from lib.time_parser import (
    get_default_meal_time,
    sort_meals_by_time,
    validate_meal_time,
)


def meal_time(**overrides):
    data = {
        "occurred_at": "2026-06-12T19:30:00+08:00",
        "meal_type": "dinner",
        "time_resolution": "inferred",
        "time_assumption": {
            "raw_time_text": "昨天晚上",
            "resolved_occurred_at": "2026-06-12T19:30:00+08:00",
            "timezone": "Asia/Shanghai",
            "date_source": "由当前时间推断昨天日期",
            "time_source": "晚上默认 19:30",
            "default_rule": "早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30",
            "confidence": 0.75,
        },
    }
    data.update(overrides)
    return data


def test_validate_inferred_time_passes():
    assert validate_meal_time(meal_time()) is True


def test_validate_rejects_mismatched_resolved_time():
    invalid = meal_time(
        time_assumption={
            **meal_time()["time_assumption"],
            "resolved_occurred_at": "2026-06-12T20:00:00+08:00",
        }
    )

    with pytest.raises(ValueError, match="occurred_at 与 resolved_occurred_at 不一致"):
        validate_meal_time(invalid)


def test_validate_rejects_unknown_time_resolution():
    invalid = meal_time(time_resolution="unknown")

    with pytest.raises(ValueError, match="无法判断用餐时间"):
        validate_meal_time(invalid)


def test_validate_rejects_confidence_out_of_range():
    invalid = meal_time(
        time_assumption={**meal_time()["time_assumption"], "confidence": 1.2}
    )

    with pytest.raises(ValueError, match="时间置信度必须在 0 到 1 之间"):
        validate_meal_time(invalid)


def test_validate_explicit_time_passes():
    explicit = meal_time(
        occurred_at="2026-06-12T18:45:00+08:00",
        time_resolution="explicit",
        time_assumption={
            **meal_time()["time_assumption"],
            "raw_time_text": "2026年6月12日晚上6点45",
            "resolved_occurred_at": "2026-06-12T18:45:00+08:00",
            "confidence": 0.98,
        },
    )

    assert validate_meal_time(explicit) is True


def test_validate_rejects_iso_datetime_without_timezone():
    invalid = meal_time(
        occurred_at="2026-06-12T19:30:00",
        time_assumption={
            **meal_time()["time_assumption"],
            "resolved_occurred_at": "2026-06-12T19:30:00",
        },
    )

    with pytest.raises(ValueError, match="occurred_at 必须带时区"):
        validate_meal_time(invalid)


def test_get_default_meal_time_returns_expected_values():
    assert get_default_meal_time("breakfast") == "08:00"
    assert get_default_meal_time("lunch") == "12:30"
    assert get_default_meal_time("dinner") == "19:30"
    assert get_default_meal_time("snack") == "22:30"


def test_sort_meals_by_time_orders_descending():
    meals = [
        {"meal_id": "old", "occurred_at": "2026-06-12T12:30:00+08:00"},
        {"meal_id": "new", "occurred_at": "2026-06-13T19:30:00+08:00"},
        {"meal_id": "middle", "occurred_at": "2026-06-13T08:00:00+08:00"},
    ]

    sorted_meals = sort_meals_by_time(meals)

    assert [meal["meal_id"] for meal in sorted_meals] == ["new", "middle", "old"]
