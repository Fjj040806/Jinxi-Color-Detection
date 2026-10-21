# Advisor feedback response · final submission

| Advisor concern | Implemented response | Verification evidence |
|---|---|---|
| Confirm a real candidate has both Local Contrast and Reference Novelty | Added a fixed panorama-derived lotus frame and report the two signals separately | `evidence/README.md`; `tests/test_field_regression.py` |
| Use human-readable explanations | Candidate cards show separate named scores, qualitative reading aids, ΔE00, percentile, area, and nearest reference color | `static/index.html`; API candidate payload |
| Explain network nodes and edges | Added a permanent bilingual explainer and precise names for local-adjacency and reference-matching networks | `static/index.html` |
| Increase small spatial/network labels | Increased headings, map captions, timeline text, node labels, legends, and readout sizes | `static/index.html` CSS |
| Justify the 360° component | Reframed it as a way to test direction/FOV sensitivity; added a warning that framing changes segmentation and scores | scene card, guide, and evidence boundary |
| Verify browser → Python → analysis → visualization | `/api/health` now exposes version, build SHA, model fingerprint, implemented methods, and PatchCore status; the browser displays the result | `app.py`; `static/index.html`; `tests/test_api.py` |
| Match implementation to stated methods | Health manifest and documentation name SLIC, CIELAB, CIEDE2000, MiniBatchKMeans, and leave-one-reference-out calibration | `app.py`; `README.md`; `OPEN_SOURCE_RESEARCH.md` |
| Do not imply PatchCore is implemented | Added “research precedent · not implemented” labels and a machine-readable false status | `/learning`; `/api/health` |
| Improve usability evidence | Added a task-based protocol with comprehension, linkage, and framing-sensitivity checks | `USABILITY_TEST.md` |

No row should be interpreted as a cultural-validity claim. Community review,
reference-data expansion, and real user-study results remain future evidence.
