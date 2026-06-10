#!/usr/bin/env python3
"""Generate a self-contained index.html for the Trafford bin collection calendar.

This script is the single source of truth: it holds the calendar data and emits
a static, self-contained index.html (inline CSS, data embedded as JSON, plus a
tiny inline script that highlights the next collection and computes relative
dates against the viewer's "today").

Usage:
    python3 generate.py        # writes ./index.html
"""

import json
from datetime import date
from pathlib import Path

# --- Bin definitions --------------------------------------------------------
# Legend decoded from the Trafford Council calendar:
#   grey  (● grey circle)    -> general / non-recyclable waste (every 2 weeks)
#   black (▲ black triangle) -> mixed recycling: plastics, glass, cans (every 4 weeks)
#   blue  (✚ blue plus)      -> paper & card (every 4 weeks)
#   green (caddy)            -> food & garden waste (weekly, on every collection day)
BIN_TYPES = {
    "grey":  {"name": "Grey bin",  "desc": "General / non-recyclable waste",        "color": "#6B7280", "emoji": "🗑️"},
    "black": {"name": "Black bin", "desc": "Mixed recycling — plastics, glass, cans", "color": "#1F2937", "emoji": "♻️"},
    "blue":  {"name": "Blue bin",  "desc": "Paper & cardboard",                      "color": "#2563EB", "emoji": "📦"},
    "green": {"name": "Green bin / caddy", "desc": "Food & garden waste (weekly)",   "color": "#16A34A", "emoji": "🌿"},
}

# Primary (rotating) bin per collection date, transcribed from the calendar.
PRIMARY_SCHEDULE = [
    ("2025-11-05", "grey"),  ("2025-11-12", "black"), ("2025-11-19", "grey"), ("2025-11-26", "blue"),
    ("2025-12-03", "grey"),  ("2025-12-10", "black"), ("2025-12-17", "grey"), ("2025-12-24", "blue"), ("2025-12-31", "grey"),
    ("2026-01-07", "black"), ("2026-01-14", "grey"),  ("2026-01-21", "blue"), ("2026-01-28", "grey"),
    ("2026-02-04", "black"), ("2026-02-11", "grey"),  ("2026-02-18", "blue"), ("2026-02-25", "grey"),
    ("2026-03-04", "black"), ("2026-03-11", "grey"),  ("2026-03-18", "blue"), ("2026-03-25", "grey"),
    ("2026-04-01", "black"), ("2026-04-08", "grey"),  ("2026-04-15", "blue"), ("2026-04-22", "grey"), ("2026-04-29", "black"),
    ("2026-05-06", "grey"),  ("2026-05-13", "blue"),  ("2026-05-20", "grey"), ("2026-05-27", "black"),
    ("2026-06-03", "grey"),  ("2026-06-10", "blue"),  ("2026-06-17", "grey"), ("2026-06-24", "black"),
    ("2026-07-01", "grey"),  ("2026-07-08", "blue"),  ("2026-07-15", "grey"), ("2026-07-22", "black"), ("2026-07-29", "grey"),
    ("2026-08-05", "blue"),  ("2026-08-12", "grey"),  ("2026-08-19", "black"), ("2026-08-26", "grey"),
    ("2026-09-02", "blue"),  ("2026-09-09", "grey"),  ("2026-09-16", "black"), ("2026-09-23", "grey"), ("2026-09-30", "blue"),
    ("2026-10-07", "grey"),  ("2026-10-14", "black"), ("2026-10-21", "grey"), ("2026-10-28", "blue"),
    ("2026-11-04", "grey"),  ("2026-11-11", "black"), ("2026-11-18", "grey"), ("2026-11-25", "blue"),
]


def green_suspended(iso: str) -> bool:
    """Green collections are suspended 22–28 December (festive period)."""
    return "2025-12-22" <= iso <= "2025-12-28"


def build_collections():
    out = []
    for iso, primary in PRIMARY_SCHEDULE:
        bins = [primary]
        if not green_suspended(iso):
            bins.append("green")
        out.append({"date": iso, "bins": bins})
    return out


