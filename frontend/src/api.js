// All backend calls live here. Change endpoints in this one file.
const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const STATUSES = ["arrested", "remand", "chargesheet_filed", "trial",
  "convicted", "acquitted", "custody", "released"];

// Which roles may do what (mirrors backend require_role; admin can do everything)
export const can = {
  arrest: (r) => ["police", "admin"].includes(r),
  fir: (r) => ["police", "admin"].includes(r),
  advance: (r) => ["police", "court", "custody", "admin"].includes(r),
};

const getToken = () => localStorage.getItem("token");

async function req(path, { method = "GET", json, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let body;
  if (json) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  const res = await fetch(BASE + path, { method, headers, body });
  if (res.status === 401 && path !== "/auth/login") {
    localStorage.clear();
    window.location.reload();
  }
  if (!res.ok) {
    let msg = res.statusText;
    try { const d = await res.json(); msg = typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail); } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  login: (username, password) => req("/auth/login", { method: "POST", json: { username, password } }),
  summary: () => req("/dashboard/summary"),
  suspects: () => req("/suspects"),
  createSuspect: (name, alias, photo) => {
    const f = new FormData();
    f.append("name", name);
    if (alias) f.append("alias", alias);
    f.append("photo", photo);
    return req("/suspects", { method: "POST", form: f });
  },
  updateStatus: (id, status, notes) =>
    req(`/suspects/${id}/status`, { method: "PATCH", json: { status, notes: notes || null } }),
  cases: () => req("/cases"),
  createCase: (data) => req("/cases", { method: "POST", json: data }),
};
