import { useEffect, useState } from "react";
import BudgetSlider from "../components/BudgetSlider.jsx";

const emptyForm = {
  name: "",
  taste_description: "",
  avoid_ingredients: "",
  health_goals: "",
  default_budget: { breakfast: [8, 15], lunch: [15, 30], dinner: [20, 40] },
  remark_habits: "",
};

const mealLabels = { breakfast: "早餐预算", lunch: "午餐预算", dinner: "晚餐预算" };

function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadContacts() {
    setError("");
    try {
      const res = await fetch("/api/contacts");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "亲友列表加载失败");
      setContacts(data.contacts || []);
    } catch (err) {
      setError(err.message || "亲友列表加载失败");
    }
  }

  useEffect(() => { loadContacts(); }, []);

  const openCreateForm = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormOpen(true);
    setMessage("");
    setError("");
  };

  const openEditForm = (contact) => {
    setEditingId(contact.contact_id);
    setForm({
      name: contact.name || "",
      taste_description: contact.taste_description || "",
      avoid_ingredients: listToText(contact.avoid_ingredients),
      health_goals: listToText(contact.health_goals),
      default_budget: { ...emptyForm.default_budget, ...(contact.default_budget || {}) },
      remark_habits: listToText(contact.remark_habits),
    });
    setFormOpen(true);
    setMessage("");
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");
    const payload = {
      name: form.name,
      taste_description: form.taste_description,
      avoid_ingredients: textToList(form.avoid_ingredients),
      health_goals: textToList(form.health_goals),
      default_budget: form.default_budget,
      remark_habits: textToList(form.remark_habits),
    };
    const url = editingId ? `/api/contacts/${editingId}` : "/api/contacts";
    const method = editingId ? "PUT" : "POST";
    try {
      const res = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "保存失败");
      await loadContacts();
      setFormOpen(false);
      setMessage(editingId ? "亲友档案已更新。" : "亲友档案已创建。");
    } catch (err) {
      setError(err.message || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (contactId) => {
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const res = await fetch(`/api/contacts/${contactId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "删除失败");
      await loadContacts();
      setMessage("亲友档案已删除。");
      if (editingId === contactId) setFormOpen(false);
    } catch (err) {
      setError(err.message || "删除失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <div className="page-panel">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="section-label">亲友档案</p>
            <h2 className="page-title">为家人朋友保存点餐偏好</h2>
            <p className="mt-2 text-slate-500">
              切换"帮谁点"后，推荐和备注会基于对应亲友的口味、忌口、预算和健康目标。
            </p>
          </div>
          <button type="button" onClick={openCreateForm} className="btn-primary flex-shrink-0">
            + 新建亲友
          </button>
        </div>
      </div>

      {message && <div className="status-success">✓ {message}</div>}
      {error && <div className="status-error">⚠ {error}</div>}

      <div className="grid gap-3 md:grid-cols-2">
        {contacts.length === 0 ? (
          <div className="page-panel col-span-full text-center text-sm text-slate-400">
            <p className="text-4xl">👥</p>
            <p className="mt-2">暂无亲友档案</p>
            <p className="mt-1">点击"新建亲友"添加家人或朋友的口味档案</p>
          </div>
        ) : (
          contacts.map((contact) => (
            <ContactCard
              key={contact.contact_id}
              contact={contact}
              onEdit={() => openEditForm(contact)}
              onDelete={() => handleDelete(contact.contact_id)}
              disabled={loading}
            />
          ))
        )}
      </div>

      {formOpen && (
        <div className="page-panel">
          <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <h3 className="flex items-center gap-2 text-lg font-semibold">
              <span>{editingId ? "✏️" : "➕"}</span>
              {editingId ? "编辑亲友档案" : "新建亲友档案"}
            </h3>
            <button type="button" onClick={() => setFormOpen(false)} className="btn-secondary">
              关闭
            </button>
          </div>

          <form onSubmit={handleSubmit} className="mt-5 space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <TextField label="姓名" value={form.name} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="例如：妈妈" />
              <TextField label="健康目标" value={form.health_goals} onChange={(v) => setForm((f) => ({ ...f, health_goals: v }))} placeholder="例如：少油，少盐，多蔬菜" />
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">口味描述</span>
              <textarea
                value={form.taste_description}
                onChange={(e) => setForm((f) => ({ ...f, taste_description: e.target.value }))}
                rows={3}
                placeholder="例如：清淡，少盐，不吃辣，喜欢汤类"
                className="input-base resize-none"
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <TextField label="忌口/过敏原" value={form.avoid_ingredients} onChange={(v) => setForm((f) => ({ ...f, avoid_ingredients: v }))} placeholder="例如：香菜，葱，花生" />
              <TextField label="备注习惯" value={form.remark_habits} onChange={(v) => setForm((f) => ({ ...f, remark_habits: v }))} placeholder="例如：少油，不要香菜" />
            </div>

            <div>
              <p className="text-sm font-medium text-slate-700">默认预算</p>
              <div className="mt-3 grid gap-4 md:grid-cols-3">
                {Object.entries(mealLabels).map(([mealType, label]) => (
                  <BudgetSlider
                    key={mealType}
                    label={label}
                    value={form.default_budget[mealType]}
                    onChange={(range) => setForm((f) => ({ ...f, default_budget: { ...f.default_budget, [mealType]: range } }))}
                  />
                ))}
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? "保存中..." : "保存档案"}
            </button>
          </form>
        </div>
      )}
    </section>
  );
}

function ContactCard({ contact, onEdit, onDelete, disabled }) {
  const lunchBudget = contact.default_budget?.lunch || [15, 30];
  const initial = contact.name?.[0] || "?";
  const colors = ["bg-emerald-100 text-emerald-700", "bg-blue-100 text-blue-700", "bg-violet-100 text-violet-700", "bg-pink-100 text-pink-700"];
  const colorIdx = contact.name?.charCodeAt(0) % colors.length || 0;

  return (
    <div className="page-panel transition-all hover:border-slate-300">
      <div className="flex items-start gap-4">
        <div className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full text-xl font-bold ${colors[colorIdx]}`}>
          {initial}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold text-slate-800">{contact.name}</h3>
              <p className="mt-0.5 text-sm text-slate-500 truncate">
                {contact.taste_description || listToText(contact.taste_tags) || "口味未填写"}
              </p>
            </div>
            <div className="flex flex-shrink-0 gap-1.5">
              <button type="button" disabled={disabled} onClick={onEdit} className="btn-secondary py-1 px-3 text-xs">
                编辑
              </button>
              <button type="button" disabled={disabled} onClick={onDelete} className="rounded-lg border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-600 transition hover:bg-red-100 disabled:opacity-50">
                删除
              </button>
            </div>
          </div>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {listToText(contact.avoid_ingredients) && (
              <span className="rounded-full bg-red-50 px-2 py-0.5 text-red-600">
                忌：{listToText(contact.avoid_ingredients)}
              </span>
            )}
            <span className="rounded-full bg-orange-50 px-2 py-0.5 text-mealmate-orange font-medium">
              午餐 ¥{lunchBudget[0]}–{lunchBudget[1]}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function TextField({ label, value, onChange, placeholder }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input-base" />
    </label>
  );
}

function listToText(value) {
  return Array.isArray(value) ? value.join("，") : "";
}

function textToList(value) {
  return String(value || "").replace(/，/g, ",").split(",").map((s) => s.trim()).filter(Boolean);
}

export default Contacts;
