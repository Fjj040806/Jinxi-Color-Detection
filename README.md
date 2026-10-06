---
title: Jinxi 360 Color Lens
emoji: 📷
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
license: mit
---

# Jinxi 360 Color Lens · Prototype 0.5

This version adds a small-sample positive-reference color model to the existing
360-degree field experience. A visitor frames a view, takes a virtual
photograph, and receives two coordinated forms of evidence:

1. **within-frame evidence** — which regions differ from their local context;
2. **reference evidence** — which region colors are uncommon among the supplied
   positive reference images.

The interface includes two linked visualization idioms. A **network view**
shows high-color-difference relationships among touching candidate and context
regions. A **spatial-temporal companion view** shows the fixed camera point,
current view direction, and a session timeline of captured frames.

The system proposes regions for review. It does **not** classify objects as
beautiful, ugly, culturally appropriate, authentic, or suitable for removal.

## Demo

![Jinxi Color Lens demo](media/demo.gif)

[Download the short MP4 demo](media/demo.mp4)

## What this version supports

- fixed-position 360° navigation with drag, touch, keyboard, wheel, zoom,
  reset, auto-rotation, fullscreen, and virtual shutter controls;
- automatic capture and analysis of the clean WebGL scene;
- SLIC superpixels, CIELAB measurements, CIEDE2000 distance, local color
  context, chroma lift, lightness difference, and color rarity;
- a learned memory of 28 reference-color prototypes from 13 supplied
  positive cases;
- equal contribution per reference image and capped region weights so broad
  sky, wall, or water areas do not dominate the memory;
- leave-one-reference-out calibration of the reference-novelty percentile;
- coordinated overlay, spatial mosaic, dominant palette, diagnostics, and
  ranked candidate views;
- a linked color-contrast network in which nodes are exact image regions and
  edges require both spatial adjacency and CIEDE2000 difference above the
  reported adaptive threshold;
- hover/click coordination between every network node and its precise region
  mask in the captured photograph;
- a fixed-point 2D site schematic with a live field-of-view cone and a
  clickable capture timeline that restores direction, field of view, frame,
  and analysis results;
- a bilingual **Learning & Evidence** page at `/learning` showing the reference
  cases, learned prototypes, calibration curve, interactive color inspector,
  evidence boundaries, and next-data requirements;
- a two-step session welcome that asks users to choose Simplified Chinese or
  English, then read and acknowledge the evidence boundary before entering;
- a persistent language preference plus a top-level control that reopens the
  product notice and links to the complete Learning & Evidence page;
- a cinematic motion mode with slow panorama movement, ambient light, animated
  reticle/network cues, pointer-responsive depth, staged result reveals, and
  automatic reduced-motion support.

The reference contribution is deliberately capped at 35% because the current
dataset contains only 13 user-selected images. The local detector remains the main source
of evidence.

## Review workflow

Choose Chinese or English in the first-session evidence notice, enter the fixed
360° observation point, frame and capture a view, then inspect the ranked
candidates. The results distinguish local-context evidence from reference
comparison and include a region-to-nearest-reference-color network. The diagnostics tab now renders animated SVG CIELAB scatter and feature bars
from measured API data. Hover/focus reveals values, and reduced-motion
preferences disable entrance animations. The interface follows shadcn/ui-style
Tabs, Card, and button conventions in the existing native HTML stack. Network
edges show measured CIEDE2000 distances; their lengths and layout do not encode
distance. Multiple candidates can share a prototype. Select a candidate node
to jump to its evidence card, and open “Why this result?” for interpretation.
The Learning & Evidence page remains available for detailed methodology.

The SDG 11.4 note connects evidence to community heritage discussion without
claiming that the tool establishes preservation decisions or measured SDG
impact. This version has one fixed panorama; a navigable Jinxi map requires
verified observation coordinates and additional scenes.

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

### Windows proxy / `403 Forbidden` during installation

If the terminal reports `Tunnel connection failed: 403 Forbidden`, the app has
not failed: a proxy blocked pip before packages such as NumPy and FastAPI could
be installed. The current `start_windows.bat` clears stale proxy settings for
that run and automatically retries with the Tsinghua PyPI mirror.

For a manual retry in PowerShell, from the project folder run:

```powershell
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""
$env:ALL_PROXY=""
$env:NO_PROXY="*"
$env:PIP_PROXY=""
$env:PIP_CONFIG_FILE="NUL"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
.\.venv\Scripts\python.exe app.py
```

Do not run `app.py` until the installation command finishes successfully.

## Run on macOS or Linux

```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

## Retrain the reference model

Use only images that you have permission to process. The current 13
watermark-free originals are included in `static/reference-originals/` because
the user confirmed permission to use and display them in this project. Record
specific license terms and creator credits when they become available.

```powershell
.\.venv\Scripts\python.exe train_reference_model.py reference-1.jpg reference-2.jpg reference-3.jpg --output reference_model.json --assets static/reference-derived --segments 220 --prototypes 28
```

Restart `app.py` after retraining so the API loads the new model. The model JSON
stores hashes, derived statistics, calibration, prototype colors, and public
paths to the permitted originals.

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

- These 13 references cannot represent Chinese historic towns, different
  communities, seasons, weather, times of day, or camera systems.
- Exposure, white balance, haze, editing, and shadows can change measured
  colors.
- The model learns color distribution only. It does not identify objects,
  materials, provenance, cultural meaning, or stakeholder preference.
- A high percentile means “rare in this reference set,” not “unattractive.”
- The network “hub” is the node with the most retained high-contrast local
  relationships. It is not an aesthetic verdict or an identified object.
- The companion site view is deliberately schematic. It is not surveyed,
  georeferenced, or evidence of an exact location.
- The user confirmed permission to use and display the supplied watermark-free
  reference images in this project. Specific license terms, creator credits,
  and capture metadata still need to be documented.
- Candidate regions require review with residents, planners, business owners,
  visitors, maintenance staff, and other affected stakeholders.

## Deploy to Hugging Face Spaces

Create a Docker Space and upload every file and folder in this project to the
repository root. The included `Dockerfile` launches the app on port 7860.
