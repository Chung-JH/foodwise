import { NavLink, Route, Routes } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Profile from "./pages/Profile.jsx";
import LogMeal from "./pages/LogMeal.jsx";
import MealHistory from "./pages/MealHistory.jsx";
import Recommend from "./pages/Recommend.jsx";
import Contacts from "./pages/Contacts.jsx";
import { BrandLogo } from "./components/BrandLogo.jsx";

const navItems = [
  { to: "/",         label: "首页" },
  { to: "/profile",  label: "偏好设置" },
  { to: "/log",      label: "记录一餐" },
  { to: "/meals",    label: "饮食历史" },
  { to: "/recommend",label: "推荐下一餐" },
  { to: "/contacts", label: "亲友档案" },
];

function App() {
  return (
    <div className="min-h-screen bg-stone-50 text-mealmate-ink">
      <header className="sticky top-0 z-50 border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-6 py-3.5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2.5">
            <BrandLogo className="h-8 w-8 text-mealmate-green" />
            <div className="leading-none">
              <p className="text-[10px] font-medium tracking-[0.18em] text-mealmate-green/70 uppercase">FoodWise</p>
              <h1 className="mt-0.5 text-[17px] font-bold tracking-tight text-mealmate-ink">慧食</h1>
            </div>
          </div>
          <nav className="flex flex-wrap gap-0.5">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-mealmate-green/10 text-mealmate-green"
                      : "text-stone-500 hover:bg-stone-100 hover:text-stone-800"
                  }`
                }
                end={item.to === "/"}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-[1440px] px-6 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/log" element={<LogMeal />} />
          <Route path="/meals" element={<MealHistory />} />
          <Route path="/recommend" element={<Recommend />} />
          <Route path="/contacts" element={<Contacts />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
