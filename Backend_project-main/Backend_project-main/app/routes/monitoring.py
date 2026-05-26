"""
Monitoring & Dashboard routes.

GET /monitoring/stats   → JSON snapshot of app metrics (request counts, error rate, recent logs)
GET /monitoring/dashboard → HTML dashboard page
"""

import os
import json
from collections import defaultdict
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

LOG_PATH = "logs/app.log"
AUDIT_PATH = "logs/audit.log"


def _parse_logs(path: str, max_lines: int = 500) -> list[dict]:
    """Read the last `max_lines` lines from a log file and parse JSON records."""
    records = []
    if not os.path.exists(path):
        return records
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-max_lines:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({"message": line, "level": "INFO"})
    except Exception:
        pass
    return records


@router.get("/stats", summary="Get live application metrics")
def get_stats():
    """
    Returns a JSON snapshot containing:
    - total_requests: total API calls logged
    - error_count: number of requests with 4xx/5xx status
    - error_rate_pct: percentage of errored requests
    - requests_by_method: breakdown by HTTP method
    - requests_by_path: breakdown by endpoint path
    - recent_errors: last 10 error log entries
    - recent_audit: last 10 audit log entries
    - system_health: 'ok' always (extend with real checks as needed)
    """
    logs = _parse_logs(LOG_PATH)

    total_requests = 0
    error_count = 0
    requests_by_method: dict = defaultdict(int)
    requests_by_path: dict = defaultdict(int)
    recent_errors: list = []

    for record in logs:
        extra = record.get("extra", {})
        message = record.get("message", "")
        level = record.get("level", "INFO")

        # Count completed requests (middleware emits "request_end")
        if message == "request_end":
            total_requests += 1
            method = extra.get("method", "UNKNOWN")
            path = extra.get("path", "/")
            status_code = extra.get("status_code", 200)

            requests_by_method[method] += 1
            requests_by_path[path] += 1

            if isinstance(status_code, int) and status_code >= 400:
                error_count += 1

        # Collect error-level records
        if level in ("ERROR", "CRITICAL"):
            recent_errors.append({
                "timestamp": record.get("timestamp", ""),
                "message": message,
                "extra": extra,
            })

    error_rate = round((error_count / total_requests * 100), 2) if total_requests else 0.0
    recent_audit = _parse_logs(AUDIT_PATH, max_lines=50)[-10:]

    return JSONResponse({
        "system_health": "ok",
        "total_requests": total_requests,
        "error_count": error_count,
        "error_rate_pct": error_rate,
        "requests_by_method": dict(requests_by_method),
        "requests_by_path": dict(requests_by_path),
        "recent_errors": recent_errors[-10:],
        "recent_audit_events": [
            {
                "timestamp": r.get("timestamp", ""),
                "event": r.get("extra", {}).get("event", ""),
                "message": r.get("message", ""),
            }
            for r in recent_audit
        ],
    })


