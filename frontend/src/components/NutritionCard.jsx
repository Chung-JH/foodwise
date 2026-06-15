function NutritionCard({ title = "营养信息", items = ["热量适中", "蛋白质较高", "仅供参考"] }) {
  return (
    <div className="page-panel">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded-md bg-slate-100 px-3 py-1 text-sm text-slate-700">
            {item}
          </span>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">营养估算仅供参考，不构成医学建议。</p>
    </div>
  );
}

export default NutritionCard;
