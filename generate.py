#!/usr/bin/env python3
"""Generate a self-contained index.html for the Trafford bin collection calendar.

This script is the single source of truth: it holds the calendar data for each
supported postcode and emits a static, self-contained index.html (inline CSS,
data embedded as JSON, plus a small inline script that lets you pick a postcode,
remembers the choice, highlights the active one, and shows the next collection).

Usage:
    python3 generate.py        # writes ./index.html
"""

import json
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

# --- Schedules per postcode -------------------------------------------------
# Each entry: postcode -> list of (ISO date, primary rotating bin).
# The Green bin/caddy is added automatically on every collection day (weekly),
# except during the festive suspension (see green_suspended()).
#
# To add a postcode, paste its (date, bin) rows below.

# Transcribed from the Trafford 2025/26 calendar. The calendars supplied for
# M33 7TJ and M33 6UU are identical, so both postcodes share this schedule.
_M33_2025_26 = [
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

PRIMARY_SCHEDULES = {
    "M33 7TJ": _M33_2025_26,
    "M33 6UU": _M33_2025_26,
}

DEFAULT_POSTCODE = "M33 7TJ"

# Optional: a Google OAuth *Web* client ID (…apps.googleusercontent.com) used
# for the "Sync to Google Calendar" feature. Leave blank to enter it in the app
# UI instead (it is stored only in the browser). Create one in Google Cloud
# Console → APIs & Services → Credentials, enable the Google Calendar API, and
# add your site's URL to the OAuth client's Authorized JavaScript origins.
GOOGLE_CLIENT_ID = "193554635172-0k01k1tkem9atv96599gqjnv6tgu2eea.apps.googleusercontent.com"

# Event reminder, in minutes before the all-day event's midnight start. All-day
# events are measured from 00:00 on the collection day, so 900 minutes = 1 day
# before at 09:00. (1440 would be exactly 24h before, i.e. midnight.)
EVENT_REMINDER_MINUTES = 900


def green_suspended(iso: str) -> bool:
    """Green collections are suspended 22–28 December (festive period)."""
    return "2025-12-22" <= iso <= "2025-12-28"


def build_collections(primary_schedule):
    out = []
    for iso, primary in primary_schedule:
        bins = [primary]
        if not green_suspended(iso):
            bins.append("green")
        out.append({"date": iso, "bins": bins})
    return out


def build_all():
    """postcode -> list of {date, bins}."""
    return {pc: build_collections(rows) for pc, rows in PRIMARY_SCHEDULES.items()}


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
/* Postcode picker */
.pc-card { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.pc-left { display:flex; align-items:center; gap:10px; }
.pc-left label { font-weight:600; }
#postcode { font-size:1rem; font-weight:600; padding:8px 12px; border-radius:10px;
  border:1px solid var(--border); background:var(--card); color:var(--text); }
.pc-badge { display:inline-flex; align-items:center; gap:6px; background:var(--purple); color:#fff;
  font-weight:700; padding:6px 14px; border-radius:999px; font-size:.9rem; letter-spacing:.02em; }
.pc-badge::before { content:"📍"; }
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
.empty { color:var(--muted); padding:6px 0; }
.gcal-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
.gcal-status { margin:0; }
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


def render_options() -> str:
    return "\n".join(
        f'        <option value="{pc}">{pc}</option>' for pc in PRIMARY_SCHEDULES
    )


# Inline script: postcode selection (remembered in localStorage), active-postcode
# highlight, and the date-dependent "next" hero + upcoming list, rendered from
# embedded JSON so the page stays accurate against the viewer's current date.
SCRIPT = r"""
(function () {
  var BIN = __BIN_TYPES__;
  var DATA = __DATA__;                 // postcode -> [{date, bins}]
  var DEFAULT_PC = __DEFAULT__;
  var STORE = "trafford-postcode";

  function parseISO(s){var p=s.split("-");return new Date(+p[0],+p[1]-1,+p[2]);}
  function todayISO(){return new Date().toISOString().slice(0,10);}
  function fmtFull(s){return parseISO(s).toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long"});}
  function daysUntil(s){return Math.round((parseISO(s)-parseISO(todayISO()))/86400000);}
  function rel(n){if(n===0)return"Today";if(n===1)return"Tomorrow";if(n<0)return(-n)+"d ago";
    if(n<7)return"In "+n+" days";if(n<14)return"Next week";return"In "+Math.round(n/7)+" weeks";}
  function chips(bins){return bins.map(function(k){var b=BIN[k];
    return '<span class="bin-chip" style="background:'+b.color+'"><span class="e">'+b.emoji+'</span>'+b.name+'</span>';}).join("");}
  function dots(bins){return bins.map(function(k){var b=BIN[k];
    return '<span class="dot"><span class="s" style="background:'+b.color+'"></span>'+b.name+'</span>';}).join("");}

  function loadPC(){var s=localStorage.getItem(STORE);return (s && DATA[s])?s:DEFAULT_PC;}
  function savePC(pc){try{localStorage.setItem(STORE,pc);}catch(e){}}

  var current = loadPC();
  var showAll = false;

  function list(){return DATA[current]||[];}
  function upcoming(){var t=todayISO();return list().filter(function(c){return c.date>=t;});}

  function renderNext(){
    var el=document.getElementById("next");
    if(!list().length){el.innerHTML='<div class="empty">No schedule added yet for <strong>'+current+'</strong>.</div>';return;}
    var c=upcoming()[0];
    if(!c){el.innerHTML='<div class="empty">No upcoming collections in the calendar for '+current+'.</div>';return;}
    var n=daysUntil(c.date);
    el.innerHTML='<div class="next-when">Next collection · '+current+' · '+rel(n)+'</div>'+
      '<div class="next-date">'+fmtFull(c.date)+'</div><div class="next-bins">'+chips(c.bins)+'</div>';
  }

  function renderUpcoming(){
    var el=document.getElementById("upcoming");
    if(!list().length){el.innerHTML='<li class="empty">Nothing to show yet for '+current+'.</li>';return;}
    var t=todayISO(),items=showAll?list():upcoming().slice(0,8);
    el.innerHTML=items.map(function(c){
      var d=parseISO(c.date),past=c.date<t,n=daysUntil(c.date);
      return '<li class="'+(past?"past":"")+'"><div class="col-date"><div class="d">'+d.getDate()+
        '</div><div class="m">'+d.toLocaleDateString("en-GB",{month:"short"})+'</div></div>'+
        '<div class="col-bins">'+dots(c.bins)+'</div><div class="col-rel">'+(past?"":rel(n))+'</div></li>';
    }).join("");
  }

  function refresh(){
    document.getElementById("pc-badge").textContent=current;
    renderNext();renderUpcoming();
  }

  var sel=document.getElementById("postcode");
  sel.value=current;
  sel.addEventListener("change",function(){current=sel.value;savePC(current);refresh();});
  document.getElementById("toggle-all").addEventListener("click",function(e){
    showAll=!showAll;e.target.textContent=showAll?"Show less":"Show all";renderUpcoming();});
  document.addEventListener("visibilitychange",function(){if(!document.hidden)refresh();});

  // ---- Google Calendar sync ------------------------------------------------
  var GCAL_CLIENT_ID = (__GCAL_CLIENT_ID__||"").trim();
  var REMINDER_MIN = __REMINDER_MIN__;
  var GCAL_SCOPE = "https://www.googleapis.com/auth/calendar.events";
  var GIS_SRC = "https://accounts.google.com/gsi/client";
  var gisLoaded = false, accessToken = null;

  function gcalStatus(msg){document.getElementById("gcal-status").textContent=msg;}

  function pad(n){return (n<10?"0":"")+n;}
  function addDays(iso,n){var d=parseISO(iso);d.setDate(d.getDate()+n);
    return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate());}

  function loadGIS(){return new Promise(function(res,rej){
    if(gisLoaded && window.google && google.accounts){return res();}
    var s=document.createElement("script");s.src=GIS_SRC;s.async=true;s.defer=true;
    s.onload=function(){gisLoaded=true;res();};
    s.onerror=function(){rej(new Error("Could not load Google sign-in (offline?)."));};
    document.head.appendChild(s);
  });}

  function getToken(){return new Promise(function(res,rej){
    var cid=GCAL_CLIENT_ID;
    if(!cid){rej(new Error("Google Calendar sync isn't configured."));return;}
    var tc=google.accounts.oauth2.initTokenClient({
      client_id:cid, scope:GCAL_SCOPE,
      callback:function(r){if(r&&r.access_token){accessToken=r.access_token;res(accessToken);}else{rej(new Error("Authorisation failed."));}},
      error_callback:function(){rej(new Error("Authorisation was cancelled."));}
    });
    tc.requestAccessToken({prompt: accessToken? "":"consent"});
  });}

  function api(path,opts){opts=opts||{};
    opts.headers=Object.assign({Authorization:"Bearer "+accessToken,"Content-Type":"application/json"},opts.headers||{});
    return fetch("https://www.googleapis.com/calendar/v3"+path,opts).then(function(r){
      if(!r.ok){return r.text().then(function(t){throw new Error("Google API "+r.status+": "+t.slice(0,180));});}
      return r.status===204? null : r.json();
    });
  }

  // List events this app created (we tag every event with traffordBinApp=1).
  // Returns [{id, key}] across the given window, following pagination.
  function listAppEvents(timeMin,timeMax){
    var out=[], token=null;
    function page(){
      var q="/calendars/primary/events?privateExtendedProperty="+encodeURIComponent("traffordBinApp=1")+
        "&singleEvents=true&maxResults=2500&timeMin="+encodeURIComponent(timeMin)+
        "&timeMax="+encodeURIComponent(timeMax)+(token?("&pageToken="+token):"");
      return api(q).then(function(data){
        (data.items||[]).forEach(function(ev){
          var p=ev.extendedProperties&&ev.extendedProperties.private;
          out.push({id:ev.id, key:(p&&p.traffordBinKey)||""});
        });
        if(data.nextPageToken){token=data.nextPageToken;return page();}
        return out;
      });
    }
    return page();
  }

  function eventFor(c){
    var names=c.bins.map(function(k){return BIN[k].name;}).join(" + ");
    return {
      summary:"🗑️ Bin day — "+names,
      description:"Put out: "+names+"\nPostcode: "+current+"\nTrafford bin calendar",
      start:{date:c.date}, end:{date:addDays(c.date,1)},
      transparency:"transparent",
      reminders:{useDefault:false, overrides:[{method:"popup", minutes:REMINDER_MIN}]},
      extendedProperties:{private:{traffordBinApp:"1", traffordBinKey:current+"|"+c.date}}
    };
  }

  function syncGCal(){
    var btn=document.getElementById("gcal-sync");
    var items=upcoming();
    if(!items.length){gcalStatus("No upcoming collections to add for "+current+".");return;}
    btn.disabled=true;
    gcalStatus("Connecting to Google…");
    loadGIS().then(getToken).then(function(){
      var timeMin=parseISO(todayISO()).toISOString();
      var timeMax=parseISO(addDays(items[items.length-1].date,2)).toISOString();
      gcalStatus("Checking existing events…");
      return listAppEvents(timeMin,timeMax).then(function(events){
        var have={}; events.forEach(function(e){if(e.key){have[e.key]=true;}});
        var toAdd=items.filter(function(c){return !have[current+"|"+c.date];});
        if(!toAdd.length){gcalStatus("✓ Already up to date for "+current+" — "+items.length+" collections present, nothing added.");return;}
        var added=0;
        function next(){
          if(added>=toAdd.length){
            gcalStatus("✓ Added "+added+" new date"+(added===1?"":"s")+" for "+current+" ("+(items.length-added)+" already existed).");
            return;
          }
          return api("/calendars/primary/events",{method:"POST",body:JSON.stringify(eventFor(toAdd[added]))}).then(function(){
            added++;gcalStatus("Adding… "+added+"/"+toAdd.length);return next();
          });
        }
        return next();
      });
    }).catch(function(e){gcalStatus("⚠ "+e.message);}).then(function(){btn.disabled=false;});
  }

  // Remove every event this app added (all postcodes, past and future).
  function removeGCal(){
    var btn=document.getElementById("gcal-remove");
    if(!confirm("Remove all bin collection events this app added to your Google Calendar?")){return;}
    btn.disabled=true;
    gcalStatus("Connecting to Google…");
    loadGIS().then(getToken).then(function(){
      var timeMin=new Date(Date.UTC(2025,0,1)).toISOString();
      var timeMax=new Date(Date.UTC(2027,0,1)).toISOString();
      gcalStatus("Finding events to remove…");
      return listAppEvents(timeMin,timeMax).then(function(events){
        if(!events.length){gcalStatus("No synced events found to remove.");return;}
        var removed=0;
        function next(){
          if(removed>=events.length){
            gcalStatus("✓ Removed "+removed+" synced event"+(removed===1?"":"s")+".");return;
          }
          return api("/calendars/primary/events/"+encodeURIComponent(events[removed].id),{method:"DELETE"}).then(function(){
            removed++;gcalStatus("Removing… "+removed+"/"+events.length);return next();
          });
        }
        return next();
      });
    }).catch(function(e){gcalStatus("⚠ "+e.message);}).then(function(){btn.disabled=false;});
  }

  document.getElementById("gcal-sync").addEventListener("click",syncGCal);
  document.getElementById("gcal-remove").addEventListener("click",removeGCal);

  refresh();
})();
""".strip()


def render_html() -> str:
    script = (
        SCRIPT
        .replace("__BIN_TYPES__", json.dumps(BIN_TYPES, ensure_ascii=False))
        .replace("__DATA__", json.dumps(build_all(), ensure_ascii=False))
        .replace("__DEFAULT__", json.dumps(DEFAULT_POSTCODE, ensure_ascii=False))
        .replace("__GCAL_CLIENT_ID__", json.dumps(GOOGLE_CLIENT_ID, ensure_ascii=False))
        .replace("__REMINDER_MIN__", json.dumps(EVENT_REMINDER_MINUTES))
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
    <p class="sub">Present bins by 6:30am · bring them back within 48 hours</p>
  </header>

  <main>
    <section class="card pc-card">
      <div class="pc-left">
        <label for="postcode">Postcode</label>
        <select id="postcode">
{render_options()}
        </select>
      </div>
      <span class="pc-badge" id="pc-badge">{DEFAULT_POSTCODE}</span>
    </section>

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

    <section class="card gcal-card">
      <h2>Google Calendar</h2>
      <p class="gcal-status muted" id="gcal-status">Add this postcode's upcoming collections to your Google Calendar. Dates already in your calendar are skipped — re-syncing never creates duplicates.</p>
      <div class="gcal-actions">
        <button id="gcal-sync" class="btn">Sync to Google Calendar</button>
        <button id="gcal-remove" class="btn btn-ghost">Remove synced events</button>
      </div>
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
    counts = ", ".join(f"{pc}: {len(rows)}" for pc, rows in PRIMARY_SCHEDULES.items())
    print(f"Wrote {out} ({counts})")


if __name__ == "__main__":
    main()
