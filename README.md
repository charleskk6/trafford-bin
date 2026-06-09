# Trafford Bin Collections

A small **web app (PWA)** that shows the Trafford Council waste collection
calendar (Nov 2025 – Nov 2026) and sends a **local notification the evening
before each collection** telling you which bins to put out.

## Features

- 📅 **Next collection** banner + full upcoming list
- 🔔 **Day-before reminders** via the browser Notification API (default 18:00, configurable)
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

Notifications require a **secure context** (`https://` or `localhost`). For use
on your phone, host the folder on any static host (e.g. GitHub Pages) over
HTTPS, open it, tap **Enable reminders**, then **Add to Home Screen**.

## How reminders work

- When the app is open it schedules timers for upcoming reminders.
- Where supported (Chrome's Notification Triggers API) reminders are registered
  with the service worker so they can fire even when the app is closed.
- As a fallback, each time you open the app it "catches up" — if a collection is
  due tomorrow and the reminder time has passed, it notifies you straight away.
- For the most reliable delivery, install the app to your home screen and open
  it once a day. (True scheduled push when fully closed needs a push server,
  which this offline-only app intentionally avoids.)

## Files

- `index.html` — layout
- `css/styles.css` — styling (light/dark)
- `js/data.js` — the calendar data + bin definitions
- `js/app.js` — rendering + notification scheduling
- `sw.js` — service worker (offline cache + notification clicks)
- `manifest.webmanifest`, `icons/` — PWA install metadata

Unofficial app. Data transcribed from the Trafford Council waste collection
calendar 2025–2026.
