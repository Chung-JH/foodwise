import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import BudgetSlider from "../components/BudgetSlider.jsx";

function useToast() {
  const [toast, setToast] = useState(null);
  const timerRef = useRef(null);
  const show = useCallback((msg, type = "success") => {
    clearTimeout(timerRef.current);
    setToast({ msg, type });
    timerRef.current = setTimeout(() => setToast(null), 3000);
  }, []);
  return { toast, show };
}

const MEAL_TYPES = [
  { value: "breakfast", label: "早餐" },
  { value: "lunch",     label: "午餐" },
  { value: "dinner",    label: "晚餐" },
  { value: "snack",     label: "加餐" },
];

const COURSE_CONFIG = {
  主食: { icon: "🍱", color: "text-mealmate-green", activeBg: "bg-mealmate-green", border: "border-mealmate-green/25", rowBg: "bg-mealmate-mint/30" },
  饮品: { icon: "🥤", color: "text-sky-600",         activeBg: "bg-sky-600",         border: "border-sky-200",          rowBg: "bg-sky-50/60" },
  点心: { icon: "🍰", color: "text-amber-600",       activeBg: "bg-amber-500",       border: "border-amber-200",        rowBg: "bg-amber-50/60" },
};

const COURSE_ORDER = ["主食", "饮品", "点心"];

const NUTRITION_KEYS = [
  { key: "calories_kcal", label: "热量",  unit: "kcal", color: "text-rose-500" },
  { key: "protein_g",     label: "蛋白质", unit: "g",    color: "text-sky-500" },
  { key: "fat_g",         label: "脂肪",  unit: "g",    color: "text-amber-500" },
  { key: "carbs_g",       label: "碳水",  unit: "g",    color: "text-violet-500" },
  { key: "sodium_mg",     label: "钠",    unit: "mg",   color: "text-slate-500" },
];

function guessCurrentMealType() {
  const h = new Date().getHours();
  if (h >= 5  && h < 10) return "breakfast";
  if (h >= 10 && h < 15) return "lunch";
  if (h >= 15 && h < 21) return "dinner";
  return "snack";
}

