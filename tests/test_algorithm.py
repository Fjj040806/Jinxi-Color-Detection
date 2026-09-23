import numpy as np

from color_incongruity import analyze_color_context


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
