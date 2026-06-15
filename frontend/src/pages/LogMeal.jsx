import { useEffect, useMemo, useState } from "react";
import PhotoUpload from "../components/PhotoUpload.jsx";

const tabs = [
  { key: "text", label: "✍️ 文本记录" },
  { key: "photo", label: "📷 照片上传" },
];

function toDatetimeLocal(date = new Date()) {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60 * 1000).toISOString().slice(0, 16);
}

function LogMeal() {
  const [activeTab, setActiveTab] = useState("text");
  const [text, setText] = useState("昨天晚上吃了炸鸡汉堡套餐和可乐");
  const [textResult, setTextResult] = useState(null);
  const [photoFile, setPhotoFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [photoResult, setPhotoResult] = useState(null);
  const [photoOccurredAt, setPhotoOccurredAt] = useState(toDatetimeLocal());
  const [photoPrice, setPhotoPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [savingPhoto, setSavingPhoto] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!photoFile) { setPreviewUrl(""); return; }
    const url = URL.createObjectURL(photoFile);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [photoFile]);

  const currentResult = useMemo(() => (activeTab === "text" ? textResult : photoResult), [activeTab, textResult, photoResult]);

  const handleTextSubmit = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    setTextResult(null);
    try {
      const res = await fetch("/api/log-meal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "解析失败");
      setTextResult(data);
      setMessage("文本记录已解析并保存到饮食历史。");
    } catch (err) {
      setError(err.message || "解析失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoAnalyze = async () => {
    if (!photoFile) { setError("请先选择一张菜品照片或菜单截图"); return; }
    setLoading(true);
    setError("");
    setMessage("");
    setPhotoResult(null);
    const formData = new FormData();
    formData.append("image", photoFile);
    if (photoPrice) formData.append("price", photoPrice);
    try {
      const res = await fetch("/api/log-meal/photo", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "照片分析失败");
      setPhotoResult(data);
      setPhotoPrice(String(data.analysis.price ?? ""));
      setMessage("照片分析完成，菜品已加入菜品库。请确认时间和价格后保存。");
    } catch (err) {
      setError(err.message || "照片分析失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoSave = async () => {
    if (!photoResult?.analysis) { setError("请先完成照片分析"); return; }
    setSavingPhoto(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch("/api/log-meal/photo/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis: photoResult.analysis, occurred_at: photoOccurredAt, price: photoPrice }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "保存失败");
      setPhotoResult({ ...photoResult, savedMeal: data.meal, saved: true });
      setMessage("照片记录已保存到饮食历史。");
    } catch (err) {
      setError(err.message || "保存失败，请稍后重试");
    } finally {
      setSavingPhoto(false);
    }
  };

  return (
    <section className="space-y-6">
      <div className="page-panel">
        <p className="section-label">记录一餐</p>
        <h2 className="page-title">文本或照片记录饮食</h2>
        <p className="mt-2 text-slate-500">
          打字描述你吃了什么，AI 自动识别时间和菜品；或上传菜品照片，AI 自动分析菜名、营养和价格。
        </p>
      </div>

      {message && <div className="status-success">✓ {message}</div>}
      {error && <div className="status-error">⚠ {error}</div>}

      <div className="page-panel space-y-5">
        {/* Tab 选择器 */}
        <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => { setActiveTab(tab.key); setError(""); setMessage(""); }}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
                activeTab === tab.key
                  ? "bg-white text-mealmate-green shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "text" ? (
          <div className="space-y-4">
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">自然语言饮食记录</span>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={5}
                placeholder="例如：昨天晚上吃了炸鸡汉堡套餐和可乐"
                className="input-base resize-none"
              />
            </label>
            <button type="button" onClick={handleTextSubmit} disabled={loading} className="btn-primary">
              {loading ? <><span className="animate-spin">⏳</span> 解析中...</> : "解析并保存"}
            </button>
          </div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
            <PhotoUpload
              file={photoFile}
              previewUrl={previewUrl}
              disabled={loading}
              onChange={(file) => { setPhotoFile(file); setPhotoResult(null); setMessage(""); setError(""); }}
            />
            <div className="space-y-4">
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-slate-700">用餐时间</span>
                <input type="datetime-local" value={photoOccurredAt} onChange={(e) => setPhotoOccurredAt(e.target.value)} className="input-base" />
              </label>
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-slate-700">价格（元）</span>
                <input
                  type="number" min="0" step="0.1" value={photoPrice}
                  onChange={(e) => setPhotoPrice(e.target.value)}
                  placeholder="照片无价格时可手动补充"
                  className="input-base"
                />
              </label>
              <button type="button" onClick={handlePhotoAnalyze} disabled={loading || !photoFile} className="btn-primary">
                {loading ? <><span className="animate-spin">⏳</span> 分析中...</> : "🔍 分析照片"}
              </button>
            </div>
          </div>
        )}
      </div>

      {currentResult && (
        <ResultPanel
          mode={activeTab}
          result={currentResult}
          photoOccurredAt={photoOccurredAt}
          setPhotoOccurredAt={setPhotoOccurredAt}
          photoPrice={photoPrice}
          setPhotoPrice={setPhotoPrice}
          onPhotoSave={handlePhotoSave}
          savingPhoto={savingPhoto}
        />
      )}
    </section>
  );
}

function ResultPanel({ mode, result, photoOccurredAt, setPhotoOccurredAt, photoPrice, setPhotoPrice, onPhotoSave, savingPhoto }) {
  const parsed = result.parsed;
  const textMeal = result.meal;
  const photoAnalysis = result.analysis;
  const photoMeal = result.savedMeal;
  const mealTime = parsed?.meal_time || photoMeal;
  const foods = parsed?.recognized_foods || (photoAnalysis ? [photoAnalysisToFood(photoAnalysis)] : []);
  const saved = result.saved;

  return (
    <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="page-panel space-y-4">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800">
          <span>⏱️</span>
          {mode === "text" ? "解析结果" : "确认信息"}
        </h3>

        {mode === "text" ? (
          <TimeBlock mealTime={mealTime} />
        ) : (
          <div className="space-y-3">
            <label className="block space-y-1.5 text-sm">
              <span className="font-medium text-slate-700">用餐时间（可编辑确认）</span>
              <input type="datetime-local" value={photoOccurredAt} disabled={saved} onChange={(e) => setPhotoOccurredAt(e.target.value)} className="input-base" />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="font-medium text-slate-700">价格（可手动补充）</span>
              <input type="number" min="0" step="0.1" value={photoPrice} disabled={saved} onChange={(e) => setPhotoPrice(e.target.value)} className="input-base" />
            </label>
            {photoAnalysis?.confidence < 0.7 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
                ⚠ 照片识别结果可能不准确，请确认菜名、价格和营养后再保存。
              </div>
            )}
          </div>
        )}

        <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-500">
          {mode === "text" ? "AI 已识别并保存到饮食历史。" : saved ? "照片记录已保存到饮食历史。" : "照片分析完成，确认后保存。"}
        </div>

        {mode === "photo" && (
          <button
            type="button"
            onClick={onPhotoSave}
            disabled={saved || savingPhoto}
            className="btn-orange"
          >
            {saved ? "✓ 已保存" : savingPhoto ? "保存中..." : "确认保存"}
          </button>
        )}

        {textMeal && (
          <p className="text-xs text-slate-400">总热量约 {textMeal.total_nutrition?.calories_kcal || 0} kcal</p>
        )}
        {photoMeal && (
          <p className="text-xs text-slate-400">消费 ¥{photoMeal.total_price}</p>
        )}
      </div>

      <div className="page-panel space-y-4">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800">
          <span>🥗</span> 菜品与营养
        </h3>
        <div className="space-y-3">
          {foods.map((food) => <FoodCard key={food.standard_name || food.dish_name} food={food} />)}
        </div>
      </div>
    </div>
  );
}

function TimeBlock({ mealTime }) {
  if (!mealTime) return null;
  const assumption = mealTime.time_assumption || {};
  const unknown = mealTime.time_resolution === "unknown";
  return (
    <div className="space-y-3">
      <label className="block space-y-1.5 text-sm">
        <span className="font-medium text-slate-700">用餐时间</span>
        <input value={mealTime.occurred_at || ""} readOnly className="input-base bg-slate-50" />
      </label>
      {unknown && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
          ⚠ 没有识别到用餐时间，请补充一下什么时候吃的再保存。
        </div>
      )}
      <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">时间识别详情</p>
        <div className="space-y-1 text-xs text-slate-600">
          <p><span className="text-slate-400 w-20 inline-block">你的描述</span>{assumption.raw_time_text || "未提供"}</p>
          <p><span className="text-slate-400 w-20 inline-block">识别结果</span>{assumption.resolved_occurred_at}</p>
          <p><span className="text-slate-400 w-20 inline-block">推断依据</span>{assumption.date_source || "未提供"}</p>
        </div>
      </div>
    </div>
  );
}

