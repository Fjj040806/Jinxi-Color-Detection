"""Interpretable positive-reference color model for the Jinxi prototype.

The model is intentionally narrow. It learns a balanced memory of CIELAB
region colors from user-supplied positive reference images. It does not learn
beauty, heritage value, object identity, or a universal style standard.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from sklearn.cluster import MiniBatchKMeans
from skimage import color, segmentation


MODEL_VERSION = "0.3.0"
DEFAULT_SEGMENTS = 220
DEFAULT_PROTOTYPES = 28


def _to_hex(rgb: np.ndarray) -> str:
    channels = np.clip(np.rint(rgb), 0, 255).astype(int)
    return "#" + "".join(f"{value:02X}" for value in channels[:3])


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if not len(values):
        return 0.0
    order = np.argsort(values)
    values = values[order]
    weights = np.maximum(weights[order], 0.0)
    cumulative = np.cumsum(weights)
    if cumulative[-1] <= 0:
        return float(np.quantile(values, q))
    target = float(np.clip(q, 0.0, 1.0)) * cumulative[-1]
    return float(np.interp(target, cumulative, values))


def _prepare_rgb(path: Path, max_side: int = 900) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    if max(image.size) > max_side:
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def _watermark_mask(height: int, width: int) -> np.ndarray:
    """Mask the common bottom-right provenance/watermark zone.

    The source pixels remain untouched. The zone is excluded only from model
    fitting so publisher marks do not become part of the learned color memory.
    """

    mask = np.zeros((height, width), dtype=bool)
    mask[int(height * 0.90) :, int(width * 0.70) :] = True
    return mask


def _reference_segments(rgb: np.ndarray, requested_segments: int) -> dict[str, Any]:
    height, width = rgb.shape[:2]
    rgb_float = rgb.astype(np.float32) / 255.0
    lab = color.rgb2lab(rgb_float)
    labels = segmentation.slic(
        rgb_float,
        n_segments=int(np.clip(requested_segments, 80, 420)),
        compactness=11.0,
        sigma=1.0,
        convert2lab=True,
        enforce_connectivity=True,
        start_label=0,
        channel_axis=-1,
    )
    count = int(labels.max()) + 1
    pixel_count = height * width
    excluded = _watermark_mask(height, width)
    median_lab: list[np.ndarray] = []
    mean_rgb: list[np.ndarray] = []
    weights: list[float] = []

    for index in range(count):
        mask = labels == index
        area = int(mask.sum())
        if area < 12:
            continue
        if float(np.mean(excluded[mask])) > 0.22:
            continue
        area_fraction = area / pixel_count
        median_lab.append(np.median(lab[mask], axis=0))
        mean_rgb.append(np.mean(rgb[mask], axis=0))
        # Cap very large sky/wall/water regions and retain small architectural
        # regions so every image contributes a diverse color vocabulary.
        weights.append(float(np.clip(np.sqrt(area_fraction), 0.018, 0.095)))

    lab_array = np.asarray(median_lab, dtype=float)
    rgb_array = np.asarray(mean_rgb, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    if not len(lab_array):
        raise ValueError("No usable reference regions were extracted.")
    weight_array /= max(weight_array.sum(), 1e-12)
    return {
        "lab": lab_array,
        "rgb": rgb_array,
        "weights": weight_array,
        "labels": labels,
        "retained_count": int(len(lab_array)),
    }


def _fit_prototypes(
    lab: np.ndarray,
    weights: np.ndarray,
    count: int,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    cluster_count = int(np.clip(count, 2, max(2, len(lab))))
    model = MiniBatchKMeans(
        n_clusters=cluster_count,
        random_state=random_state,
        batch_size=max(64, min(512, len(lab))),
        n_init="auto",
    )
    assignments = model.fit_predict(lab, sample_weight=weights)
    support = np.bincount(assignments, weights=weights, minlength=cluster_count)
    order = np.argsort(support)[::-1]
    return model.cluster_centers_[order], support[order] / max(support.sum(), 1e-12)


def _nearest_delta_e(samples: np.ndarray, prototypes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    distances = color.deltaE_ciede2000(samples[:, None, :], prototypes[None, :, :])
    nearest = np.argmin(distances, axis=1)
    return distances[np.arange(len(samples)), nearest], nearest


def _palette_for_image(lab: np.ndarray, weights: np.ndarray, count: int = 6) -> list[dict[str, Any]]:
    centers, support = _fit_prototypes(lab, weights, min(count, len(lab)), random_state=7)
    rgb = np.clip(color.lab2rgb(centers.reshape(1, -1, 3)).reshape(-1, 3) * 255, 0, 255)
    return [
        {
            "hex": _to_hex(center_rgb),
            "weight": round(float(weight), 6),
            "lab": [round(float(value), 4) for value in center_lab],
        }
        for center_lab, center_rgb, weight in zip(centers, rgb, support)
    ]


def _derived_mosaic(rgb: np.ndarray, destination: Path, cells: int = 18) -> None:
    height, width = rgb.shape[:2]
    cells_x = cells
    cells_y = max(8, int(round(cells_x * height / width)))
    small = Image.fromarray(rgb).resize((cells_x, cells_y), Image.Resampling.BOX)
    mosaic = small.resize((cells_x * 16, cells_y * 16), Image.Resampling.NEAREST)
    mosaic = ImageOps.expand(mosaic, border=2, fill=(216, 211, 200))
    destination.parent.mkdir(parents=True, exist_ok=True)
    mosaic.save(destination, optimize=True)


def _derived_palette(palette: list[dict[str, Any]], destination: Path) -> None:
    width, height = 720, 92
    image = Image.new("RGB", (width, height), (239, 233, 220))
    draw = ImageDraw.Draw(image)
    cursor = 0
    for index, item in enumerate(palette):
        next_cursor = width if index == len(palette) - 1 else cursor + int(round(width * item["weight"]))
        draw.rectangle((cursor, 0, next_cursor, 62), fill=item["hex"])
        cursor = next_cursor
    draw.text((12, 70), "Derived color signature · raw reference not redistributed", fill=(42, 48, 45))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)


def _fingerprint(image_hashes: Sequence[str], prototypes: np.ndarray) -> str:
    digest = hashlib.sha256()
    for image_hash in image_hashes:
        digest.update(image_hash.encode("ascii"))
    digest.update(np.asarray(prototypes, dtype=np.float32).tobytes())
    return digest.hexdigest()[:16]


def train_reference_model(
    image_paths: Sequence[Path | str],
    output_path: Path | str,
    asset_dir: Path | str,
    labels: Sequence[str] | None = None,
    segment_detail: int = DEFAULT_SEGMENTS,
    prototype_count: int = DEFAULT_PROTOTYPES,
) -> dict[str, Any]:
    """Learn and save a balanced reference color memory from positive images."""

    paths = [Path(path) for path in image_paths]
    if len(paths) < 2:
        raise ValueError("At least two positive reference images are required.")
    if labels is None:
        labels = [f"Positive reference {index + 1}" for index in range(len(paths))]
    if len(labels) != len(paths):
        raise ValueError("The number of labels must match the number of images.")

    asset_root = Path(asset_dir)
    per_image: list[dict[str, Any]] = []
    all_lab: list[np.ndarray] = []
    all_weights: list[np.ndarray] = []
    image_hashes: list[str] = []

    for index, (path, label) in enumerate(zip(paths, labels), start=1):
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        image_hashes.append(file_hash)
        rgb = _prepare_rgb(path)
        segments = _reference_segments(rgb, segment_detail)
        palette = _palette_for_image(segments["lab"], segments["weights"])
        reference_id = f"ref-{index:02d}"
        mosaic_name = f"{reference_id}-mosaic.png"
        palette_name = f"{reference_id}-palette.png"
        _derived_mosaic(rgb, asset_root / mosaic_name)
        _derived_palette(palette, asset_root / palette_name)

        chroma = np.linalg.norm(segments["lab"][:, 1:3], axis=1)
        per_image.append(
            {
                "id": reference_id,
                "label": str(label),
                "sha256": file_hash,
                "dimensions": {"width": int(rgb.shape[1]), "height": int(rgb.shape[0])},
                "retained_regions": segments["retained_count"],
                "median_chroma": round(_weighted_quantile(chroma, segments["weights"], 0.5), 3),
                "p90_chroma": round(_weighted_quantile(chroma, segments["weights"], 0.9), 3),
                "palette": palette,
                "derived_mosaic": f"/static/reference-derived/{mosaic_name}",
                "derived_palette": f"/static/reference-derived/{palette_name}",
                "provenance": "user-supplied positive reference",
                "license": "not provided",
                "redistribution": "raw image excluded from project package",
                "watermark_handling": "bottom-right provenance zone excluded from fitting",
            }
        )
        # Equal total contribution per image prevents a large image or a broad
        # sky/wall region from dominating the learned reference memory.
        all_lab.append(segments["lab"])
        all_weights.append(segments["weights"] / len(paths))

    lab = np.concatenate(all_lab, axis=0)
    weights = np.concatenate(all_weights, axis=0)
    weights /= weights.sum()
    prototypes, prototype_support = _fit_prototypes(
        lab, weights, min(prototype_count, max(8, len(lab) // 5))
    )
    prototype_rgb = np.clip(
        color.lab2rgb(prototypes.reshape(1, -1, 3)).reshape(-1, 3) * 255,
        0,
        255,
    )

    # Leave-one-reference-out calibration: each positive image is compared to
    # a memory learned only from the other images. This avoids self-matches and
    # yields an honest small-sample novelty baseline.
    heldout_distances: list[np.ndarray] = []
    heldout_weights: list[np.ndarray] = []
    for heldout_index in range(len(paths)):
        train_lab = np.concatenate(
            [values for idx, values in enumerate(all_lab) if idx != heldout_index], axis=0
        )
        train_weights = np.concatenate(
            [values for idx, values in enumerate(all_weights) if idx != heldout_index], axis=0
        )
        train_weights /= train_weights.sum()
        fold_prototypes, _ = _fit_prototypes(
            train_lab,
            train_weights,
            min(20, max(6, len(train_lab) // 8)),
            random_state=100 + heldout_index,
        )
        distances, _ = _nearest_delta_e(all_lab[heldout_index], fold_prototypes)
        heldout_distances.append(distances)
        heldout_weights.append(all_weights[heldout_index])

    calibration_values = np.concatenate(heldout_distances)
    calibration_weights = np.concatenate(heldout_weights)
    calibration_weights /= calibration_weights.sum()
    percentiles = list(range(0, 101, 2))
    calibration_curve = [
        {
            "percentile": percentile,
            "delta_e": round(
                _weighted_quantile(calibration_values, calibration_weights, percentile / 100),
                5,
            ),
        }
        for percentile in percentiles
    ]

    fingerprint = _fingerprint(image_hashes, prototypes)
    reference_weight = 0.35
    model = {
        "model_version": MODEL_VERSION,
        "model_type": "balanced-superpixel-color-memory",
        "trained_on": str(date.today()),
        "fingerprint": fingerprint,
        "status": "prototype evidence",
        "reference_count": len(paths),
        "training_region_count": int(len(lab)),
        "prototype_count": int(len(prototypes)),
        "reference_weight": round(reference_weight, 3),
        "feature_space": "CIELAB median region color with CIEDE2000 matching",
        "training_method": [
            "SLIC superpixel extraction",
            "equal contribution from each reference image",
            "area-capped region weighting",
            "MiniBatchKMeans prototype compression",
            "leave-one-image-out novelty calibration",
        ],
        "prototype_colors": [
            {
                "rank": index + 1,
                "lab": [round(float(value), 5) for value in lab_color],
                "rgb": [int(round(value)) for value in rgb_color],
                "hex": _to_hex(rgb_color),
                "support": round(float(support), 7),
            }
            for index, (lab_color, rgb_color, support) in enumerate(
                zip(prototypes, prototype_rgb, prototype_support)
            )
        ],
        "calibration": {
            "method": "leave-one-reference-out nearest-prototype CIEDE2000",
            "curve": calibration_curve,
            "q50_delta_e": round(_weighted_quantile(calibration_values, calibration_weights, 0.50), 4),
            "q90_delta_e": round(_weighted_quantile(calibration_values, calibration_weights, 0.90), 4),
            "q95_delta_e": round(_weighted_quantile(calibration_values, calibration_weights, 0.95), 4),
        },
        "references": per_image,
        "evidence_boundaries": {
            "en": [
                "The model learns only the supplied color distributions; it does not learn beauty or cultural value.",
                f"{len(paths)} user-selected reference images do not establish representative coverage of historic towns, seasons, or communities.",
                "Weather, time of day, exposure, white balance, haze, and editing can shift measured colors.",
                "Composition and object frequency in the references affect which colors appear normal.",
                "The model does not recognize objects, materials, authenticity, safety, or historical significance.",
                "Candidates require review by residents, planners, designers, and other affected stakeholders.",
                "Source licenses were not provided; raw reference images are not redistributed.",
            ],
            "zh-CN": [
                "模型只学习所提供图片的色彩分布；它不学习美感或文化价值。",
                f"{len(paths)} 张用户选择的参考图不等于覆盖中国古镇、不同季节或不同社区的代表性数据集。",
                "天气、时间、曝光、白平衡、雾霾和后期处理都会改变测得的颜色。",
                "参考图的构图和物体出现频率会影响哪些颜色被模型视为常见。",
                "模型无法识别物体、材料、真实性、安全性或历史意义。",
                "候选区域仍需居民、规划者、设计者和其他受影响群体共同审查。",
                "参考图未提供使用许可，因此项目不分发原始图片。",
            ],
        },
        "recommended_next_evidence": {
            "en": [
                "Collect licensed images across seasons, weather, time of day, and camera devices.",
                "Record location, date, exposure, white balance, photographer, and permission metadata.",
                "Add stakeholder labels and task-based evaluation before making design recommendations.",
                "Compare this interpretable baseline with PatchCore or DINOv2 only after the dataset expands.",
            ],
            "zh-CN": [
                "收集覆盖不同季节、天气、时间和拍摄设备的授权图片。",
                "记录地点、日期、曝光、白平衡、摄影者和许可信息。",
                "在提出规划建议前加入利益相关者标注和基于任务的评估。",
                "数据扩展后，再将这一可解释基线与 PatchCore 或 DINOv2 做对照实验。",
            ],
        },
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return model


def load_reference_model(path: Path | str) -> dict[str, Any] | None:
    model_path = Path(path)
    if not model_path.exists():
        return None
    return json.loads(model_path.read_text(encoding="utf-8"))


def score_reference_colors(lab_values: np.ndarray, model: dict[str, Any] | None) -> dict[str, np.ndarray]:
    """Score region colors against the learned positive-reference memory."""

    samples = np.asarray(lab_values, dtype=float).reshape(-1, 3)
    if not model or not model.get("prototype_colors"):
        zeros = np.zeros(len(samples), dtype=float)
        return {
            "distance": zeros,
            "percentile": zeros,
            "score": zeros,
            "nearest_index": np.zeros(len(samples), dtype=int),
        }

    prototypes = np.asarray([item["lab"] for item in model["prototype_colors"]], dtype=float)
    distance, nearest = _nearest_delta_e(samples, prototypes)
    curve = model.get("calibration", {}).get("curve", [])
    curve_distance = np.asarray([item["delta_e"] for item in curve], dtype=float)
    curve_percentile = np.asarray([item["percentile"] for item in curve], dtype=float)
    if len(curve_distance) >= 2:
        curve_distance = np.maximum.accumulate(curve_distance)
        percentile = np.interp(distance, curve_distance, curve_percentile, left=0.0, right=100.0)
    else:
        percentile = np.zeros_like(distance)
    # Below-median reference distances carry no anomaly weight. The 95th
    # positive-reference percentile maps to full reference novelty.
    score = np.clip((percentile - 50.0) / 45.0, 0.0, 1.0) * 100.0
    return {
        "distance": distance,
        "percentile": percentile,
        "score": score,
        "nearest_index": nearest,
    }
