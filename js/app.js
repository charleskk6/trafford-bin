/* Trafford Bin Collections — calendar viewer */
(function () {
  "use strict";

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

  // ---- wiring ----------------------------------------------------------------
  function wire() {
    $("#toggle-all").addEventListener("click", (e) => {
      showAll = !showAll;
      e.target.textContent = showAll ? "Show less" : "Show all";
      renderUpcoming();
    });
  }

  async function init() {
    renderNext();
    renderLegend();
    renderUpcoming();
    wire();

    if ("serviceWorker" in navigator) {
      try { await navigator.serviceWorker.register("sw.js"); }
      catch (e) { /* offline-only feature; ignore */ }
    }

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) { renderNext(); renderUpcoming(); }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
