# Inspectable field regression evidence

`lotus_yaw107_fov34.jpg` is a clean 960 × 540 view derived from the public
Jinxi panorama at relative yaw 107° and vertical field of view 34°. It is kept
in the repository so that the field claim can be rerun against the exact input,
parameters, model fingerprint, and code revision.

- Input SHA-256: `e33cacc553247ef0e8891bacd4a43cfd8e4ad798560e3303c746515c4e94aa72`
- Model fingerprint: `25eb239bafb2bda1`
- Parameters: sensitivity 84, detail 260, top-k 5, mosaic cells 18
- Candidate #2 (pink lotus region): combined review 80.7/100; local contrast
  92.5/100; local ΔE00 27.8; reference novelty 100/100; P99.8; nearest-reference
  ΔE00 19.7; representative color `#9F7583`
- Local adjacency network: 14 nodes, 9 retained edges, adaptive threshold
  ΔE00 24.0; candidate #1 is the highest-degree hub in this framing.

These values show that the lotus region receives both local-contrast and
reference-novelty evidence. They do not establish that it is ugly, culturally
inappropriate, or suitable for removal. A different direction, field of view,
exposure, segmentation detail, model, or code revision can change the result.

Run the case with:

```bash
python -m pytest tests/test_field_regression.py -q
```
