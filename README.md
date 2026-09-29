---
title: Jinxi 360 Color Lens
emoji: 📷
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
license: mit
---

# Jinxi 360 Color Lens · Prototype 0.3

This version adds a small-sample positive-reference color model to the existing
360-degree field experience. A visitor frames a view, takes a virtual
photograph, and receives two coordinated forms of evidence:

1. **within-frame evidence** — which regions differ from their local context;
2. **reference evidence** — which region colors are uncommon among the supplied
   positive reference images.

The system proposes regions for review. It does **not** classify objects as
beautiful, ugly, culturally appropriate, authentic, or suitable for removal.

## Demo

> **Temporary workflow test.** This short clip verifies the repository video pattern. It will be replaced with a narrated or captioned final project walkthrough.

[![Short animated preview of the Jinxi Color Lens visualization](media/demo.gif)](media/demo.mp4)

[Watch the full demo video](media/demo.mp4)

## What this version supports

- fixed-position 360° navigation with drag, touch, keyboard, wheel, zoom,
  reset, auto-rotation, fullscreen, and virtual shutter controls;
- automatic capture and analysis of the clean WebGL scene;
- SLIC superpixels, CIELAB measurements, CIEDE2000 distance, local color
  context, chroma lift, lightness difference, and color rarity;
- a learned memory of 28 reference-color prototypes from three supplied
  positive cases;
- equal contribution per reference image and capped region weights so broad
  sky, wall, or water areas do not dominate the memory;
- leave-one-reference-out calibration of the reference-novelty percentile;
- coordinated overlay, spatial mosaic, dominant palette, diagnostics, and
  ranked candidate views;
- a bilingual **Learning & Evidence** page at `/learning` showing the reference
  cases, learned prototypes, calibration curve, interactive color inspector,
  evidence boundaries, and next-data requirements;
- persistent Simplified Chinese / English switching, responsive layout, and
  reduced-motion support.

The reference contribution is deliberately capped at 35% because the current
dataset contains only three images. The local detector remains the main source
of evidence.

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

Open:

- main experience: <http://127.0.0.1:7860/>
- learning and evidence: <http://127.0.0.1:7860/learning>

If an older interface remains visible, stop the old process with `Ctrl+C`,
start this folder's `app.py`, and refresh with `Ctrl+F5`.

## Run on macOS or Linux

```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

## Retrain the reference model

Use only images that you have permission to process. Keep the source files
outside the public project package unless their redistribution license is
confirmed.

```powershell
.\.venv\Scripts\python.exe train_reference_model.py reference-1.jpg reference-2.jpg reference-3.jpg --output reference_model.json --assets static/reference-derived --segments 220 --prototypes 28
```

Restart `app.py` after retraining so the API loads the new model. The model JSON
stores hashes, derived statistics, calibration, and prototype colors. It does
not store the raw photographs.

## Method

For each positive reference image, the trainer:

1. segments the image into spatially continuous regions with SLIC;
2. converts pixels to CIELAB and records the median color per region;
3. balances total contribution across images and caps large-region weight;
4. compresses region colors into prototypes with MiniBatchKMeans;
5. holds out each image in turn and measures its nearest-prototype CIEDE2000
   distance against the other images;
6. converts target-image distances into an empirical reference-novelty
   percentile;
7. fuses reference evidence with the original within-frame detector.

See `OPEN_SOURCE_RESEARCH.md` for the research basis and why the current
prototype uses a transparent color memory rather than a deep model.

## Evidence boundary

- Three references cannot represent Chinese historic towns, different
  communities, seasons, weather, times of day, or camera systems.
- Exposure, white balance, haze, editing, and shadows can change measured
  colors.
- The model learns color distribution only. It does not identify objects,
  materials, provenance, cultural meaning, or stakeholder preference.
- A high percentile means “rare in this reference set,” not “unattractive.”
- The supplied reference images did not include usage-license metadata. Their
  bottom-right provenance marks were excluded from model fitting, and the raw
  files are not redistributed in this package.
- Candidate regions require review with residents, planners, business owners,
  visitors, maintenance staff, and other affected stakeholders.

## Deploy to Hugging Face Spaces

Create a Docker Space and upload every file and folder in this project to the
repository root. The included `Dockerfile` launches the app on port 7860.