# --- HTML rendering ---------------------------------------------------------
CSS = """
:root {
  --purple:#5b1a72; --purple-light:#7a2a96; --bg:#f4f1f6; --card:#fff;
  --text:#1f2430; --muted:#6b7280; --border:#e5e0ea;
}
* { box-sizing:border-box; }
body { margin:0; font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background:var(--bg); color:var(--text); -webkit-font-smoothing:antialiased; }
.topbar { background:linear-gradient(135deg,var(--purple),var(--purple-light));
  color:#fff; padding:calc(env(safe-area-inset-top) + 20px) 20px 22px; text-align:center; }
.topbar h1 { margin:0; font-size:1.4rem; }
.topbar .sub { margin:6px 0 0; font-size:.85rem; opacity:.9; }
main { max-width:640px; margin:0 auto; padding:16px; display:flex; flex-direction:column; gap:16px; }
.card { background:var(--card); border-radius:16px; padding:18px; box-shadow:0 1px 3px rgba(0,0,0,.06); }
.card h2 { margin:0 0 12px; font-size:1.05rem; }
.card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.card-head h2 { margin:0; }
.muted { color:var(--muted); }
.next-card { background:linear-gradient(135deg,#fff,#faf7fc); border:1px solid var(--border); }
.next-when { font-size:.85rem; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
.next-date { font-size:1.5rem; font-weight:700; margin:4px 0 14px; }
.next-bins { display:flex; flex-wrap:wrap; gap:10px; }
.bin-chip { display:flex; align-items:center; gap:8px; padding:8px 14px; border-radius:999px;
  color:#fff; font-weight:600; font-size:.95rem; }
.bin-chip .e { font-size:1.1rem; }
.btn { background:var(--purple); color:#fff; border:none; border-radius:10px; padding:10px 16px;
  font-size:.9rem; font-weight:600; cursor:pointer; white-space:nowrap; }
.btn:active { transform:translateY(1px); }
.btn-ghost { background:transparent; color:var(--purple); border:1px solid var(--purple); }
.btn-sm { padding:6px 12px; font-size:.8rem; }
.legend { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:12px; }
.legend li { display:flex; align-items:center; gap:12px; }
.swatch { width:18px; height:18px; border-radius:5px; flex:none; }
.legend .l-name { font-weight:600; }
.legend .l-desc { color:var(--muted); font-size:.85rem; }
.collections { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; }
.collections li { display:flex; align-items:center; gap:14px; padding:12px 0; border-bottom:1px solid var(--border); }
.collections li:last-child { border-bottom:none; }
.col-date { flex:none; width:64px; text-align:center; }
.col-date .d { font-size:1.4rem; font-weight:700; line-height:1; }
.col-date .m { font-size:.72rem; color:var(--muted); text-transform:uppercase; }
.col-bins { display:flex; flex-wrap:wrap; gap:6px; flex:1; }
.dot { display:inline-flex; align-items:center; gap:6px; font-size:.8rem; padding:4px 10px;
  border-radius:999px; background:#f3f0f6; color:var(--text); }
.dot .s { width:10px; height:10px; border-radius:50%; flex:none; }
.col-rel { flex:none; font-size:.75rem; color:var(--muted); }
.past { opacity:.4; }
.foot { text-align:center; padding:24px 16px calc(env(safe-area-inset-bottom) + 24px);
  color:var(--muted); font-size:.78rem; }
.foot p { margin:4px 0; }
@media (prefers-color-scheme:dark) {
  :root { --bg:#15131a; --card:#211d29; --text:#ece9f1; --muted:#a39db0; --border:#352e40; }
  .next-card { background:linear-gradient(135deg,#241f2d,#2a2335); }
  .dot { background:#2c2636; }
}
""".strip()


def render_legend() -> str:
    """Statically render the bin legend (not date-dependent)."""
    rows = []
    for key in ("grey", "black", "blue", "green"):
        b = BIN_TYPES[key]
        rows.append(
            f'      <li><span class="swatch" style="background:{b["color"]}"></span>'
            f'<span><span class="l-name">{b["name"]}</span> — '
            f'<span class="l-desc">{b["desc"]}</span></span></li>'
        )
    return "\n".join(rows)


