# Validation record

## Automated checks

- Python syntax compilation: passed for `app.py` and `color_incongruity.py`.
- Front-end JavaScript parse check: passed.
- Required interface-element check: passed.
- FastAPI health and home-page tests: 2 passed.
- End-to-end analysis request: HTTP 200.
- End-to-end response contained four expected images: overlay, mosaic, palette,
  and diagnostics.
- End-to-end response contained three requested candidate records and a claim-
  boundary summary.

## Test image result

One supplied Jinxi field photograph was submitted through the same API used by
the virtual shutter. At sensitivity 84, segmentation detail 180, and top-k 3,
the detector returned three candidates. The first candidate covered 2.16% of
the frame and had a local CIEDE2000 difference of 29.6.

## Manual checks still recommended

- Open the prototype in Chrome or Edge on the presentation computer.
- Confirm WebGL hardware acceleration is enabled.
- Test one capture at the intended presentation-window size.
- Check the mobile layout if the prototype will be demonstrated on a phone.
- Treat all candidate regions as prompts for inspection, not aesthetic labels.
