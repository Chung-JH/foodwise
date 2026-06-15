function RemarkEditor({ value, onChange, onCopy, copied = false, disabled = false }) {
  return (
    <div className="page-panel flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="section-label">智能备注</p>
          <h3 className="page-title text-xl">可编辑后复制</h3>
          <p className="mt-1 text-sm text-slate-500">复制到外卖 App 下单备注栏。</p>
        </div>
        <button
          type="button"
          disabled={disabled || !value}
          onClick={onCopy}
          className={`flex-shrink-0 rounded-lg px-4 py-2 text-sm font-medium transition ${
            copied
              ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
              : "btn-primary"
          } disabled:cursor-not-allowed disabled:opacity-40`}
        >
          {copied ? "✓ 已复制" : "一键复制备注"}
        </button>
      </div>
      <textarea
        value={value || ""}
        disabled={disabled}
        onChange={(e) => onChange?.(e.target.value)}
        rows={4}
        placeholder="生成推荐后自动填入备注，也可手动编辑"
        className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-4 font-mono text-sm leading-relaxed text-slate-700 outline-none transition-colors focus:border-mealmate-green focus:ring-2 focus:ring-mealmate-green/10 disabled:bg-slate-100"
      />
    </div>
  );
}

export default RemarkEditor;
