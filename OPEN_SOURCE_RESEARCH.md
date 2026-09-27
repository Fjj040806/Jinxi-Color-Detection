# Open-source research basis

## Methods reviewed

### PatchCore

- Paper: <https://arxiv.org/abs/2106.08265>
- Official repository: <https://github.com/amazon-science/patchcore-inspection>

PatchCore represents nominal image patches in a memory bank and uses
nearest-neighbor distance to localize unusual patches. Its normal-only
formulation matches this project's need to learn from positive references
without requiring a complete catalogue of undesirable objects.

### PaDiM

- Paper: <https://arxiv.org/abs/2011.08785>

PaDiM models the distribution of pretrained patch embeddings at spatial
locations. It provides another one-class anomaly-detection baseline, but its
location-dependent assumptions are less suitable when the townscape camera
angle and composition vary strongly.

### Anomalib

- Official repository: <https://github.com/open-edge-platform/anomalib>

Anomalib collects multiple visual-anomaly methods, including PatchCore and
PaDiM. It is a useful future benchmarking framework once the project has a
larger licensed dataset and a stable evaluation protocol.

### DINOv2

- Official repository: <https://github.com/facebookresearch/dinov2>

DINOv2 provides general-purpose self-supervised visual features. These features
could complement color evidence with material, texture, and object-level
signals, but they would also make the current evidence chain harder to inspect.

## Why Prototype 0.3 uses a transparent color memory

The current evidence set has only three positive images. A deep model would add
deployment cost and apparent sophistication without solving the central data
problem. Prototype 0.3 therefore adopts the normal-only memory-bank idea while
keeping every feature visible:

- SLIC regions;
- CIELAB median colors;
- balanced reference contribution;
- MiniBatchKMeans prototypes;
- CIEDE2000 nearest-prototype distance;
- leave-one-reference-out empirical calibration;
- capped fusion with the existing within-frame detector.

This design supports an inspectable baseline and a meaningful future
comparison. A later PatchCore or DINOv2 experiment should use a train/validation
split, documented capture conditions, stakeholder-reviewed labels, region-level
metrics, and ablations comparing local-only, color-memory, and deep-feature
models.

## Open-source components used directly

The implementation uses NumPy, Pillow, scikit-image, scikit-learn, SciPy,
pandas, Matplotlib, FastAPI, Uvicorn, and python-multipart. PatchCore, PaDiM,
Anomalib, and DINOv2 were reviewed as research precedents but are **not** copied
or imported into Prototype 0.3.
