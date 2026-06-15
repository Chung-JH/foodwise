function PhotoUpload({ file, previewUrl, onChange, disabled = false }) {
  return (
    <label
      className={`block cursor-pointer rounded-xl border-2 border-dashed bg-slate-50 transition ${
        disabled
          ? "cursor-not-allowed opacity-60"
          : "border-slate-300 hover:border-mealmate-green hover:bg-mealmate-mint/30"
      }`}
    >
      <input
        type="file"
        accept="image/*"
        disabled={disabled}
        onChange={(e) => onChange?.(e.target.files?.[0] || null)}
        className="hidden"
      />
      <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 p-6">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt="菜品预览"
            className="max-h-48 w-full rounded-lg object-cover shadow-sm"
          />
        ) : (
          <>
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm">
              <svg className="h-8 w-8 text-mealmate-green" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM18.75 10.5h.008v.008h-.008V10.5z" />
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-700">点击选择菜品照片或菜单截图</p>
            <p className="text-xs text-slate-400">调用 Qwen-VL 识别菜名、营养和价格</p>
          </>
        )}
        {file && (
          <p className="mt-1 max-w-full truncate text-center text-xs text-mealmate-green">
            {file.name}
          </p>
        )}
        {!previewUrl && (
          <span className="mt-1 rounded-lg bg-mealmate-green px-4 py-1.5 text-sm font-medium text-white">
            选择图片
          </span>
        )}
      </div>
    </label>
  );
}

export default PhotoUpload;
