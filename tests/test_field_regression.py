from pathlib import Path

from PIL import Image

from color_incongruity import analyze_color_context
from reference_model import load_reference_model


ROOT = Path(__file__).resolve().parents[1]


def test_lotus_field_frame_exposes_local_and_reference_evidence():
    """Keep one real field-derived frame as an inspectable regression case."""

    image = Image.open(ROOT / "evidence" / "lotus_yaw107_fov34.jpg").convert("RGB")
    model = load_reference_model(ROOT / "reference_model.json")
    result = analyze_color_context(
        image,
        sensitivity=84,
        segment_detail=260,
        top_candidates=5,
        mosaic_cells=18,
        language="en",
        reference_model=model,
    )

    assert list(result.table.columns[:4]) == [
        "候选区域",
        "综合复核分数 (0–100)",
        "局部对比分数 (0–100)",
        "参考新颖度分数 (0–100)",
    ]

    # Candidate #2 is the pink lotus region in this recorded framing. The test
    # verifies measured color evidence, not an aesthetic or removal judgment.
    lotus = result.table.iloc[1]
    assert lotus["代表色"] == "#9F7583"
    assert lotus["局部对比分数 (0–100)"] >= 90
    assert lotus["局部色差 ΔE00"] >= 27
    assert lotus["参考新颖度分数 (0–100)"] == 100
    assert lotus["参考新颖度百分位"] >= 99
    assert lotus["距参考色 ΔE00"] >= 19

    assert result.network["hub_id"] == "candidate-1"
    assert result.network["threshold_delta_e"] == 24.0
    assert len(result.network["nodes"]) == 14
    assert len(result.network["edges"]) == 9
