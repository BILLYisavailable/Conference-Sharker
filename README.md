# Conference-Sharker

**Never miss a conference deadline again — always-on-top, second-precision, zero setup.**

Conference-Sharker is a tiny Windows desktop widget that stays on top of your screen and counts down every deadline that matters — **to the second**. No browser tabs. No config. No dependencies. Just run it and keep writing.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows&logoColor=white)
![Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Table of Contents

- [Why](#why)
- [Features](#features)
- [Color Coding](#color-coding)
- [Super Quick Start](#super-quick-start)
- [Usage](#usage)
- [Auto-start (Run on Windows startup)](#auto-start-run-on-windows-startup)
- [Data File](#data-file)
- [Project Structure](#project-structure)
- [FAQ](#faq)
- [License](#license)

## Why

Deadline sites are great, but you still have to *remember to check them*. Conference-Sharker flips that: it **pushes the countdown onto your desktop**, always visible, always ticking.

## Features

- **Always-on-top floating widget**: translucent, rounded corners, dark theme (Catppuccin Mocha)
- **Second-precision countdown**: automatically color-coded by urgency
- **Built-in calendar picker**: click to pick dates, no manual typing
- **Auto-start on login**: enable/disable anytime (one right-click)
- **Zero dependencies**: pure Python standard library (`tkinter`, `json`, `datetime`, ...)
- **Single file**: the entire app is one `.pyw` file — easy to hack and extend

## Color Coding

| Time Remaining | Color | Vibe |
|---|---|---|
| > 30 days | Green | Plenty of time (but start writing) |
| 7–30 days | Yellow | Getting real |
| 1–7 days | Orange | Crunch time |
| < 24 hours | Red | All-nighter territory |
| Past due | Gray | F |

## Super Quick Start

### Requirements

- Windows 10 / 11
- Python 3.7+ (during installation, it helps to check **Add Python to PATH**)

### Run (no installation step)

Just double-click:

- `Conference-Sharker.pyw`

Or run from PowerShell (no console window):

```powershell
pythonw .\Conference-Sharker.pyw
```

On first launch, it will create `deadlines.json` next to the program automatically.

### Optional: Build a standalone `.exe`

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name Conference-Sharker .\Conference-Sharker.pyw
```

The executable will be at `dist\Conference-Sharker.exe` and can run anywhere (no Python needed). It will also keep `deadlines.json` next to the `.exe`.

## Usage

### Widget Controls

| Action | How |
|---|---|
| Move the widget | Drag the title bar |
| Add a conference | Click **+ Add Conference** |
| Open manager panel | Click **≡ Manage** or the `≡` button |
| Collapse / expand | Click the `─` button |
| Edit / delete an entry | Right-click on a countdown card |
| Quit | Click `×` or right-click → **Quit** |

### Add a deadline

1. Click **+ Add Conference**
2. Enter **Paper Title** and **Conference**
3. Pick a date in the calendar
4. Set the time (defaults to 20:00:00)
5. Click **Save**

## Auto-start (Run on Windows startup)

Conference-Sharker supports starting automatically when you log in to Windows.

### Toggle auto-start in the app (recommended)

1. **Right-click anywhere** on the widget (including blank areas)
2. Click **Toggle Auto-start**
3. You will see a popup confirming **enabled** / **disabled**

### How it works (for troubleshooting)

It adds/removes an entry under this Windows Registry key:

- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

## Data File

All your data is stored in `deadlines.json`:

- **Running from source**: next to `Conference-Sharker.pyw`
- **Running from exe**: next to `Conference-Sharker.exe`

It’s plain JSON — feel free to back it up or sync it. Example:

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
Conference-Sharker/
├── Conference-Sharker.pyw   # Main app (double-click to run)
├── README.md
└── LICENSE
```

> `deadlines.json` is auto-generated on first run, so it typically isn’t committed.

## FAQ

### Double-click does nothing / exits immediately

- Make sure Python is installed and `python --version` works in a terminal
- Try launching from PowerShell to see if there are errors:

```powershell
pythonw .\Conference-Sharker.pyw
```

### Where is my data? Can I rename the file?

- The data filename is currently fixed in code as `deadlines.json`, always stored next to the program (`.pyw` or `.exe`).

## License

MIT
