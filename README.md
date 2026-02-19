# Conference-Sharker

**Never miss a conference deadline again.**

You know the feeling — juggling three papers, each targeting a different venue, and suddenly realizing an abstract deadline was *yesterday*. You've been there. We've all been there.

Conference-Sharker is a tiny, always-on-top desktop widget that sits on your screen and counts down to every deadline that matters — **to the second**. No browser tabs. No bookmarks. No "let me check ccf-ddl real quick." Just a persistent, impossible-to-ignore reminder floating right next to your LaTeX editor.

![Python](https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Why This Exists

> I got tired of opening [ccf-ddl.github.io](https://ccf-ddl.github.io/) every single day just to check if I still had time. So I built a tool that tells me — always, automatically, right on my desktop.

The CCF deadline website is great, but it requires you to *actively* check it. Conference-Sharker flips that around: it **pushes** the countdown to you, always visible, always ticking. You can't forget what's staring you in the face.

## Features

- **Always-on-top floating widget** — translucent, rounded-corner dark theme (Catppuccin Mocha)
- **Second-precision countdown** — color-coded by urgency so you feel the pressure
- **Built-in calendar picker** — no more typing dates manually; just click
- **Startup with Windows** — one click to enable auto-start via the Registry
- **Zero dependencies** — pure Python standard library, ~20 MB memory footprint
- **Single file** — the entire app is one `.pyw` file, easy to hack and extend

## Countdown Color Coding

| Time Remaining | Color | Vibe |
|---|---|---|
| > 30 days | Green | Plenty of time (but start writing) |
| 7 – 30 days | Yellow | Getting real |
| 1 – 7 days | Orange | Crunch time |
| < 24 hours | Red | All-nighter territory |
| Past due | Gray | F |

## Quick Start

### Prerequisites

- Windows 10 / 11
- Python 3.7+ (make sure to check **"Add Python to PATH"** during installation)

### Run

Simply double-click `main.pyw`. That's it. No console window, no setup, no config files.

Or from the terminal:

```powershell
pythonw main.pyw
```

### Build a Standalone .exe (Optional)

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name Conference-Sharker main.pyw
```

The resulting `dist/Conference-Sharker.exe` runs anywhere — no Python needed.

## Usage

### Widget Controls

| Action | How |
|---|---|
| Move the widget | Drag the title bar |
| Add a conference | Click **"+ Add Conference"** at the bottom |
| Open manager panel | Click **"\u2261 Manage"** or the `\u2261` button in the title bar |
| Collapse / expand | Click the `\u2500` button |
| Edit / delete an entry | Right-click on any countdown card |
| Enable auto-start | Right-click anywhere → **"Toggle Auto-start"** |
| Quit | Click `\u00d7` or right-click → **"Quit"** |

### Adding a Conference

1. Click **"+ Add Conference"**
2. Enter your paper title and conference name
3. Pick the deadline date from the calendar
4. Adjust the time (defaults to 20:00, because most deadlines are "anywhere on Earth")
5. Hit **Save**

## Data Storage

All data lives in `deadlines.json` next to the executable. Back it up, sync it, version-control it — it's just JSON:

```json
{
  "deadlines": [
    {
      "id": "81eb827b",
      "paper": "My Awesome Paper",
      "conference": "NeurIPS",
      "deadline": "2026-05-08 20:00:00"
    }
  ],
  "pos": [100, 100]
}
```

## Project Structure

```
conference-sharker/
├── main.pyw          # The entire app (double-click to run)
├── deadlines.json    # Your data (auto-generated)
└── README.md
```

## Theme

UI powered by the [Catppuccin Mocha](https://github.com/catppuccin/catppuccin) color palette — easy on the eyes during those late-night paper-writing sessions.

## Contributing

Found a bug? Have an idea? PRs and issues welcome.

## License

MIT
