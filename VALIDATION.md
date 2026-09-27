# Validation record · Prototype 0.3

## Reference model

- Three user-supplied positive reference images were processed.
- The trainer retained 506 SLIC regions and compressed them to 28 CIELAB color
  prototypes.
- Each reference image contributed the same total weight.
- The bottom-right provenance/watermark zone was excluded from fitting.
- Leave-one-reference-out calibration produced a positive-reference Q95 of
  `ΔE00 = 8.1258`.
- Model fingerprint: `9757bc4dfd13b0f2`.
- Raw reference images are not included in the distributable package.

## Field-image checks

At sensitivity 84, segmentation detail 220, and top-k 5:

- The supplied pink-lotus image returned the lotus as candidate #1. The region
  covered 1.91% of the frame, had local `ΔE00 = 26.2`, and reached the 100th
  reference-novelty percentile (`ΔE00 = 21.4` from its nearest prototype).
- A supplied fish-decoration image placed the fish regions among the leading
  candidates and reached the 100th reference-novelty percentile.
- A held positive-reference image produced a lower top-candidate reference
  novelty of P79, illustrating that local and reference evidence are distinct.

These checks confirm implementation behavior on the current examples. They do
not establish accuracy, cultural validity, or generalization.

## Automated checks

- Python syntax compilation: passed.
- Front-end JavaScript parse checks: passed for the viewfinder and Learning &
  Evidence pages.
- Simplified Chinese and English translation keys: matched.
- Reference trainer: completed successfully.
- Algorithm unit tests: passed, including a synthetic magenta-patch case with
  reference-model evidence.
- FastAPI health, home, Learning & Evidence, and reference-model endpoints:
  passed.
- End-to-end analysis request: HTTP 200 with overlay, mosaic, palette,
  diagnostics, ranked candidates, reference metrics, and claim boundary.

## Manual checks still recommended

- Open both `/` and `/learning` in Chrome or Edge on the presentation computer.
- Confirm WebGL hardware acceleration and test one virtual capture.
- Verify Chinese and English switching on both pages.
- Test the mobile layout if the prototype will be shown on a phone.
- Replace the three-reference demonstration set with licensed, documented,
  seasonally and environmentally diverse evidence before interpreting results.
- Treat all candidate regions as prompts for inspection, not aesthetic labels.
