# Validation record · Prototype 0.5

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

## Field-image checks

The following checks were recorded against the earlier three-reference model
and must be repeated before being treated as current quantitative evidence:

- The supplied pink-lotus image returned the lotus as candidate #1. The region
  covered 1.91% of the frame, had local `ΔE00 = 26.2`, and reached the 100th
  reference-novelty percentile (`ΔE00 = 21.4` from its nearest prototype).
- A supplied fish-decoration image placed the fish regions among the leading
  candidates and reached the 100th reference-novelty percentile.
- A held positive-reference image produced a lower top-candidate reference
  novelty of P79, illustrating that local and reference evidence are distinct.

They remain useful regression targets, but their exact scores are not claims
about the retrained 13-reference model. They do not establish accuracy,
cultural validity, or generalization.

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
