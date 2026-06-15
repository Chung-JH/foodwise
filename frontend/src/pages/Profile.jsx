import { useEffect, useMemo, useState } from "react";
import BudgetSlider from "../components/BudgetSlider.jsx";

const mealLabels = {
  breakfast: "早餐预算",
  lunch: "午餐预算",
  dinner: "晚餐预算",
};

const healthGoalOptions = ["少油", "高蛋白", "低碳水", "多蔬菜"];

const emptyForm = {
  name: "",
  taste_description: "",
  taste_tags: [],
  avoid_ingredients: "",
  health_goals: [],
  default_budget: {
    breakfast: [8, 15],
    lunch: [15, 30],
    dinner: [20, 40],
  },
  remark_habits: "",
};

function listToText(value) {
  return Array.isArray(value) ? value.join("，") : "";
}

function textToList(value) {
  return value.replace(/，/g, ",").split(",").map((s) => s.trim()).filter(Boolean);
}

function profileToForm(profile) {
  return {
    ...emptyForm,
    name: profile?.name || "",
    taste_description: profile?.taste_description || "",
    taste_tags: Array.isArray(profile?.taste_tags) ? profile.taste_tags : [],
    avoid_ingredients: listToText(profile?.avoid_ingredients),
    health_goals: Array.isArray(profile?.health_goals) ? profile.health_goals : [],
    default_budget: { ...emptyForm.default_budget, ...(profile?.default_budget || {}) },
    remark_habits: listToText(profile?.remark_habits),
  };
}

