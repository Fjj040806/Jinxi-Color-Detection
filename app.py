"""FastAPI application for the Jinxi 360 Color Lens prototype."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from starlette.concurrency import run_in_threadpool

from color_incongruity import analyze_color_context
from reference_model import load_reference_model


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
REFERENCE_MODEL_PATH = ROOT / "reference_model.json"
REFERENCE_MODEL = load_reference_model(REFERENCE_MODEL_PATH)
MAX_UPLOAD_BYTES = 18 * 1024 * 1024

app = FastAPI(
    title="Jinxi 360 Color Lens",
    description=(
        "A fixed-position 360-degree field prototype that captures a user-framed "
        "view and measures contextual color differences."
    ),
    version="0.5.0",
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _data_url(array, image_format: str = "PNG") -> str:
    image = Image.fromarray(array)
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    mime = "image/png" if image_format == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"


def _candidate_records(table) -> list[dict[str, object]]:
    records = []
    for row in table.to_dict(orient="records"):
        records.append(
            {
                "rank": str(row["候选区域"]),
                "score": float(row["相对色彩突出度 (0–100)"]),
                "area": float(row["画面面积 (%)"]),
                "delta_e": float(row["局部色差 ΔE00"]),
                "chromatic_distance": float(row["色度距离 Δab"]),
                "lightness_gap": float(row["明度差"]),
                "chroma_lift": float(row["彩度提升"]),
                "reference_percentile": float(row["参考新颖度百分位"]),
                "reference_delta_e": float(row["距参考色 ΔE00"]),
                "closest_reference_hex": str(row["最近参考色"]),
                "hex": str(row["代表色"]),
            }
        )
    return records


def _network_record(network: dict[str, object]) -> dict[str, object]:
    """Convert internal node masks to compact transparent PNG overlays."""

    nodes = []
    for node in network.get("nodes", []):
        record = {key: value for key, value in node.items() if key != "mask"}
        mask = np.asarray(node["mask"], dtype=bool)
        rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
        rgba[mask, :3] = (244, 190, 82) if node.get("is_hub") else (113, 216, 196)
        rgba[mask, 3] = 190
        record["mask"] = _data_url(rgba)
        nodes.append(record)
    return {
        **{key: value for key, value in network.items() if key != "nodes"},
        "nodes": nodes,
    }


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/learning", include_in_schema=False)
def learning() -> FileResponse:
    return FileResponse(STATIC / "learning.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.5.0",
        "reference_model": "ready" if REFERENCE_MODEL else "missing",
    }


@app.get("/api/reference-model")
def reference_model() -> dict[str, object]:
    if not REFERENCE_MODEL:
        raise HTTPException(status_code=503, detail="Reference model is not available.")
    return REFERENCE_MODEL


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    sensitivity: float = Form(84),
    detail: int = Form(260),
    top_k: int = Form(5),
    mosaic_cells: int = Form(18),
    language: str = Form("zh-CN"),
) -> dict[str, object]:
    english = language.lower().startswith("en")
    content = await image.read()
    if not content:
        message = "No captured image was received." if english else "没有收到截图。"
        raise HTTPException(status_code=400, detail=message)
    if len(content) > MAX_UPLOAD_BYTES:
        message = (
            "The captured image is too large. Reduce the browser window size and try again."
            if english
            else "截图过大，请缩小浏览器窗口后重试。"
        )
        raise HTTPException(status_code=413, detail=message)

    try:
        source = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as exc:
        message = "The captured image format could not be read." if english else "无法读取截图格式。"
        raise HTTPException(status_code=400, detail=message) from exc

    try:
        result = await run_in_threadpool(
            analyze_color_context,
            source,
            float(sensitivity),
            int(detail),
            int(top_k),
            int(mosaic_cells),
            language,
            REFERENCE_MODEL,
        )
    except Exception as exc:
        prefix = "Color analysis failed" if english else "色彩分析失败"
        raise HTTPException(status_code=500, detail=f"{prefix}: {exc}") from exc

    return {
        "summary": result.summary,
        "images": {
            "overlay": _data_url(result.overlay),
            "mosaic": _data_url(result.mosaic),
            "palette": _data_url(result.palette),
            "diagnostics": _data_url(result.diagnostics),
        },
        "candidates": _candidate_records(result.table),
        "network": _network_record(result.network),
        "diagnostic_data": result.diagnostic_data,
        "reference_model": result.model_info,
        "method": {
            "sensitivity": float(sensitivity),
            "segment_detail": int(detail),
            "top_k": int(top_k),
            "mosaic_cells": int(mosaic_cells),
            "language": "en" if english else "zh-CN",
            "reference_learning": (
                "Positive-reference color memory with leave-one-image-out calibration"
                if REFERENCE_MODEL
                else "Disabled"
            ),
            "network_definition": (
                "Nodes are candidate and adjacent context regions. Edges require image-space "
                "adjacency and CIEDE2000 difference above the reported adaptive threshold."
            ),
            "spatial_temporal_boundary": (
                "The two-dimensional site view is a schematic of one fixed camera point, not "
                "a surveyed or georeferenced map. Capture times are browser-session records."
            ),
            "claim_boundary": (
                "Results combine within-frame color contrast with a limited positive-reference "
                "color memory. They do not judge beauty, cultural value, object identity, or "
                "whether anything should be removed."
                if english
                else "结果结合画面内色彩差异与有限正面参考集，不表示美丑、文化价值、物体身份或应当移除。"
            ),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860)
