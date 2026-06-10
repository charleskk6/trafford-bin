# Trafford Bin Collections

A small **web app (PWA)** that shows the Trafford Council waste collection
calendar (Nov 2025 – Nov 2026) — which bins to put out, and when.

## Features

- 📅 **Next collection** banner + full upcoming list
- ♻️ **Bin legend** decoded from the council calendar
- 📲 **Installable** to your phone's home screen and works **offline** (service worker)

## The bins

| Symbol on the council calendar | Bin | Contents | Frequency |
|---|---|---|---|
| ● grey circle | **Grey bin** | General / non-recyclable waste | Every 2 weeks |
| ▲ black triangle | **Black bin** | Mixed recycling — plastics, glass, cans | Every 4 weeks |
| ✚ blue plus | **Blue bin** | Paper & cardboard | Every 4 weeks |
| (every collection day) | **Green bin / caddy** | Food & garden waste | Weekly |

> Green bin collections are suspended **22–28 December**.

## Run it

It's a static site — no build step.

```bash
# from the repo root
python3 -m http.server 8000
# then open http://localhost:8000
```

To use it on your phone, host the folder on any static host (e.g. GitHub Pages),
open it, then **Add to Home Screen**.

## Files

- `index.html` — layout
- `css/styles.css` — styling (light/dark)
- `js/data.js` — the calendar data + bin definitions
- `js/app.js` — rendering
- `sw.js` — service worker (offline cache)
- `manifest.webmanifest`, `icons/` — PWA install metadata

Unofficial app. Data transcribed from the Trafford Council waste collection
calendar 2025–2026.
