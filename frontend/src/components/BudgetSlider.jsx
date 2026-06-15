const TRACK_MAX = 80;

const PRESETS = [
  { label: "经济", range: [8, 15] },
  { label: "日常", range: [15, 30] },
  { label: "改善", range: [30, 55] },
];

function BudgetSlider({ label = "价格区间", value, onChange, disabled = false }) {
  const currentMin = Number(value?.[0] ?? 15);
  const currentMax = Number(value?.[1] ?? 30);

  const updateValue = (index, nextValue) => {
    if (!onChange) return;
    const nextRange = [currentMin, currentMax];
    nextRange[index] = Number(nextValue);
    if (nextRange[0] > nextRange[1]) nextRange.sort((a, b) => a - b);
    onChange(nextRange);
  };

  const fillLeft = `${Math.round((Math.min(currentMin, TRACK_MAX) / TRACK_MAX) * 100)}%`;
  const fillWidth = `${Math.round((Math.min(currentMax - currentMin, TRACK_MAX) / TRACK_MAX) * 100)}%`;

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className="rounded-full bg-orange-100 px-2.5 py-0.5 text-sm font-semibold text-mealmate-orange">
          ¥{currentMin}–{currentMax}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <label className="space-y-1">
          <span className="text-xs text-slate-500">最低（元）</span>
          <input
            type="number"
            min="0"
            value={currentMin}
            disabled={disabled}
            onChange={(e) => updateValue(0, e.target.value)}
            className="input-base"
          />
        </label>
        <label className="space-y-1">
          <span className="text-xs text-slate-500">最高（元）</span>
          <input
            type="number"
            min="0"
            value={currentMax}
            disabled={disabled}
            onChange={(e) => updateValue(1, e.target.value)}
            className="input-base"
          />
        </label>
      </div>

      <div className="relative mt-3 h-2 rounded-full bg-slate-200">
        <div
          className="absolute h-2 rounded-full bg-mealmate-green"
          style={{ left: fillLeft, width: fillWidth }}
        />
      </div>

      <div className="mt-3 flex gap-1.5">
        {PRESETS.map((preset) => {
          const active = currentMin === preset.range[0] && currentMax === preset.range[1];
          return (
            <button
              key={preset.label}
              type="button"
              disabled={disabled}
              onClick={() => onChange?.(preset.range)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                active
                  ? "bg-mealmate-green text-white"
                  : "bg-white border border-slate-200 text-slate-500 hover:border-mealmate-green hover:text-mealmate-green"
              }`}
            >
              {preset.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default BudgetSlider;
