/* eslint-disable */
/* Panel Time Predictor — clean sidebar layout */
const { useState: useStateE, useEffect: useEffectE, useRef: useRefE, useCallback } = React;

/* ============================================================
 * ICONS
 * ============================================================ */
const stroke = "1.5";
const Svg = ({ size = 18, className = "", children }) =>
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" className={className}>{children}</svg>;

const I = {
  Calculator: (p) => <Svg {...p}><rect x="4" y="2" width="16" height="20" rx="2" /><line x1="8" x2="16" y1="6" y2="6" /><line x1="16" x2="16" y1="14" y2="18" /><path d="M16 10h.01M12 10h.01M8 10h.01M12 14h.01M8 14h.01M12 18h.01M8 18h.01" /></Svg>,
  Cpu: (p) => <Svg {...p}><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2" /></Svg>,
  History: (p) => <Svg {...p}><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l4 2" /></Svg>,
  Server: (p) => <Svg {...p}><rect width="20" height="8" x="2" y="2" rx="2" /><rect width="20" height="8" x="2" y="14" rx="2" /><line x1="6" x2="6.01" y1="6" y2="6" /><line x1="6" x2="6.01" y1="18" y2="18" /></Svg>,
  Brain: (p) => <Svg {...p}><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 0 0 12 21z" /><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 0 1 12 21" /><path d="M12 5v16" /></Svg>,
  CircleCheck: (p) => <Svg {...p}><circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" /></Svg>,
  CircleAlert: (p) => <Svg {...p}><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></Svg>,
  Loader: (p) => <Svg {...p} className={"animate-spin " + (p.className || "")}><path d="M21 12a9 9 0 1 1-6.219-8.56" /></Svg>,
  BadgeCheck: (p) => <Svg {...p}><path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" /><path d="m9 12 2 2 4-4" /></Svg>,
  Shield: (p) => <Svg {...p}><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" /><path d="M12 8v4" /><path d="M12 16h.01" /></Svg>,
  Octagon: (p) => <Svg {...p}><path d="M2.586 16.726A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2h6.624a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586z" /><path d="M12 8v4" /><path d="M12 16h.01" /></Svg>,
  Refresh: (p) => <Svg {...p}><path d="M21 12a9 9 0 1 1-3-6.7" /><path d="M21 4v5h-5" /></Svg>,
  Clock: (p) => <Svg {...p}><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></Svg>,
  Calendar: (p) => <Svg {...p}><rect width="18" height="18" x="3" y="4" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></Svg>,
  ChevDown: (p) => <Svg {...p}><path d="m6 9 6 6 6-6" /></Svg>,
  ArrowRight: (p) => <Svg {...p}><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></Svg>,
  Layers: (p) => <Svg {...p}><path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.84z" /><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12" /><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17" /></Svg>,
  Activity: (p) => <Svg {...p}><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.5.5 0 0 1-.96 0L9.68 2.18a.5.5 0 0 0-.96 0l-2.35 8.36A2 2 0 0 1 4.45 12H2" /></Svg>,
  Plus: (p) => <Svg {...p}><path d="M12 5v14M5 12h14" /></Svg>,
  Minus: (p) => <Svg {...p}><path d="M5 12h14" /></Svg>,
  FileUp: (p) => <Svg {...p}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="M12 12v6" /><path d="m9 15 3-3 3 3" /></Svg>,
  FileText: (p) => <Svg {...p}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" /></Svg>,
  FileSearch: (p) => <Svg {...p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><circle cx="11.5" cy="14.5" r="2.5" /><path d="M13.27 16.27 15 18" /></Svg>,
  X: (p) => <Svg {...p}><path d="M18 6 6 18M6 6l12 12" /></Svg>,
  CircleX: (p) => <Svg {...p}><circle cx="12" cy="12" r="10" /><path d="m15 9-6 6" /><path d="m9 9 6 6" /></Svg>,
  ChevUp: (p) => <Svg {...p}><path d="m18 15-6-6-6 6" /></Svg>,
  Copy: (p) => <Svg {...p}><rect width="14" height="14" x="8" y="8" rx="2" /><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" /></Svg>,
  RotateCcw: (p) => <Svg {...p}><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></Svg>,
  Merge: (p) => <Svg {...p}><circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M6 21V9a9 9 0 0 0 9 9" /></Svg>,
  HelpCircle: (p) => <Svg {...p}><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><path d="M12 17h.01" /></Svg>,
  Info: (p) => <Svg {...p}><circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" /></Svg>,
  Gauge: (p) => <Svg {...p}><path d="m12 14 4-4" /><path d="M3.34 19a10 10 0 1 1 17.32 0" /></Svg>,
  Play: (p) => <Svg {...p}><polygon points="6 3 20 12 6 21 6 3" /></Svg>,
  User: (p) => <Svg {...p}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></Svg>,
  BarChart: (p) => <Svg {...p}><line x1="12" x2="12" y1="20" y2="10" /><line x1="18" x2="18" y1="20" y2="4" /><line x1="6" x2="6" y1="20" y2="16" /></Svg>,
  TrendingDown: (p) => <Svg {...p}><polyline points="22 17 13.5 8.5 8.5 13.5 2 7" /><polyline points="16 17 22 17 22 11" /></Svg>,
  List: (p) => <Svg {...p}><line x1="8" x2="21" y1="6" y2="6" /><line x1="8" x2="21" y1="12" y2="12" /><line x1="8" x2="21" y1="18" y2="18" /><line x1="3" x2="3.01" y1="6" y2="6" /><line x1="3" x2="3.01" y1="12" y2="12" /><line x1="3" x2="3.01" y1="18" y2="18" /></Svg>
};

/* ============================================================
 * HELPERS
 * ============================================================ */
const E_DEFAULT_SERVER = "http://127.0.0.1:8000";

function eFormatSeconds(s) {
  if (s == null || isNaN(s)) return "—";
  const total = Math.max(0, Math.round(Number(s)));
  const h = Math.floor(total / 3600);
  const m = Math.floor(total % 3600 / 60);
  const sec = total % 60;
  const pad = (n) => String(n).padStart(2, "0");
  if (h > 0) return `${h}h ${pad(m)}m ${pad(sec)}s`;
  if (m > 0) return `${m}m ${pad(sec)}s`;
  return `${sec}s`;
}
function eFormatAbs(ts) {
  if (!ts) return "—";
  const d = typeof ts === "number" ? new Date(ts * (ts < 1e12 ? 1000 : 1)) : new Date(ts);
  if (!d.getTime()) return "—";
  const Y = d.getFullYear();
  const M = String(d.getMonth() + 1).padStart(2, "0");
  const D = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const mn = String(d.getMinutes()).padStart(2, "0");
  return `${Y}-${M}-${D} ${h}:${mn}`;
}
function eTimeAgo(ts) {
  if (!ts) return "";
  const t = typeof ts === "number" ? ts * (ts < 1e12 ? 1000 : 1) : new Date(ts).getTime();
  if (!t) return "";
  const diff = (Date.now() - t) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  const d = Math.floor(diff / 86400);
  if (d < 30) return `${d}d ago`;
  const mo = Math.floor(d / 30);
  if (mo < 12) return `${mo}mo ago`;
  return `${Math.floor(d / 365)}y ago`;
}

function eGetApiKey() {
  try { return (localStorage.getItem("blufab_api_key") || "").trim(); } catch { return ""; }
}
function eSetApiKey(v) {
  try { v ? localStorage.setItem("blufab_api_key", v.trim()) : localStorage.removeItem("blufab_api_key"); } catch {}
}

async function eApi(base, path, opts = {}) {
  const url = base.replace(/\/+$/, "") + path;
  const key = eGetApiKey();
  const headers = {
    "ngrok-skip-browser-warning": "true",
    ...(key ? { "X-API-Key": key } : {}),
    ...(opts.body ? { "Content-Type": "application/json" } : {}),
    ...(opts.headers || {})
  };
  const res = await fetch(url, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
  const text = await res.text();
  let data = null;try {data = text ? JSON.parse(text) : null;} catch {data = text;}
  if (!res.ok) {
    const err = new Error(data && data.detail || typeof data === "string" && data || `HTTP ${res.status}`);
    err.status = res.status;err.data = data;throw err;
  }
  return data;
}
function eErrorMessage(e, ctx) {
  if (!e) return "Unknown error.";
  if (ctx === "predict-pdf") {
    if (e.status === 415) return "That file isn't a PDF. Drop a .pdf here.";
    if (e.status === 422) return "Couldn't read panel geometry from this PDF. New project? Set GEMINI_API_KEY for live extraction (cached projects work offline).";
    if (e.status === 404) return (e.data && e.data.detail) ? String(e.data.detail) : "Panel not found in cache yet.";
  }
  if (e.status === 404 && ctx === "predict") return "Production order not found. Verify the identifier.";
  if (e.status === 404) return "Resource not found.";
  if (e.status === 422) return "Invalid parameters. Review the form and resubmit.";
  if (e.status >= 500) return "Upstream service error. Retry shortly.";
  if (e.message && /failed to fetch|networkerror|load failed/i.test(e.message))
  return "Cannot reach server. Verify address and connectivity.";
  return e.message ? String(e.message) : "Request failed.";
}

async function eApiMultipart(base, path, formData) {
  const url = base.replace(/\/+$/, "") + path;
  const key = eGetApiKey();
  const res = await fetch(url, {
    method: "POST",
    headers: { "ngrok-skip-browser-warning": "true", ...(key ? { "X-API-Key": key } : {}) },
    body: formData
  });
  const text = await res.text();
  let data = null; try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const err = new Error((data && data.detail) || (typeof data === "string" && data) || `HTTP ${res.status}`);
    err.status = res.status; err.data = data; throw err;
  }
  return data;
}

function eShortError(e, ctx) {
  if (!e) return "Error";
  if (ctx === "pdf") {
    if (e.status === 415) return "File not a PDF";
    if (e.status === 422) return "No geometry extracted";
    if (e.status === 404) {
      const d = e.data && e.data.detail;
      if (d && /not found/i.test(String(d))) return "Order not in database";
      return "Order not in database";
    }
  }
  if (e.status === 404) return "Order not in database";
  if (e.status === 422) return "Invalid parameters";
  if (e.status >= 500) return "Server error";
  if (e.message && /failed to fetch|networkerror|load failed/i.test(e.message)) return "Network error";
  return "Request failed";
}

function eRid() {
  return Math.random().toString(36).slice(2, 10);
}

function eParseKeyList(text) {
  return text.split(/[,\n\r\t;]+/).map((s) => s.trim()).filter(Boolean);
}

function eCsvEscape(s) {
  const str = String(s == null ? "" : s);
  return /[",\n]/.test(str) ? '"' + str.replace(/"/g, '""') + '"' : str;
}

function eExtractOpFromFilename(name) {
  if (!name) return null;
  const m = String(name).match(/OP[-_\s]?(\d{4})[-_\s]?(\d{3,})/i);
  return m ? "OP-" + m[1] + "-" + m[2] : null;
}

function eNormalizeKey(k) {
  return String(k || "").trim().toUpperCase();
}

function eDownloadFile(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}

function eExportCsv(items) {
  eDownloadFile(eBuildBatchCsv(items), "blufab-estimate.csv", "text/csv;charset=utf-8;");
}

function eExportPdf(items) {
  const JsPDF = window.jspdf && window.jspdf.jsPDF;
  if (!JsPDF) { alert("PDF library not loaded — check your connection and retry."); return; }
  const doc = new JsPDF({ unit: "pt", format: "a4" });
  const M = 40; let y = M;
  doc.setFontSize(15); doc.setTextColor(20, 20, 20);
  doc.text("BluFab — Production time estimate", M, y); y += 16;
  doc.setFontSize(9); doc.setTextColor(130, 130, 130);
  doc.text(new Date().toLocaleString(), M, y); y += 14;
  const success = items.filter(it => it.state === "success" && it.result);
  for (const it of success) {
    const label = (it.result.key || it.label || "order");
    const total = eFormatSeconds(eItemTotalSec(it));
    if (y > 740) { doc.addPage(); y = M; }
    doc.setFontSize(11); doc.setTextColor(20, 20, 20);
    doc.text(`${label}   —   ${total}`, M, y);
    const preds = (it.result.predictions || []).slice().sort((a, b) => (a.op_order || 0) - (b.op_order || 0));
    const body = preds.map(p => [String(p.op_order ?? ""), String(p.op_id ?? ""), eFormatSeconds(p.predicted_duration_sec)]);
    doc.autoTable({
      startY: y + 8,
      head: [["#", "Operation", "Duration"]],
      body,
      styles: { fontSize: 9, cellPadding: 4 },
      headStyles: { fillColor: [37, 99, 235], textColor: 255 },
      columnStyles: { 0: { cellWidth: 36 }, 2: { halign: "right", cellWidth: 90 } },
      margin: { left: M, right: M },
      theme: "grid",
    });
    y = doc.lastAutoTable.finalY + 20;
  }
  doc.save("blufab-estimate.pdf");
}

function eBuildBatchCsv(items) {
  const rows = ["order,op_id,op_order,predicted_duration_sec"];
  for (const it of items) {
    if (it.state !== "success" || !it.result) continue;
    const order =
      it.result.key ||
      (it.result.extracted && it.result.extracted.op_producao) ||
      it.label ||
      "";
    const preds = (it.result.predictions || [])
      .slice()
      .sort((a, b) => (a.op_order || 0) - (b.op_order || 0));
    for (const p of preds) {
      rows.push(
        [
          eCsvEscape(order),
          eCsvEscape(p.op_id),
          eCsvEscape(p.op_order ?? ""),
          eCsvEscape(p.predicted_duration_sec ?? "")
        ].join(",")
      );
    }
  }
  return rows.join("\n");
}

function eParseScheduleTime(data) {
  if (!data) return null;
  const candidates = [
  data.next_run_utc, data.next_run_at, data.next_run, data.next, data.next_at,
  data.next_execution, data.next_execution_at, data.scheduled_at,
  data.fire_at, data.fireAt, data.timestamp, data.run_at, data.nextFireTime];

  for (const c of candidates) {
    if (c == null) continue;
    if (typeof c === "number") {const ms = c < 1e12 ? c * 1000 : c;if (ms > 0) return ms;}
    if (typeof c === "string") {const t = Date.parse(c);if (!isNaN(t)) return t;}
  }
  if (typeof data.next_run_in_sec === "number") return Date.now() + data.next_run_in_sec * 1000;
  if (typeof data.next_run_in === "number") return Date.now() + data.next_run_in * 1000;
  if (typeof data.seconds_until_next === "number") return Date.now() + data.seconds_until_next * 1000;
  return null;
}

/* ============================================================
 * PRIMITIVES
 * ============================================================ */
function Card({ children, className = "", padded = true }) {
  return (
    <div className={"bg-[var(--surface)] border border-[var(--border)] rounded-lg " + (padded ? "p-6 " : "") + className}>
      {children}
    </div>);

}

let _helpTipUid = 0;
function HelpTip({ text, label, size = 14, className = "" }) {
  const [open, setOpen] = useStateE(false);
  const [coords, setCoords] = useStateE(null);
  const btnRef = useRefE(null);
  const tipRef = useRefE(null);
  const idRef = useRefE("ht-" + (++_helpTipUid));

  function place() {
    if (!btnRef.current) return;
    const r = btnRef.current.getBoundingClientRect();
    setCoords({ top: r.bottom + 8, left: r.left + r.width / 2 });
  }
  function show() { place(); setOpen(true); }
  function hide() { setOpen(false); }

  useEffectE(() => {
    if (!open) return;
    function onKey(e) { if (e.key === "Escape") { hide(); btnRef.current && btnRef.current.focus(); } }
    function onScrollResize() { place(); }
    window.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onScrollResize, true);
    window.addEventListener("resize", onScrollResize);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onScrollResize, true);
      window.removeEventListener("resize", onScrollResize);
    };
  }, [open]);

  const ariaLabel = "Help: " + (label || "More information");
  return (
    <>
      <button
        ref={btnRef}
        type="button"
        aria-label={ariaLabel}
        aria-describedby={open ? idRef.current : undefined}
        aria-expanded={open}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        onClick={(e) => { e.preventDefault(); open ? hide() : show(); }}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open ? hide() : show(); } }}
        className={"inline-flex items-center justify-center rounded-full text-slate-400 hover:text-blue-400 focus:text-blue-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/50 transition-colors align-middle " + className}>
        <I.HelpCircle size={size} />
      </button>
      {open && coords && ReactDOM.createPortal(
        <div
          ref={tipRef}
          id={idRef.current}
          role="tooltip"
          style={{
            position: "fixed",
            top: coords.top + "px",
            left: coords.left + "px",
            transform: "translateX(-50%)",
            maxWidth: "20rem",
            zIndex: 1000
          }}
          className="rounded-lg border border-blue-100 bg-white shadow-lg p-3 text-[12.5px] leading-snug text-slate-700 pointer-events-none">
          {text}
        </div>,
        document.body
      )}
    </>
  );
}

