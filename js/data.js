// Trafford waste collection calendar (2025–2026)
// Source: trafford.gov.uk waste collection calendar
//
// Legend decoded from the calendar:
//   grey  (● grey circle)  -> Grey bin: general / non-recyclable waste (every 2 weeks)
//   black (▲ black triangle)-> Black bin: mixed recycling – plastics, glass, cans (every 4 weeks)
//   blue  (✚ blue plus)    -> Blue bin: paper & card (every 4 weeks)
//
// The Green bin / green caddy (food & garden waste) is collected EVERY week,
// so it goes out on every collection day below — except 22–28 Dec when green
// collections are suspended over the festive period.

const BIN_TYPES = {
  grey: {
    key: "grey",
    name: "Grey bin",
    desc: "General / non-recyclable waste",
    color: "#6b7280",
    emoji: "🗑️",
  },
  black: {
    key: "black",
    name: "Black bin",
    desc: "Mixed recycling — plastics, glass, cans",
    color: "#1f2937",
    emoji: "♻️",
  },
  blue: {
    key: "blue",
    name: "Blue bin",
    desc: "Paper & cardboard",
    color: "#2563eb",
    emoji: "📦",
  },
  green: {
    key: "green",
    name: "Green bin / caddy",
    desc: "Food & garden waste (weekly)",
    color: "#16a34a",
    emoji: "🌿",
  },
};

// Primary (rotating) bin for each collection date, transcribed from the calendar.
// Dates are ISO yyyy-mm-dd.
const PRIMARY_SCHEDULE = [
  ["2025-11-05", "grey"],  ["2025-11-12", "black"], ["2025-11-19", "grey"], ["2025-11-26", "blue"],
  ["2025-12-03", "grey"],  ["2025-12-10", "black"], ["2025-12-17", "grey"], ["2025-12-24", "blue"], ["2025-12-31", "grey"],
  ["2026-01-07", "black"], ["2026-01-14", "grey"],  ["2026-01-21", "blue"], ["2026-01-28", "grey"],
  ["2026-02-04", "black"], ["2026-02-11", "grey"],  ["2026-02-18", "blue"], ["2026-02-25", "grey"],
  ["2026-03-04", "black"], ["2026-03-11", "grey"],  ["2026-03-18", "blue"], ["2026-03-25", "grey"],
  ["2026-04-01", "black"], ["2026-04-08", "grey"],  ["2026-04-15", "blue"], ["2026-04-22", "grey"], ["2026-04-29", "black"],
  ["2026-05-06", "grey"],  ["2026-05-13", "blue"],  ["2026-05-20", "grey"], ["2026-05-27", "black"],
  ["2026-06-03", "grey"],  ["2026-06-10", "blue"],  ["2026-06-17", "grey"], ["2026-06-24", "black"],
  ["2026-07-01", "grey"],  ["2026-07-08", "blue"],  ["2026-07-15", "grey"], ["2026-07-22", "black"], ["2026-07-29", "grey"],
  ["2026-08-05", "blue"],  ["2026-08-12", "grey"],  ["2026-08-19", "black"], ["2026-08-26", "grey"],
  ["2026-09-02", "blue"],  ["2026-09-09", "grey"],  ["2026-09-16", "black"], ["2026-09-23", "grey"], ["2026-09-30", "blue"],
  ["2026-10-07", "grey"],  ["2026-10-14", "black"], ["2026-10-21", "grey"], ["2026-10-28", "blue"],
  ["2026-11-04", "grey"],  ["2026-11-11", "black"], ["2026-11-18", "grey"], ["2026-11-25", "blue"],
];

// Festive suspension of green collections (inclusive).
const GREEN_SUSPENDED = (iso) => iso >= "2025-12-22" && iso <= "2025-12-28";

// Build the full collection list: each date -> array of bin keys (green added weekly).
const COLLECTIONS = PRIMARY_SCHEDULE.map(([date, primary]) => {
  const bins = [primary];
  if (!GREEN_SUSPENDED(date)) bins.push("green");
  return { date, bins };
});

if (typeof module !== "undefined") {
  module.exports = { BIN_TYPES, COLLECTIONS, PRIMARY_SCHEDULE, GREEN_SUSPENDED };
}
