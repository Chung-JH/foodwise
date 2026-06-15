from lib import remark
from lib.llm import LLMError


def profile(avoid_ingredients=None, remark_habits=None):
    return {
        "avoid_ingredients": avoid_ingredients or [],
        "remark_habits": remark_habits or [],
    }


def dish(category, remark_rules=None):
    return {
        "name": f"测试{category}",
        "category": category,
        "remark_rules": remark_rules or [],
    }


def test_rule_remark_includes_all_avoid_ingredients():
    text = remark.generate_remark(
        profile(avoid_ingredients=["香菜", "葱"], remark_habits=["少油"]),
        [dish("盖饭类")],
        use_llm=False,
    )

    assert "不要香菜" in text
    assert "不要葱" in text


def test_rule_remark_deduplicates_habits_and_dish_rules():
    text = remark.generate_remark(
        profile(avoid_ingredients=["香菜"], remark_habits=["少油", "不要香菜"]),
        [dish("盖饭类", remark_rules=["少油", "米饭少一点"])],
        use_llm=False,
    )

    assert text.count("少油") == 1
    assert text.count("不要香菜") == 1
    assert text.count("米饭少一点") == 1


def test_gaifan_remark_adds_less_rice():
    text = remark.generate_remark(profile(), [dish("盖饭类")], use_llm=False)

    assert "米饭少一点" in text


def test_noodle_remark_adds_less_soup():
    text = remark.generate_remark(profile(), [dish("粉面类")], use_llm=False)

    assert "汤少一点" in text


def test_light_meal_remark_adds_separate_sauce():
    text = remark.generate_remark(profile(), [dish("轻食类")], use_llm=False)

    assert "酱料分开放" in text


def test_remark_ends_with_thanks():
    text = remark.generate_remark(profile(remark_habits=["少油"]), [dish("盖饭类")], use_llm=False)

    assert text.endswith("谢谢。")


def test_llm_mode_returns_llm_remark(monkeypatch):
    monkeypatch.setattr(remark, "_generate_remark_llm", lambda user_profile, dishes: "少油，谢谢。")

    text = remark.generate_remark(
        profile(avoid_ingredients=["香菜"]),
        [dish("盖饭类")],
        use_llm=True,
    )

    assert text == "少油，不要香菜，谢谢。"


def test_llm_failure_falls_back_to_rule(monkeypatch):
    def fail_llm(user_profile, dishes):
        raise LLMError("LLM 不可用")

    monkeypatch.setattr(remark, "_generate_remark_llm", fail_llm)

    text = remark.generate_remark(
        profile(avoid_ingredients=["香菜"], remark_habits=["少油"]),
        [dish("盖饭类")],
        use_llm=True,
    )

    assert "少油" in text
    assert "不要香菜" in text
    assert "米饭少一点" in text
    assert text.endswith("谢谢。")