export default function Recommend() {
  const [profile,         setProfile]        = useState(null);
  const [contacts,        setContacts]       = useState([]);
  const [target,          setTarget]         = useState("self");
  const [budgetRange,     setBudgetRange]    = useState([15, 25]);
  const [mealType,        setMealType]       = useState(guessCurrentMealType);
  const [extraConstraint, setExtraConstraint]= useState("");
  const [initialMeals,    setInitialMeals]   = useState([]);
  const [mealsByType,     setMealsByType]    = useState([]);
  const [initialStats,    setInitialStats]   = useState(null);
  const [result,          setResult]         = useState(null);
  const [checkedIds,      setCheckedIds]     = useState(new Set());
  const [excludeIds,      setExcludeIds]     = useState([]);
  const [remarks,         setRemarks]        = useState([]);      // [{dish_id,name,course_type,remark}]
  const [editedRemarks,   setEditedRemarks]  = useState({});      // dish_id → text
  const [loading,         setLoading]        = useState(false);
  const [confirming,      setConfirming]     = useState(false);
  const [message,         setMessage]        = useState("");
  const [error,           setError]          = useState("");
  const { toast, show: showToast } = useToast();

  useEffect(() => {
    async function load() {
      try {
        const [pR, cR, mR, sR] = await Promise.all([
          fetch("/api/profile"), fetch("/api/contacts"),
          fetch("/api/meals?days=7"), fetch("/api/meals/stats?days=7"),
        ]);
        const [pD, cD, mD, sD] = await Promise.all([pR.json(), cR.json(), mR.json(), sR.json()]);
        if (pR.ok) { setProfile(pD); setBudgetRange(pD.default_budget?.lunch || [15, 25]); }
        if (cR.ok) setContacts(cD.contacts || []);
        if (mR.ok) setInitialMeals((mD.meals || []).slice(0, 3));
        if (sR.ok) setInitialStats(sD);
      } catch { setError("初始化推荐页面失败，请确认后端服务已启动"); }
    }
    load();
  }, []);

  // Fetch recent meals for the selected meal type whenever it changes
  useEffect(() => {
    fetch(`/api/meals?days=30&meal_type=${mealType}`)
      .then((r) => r.json())
      .then((d) => setMealsByType((d.meals || []).slice(0, 3)))
      .catch(() => {});
  }, [mealType]);

  const selectedContact = useMemo(() => {
    if (!target.startsWith("contact:")) return null;
    return contacts.find((c) => c.contact_id === target.replace("contact:", "")) || null;
  }, [contacts, target]);

  useEffect(() => {
    if (target === "self" && profile?.default_budget?.lunch) setBudgetRange(profile.default_budget.lunch);
    if (selectedContact?.default_budget?.lunch) setBudgetRange(selectedContact.default_budget.lunch);
  }, [target, profile, selectedContact]);

  const mealTypeLabel  = MEAL_TYPES.find((m) => m.value === mealType)?.label || "";
  // Use same-type meals from result if available, otherwise use the pre-fetched type-filtered list
  const recentMeals    = result?.recent_meals_same_type?.length > 0
    ? result.recent_meals_same_type
    : mealsByType;
  const recentAnalysis = result?.recent_analysis || initialStats;
  const recommendations = result?.recommendations || [];

  const checkedItems = recommendations.filter((r) => checkedIds.has(r.dish_id));
  const selectedTotal = checkedItems.reduce((s, r) => s + (r.price || 0), 0);
  const totalNutrition = checkedItems.reduce((acc, r) => {
    const n = r.estimated_nutrition || {};
    for (const { key } of NUTRITION_KEYS) acc[key] = (acc[key] || 0) + (n[key] || 0);
    return acc;
  }, {});

  const visibleRemarks = remarks.filter((r) => checkedIds.has(r.dish_id));

  const handleGenerate = async () => {
    setLoading(true); setError(""); setMessage("");
    const isContact = target.startsWith("contact:");
    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget_range: budgetRange, meal_type: mealType,
          user_type:    isContact ? "contact" : "self",
          contact_id:   isContact ? target.replace("contact:", "") : null,
          extra_constraint: extraConstraint.trim() || null,
          exclude_dish_ids: excludeIds,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "生成推荐失败");
      setResult(data);

      // Default: check only top-1 per category
      const topPerType = {};
      for (const r of (data.recommendations || [])) {
        const ct = r.course_type || "主食";
        if (!topPerType[ct]) topPerType[ct] = r.dish_id;
      }
      setCheckedIds(new Set(Object.values(topPerType)));
      setExcludeIds((data.recommendations || []).map((r) => r.dish_id));

      const apiRemarks = data.remarks || [];
      setRemarks(apiRemarks);
      const init = {};
      for (const r of apiRemarks) init[r.dish_id] = r.remark;
      setEditedRemarks(init);

      setMessage(data.mode === "rule_fallback" ? "推荐已生成（备用模式）。" : "推荐已生成。");
    } catch (err) {
      setError(err.message || "生成推荐失败，请稍后重试");
    } finally { setLoading(false); }
  };

  const handleConfirm = async () => {
    if (checkedItems.length === 0) { setError("请至少勾选一个菜品"); return; }
    setConfirming(true); setError(""); setMessage("");
    const isContact = target.startsWith("contact:");
    const combinedRemark = visibleRemarks
      .map((r) => editedRemarks[r.dish_id] || r.remark)
      .filter(Boolean).join(" | ");
    try {
      const res = await fetch("/api/recommend/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recommendations: checkedItems, remark: combinedRemark,
          meal_type:    mealType,
          budget_range: budgetRange,
          user_type:    isContact ? "contact" : "self",
          contact_id:   isContact ? target.replace("contact:", "") : null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "确认选择失败");
      showToast(`已记录：${checkedItems.map((r) => r.name).join("、")}`);
    } catch (err) {
      setError(err.message || "确认选择失败，请稍后重试");
    } finally { setConfirming(false); }
  };

  return (
    <section className="space-y-6">
      <div className="page-panel">
        <p className="section-label">推荐下一餐</p>
        <h2 className="page-title">AI 智能推荐</h2>
        <p className="mt-2 text-slate-500">
          根据你的口味、近期饮食和预算，AI 推荐适合的主食、饮品和点心，勾选组合后查看营养总量和下单备注。
        </p>
      </div>

      {message && <div className="status-success">✓ {message}</div>}
      {error   && <div className="status-error">⚠ {error}</div>}

      <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
        {/* 左：条件面板 */}
        <div className="space-y-4">
          <div className="page-panel space-y-4">
            <h3 className="flex items-center gap-2 font-semibold text-slate-800"><span>⚙️</span> 本次条件</h3>

            <div className="space-y-1.5">
              <span className="text-sm font-medium text-slate-700">餐型</span>
              <div className="grid grid-cols-4 gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1">
                {MEAL_TYPES.map(({ value, label }) => (
                  <button key={value} type="button" onClick={() => { setMealType(value); setResult(null); setRemarks([]); setCheckedIds(new Set()); setExcludeIds([]); }}
                    className={`rounded-md py-1.5 text-sm font-medium transition-all ${
                      mealType === value
                        ? "bg-white shadow-sm text-mealmate-green ring-1 ring-mealmate-green/30"
                        : "text-slate-500 hover:text-slate-700"
                    }`}>
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">为谁点</span>
              <select value={target}
                onChange={(e) => { setTarget(e.target.value); setResult(null); setRemarks([]); setCheckedIds(new Set()); setExcludeIds([]); }}
                className="input-base">
                <option value="self">自己</option>
                {contacts.map((c) => (
                  <option key={c.contact_id} value={`contact:${c.contact_id}`}>{c.name}</option>
                ))}
              </select>
            </label>

            <BudgetSlider label="主食价格区间" value={budgetRange} onChange={setBudgetRange} />

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">
                额外描述 <span className="text-slate-400 font-normal">（可选）</span>
              </label>
              <input type="text" value={extraConstraint}
                onChange={(e) => setExtraConstraint(e.target.value)}
                placeholder="如：想搭配热饮、今天想吃辣的…"
                className="input-base text-sm" maxLength={80} />
            </div>

            <button type="button" onClick={handleGenerate} disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? <><span className="animate-spin">⏳</span> 生成中...</> : "🍽️ 生成推荐"}
            </button>
          </div>

          <AnalysisPanel analysis={recentAnalysis} />
        </div>

        {/* 右：历史 + 推荐 */}
        <div className="space-y-4">
          <RecentMeals meals={recentMeals} mealTypeLabel={mealTypeLabel} />
          <GroupedRecommendations
            recommendations={recommendations}
            checkedIds={checkedIds}
            onToggle={(id) => setCheckedIds((prev) => {
              const next = new Set(prev);
              next.has(id) ? next.delete(id) : next.add(id);
              return next;
            })}
            onRefresh={handleGenerate}
            loading={loading}
          />
        </div>
      </div>

      {result && (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* 组合说明 */}
          <div className="page-panel space-y-4">
            <h3 className="flex items-center gap-2 font-semibold text-slate-800"><span>📝</span> 组合说明</h3>

            {checkedItems.length === 0 ? (
              <p className="text-sm text-slate-400">请在上方勾选想要的菜品</p>
            ) : (
              <>
                {/* 已选菜品 + 评估总价 */}
                <div className="rounded-lg bg-mealmate-mint/40 px-4 py-3 flex items-start justify-between gap-3">
                  <div className="space-y-1 text-sm text-slate-600 min-w-0">
                    {checkedItems.map((r) => (
                      <div key={r.dish_id} className="flex items-center gap-2">
                        <span>{COURSE_CONFIG[r.course_type]?.icon || "•"}</span>
                        <span className="truncate">{r.name}</span>
                        <span className="text-slate-400 flex-shrink-0">¥{r.price}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <p className="text-xl font-bold text-mealmate-orange">¥{selectedTotal.toFixed(1)}</p>
                    <p className="text-xs text-slate-400 mt-0.5">评估价格</p>
                  </div>
                </div>

                {/* 营养汇总 */}
                <div>
                  <p className="text-xs font-medium text-slate-500 mb-2">营养估算（勾选合计）</p>
                  <div className="grid grid-cols-5 gap-2">
                    {NUTRITION_KEYS.map(({ key, label, unit, color }) => (
                      <div key={key} className="rounded-lg bg-slate-50 border border-slate-100 p-2 text-center">
                        <p className={`text-sm font-bold ${color}`}>
                          {Math.round(totalNutrition[key] || 0)}
                        </p>
                        <p className="text-[10px] text-slate-400 mt-0.5">{label}</p>
                        <p className="text-[10px] text-slate-300">{unit}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            <div className="grid gap-2 text-sm">
              {[
                { label: "营养建议", value: result.nutrition_summary },
                { label: "预算说明", value: result.budget_note },
                { label: "健康提示", value: result.health_tip },
              ].map(({ label, value }) => (
                <div key={label} className="flex gap-3">
                  <span className="w-16 flex-shrink-0 text-xs font-medium text-slate-400 pt-0.5">{label}</span>
                  <span className="text-slate-600">{value}</span>
                </div>
              ))}
            </div>

            <button type="button" onClick={handleConfirm}
              disabled={confirming || checkedItems.length === 0} className="btn-orange">
              {confirming ? "确认中..." : "✓ 确认选择并记录"}
            </button>
          </div>

          {/* 下单备注 */}
          <DishRemarksPanel
            visibleRemarks={visibleRemarks}
            editedRemarks={editedRemarks}
            onEdit={(id, text) => setEditedRemarks((prev) => ({ ...prev, [id]: text }))}
          />
        </div>
      )}

      {/* Toast 提示 */}
      {toast && (
        <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-2xl px-5 py-3.5 shadow-xl text-sm font-medium animate-slide-up ${
          toast.type === "success"
            ? "bg-emerald-600 text-white"
            : "bg-red-500 text-white"
        }`}>
          <span className="text-base">{toast.type === "success" ? "✓" : "⚠"}</span>
          {toast.msg}
        </div>
      )}
    </section>
  );
}

/* ─── 近期饮食分析 ─── */
function AnalysisPanel({ analysis }) {
  const flags      = analysis?.recent_pattern?.flags || [];
  const preferNext = analysis?.prefer_next || [];
  return (
    <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-mealmate-mint to-emerald-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-mealmate-green">近期饮食分析</p>
      <div className="mt-3 space-y-2 text-sm">
        <div>
          <span className="text-xs text-slate-500">发现</span>
          <p className="mt-0.5 text-slate-700">{flags.length ? flags.join("、") : "暂无明显问题"}</p>
        </div>
        <div>
          <span className="text-xs text-slate-500">建议</span>
          <p className="mt-0.5 font-medium text-mealmate-green">{preferNext.length ? preferNext.join("、") : "均衡饮食"}</p>
        </div>
      </div>
    </div>
  );
}

/* ─── 最近同餐型记录 ─── */
function RecentMeals({ meals, mealTypeLabel }) {
  return (
    <div className="page-panel">
      <h3 className="flex items-center gap-2 font-semibold text-slate-800">
        <span>🕐</span>
        最近{mealTypeLabel ? ` 3 次${mealTypeLabel}` : " 3 餐"}
      </h3>
      <div className="mt-4 space-y-2">
        {meals.length === 0 ? (
          <p className="text-sm text-slate-400">
            暂无{mealTypeLabel ? mealTypeLabel : ""}记录，将基于画像和预算推荐。
          </p>
        ) : meals.slice(0, 3).map((meal) => (
          <div key={meal.meal_id} className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm">
            <span className="text-base">{meal.input_type === "photo" ? "📷" : "✍️"}</span>
            <div className="min-w-0">
              <p className="truncate font-medium text-slate-700">
                {(meal.recognized_foods || []).map((f) => f.standard_name || f.raw_text).filter(Boolean).join("、") || "未识别菜品"}
              </p>
              <p className="text-xs text-slate-400">{meal.occurred_at}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── 分类 Tab 推荐 ─── */
function GroupedRecommendations({ recommendations, checkedIds, onToggle, onRefresh, loading }) {
  const [activeTab, setActiveTab] = useState("主食");

  const grouped = useMemo(() => {
    const g = {};
    for (const item of recommendations) {
      const ct = item.course_type || "主食";
      if (!g[ct]) g[ct] = [];
      g[ct].push(item);
    }
    return g;
  }, [recommendations]);

  const availableTabs = COURSE_ORDER.filter((ct) => grouped[ct]?.length > 0);

  useEffect(() => {
    if (availableTabs.length > 0 && !grouped[activeTab]) {
      setActiveTab(availableTabs[0]);
    }
  }, [recommendations]);

  if (recommendations.length === 0) {
    return (
      <div className="page-panel flex items-center justify-center py-12 text-sm text-slate-400">
        <div className="text-center">
          <p className="text-3xl">🍽️</p>
          <p className="mt-2">点击"生成推荐"显示各类搭配选项</p>
        </div>
      </div>
    );
  }

  const currentItems = grouped[activeTab] || [];
  const cfg = COURSE_CONFIG[activeTab] || COURSE_CONFIG["主食"];

  return (
    <div className="space-y-3">
      {/* 标题行 */}
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-700">推荐搭配</p>
        <button type="button" onClick={onRefresh} disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm hover:border-mealmate-green hover:text-mealmate-green disabled:cursor-not-allowed disabled:opacity-50 transition">
          <span className={loading ? "animate-spin" : ""}>🔄</span>
          {loading ? "换一批中..." : "换一批"}
        </button>
      </div>

      {/* Tab 按钮 */}
      <div className="flex gap-2">
        {availableTabs.map((ct) => {
          const c = COURSE_CONFIG[ct] || COURSE_CONFIG["主食"];
          const checkedCount = (grouped[ct] || []).filter((i) => checkedIds.has(i.dish_id)).length;
          const isActive = activeTab === ct;
          return (
            <button key={ct} type="button" onClick={() => setActiveTab(ct)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? `${c.activeBg} text-white shadow-sm`
                  : `bg-slate-100 ${c.color} hover:bg-slate-200`
              }`}>
              <span>{c.icon}</span>
              <span>{ct}</span>
              {checkedCount > 0 && (
                <span className={`text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center ${
                  isActive ? "bg-white/30" : "bg-white shadow-sm text-slate-600"
                }`}>{checkedCount}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* 当前 Tab 菜品列表 */}
      <div className={`rounded-xl border ${cfg.border} overflow-hidden`}>
        <div className="divide-y divide-slate-100">
          {currentItems.map((item, idx) => {
            const checked = checkedIds.has(item.dish_id);
            return (
              <label key={item.dish_id}
                className={`flex cursor-pointer items-start gap-3 px-4 py-3.5 transition-colors ${
                  checked ? "bg-white" : "bg-slate-50/50"
                }`}>
                {/* 排名 */}
                <div className={`mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  idx === 0 ? "bg-yellow-100 text-yellow-700" :
                  idx === 1 ? "bg-slate-100 text-slate-500" :
                              "bg-orange-50 text-orange-400"
                }`}>{idx + 1}</div>

                {/* 复选框 */}
                <input type="checkbox" checked={checked} onChange={() => onToggle(item.dish_id)}
                  className="mt-0.5 h-4 w-4 flex-shrink-0 rounded border-slate-300 accent-emerald-600 cursor-pointer" />

                {/* 内容 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className={`font-medium text-sm ${checked ? "text-slate-800" : "text-slate-400"}`}>
                        {item.name}
                      </p>
                      <p className={`mt-0.5 text-xs leading-snug ${checked ? "text-slate-500" : "text-slate-300"}`}>
                        {item.reason}
                      </p>
                      {checked && (
                        <p className={`mt-1 text-xs ${cfg.color}`}>✦ {item.nutrition_highlight}</p>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className={`font-bold text-sm ${checked ? "text-mealmate-orange" : "text-slate-300"}`}>
                        ¥{item.price}
                      </p>
                      {item.score > 0 && (
                        <p className="text-[10px] text-slate-400 mt-0.5">{item.score}分</p>
                      )}
                    </div>
                  </div>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      <p className="text-xs text-slate-400 text-center pt-1">
        勾选想要的菜品，营养和备注将在下方实时更新
      </p>
    </div>
  );
}

/* ─── 逐菜备注面板 ─── */
function DishRemarksPanel({ visibleRemarks, editedRemarks, onEdit }) {
  const [copiedId, setCopiedId] = useState(null);

  async function copyRemark(id, text) {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text; ta.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(ta); ta.select();
        document.execCommand("copy"); document.body.removeChild(ta);
      }
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch { /* ignore */ }
  }

  if (visibleRemarks.length === 0) {
    return (
      <div className="page-panel flex items-center justify-center py-12 text-sm text-slate-400">
        <div className="text-center">
          <p className="text-2xl">📋</p>
          <p className="mt-2">勾选菜品后显示下单备注</p>
        </div>
      </div>
    );
  }

  const byType = {};
  for (const r of visibleRemarks) {
    const ct = r.course_type || "主食";
    if (!byType[ct]) byType[ct] = [];
    byType[ct].push(r);
  }

  return (
    <div className="page-panel space-y-4">
      <h3 className="flex items-center gap-2 font-semibold text-slate-800"><span>📋</span> 下单备注</h3>
      <p className="text-xs text-slate-400">每道菜独立备注，可直接编辑后复制给商家</p>

      {COURSE_ORDER.filter((ct) => byType[ct]).map((ct) => {
        const cfg = COURSE_CONFIG[ct] || COURSE_CONFIG["主食"];
        return (
          <div key={ct} className="space-y-2">
            <p className={`text-xs font-semibold ${cfg.color} flex items-center gap-1`}>
              <span>{cfg.icon}</span> {ct}
            </p>
            {byType[ct].map((r) => {
              const text = editedRemarks[r.dish_id] ?? r.remark;
              return (
                <div key={r.dish_id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-2">
                  <p className="text-xs font-medium text-slate-600">{r.name}</p>
                  <textarea
                    value={text}
                    onChange={(e) => onEdit(r.dish_id, e.target.value)}
                    rows={2}
                    className="w-full resize-none rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-mealmate-green focus:outline-none focus:ring-1 focus:ring-mealmate-green/30"
                  />
                  <button
                    type="button"
                    onClick={() => copyRemark(r.dish_id, text)}
                    className="flex items-center gap-1 text-xs text-slate-500 hover:text-mealmate-green transition"
                  >
                    {copiedId === r.dish_id ? "✓ 已复制" : "⎘ 复制备注"}
                  </button>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
