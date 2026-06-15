import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, Cell,
  PieChart, Pie,
} from "recharts";

const mealTypeLabels = { breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" };
const dayOptions = [3, 7, 14, 30];
const PAGE_SIZE = 5;

/* ─── 中国居民膳食指南 2022 参考值（每餐） ─── */
const MACRO_REFS = {
  "碳水化合物": { range: "≈100 g/餐", color: "#7c3aed" },
  "蛋白质":     { range: "≈20 g/餐",  color: "#2563eb" },
  "脂肪":       { range: "≈18 g/餐",  color: "#d97706" },
  "膳食纤维":   { range: "≥8 g/餐",   color: "#16a34a" },
  "钠":         { range: "≤800 mg/餐", color: "#64748b" },
};
const MEAL_SODIUM_REF = 800; // 2400 mg/day ÷ 3 餐 ≈ 800 mg/餐

/* ══════════════════════════════════════ */
function MealHistory() {
  const [days, setDays] = useState(7);
  const [meals, setMeals] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);

  async function loadData(selectedDays = days) {
    setLoading(true);
    setError("");
    setPage(1);
    try {
      const [mealsRes, statsRes] = await Promise.all([
        fetch(`/api/meals?days=${selectedDays}`),
        fetch(`/api/meals/stats?days=${selectedDays}`),
      ]);
      const mealsData = await mealsRes.json();
      const statsData = await statsRes.json();
      if (!mealsRes.ok) throw new Error(mealsData.error || "饮食历史加载失败");
      if (!statsRes.ok) throw new Error(statsData.error || "统计数据加载失败");
      setMeals(mealsData.meals || []);
      setStats(statsData);
    } catch (err) {
      setError(err.message || "加载失败，请确认后端服务已启动");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(days); }, [days]);

  function handleDeleteMeal(meal_id) {
    setMeals((prev) => {
      const next = prev.filter((m) => m.meal_id !== meal_id);
      // If deleting the last item on a non-first page, step back
      const totalPages = Math.max(1, Math.ceil(next.length / PAGE_SIZE));
      setPage((p) => Math.min(p, totalPages));
      return next;
    });
    fetch(`/api/meals/stats?days=${days}`)
      .then((r) => r.json())
      .then((data) => setStats(data))
      .catch(() => {});
  }

  function handleUpdateMeal(updatedMeal) {
    setMeals((prev) => prev.map((m) => m.meal_id === updatedMeal.meal_id ? updatedMeal : m));
  }

  const totalPages = Math.max(1, Math.ceil(meals.length / PAGE_SIZE));
  const pagedMeals = meals.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const avgNutrition = stats?.stats?.average_nutrition || {};

  return (
    <section className="space-y-6">
      <div className="page-panel">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="section-label">饮食历史</p>
            <h2 className="page-title">最近吃了什么</h2>
            <p className="mt-2 text-slate-500">
              按时间倒序查看用餐记录、营养信息和消费统计。
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {dayOptions.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => setDays(opt)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  days === opt ? "bg-mealmate-green text-white shadow-sm" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                近 {opt} 天
              </button>
            ))}
            <button type="button" onClick={() => loadData(days)} className="btn-orange px-3 py-1.5">
              刷新
            </button>
          </div>
        </div>
      </div>

      {error && <div className="status-error">{error}</div>}

      {/* 统计数字卡 */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label={`近 ${stats?.days || days} 天用餐`} value={stats?.meal_count ?? "—"} unit="餐" color="green" loading={loading && !stats} />
        <StatCard label="总消费" value={stats?.stats?.total_spending ?? "—"} unit="元" prefix="¥" color="orange" loading={loading && !stats} />
        <StatCard label="平均每餐" value={stats?.stats?.average_spending ?? "—"} unit="元" prefix="¥" color="slate" loading={loading && !stats} />
        <StatCard label="平均热量" value={avgNutrition.calories_kcal ?? "—"} unit="kcal" color="violet" loading={loading && !stats} />
      </div>

      {/* 可视化图表 */}
      <DietCharts meals={meals} stats={stats} days={days} loading={loading} />

      {/* 饮食分析 */}
      <div className="page-panel">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800"><span>📊</span> 近期饮食分析</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <TagLine label="发现问题" items={stats?.recent_pattern?.flags?.length ? stats.recent_pattern.flags : ["暂无明显问题"]} tone="orange" />
          <TagLine label="建议下一餐" items={stats?.prefer_next?.length ? stats.prefer_next : ["均衡饮食"]} tone="green" />
          <TagLine label="建议少选" items={stats?.avoid_next?.length ? stats.avoid_next : ["暂无"]} tone="slate" />
        </div>
        <p className="mt-3 text-xs text-slate-400">营养估算仅供参考，不构成医学建议。</p>
      </div>

      {/* 历史列表 */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">饮食记录</h3>
          {!loading && meals.length > 0 && (
            <span className="text-xs text-slate-400">近 {days} 天 · 共 {meals.length} 条</span>
          )}
        </div>
        {loading ? (
          <div className="page-panel flex items-center gap-3 text-sm text-slate-500">
            <span className="animate-spin">⏳</span> 正在加载饮食历史...
          </div>
        ) : meals.length === 0 ? (
          <div className="page-panel text-center text-sm text-slate-400">
            <p className="text-4xl">🍽️</p>
            <p className="mt-3">近 {days} 天暂无饮食记录</p>
            <p className="mt-1">完成一次"记录一餐"后刷新本页即可查看</p>
          </div>
        ) : (
          <>
            {pagedMeals.map((meal) => (
              <MealCard
                key={meal.meal_id}
                meal={meal}
                onDelete={handleDeleteMeal}
                onUpdate={handleUpdateMeal}
              />
            ))}
            {totalPages > 1 && (
              <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 transition"
                >
                  ← 上一页
                </button>
                <div className="flex items-center gap-1.5">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPage(p)}
                      className={`h-8 w-8 rounded-lg text-sm font-medium transition ${
                        p === page
                          ? "bg-mealmate-green text-white shadow-sm"
                          : "text-slate-500 hover:bg-slate-100"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 transition"
                >
                  下一页 →
                </button>
              </div>
            )}
            <p className="text-center text-xs text-slate-400">
              共 {meals.length} 条记录，每页 {PAGE_SIZE} 条，第 {page} / {totalPages} 页
            </p>
          </>
        )}
      </div>
    </section>
  );
}

/* ─── 图表容器 ─── */
function DietCharts({ meals, stats, days, loading }) {
  const mealTypeData = useMemo(() => {
    const colors = { 早餐: "#f59e0b", 午餐: "#2f7d57", 晚餐: "#8b5cf6", 加餐: "#64748b" };
    const counts = {};
    meals.forEach((m) => {
      const label = mealTypeLabels[m.meal_type];
      if (label) counts[label] = (counts[label] || 0) + 1;
    });
    return Object.entries(counts).filter(([, v]) => v > 0).map(([name, value]) => ({ name, value, color: colors[name] }));
  }, [meals]);

  if (loading) {
    return (
      <div className="page-panel flex items-center justify-center py-10 text-sm text-slate-400">
        <span className="animate-spin mr-2">⏳</span> 加载图表数据中...
      </div>
    );
  }
  if (!meals.length) {
    return (
      <div className="page-panel py-6 text-center text-sm text-slate-400">
        暂无数据，记录一餐后图表将自动更新。
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 营养圈图 + 餐型分布 */}
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <NutritionDonut meals={meals} stats={stats} />
        <MealTypeChart data={mealTypeData} />
      </div>
    </div>
  );
}

/* ─── 营养圈图：LLM 分析结果可视化 ─── */
function NutritionDonut({ meals, stats }) {
  const avgNutrition = stats?.stats?.average_nutrition || {};
  const avgCal    = Math.round(avgNutrition.calories_kcal || 0);
  const protein_g = avgNutrition.protein_g || 0;
  const fat_g     = avgNutrition.fat_g     || 0;
  const carbs_g   = avgNutrition.carbs_g   || 0;
  const fiber_g   = avgNutrition.fiber_g   || 0;
  const sodium_mg = avgNutrition.sodium_mg || 0;

  /* 克重模型：各营养素克重占比（钠 mg÷1000→g 参与比例计算） */
  const macroData = useMemo(() => {
    const sodium_g = sodium_mg / 1000;
    const total = carbs_g + protein_g + fat_g + fiber_g + sodium_g || 1;
    return [
      { name: "碳水化合物", value: carbs_g,   grams: carbs_g,   color: "#7c3aed", pct: Math.round(carbs_g   / total * 100) },
      { name: "蛋白质",     value: protein_g, grams: protein_g, color: "#2563eb", pct: Math.round(protein_g / total * 100) },
      { name: "脂肪",       value: fat_g,     grams: fat_g,     color: "#d97706", pct: Math.round(fat_g     / total * 100) },
      { name: "膳食纤维",   value: fiber_g,   grams: fiber_g,   color: "#16a34a", pct: Math.round(fiber_g   / total * 100) },
      { name: "钠",         value: sodium_g,  grams: sodium_g,  color: "#64748b", pct: Math.round(sodium_g  / total * 100), sodium_mg },
    ].filter(d => d.value > 0);
  }, [carbs_g, protein_g, fat_g, fiber_g, sodium_mg]);

  /* 汇聚所有食物的 LLM levels 字段 */
  const allFoods = useMemo(() => meals.flatMap(m => m.recognized_foods || []), [meals]);

  function dominantLevel(levelKey) {
    const vals = allFoods.map(f => f.levels?.[levelKey]).filter(Boolean);
    if (!vals.length) return null;
    const counts = { low: 0, medium: 0, high: 0 };
    vals.forEach(v => { if (v in counts) counts[v]++; });
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
  }

  const calLevel     = dominantLevel("calorie_level");
  const carbsLevel   = dominantLevel("carbs_level");
  const vegLevel     = dominantLevel("vegetable_level");
  const sodiumLevel  = dominantLevel("sodium_level");
  const fatLevel     = dominantLevel("fat_level");
  const proteinLevel = dominantLevel("protein_level");

  const sodiumPct = Math.min(Math.round((sodium_mg / MEAL_SODIUM_REF) * 100), 150);

  return (
    <div className="page-panel">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-4 mb-5">
        <span className="text-xl">🔬</span>
        <h3 className="font-semibold text-slate-800">平均营养结构（每餐）</h3>
        <span className="ml-auto text-xs text-slate-400 hidden sm:block">中国居民膳食指南 2022</span>
      </div>

      <div className="grid gap-5 sm:grid-cols-[auto_1fr]">
        {/* 圈图 */}
        <div className="flex flex-col items-center gap-4">
          <div className="relative" style={{ width: 200, height: 200 }}>
            <PieChart width={200} height={200}>
              <Pie
                data={macroData}
                cx={100} cy={100}
                innerRadius={60} outerRadius={88}
                paddingAngle={3}
                dataKey="value"
                startAngle={90} endAngle={-270}
              >
                {macroData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.color} opacity={0.88} />
                ))}
              </Pie>
              <Tooltip content={<MacroTooltip />} />
            </PieChart>
            {/* 圈心文字 */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold text-slate-800 leading-tight">{avgCal}</span>
              <span className="text-xs text-slate-400">kcal / 餐</span>
            </div>
          </div>

          {/* 图例 */}
          <div className="w-full space-y-2 min-w-[170px]">
            {macroData.map(m => (
              <div key={m.name} className="flex items-center justify-between gap-2 text-sm">
                <span className="flex items-center gap-2 flex-shrink-0">
                  <span className="h-3 w-3 rounded-full" style={{ background: m.color }} />
                  <span className="text-slate-700">{m.name}</span>
                </span>
                <div className="flex items-center gap-2 text-xs text-right">
                  <span className="text-slate-500">
                    {m.name === "钠" ? `${Math.round(m.sodium_mg)} mg` : `${m.grams.toFixed(1)} g`}
                  </span>
                  <span className="font-semibold w-8 text-right" style={{ color: m.color }}>{m.pct}%</span>
                  <span className="text-slate-300 hidden sm:inline">/{MACRO_REFS[m.name]?.range}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* LLM 分析质量指标 */}
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">AI 分析 · 各营养素水平</p>
          <div className="grid grid-cols-2 gap-2.5">
            <LevelCard label="热量"   icon="🔥" level={calLevel}     good="low"  bad="high" goodText="偏低" midText="适中" badText="偏高"
              detail={avgCal > 0 ? `均 ${avgCal} kcal/餐` : null} />
            <LevelCard label="碳水"   icon="🌾" level={carbsLevel}   good="medium" bad={null} goodText="适中" midText="一般" badText="—"
              detail={carbs_g > 0 ? `均 ${carbs_g.toFixed(1)} g / ≈100 g/餐` : null} />
            <LevelCard label="蛋白质" icon="🥩" level={proteinLevel} good="high" bad="low"  goodText="充足" midText="适中" badText="偏少"
              detail={protein_g > 0 ? `均 ${protein_g.toFixed(1)} g / ≈20 g/餐` : null} />
            <LevelCard label="脂肪"   icon="🫙" level={fatLevel}     good="low"  bad="high" goodText="偏少" midText="适中" badText="偏高"
              detail={fat_g > 0 ? `均 ${fat_g.toFixed(1)} g / ≈18 g/餐` : null} />
            <LevelCard label="蔬菜 & 纤维" icon="🥦" level={vegLevel} good="high" bad="low" goodText="蔬菜充足" midText="蔬菜一般" badText="蔬菜偏少"
              detail={fiber_g > 0 ? `膳食纤维 ${fiber_g.toFixed(1)} g / 建议 ≥8 g/餐` : "膳食纤维暂无数据"} />
            <LevelCard label="钠 / 盐" icon="🧂" level={sodiumLevel} good="low"  bad="high" goodText="适量" midText="适中" badText="偏高"
              detail={sodium_mg > 0 ? `均 ${Math.round(sodium_mg)} mg/餐` : null} />
          </div>

          {/* 钠摄入进度条 */}
          {sodium_mg > 0 && (
            <div className="mt-1">
              <div className="flex items-center justify-between mb-1 text-xs text-slate-500">
                <span>单餐钠摄入 vs 建议上限（800 mg）</span>
                <span className={`font-semibold ${sodium_mg > MEAL_SODIUM_REF ? "text-red-500" : sodium_mg > MEAL_SODIUM_REF * 0.7 ? "text-amber-500" : "text-emerald-600"}`}>
                  {Math.round(sodium_mg)} mg
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-2 rounded-full transition-all duration-700 ${
                    sodium_mg > MEAL_SODIUM_REF ? "bg-red-400" :
                    sodium_mg > MEAL_SODIUM_REF * 0.7 ? "bg-amber-400" : "bg-emerald-400"
                  }`}
                  style={{ width: `${Math.min(sodiumPct, 100)}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-slate-400">参考：中国居民膳食指南 2022，每日钠 ≤2400 mg，每餐 ≤800 mg</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── 餐型分布 ─── */
function MealTypeChart({ data }) {
  return (
    <div className="page-panel">
      <h3 className="flex items-center gap-2 font-semibold text-slate-800 mb-4"><span>🕐</span> 餐型分布</h3>
      {data.length === 0 ? (
        <p className="text-sm text-slate-400">暂无数据</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data} layout="vertical" margin={{ top: 0, right: 32, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 13, fill: "#475569" }} axisLine={false} tickLine={false} width={36} />
              <Tooltip
                formatter={(val) => [`${val} 餐`, ""]}
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }}
                cursor={{ fill: "#f8fafc" }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={28}>
                {data.map((entry, idx) => <Cell key={idx} fill={entry.color} opacity={0.85} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-3 flex flex-wrap gap-3">
            {data.map((d) => (
              <span key={d.name} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: d.color }} />
                {d.name} {d.value} 餐
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* ─── 营养素水平卡片（LLM 定性分析） ─── */
function LevelCard({ label, icon, level, good, bad, goodText, midText, badText, detail }) {
  const isGood = level && level === good;
  const isBad  = level && bad && level === bad;
  const text   = isGood ? goodText : isBad ? badText : level ? midText : "—";

  const style = isGood
    ? "bg-emerald-50 border-emerald-200 text-emerald-700"
    : isBad
    ? "bg-red-50 border-red-200 text-red-600"
    : "bg-slate-50 border-slate-200 text-slate-600";

  return (
    <div className={`rounded-xl border p-3 ${style}`}>
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-base leading-none">{icon}</span>
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className="text-sm font-bold">{text}</p>
      {detail && <p className="mt-0.5 text-xs opacity-60 leading-snug">{detail}</p>}
    </div>
  );
}

/* ─── Tooltips ─── */
function MacroTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  const isSodium = d?.name === "钠";
  const display = isSodium
    ? `${Math.round(d.sodium_mg)} mg`
    : `${d?.grams?.toFixed(1)} g`;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
      <p className="font-semibold text-sm" style={{ color: d?.color }}>{d?.name}</p>
      <p className="text-sm text-slate-600">{display} · 占比 {d?.pct}%</p>
      <p className="text-xs text-slate-400 mt-1">参考：{MACRO_REFS[d?.name]?.range}</p>
    </div>
  );
}

/* ─── 通用子组件 ─── */
function StatCard({ label, value, unit, prefix = "", color, loading }) {
  const colorMap = { green: "text-mealmate-green", orange: "text-mealmate-orange", slate: "text-slate-700", violet: "text-violet-600" };
  return (
    <div className="page-panel p-5">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${colorMap[color] || "text-slate-700"}`}>
        {loading ? <span className="text-slate-300">—</span> : <>{prefix}{value}</>}
        {!loading && <span className="ml-1 text-sm font-normal text-slate-400">{unit}</span>}
      </p>
    </div>
  );
}

function TagLine({ label, items, tone }) {
  const cls =
    tone === "green"  ? "bg-mealmate-mint text-mealmate-green" :
    tone === "orange" ? "bg-orange-50 text-mealmate-orange" :
    "bg-slate-100 text-slate-600";
  return (
    <div>
      <p className="mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <span key={item} className={`rounded-full px-2.5 py-1 text-xs font-medium ${cls}`}>{item}</span>
        ))}
      </div>
    </div>
  );
}

function MealCard({ meal, onDelete, onUpdate }) {
  const [mode, setMode] = useState("view"); // "view" | "edit" | "confirm-delete"
  const [editForm, setEditForm] = useState({
    meal_type: meal.meal_type,
    occurred_at: meal.occurred_at ? meal.occurred_at.slice(0, 16) : "",
    total_price: meal.total_price ?? 0,
    food_names: (meal.recognized_foods || []).map(
      (f) => f.standard_name || f.dish_name || f.raw_text || ""
    ),
  });
  const [busy, setBusy] = useState(false);
  const [cardErr, setCardErr] = useState("");

  const foods = meal.recognized_foods || [];
  const tags = unique(foods.flatMap((f) => f.nutrition_tags || []));

  async function handleDelete() {
    setBusy(true);
    setCardErr("");
    try {
      const res = await fetch(`/api/meals/${meal.meal_id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("删除失败");
      onDelete(meal.meal_id);
    } catch (e) {
      setCardErr(e.message || "删除失败");
      setBusy(false);
      setMode("view");
    }
  }

  async function handleUpdate() {
    setBusy(true);
    setCardErr("");
    try {
      const updatedFoods = foods.map((f, i) => ({
        ...f,
        standard_name: editForm.food_names[i] ?? f.standard_name,
      }));
      const body = {
        meal_type: editForm.meal_type,
        total_price: parseFloat(editForm.total_price) || 0,
        recognized_foods: updatedFoods,
      };
      if (editForm.occurred_at) body.occurred_at = editForm.occurred_at + ":00+08:00";
      const res = await fetch(`/api/meals/${meal.meal_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "保存失败");
      onUpdate(data);
      setMode("view");
    } catch (e) {
      setCardErr(e.message || "保存失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="page-panel transition-colors">
      {/* 头部：图标 + 时间/名称 + 价格 */}
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="flex gap-4">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-mealmate-mint text-xl">
            {meal.input_type === "photo" ? "📷" : "✍️"}
          </div>
          <div>
            <p className="text-xs text-slate-400">
              {formatDateTime(meal.occurred_at)} · {mealTypeLabels[meal.meal_type] || meal.meal_type}
            </p>
            <h3 className="mt-0.5 font-semibold text-slate-800">
              {foods.map((f) => f.standard_name || f.dish_name || f.raw_text).join("、") || "未识别菜品"}
            </h3>
            <p className="mt-0.5 text-xs text-slate-400">{meal.input_type === "photo" ? "照片上传" : "文字描述"}</p>
          </div>
        </div>
        <span className="flex-shrink-0 self-start rounded-full bg-orange-50 border border-orange-100 px-3 py-1 text-sm font-semibold text-mealmate-orange">
          ¥{meal.total_price || 0}
        </span>
      </div>

      {/* 营养标签 */}
      {tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span key={tag} className="rounded-full bg-mealmate-mint px-2.5 py-0.5 text-xs font-medium text-mealmate-green">{tag}</span>
          ))}
        </div>
      )}

      {/* 营养估算 */}
      <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">营养估算</p>
        <div className="mt-2 grid grid-cols-5 gap-1 text-center text-xs">
          {[
            { label: "热量",   value: meal.total_nutrition?.calories_kcal || 0, unit: "kcal" },
            { label: "蛋白质", value: meal.total_nutrition?.protein_g     || 0, unit: "g" },
            { label: "脂肪",   value: meal.total_nutrition?.fat_g         || 0, unit: "g" },
            { label: "碳水",   value: meal.total_nutrition?.carbs_g       || 0, unit: "g" },
            { label: "钠",     value: meal.total_nutrition?.sodium_mg     || 0, unit: "mg" },
          ].map(({ label, value, unit }) => (
            <div key={label} className="flex flex-col">
              <span className="text-slate-400">{label}</span>
              <span className="font-semibold text-slate-700">{value}</span>
              <span className="text-slate-400">{unit}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 操作栏 */}
      {mode === "view" && (
        <div className="mt-3 flex items-center justify-end gap-1 border-t border-slate-100 pt-3">
          {cardErr && <span className="flex-1 text-xs text-red-500">{cardErr}</span>}
          <button
            type="button"
            onClick={() => { setCardErr(""); setMode("edit"); }}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-mealmate-green transition"
          >
            ✏️ 修改
          </button>
          <button
            type="button"
            onClick={() => { setCardErr(""); setMode("confirm-delete"); }}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:bg-red-50 hover:text-red-500 transition"
          >
            🗑 删除
          </button>
        </div>
      )}

      {/* 删除确认 */}
      {mode === "confirm-delete" && (
        <div className="mt-3 flex items-center gap-3 border-t border-slate-100 pt-3">
          <p className="flex-1 text-sm text-slate-600">确认删除这条记录？删除后无法恢复。</p>
          <button
            type="button"
            onClick={handleDelete}
            disabled={busy}
            className="rounded-lg bg-red-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-600 disabled:opacity-50 transition"
          >
            {busy ? "删除中..." : "确认删除"}
          </button>
          <button
            type="button"
            onClick={() => setMode("view")}
            disabled={busy}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition"
          >
            取消
          </button>
        </div>
      )}

      {/* 编辑面板 */}
      {mode === "edit" && (
        <div className="mt-3 space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">修改记录</p>

          <div className="space-y-1.5">
            <p className="text-xs font-medium text-slate-600">餐次</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(mealTypeLabels).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setEditForm((f) => ({ ...f, meal_type: key }))}
                  className={`rounded-lg border px-3 py-1 text-xs font-medium transition ${
                    editForm.meal_type === key
                      ? "border-mealmate-green bg-mealmate-green text-white"
                      : "border-slate-200 bg-white text-slate-600 hover:border-mealmate-green hover:text-mealmate-green"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <p className="text-xs font-medium text-slate-600">用餐时间</p>
            <input
              type="datetime-local"
              value={editForm.occurred_at}
              onChange={(e) => setEditForm((f) => ({ ...f, occurred_at: e.target.value }))}
              className="input-base py-1.5 text-sm"
            />
          </div>

          <div className="space-y-1.5">
            <p className="text-xs font-medium text-slate-600">实付价格（元）</p>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">¥</span>
              <input
                type="number"
                min="0"
                step="0.5"
                value={editForm.total_price}
                onChange={(e) => setEditForm((f) => ({ ...f, total_price: e.target.value }))}
                className="input-base py-1.5 text-sm w-32"
              />
            </div>
          </div>

          {editForm.food_names.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs font-medium text-slate-600">餐品名称</p>
              <div className="space-y-2">
                {editForm.food_names.map((name, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 w-4 flex-shrink-0">{i + 1}</span>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => {
                        const names = [...editForm.food_names];
                        names[i] = e.target.value;
                        setEditForm((f) => ({ ...f, food_names: names }));
                      }}
                      className="input-base flex-1 py-1.5 text-sm"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {cardErr && <p className="text-xs text-red-500">{cardErr}</p>}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => { setMode("view"); setCardErr(""); }}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleUpdate}
              disabled={busy}
              className="btn-primary py-1.5 px-4 text-xs disabled:opacity-50"
            >
              {busy ? "保存中..." : "保存修改"}
            </button>
          </div>
        </div>
      )}
    </article>
  );
}

/* ─── 工具函数 ─── */
function formatDateTime(value) {
  if (!value) return "时间未知";
  try {
    return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
  } catch { return value; }
}


function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

export default MealHistory;
