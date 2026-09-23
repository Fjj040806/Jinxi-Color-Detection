"""FastAPI application for the Jinxi 360 Color Lens prototype."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from starlette.concurrency import run_in_threadpool

from color_incongruity import analyze_color_context


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
MAX_UPLOAD_BYTES = 18 * 1024 * 1024

app = FastAPI(
    title="Jinxi 360 Color Lens",
    description=(
        "A fixed-position 360-degree field prototype that captures a user-framed "
        "view and measures contextual color differences."
    ),
    version="0.1.0",
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
                "hex": str(row["代表色"]),
            }
        )
    return records


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    sensitivity: float = Form(84),
    detail: int = Form(260),
    top_k: int = Form(5),
    mosaic_cells: int = Form(18),
) -> dict[str, object]:
    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="没有收到截图。")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="截图过大，请缩小浏览器窗口后重试。")

    try:
        source = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="无法读取截图格式。") from exc

    try:
        result = await run_in_threadpool(
            analyze_color_context,
            source,
            float(sensitivity),
            int(detail),
            int(top_k),
            int(mosaic_cells),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"色彩分析失败：{exc}") from exc

    return {
        "summary": result.summary,
        "images": {
            "overlay": _data_url(result.overlay),
            "mosaic": _data_url(result.mosaic),
            "palette": _data_url(result.palette),
            "diagnostics": _data_url(result.diagnostics),
        },
        "candidates": _candidate_records(result.table),
        "method": {
            "sensitivity": float(sensitivity),
            "segment_detail": int(detail),
            "top_k": int(top_k),
            "mosaic_cells": int(mosaic_cells),
            "claim_boundary": (
                "结果仅表示同一画面内的相对色彩差异，不表示美丑、文化价值或应当移除。"
            ),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860)
