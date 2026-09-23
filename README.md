---
title: Jinxi 360 Color Lens
emoji: 📷
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
license: mit
---

# Jinxi 360 Color Lens · Prototype 0.1

This prototype replaces the upload-first interaction with a fixed-position
360-degree field experience. A visitor chooses a viewing direction and field of
view, takes a virtual photograph, and receives coordinated color-context
evidence from the existing Jinxi detector.

## What this version supports

- drag, touch, keyboard, and wheel navigation inside one panorama;
- zoom, reset, auto-rotation, and fullscreen controls;
- a camera-style viewfinder and shutter interaction;
- automatic capture of the clean WebGL scene without interface overlays;
- a four-stage analysis feedback sequence;
- linked views for the captured frame, anomaly overlay, spatial mosaic,
  dominant palette, diagnostics, and ranked candidates;
- adjustable sensitivity, segmentation detail, and candidate count;
- responsive layout and reduced-motion support.

This is a **fixed camera position**. It supports viewing-angle changes but not
walking, translation, parallax, or measurement. The panorama is a reconstruction
from limited field material, so missing directions and architectural details
must not be treated as a survey of the actual site.

The detector reports relative color differences within one captured frame. It
does not decide whether an object is beautiful, ugly, culturally valuable, or
appropriate for removal.

## Run on Windows

The simplest method is to double-click `start_windows.bat`. On the first run it
creates `.venv` and installs the required packages. When the terminal displays
`http://127.0.0.1:7860`, open that address in Chrome or Edge. Keep the terminal
window open while using the prototype.

Manual PowerShell commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Run on macOS or Linux

```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

Then open <http://127.0.0.1:7860>.

## Interaction

- Drag or use arrow keys: change viewing direction.
- Mouse wheel or `+` / `-`: change field of view.
- Space: capture and analyze.
- Escape: close the result drawer.

## Deploy to Hugging Face Spaces

Create a Docker Space and upload every file and folder in this project to the
repository root. The included `Dockerfile` launches the app on port 7860.

## Analysis method

The algorithm uses SLIC superpixels and CIELAB color measurements. Its proposal
score combines local chromatic distance, positive chroma lift, CIEDE2000 color
difference, lightness difference, and global color rarity. Candidate regions
are then compared with their surrounding rings and re-ranked. The resulting
0–100 values are relative within the captured image and should not be compared
as absolute scores between different photographs.