function FoodCard({ food }) {
  const nutrition = food.estimated_nutrition || {};
  const tags = food.nutrition_tags || [];
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-slate-800">{food.standard_name || food.dish_name}</h4>
          <p className="mt-0.5 text-xs text-slate-400">{food.category} · {food.portion || "一份"}</p>
        </div>
        {typeof food.price === "number" && (
          <span className="flex-shrink-0 rounded-full bg-orange-100 px-2.5 py-0.5 text-sm font-semibold text-mealmate-orange">
            ¥{food.price}
          </span>
        )}
      </div>
      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tags.map((tag) => (
            <span key={tag} className="rounded-full bg-mealmate-mint px-2 py-0.5 text-xs font-medium text-mealmate-green">{tag}</span>
          ))}
        </div>
      )}
      <div className="mt-3 grid grid-cols-5 gap-1 text-center text-xs">
        {[
          { label: "热量", value: nutrition.calories_kcal ?? 0, unit: "kcal" },
          { label: "蛋白质", value: nutrition.protein_g ?? 0, unit: "g" },
          { label: "脂肪", value: nutrition.fat_g ?? 0, unit: "g" },
          { label: "碳水", value: nutrition.carbs_g ?? 0, unit: "g" },
          { label: "钠", value: nutrition.sodium_mg ?? 0, unit: "mg" },
        ].map(({ label, value, unit }) => (
          <div key={label} className="flex flex-col">
            <span className="text-slate-400">{label}</span>
            <span className="font-semibold text-slate-700">{value}</span>
            <span className="text-slate-400">{unit}</span>
          </div>
        ))}
      </div>
      {food.assumption && <p className="mt-2 text-xs text-slate-400">营养估算说明：{food.assumption}</p>}
    </div>
  );
}

function photoAnalysisToFood(analysis) {
  return {
    standard_name: analysis.dish_name,
    category: analysis.category,
    portion: "一份",
    estimated_nutrition: analysis.estimated_nutrition,
    nutrition_tags: analysis.nutrition_tags,
    price: analysis.price,
    confidence: analysis.confidence,
    assumption: analysis.assumption,
  };
}

export default LogMeal;
