/* Trafford Bin Collections — UI + local notification scheduling */
(function () {
  "use strict";

  const STORE_KEY = "trafford-bin-prefs";
  const NOTIFIED_KEY = "trafford-bin-notified"; // dates we've already alerted for

  // ---- helpers ---------------------------------------------------------------
  const $ = (sel) => document.querySelector(sel);
  const todayISO = () => new Date().toISOString().slice(0, 10);

  function parseISO(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d);
  }
  function fmtFull(iso) {
    return parseISO(iso).toLocaleDateString("en-GB", {
      weekday: "long", day: "numeric", month: "long",
    });
  }
  function daysUntil(iso) {
    const a = parseISO(todayISO());
    const b = parseISO(iso);
    return Math.round((b - a) / 86400000);
  }
  function relLabel(n) {
    if (n === 0) return "Today";
    if (n === 1) return "Tomorrow";
    if (n < 0) return `${-n}d ago`;
    if (n < 7) return `In ${n} days`;
    if (n < 14) return "Next week";
    return `In ${Math.round(n / 7)} weeks`;
  }
  function binList(keys) {
    return keys.map((k) => BIN_TYPES[k].name).join(" + ");
  }

  function loadPrefs() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; }
    catch { return {}; }
  }
  function savePrefs(p) { localStorage.setItem(STORE_KEY, JSON.stringify(p)); }
  function loadNotified() {
    try { return JSON.parse(localStorage.getItem(NOTIFIED_KEY)) || {}; }
    catch { return {}; }
  }
  function saveNotified(n) { localStorage.setItem(NOTIFIED_KEY, JSON.stringify(n)); }

  // ---- data views ------------------------------------------------------------
  function upcoming() {
    const t = todayISO();
    return COLLECTIONS.filter((c) => c.date >= t);
  }
  function nextCollection() {
    return upcoming()[0] || null;
  }

  // ---- rendering -------------------------------------------------------------
  function renderNext() {
    const el = $("#next");
    const c = nextCollection();
    if (!c) {
      el.innerHTML = `<div class="next-loading">No upcoming collections in the calendar.</div>`;
      return;
    }
    const n = daysUntil(c.date);
    const chips = c.bins.map((k) => {
      const b = BIN_TYPES[k];
      return `<span class="bin-chip" style="background:${b.color}">
                <span class="e">${b.emoji}</span>${b.name}</span>`;
    }).join("");
    el.innerHTML = `
      <div class="next-when">Next collection · ${relLabel(n)}</div>
      <div class="next-date">${fmtFull(c.date)}</div>
      <div class="next-bins">${chips}</div>`;
  }

  function renderLegend() {
    const order = ["grey", "black", "blue", "green"];
    $("#legend").innerHTML = order.map((k) => {
      const b = BIN_TYPES[k];
      return `<li>
        <span class="swatch" style="background:${b.color}"></span>
        <span><span class="l-name">${b.name}</span> —
        <span class="l-desc">${b.desc}</span></span>
      </li>`;
    }).join("");
  }

  let showAll = false;
  function renderUpcoming() {
    const list = $("#upcoming");
    const t = todayISO();
    const items = showAll ? COLLECTIONS : upcoming().slice(0, 8);
    list.innerHTML = items.map((c) => {
      const d = parseISO(c.date);
      const past = c.date < t;
      const n = daysUntil(c.date);
      const bins = c.bins.map((k) => {
        const b = BIN_TYPES[k];
        return `<span class="dot"><span class="s" style="background:${b.color}"></span>${b.name}</span>`;
      }).join("");
      return `<li class="${past ? "past" : ""}">
        <div class="col-date">
          <div class="d">${d.getDate()}</div>
          <div class="m">${d.toLocaleDateString("en-GB", { month: "short" })}</div>
        </div>
        <div class="col-bins">${bins}</div>
        <div class="col-rel">${past ? "" : relLabel(n)}</div>
      </li>`;
    }).join("");
  }

  // ---- notifications ---------------------------------------------------------
  let swReg = null;

  function notifyStatus(msg, ok) {
    const s = $("#notify-status");
    s.textContent = msg;
    s.className = ok ? "" : "muted";
  }

  function updateNotifyUI() {
    const btn = $("#notify-btn");
    const controls = $("#notify-controls");
    if (!("Notification" in window)) {
      btn.disabled = true;
      btn.textContent = "Not supported";
      notifyStatus("This browser doesn't support notifications.", false);
      return;
    }
    const perm = Notification.permission;
    if (perm === "granted") {
      btn.textContent = "Reminders on";
      btn.disabled = true;
      controls.hidden = false;
      const p = loadPrefs();
      notifyStatus(`You'll be reminded the day before at ${p.remindTime || "18:00"}.`, true);
    } else if (perm === "denied") {
      btn.textContent = "Blocked";
      btn.disabled = true;
      notifyStatus("Notifications are blocked. Enable them in your browser settings.", false);
    } else {
      btn.textContent = "Enable reminders";
      btn.disabled = false;
      controls.hidden = true;
    }
  }

  async function requestNotify() {
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      const p = loadPrefs();
      p.enabled = true;
      p.remindTime = p.remindTime || "18:00";
      savePrefs(p);
      scheduleAll();
    }
    updateNotifyUI();
  }

  function showNotification(title, body, tag) {
    const opts = {
      body,
      tag,
      icon: "icons/icon-192.png",
      badge: "icons/icon-192.png",
      requireInteraction: true,
    };
    if (swReg && swReg.showNotification) {
      swReg.showNotification(title, opts);
    } else {
      new Notification(title, opts);
    }
  }

  // The "day before" reminder time as a Date for a given collection.
  function reminderTimeFor(iso) {
    const p = loadPrefs();
    const [h, m] = (p.remindTime || "18:00").split(":").map(Number);
    const d = parseISO(iso);
    d.setDate(d.getDate() - 1);
    d.setHours(h, m, 0, 0);
    return d;
  }

  // Catch-up: if a collection is tomorrow (or today) and we've passed the
  // reminder time but haven't notified yet, fire it now. Runs on every load.
  function catchUp() {
    if (Notification.permission !== "granted") return;
    const p = loadPrefs();
    if (!p.enabled) return;
    const notified = loadNotified();
    const now = new Date();
    for (const c of upcoming()) {
      const n = daysUntil(c.date);
      if (n > 1) break; // list is sorted; nothing else is due soon
      const remindAt = reminderTimeFor(c.date);
      if (now >= remindAt && !notified[c.date]) {
        showNotification(
          "🗑️ Bins out tomorrow",
          `${fmtFull(c.date)}: put out your ${binList(c.bins)}.`,
          `bin-${c.date}`
        );
        notified[c.date] = true;
      }
    }
    saveNotified(notified);
  }

  // While the page is open, set timers for the next few reminders.
  let timers = [];
  function scheduleAll() {
    timers.forEach(clearTimeout);
    timers = [];
    if (Notification.permission !== "granted") return;
    const p = loadPrefs();
    if (!p.enabled) return;
    const notified = loadNotified();
    const now = Date.now();
    // Try the experimental Notification Triggers API for reminders that fire
    // even when the app is closed; fall back to in-page timers.
    const canTrigger = swReg && "showTrigger" in Notification.prototype;
    for (const c of upcoming().slice(0, 12)) {
      const at = reminderTimeFor(c.date).getTime();
      if (at <= now || notified[c.date]) continue;
      const title = "🗑️ Bins out tomorrow";
      const body = `${fmtFull(c.date)}: put out your ${binList(c.bins)}.`;
      if (canTrigger) {
        try {
          swReg.showNotification(title, {
            body, tag: `bin-${c.date}`, icon: "icons/icon-192.png",
            badge: "icons/icon-192.png", requireInteraction: true,
            showTrigger: new TimestampTrigger(at),
          });
          continue;
        } catch (_) { /* fall through to timer */ }
      }
      const delay = at - now;
      if (delay < 2147483647) { // setTimeout max (~24.8 days)
        timers.push(setTimeout(() => {
          showNotification(title, body, `bin-${c.date}`);
          const nf = loadNotified(); nf[c.date] = true; saveNotified(nf);
        }, delay));
      }
    }
  }

  // ---- wiring ----------------------------------------------------------------
  function wire() {
    $("#notify-btn").addEventListener("click", requestNotify);
    $("#test-btn").addEventListener("click", () => {
      const c = nextCollection();
      if (c) {
        showNotification("🗑️ Test reminder",
          `Next: ${fmtFull(c.date)} — ${binList(c.bins)}.`, "bin-test");
      } else {
        showNotification("🗑️ Test reminder", "Notifications are working!", "bin-test");
      }
    });
    $("#remind-time").addEventListener("change", (e) => {
      const p = loadPrefs();
      p.remindTime = e.target.value;
      savePrefs(p);
      saveNotified({}); // reset so new time can re-fire
      updateNotifyUI();
      scheduleAll();
    });
    $("#toggle-all").addEventListener("click", (e) => {
      showAll = !showAll;
      e.target.textContent = showAll ? "Show less" : "Show all";
      renderUpcoming();
    });
  }

  async function init() {
    const p = loadPrefs();
    if (p.remindTime) $("#remind-time").value = p.remindTime;

    renderNext();
    renderLegend();
    renderUpcoming();
    wire();
    updateNotifyUI();

    if ("serviceWorker" in navigator) {
      try {
        swReg = await navigator.serviceWorker.register("sw.js");
      } catch (e) { /* offline-only feature; ignore */ }
    }

    catchUp();
    scheduleAll();

    // Re-check when the tab regains focus (e.g. opened the next morning).
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) { renderNext(); renderUpcoming(); catchUp(); }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