function AboutPanel({ title = "About this page", body, className = "" }) {
  const [open, setOpen] = useStateE(false);
  return (
    <div className={"rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/40 overflow-hidden " + className}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full flex items-center gap-2.5 px-4 py-2.5 text-left hover:bg-[var(--surface-2)]/70 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]/40">
        <I.Info size={15} className="text-[var(--accent-hover)] shrink-0" />
        <span className="text-[13px] font-medium text-[var(--text)] flex-1">{title}</span>
        <I.ChevDown size={14} className={"text-[var(--text-faint)] transition-transform duration-150 " + (open ? "rotate-180" : "")} />
      </button>
      {open && (
        <div className="px-4 pt-3 pb-4 text-[13px] text-[var(--text-muted)] leading-relaxed border-t border-[var(--border-soft)]">
          {body}
        </div>
      )}
    </div>
  );
}

function PageHeader({ title, subtitle, action, tooltip, about }) {
  return (
    <div className="mb-6">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-[var(--text)] leading-tight inline-flex items-center gap-2">
            <span>{title}</span>
            {tooltip && <HelpTip text={tooltip} label={title} size={16} />}
          </h1>
          {subtitle && <p className="mt-1 text-[14px] text-[var(--text-muted)]">{subtitle}</p>}
        </div>
        {action}
      </div>
      {about && <AboutPanel title={"About this page"} body={about} className="mt-3" />}
    </div>);

}

function Button({ children, onClick, type = "button", disabled, loading, variant = "primary", icon, className = "", title, size = "md" }) {
  const sizes = { sm: "h-8 px-3 text-[13px]", md: "h-10 px-4 text-[14px]", lg: "h-11 px-5 text-[15px]" };
  const base = "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]/40 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap";
  const variants = {
    primary: "text-white bg-[var(--accent)] hover:bg-[var(--accent-hover)]",
    secondary: "text-[var(--text)] bg-[var(--surface-2)] hover:bg-[#222D45] border border-[var(--border)]",
    ghost: "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]",
    danger: "text-white bg-[var(--err)] hover:bg-[#DC2626]"
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled || loading} title={title}
    className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}>
      {loading ? <I.Loader size={16} /> : icon || null}
      <span>{children}</span>
    </button>);

}

function Input(props) {
  return (
    <input {...props}
    className={"h-10 px-3.5 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[14px] text-[var(--text)] placeholder:text-[var(--text-faint)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-colors w-full " + (props.className || "")} />);


}

function Field({ label, hint, error, children, className = "", tooltip }) {
  return (
    <div className={"flex flex-col gap-1.5 min-w-0 " + className}>
      <label className="text-[13px] font-medium text-[var(--text)] flex items-center gap-1.5 flex-wrap">
        <span>{label}</span>
        {tooltip && <HelpTip text={tooltip} label={label} />}
      </label>
      {children}
      {hint && !error && <span className="text-[12px] text-[var(--text-muted)]">{hint}</span>}
      {error && <span className="text-[12px] text-[var(--err)] flex items-center gap-1.5"><I.CircleAlert size={13} /> {error}</span>}
    </div>);

}

function Badge({ tone = "slate", icon, children, className = "" }) {
  const tones = {
    slate: "bg-[var(--surface-2)] text-[var(--text-muted)] border-[var(--border)]",
    blue: "bg-[var(--accent)]/10 text-[var(--accent-hover)] border-[var(--accent)]/30",
    ok: "bg-[var(--ok)]/10 text-[var(--ok)] border-[var(--ok)]/30",
    warn: "bg-[var(--warn)]/10 text-[var(--warn)] border-[var(--warn)]/30",
    err: "bg-[var(--err)]/10 text-[var(--err)] border-[var(--err)]/30"
  };
  return (
    <span className={"inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[12px] font-medium " + tones[tone] + " " + className}>
      {icon}{children}
    </span>);

}

function Toggle({ checked, onChange, srLabel }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={srLabel}
    onClick={() => onChange(!checked)}
    className={"relative inline-flex h-6 w-11 shrink-0 rounded-full border transition-colors duration-150 " + (
    checked ?
    "bg-[var(--accent)] border-[var(--accent)]" :
    "bg-[var(--surface-2)] border-[var(--border)]")}>
      <span className={"absolute top-1 left-1 h-4 w-4 rounded-full bg-white shadow transition-transform duration-150 " + (
      checked ? "translate-x-[18px]" : "translate-x-0")} />
    </button>);

}

function ToggleRow({ title, hint, checked, onChange, tooltip }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="text-[14px] text-[var(--text)] inline-flex items-center gap-1.5">
          <span>{title}</span>
          {tooltip && <HelpTip text={tooltip} label={title} />}
        </div>
        {hint && <div className="text-[12.5px] text-[var(--text-muted)] mt-0.5">{hint}</div>}
      </div>
      <Toggle checked={checked} onChange={onChange} srLabel={title} />
    </div>);

}

function ProgressBar({ value }) {
  const v = Math.max(0, Math.min(100, value || 0));
  return (
    <div className="h-1.5 w-full rounded-full bg-[var(--surface-2)] overflow-hidden">
      <div className="h-full bg-[var(--accent)] transition-[width] duration-500 ease-linear rounded-full" style={{ width: v + "%" }} />
    </div>);

}

function InlineError({ message }) {
  if (!message) return null;
  return (
    <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-md bg-[var(--err)]/8 border border-[var(--err)]/20 text-[13px] text-[var(--err)]">
      <I.CircleAlert size={15} className="mt-0.5 shrink-0" />
      <span className="text-[var(--text)]">{message}</span>
    </div>);

}

function StatusDot({ tone }) {
  const colors = { ok: "var(--ok)", warn: "var(--warn)", err: "var(--err)", slate: "var(--text-faint)" };
  return <span className="inline-block h-2 w-2 rounded-full shrink-0" style={{ background: colors[tone] || colors.slate, boxShadow: "0 0 8px " + (colors[tone] || "transparent") }} />;
}

/* ============================================================
 * SIDEBAR
 * ============================================================ */
const NAV = [
{ id: "dashboard", label: "Live Dashboard", subtitle: "Shop-floor production view (demo · simulated data).", Icon: I.Gauge },
{ id: "predict", label: "Predictor", subtitle: "Predict per-operation durations for an order.", Icon: I.Calculator },
{ id: "metrics", label: "Model Metrics", subtitle: "How accuracy improves as data grows.", Icon: I.Activity },
{ id: "retrain", label: "Training", subtitle: "Refit the deployed model on the latest data.", Icon: I.Cpu },
{ id: "history", label: "History", subtitle: "Recent retrain jobs and outcomes.", Icon: I.History }];


/* ============================================================
 * MODEL METRICS (longitudinal)
 * ============================================================ */
function MetricChart({ series, refLines = [], yMin, yMax, yUnit = "", xLabel, xTicks = [], xUnit = "", yNice = false }) {
  const W = 620, H = 250, P = { l: 46, r: 14, t: 14, b: xTicks.length ? 44 : 34 };
  const xs = series.flatMap(s => s.pts.map(p => p.x));
  const ys = series.flatMap(s => s.pts.map(p => p.y)).concat(refLines.map(r => r.y));
  if (!xs.length) return null;
  const xmin = Math.min(...xs), xmax = Math.max(...xs);
  let ymin = yMin != null ? yMin : Math.min(...ys) * 0.92;
  let ymax = yMax != null ? yMax : Math.max(...ys) * 1.06;
  if (yNice) {  // arredonda a múltiplos "limpos" para um eixo legível
    const span = Math.max(1, ymax - ymin);
    const step = Math.pow(10, Math.floor(Math.log10(span)));
    ymin = Math.floor(ymin / step) * step;
    ymax = Math.ceil(ymax / step) * step;
  }
  const sx = x => P.l + (xmax === xmin ? 0.5 : (x - xmin) / (xmax - xmin)) * (W - P.l - P.r);
  const sy = y => H - P.b - (ymax === ymin ? 0.5 : (y - ymin) / (ymax - ymin)) * (H - P.t - P.b);
  const yticks = [ymin, (ymin + ymax) / 2, ymax];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 260 }}>
      {yticks.map((t, i) => (
        <g key={i}>
          <line x1={P.l} x2={W - P.r} y1={sy(t)} y2={sy(t)} stroke="var(--border-soft)" strokeWidth="1" />
          <text x={P.l - 6} y={sy(t) + 3} textAnchor="end" fontSize="10" fill="var(--text-faint)">{Math.round(t)}{yUnit}</text>
        </g>
      ))}
      {xTicks.map((t, i) => (
        <text key={"x" + i} x={sx(t)} y={H - P.b + 14} textAnchor="middle" fontSize="10" fill="var(--text-faint)">{t}{xUnit}</text>
      ))}
      {refLines.map((r, i) => (
        <g key={"r" + i}>
          <line x1={P.l} x2={W - P.r} y1={sy(r.y)} y2={sy(r.y)} stroke={r.color} strokeWidth="1.5" strokeDasharray="5 4" opacity="0.85" />
          <text x={W - P.r} y={sy(r.y) - 4} textAnchor="end" fontSize="10" fill={r.color}>{r.label}</text>
        </g>
      ))}
      {series.map((s, si) => {
        const d = s.pts.map((p, i) => (i ? "L" : "M") + sx(p.x) + " " + sy(p.y)).join(" ");
        return (
          <g key={si}>
            <path d={d} fill="none" stroke={s.color} strokeWidth="2"
              strokeDasharray={s.dashed ? "6 4" : "0"} opacity={s.dashed ? 0.7 : 1} />
            {!s.dashed && s.pts.map((p, i) => <circle key={i} cx={sx(p.x)} cy={sy(p.y)} r="3" fill={s.color} />)}
          </g>
        );
      })}
      {xLabel && <text x={(P.l + W - P.r) / 2} y={H - 6} textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">{xLabel}</text>}
    </svg>
  );
}

function MetricStat({ label, value, sub, tone }) {
  const col = tone === "ok" ? "var(--ok)" : tone === "warn" ? "var(--warn)" : "var(--text)";
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3">
      <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">{label}</div>
      <div className="mt-1 text-[20px] font-semibold tabular-nums" style={{ color: col }}>{value}</div>
      {sub && <div className="text-[11.5px] text-[var(--text-faint)] mt-0.5">{sub}</div>}
    </div>
  );
}

function MetricsPage({ server }) {
  const [data, setData] = useStateE(null);
  const [err, setErr] = useStateE(null);
  useEffectE(() => {
    let cancelled = false;
    (async () => {
      try { const d = await eApi(server, "/metrics"); if (!cancelled) { setData(d); setErr(null); } }
      catch (e) { if (!cancelled) setErr(e); }
    })();
  }, [server]);

  if (err) return <div className="text-[13px] text-[var(--text-muted)]">Sem métricas. Corre <span className="font-mono">pipeline train</span> primeiro.</div>;
  if (!data) return <div className="text-[13px] text-[var(--text-muted)]">A carregar métricas…</div>;

  const hist = data.history || [];
  const last = hist[hist.length - 1] || {};
  const floor = data.noise_floor;
  const accReal = { pts: hist.map(h => ({ x: h.n_panels, y: h.mae })), color: "var(--accent)" };
  const accProj = { pts: (data.projection || []).map(p => ({ x: p.n_panels, y: p.mae })), color: "var(--accent)", dashed: true };
  const covQ80 = { pts: hist.map(h => ({ x: h.n_panels, y: h.coverage_q80 })), color: "var(--ok)" };
  const covQ90 = { pts: hist.map(h => ({ x: h.n_panels, y: h.coverage_q90 })), color: "var(--accent-hover)" };

  return (
    <div className="space-y-6">
      <PageHeader title="Model Metrics" subtitle="How the model improves as production data accumulates — and how honest its confidence stays." />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricStat label="Current error (MAE)" value={`${last.mae}s`} sub={`vs human limit ${floor}s`} />
        <MetricStat label="Human noise floor" value={`${floor}s`} sub={`CV ${data.noise_floor_cv_pct}%`} tone="ok" />
        <MetricStat label="Calibration 80%" value={`${last.coverage_q80}%`} sub="target 80%" tone={Math.abs(last.coverage_q80 - 80) <= 8 ? "ok" : "warn"} />
        <MetricStat label="Training data" value={`${last.n_obs}`} sub={`${last.n_panels} panels`} />
      </div>

      <Card padded={false}>
        <div className="px-5 pt-4">
          <div className="text-[14px] font-semibold text-[var(--text)]">Accuracy vs data volume</div>
          <div className="text-[12px] text-[var(--text-muted)] mt-0.5">Each panel of data lowers the error toward the human limit. Dashed = projection.</div>
        </div>
        <div className="px-3 pb-4 pt-2">
          <MetricChart series={[accProj, accReal]} xLabel="training panels"
            refLines={[{ y: floor, color: "var(--ok)", label: "human limit" }]} yUnit="s" />
        </div>
      </Card>

      <Card padded={false}>
        <div className="px-5 pt-4">
          <div className="text-[14px] font-semibold text-[var(--text)]">Calibration over time</div>
          <div className="text-[12px] text-[var(--text-muted)] mt-0.5">Confidence intervals stay honest as data grows (lines should hug the targets).</div>
        </div>
        <div className="px-3 pb-4 pt-2">
          <MetricChart series={[covQ80, covQ90]} xLabel="training panels" yMin={50} yMax={100} yUnit="%"
            refLines={[{ y: 80, color: "var(--ok)", label: "80% target" }, { y: 90, color: "var(--accent-hover)", label: "90% target" }]} />
          <div className="px-2 mt-2 flex items-center gap-4 text-[11.5px] text-[var(--text-muted)]">
            <span className="inline-flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block" style={{ background: "var(--ok)" }} />80% interval</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block" style={{ background: "var(--accent-hover)" }} />90% interval</span>
          </div>
        </div>
      </Card>

      <div className="text-[11.5px] text-[var(--text-faint)] leading-relaxed">
        Historical points are backfilled by training on increasing data volumes (an honest proxy for monthly retrains);
        the last point is the live model. The projection extrapolates the trend toward the human noise floor and is an
        estimate, not a measurement.
      </div>
    </div>
  );
}


/* ============================================================
 * LIVE DASHBOARD (demo · simulated data)
 * ============================================================ */
/* actual (min) vs expected per micro-operation */
const D_MICRO = [
  { n: 1, name: "Pick profiles", real: 0.8, exp: 0.8 },
  { n: 2, name: "Place profiles", real: 1.2, exp: 1.1 },
  { n: 3, name: "Fix frame", real: 0.6, exp: 0.7 },
  { n: 4, name: "Measure / align", real: 2.1, exp: 1.6 },
  { n: 5, name: "Crimp frame", real: 1.4, exp: 1.4 },
  { n: 6, name: "Place 1st board", real: 1.7, exp: 1.6 },
  { n: 7, name: "Measure on board", real: 2.6, exp: 1.9 },
  { n: 8, name: "Screw board", real: null, exp: 1.0, state: "active" },
  { n: 9, name: "Remove fasteners", real: null, exp: null, state: "todo" },
  { n: 10, name: "Flip frame", real: null, exp: null, state: "todo" }];

/* ordered by production sequence: completed first (in finish order), in-progress last */
const D_COMPARE = [
  { ref: "PG01K", real: 16.2, est: 18.0, done: "08:28" },
  { ref: "PG02K", real: 15.8, est: 17.5, done: "08:49" },
  { ref: "PCT01K", real: 14.0, est: 15.2, done: "11:05" },
  { ref: "PP01K", real: 25.4, est: 19.8, done: "11:42" },
  { ref: "PL01K", real: 17.3, est: 18.5, done: "13:30" },
  { ref: "PG03K", real: 12.1, est: 16.0, running: true }];

const D_QUEUE = [
  { ref: "ECO_PG01K", start: "08:12", dur: "16m", status: "done" },
  { ref: "ECO_PG02K", start: "08:31", dur: "18m", status: "done" },
  { ref: "ECO_PG03K", start: "14:20", dur: "—", status: "active" },
  { ref: "ECO_PP01K", start: "—", dur: "~20m", status: "queue" },
  { ref: "ECO_PL01K", start: "—", dur: "~17m", status: "queue" }];