# Inline script: renders the date-dependent "next" hero and upcoming list from
# embedded JSON so the page stays accurate against the viewer's current date.
SCRIPT = r"""
(function () {
  var BIN = __BIN_TYPES__;
  var COLLECTIONS = __COLLECTIONS__;
  function parseISO(s){var p=s.split("-");return new Date(+p[0],+p[1]-1,+p[2]);}
  function todayISO(){return new Date().toISOString().slice(0,10);}
  function fmtFull(s){return parseISO(s).toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long"});}
  function daysUntil(s){return Math.round((parseISO(s)-parseISO(todayISO()))/86400000);}
  function rel(n){if(n===0)return"Today";if(n===1)return"Tomorrow";if(n<0)return(-n)+"d ago";
    if(n<7)return"In "+n+" days";if(n<14)return"Next week";return"In "+Math.round(n/7)+" weeks";}
  function upcoming(){var t=todayISO();return COLLECTIONS.filter(function(c){return c.date>=t;});}
  function chips(bins){return bins.map(function(k){var b=BIN[k];
    return '<span class="bin-chip" style="background:'+b.color+'"><span class="e">'+b.emoji+'</span>'+b.name+'</span>';}).join("");}
  function dots(bins){return bins.map(function(k){var b=BIN[k];
    return '<span class="dot"><span class="s" style="background:'+b.color+'"></span>'+b.name+'</span>';}).join("");}
  function renderNext(){
    var el=document.getElementById("next"),c=upcoming()[0];
    if(!c){el.innerHTML='<div>No upcoming collections in the calendar.</div>';return;}
    var n=daysUntil(c.date);
    el.innerHTML='<div class="next-when">Next collection · '+rel(n)+'</div>'+
      '<div class="next-date">'+fmtFull(c.date)+'</div><div class="next-bins">'+chips(c.bins)+'</div>';
  }
  var showAll=false;
  function renderUpcoming(){
    var t=todayISO(),items=showAll?COLLECTIONS:upcoming().slice(0,8);
    document.getElementById("upcoming").innerHTML=items.map(function(c){
      var d=parseISO(c.date),past=c.date<t,n=daysUntil(c.date);
      return '<li class="'+(past?"past":"")+'"><div class="col-date"><div class="d">'+d.getDate()+
        '</div><div class="m">'+d.toLocaleDateString("en-GB",{month:"short"})+'</div></div>'+
        '<div class="col-bins">'+dots(c.bins)+'</div><div class="col-rel">'+(past?"":rel(n))+'</div></li>';
    }).join("");
  }
  document.getElementById("toggle-all").addEventListener("click",function(e){
    showAll=!showAll;e.target.textContent=showAll?"Show less":"Show all";renderUpcoming();});
  renderNext();renderUpcoming();
  document.addEventListener("visibilitychange",function(){if(!document.hidden){renderNext();renderUpcoming();}});
})();
""".strip()


def render_html() -> str:
    collections = build_collections()
    script = (
        SCRIPT
        .replace("__BIN_TYPES__", json.dumps(BIN_TYPES, ensure_ascii=False))
        .replace("__COLLECTIONS__", json.dumps(collections, ensure_ascii=False))
    )
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="theme-color" content="#5b1a72" />
  <title>Trafford Bin Collections</title>
  <meta name="description" content="Trafford waste collection calendar 2025–2026." />
  <link rel="manifest" href="manifest.webmanifest" />
  <link rel="icon" href="icons/icon.svg" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="icons/icon-192.png" />
  <!-- This file is generated by generate.py — edit that, not this. -->
  <style>{CSS}</style>
</head>
<body>
  <header class="topbar">
    <h1>🗑️ Trafford Bin Collections</h1>
    <p class="sub">Present bins by 6:30am · bring them back in the same day</p>
  </header>

  <main>
    <section id="next" class="card next-card" aria-live="polite">
      <div>Loading…</div>
    </section>

    <section class="card">
      <h2>What goes out</h2>
      <ul class="legend">
{render_legend()}
      </ul>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Upcoming collections</h2>
        <button id="toggle-all" class="btn btn-ghost btn-sm">Show all</button>
      </div>
      <ul id="upcoming" class="collections"></ul>
    </section>
  </main>

  <footer class="foot">
    <p>Green bin collections are suspended 22–28 December.</p>
    <p>Unofficial app · data from the Trafford Council waste calendar 2025–2026.</p>
  </footer>

  <script>{script}</script>
</body>
</html>
"""


def main() -> None:
    out = Path(__file__).resolve().parent / "index.html"
    out.write_text(render_html(), encoding="utf-8")
    print(f"Wrote {out} ({len(build_collections())} collections)")


if __name__ == "__main__":
    main()
