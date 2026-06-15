import { Link } from "react-router-dom";
import { BrandLogo } from "../components/BrandLogo.jsx";

const actions = [
  { to: "/profile",   label: "设置偏好",   desc: "口味、忌口、预算、健康目标",           icon: "👤", accent: "border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50" },
  { to: "/log",       label: "记录一餐",   desc: "打字或拍照，AI 自动识别内容和营养",     icon: "✍️", accent: "border-slate-200 hover:border-sky-300 hover:bg-sky-50/50" },
  { to: "/meals",     label: "饮食历史",   desc: "查看记录、营养摄入与消费统计",           icon: "📋", accent: "border-slate-200 hover:border-violet-300 hover:bg-violet-50/50" },
  { to: "/recommend", label: "推荐下一餐", desc: "按餐型推荐主食/饮品/点心，自动生成备注", icon: "🍽️", accent: "border-slate-200 hover:border-orange-300 hover:bg-orange-50/50" },
  { to: "/contacts",  label: "亲友档案",   desc: "保存家人朋友的口味偏好，帮他们点餐",   icon: "👥", accent: "border-slate-200 hover:border-pink-300 hover:bg-pink-50/50" },
];

const steps = [
  "告诉 AI 你的口味偏好和预算",
  "打字或拍照记录你吃了什么",
  "查看饮食历史和营养统计",
  "按餐型获取分类推荐，勾选搭配一键复制备注",
];

const usageGuide = [
  {
    step: "01", title: "告诉 AI 你的口味", page: "/profile", pageLabel: "去设置",
    bg: "bg-emerald-50/60", border: "border-emerald-200/70",
    stepColor: "text-emerald-600 bg-emerald-100", linkColor: "text-emerald-700 hover:bg-emerald-100", dotColor: "bg-emerald-300",
    items: [
      "写下你的口味偏好，例：喜欢微辣，不太能吃油腻的",
      "填写不吃的食材，例：香菜、葱、花生",
      "勾选健康目标：少油 / 高蛋白 / 低碳水 / 多蔬菜",
      "拖动滑块设定早、午、晚餐各自的预算范围",
    ],
  },
  {
    step: "02", title: "记录你吃了什么", page: "/log", pageLabel: "去记录",
    bg: "bg-sky-50/60", border: "border-sky-200/70",
    stepColor: "text-sky-600 bg-sky-100", linkColor: "text-sky-700 hover:bg-sky-100", dotColor: "bg-sky-300",
    items: [
      "打字记录：随口描述就行，例：午饭吃了炸鸡汉堡和可乐",
      "拍照记录：上传菜品照片，AI 自动识别内容与营养",
      '支持自然时间描述，例："今天早上""昨晚""上午十一点"',
    ],
  },
  {
    step: "03", title: "回顾你的饮食", page: "/meals", pageLabel: "看历史",
    bg: "bg-violet-50/60", border: "border-violet-200/70",
    stepColor: "text-violet-600 bg-violet-100", linkColor: "text-violet-700 hover:bg-violet-100", dotColor: "bg-violet-300",
    items: [
      "所有餐食按时间倒序，最近一餐置顶",
      "每条记录显示热量、蛋白质、脂肪、碳水等营养估算",
      "可切换近 3 / 7 / 14 / 30 天，顶部汇总总消费与总热量",
    ],
  },
  {
    step: "04", title: "获取个性化推荐", page: "/recommend", pageLabel: "去推荐",
    bg: "bg-orange-50/60", border: "border-orange-200/70",
    stepColor: "text-orange-600 bg-orange-100", linkColor: "text-orange-700 hover:bg-orange-100", dotColor: "bg-orange-300",
    items: [
      "选择早餐/午餐/晚餐/加餐，设置这次的预算",
      "可填写额外限定，例：今天想吃清淡一些",
      "AI 推荐主食、饮品和点心搭配，勾选组合复制备注",
      "一键复制下单备注，粘贴到外卖 App 备注栏即可",
    ],
  },
  {
    step: "05", title: "帮亲友点餐", page: "/contacts", pageLabel: "管理亲友",
    bg: "bg-pink-50/60", border: "border-pink-200/70",
    stepColor: "text-pink-600 bg-pink-100", linkColor: "text-pink-700 hover:bg-pink-100", dotColor: "bg-pink-300",
    items: [
      "在【亲友档案】新建一个人，填写口味和忌口",
      '去【推荐下一餐】，在"为谁点"里选择这个人',
      "AI 会根据他们的口味推荐，备注也会自动调整",
    ],
  },
];

function Home() {
  return (
    <section className="space-y-5">

      {/* Hero */}
      <div className="page-panel">
        <div className="flex items-center gap-3">
          <BrandLogo className="h-9 w-9 flex-shrink-0 text-mealmate-green" />
          <div>
            <p className="section-label">FoodWise</p>
            <h2 className="page-title">慧食</h2>
          </div>
        </div>

        <p className="mt-3 text-base leading-relaxed text-slate-500">
          记录饮食、AI 分析营养、个性化推荐下一餐，结合你的口味偏好、预算与健康目标，自动生成外卖备注。
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 border-t border-slate-100 pt-5 md:grid-cols-4">
          {steps.map((step, i) => (
            <div key={i} className="flex items-start gap-2.5">
              <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-mealmate-green/10 text-[10px] font-semibold text-mealmate-green">
                {i + 1}
              </span>
              <p className="text-sm leading-snug text-slate-500">{step}</p>
            </div>
          ))}
        </div>

        <p className="mt-4 text-xs text-slate-400">营养估算仅供参考，不构成医学建议。</p>
      </div>

      {/* 快速入口 */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {actions.map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className={`group flex items-center gap-3.5 rounded-2xl border bg-white p-4 transition-all duration-200 ${action.accent}`}
          >
            <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-slate-50 text-lg transition-colors group-hover:bg-white">
              {action.icon}
            </span>
            <div className="min-w-0">
              <span className="block text-sm font-semibold text-mealmate-ink">{action.label}</span>
              <span className="mt-0.5 block truncate text-xs text-slate-400">{action.desc}</span>
            </div>
          </Link>
        ))}
      </div>

      {/* 使用说明 */}
      <div className="page-panel">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-semibold text-slate-800">使用说明</h3>
          <span className="text-xs text-slate-400">5 步上手</span>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {usageGuide.map((guide) => (
            <div key={guide.step} className={`rounded-xl border p-4 ${guide.bg} ${guide.border}`}>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${guide.stepColor}`}>
                    {guide.step}
                  </span>
                  <p className="text-sm font-semibold text-slate-700">{guide.title}</p>
                </div>
                <Link
                  to={guide.page}
                  className={`flex-shrink-0 rounded-lg px-2.5 py-1 text-xs font-medium transition ${guide.linkColor}`}
                >
                  {guide.pageLabel} →
                </Link>
              </div>
              <ul className="mt-3 space-y-1.5">
                {guide.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs leading-relaxed text-slate-500">
                    <span className={`mt-[5px] h-1 w-1 flex-shrink-0 rounded-full ${guide.dotColor}`} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

    </section>
  );
}

export default Home;