/* phases group the 14 steps — so the progress bar aligns with the labels */
const D_PHASES = [
  { name: "pick profiles", steps: 3 },
  { name: "crimping", steps: 3 },
  { name: "boarding", steps: 5 },
  { name: "labeling", steps: 3 }];

const D_TONE = { ok: "var(--ok)", warn: "var(--warn)", err: "var(--err)", active: "var(--accent-hover)", todo: "var(--border)" };

/* single color rule: <=10% within · 10-20% near limit · >20% deviation */
function dDeltaPct(real, exp) {
  if (real == null || exp == null || !exp) return null;
  return Math.round((real - exp) / exp * 100);
}
function dDevTone(real, exp) {
  const d = dDeltaPct(real, exp);
  if (d == null) return "ok";
  const a = Math.abs(d);
  if (a > 20) return "err";
  if (a > 10) return "warn";
  return "ok";
}
function dFmtDelta(d) {
  if (d == null) return "";
  return (d > 0 ? "+" : "") + d + "%";
}

function DLegend({ className = "" }) {
  const items = [
    { c: "var(--ok)", t: "within estimate (±10%)" },
    { c: "var(--warn)", t: "near limit (10–20%)" },
    { c: "var(--err)", t: "deviation > 20%" }];
  return (
    <div className={"flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-[var(--text-muted)] " + className}>
      {items.map((it) => (
        <span key={it.t} className="inline-flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: it.c }} />{it.t}
        </span>
      ))}
    </div>);
}

function DMetric({ icon, label, value, unit, sub, subTone, hint, alert }) {
  const Icon = icon;
  const sc = subTone === "up" ? "var(--ok)" : subTone === "down" ? "var(--err)" : "var(--text-faint)";
  return (
    <div className="rounded-lg px-4 py-3.5 border bg-[var(--surface)]"
      style={alert ? { borderColor: "var(--err)", background: "color-mix(in srgb, var(--err) 8%, var(--surface))" } : { borderColor: "var(--border)" }}>
      <div className="text-[11.5px] flex items-center gap-1.5" style={{ color: alert ? "var(--err)" : "var(--text-muted)" }}>
        <Icon size={13} />{label}
      </div>
      <div className="mt-1.5 text-[22px] font-semibold text-[var(--text)] tabular-nums">
        {value}{unit && <span className="text-[14px] font-normal text-[var(--text-muted)] ml-0.5">{unit}</span>}
      </div>
      {sub && <div className="text-[11px] mt-0.5" style={{ color: alert ? "var(--err)" : sc }}>{sub}</div>}
      {hint && <div className="text-[10.5px] mt-0.5 text-[var(--text-faint)]">{hint}</div>}
    </div>);
}

