from pathlib import Path

import numpy as np

from color_incongruity import analyze_color_context
from reference_model import load_reference_model


ROOT = Path(__file__).resolve().parents[1]


def test_magenta_patch_is_returned_as_candidate():
    image = np.full((240, 320, 3), [115, 126, 110], dtype=np.uint8)
    image[80:150, 126:194] = [228, 44, 154]
    result = analyze_color_context(
        image,
        sensitivity=80,
        segment_detail=140,
        top_candidates=3,
        mosaic_cells=12,
    )
    assert not result.table.empty
    assert result.overlay.ndim == 3
    assert result.mosaic.ndim == 3
    assert result.palette.ndim == 3
    assert result.diagnostics.ndim == 3
    assert result.diagnostic_data["points"]
    assert result.diagnostic_data["candidates"]
    assert result.network["nodes"]
    assert result.network["hub_id"] in {node["id"] for node in result.network["nodes"]}
    assert result.network["threshold_delta_e"] >= 16
    assert result.network["edges"]
    assert all("mask" in node for node in result.network["nodes"])


def test_english_summary_is_available():
    image = np.full((180, 240, 3), [115, 126, 110], dtype=np.uint8)
    image[60:120, 90:150] = [228, 44, 154]
    result = analyze_color_context(
        image,
        sensitivity=80,
        segment_detail=100,
        top_candidates=2,
        mosaic_cells=10,
        language="en",
    )
    assert "candidate" in result.summary.lower()
    assert "beauty" in result.summary.lower()


def test_reference_model_prioritizes_a_magenta_patch():
    model = load_reference_model(ROOT / "reference_model.json")
    assert model is not None
    assert model["reference_count"] == 13
    assert model["prototype_count"] == 28

    image = np.full((240, 320, 3), [105, 119, 107], dtype=np.uint8)
    image[75:165, 120:210] = [239, 70, 158]
    result = analyze_color_context(
        image,
        sensitivity=80,
        segment_detail=140,
        top_candidates=3,
        mosaic_cells=12,
        language="en",
        reference_model=model,
    )

    first = result.table.iloc[0]
    assert first["参考新颖度百分位"] >= 98.5
    assert first["相对色彩突出度 (0–100)"] == 100
    assert result.model_info["enabled"] is True
    assert result.model_info["fingerprint"] == model["fingerprint"]