function Profile() {
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [newTagInput, setNewTagInput] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    async function loadProfile() {
      try {
        const res = await fetch("/api/profile");
        if (!res.ok) throw new Error("画像加载失败");
        const data = await res.json();
        if (alive) setForm(profileToForm(data));
      } catch (err) {
        if (alive) setError(err.message || "画像加载失败，请确认后端服务已启动");
      } finally {
        if (alive) setLoading(false);
      }
    }
    loadProfile();
    return () => { alive = false; };
  }, []);

  const updateField = (field, value) => setForm((f) => ({ ...f, [field]: value }));
  const updateBudget = (mealType, range) =>
    setForm((f) => ({ ...f, default_budget: { ...f.default_budget, [mealType]: range } }));
  const toggleGoal = (goal) =>
    setForm((f) => ({
      ...f,
      health_goals: f.health_goals.includes(goal)
        ? f.health_goals.filter((g) => g !== goal)
        : [...f.health_goals, goal],
    }));

  const removeTag = (tag) =>
    setForm((f) => ({ ...f, taste_tags: f.taste_tags.filter((t) => t !== tag) }));

  const addTag = (tag) => {
    const trimmed = tag.trim();
    if (!trimmed || form.taste_tags.includes(trimmed)) return;
    setForm((f) => ({ ...f, taste_tags: [...f.taste_tags, trimmed] }));
    setNewTagInput("");
  };

  const handleTagKeyDown = (e) => {
    if (e.key === "Enter") { e.preventDefault(); addTag(newTagInput); }
  };

  const buildPayload = () => ({
    name: form.name,
    taste_description: form.taste_description,
    taste_tags: form.taste_tags,
    avoid_ingredients: textToList(form.avoid_ingredients),
    health_goals: form.health_goals,
    default_budget: form.default_budget,
    remark_habits: textToList(form.remark_habits),
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload()),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "保存失败");
      setForm(profileToForm(data));
      setMessage("偏好已保存，AI 已生成你的口味标签。");
    } catch (err) {
      setError(err.message || "保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "",
          taste_description: "",
          taste_tags: [],
          avoid_ingredients: [],
          health_goals: [],
          default_budget: emptyForm.default_budget,
          remark_habits: [],
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "清空失败");
      setForm(profileToForm(data));
      setNewTagInput("");
      setConfirmReset(false);
      setMessage("画像已清空。");
    } catch (err) {
      setError(err.message || "清空失败");
    } finally {
      setResetting(false);
    }
  };

  const disabled = loading || saving || resetting;

  return (
    <section className="space-y-6">
      <div className="page-panel">
        <p className="section-label">用户画像</p>
        <h2 className="page-title">偏好设置</h2>
        <p className="mt-2 text-slate-500">
          用自己的话写下口味偏好，保存后 AI 自动识别并记住，用于推荐和备注生成。
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="page-panel space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
              <span className="text-lg">👤</span>
              <h3 className="font-semibold text-slate-800">基础信息</h3>
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">姓名</span>
              <input
                value={form.name}
                disabled={disabled}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="例如：小明"
                className="input-base"
              />
            </label>

            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">口味偏好描述</span>
              <textarea
                value={form.taste_description}
                disabled={disabled}
                onChange={(e) => updateField("taste_description", e.target.value)}
                placeholder="例如：喜欢川菜但不能太辣，偏爱汤类和番茄口味。"
                rows={4}
                className="input-base resize-none"
              />
            </label>

            {/* 口味标签 — 可手动编辑 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-700">AI 识别的口味标签</p>
                <span className="text-xs text-slate-400">可手动增删</span>
              </div>
              <div className="flex flex-wrap gap-2 min-h-8">
                {form.taste_tags.length === 0 && (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-400">
                    保存后 AI 自动生成
                  </span>
                )}
                {form.taste_tags.map((tag) => (
                  <span
                    key={tag}
                    className="flex items-center gap-1 rounded-full bg-mealmate-mint px-3 py-1 text-xs font-medium text-mealmate-green"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      disabled={disabled}
                      className="ml-0.5 flex h-4 w-4 items-center justify-center rounded-full text-mealmate-green/60 hover:bg-mealmate-green/10 hover:text-mealmate-green disabled:cursor-not-allowed"
                      aria-label={`删除标签 ${tag}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={newTagInput}
                  disabled={disabled}
                  onChange={(e) => setNewTagInput(e.target.value)}
                  onKeyDown={handleTagKeyDown}
                  placeholder="输入标签后回车添加"
                  className="input-base flex-1 py-1.5 text-sm"
                />
                <button
                  type="button"
                  disabled={disabled || !newTagInput.trim()}
                  onClick={() => addTag(newTagInput)}
                  className="rounded-lg border border-mealmate-green px-3 py-1.5 text-sm font-medium text-mealmate-green hover:bg-mealmate-mint disabled:opacity-40 transition"
                >
                  添加
                </button>
              </div>
            </div>
          </div>

          <div className="page-panel space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
              <span className="text-lg">🚫</span>
              <h3 className="font-semibold text-slate-800">忌口与备注</h3>
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">忌口 / 过敏原</span>
              <input
                value={form.avoid_ingredients}
                disabled={disabled}
                onChange={(e) => updateField("avoid_ingredients", e.target.value)}
                placeholder="例如：香菜，葱，花生"
                className="input-base"
              />
              <span className="text-xs text-slate-400">支持中文逗号或英文逗号分隔</span>
            </label>

            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">备注习惯</span>
              <textarea
                value={form.remark_habits}
                disabled={disabled}
                onChange={(e) => updateField("remark_habits", e.target.value)}
                placeholder="例如：少油，不要香菜，米饭少一点"
                rows={4}
                className="input-base resize-none"
              />
            </label>
          </div>
        </div>

        <div className="page-panel space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <span className="text-lg">🎯</span>
            <h3 className="font-semibold text-slate-800">健康目标</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {healthGoalOptions.map((goal) => {
              const checked = form.health_goals.includes(goal);
              return (
                <button
                  key={goal}
                  type="button"
                  disabled={disabled}
                  onClick={() => toggleGoal(goal)}
                  className={`rounded-full border px-4 py-1.5 text-sm font-medium transition select-none ${
                    checked
                      ? "border-mealmate-green bg-mealmate-green text-white shadow-sm"
                      : "border-slate-200 bg-white text-slate-600 hover:border-mealmate-green hover:text-mealmate-green"
                  }`}
                >
                  {checked ? "✓ " : ""}{goal}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-slate-400">营养相关结果仅供参考，不作为医学建议。</p>
        </div>

        <div className="page-panel space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <span className="text-lg">💰</span>
            <h3 className="font-semibold text-slate-800">默认预算</h3>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {Object.entries(mealLabels).map(([mealType, label]) => (
              <BudgetSlider
                key={mealType}
                label={label}
                value={form.default_budget[mealType]}
                disabled={disabled}
                onChange={(range) => updateBudget(mealType, range)}
              />
            ))}
          </div>
        </div>

        {/* 底栏：状态 + 清空 + 保存 */}
        <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="min-h-6 text-sm">
            {message && <span className="font-medium text-emerald-600">✓ {message}</span>}
            {error && <span className="font-medium text-red-600">⚠ {error}</span>}
            {!message && !error && <span className="text-slate-400">保存后下次打开 App 仍然有效。</span>}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {confirmReset ? (
              <>
                <span className="text-sm text-slate-600">确认清空所有偏好？</span>
                <button
                  type="button"
                  disabled={resetting}
                  onClick={handleReset}
                  className="rounded-lg bg-red-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50 transition"
                >
                  {resetting ? "清空中..." : "确认清空"}
                </button>
                <button
                  type="button"
                  disabled={resetting}
                  onClick={() => setConfirmReset(false)}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 transition"
                >
                  取消
                </button>
              </>
            ) : (
              <button
                type="button"
                disabled={disabled}
                onClick={() => setConfirmReset(true)}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-500 hover:border-red-300 hover:text-red-500 transition"
              >
                清空画像
              </button>
            )}
            <button type="submit" disabled={disabled} className="btn-primary">
              {saving ? "保存中..." : "保存画像"}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}

export default Profile;