function DashboardPage() {
  const TOTAL_STEPS = 14, DONE_STEPS = 7, ACTIVE_STEP = 8;
  const [secs, setSecs] = useStateE(724);
  const [clock, setClock] = useStateE("");
  useEffectE(() => {
    const id = setInterval(() => setSecs((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);
  useEffectE(() => {
    function tick() {
      const d = new Date();
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      setClock(`${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()} · ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`);
    }
    tick();
    const id = setInterval(tick, 30000);
    return () => clearInterval(id);
  }, []);
  const elapsed = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;
  const EST_SEC = 16 * 60;
  const overEst = secs > EST_SEC;
  const remainMin = Math.ceil(Math.abs(EST_SEC - secs) / 60);
  const paceLabel = overEst ? `behind · +${remainMin} min` : `on time · ${remainMin} min left`;
  const paceColor = overEst ? "var(--err)" : "var(--ok)";
  const maxCmp = Math.max(...D_COMPARE.flatMap((c) => [c.real, c.est])) * 1.05;
  const maxMicro = Math.max(...D_MICRO.map((m) => m.real || 0).concat(D_MICRO.map((m) => m.exp || 0)));

  return (
    <div className="space-y-5">
      {/* demo banner */}
      <div className="rounded-lg border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-4 py-3 flex items-start gap-2.5">
        <span className="text-[var(--accent-hover)] mt-0.5"><I.Info size={16} /></span>
        <div className="text-[12.5px] text-[var(--text)] leading-relaxed">
          <span className="font-semibold">Demo · simulated data.</span>{" "}
          <span className="text-[var(--text-muted)]">Mockup of a shop-floor production panel. With real-time capture at the station (MES / sensors / per-panel label scan), these numbers feed live and the dashboard becomes functional — the model already predicts time per panel and per micro-operation.</span>
        </div>
      </div>

      {/* top bar */}
      <div className="flex items-center justify-between flex-wrap gap-3 pb-1 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5 text-[15px] font-medium text-[var(--text)]">
          <I.Gauge size={18} /> BluFab · Station 66 — Framing &amp; Boarding
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[12px] text-[var(--text-muted)]">{clock}</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--ok)]/15 text-[var(--ok)] text-[11px] font-medium px-2.5 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--ok)] animate-pulse" /> live
          </span>
        </div>
      </div>

      {/* color legend — defines the rule once for the whole dashboard */}
      <DLegend className="-mt-1" />

      {/* metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <DMetric icon={I.CircleCheck} label="Panels completed" value="7" sub="of 11 planned today" hint="64% of today's plan" />
        <DMetric icon={I.Clock} label="Avg actual time" value="18" unit="min" sub="↓ 2 min vs estimate" subTone="up" hint="average of panels completed today" />
        <DMetric icon={I.Activity} label="Model accuracy" value="91" unit="%" sub="↑ 3% this week" subTone="up" hint="predictions within ±15% of actual" />
        <DMetric icon={I.CircleAlert} label="Deviations > 20%" value="1" sub="ECO_PP01K · 25.4m vs 19.8m est." alert />
      </div>

      {/* in production now */}
      <Card padded={false}>
        <div className="px-5 pt-4 text-[12px] font-medium uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
          <I.Play size={13} /> In production now
        </div>
        <div className="px-5 py-4 flex flex-col md:flex-row items-start gap-5">
          <div className="flex-1 min-w-0 w-full">
            <div className="text-[20px] font-semibold text-[var(--text)] font-mono">ECO_PG03K</div>
            <div className="text-[12px] text-[var(--text-muted)] mt-0.5">ECOCIAF01 GENERAL PAIR 03K · IS01A · Batch #024</div>
            {/* progress grouped by phase so segments align with labels */}
            <div className="flex gap-2 mt-3.5">
              {D_PHASES.map((ph, pi) => {
                const before = D_PHASES.slice(0, pi).reduce((a, p) => a + p.steps, 0);
                const isCurrent = ACTIVE_STEP > before && ACTIVE_STEP <= before + ph.steps;
                return (
                  <div key={ph.name} className="flex-1 min-w-0">
                    <div className="flex gap-1">
                      {Array.from({ length: ph.steps }, (_, i) => {
                        const idx = before + i + 1;
                        const cls = idx < ACTIVE_STEP ? "bg-[var(--ok)]" : idx === ACTIVE_STEP ? "bg-[var(--warn)] animate-pulse" : "bg-[var(--surface-2)]";
                        return <span key={i} className={"h-1.5 flex-1 min-w-[10px] rounded-full " + cls} />;
                      })}
                    </div>
                    <div className="text-[10px] mt-1.5 text-center truncate" style={{ color: isCurrent ? "var(--warn)" : "var(--text-faint)", fontWeight: isCurrent ? 600 : 400 }}>{ph.name}</div>
                  </div>);
              })}
            </div>
            <div className="text-[13px] font-medium text-[var(--text)] mt-3">Screw board to frame</div>
            <div className="text-[12px] text-[var(--text-muted)]">Step {ACTIVE_STEP} of {TOTAL_STEPS} · phase <span className="text-[var(--warn)]">boarding</span> · in progress</div>
          </div>
          <div className="hidden md:block w-px self-stretch bg-[var(--border)]" />
          <div className="text-right md:min-w-[140px]">
            <div className="text-[11px] text-[var(--text-muted)]">elapsed</div>
            <div className="text-[28px] font-semibold font-mono mt-1 tabular-nums" style={{ color: overEst ? "var(--err)" : "var(--text)" }}>{elapsed}</div>
            <div className="text-[11px] text-[var(--text-muted)] mt-1">estimate: 16 min</div>
            <div className="text-[12px] font-medium mt-1.5 inline-flex items-center gap-1 justify-end" style={{ color: paceColor }}>
              {overEst ? <I.CircleAlert size={13} /> : <I.CircleCheck size={13} />} {paceLabel}
            </div>
          </div>
        </div>
      </Card>

      {/* two-col bottom */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* micro-processes */}
        <Card padded={false}>
          <div className="px-5 pt-4 pb-1 text-[12px] font-medium uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
            <I.BarChart size={13} /> Time per micro-operation
          </div>
          <div className="px-5 text-[10.5px] text-[var(--text-faint)] pb-2">longer bar = slower · color = deviation vs expected</div>
          <div className="px-5 pb-4 space-y-2">
            {D_MICRO.map((m) => {
              const isActive = m.state === "active", isTodo = m.state === "todo";
              const tone = isActive ? "active" : dDevTone(m.real, m.exp);
              const delta = dDeltaPct(m.real, m.exp);
              const w = isTodo ? 0 : ((isActive ? m.exp : m.real) / maxMicro) * 100;
              return (
                <div key={m.n} className={"flex items-center gap-2.5 text-[12px] rounded-md px-1.5 py-1 " + (isActive ? "bg-[var(--surface-2)]" : "")} style={{ opacity: isTodo ? 0.45 : 1 }}>
                  <span className="text-[11px] w-4 shrink-0" style={{ color: isActive ? "var(--warn)" : "var(--text-faint)" }}>{m.n}</span>
                  <span className={"flex-1 truncate " + (isActive ? "font-medium text-[var(--text)]" : "text-[var(--text)]")}>
                    {m.name}{isActive && <span className="text-[var(--warn)]"> ← now</span>}
                  </span>
                  <span className="w-20 h-1.5 rounded-full bg-[var(--surface-2)] overflow-hidden shrink-0">
                    <span className={"block h-full rounded-full " + (isActive ? "animate-pulse" : "")} style={{ width: w + "%", background: D_TONE[tone] }} />
                  </span>
                  <span className="text-[11px] w-24 text-right shrink-0 tabular-nums" style={{ color: isActive ? "var(--warn)" : "var(--text-muted)" }}>
                    {isActive ? "in progress" : isTodo ? "—" : (
                      <>{m.real.toFixed(1)} min{delta != null && delta > 5 && <span style={{ color: D_TONE[tone] }}> · {dFmtDelta(delta)}</span>}</>
                    )}
                  </span>
                </div>);
            })}
          </div>
        </Card>

        {/* right column */}
        <div className="space-y-3">
          {/* actual vs estimate */}
          <Card padded={false}>
            <div className="px-5 pt-4 text-[12px] font-medium uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
              <I.Activity size={13} /> Actual vs estimate · by finish order
            </div>
            <div className="px-5 pt-2 pb-4">
              <div className="flex gap-4 text-[11px] text-[var(--text-muted)] mb-3">
                <span className="inline-flex items-center gap-1.5"><span className="w-3 h-1.5 rounded-sm inline-block" style={{ background: "var(--text-muted)" }} />bar = actual</span>
                <span className="inline-flex items-center gap-1.5"><span className="w-0.5 h-3 rounded-sm inline-block" style={{ background: "var(--text)" }} />mark = estimate</span>
              </div>
              {D_COMPARE.map((c) => {
                const delta = dDeltaPct(c.real, c.est);
                const tone = c.running ? "active" : dDevTone(c.real, c.est);
                const col = D_TONE[tone];
                return (
                  <div key={c.ref} className="flex items-center gap-2.5 text-[12px] mb-2.5">
                    <span className="w-14 text-[var(--text-muted)] shrink-0 font-mono text-[11px]">{c.ref}</span>
                    <span className="flex-1 h-2 rounded-full bg-[var(--surface-2)] overflow-hidden relative">
                      <span className="block h-full rounded-full" style={{ width: (c.real / maxCmp * 100) + "%", background: col }} />
                      <span className="absolute top-[-2px] bottom-[-2px] w-[2px] rounded bg-[var(--text)]" style={{ left: (c.est / maxCmp * 100) + "%" }} title={"estimate " + c.est.toFixed(1) + "m"} />
                    </span>
                    <span className="w-12 text-right font-medium text-[var(--text)] tabular-nums text-[11px]">{c.real.toFixed(1)}m</span>
                    <span className="w-16 text-right tabular-nums text-[11px] font-medium shrink-0" style={{ color: col }}>
                      {c.running ? "in progress" : dFmtDelta(delta)}
                    </span>
                  </div>);
              })}
            </div>
          </Card>

          {/* MES queue */}
          <Card padded={false}>
            <div className="px-5 pt-4 pb-2 text-[12px] font-medium uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
              <I.List size={13} /> MES sequence · today
            </div>
            <div className="px-5 pb-4">
              <table className="w-full text-[12px]">
                <thead>
                  <tr className="text-[var(--text-muted)] text-left border-b border-[var(--border)]">
                    <th className="font-medium pb-2">Ref.</th><th className="font-medium pb-2">Start</th>
                    <th className="font-medium pb-2">Dur.</th><th className="font-medium pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {D_QUEUE.map((r) => {
                    const pill = r.status === "done" ? { bg: "var(--ok)", t: "done" } : r.status === "active" ? { bg: "var(--warn)", t: "in progress" } : { bg: "var(--text-faint)", t: "queued" };
                    return (
                      <tr key={r.ref} className="border-b border-[var(--border)] last:border-0">
                        <td className="py-2 font-mono text-[11px] text-[var(--text)]">{r.ref}</td>
                        <td className="py-2 text-[var(--text-muted)]">{r.start}</td>
                        <td className="py-2 text-[var(--text-muted)]">{r.dur}</td>
                        <td className="py-2">
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full" style={{ background: pill.bg + "26", color: pill.bg }}>{pill.t}</span>
                        </td>
                      </tr>);
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </div>);
}


function Sidebar({ active, onChange }) {
  return (
    <aside className="w-[244px] shrink-0 border-r border-[var(--border)] bg-[#0E1626] flex flex-col">
      <div className="h-[60px] px-5 border-b border-[var(--border)] flex items-center">
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-9 w-9 rounded-lg bg-[var(--accent)] flex items-center justify-center text-white shrink-0">
            <I.Activity size={18} />
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-[15px] text-[var(--text)] tracking-tight leading-tight">BluFab</div>
            <div className="text-[11.5px] text-[var(--text-muted)] leading-tight mt-0.5 truncate">Panel Time Predictor</div>
          </div>
        </div>
      </div>

      <nav className="px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-faint)]">Workspace</div>
        {NAV.map((n) => {
          const isActive = active === n.id;
          return (
            <button key={n.id} onClick={() => onChange(n.id)}
            className={"w-full text-left flex items-center gap-3 px-3 h-10 rounded-md transition-colors duration-150 " + (
            isActive ?
            "bg-[var(--accent)]/12 text-[var(--text)]" :
            "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]")}>
              <span className={isActive ? "text-[var(--accent-hover)]" : "text-[var(--text-faint)]"}>
                <n.Icon size={17} />
              </span>
              <span className="text-[14px] font-medium flex-1">{n.label}</span>
              {isActive && <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-hover)]" />}
            </button>);

        })}
      </nav>

      <div className="mt-auto px-5 py-4 border-t border-[var(--border)] text-[12px] text-[var(--text-faint)]">
        Production Order Duration Forecasting
      </div>
    </aside>);

}

/* ============================================================
 * TOP BAR
 * ============================================================ */
function TopBar({ server, setServer, health, modelName, onFuture }) {
  const tone = health === "ok" ? "ok" : health === "checking" ? "slate" : "err";
  const label = health === "ok" ? "Connected" : health === "checking" ? "Checking…" : "Disconnected";
  const healthTip = health === "ok"
    ? "Green means everything is working. If it turns red, the page can't reach the program that does the calculations — try refreshing, or call IT."
    : health === "checking"
      ? "We're checking whether the calculation program is reachable. This usually only takes a moment."
      : "Red means we can't reach the program that does the calculations. Try refreshing the page. If it stays red, call IT.";
  return (
    <div className="h-[60px] border-b border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur-sm flex items-center gap-3 px-6">
      <div className="flex items-center gap-2 h-9 px-3 rounded-md bg-[var(--surface)] border border-[var(--border)] focus-within:border-[var(--accent)] transition-colors min-w-[280px] max-w-[480px] flex-1">
        <I.Server size={15} className="text-[var(--text-faint)] shrink-0" />
        <input
          value={server}
          onChange={(e) => setServer(e.target.value)}
          spellCheck={false}
          className="flex-1 min-w-0 bg-transparent outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)]"
          placeholder="Server address" />
        <HelpTip
          label="Server address"
          text="The web address of the program that does the calculations. Your IT team set this. Leave it as-is unless someone tells you to change it." />
      </div>

      <div className="ml-auto flex items-center gap-2">
        {onFuture && (
          <button onClick={onFuture}
            className="flex items-center gap-1.5 h-9 px-3 rounded-md border border-[var(--accent)]/40 bg-[var(--accent)]/10 text-[13px] text-[var(--accent-hover)] hover:bg-[var(--accent)]/20 transition-colors">
            <I.Activity size={15} />
            <span>Future Vision</span>
            <I.ChevDown size={14} className="-rotate-90" />
          </button>
        )}
        <div className="flex items-center gap-2 h-9 px-3 rounded-md border border-[var(--border)] bg-[var(--surface)]">
          <StatusDot tone={tone} />
          <span className="text-[13px] text-[var(--text)]">{label}</span>
          <HelpTip label="Connection status" text={healthTip} />
        </div>

        <div className="flex items-center gap-2 h-9 px-3 rounded-md border border-[var(--border)] bg-[var(--surface)]">
          <I.Brain size={15} className="text-[var(--accent-hover)]" />
          <span className="text-[12px] text-[var(--text-muted)]">Model</span>
          <span className="text-[13px] text-[var(--text)] truncate max-w-[160px]">{modelName || "—"}</span>
          <HelpTip
            label="Current model"
            text="The nickname of the 'brain' currently making predictions. Every so often we teach it from newer data and the nickname changes — that's normal." />
        </div>
      </div>
    </div>);

}

/* ============================================================
 * FORECAST
 * ============================================================ */
function eItemTotalSec(it) {
  if (!it.result) return 0;
  if (typeof it.result.total_sec === "number") return it.result.total_sec;
  return (it.result.predictions || []).reduce((a, p) => a + (p.predicted_duration_sec || 0), 0);
}

function UnifiedEntriesInput({ entries, onChange, disabled }) {
  const inputRef = useRefE(null);
  const pendingRowRef = useRefE(null);
  const [dragging, setDragging] = useStateE(false);
  const [flashId, setFlashId] = useStateE(null);
  const flashTimerRef = useRefE(null);

  function flashRow(id) {
    setFlashId(id);
    if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    flashTimerRef.current = setTimeout(() => setFlashId(null), 1200);
  }

  function setRow(id, patch) {
    onChange(entries.map(r => r.id === id ? { ...r, ...patch } : r));
  }
  function clearRow(id) {
    setRow(id, { kind: "key", value: "", file: null });
  }
  function remove(id) {
    if (entries.length === 1) {
      onChange([{ id: eRid(), kind: "key", value: "", file: null }]);
      return;
    }
    onChange(entries.filter(r => r.id !== id));
  }
  function add() {
    onChange([...entries, { id: eRid(), kind: "key", value: "", file: null }]);
  }

  function addFilesToRow(triggerRowId, fileList) {
    const files = Array.from(fileList || []).filter(f => /\.pdf$/i.test(f.name) || f.type === "application/pdf");
    if (!files.length) return;
    const next = entries.slice();
    let triggerIdx = next.findIndex(r => r.id === triggerRowId);
    let lastDupeId = null;
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      const dupe = next.find(r => r.file && r.file.name === f.name && r.file.size === f.size);
      if (dupe) { lastDupeId = dupe.id; continue; }
      // First non-dupe file goes to the trigger row if it's empty or being replaced
      if (triggerIdx >= 0) {
        next[triggerIdx] = { ...next[triggerIdx], kind: "pdf", value: "", file: f };
        triggerIdx = -1; // consumed
        continue;
      }
      // Subsequent files: fill any other empty row, else append
      const emptyIdx = next.findIndex(r => !r.value && !r.file);
      if (emptyIdx >= 0) {
        next[emptyIdx] = { ...next[emptyIdx], kind: "pdf", value: "", file: f };
      } else {
        next.push({ id: eRid(), kind: "pdf", value: "", file: f });
      }
    }
    onChange(next);
    if (lastDupeId) flashRow(lastDupeId);
  }

  function openPicker(rowId) {
    pendingRowRef.current = rowId;
    if (inputRef.current) inputRef.current.value = "";
    inputRef.current && inputRef.current.click();
  }
  function onPicked(list) {
    if (!list || !list.length) return;
    const rowId = pendingRowRef.current;
    pendingRowRef.current = null;
    if (rowId) addFilesToRow(rowId, list);
  }

  // Card-wide drop: each file becomes a row (fill empty rows first), with dedupe
  function onDragOver(e) { e.preventDefault(); e.stopPropagation(); if (!dragging) setDragging(true); }
  function onDragLeave(e) {
    e.preventDefault(); e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setDragging(false);
  }
  function onDrop(e) {
    e.preventDefault(); e.stopPropagation();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files || []).filter(f => /\.pdf$/i.test(f.name) || f.type === "application/pdf");
    if (!files.length) return;
    const next = entries.slice();
    let lastDupeId = null;
    for (const f of files) {
      const dupe = next.find(r => r.file && r.file.name === f.name && r.file.size === f.size);
      if (dupe) { lastDupeId = dupe.id; continue; }
      const emptyIdx = next.findIndex(r => !r.value && !r.file);
      if (emptyIdx >= 0) {
        next[emptyIdx] = { ...next[emptyIdx], kind: "pdf", value: "", file: f };
      } else {
        next.push({ id: eRid(), kind: "pdf", value: "", file: f });
      }
    }
    onChange(next);
    if (lastDupeId) flashRow(lastDupeId);
  }

  return (
    <div
      onDragOver={onDragOver}
      onDragEnter={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={"relative rounded-lg transition-colors " + (dragging ? "ring-2 ring-blue-400 ring-offset-2 ring-offset-[var(--surface)]" : "")}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="application/pdf"
        className="hidden"
        onChange={(e) => onPicked(e.target.files)}
      />

      <div className="text-[13px] font-medium text-[var(--text)] mb-2 inline-flex items-center gap-1.5">
        <span>Production orders</span>
        <HelpTip
          label="Production orders"
          text="One row per order. Type the order number (the code at the top of the BOM drawing, e.g. OP-2026-001), or click the paperclip — or drop a PDF anywhere on the card — to read the number from the file." />
      </div>

      <div className="space-y-2">
        {entries.map((r, i) => {
          const isFlashing = flashId === r.id;
          const isFile = r.kind === "pdf" && r.file;
          return (
            <div key={r.id}
              className={"flex items-center gap-2 rounded-md transition-colors duration-300 " + (isFlashing ? "bg-amber-500/20" : "")}
              title={isFlashing ? "Already added." : undefined}>
              <div className="w-7 text-[11.5px] tabular-nums text-[var(--text-faint)] text-right shrink-0">{String(i + 1).padStart(2, "0")}</div>

              {isFile ? (
                <div className="flex-1 flex items-center gap-2.5 h-10 px-3 rounded-md bg-[var(--surface-2)] border border-[var(--accent)]/30 min-w-0">
                  <I.FileText size={14} className="text-[var(--accent-hover)] shrink-0" />
                  <span className="text-[13.5px] font-mono text-[var(--text)] truncate min-w-0 flex-1" title={r.file.name}>{r.file.name}</span>
                  <span className="text-[11.5px] text-[var(--text-muted)] tabular-nums shrink-0">{(r.file.size / 1024).toFixed(1)} KB</span>
                  <button type="button" onClick={() => clearRow(r.id)} disabled={disabled}
                    title="Clear file"
                    className="text-[var(--text-faint)] hover:text-[var(--text)] shrink-0 disabled:opacity-40">
                    <I.X size={13} />
                  </button>
                </div>
              ) : (
                <div className="flex-1 flex items-center gap-1.5 min-w-0">
                  <input
                    value={r.value}
                    onChange={(e) => setRow(r.id, { kind: "key", value: e.target.value, file: null })}
                    placeholder="OP-2026-001  or drop a BOM PDF"
                    spellCheck={false}
                    disabled={disabled}
                    className="flex-1 min-w-0 h-10 px-3 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[14px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-colors font-mono"
                  />
                  <button type="button" onClick={() => openPicker(r.id)} disabled={disabled}
                    title="Attach BOM PDF"
                    className="h-10 w-10 rounded-md border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)] flex items-center justify-center shrink-0 transition-colors disabled:opacity-40">
                    <I.FileUp size={14} />
                  </button>
                </div>
              )}

              <button type="button"
                onClick={() => remove(r.id)}
                disabled={disabled}
                title={entries.length === 1 ? "Clear row" : "Remove row"}
                className="h-10 w-10 rounded-md border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)] flex items-center justify-center shrink-0 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                <I.Minus size={14} />
              </button>
            </div>
          );
        })}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button type="button" onClick={add} disabled={disabled}
          className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md text-[13px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50">
          <I.Plus size={14} />
          Add another
        </button>
        <HelpTip label="Add another order" text="Add another order to predict in the same batch. You can mix typed order numbers and dropped PDFs freely." />
      </div>

      <div className="mt-2 text-[12px] text-[var(--text-muted)] flex items-center gap-1.5">
        <I.FileUp size={12} className="text-[var(--text-faint)]" />
        Type order numbers or attach / drop BOM PDFs. Mix freely.
      </div>

      {dragging && (
        <div className="pointer-events-none absolute inset-0 rounded-lg flex items-center justify-center bg-blue-500/15 text-[var(--text)]">
          <div className="flex items-center gap-2 text-[14px] font-medium">
            <I.FileUp size={18} className="text-blue-300" />
            Drop PDFs to add as new rows
          </div>
        </div>
      )}
    </div>
  );
}


function RunPredictionsButton({ count, loading, disabled, onClick }) {
  return (
    <button type="button" onClick={onClick}
      disabled={disabled || loading || count === 0}
      className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md text-[14.5px] font-medium text-white bg-gradient-to-br from-blue-600 to-blue-900 hover:from-blue-500 hover:to-blue-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm whitespace-nowrap">
      {loading ? <I.Loader size={16} /> : <I.Calculator size={16} />}
      <span>Run predictions</span>
      {count > 1 && (
        <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1.5 rounded-full bg-white/15 text-[12px] font-semibold tabular-nums">
          {count}
        </span>
      )}
    </button>
  );
}

function ResultStatusIcon({ state }) {
  if (state === "running") return <I.Loader size={18} className="text-blue-400" />;
  if (state === "success") return <I.CircleCheck size={18} className="text-[var(--ok)]" />;
  if (state === "error") return <I.CircleX size={18} className="text-[var(--err)]" />;
  return <div className="h-[18px] w-[18px] rounded-full border border-[var(--border)] bg-[var(--surface-2)]" />;
}

function ExtractedDetails({ extracted }) {
  if (!extracted || typeof extracted !== "object") return null;
  function fmtVal(k, v) {
    if (v == null || v === "") return null;
    if (k === "largura_mm" || k === "altura_mm" || k === "espessura_mm") return v + " mm";
    if (k === "area_m2") return Number(v).toFixed(2) + " m\u00b2";
    return String(v);
  }
  const labels = {
    panel_id: "Panel ID", panel_tipo: "Panel type",
    largura_mm: "Width", altura_mm: "Height", espessura_mm: "Thickness",
    area_m2: "Area", cladding_material: "Cladding material", categoria: "Category"
  };
  const entries = Object.keys(extracted)
    .filter(k => k !== "op_producao")
    .map(k => ({ k, label: labels[k] || k.replace(/_/g, " "), value: fmtVal(k, extracted[k]) }))
    .filter(e => e.value != null);
  if (!entries.length) return null;
  return (
    <div className="px-6 py-4 border-b border-[var(--border-soft)]">
      <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-3 inline-flex items-center gap-1.5">
        <span>Detected from PDF</span>
        <HelpTip label="Detected from PDF" text="Information we read off the BOM drawing — the panel's size, material, and so on. Useful to double-check we picked up the right file." />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-3">
        {entries.map(e => (
          <div key={e.k} className="min-w-0">
            <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">{e.label}</div>
            <div className="mt-0.5 text-[13px] text-[var(--text)] font-mono tabular-nums truncate">{e.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RunningDots() {
  return (
    <span className="inline-flex gap-0.5 text-[var(--text-muted)] text-[18px] leading-none align-middle">
      <span className="animate-pulse" style={{ animationDelay: "0ms" }}>.</span>
      <span className="animate-pulse" style={{ animationDelay: "150ms" }}>.</span>
      <span className="animate-pulse" style={{ animationDelay: "300ms" }}>.</span>
    </span>
  );
}

function PanelGroupRow({ panel, defaultOpen }) {
  const [open, setOpen] = useStateE(defaultOpen);
  const ops = (panel.micro_ops || []).slice().sort((a, b) => (a.op_order || 0) - (b.op_order || 0));
  const ptotal = panel.total_sec || ops.reduce((a, p) => a + (p.predicted_duration_sec || 0), 0);
  return (
    <div>
      <button type="button" onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-[var(--surface-2)]/40 transition-colors">
        <I.Layers size={14} className="text-[var(--text-faint)] shrink-0" />
        <span className="flex-1 min-w-0 text-[13.5px] font-mono text-[var(--text)] truncate">{panel.panel_id}</span>
        <span className="text-[12px] text-[var(--text-muted)] tabular-nums">{ops.length} ops</span>
        <span className="text-[13px] font-medium text-[var(--text)] tabular-nums">{eFormatSeconds(ptotal)}</span>
        <span className="text-[var(--text-faint)] shrink-0">{open ? <I.ChevUp size={15} /> : <I.ChevDown size={15} />}</span>
      </button>
      {open && (
        <div className="overflow-x-auto border-t border-[var(--border-soft)] bg-[var(--bg)]/30">
          <table className="w-full text-[13px]">
            <tbody>
              {ops.map((p, i) => {
                const pct = ptotal ? (p.predicted_duration_sec / ptotal) * 100 : 0;
                return (
                  <tr key={(p.op_id || "") + "-" + i} className="border-b border-[var(--border-soft)] last:border-b-0 hover:bg-[var(--surface-2)]/40 transition-colors">
                    <td className="px-4 py-2 w-16 tabular-nums text-[var(--text-muted)]">{String(p.op_order ?? i + 1).padStart(2, "0")}</td>
                    <td className="px-4 py-2 text-[var(--text)]">{p.op_id}</td>
                    <td className="px-4 py-2 w-36 tabular-nums text-right text-[var(--text)] font-medium">{eFormatSeconds(p.predicted_duration_sec)}</td>
                    <td className="px-4 py-2 w-44 pr-4">
                      <div className="flex items-center gap-2.5 justify-end">
                        <div className="h-1.5 w-20 rounded-full bg-[var(--surface-2)] overflow-hidden">
                          <div className="h-full bg-[var(--accent)] rounded-full" style={{ width: pct + "%" }} />
                        </div>
                        <span className="tabular-nums text-[12px] text-[var(--text-muted)] w-10 text-right">{pct.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function PanelAccordion({ panels }) {
  return (
    <div className="divide-y divide-[var(--border-soft)]">
      {panels.map((p, i) => <PanelGroupRow key={(p.panel_id || "") + i} panel={p} defaultOpen={panels.length <= 2} />)}
    </div>
  );
}

function ResultCard({ item, onToggle, onRetry }) {
  const expanded = !!item.expanded;
  const isMerged = Array.isArray(item.members) && item.members.length > 1;
  const opChip = item.kind === "pdf" && item.result && item.result.key ? item.result.key : null;
  const total = eItemTotalSec(item);
  const preds = (item.result && item.result.predictions) || [];
  const warnings = (item.result && item.result.warnings) || [];
  const extracted = item.result && item.result.extracted;
  const panelsDetail = (item.result && item.result.panels) || [];
  const multiPanel = panelsDetail.length > 1;
  const errCtx = item.kind === "pdf" ? "pdf" : "key";

  return (
    <div className={"bg-[var(--surface)] border rounded-lg overflow-hidden transition-colors " + (
      item.state === "error" ? "border-[var(--err)]/40" : "border-[var(--border)]")}>
      <button type="button"
        onClick={() => onToggle(item)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[var(--surface-2)]/40 transition-colors">
        <ResultStatusIcon state={item.state} />
        <div className="min-w-0 flex-1 flex items-center gap-2 flex-wrap">
          {isMerged ? (
            <>
              <span className="text-[13.5px] font-mono text-[var(--text)] truncate" title={opChip || item.label}>
                {opChip || eExtractOpFromFilename(item.label) || item.label}
              </span>
              <span className="inline-flex items-center gap-1 px-2 h-5 rounded-full bg-[var(--accent)]/12 border border-[var(--accent)]/30 text-[11.5px] text-[var(--accent-hover)] font-medium">
                <I.Merge size={11} />
                {item.members.length} files
              </span>
            </>
          ) : item.kind === "pdf" ? (
            <>
              <I.FileText size={14} className="text-[var(--text-faint)] shrink-0" />
              <span className="text-[13.5px] font-mono text-[var(--text)] truncate" title={item.label}>{item.label}</span>
              {opChip && (
                <span className="inline-flex items-center gap-1 px-2 h-5 rounded-full bg-[var(--surface-2)] border border-[var(--border)] text-[11.5px] font-mono text-[var(--text-muted)]">
                  {opChip}
                </span>
              )}
            </>
          ) : (
            <span className="text-[13.5px] font-mono text-[var(--text)] truncate">{item.label}</span>
          )}
        </div>
        <div className="shrink-0 text-right min-w-0 max-w-[40%]">
          {item.state === "running" && <RunningDots />}
          {item.state === "success" && (
            <div className="text-[13.5px] font-medium text-[var(--text)] tabular-nums">{eFormatSeconds(total)}</div>
          )}
          {item.state === "error" && (
            <div className="text-[12.5px] text-[var(--err)] truncate">{eShortError(item.error, errCtx)}</div>
          )}
          {item.state === "pending" && <div className="text-[12.5px] text-[var(--text-faint)]">Queued</div>}
        </div>
        <div className="text-[var(--text-faint)] shrink-0">
          {expanded ? <I.ChevUp size={16} /> : <I.ChevDown size={16} />}
        </div>
      </button>

      {expanded && item.state === "success" && (
        <div className="border-t border-[var(--border)]">
          {warnings.length > 0 && (
            <div className="mx-4 my-3 flex items-start gap-2.5 px-4 py-3 rounded-lg border border-[var(--warn)]/30 bg-[var(--warn)]/8 text-[12.5px] text-[var(--text)]">
              <I.CircleAlert size={15} className="text-[var(--warn)] mt-0.5 shrink-0" />
              <div className="flex-1">
                {warnings.length === 1 ? warnings[0] :
                  <ul className="list-disc list-inside space-y-0.5">{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
                }
              </div>
            </div>
          )}
          {isMerged ? (
            <MembersList members={item.members} />
          ) : (
            extracted && <ExtractedDetails extracted={extracted} />
          )}
          {multiPanel ? (
            <PanelAccordion panels={panelsDetail} />
          ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-left text-[12px] font-medium text-[var(--text-muted)] border-b border-[var(--border-soft)] bg-[var(--surface-2)]/30">
                  <th className="px-4 py-2 w-16">#</th>
                  <th className="px-4 py-2">
                    <span className="inline-flex items-center gap-1.5">
                      Operation ID
                      <HelpTip label="Operation ID" text="The internal code for one manufacturing step on this panel (for example, cutting, drilling, or finishing)." />
                    </span>
                  </th>
                  <th className="px-4 py-2 text-right w-36">
                    <span className="inline-flex items-center gap-1.5 justify-end w-full">
                      Duration
                      <HelpTip label="Predicted duration" text="How long we estimate this step will take, shown as hours, minutes, and seconds. Smart estimate based on past orders, not a guarantee." />
                    </span>
                  </th>
                  <th className="px-4 py-2 w-44 text-right pr-4">
                    <span className="inline-flex items-center gap-1.5 justify-end w-full">
                      Share
                      <HelpTip label="Share of total time" text="What slice of the whole panel's time this single step takes up." />
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {preds.slice().sort((a, b) => (a.op_order || 0) - (b.op_order || 0)).map((p, i) => {
                  const pct = total ? (p.predicted_duration_sec / total) * 100 : 0;
                  return (
                    <tr key={p.op_id + "-" + i} className="border-b border-[var(--border-soft)] last:border-b-0 hover:bg-[var(--surface-2)]/40 transition-colors">
                      <td className="px-4 py-2 tabular-nums text-[var(--text-muted)]">{String(p.op_order ?? i + 1).padStart(2, "0")}</td>
                      <td className="px-4 py-2 text-[var(--text)]">{p.op_id}</td>
                      <td className="px-4 py-2 tabular-nums text-right text-[var(--text)] font-medium">{eFormatSeconds(p.predicted_duration_sec)}</td>
                      <td className="px-4 py-2 pr-4">
                        <div className="flex items-center gap-2.5 justify-end">
                          <div className="h-1.5 w-20 rounded-full bg-[var(--surface-2)] overflow-hidden">
                            <div className="h-full bg-[var(--accent)] rounded-full" style={{ width: pct + "%" }} />
                          </div>
                          <span className="tabular-nums text-[12px] text-[var(--text-muted)] w-10 text-right">{pct.toFixed(1)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          )}
        </div>
      )}

      {expanded && item.state === "error" && (
        <div className="border-t border-[var(--border)] p-4 space-y-3">
          {isMerged && <MembersList members={item.members} compact />}
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg border border-[var(--warn)]/30 bg-[var(--warn)]/8 text-[13px] text-[var(--text)]">
            <I.CircleAlert size={16} className="text-[var(--warn)] mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-[var(--text)]">{eShortError(item.error, errCtx)}</div>
              <div className="mt-1 text-[12.5px] text-[var(--text-muted)]">
                {eErrorMessage(item.error, item.kind === "pdf" ? "predict-pdf" : "predict")}
              </div>
              {!isMerged && (
                <div className="mt-2 text-[12px] font-mono text-[var(--text-faint)] truncate">{item.label}</div>
              )}
            </div>
            {!isMerged && (
              <button type="button" onClick={() => onRetry(item.id)}
                className="shrink-0 inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-[12.5px] font-medium bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors">
                <I.RotateCcw size={13} />
                Try again
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MembersList({ members, compact }) {
  return (
    <div className={(compact ? "" : "px-6 py-4 border-b border-[var(--border-soft)] ")}>
      <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-2">Detected in</div>
      <div className="space-y-1.5">
        {members.map((m) => (
          <div key={m.id} className="flex items-center gap-2.5 text-[12.5px]">
            <span className="text-[var(--text-faint)] tabular-nums select-none">──</span>
            {m.state === "error" ? (
              <I.CircleAlert size={13} className="text-[var(--warn)] shrink-0" />
            ) : (
              <I.FileText size={13} className="text-[var(--text-faint)] shrink-0" />
            )}
            <span className="font-mono text-[var(--text)] truncate min-w-0 flex-1" title={m.label}>{m.label}</span>
            {m.size != null && (
              <span className="text-[var(--text-muted)] tabular-nums text-[11.5px] shrink-0">{(m.size / 1024).toFixed(1)} KB</span>
            )}
            {m.state === "error" && m.error && (
              <span className="text-[11.5px] text-[var(--warn)] shrink-0">{eShortError(m.error, "pdf")}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function BatchSummaryBar({ items, onToggleAll, allCollapsed, onExportCsv, onExportPdf, onClear, mergedCount = 0 }) {
  const total = items.length;
  const success = items.filter(it => it.state === "success").length;
  const error = items.filter(it => it.state === "error").length;
  const running = items.filter(it => it.state === "running" || it.state === "pending").length;
  const aggregateSec = items.reduce((a, it) => a + (it.state === "success" ? eItemTotalSec(it) : 0), 0);

  return (
    <Card padded={false}>
      <div className="px-5 py-4 flex items-center gap-5 flex-wrap">
        <div className="flex items-center gap-5 flex-1 min-w-0 flex-wrap">
          <div className="flex items-center gap-1.5 text-[13px] text-[var(--text-muted)]">
            <I.Layers size={14} className="text-[var(--text-faint)]" />
            <span className="tabular-nums text-[var(--text)] font-medium">{total}</span> total
            {mergedCount > 0 && (
              <span className="text-[11.5px] text-slate-500 ml-1">({mergedCount} {mergedCount === 1 ? "duplicate" : "duplicates"} merged)</span>
            )}
            <HelpTip label="Total orders" text="How many separate orders we're showing results for in this batch." />
          </div>
          <div className="flex items-center gap-1.5 text-[13px] text-[var(--text-muted)]">
            <I.CircleCheck size={14} className="text-[var(--ok)]" />
            <span className="tabular-nums text-[var(--text)] font-medium">{success}</span> succeeded
          </div>
          <div className="flex items-center gap-1.5 text-[13px] text-[var(--text-muted)]">
            <I.CircleX size={14} className={error > 0 ? "text-[var(--err)]" : "text-[var(--text-faint)]"} />
            <span className="tabular-nums text-[var(--text)] font-medium">{error}</span> failed
          </div>
          {running > 0 && (
            <div className="flex items-center gap-1.5 text-[13px] text-[var(--text-muted)]">
              <I.Loader size={14} className="text-blue-400" />
              <span className="tabular-nums text-[var(--text)] font-medium">{running}</span> running
            </div>
          )}
          <div className="h-6 w-px bg-[var(--border)]" />
          <div className="min-w-0">
            <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium leading-none inline-flex items-center gap-1.5">
              <span>Combined</span>
              <HelpTip label="Combined estimated time" text="All the per-order estimates added together — roughly how long all of these panels would take in total." />
            </div>
            <div className="mt-1 text-[18px] font-semibold text-[var(--text)] tabular-nums leading-none">{eFormatSeconds(aggregateSec)}</div>
            {success > 0 && (
              <div className="mt-1 text-[11.5px] text-[var(--text-faint)] leading-none">estimated time for {success} {success === 1 ? "order" : "orders"}</div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button type="button" onClick={onToggleAll}
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md text-[12.5px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] border border-[var(--border)] transition-colors">
            {allCollapsed ? <I.ChevDown size={13} /> : <I.ChevUp size={13} />}
            {allCollapsed ? "Expand all" : "Collapse all"}
          </button>
          <button type="button" onClick={onExportCsv} disabled={success === 0}
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md text-[12.5px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] border border-[var(--border)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
            <I.FileText size={13} />
            Export CSV
          </button>
          <button type="button" onClick={onExportPdf} disabled={success === 0}
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md text-[12.5px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] border border-[var(--border)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
            <I.FileUp size={13} />
            Export PDF
          </button>
          <button type="button" onClick={onClear}
            title="Clear all results"
            className="h-9 w-9 inline-flex items-center justify-center rounded-md text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] border border-[var(--border)] transition-colors">
            <I.X size={14} />
          </button>
        </div>
      </div>
    </Card>
  );
}

function eGroupResultItems(items) {
  // Returns { displayItems, mergedCount }
  // - Key items always pass through individually (already deduped at submit).
  // - PDF items, once all batch items are settled, group by extracted op key
  //   (response.key, falling back to OP-pattern parsed from filename).
  const allSettled = items.length > 0 && items.every(it => it.state === "success" || it.state === "error");
  if (!allSettled || items.length === 0) {
    return { displayItems: items.map(it => ({ ...it, memberIds: [it.id] })), mergedCount: 0 };
  }
  const buckets = new Map();
  const order = [];
  for (const it of items) {
    let groupKey;
    if (it.kind === "pdf") {
      if (it.state === "success" && it.result && it.result.key) {
        groupKey = "k:" + eNormalizeKey(it.result.key);
      } else {
        const fromName = eExtractOpFromFilename(it.label);
        groupKey = fromName ? "k:" + fromName : "i:" + it.id;
      }
    } else {
      groupKey = "i:" + it.id;
    }
    if (!buckets.has(groupKey)) { buckets.set(groupKey, []); order.push(groupKey); }
    buckets.get(groupKey).push(it);
  }
  let mergedCount = 0;
  const displayItems = order.map(gk => {
    const group = buckets.get(gk);
    if (group.length === 1) {
      const it = group[0];
      return { ...it, memberIds: [it.id] };
    }
    mergedCount += group.length - 1;
    const success = group.find(g => g.state === "success");
    const anchor = success || group[0];
    const allErrored = !success;
    return {
      id: anchor.id,
      kind: "pdf",
      label: anchor.label,
      state: allErrored ? "error" : "success",
      result: success ? success.result : null,
      error: success ? null : anchor.error,
      expanded: anchor.expanded,
      members: group.map(g => ({
        id: g.id,
        label: g.label,
        state: g.state,
        error: g.error,
        size: g.file && g.file.size
      })),
      memberIds: group.map(g => g.id)
    };
  });
  return { displayItems, mergedCount };
}

function PredictTab({ server }) {
  const [entries, setEntries] = useStateE([{ id: eRid(), kind: "key", value: "", file: null }]);
  const [items, setItems] = useStateE([]);
  const [keyMergedCount, setKeyMergedCount] = useStateE(0);
  const [running, setRunning] = useStateE(false);
  const [visibleCount, setVisibleCount] = useStateE(20);
  const [copied, setCopied] = useStateE(false);
  const [submitError, setSubmitError] = useStateE(null);
  const itemsRef = useRefE(items);
  itemsRef.current = items;
  const sentinelRef = useRefE(null);

  function patchItem(id, patch) {
    setItems(prev => prev.map(it => it.id === id ? (typeof patch === "function" ? patch(it) : { ...it, ...patch }) : it));
  }

  function shouldStartCollapsed(totalCount) { return totalCount > 3; }

  async function runOneItem(it) {
    try {
      let data;
      if (it.kind === "pdf") {
        const fd = new FormData();
        fd.append("file", it.file);
        data = await eApiMultipart(server, "/predict/pdf", fd);
      } else {
        data = await eApi(server, "/predict", { method: "POST", body: { key: it.key, prefer: "skops" } });
      }
      const total = itemsRef.current.length;
      patchItem(it.id, { state: "success", result: data, error: null, expanded: !shouldStartCollapsed(total) });
    } catch (e) {
      patchItem(it.id, { state: "error", error: e, expanded: true });
    }
  }

  async function runBatch(batchItems) {
    setRunning(true);
    setVisibleCount(20);
    setCopied(false);
    const queue = batchItems.slice();
    const workers = Array.from({ length: Math.min(4, queue.length) }, async () => {
      while (queue.length > 0) {
        const next = queue.shift();
        patchItem(next.id, { state: "running" });
        await runOneItem(next);
      }
    });
    await Promise.all(workers);
    setRunning(false);
  }

  function submit() {
    setSubmitError(null);
    const valid = entries.filter(r => (r.kind === "pdf" && r.file) || (r.kind === "key" && r.value.trim()));
    if (!valid.length) { setSubmitError("Add at least one order number or BOM PDF."); return; }
    const seenKeys = new Map();
    let keyMerged = 0;
    const newItems = [];
    for (const r of valid) {
      if (r.kind === "pdf") {
        newItems.push({
          id: eRid(), kind: "pdf", file: r.file, label: r.file.name,
          state: "pending", result: null, error: null, expanded: false
        });
      } else {
        const trimmed = r.value.trim();
        const norm = eNormalizeKey(trimmed);
        if (seenKeys.has(norm)) { keyMerged++; continue; }
        seenKeys.set(norm, trimmed);
        newItems.push({
          id: eRid(), kind: "key", key: trimmed, label: trimmed,
          state: "pending", result: null, error: null, expanded: false
        });
      }
    }
    setKeyMergedCount(keyMerged);
    setItems(newItems);
    runBatch(newItems);
  }

  async function retryItem(id) {
    const it = itemsRef.current.find(x => x.id === id);
    if (!it) return;
    patchItem(id, { state: "running", error: null, expanded: false });
    await runOneItem(it);
  }

  function toggleItem(displayItem) {
    const memberIds = displayItem.memberIds || [displayItem.id];
    const next = !displayItem.expanded;
    setItems(prev => prev.map(it => memberIds.includes(it.id) ? { ...it, expanded: next } : it));
  }

  const { displayItems, mergedCount: pdfMergedCount } = eGroupResultItems(items);
  const totalMerged = keyMergedCount + pdfMergedCount;

  const allCollapsed = displayItems.length > 0 && displayItems.every(it => !it.expanded);
  function toggleAll() {
    const next = allCollapsed;
    setItems(prev => prev.map(it => ({ ...it, expanded: next })));
  }

  function exportCsv() { eExportCsv(itemsRef.current); }
  function exportPdf() { eExportPdf(itemsRef.current); }

  function clearAll() {
    setItems([]);
    setKeyMergedCount(0);
    setVisibleCount(20);
    setCopied(false);
  }

  useEffectE(() => {
    if (!sentinelRef.current) return;
    const el = sentinelRef.current;
    const obs = new IntersectionObserver((es) => {
      for (const e of es) {
        if (e.isIntersecting) setVisibleCount(v => Math.min(v + 20, displayItems.length));
      }
    }, { rootMargin: "200px" });
    obs.observe(el);
    return () => obs.disconnect();
  }, [displayItems.length, visibleCount]);

  const submitCount = entries.filter(r => (r.kind === "pdf" && r.file) || (r.kind === "key" && r.value.trim())).length;
  const visibleItems = displayItems.slice(0, visibleCount);
  const remaining = Math.max(0, displayItems.length - visibleItems.length);

  return (
    <div>
      <PageHeader
        title="Predictor"
        subtitle="Predict per-operation durations for one or many production orders."
        tooltip="Type a production order number (or attach its BOM drawing PDF) and we'll estimate how long each step takes to build that panel."
        about={
          <p>
            Type a production order number (for example, <span className="font-mono text-[var(--text)]">OP-2026-001</span>), or attach the BOM drawing PDF and we'll read the number for you. The program will then estimate how long each manufacturing step should take for that panel. The numbers come from a program that learned by watching many past orders — they're smart estimates, not guarantees.
          </p>
        }
      />

      <Card className="mb-5">
        <UnifiedEntriesInput entries={entries} onChange={setEntries} disabled={running} />

        <div className="mt-5 flex items-center justify-end gap-3 flex-wrap">
          <HelpTip label="Run predictions" text="Ask the program to estimate the time for every order or PDF in the list above. Each one gets its own result card below." />
          <RunPredictionsButton count={submitCount} loading={running} onClick={submit} />
        </div>

        {submitError && (
          <div className="mt-3 flex items-start gap-2.5 px-4 py-3 rounded-lg border border-[var(--warn)]/30 bg-[var(--warn)]/8 text-[13px] text-[var(--text)]">
            <I.CircleAlert size={16} className="text-[var(--warn)] mt-0.5 shrink-0" />
            <div className="flex-1">{submitError}</div>
          </div>
        )}
      </Card>

      {displayItems.length > 0 && (
        <div className="space-y-4">
          <BatchSummaryBar
            items={displayItems}
            mergedCount={totalMerged}
            allCollapsed={allCollapsed}
            onToggleAll={toggleAll}
            onExportCsv={exportCsv}
            onExportPdf={exportPdf}
            onClear={clearAll}
          />

          {keyMergedCount > 0 && (
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/50 text-[12.5px] text-[var(--text-muted)]">
              <I.Merge size={14} className="text-[var(--text-faint)]" />
              <span>{keyMergedCount} duplicate order {keyMergedCount === 1 ? "number was" : "numbers were"} merged.</span>
            </div>
          )}
          {pdfMergedCount > 0 && (
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/50 text-[12.5px] text-[var(--text-muted)]">
              <I.Merge size={14} className="text-[var(--text-faint)]" />
              <span>{pdfMergedCount} duplicate {pdfMergedCount === 1 ? "PDF was" : "PDFs were"} merged into existing orders.</span>
            </div>
          )}

          <div className="space-y-2.5">
            {visibleItems.map(it => (
              <ResultCard key={it.id} item={it} onToggle={toggleItem} onRetry={retryItem} />
            ))}
            {remaining > 0 && (
              <div ref={sentinelRef} className="py-3 text-center text-[12px] text-[var(--text-muted)] border-t border-[var(--border-soft)]">
                {remaining} more below
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}



/* ============================================================
 * SCHEDULE COUNTDOWN
 * ============================================================ */
function useNextSchedule(server) {
  const [state, setState] = useStateE({ loading: true, error: null, nextAt: null, raw: null });
  const refresh = useCallback(async () => {
    try {
      const raw = await eApi(server, "/schedule");
      const data = Array.isArray(raw) ? raw[0] || null : raw && Array.isArray(raw.items) ? raw.items[0] : raw;
      const nextAt = eParseScheduleTime(data);
      setState({ loading: false, error: nextAt ? null : "No upcoming run reported.", nextAt, raw: data });
    } catch (e) {
      setState({ loading: false, error: eErrorMessage(e, "schedule"), nextAt: null, raw: null });
    }
  }, [server]);
  useEffectE(() => {
    setState((s) => ({ ...s, loading: true }));refresh();
    const id = setInterval(refresh, 60000);
    return () => clearInterval(id);
  }, [refresh]);
  return { ...state, refresh };
}
function useCountdown(targetMs) {
  const [now, setNow] = useStateE(() => Date.now());
  useEffectE(() => {
    if (!targetMs) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [targetMs]);
  if (!targetMs) return null;
  return Math.max(0, targetMs - now);
}
function eCountdownParts(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return { days: Math.floor(s / 86400), hours: Math.floor(s % 86400 / 3600), mins: Math.floor(s % 3600 / 60), secs: s % 60, total: s };
}

function CountdownUnit({ value, label, size = "lg" }) {
  const num = size === "sm" ? "text-[26px] sm:text-[28px]" : "text-[32px] sm:text-[40px]";
  const lbl = size === "sm" ? "text-[10px] mt-1" : "text-[11px] mt-2";
  return (
    <div className="flex flex-col items-center">
      <div className={num + " font-semibold tracking-tight text-[var(--text)] tabular-nums leading-none"}>
        {String(value).padStart(2, "0")}
      </div>
      <div className={lbl + " uppercase tracking-wider text-[var(--text-muted)]"}>{label}</div>
    </div>);

}
function Sep({ size = "lg" }) {
  const c = size === "sm"
    ? "text-[22px] pb-4"
    : "text-[28px] sm:text-[34px] pb-6";
  return <div className={c + " text-[var(--text-faint)] font-light leading-none select-none"}>:</div>;
}

function ScheduleCard({ server, compact = false }) {
  const { loading, error, nextAt, raw, refresh } = useNextSchedule(server);
  const remainingMs = useCountdown(nextAt);
  const overdue = nextAt && remainingMs === 0;
  const parts = remainingMs != null ? eCountdownParts(remainingMs) : null;

  const cron = raw && (raw.cron || raw.cadence || raw.schedule || raw.interval);
  const source = raw && (raw.source || raw.workflow || raw.workflow_name || raw.trigger);
  const updated = raw && raw.updated_at;

  const headerPad = compact ? "px-5 py-3" : "px-6 py-4";
  const bodyPad = compact ? "px-5 py-4" : "px-6 py-6";
  const gap = compact ? "gap-5" : "gap-8";
  const digitGap = compact ? "gap-2 sm:gap-3" : "gap-3 sm:gap-5";

  return (
    <Card padded={false} className="overflow-hidden">
      <div className={headerPad + " border-b border-[var(--border)] flex items-center justify-between gap-3"}>
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="h-9 w-9 rounded-md bg-[var(--accent)]/12 text-[var(--accent-hover)] flex items-center justify-center shrink-0">
            <I.Calendar size={16} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[14px] font-semibold text-[var(--text)] truncate inline-flex items-center gap-1.5">
              <span>Next automated retrain</span>
              <HelpTip label="Next automated retrain" text="The next time the program will learn on its own. You don't have to do anything before then — it just happens." />
            </div>
            <div className="text-[12px] text-[var(--text-muted)] mt-0.5 truncate">Triggered automatically — no action needed</div>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={refresh} loading={loading} icon={<I.Refresh size={13} />}>Refresh</Button>
      </div>

      <div className={bodyPad}>
        {loading &&
        <div className="flex items-center gap-2.5 text-[13px] text-[var(--text-muted)]">
            <I.Loader size={15} className="text-[var(--accent-hover)]" /> Loading schedule…
          </div>
        }

        {!loading && error &&
        <div className="flex items-center gap-2.5 text-[13px] text-[var(--text-muted)]">
            <I.CircleAlert size={15} className="text-[var(--warn)]" /> {error}
          </div>
        }

        {!loading && !error && nextAt &&
        <div className={"grid grid-cols-1 lg:grid-cols-[auto_1fr] items-center " + gap}>
            {overdue ?
          <div className="text-[20px] font-semibold text-[var(--warn)]">Cycle running now…</div> :

          <div className={"flex items-end " + digitGap}>
                <CountdownUnit value={parts.days} label="Days" size={compact ? "sm" : "lg"} />
                <Sep size={compact ? "sm" : "lg"} />
                <CountdownUnit value={parts.hours} label="Hours" size={compact ? "sm" : "lg"} />
                <Sep size={compact ? "sm" : "lg"} />
                <CountdownUnit value={parts.mins} label="Minutes" size={compact ? "sm" : "lg"} />
                <Sep size={compact ? "sm" : "lg"} />
                <CountdownUnit value={parts.secs} label="Seconds" size={compact ? "sm" : "lg"} />
              </div>
          }

            {compact ? (
              <div className="grid grid-cols-3 gap-x-4 lg:border-l lg:border-[var(--border)] lg:pl-5">
                <Meta k="Target" v={nextAt ? eFormatAbs(nextAt) : "—"} accent stacked />
                <Meta k="Source" v={source || "—"} stacked />
                <Meta k="Last sync" v={updated ? eFormatAbs(updated) : "—"} stacked />
              </div>
            ) : (
            <div className="flex flex-col gap-4 lg:border-l lg:border-[var(--border)] lg:pl-8 self-stretch justify-center">
              <Meta k="Target" v={nextAt ? eFormatAbs(nextAt) : "—"} hint="UTC" accent />
              <div className="h-px bg-[var(--border-soft)]" />
              <Meta k="Source" v={source || "—"} />
              <div className="h-px bg-[var(--border-soft)]" />
              <Meta k="Last sync" v={updated ? eFormatAbs(updated) : "—"} hint={updated ? eTimeAgo(updated) : null} />
            </div>
            )}
          </div>
        }
      </div>
    </Card>);

}
function Meta({ k, v, hint, accent, mono, stacked }) {
  if (stacked) {
    return (
      <div className="min-w-0">
        <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">{k}</div>
        <div className={"mt-1 text-[13.5px] truncate " + (accent ? "text-[var(--accent-hover)] font-medium" : "text-[var(--text)]") + (mono ? " font-mono tabular-nums" : "")}>{v}</div>
      </div>
    );
  }
  return (
    <div className="flex items-baseline justify-between gap-4">
      <div className="text-[12px] uppercase tracking-wider text-[var(--text-muted)] font-medium shrink-0">{k}</div>
      <div className="text-right min-w-0">
        <div className={"text-[14px] " + (accent ? "text-[var(--accent-hover)] font-medium" : "text-[var(--text)]") + (mono ? " font-mono tabular-nums" : "")}>{v}</div>
        {hint && <div className="text-[11.5px] text-[var(--text-faint)] mt-0.5">{hint}</div>}
      </div>
    </div>);

}

/* ============================================================
 * RETRAIN
 * ============================================================ */
const E_TERMINAL = ["completed", "failed", "succeeded", "rejected", "deployed", "done"];
function isTerminal(status) {
  if (!status) return false;
  return E_TERMINAL.some((s) => String(status).toLowerCase().includes(s));
}

function NumberStepper({ value, onChange, min = 1, max, disabled }) {
  function step(d) {
    let next = Math.max(min, (value || min) + d);
    if (max != null) next = Math.min(max, next);
    onChange(next);
  }
  return (
    <div className={"inline-flex items-stretch rounded-md border border-[var(--border)] bg-[var(--surface-2)] " + (disabled ? "opacity-50" : "")}>
      <button type="button" onClick={() => step(-1)} disabled={disabled}
      className="h-10 w-10 flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)] disabled:cursor-not-allowed transition-colors">
        <I.Minus size={14} />
      </button>
      <input
        type="number" min={min} max={max} value={value} disabled={disabled}
        onChange={(e) => {
          let v = +e.target.value || min;
          v = Math.max(min, v);
          if (max != null) v = Math.min(max, v);
          onChange(v);
        }}
        className="w-16 h-10 bg-transparent text-center text-[14px] text-[var(--text)] tabular-nums outline-none border-x border-[var(--border)] focus:bg-[var(--bg)]" />
      
      <button type="button" onClick={() => step(1)} disabled={disabled}
      className="h-10 w-10 flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)] disabled:cursor-not-allowed transition-colors">
        <I.Plus size={14} />
      </button>
    </div>);

}

function Segmented({ value, onChange, options }) {
  return (
    <div className="inline-flex p-1 rounded-md bg-[var(--surface-2)] border border-[var(--border)]">
      {options.map((o) =>
      <button key={o.value} type="button" onClick={() => onChange(o.value)}
      className={"h-8 px-3.5 rounded text-[13px] font-medium transition-colors " + (
      value === o.value ?
      "bg-[var(--accent)] text-white" :
      "text-[var(--text-muted)] hover:text-[var(--text)]")}>
          {o.label}
        </button>
      )}
    </div>);

}

function Modal({ open, onClose, children, maxWidth = "max-w-md" }) {
  useEffectE(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") onClose && onClose(); };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = prev; };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className={"relative w-full " + maxWidth + " rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-2xl"} role="dialog" aria-modal="true">
        {children}
      </div>
    </div>);
}

function ConfirmRetrainDialog({ open, onCancel, onConfirm, useSimulated, trials, requireImprovement, skipBenchmark, skipTests, simOutcome, simSeconds }) {
  const summary = useSimulated ? [
    { k: "Mode", v: "Simulated run", accent: true },
    { k: "Outcome", v: simOutcome.charAt(0).toUpperCase() + simOutcome.slice(1) },
    { k: "Duration", v: `${simSeconds} seconds` },
  ] : [
    { k: "Mode", v: "Real retrain", accent: true },
    { k: "Trials", v: String(trials) },
    { k: "Require improvement", v: requireImprovement ? "Yes" : "No" },
    { k: "Skip benchmark", v: skipBenchmark ? "Yes" : "No" },
    { k: "Skip tests", v: skipTests ? "Yes" : "No" },
  ];

  return (
    <Modal open={open} onClose={onCancel} maxWidth="max-w-lg">
      <div className="px-6 py-5 border-b border-[var(--border)] flex items-start gap-3">
        <div className={"h-10 w-10 rounded-lg flex items-center justify-center shrink-0 " + (useSimulated ? "bg-[var(--accent)]/12 text-[var(--accent-hover)]" : "bg-[var(--warn)]/12 text-[var(--warn)]")}>
          {useSimulated ? <I.Cpu size={18} /> : <I.CircleAlert size={18} />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[16px] font-semibold text-[var(--text)] leading-tight">
            {useSimulated ? "Start simulated run?" : "Start real retrain?"}
          </div>
          <div className="text-[13px] text-[var(--text-muted)] mt-1">
            {useSimulated
              ? "This validates orchestration without executing the real training pipeline."
              : "Real retrains take 30 minutes or more and will consume compute. Review the parameters below before continuing."}
          </div>
        </div>
      </div>

      <div className="px-6 py-4">
        <div className="rounded-lg border border-[var(--border)] divide-y divide-[var(--border)] overflow-hidden">
          {summary.map((row) => (
            <div key={row.k} className="flex items-center justify-between gap-4 px-4 py-2.5">
              <div className="text-[12.5px] text-[var(--text-muted)] uppercase tracking-wider font-medium">{row.k}</div>
              <div className={"text-[13.5px] " + (row.accent ? "text-[var(--accent-hover)] font-medium" : "text-[var(--text)]")}>{row.v}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="px-6 py-4 border-t border-[var(--border)] flex items-center justify-end gap-2">
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} icon={<I.Cpu size={15}/>}>
          {useSimulated ? "Yes, start simulated run" : "Yes, start retrain"}
        </Button>
      </div>
    </Modal>
  );
}

function RetrainTab({ server, onJobFinished }) {
  const [trials, setTrials] = useStateE(80);
  const [requireImprovement, setRequireImprovement] = useStateE(true);
  const [skipBenchmark, setSkipBenchmark] = useStateE(false);
  const [skipTests, setSkipTests] = useStateE(false);
  const [useSimulated, setUseSimulated] = useStateE(false);
  const [simOutcome, setSimOutcome] = useStateE("deployed");
  const [simSeconds, setSimSeconds] = useStateE(15);

  const [submitting, setSubmitting] = useStateE(false);
  const [error, setError] = useStateE(null);
  const [job, setJob] = useStateE(null);
  const [elapsed, setElapsed] = useStateE(0);
  const pollRef = useRefE(null);
  const tickRef = useRefE(null);

  useEffectE(() => {
    if (!job || isTerminal(job.status)) {clearInterval(tickRef.current);return;}
    const startedAt = job.started_at ? new Date(job.started_at).getTime() : Date.now();
    tickRef.current = setInterval(() => setElapsed(Math.max(0, (Date.now() - startedAt) / 1000)), 200);
    return () => clearInterval(tickRef.current);
  }, [job && job.job_id, job && job.status]);

  useEffectE(() => {
    if (!job || !job.job_id || isTerminal(job.status)) return;
    let cancelled = false;
    async function tick() {
      try {
        const data = await eApi(server, "/retrain/" + encodeURIComponent(job.job_id));
        if (cancelled) return;
        setJob((j) => ({ ...j, ...data }));
        if (isTerminal(data.status)) {onJobFinished && onJobFinished();return;}
      } catch (_) {}
      if (!cancelled) pollRef.current = setTimeout(tick, 2000);
    }
    pollRef.current = setTimeout(tick, 1200);
    return () => {cancelled = true;clearTimeout(pollRef.current);};
  }, [job && job.job_id, job && job.status]);

  async function startRetrain() {
    setError(null);setSubmitting(true);
    const body = useSimulated ?
    { dry_run: true, dry_run_outcome: simOutcome, dry_run_seconds: simSeconds } :
    { dry_run: false, trials, require_improvement: requireImprovement, skip_benchmark: skipBenchmark, skip_tests: skipTests };
    try {
      const data = await eApi(server, "/retrain", { method: "POST", body });
      setJob({ ...data, started_at: data.started_at || new Date().toISOString() });
      setElapsed(0);
    } catch (e) {setError(eErrorMessage(e, "retrain"));} finally
    {setSubmitting(false);}
  }

  const [confirmOpen, setConfirmOpen] = useStateE(false);
  function requestStart() { setConfirmOpen(true); }
  async function confirmStart() {
    setConfirmOpen(false);
    await startRetrain();
  }

  const expected = useSimulated ? simSeconds : 30 * 60;
  const progress = job ? isTerminal(job.status) ? 100 : Math.min(95, elapsed / expected * 100) : 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0">
          <h1 className="text-[20px] font-semibold tracking-tight text-[var(--text)] leading-tight inline-flex items-center gap-2">
            <span>Training</span>
            <HelpTip size={16} label="Training" text="This page lets you trigger the program's learning manually. Most of the time you won't need to — it runs by itself once a month." />
          </h1>
          <p className="mt-0.5 text-[13px] text-[var(--text-muted)]">Refit the deployed model on the latest training data.</p>
        </div>
        <Button onClick={requestStart} loading={submitting} disabled={submitting || job && !isTerminal(job.status)}
          icon={<I.Cpu size={16} />} size="md">
          {useSimulated ? "Start simulated run" : "Start retrain"}
        </Button>
      </div>

      <AboutPanel
        body={
          <span>
            Every so often the program needs to learn from the most recent orders so its estimates stay accurate. This page lets you start that learning manually. Most of the time you won't need to — it runs by itself once a month. A real training takes about 30 minutes; use <span className="font-medium text-[var(--text)]">"simulated run"</span> to test the buttons without waiting.
          </span>
        }
      />

      <ScheduleCard server={server} compact />

      <Card padded={false}>
        <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between gap-2">
          <div className="text-[14px] font-semibold text-[var(--text)] inline-flex items-center gap-1.5">
            <span>Training parameters</span>
            <HelpTip label="Training parameters" text="Settings the program uses while it learns. The defaults are sensible — change them only if you know what you're doing." />
          </div>
          <div className="flex items-center gap-2">
            {useSimulated && <Badge tone="blue">Test mode on</Badge>}
          </div>
        </div>

        <div className={"px-5 py-4 grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 " + (useSimulated ? "opacity-50 pointer-events-none" : "")}>
          <Field
            label="Trials"
            tooltip="How many different settings the program will try before picking the best one. More trials = a better result, but a longer wait. 80 is the usual sweet spot.">
            <NumberStepper value={trials} onChange={setTrials} min={1} disabled={useSimulated} />
          </Field>
          <div className="self-end">
            <ToggleRow
              title="Require improvement"
              tooltip="Safety net. If the new program turns out worse than the one in use, throw the new one away and keep the existing one. Leave this ON."
              checked={requireImprovement}
              onChange={setRequireImprovement} />
          </div>
          <ToggleRow
            title="Skip benchmark"
            tooltip="Advanced. Skip the part where the program tries lots of settings, and just retrain with the last winner. Only useful if you ran a full training very recently."
            checked={skipBenchmark}
            onChange={setSkipBenchmark} />
          <ToggleRow
            title="Skip tests"
            tooltip="Advanced. Skip the safety checks at the end. Don't tick this unless someone specifically tells you to."
            checked={skipTests}
            onChange={setSkipTests} />
        </div>

        <div className="px-5 py-3 border-t border-[var(--border)] bg-[var(--surface-2)]/30 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Toggle checked={useSimulated} onChange={setUseSimulated} srLabel="Use simulated run" />
            <span className="text-[13px] text-[var(--text)] inline-flex items-center gap-1.5">
              <span>Test mode (simulated run)</span>
              <HelpTip label="Test mode (simulated run)" text="Pretend to train for a few seconds without doing any real work. Use this to check that the buttons and messages behave as expected. Always OFF for a real training." />
            </span>
          </div>

          {useSimulated && (
            <div className="flex items-center gap-3 ml-auto flex-wrap">
              <span className="inline-flex items-center gap-1.5 text-[12.5px] text-[var(--text-muted)]">
                Outcome
                <HelpTip label="Simulated outcome" text="What pretend ending you'd like to see: a successful deployment, a rejected one, or a failed one. Useful for previewing each kind of result." />
              </span>
              <Segmented
                value={simOutcome}
                onChange={setSimOutcome}
                options={[
                  { value: "deployed", label: "Deployed" },
                  { value: "rejected", label: "Rejected" },
                  { value: "failed", label: "Failed" }]
                } />
              <span className="inline-flex items-center gap-1.5 text-[12.5px] text-[var(--text-muted)]">
                Duration
                <HelpTip label="Simulated duration" text="How long the pretend training should take before showing the result. Between 5 and 120 seconds." />
              </span>
              <div className="flex items-center gap-2">
                <NumberStepper value={simSeconds} onChange={setSimSeconds} min={5} max={120} />
                <span className="text-[12.5px] text-[var(--text-muted)]">sec</span>
              </div>
            </div>
          )}
        </div>
      </Card>

      {error && <InlineError message={error} />}

      {job && <JobCard job={job} elapsed={elapsed} progress={progress} />}

      <ConfirmRetrainDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={confirmStart}
        useSimulated={useSimulated}
        trials={trials}
        requireImprovement={requireImprovement}
        skipBenchmark={skipBenchmark}
        skipTests={skipTests}
        simOutcome={simOutcome}
        simSeconds={simSeconds}
      />
    </div>);

}

function JobCard({ job, elapsed, progress }) {
  const [showDetails, setShowDetails] = useStateE(false);
  const status = (job.status || "").toLowerCase();
  const terminal = isTerminal(status);
  const deployed = job.deployed === true || /deployed/.test(status);
  const failed = /failed|error/.test(status) || terminal && job.error;
  const rejected = terminal && !deployed && !failed;

  const mae = job?.train_report?.mae ?? job?.train_report?.MAE ?? job?.mae;
  const modelName = job?.train_report?.model_name || job?.model_name || job?.model;

  let badge;
  if (!terminal) badge = <Badge tone="blue" icon={<I.Loader size={11} />}>Running</Badge>;else
  if (deployed) badge = <Badge tone="ok" icon={<I.BadgeCheck size={11} />}>Deployed</Badge>;else
  if (rejected) badge = <Badge tone="warn" icon={<I.Shield size={11} />}>Rejected</Badge>;else
  badge = <Badge tone="err" icon={<I.Octagon size={11} />}>Failed</Badge>;

  return (
    <Card padded={false}>
      <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between gap-4 flex-wrap">
        <div className="flex-1 min-w-0">
          <div className="text-[12.5px] text-[var(--text-muted)]">Current job</div>
          <div className="mt-0.5 text-[14px] font-mono text-[var(--text)] truncate">{job.job_id}</div>
        </div>
        <div className="text-[12.5px] text-[var(--text-muted)]">
          Started <span className="text-[var(--text)] font-mono">{eFormatAbs(job.started_at)}</span>
        </div>
        {badge}
      </div>

      <div className="px-6 py-5">
        {!terminal &&
        <div>
            <ProgressBar value={progress} />
            <div className="flex items-center justify-between text-[12.5px] text-[var(--text-muted)] mt-3 tabular-nums">
              <span>Elapsed <span className="text-[var(--text)]">{eFormatSeconds(elapsed)}</span></span>
              <span>~{Math.round(progress)}%</span>
            </div>
          </div>
        }

        {terminal && (deployed || rejected) &&
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <MetricTile label="Outcome" value={deployed ? "Model deployed" : "Candidate rejected"} tone={deployed ? "ok" : "warn"} />
            <MetricTile label="Candidate MAE" value={mae != null ? typeof mae === "number" ? mae.toFixed(3) : String(mae) : "—"} mono />
            <MetricTile label="Model" value={modelName || "—"} mono />
          </div>
        }

        {terminal && failed &&
        <div>
            <div className="flex items-start gap-3 p-4 rounded-lg bg-[var(--err)]/8 border border-[var(--err)]/25">
              <I.Octagon size={18} className="text-[var(--err)] mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-[14px] font-medium text-[var(--text)]">Retrain failed</div>
                <div className="text-[12.5px] text-[var(--text-muted)] mt-1">Production model unchanged. Inspect details before retrying.</div>
              </div>
            </div>
            <button onClick={() => setShowDetails((v) => !v)}
          className="mt-3 inline-flex items-center gap-1.5 text-[12.5px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
              <I.ChevDown size={14} className={"transition-transform duration-150 " + (showDetails ? "rotate-180" : "")} />
              {showDetails ? "Hide details" : "Show details"}
            </button>
            {showDetails &&
          <div className="mt-3 space-y-3">
                {job.error && <PreBlock label="Error" content={String(job.error)} />}
                {job.stderr_tail && <PreBlock label="stderr" content={String(job.stderr_tail)} max />}
              </div>
          }
          </div>
        }
      </div>
    </Card>);

}

function PreBlock({ label, content, max }) {
  return (
    <div>
      <div className="text-[11.5px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-1.5">{label}</div>
      <pre className={"text-[12px] font-mono bg-[var(--bg)] border border-[var(--border)] rounded-md p-3 text-[var(--text-muted)] whitespace-pre-wrap break-words " + (max ? "overflow-auto max-h-72" : "")}>{content}</pre>
    </div>);

}

function MetricTile({ label, value, tone, mono }) {
  const colors = tone === "ok" ? "text-[var(--ok)]" : tone === "warn" ? "text-[var(--warn)]" : "text-[var(--text)]";
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/50 p-4">
      <div className="text-[11.5px] uppercase tracking-wider text-[var(--text-muted)] font-medium">{label}</div>
      <div className={"mt-2 text-[15px] font-medium " + colors + (mono ? " font-mono tabular-nums" : "")}>{value}</div>
    </div>);

}

/* ============================================================
 * HISTORY
 * ============================================================ */
function HistoryTab({ server, reloadKey }) {
  const [loading, setLoading] = useStateE(true);
  const [error, setError] = useStateE(null);
  const [items, setItems] = useStateE([]);

  async function load() {
    setLoading(true);setError(null);
    try {
      const data = await eApi(server, "/retrain/log?limit=20");
      const arr = Array.isArray(data) ? data : data.items || data.log || data.runs || [];
      setItems(arr);
    } catch (e) {setError(eErrorMessage(e, "history"));} finally
    {setLoading(false);}
  }
  useEffectE(() => {load(); /* eslint-disable-next-line */}, [server, reloadKey]);

  return (
    <div>
      <PageHeader
        title="History"
        subtitle="The most recent 20 retrain jobs and their outcomes."
        tooltip="Every time we taught the program new tricks shows up here."
        about={
          <p>
            A log of every time the program has been taught new tricks. Each row shows <span className="font-medium text-[var(--text)]">when</span> the training ran, which <span className="font-medium text-[var(--text)]">version</span> was tried, how accurate it turned out, and whether we <span className="font-medium text-[var(--text)]">kept it</span>.
          </p>
        }
        action={<Button variant="secondary" onClick={load} loading={loading} icon={<I.Refresh size={15} />}>Refresh</Button>} />
      

      <Card padded={false}>
        {loading &&
        <div className="p-6 flex items-center gap-2.5 text-[13px] text-[var(--text-muted)]"><I.Loader size={15} /> Loading history…</div>
        }
        {!loading && error && <div className="p-6"><InlineError message={error} /></div>}
        {!loading && !error && items.length === 0 &&
        <div className="px-6 py-16 text-center">
            <div className="mx-auto h-12 w-12 rounded-full bg-[var(--surface-2)] flex items-center justify-center text-[var(--text-faint)]">
              <I.History size={20} />
            </div>
            <div className="mt-3 text-[14px] text-[var(--text)] font-medium">No retrains yet</div>
            <div className="text-[12.5px] text-[var(--text-muted)] mt-1">Jobs will appear here once you start a retrain.</div>
          </div>
        }

        {!loading && !error && items.length > 0 &&
        <div className="overflow-x-auto">
            <table className="w-full text-[13.5px]">
              <thead>
                <tr className="text-left text-[12.5px] font-medium text-[var(--text-muted)] border-b border-[var(--border)]">
                  <th className="px-6 py-3">
                    <span className="inline-flex items-center gap-1.5">
                      Timestamp
                      <HelpTip label="Timestamp" text="When the training ran. The smaller line below says roughly how long ago that was." />
                    </span>
                  </th>
                  <th className="px-6 py-3">
                    <span className="inline-flex items-center gap-1.5">
                      Model
                      <HelpTip label="Model" text="The internal nickname of the program version that was tried in this run." />
                    </span>
                  </th>
                  <th className="px-6 py-3 text-right w-32">
                    <span className="inline-flex items-center gap-1.5 justify-end w-full">
                      MAE
                      <HelpTip label="MAE — Mean Absolute Error" text="Mean Absolute Error. On average, how many seconds off the program's estimates were from real measurements. Smaller is better." />
                    </span>
                  </th>
                  <th className="px-6 py-3 w-40">
                    <span className="inline-flex items-center gap-1.5">
                      Outcome
                      <HelpTip label="Outcome" text="Deployed = the new version replaced the old one. Rejected = the new version was worse, so we kept the old one. Failed = something went wrong during training." />
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.slice().sort((a, b) => new Date(b.started_at || b.finished_at || 0) - new Date(a.started_at || a.finished_at || 0)).map((it, i) => {
                const status = (it.status || "").toLowerCase();
                const deployed = it.deployed === true || /deployed/.test(status);
                const failed = /failed|error/.test(status) || !!it.error;
                const rejected = !deployed && !failed && /completed|succeeded|done|rejected/.test(status);
                const when = it.finished_at || it.started_at;
                const mae = it?.train_report?.mae ?? it?.train_report?.MAE ?? it.mae;
                const modelName = it?.train_report?.model_name || it.model_name || it.model || "—";
                let badge;
                if (failed) badge = <Badge tone="err" icon={<I.Octagon size={11} />}>Failed</Badge>;else
                if (deployed) badge = <Badge tone="ok" icon={<I.BadgeCheck size={11} />}>Deployed</Badge>;else
                if (rejected) badge = <Badge tone="warn" icon={<I.Shield size={11} />}>Rejected</Badge>;else
                badge = <Badge tone="slate" icon={<I.Loader size={11} />}>{it.status || "Pending"}</Badge>;
                return (
                  <tr key={(it.job_id || it.id || i) + "-" + i} className="border-b border-[var(--border-soft)] last:border-b-0 hover:bg-[var(--surface-2)]/50 transition-colors">
                      <td className="px-6 py-3">
                        <div className="font-mono tabular-nums text-[var(--text)]">{eFormatAbs(when)}</div>
                        <div className="text-[11.5px] text-[var(--text-faint)] mt-0.5">{eTimeAgo(when)}</div>
                      </td>
                      <td className="px-6 py-3 font-mono text-[var(--text-muted)] truncate max-w-[260px]">{modelName}</td>
                      <td className="px-6 py-3 font-mono tabular-nums text-right text-[var(--text)]">
                        {mae != null ? typeof mae === "number" ? mae.toFixed(3) : String(mae) : "—"}
                      </td>
                      <td className="px-6 py-3">{badge}</td>
                    </tr>);

              })}
              </tbody>
            </table>
          </div>
        }
      </Card>
    </div>);

}

/* ============================================================
 * FUTURE VISION (separate page — fictitious data, what richer data unlocks)
 * ============================================================ */
function FutureSectionHead({ icon, title, note }) {
  return (
    <div className="flex items-start gap-2.5 mb-3">
      <div className="mt-0.5 text-[var(--accent-hover)] shrink-0">{icon}</div>
      <div>
        <div className="text-[15px] font-semibold text-[var(--text)]">{title}</div>
        {note && <div className="text-[12.5px] text-[var(--text-muted)] mt-0.5">{note}</div>}
      </div>
    </div>
  );
}

function FutureBreakdownBar({ breakdown }) {
  const seg = [
    { key: "Productive", sec: breakdown.productive_sec, pct: breakdown.productive_pct, color: "var(--ok)" },
    { key: "Material run (necessary)", sec: breakdown.material_necessary_sec, pct: breakdown.material_necessary_pct, color: "var(--warn)" },
    { key: "Idle (no value)", sec: breakdown.idle_no_value_sec, pct: breakdown.idle_no_value_pct, color: "var(--err)" },
  ];
  return (
    <div>
      <div className="flex h-6 w-full overflow-hidden rounded-md border border-[var(--border)]">
        {seg.map((s, i) => (
          <div key={i} title={`${s.key}: ${s.pct}%`} style={{ width: `${s.pct}%`, background: s.color }} />
        ))}
      </div>
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {seg.map((s, i) => (
          <div key={i} className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-full shrink-0" style={{ background: s.color }} />
              <span className="text-[12px] text-[var(--text-muted)]">{s.key}</span>
            </div>
            <div className="mt-1 text-[16px] font-semibold text-[var(--text)] tabular-nums">{s.pct}%</div>
            <div className="text-[11.5px] text-[var(--text-faint)] tabular-nums">{eFormatSeconds(s.sec)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FutureScenarioCards({ scenarios, unit }) {
  const totals = scenarios.map(s => s.total_sec);
  const best = Math.min(...totals), worst = Math.max(...totals);
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
      {scenarios.map((s, i) => {
        const isBest = s.total_sec === best, isWorst = s.total_sec === worst;
        const col = isBest ? "var(--ok)" : isWorst ? "var(--err)" : "var(--text)";
        const deltaPct = best > 0 ? Math.round((s.total_sec - best) / best * 100) : 0;
        return (
          <div key={i} className="rounded-lg border bg-[var(--surface)] px-3 py-3"
            style={{ borderColor: isBest ? "var(--ok)" : "var(--border)" }}>
            <div className="text-[12px] text-[var(--text-muted)]">{s.label}</div>
            <div className="mt-1 text-[18px] font-semibold tabular-nums" style={{ color: col }}>{eFormatSeconds(s.total_sec)}</div>
            <div className="text-[11.5px] tabular-nums mt-0.5" style={{ color: col }}>
              {isBest ? "best" : `+${deltaPct}% slower`}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function FutureScenarioBlock({ icon, title, note, data, xLabel, xUnit = "" }) {
  const pts = (data.curve && data.curve.length ? data.curve : data.scenarios)
    .map(s => ({ x: Number(s.value), y: s.total_sec }));
  const series = [{ pts, color: "var(--accent)" }];
  const xv = pts.map(p => p.x);
  const xTicks = xv.length ? [xv[0], xv[Math.floor(xv.length / 2)], xv[xv.length - 1]] : [];
  return (
    <Card className="mb-4">
      <FutureSectionHead icon={icon} title={title} note={note} />
      <FutureScenarioCards scenarios={data.scenarios} unit={data.unit} />
      <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg)]/40 px-2 pt-3">
        <MetricChart series={series} yUnit="s" xLabel={xLabel} xTicks={xTicks} xUnit={xUnit} yNice />
      </div>
    </Card>
  );
}

function FutureGeneralResult({ general }) {
  return (
    <Card className="mb-4">
      <FutureSectionHead
        icon={<I.Layers size={18} />}
        title="General model — predicted build time with waste exposed"
        note="The central estimate now separates productive work from two kinds of waste this richer data reveals."
      />
      <div className="mb-4 flex flex-wrap items-end gap-x-6 gap-y-1">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-[var(--text-muted)]">Total</div>
          <div className="text-[24px] font-semibold text-[var(--text)] tabular-nums leading-tight">{eFormatSeconds(general.total_sec)}</div>
        </div>
      </div>
      <FutureBreakdownBar breakdown={general.breakdown} />
      <div className="mt-4 flex items-start gap-2.5 px-4 py-3 rounded-lg border border-[var(--warn)]/30 bg-[var(--warn)]/8 text-[12.5px] text-[var(--text)]">
        <I.Info size={15} className="text-[var(--warn)] mt-0.5 shrink-0" />
        <div>
          <span className="font-medium">Optimization signal:</span> the <span className="text-[var(--warn)] font-medium">material run</span> is
          large and <span className="font-medium">consistent</span> (narrow interval) — a systematic loss you can cut by reorganizing
          material flow / kitting closer to the bench. The <span className="text-[var(--err)] font-medium">no-value idle</span> is
          <span className="font-medium"> random</span> (wide interval) — addressed through workflow discipline, not layout.
        </div>
      </div>
      <FutureOpTable items={general.items} />
    </Card>
  );
}

function FutureOpRow({ it }) {
  const waste = it.micro_op_num >= 15;
  return (
    <tr className="border-t border-[var(--border-soft)]">
      <td className="px-4 py-2 text-[var(--text)]">
        {waste && <span className="inline-block h-2 w-2 rounded-full mr-2 align-middle"
          style={{ background: it.micro_op_num === 16 ? "var(--warn)" : "var(--err)" }} />}
        <span className={waste ? "font-medium" : ""}>{it.micro_op_name}</span>
      </td>
      <td className="px-4 py-2 text-right tabular-nums text-[var(--text)] font-medium">{eFormatSeconds(it.point_sec)}</td>
      <td className="px-4 py-2 text-right tabular-nums text-[var(--text-muted)] text-[12px]">{eFormatSeconds(it.lo_sec)}–{eFormatSeconds(it.hi_sec)}</td>
    </tr>
  );
}

function FutureOpTable({ items }) {
  const [open, setOpen] = useStateE(false);
  const productive = items.filter(it => it.micro_op_num <= 14);
  const waste = items.filter(it => it.micro_op_num >= 15);
  return (
    <div className="mt-4">
      <button onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 text-[12.5px] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
        <I.ChevDown size={15} className={"transition-transform " + (open ? "" : "-rotate-90")} />
        {open ? "Hide" : "Show"} per-operation detail ({items.length} steps)
      </button>
      {open && (
        <div className="mt-3 overflow-hidden rounded-lg border border-[var(--border)]">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="bg-[var(--surface-2)] text-[var(--text-muted)] text-[11.5px] uppercase tracking-wider">
                <th className="px-4 py-2 text-left font-medium">Micro-operation</th>
                <th className="px-4 py-2 text-right font-medium">Estimate</th>
                <th className="px-4 py-2 text-right font-medium">Interval</th>
              </tr>
            </thead>
            <tbody>
              {productive.map((it, i) => <FutureOpRow key={"p" + i} it={it} />)}
              {waste.length > 0 && (
                <tr className="border-t border-[var(--border)]">
                  <td colSpan={3} className="px-4 py-1.5 bg-[var(--surface-2)]/60 text-[10.5px] uppercase tracking-wider text-[var(--text-faint)] font-medium">
                    Waste — revealed by richer data
                  </td>
                </tr>
              )}
              {waste.map((it, i) => <FutureOpRow key={"w" + i} it={it} />)}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FuturePage({ server, onBack }) {
  const [code, setCode] = useStateE("");
  const [file, setFile] = useStateE(null);
  const [loading, setLoading] = useStateE(false);
  const [result, setResult] = useStateE(null);
  const [error, setError] = useStateE(null);
  const fileRef = useRefE(null);

  async function run() {
    setError(null);
    if (!code.trim() && !file) { setError("Enter a panel code (e.g. PG02K) or attach a process PDF."); return; }
    setLoading(true); setResult(null);
    try {
      let data;
      if (file) {
        const fd = new FormData(); fd.append("file", file);
        data = await eApiMultipart(server, "/future/predict/pdf", fd);
      } else {
        data = await eApi(server, "/future/predict", { method: "POST", body: { key: code.trim() } });
      }
      setResult(data);
    } catch (e) {
      setError(eErrorMessage(e, file ? "predict-pdf" : "predict"));
    } finally { setLoading(false); }
  }

  return (
    <div className="h-screen overflow-auto bg-[var(--bg)]">
      {/* standalone top bar (no sidebar) */}
      <div className="h-[60px] border-b border-[var(--border)] flex items-center gap-3 px-6 sticky top-0 bg-[var(--bg)] z-20">
        <button onClick={onBack}
          className="flex items-center gap-1.5 h-9 px-3 rounded-md border border-[var(--border)] bg-[var(--surface)] text-[13px] text-[var(--text)] hover:border-[var(--accent)] transition-colors">
          <I.ChevDown size={15} className="rotate-90" /> Back
        </button>
        <div className="flex items-center gap-2">
          <I.Activity size={17} className="text-[var(--accent-hover)]" />
          <span className="text-[14px] font-semibold text-[var(--text)]">Future Vision</span>
          <span className="text-[11px] px-2 py-0.5 rounded-full border border-[var(--accent)]/40 text-[var(--accent-hover)] bg-[var(--accent)]/10">demo · fictitious data</span>
        </div>
      </div>

      <div className="px-6 lg:px-8 py-6 max-w-[1100px] mx-auto">
        <div className="mb-5">
          <h1 className="text-[20px] font-semibold text-[var(--text)]">What richer data unlocks</h1>
          <p className="text-[13.5px] text-[var(--text-muted)] mt-1 max-w-[760px]">
            A glimpse of the future of this project, built on <span className="text-[var(--text)] font-medium">fictitious data</span>.
            With more and richer measurements we can surface actionable patterns the current model can't see: hidden waste, and how
            <span className="text-[var(--text)]"> temperature</span>, <span className="text-[var(--text)]">operator experience</span> and
            <span className="text-[var(--text)]"> time of day</span> shift productivity. The central estimate uses the general model;
            the panels below show how each variable would move the time.
          </p>
        </div>

        <Card className="mb-5">
          <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
            <div className="flex-1">
              <label className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">Panel code</label>
              <input
                value={code}
                onChange={(e) => { setCode(e.target.value); if (e.target.value) setFile(null); }}
                placeholder="e.g. PG02K"
                spellCheck={false}
                className="mt-1 w-full h-10 px-3 rounded-md bg-[var(--surface)] border border-[var(--border)] focus:border-[var(--accent)] outline-none text-[14px] text-[var(--text)] placeholder:text-[var(--text-faint)] font-mono" />
            </div>
            <div className="text-[12px] text-[var(--text-faint)] pb-2.5 text-center">or</div>
            <div className="flex-1">
              <label className="text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-medium">Process PDF</label>
              <div className="mt-1 flex items-center gap-2">
                <button onClick={() => fileRef.current && fileRef.current.click()}
                  className="flex items-center gap-2 h-10 px-3 rounded-md bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--accent)] transition-colors text-[13px] text-[var(--text)]">
                  <I.FileUp size={15} className="text-[var(--text-faint)]" />
                  {file ? "Change file" : "Choose file"}
                </button>
                {file && <span className="text-[12px] text-[var(--text-muted)] truncate max-w-[180px]">{file.name}</span>}
                <input ref={fileRef} type="file" accept=".pdf" className="hidden"
                  onChange={(e) => { const f = e.target.files[0]; if (f) { setFile(f); setCode(""); } }} />
              </div>
            </div>
            <button onClick={run} disabled={loading}
              className="h-10 px-5 rounded-md bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white text-[13px] font-medium flex items-center gap-2 transition-colors">
              {loading ? <I.Loader size={15} className="animate-spin" /> : <I.Calculator size={15} />}
              {loading ? "Predicting…" : "Predict future"}
            </button>
          </div>
          {error && (
            <div className="mt-3 flex items-start gap-2.5 px-4 py-3 rounded-lg border border-[var(--err)]/30 bg-[var(--err)]/8 text-[13px] text-[var(--text)]">
              <I.CircleAlert size={16} className="text-[var(--err)] mt-0.5 shrink-0" />
              <div>{typeof error === "string" ? error : "Prediction failed."}</div>
            </div>
          )}
        </Card>

        {result && (
          <div>
            <div className="mb-3 text-[13px] text-[var(--text-muted)]">
              Panel <span className="font-mono text-[var(--text)]">{result.panel_id}</span>
              {result.n_panels > 1 && <span> · {result.n_panels} sub-panels aggregated</span>}
            </div>
            <FutureGeneralResult general={result.general} />
            <FutureScenarioBlock icon={<I.Activity size={18} />} title="Temperature — ambient comfort"
              note={result.temperature.note} data={result.temperature} xLabel="Temperature (°C)" xUnit="°" />
            <FutureScenarioBlock icon={<I.BadgeCheck size={18} />} title="Operator experience"
              note={result.experience.note} data={result.experience} xLabel="Experience (months)" xUnit="mo" />
            <FutureScenarioBlock icon={<I.Clock size={18} />} title="Time of day"
              note={result.timeofday.note} data={result.timeofday} xLabel="Hour of day" xUnit="h" />
          </div>
        )}
      </div>
    </div>
  );
}

/* ============================================================
 * ROOT
 * ============================================================ */
function EnterpriseApp() {
  const [server, setServer] = useStateE(E_DEFAULT_SERVER);
  const [tab, setTab] = useStateE("dashboard");
  const [health, setHealth] = useStateE("checking");
  const [modelName, setModelName] = useStateE("");
  const [reloadKey, setReloadKey] = useStateE(0);
  const [showFuture, setShowFuture] = useStateE(false);
  // keep-alive: a tab mounts on first visit and stays mounted (hidden via CSS),
  // so predictions, training jobs, etc. survive switching tabs. FuturePage too.
  const [visited, setVisited] = useStateE({ dashboard: true });
  const [futureMounted, setFutureMounted] = useStateE(false);

  useEffectE(() => {
    setVisited((v) => (v[tab] ? v : { ...v, [tab]: true }));
  }, [tab]);

  function openFuture() { setFutureMounted(true); setShowFuture(true); }

  useEffectE(() => {
    let cancelled = false;
    async function check() {
      try {await eApi(server, "/health");if (!cancelled) setHealth("ok");}
      catch {if (!cancelled) setHealth("down");}
    }
    setHealth("checking");check();
    const id = setInterval(check, 30000);
    return () => {cancelled = true;clearInterval(id);};
  }, [server]);

  useEffectE(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await eApi(server, "/model");
        if (cancelled) return;
        setModelName(data?.train_report?.model_name || data?.model_name || data?.name || data?.model || data?.version || "—");
      } catch {if (!cancelled) setModelName("");}
    })();
  }, [server, reloadKey]);

  return (
    <div className="h-screen overflow-hidden">
      <div className={"h-full flex " + (showFuture ? "hidden" : "")}>
        <Sidebar active={tab} onChange={setTab} />
        <div className="flex-1 min-w-0 min-h-0 flex flex-col">
          <TopBar server={server} setServer={setServer} health={health} modelName={modelName} onFuture={openFuture} />
          <main className="flex-1 min-h-0 px-6 lg:px-8 py-5 max-w-[1280px] w-full overflow-auto">
            {visited.dashboard && <div className={tab === "dashboard" ? "h-full" : "hidden"}><DashboardPage /></div>}
            {visited.predict && <div className={tab === "predict" ? "h-full" : "hidden"}><PredictTab server={server} /></div>}
            {visited.metrics && <div className={tab === "metrics" ? "h-full" : "hidden"}><MetricsPage server={server} /></div>}
            {visited.retrain && <div className={tab === "retrain" ? "h-full" : "hidden"}><RetrainTab server={server} onJobFinished={() => setReloadKey((k) => k + 1)} /></div>}
            {visited.history && <div className={tab === "history" ? "h-full" : "hidden"}><HistoryTab server={server} reloadKey={reloadKey} /></div>}
          </main>
        </div>
      </div>
      {futureMounted && (
        <div className={showFuture ? "" : "hidden"}>
          <FuturePage server={server} onBack={() => setShowFuture(false)} />
        </div>
      )}
    </div>);

}

window.EnterpriseApp = EnterpriseApp;