import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { ArrowRight, Brain, CheckCircle2, History, Sparkles, ShieldAlert, X, BookOpen, RotateCcw } from "lucide-react";
import "./style.css";

const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

const FIRST_INCIDENT = {
  title: "Checkout API returning HTTP 503",
  customer: "Acme Retail",
  severity: "Critical",
  symptoms: "Checkout requests are failing intermittently. Database connection utilization is at 96%.",
  context: "Enterprise customer. Renewal discussion in 18 days. Payment reliability is critical."
};

const SECOND_INCIDENT = {
  title: "Checkout API degradation during peak traffic",
  customer: "Acme Retail",
  severity: "Critical",
  symptoms: "Checkout latency increased sharply. Database connection utilization is at 94%. Some payment requests are timing out.",
  context: "Enterprise customer with renewal discussion in 18 days. Payment reliability is critical to the account."
};

function App() {
  const [incident, setIncident] = useState(FIRST_INCIDENT);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [learned, setLearned] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [library, setLibrary] = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [outcome, setOutcome] = useState({ resolution: "", result: "", business_outcome: "" });
  const [message, setMessage] = useState("");
  const [backendOnline, setBackendOnline] = useState(true);

  const memoryCount = data?.memories?.length || 0;
  const confidence = Math.round((data?.decision?.confidence ?? 0.9) * 100);

  async function analyze() {
    setLoading(true);
    setLearned(false);
    setMessage("");
    try {
      const r = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(incident),
      });
      if (!r.ok) throw new Error(await r.text());
      const result = await r.json();
      setData(result);
      setBackendOnline(true);
      setOutcome({ resolution: "", result: "", business_outcome: "" });
    } catch (e) {
      setBackendOnline(false);
      setMessage(`NEXUS backend is unavailable. Start the FastAPI server and try again. ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function teach() {
    if (!outcome.resolution.trim() || !outcome.result.trim() || !outcome.business_outcome.trim()) {
      setMessage("Fill all three outcome fields before teaching NEXUS.");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      const r = await fetch(`${API}/api/learn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          incident_title: incident.title,
          customer: incident.customer,
          resolution: outcome.resolution,
          result: outcome.result,
          business_outcome: outcome.business_outcome,
          successful: true,
        }),
      });
      const result = await r.json();
      if (!r.ok || !result.stored) throw new Error(result.detail || result.message || "Could not retain experience");
      setLearned(true);
      setMessage("Experience saved. NEXUS can use it for future incidents.");
    } catch (e) {
      setMessage(`Could not save experience: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function openLibrary() {
    setLibraryOpen(true);
    setLibraryLoading(true);
    try {
      const r = await fetch(`${API}/api/experiences`);
      const result = await r.json();
      if (!r.ok || result.error) throw new Error(result.detail || result.error || "Could not load experiences");
      setLibrary(result.experiences || []);
    } catch (e) {
      setLibrary([]);
      setMessage(`Experience Library error: ${e.message}`);
    } finally {
      setLibraryLoading(false);
    }
  }

  function loadSecondIncident() {
    setIncident(SECOND_INCIDENT);
    setData(null);
    setLearned(false);
    setOutcome({ resolution: "", result: "", business_outcome: "" });
    setMessage("Next incident loaded. Analyze it to see NEXUS use previous experience.");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetDemo() {
    setIncident(FIRST_INCIDENT);
    setData(null);
    setLearned(false);
    setOutcome({ resolution: "", result: "", business_outcome: "" });
    setMessage("Demo reset. Ready for the first problem.");
  }

  const memoryStatus = data?.memory_status;
  const recalled = useMemo(() => {
    const seen = new Set();
    return (data?.memories || []).filter((m) => {
      const k = (m.text || "").replace(/\s+/g, " ").trim().toLowerCase();
      if (!k || seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }, [data]);

  return (
    <>
      <style>{`
        .demo-flow{display:flex;align-items:center;gap:9px;margin:0 0 16px;padding:12px 14px;background:rgba(18,23,33,.72);border:1px solid rgba(255,255,255,.07);border-radius:11px;color:#596273;overflow:auto}
        .flow-step{display:flex;align-items:center;gap:7px;white-space:nowrap;padding:7px 9px;border-radius:7px;font-size:9px;letter-spacing:.08em}
        .flow-step span{font-size:8px;color:#596273;border:1px solid rgba(255,255,255,.08);border-radius:5px;padding:3px 5px}
        .flow-step.active{background:rgba(114,126,245,.08);color:#c8d0ff}
        .flow-step.active span{color:#c8d0ff;border-color:rgba(126,145,255,.25)}
        .demo-flow>svg{flex:none;color:#4d5666}
        .section-intro,.decision-intro{font-size:11px;line-height:1.5;color:#7f8999;margin:-6px 0 12px}
        .decision-intro{margin:-8px 0 15px}
      `}</style>
      <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo"><Brain size={22} /></div>
          <div><b>NEXUS</b><small>ORGANIZATIONAL MEMORY</small></div>
        </div>
        <nav>
          <button className="navbtn active"><ShieldAlert size={17} /> New Incident</button>
          <button className="navbtn" onClick={openLibrary}><BookOpen size={17} /> Experience Library</button>
        </nav>
        <div className="tagline">Every incident becomes experience.<br /><strong>Every experience improves the next decision.</strong></div>
        <div className="side-actions">
          <button onClick={loadSecondIncident}><Sparkles size={15} /> Load Demo Incident 2</button>
          <button onClick={resetDemo}><RotateCcw size={15} /> Reset Demo View</button>
        </div>
      </aside>

      <main>
        <header>
          <div>
            <p className="eyebrow">DECISION WORKSPACE</p>
            <h1>Incident Intelligence</h1>
            <p className="sub">NEXUS helps your team remember what happened before, decide what to do now, and learn from the outcome.</p>
          </div>
          <div className={`status ${backendOnline ? "" : "offline"}`}><i /> {backendOnline ? "MEMORY ONLINE" : "BACKEND OFFLINE"}</div>
        </header>

        <div className="demo-flow" aria-label="NEXUS learning flow">
          <div className="flow-step active"><span>01</span><b>A PROBLEM HAPPENS</b></div>
          <ArrowRight size={15} />
          <div className={`flow-step ${data ? "active" : ""}`}><span>02</span><b>NEXUS REMEMBERS</b></div>
          <ArrowRight size={15} />
          <div className={`flow-step ${data ? "active" : ""}`}><span>03</span><b>NEXUS HELPS DECIDE</b></div>
          <ArrowRight size={15} />
          <div className={`flow-step ${learned ? "active" : ""}`}><span>04</span><b>NEXUS LEARNS</b></div>
        </div>

        {message && <div className="toast">{message}</div>}

        <section className="grid">
          <div className="panel incident">
            <div className="panelhead"><span>01 / A PROBLEM HAPPENS</span><b>LIVE</b></div>
            <div className="section-intro">A customer problem happens. Tell NEXUS what is going on.</div>
            <label>WHAT IS HAPPENING?</label>
            <input value={incident.title} onChange={e => setIncident({ ...incident, title: e.target.value })} />
            <div className="two">
              <div><label>CUSTOMER</label><input value={incident.customer} onChange={e => setIncident({ ...incident, customer: e.target.value })} /></div>
              <div><label>SEVERITY</label><select value={incident.severity} onChange={e => setIncident({ ...incident, severity: e.target.value })}><option>Critical</option><option>High</option><option>Medium</option></select></div>
            </div>
            <label>WHAT ARE PEOPLE SEEING?</label>
            <textarea value={incident.symptoms} onChange={e => setIncident({ ...incident, symptoms: e.target.value })} />
            <label>WHY DOES IT MATTER?</label>
            <textarea value={incident.context} onChange={e => setIncident({ ...incident, context: e.target.value })} />
            <button className="primary" onClick={analyze} disabled={loading}>{loading ? "LOOKING AT WHAT HAPPENED..." : "ANALYZE WITH NEXUS"} <ArrowRight size={17} /></button>
          </div>

          <div className="panel memory-panel">
            <div className="panelhead"><span>02 / NEXUS REMEMBERS</span><span className="count">{memoryCount} EXPERIENCES FOUND</span></div>
            {!data ? <div className="empty"><Brain size={34} /><h3>NEXUS is ready to remember</h3><p>When you analyze the problem, NEXUS looks through previous company experiences for situations that can help.</p></div> : <>
              <div className="memory-state">{memoryStatus === "unavailable" ? "MEMORY COULD NOT BE REACHED — safe decision shown" : memoryStatus === "empty" ? "No matching previous experience was found" : `NEXUS FOUND ${memoryCount} RELEVANT EXPERIENCE${memoryCount === 1 ? "" : "S"}`}</div>
              <div className="memories">{recalled.map((m, i) => <div className="memory" key={i}><div className="micon"><History size={14} /></div><div><small>{m.type?.toUpperCase() || "EXPERIENCE"}</small><p>{m.text}</p></div></div>)}</div>
            </>}
          </div>
        </section>

        {data && <section className="decision">
          <div className="panel mainrec">
            <div className="panelhead"><span>03 / NEXUS HELPS DECIDE</span><span className="confidence"><Sparkles size={14} /> {confidence}% CONFIDENCE</span></div>
            <div className="decision-intro">Using what the company has experienced before, NEXUS suggests a practical next step.</div>
            <h2>{data.decision.recommendation}</h2>
            <div className="why"><b>WHY THIS SUGGESTION?</b><p>{data.decision.why}</p></div>
            <div className="cards">
              <div><b>WHAT TO AVOID</b><p>{data.decision.avoid}</p></div>
              <div><b>WHY THE CUSTOMER MATTERS</b><p>{data.decision.customer_context}</p></div>
            </div>

            {!learned ? <div className="outcome-box">
              <div className="outcome-title"><Sparkles size={16} /> 04 / WHAT ACTUALLY HAPPENED?</div>
              <p>Don't just ask AI what might work. Tell NEXUS what really happened so the company can remember the experience.</p>
              <label>WHAT DID THE TEAM DO?</label>
              <textarea placeholder="e.g. Reduced DB connection pool from 100 to 60 and restarted checkout workers." value={outcome.resolution} onChange={e => setOutcome({ ...outcome, resolution: e.target.value })} />
              <label>WHAT WAS THE RESULT?</label>
              <textarea placeholder="e.g. Checkout recovered and HTTP 503 errors stopped." value={outcome.result} onChange={e => setOutcome({ ...outcome, result: e.target.value })} />
              <label>WHAT HAPPENED FOR THE CUSTOMER?</label>
              <textarea placeholder="e.g. Customer was proactively informed. No escalation occurred and renewal remained on track." value={outcome.business_outcome} onChange={e => setOutcome({ ...outcome, business_outcome: e.target.value })} />
              <button className="learn" onClick={teach} disabled={loading}>{loading ? "SAVING EXPERIENCE..." : "SAVE THIS EXPERIENCE"} <Sparkles size={17} /></button>
            </div> : <div className="learned"><CheckCircle2 size={21} /><div><b>EXPERIENCE SAVED</b><span>{message || "NEXUS can now use what happened in future incidents."}</span></div></div>}
          </div>

          <div className="panel learning">
            <div className="panelhead"><span>05 / NEXUS LEARNS</span></div>
            <div className="loop"><div>PROBLEM</div><ArrowRight /><div>REMEMBER</div><ArrowRight /><div>DECIDE</div><ArrowRight /><div className={learned ? "on" : ""}>OUTCOME</div><ArrowRight /><div className={learned ? "on" : ""}>EXPERIENCE</div></div>
            <p>{learned ? "This real outcome is now part of the organization's memory and can help with future problems." : "Record what actually happened to turn this problem into reusable company experience."}</p>
          </div>
        </section>}

        {learned && <button className="next-incident" onClick={loadSecondIncident}>SEE HOW NEXUS USES IT NEXT <ArrowRight size={17} /></button>}
      </main>

      {libraryOpen && <div className="overlay" onClick={() => setLibraryOpen(false)}>
        <div className="library" onClick={e => e.stopPropagation()}>
          <div className="library-head"><div><p className="eyebrow">ORGANIZATIONAL MEMORY</p><h2>Experience Library</h2><p>Past experiences NEXUS can use to help with future problems.</p></div><button className="close" onClick={() => setLibraryOpen(false)}><X /></button></div>
          {libraryLoading ? <div className="empty">Loading company experiences...</div> : <div className="library-list">
            {library.map((m, i) => <div className="library-item" key={i}><span>{String(i + 1).padStart(2, "0")}</span><div><small>{m.type?.toUpperCase() || "EXPERIENCE"}</small><p>{m.text}</p></div></div>)}
            {!library.length && <div className="empty">No experiences found yet.</div>}
          </div>}
        </div>
      </div>}
      </div>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);