# ── Inline HTML dashboard ─────────────────────────────────────────────────────

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Monitoring Dashboard – Student Management System</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
  header{background:#1e293b;padding:18px 32px;border-bottom:1px solid #334155;display:flex;align-items:center;gap:14px}
  header h1{font-size:1.3rem;font-weight:700;color:#f1f5f9}
  .badge{padding:4px 12px;border-radius:999px;font-size:.75rem;font-weight:600}
  .badge-green{background:#166534;color:#bbf7d0}
  .badge-red{background:#7f1d1d;color:#fecaca}
  main{padding:28px 32px;display:grid;gap:24px}
  .grid-4{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px}
  .card h2{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin-bottom:8px}
  .card .value{font-size:2rem;font-weight:700;color:#f1f5f9}
  .card .sub{font-size:.8rem;color:#64748b;margin-top:4px}
  .section{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px}
  .section h3{font-size:.9rem;font-weight:600;color:#cbd5e1;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #334155}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th{text-align:left;padding:8px 12px;background:#0f172a;color:#64748b;font-weight:600;text-transform:uppercase;font-size:.7rem;letter-spacing:.05em}
  td{padding:8px 12px;border-bottom:1px solid #1e293b;color:#cbd5e1;max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  tr:last-child td{border-bottom:none}
  tr:hover td{background:#0f172a}
  .error-tag{color:#f87171;font-weight:600}
  .info-tag{color:#38bdf8}
  .warn-tag{color:#fbbf24}
  .empty{color:#475569;font-style:italic;font-size:.85rem;padding:12px 0}
  footer{text-align:center;padding:16px;color:#334155;font-size:.75rem}
  .refresh-btn{margin-left:auto;padding:7px 18px;background:#3b82f6;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:.85rem;font-weight:600}
  .refresh-btn:hover{background:#2563eb}
  .bar-wrap{display:flex;flex-direction:column;gap:8px}
  .bar-row{display:flex;align-items:center;gap:10px;font-size:.8rem}
  .bar-label{width:130px;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex-shrink:0}
  .bar-outer{flex:1;background:#0f172a;border-radius:4px;height:10px;overflow:hidden}
  .bar-inner{height:100%;border-radius:4px;background:#3b82f6;transition:width .4s}
  .bar-count{width:30px;text-align:right;color:#e2e8f0}
</style>
</head>
<body>
<header>
  <span style="font-size:1.4rem">📊</span>
  <h1>Monitoring Dashboard</h1>
  <span id="health-badge" class="badge badge-green">● Healthy</span>
  <button class="refresh-btn" onclick="loadStats()">↻ Refresh</button>
</header>
<main>
  <!-- KPI cards -->
  <div class="grid-4">
    <div class="card">
      <h2>Total Requests</h2>
      <div class="value" id="total-req">—</div>
      <div class="sub">since last restart</div>
    </div>
    <div class="card">
      <h2>Error Count</h2>
      <div class="value" id="err-count" style="color:#f87171">—</div>
      <div class="sub">4xx / 5xx responses</div>
    </div>
    <div class="card">
      <h2>Error Rate</h2>
      <div class="value" id="err-rate">—</div>
      <div class="sub">% of total requests</div>
    </div>
    <div class="card">
      <h2>System Health</h2>
      <div class="value" id="health-val" style="font-size:1.2rem;padding-top:6px">—</div>
      <div class="sub">live status</div>
    </div>
  </div>

  <!-- Requests by method & path -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
    <div class="section">
      <h3>Requests by HTTP Method</h3>
      <div class="bar-wrap" id="methods-chart"><p class="empty">Loading…</p></div>
    </div>
    <div class="section">
      <h3>Top Endpoints</h3>
      <div class="bar-wrap" id="paths-chart"><p class="empty">Loading…</p></div>
    </div>
  </div>

  <!-- Recent errors -->
  <div class="section">
    <h3>⚠️ Recent Errors</h3>
    <table>
      <thead><tr><th>Timestamp</th><th>Message</th><th>Details</th></tr></thead>
      <tbody id="errors-tbody"><tr><td colspan="3" class="empty">Loading…</td></tr></tbody>
    </table>
  </div>

  <!-- Audit log -->
  <div class="section">
    <h3>🔍 Recent Audit Events</h3>
    <table>
      <thead><tr><th>Timestamp</th><th>Event</th><th>Message</th></tr></thead>
      <tbody id="audit-tbody"><tr><td colspan="3" class="empty">Loading…</td></tr></tbody>
    </table>
  </div>
</main>
<footer>Student Management System — Monitoring Dashboard &nbsp;|&nbsp; Auto-refreshes every 30 s</footer>

<script>
async function loadStats() {
  try {
    const res = await fetch('/monitoring/stats');
    const d = await res.json();

    document.getElementById('total-req').textContent = d.total_requests;
    document.getElementById('err-count').textContent = d.error_count;
    document.getElementById('err-rate').textContent = d.error_rate_pct + '%';

    const health = d.system_health === 'ok';
    document.getElementById('health-val').textContent = health ? '✅ OK' : '❌ Issue';
    const badge = document.getElementById('health-badge');
    badge.textContent = health ? '● Healthy' : '● Degraded';
    badge.className = 'badge ' + (health ? 'badge-green' : 'badge-red');

    renderBars('methods-chart', d.requests_by_method);
    renderBars('paths-chart', d.requests_by_path, 6);
    renderErrorTable(d.recent_errors);
    renderAuditTable(d.recent_audit_events);
  } catch(e) {
    console.error('Failed to load stats', e);
  }
}

function renderBars(elId, data, maxItems = 10) {
  const el = document.getElementById(elId);
  const entries = Object.entries(data || {}).sort((a,b) => b[1]-a[1]).slice(0, maxItems);
  if (!entries.length) { el.innerHTML = '<p class="empty">No data yet</p>'; return; }
  const max = entries[0][1] || 1;
  el.innerHTML = entries.map(([label, count]) => `
    <div class="bar-row">
      <span class="bar-label" title="${label}">${label}</span>
      <div class="bar-outer"><div class="bar-inner" style="width:${Math.round(count/max*100)}%"></div></div>
      <span class="bar-count">${count}</span>
    </div>`).join('');
}

function renderErrorTable(errors) {
  const tbody = document.getElementById('errors-tbody');
  if (!errors || !errors.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty">No errors logged 🎉</td></tr>';
    return;
  }
  tbody.innerHTML = errors.map(e => `
    <tr>
      <td>${e.timestamp || '—'}</td>
      <td class="error-tag">${e.message || '—'}</td>
      <td>${JSON.stringify(e.extra || {})}</td>
    </tr>`).join('');
}

function renderAuditTable(events) {
  const tbody = document.getElementById('audit-tbody');
  if (!events || !events.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty">No audit events yet</td></tr>';
    return;
  }
  tbody.innerHTML = events.map(e => `
    <tr>
      <td>${e.timestamp || '—'}</td>
      <td class="info-tag">${e.event || '—'}</td>
      <td>${e.message || '—'}</td>
    </tr>`).join('');
}

loadStats();
setInterval(loadStats, 30000);
</script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def monitoring_dashboard():
    """Serve the inline monitoring dashboard HTML page."""
    return HTMLResponse(content=_DASHBOARD_HTML)
