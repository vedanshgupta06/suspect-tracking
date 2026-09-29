import { useEffect, useState } from "react";
import { api, can, STATUSES } from "./api.js";

const label = (s) => (s || "unknown").replace(/_/g, " ");
const pct = (x) => `${(x * 100).toFixed(1)}%`;

function Login({ onLogin }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const r = await api.login(u, p);
      localStorage.setItem("token", r.token);
      localStorage.setItem("role", r.role);
      localStorage.setItem("name", r.full_name);
      onLogin({ role: r.role, name: r.full_name });
    } catch (e2) { setErr(e2.message); }
  };
  return (
    <form className="card login" onSubmit={submit}>
      <h1>Suspect Tracking</h1>
      <input placeholder="Username" value={u} onChange={(e) => setU(e.target.value)} />
      <input placeholder="Password" type="password" value={p} onChange={(e) => setP(e.target.value)} />
      {err && <p className="err">{err}</p>}
      <button>Sign in</button>
    </form>
  );
}

function Dashboard() {
  const [s, setS] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.summary().then(setS).catch((e) => setErr(e.message)); }, []);
  if (err) return <p className="err">{err}</p>;
  if (!s) return <p>Loading…</p>;
  return (
    <>
      <div className="stats">
        <div className="card stat"><b>{s.total_suspects}</b>Suspects</div>
        <div className="card stat"><b>{s.total_cases}</b>Cases</div>
        <div className="card stat"><b>{s.unsolved_cases}</b>Unsolved</div>
        <div className="card stat"><b>{s.recent_case_links}</b>Case links</div>
      </div>
      <div className="card">
        <h3>Suspects by status</h3>
        {Object.entries(s.suspects_by_status).map(([k, v]) => (
          <div key={k} className="row"><span>{label(k)}</span><b>{v}</b></div>
        ))}
      </div>
    </>
  );
}

function Arrest() {
  const [name, setName] = useState("");
  const [alias, setAlias] = useState("");
  const [photo, setPhoto] = useState(null);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setRes(null); setBusy(true);
    try { setRes(await api.createSuspect(name, alias, photo)); setName(""); setAlias(""); setPhoto(null); e.target.reset(); }
    catch (e2) { setErr(e2.message); }
    setBusy(false);
  };
  return (
    <>
      <form className="card" onSubmit={submit}>
        <h3>Arrest entry</h3>
        <input placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input placeholder="Alias (optional)" value={alias} onChange={(e) => setAlias(e.target.value)} />
        <input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files[0])} required />
        {err && <p className="err">{err}</p>}
        <button disabled={busy}>{busy ? "Matching faces…" : "Register suspect"}</button>
      </form>
      {res && (
        <div className="card">
          <h3>Registered: {res.suspect.name} (#{res.suspect.id})</h3>
          <h4>Possible alias / repeat-offender matches</h4>
          {res.alias_candidates.length === 0 && <p>No candidates found.</p>}
          {res.alias_candidates.map((c) => (
            <div key={c.suspect_id} className={`row ${c.is_match ? "hit" : ""}`}>
              <span>#{c.suspect_id} {c.name}{c.alias ? ` (${c.alias})` : ""}</span>
              <span>{pct(c.score)} {c.is_match && <em className="tag">likely match</em>}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function Fir() {
  const [f, setF] = useState({ fir_number: "", mo_text: "", location: "", suspect_id: "" });
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setRes(null);
    try {
      setRes(await api.createCase({
        fir_number: f.fir_number, mo_text: f.mo_text,
        location: f.location || null,
        suspect_id: f.suspect_id ? Number(f.suspect_id) : null,
      }));
      setF({ fir_number: "", mo_text: "", location: "", suspect_id: "" });
    } catch (e2) { setErr(e2.message); }
  };
  return (
    <>
      <form className="card" onSubmit={submit}>
        <h3>File FIR</h3>
        <input placeholder="FIR number" value={f.fir_number} onChange={set("fir_number")} required />
        <textarea placeholder="Modus operandi / narrative" rows={5} value={f.mo_text} onChange={set("mo_text")} required />
        <input placeholder="Location (optional)" value={f.location} onChange={set("location")} />
        <input placeholder="Suspect ID (optional)" type="number" value={f.suspect_id} onChange={set("suspect_id")} />
        {err && <p className="err">{err}</p>}
        <button>File FIR</button>
      </form>
      {res && (
        <div className="card">
          <h3>Filed {res.case.fir_number} — status: {res.case.status}</h3>
          <h4>Linked-case suggestions</h4>
          {res.linked_cases.length === 0 && <p>No similar cases found.</p>}
          {res.linked_cases.map((c) => (
            <div key={c.case_id} className={`row ${c.is_link ? "hit" : ""}`}>
              <span>{c.fir_number}</span>
              <span>{pct(c.score)} {c.is_link && <em className="tag">likely link</em>}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function Suspects({ role }) {
  const [list, setList] = useState([]);
  const [err, setErr] = useState("");
  const load = () => api.suspects().then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  const advance = async (s, status) => {
    try { await api.updateStatus(s.id, status); load(); } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card">
      <h3>Suspects</h3>
      {err && <p className="err">{err}</p>}
      {list.map((s) => {
        const i = STATUSES.indexOf(s.current_status);
        const next = i >= 0 && i < STATUSES.length - 1 ? STATUSES[i + 1] : null;
        return (
          <div key={s.id} className="row">
            <span>#{s.id} {s.name}{s.alias ? ` (${s.alias})` : ""}</span>
            <span>
              <em className="tag">{label(s.current_status)}</em>{" "}
              {can.advance(role) && (
                <select value="" onChange={(e) => e.target.value && advance(s, e.target.value)}>
                  <option value="">{next ? `Next: ${label(next)}` : "Set status…"}</option>
                  {STATUSES.map((st) => <option key={st} value={st}>{label(st)}</option>)}
                </select>
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(() =>
    localStorage.getItem("token")
      ? { role: localStorage.getItem("role"), name: localStorage.getItem("name") } : null);
  const [tab, setTab] = useState("dashboard");
  if (!user) return <Login onLogin={setUser} />;
  const tabs = [
    ["dashboard", "Dashboard", true],
    ["suspects", "Suspects", true],
    ["arrest", "Arrest entry", can.arrest(user.role)],
    ["fir", "File FIR", can.fir(user.role)],
  ].filter((t) => t[2]);
  return (
    <div className="app">
      <header>
        <nav>
          {tabs.map(([k, l]) => (
            <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>
          ))}
        </nav>
        <span>{user.name} · {user.role}{" "}
          <button onClick={() => { localStorage.clear(); setUser(null); }}>Logout</button>
        </span>
      </header>
      <main>
        {tab === "dashboard" && <Dashboard />}
        {tab === "suspects" && <Suspects role={user.role} />}
        {tab === "arrest" && <Arrest />}
        {tab === "fir" && <Fir />}
      </main>
    </div>
  );
}
