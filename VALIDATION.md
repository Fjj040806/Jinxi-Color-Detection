# Validation record · Prototype 0.6

## Advisor-feedback changes

- Candidate cards and the API now expose local contrast, reference novelty,
  and combined review score as three distinct quantities.
- The local adjacency network permanently defines nodes and edges, links each
  node to its exact photo region, and states that “hub” is not an aesthetic
  verdict. The two network tabs now have unambiguous names.
- Spatial-temporal labels and network labels were enlarged for presentation.
- The 360° interaction is justified as a framing-sensitivity test. The interface
  now warns that direction and field of view can change segments and scores.
- The browser displays the FastAPI/Python version and model fingerprint returned
  by `/api/health`, making the deployed analysis chain inspectable.
- The Learning & Evidence page labels PatchCore, Anomalib, and DINOv2 as
  research precedents that are not implemented.

## First-use and motion experience

- Each browser session begins with a two-step modal flow: language selection,
  followed by the evidence boundary and an explicit acknowledgement.
- The main interface becomes available only after acknowledgement. The product
  notice can be reopened from the top bar at any time, and the full Learning &
  Evidence record remains one click away.
- Language preference persists locally. Evidence acknowledgement lasts for the
  current browser session so a new session presents the notice again.
- Motion mode coordinates slow panorama rotation, ambient light, reticle and
  network motion. Pointer-responsive depth and staged result entrances provide
  feedback without changing the underlying data.
- `prefers-reduced-motion` disables decorative animation and removes the motion
  layer while retaining all controls and analysis functions.

## Added visualization idioms

- **Network:** candidate masks and their neighboring color regions are nodes.
  An edge is retained only when the two regions touch in the captured image
  and their CIEDE2000 difference exceeds the reported adaptive threshold
  (bounded to ΔE00 16–24). Hovering or focusing a node displays its exact mask
  over the captured photograph. The highest-degree node is labeled a
  color-contrast hub, not an aesthetic problem.
- **Spatial-temporal:** a top-down site schematic shows one fixed camera point,
  a live view-direction cone, and field of view. Each shutter action adds a
  browser-session timestamp and orientation. Selecting a history entry restores
  its view and analysis. The diagram is explicitly marked as non-surveyed and
  non-georeferenced.

## Reference model

- Thirteen user-supplied, watermark-free positive reference images were processed.
- The trainer retained 2,053 SLIC regions and compressed them to 28 CIELAB color
  prototypes.
- Each reference image contributed the same total weight.
- No fixed image zone was excluded because the supplied originals are watermark-free.
- Leave-one-reference-out calibration produced a positive-reference Q95 of
  `ΔE00 = 10.5314`.
- Model fingerprint: `25eb239bafb2bda1`.
- The user confirmed permission to use and display the originals in this project.
  Specific license terms, creator credits, and capture metadata remain unrecorded.

## Learning-sample interface

- Desktop layout displays five reference cards per row; tablet and mobile
  breakpoints reduce the column count without distorting the images.
- Each card front contains only the derived spatial color mosaic.
- Hover or keyboard focus flips the card; pointer exit restores the front.
- The back shows the permitted original, dominant-color palette, retained-region
  count, median chroma, and the current permission boundary.
- Touch users can toggle a card by tapping. Reduced-motion preference removes
  the animated transition while preserving the two-sided content.

## Field-image check against the current model

One exact 960 × 540 panorama-derived input is versioned at
`evidence/lotus_yaw107_fov34.jpg` (SHA-256 `e33cacc5…e94aa72`). With model
fingerprint `25eb239bafb2bda1`, sensitivity 84, detail 260, top-k 5, and mosaic
cells 18, the pink lotus region appears as candidate #2:

- combined review score: 80.7/100;
- local contrast score: 92.5/100;
- local CIEDE2000 difference: 27.8;
- reference novelty score: 100/100;
- reference novelty percentile: P99.8;
- nearest-reference CIEDE2000 difference: 19.7;
- representative color: `#9F7583`.

The local adjacency network contains 14 nodes and 9 retained edges at an
adaptive threshold of ΔE00 24.0. Candidate #1—not the lotus—is the highest-degree
hub, which demonstrates why hub degree and combined candidate ranking must not
be treated as the same claim. The automated regression test checks these values.
They do not establish accuracy, cultural validity, or generalization.

## Automated checks

- Python syntax compilation: passed.
- Front-end JavaScript parse checks: passed for the viewfinder and Learning &
  Evidence pages.
- Simplified Chinese and English translation keys: matched.
- Reference trainer: completed successfully.
- Algorithm unit tests: passed, including a synthetic magenta-patch case with
  reference-model evidence.
- FastAPI health, home, Learning & Evidence, and reference-model endpoints:
  passed, including HTTP 200 checks for all 13 original-image assets.
- End-to-end analysis request: HTTP 200 with overlay, mosaic, palette,
  diagnostics, ranked candidates, linked network data and masks, reference
  metrics, and claim boundary.
- GitHub Actions installs the pinned development test dependencies and runs the
  complete suite on every push to `main` and every pull request.

## Manual checks still recommended

- Open both `/` and `/learning` in Chrome or Edge on the presentation computer.
- Confirm WebGL hardware acceleration and test one virtual capture.
- Verify Chinese and English switching on both pages.
- Open a new private/incognito session and complete both welcome steps. Confirm
  that the acknowledgement is required, the keyboard focus stays inside the
  modal, and the top-bar notice control can reopen it.
- Turn on the operating system's reduced-motion setting and confirm that all
  functions remain usable without ambient or staged motion.
- Test the mobile layout if the prototype will be shown on a phone.
- Add specific license terms, creator credits, locations, capture dates, and
  weather/device metadata for all 13 references.
- Expand the demonstration set with seasonally and environmentally diverse
  evidence before interpreting results.
- Treat all candidate regions as prompts for inspection, not aesthetic labels.
- Run the task-based protocol in `USABILITY_TEST.md` with people who were not
  involved in development; report results before claiming usability.
