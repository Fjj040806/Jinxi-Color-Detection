"""Color-context analysis for automatically locating visually unusual regions.

The module intentionally measures contextual color difference rather than
beauty, heritage value, or design quality.  Every score is relative to the
other regions in the same image.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageDraw, ImageOps
from sklearn.cluster import MiniBatchKMeans
from skimage import color, morphology, segmentation


@dataclass
class AnalysisResult:
    overlay: np.ndarray
    mosaic: np.ndarray
    palette: np.ndarray
    diagnostics: np.ndarray
    table: pd.DataFrame
    summary: str
    score_map: np.ndarray
    segment_labels: np.ndarray


def _prepare_rgb(image: Any, max_side: int = 1100) -> np.ndarray:
    if image is None:
        raise ValueError("Please upload an image first.")

    if isinstance(image, Image.Image):
        pil = image.convert("RGB")
    else:
        array = np.asarray(image)
        if array.ndim == 2:
            array = np.repeat(array[..., None], 3, axis=2)
        if array.ndim != 3:
            raise ValueError("The input must be a grayscale, RGB, or RGBA image.")
        if array.shape[2] == 4:
            rgba = Image.fromarray(_to_uint8(array))
            base = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            pil = Image.alpha_composite(base, rgba).convert("RGB")
        else:
            pil = Image.fromarray(_to_uint8(array[..., :3]))

    if max(pil.size) > max_side:
        pil.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return np.asarray(pil, dtype=np.uint8)


def _to_uint8(array: np.ndarray) -> np.ndarray:
    array = np.asarray(array)
    if array.dtype == np.uint8:
        return array
    array = np.nan_to_num(array, nan=0.0, posinf=255.0, neginf=0.0)
    if array.size and float(np.max(array)) <= 1.0:
        array = array * 255.0
    return np.clip(array, 0, 255).astype(np.uint8)


def _robust_unit(values: np.ndarray, low: float = 5.0, high: float = 95.0) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    lo, hi = np.percentile(values, [low, high])
    if hi - lo < 1e-8:
        return np.zeros_like(values)
    return np.clip((values - lo) / (hi - lo), 0.0, 1.0)


def _percentile_rank(reference: np.ndarray, value: float) -> float:
    reference = np.asarray(reference, dtype=float)
    return float(100.0 * np.mean(reference <= value))


def _build_adjacency(labels: np.ndarray, count: int) -> list[set[int]]:
    adjacency = [set() for _ in range(count)]
    horizontal = np.stack((labels[:, :-1].ravel(), labels[:, 1:].ravel()), axis=1)
    vertical = np.stack((labels[:-1, :].ravel(), labels[1:, :].ravel()), axis=1)
    pairs = np.concatenate((horizontal, vertical), axis=0)
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    if pairs.size == 0:
        return adjacency
    pairs = np.unique(np.sort(pairs, axis=1), axis=0)
    for left, right in pairs:
        a, b = int(left), int(right)
        adjacency[a].add(b)
        adjacency[b].add(a)
    return adjacency


def _two_hop_neighbors(adjacency: list[set[int]], index: int) -> list[int]:
    first = set(adjacency[index])
    expanded = set(first)
    for neighbor in first:
        expanded.update(adjacency[neighbor])
    expanded.discard(index)
    return sorted(expanded)


def _hex(rgb: np.ndarray) -> str:
    channels = np.clip(np.rint(rgb), 0, 255).astype(int)
    return "#" + "".join(f"{value:02X}" for value in channels[:3])


def _analyze_segments(rgb: np.ndarray, requested_segments: int) -> dict[str, Any]:
    height, width = rgb.shape[:2]
    pixel_count = height * width
    effective_segments = int(np.clip(requested_segments, 40, min(650, max(40, pixel_count // 120))))
    rgb_float = rgb.astype(np.float32) / 255.0
    lab = color.rgb2lab(rgb_float)

    labels = segmentation.slic(
        rgb_float,
        n_segments=effective_segments,
        compactness=11.0,
        sigma=1.0,
        convert2lab=True,
        enforce_connectivity=True,
        start_label=0,
        channel_axis=-1,
    )
    count = int(labels.max()) + 1

    areas = np.bincount(labels.ravel(), minlength=count).astype(float)
    area_fraction = areas / pixel_count
    median_lab = np.zeros((count, 3), dtype=float)
    mean_rgb = np.zeros((count, 3), dtype=float)

    for index in range(count):
        mask = labels == index
        median_lab[index] = np.median(lab[mask], axis=0)
        mean_rgb[index] = np.mean(rgb[mask], axis=0)

    adjacency = _build_adjacency(labels, count)
    context_lab = np.zeros_like(median_lab)
    for index in range(count):
        neighbors = _two_hop_neighbors(adjacency, index)
        if not neighbors:
            neighbors = [j for j in range(count) if j != index]
        neighbor_array = np.asarray(neighbors, dtype=int)
        weights = areas[neighbor_array]
        context_lab[index] = np.average(median_lab[neighbor_array], axis=0, weights=weights)

    local_delta_e = color.deltaE_ciede2000(median_lab, context_lab)
    chroma = np.linalg.norm(median_lab[:, 1:3], axis=1)
    context_chroma = np.linalg.norm(context_lab[:, 1:3], axis=1)
    chroma_gap = np.abs(chroma - context_chroma)
    chroma_lift = np.maximum(chroma - context_chroma, 0.0)
    chromatic_delta = np.linalg.norm(
        median_lab[:, 1:3] - context_lab[:, 1:3], axis=1
    )
    lightness_gap = np.abs(median_lab[:, 0] - context_lab[:, 0])

    pairwise_delta_e = color.deltaE_ciede2000(
        median_lab[:, None, :], median_lab[None, :, :]
    )
    bandwidth = max(8.0, float(np.median(pairwise_delta_e[pairwise_delta_e > 0])) * 0.75)
    kernel = np.exp(-0.5 * (pairwise_delta_e / bandwidth) ** 2)
    np.fill_diagonal(kernel, 0.0)
    density = kernel @ area_fraction
    rarity = -np.log(np.clip(density, 1e-8, None))

    feature_units = {
        "local_delta_e": _robust_unit(local_delta_e),
        "chromatic_delta": _robust_unit(chromatic_delta),
        "chroma_lift": _robust_unit(chroma_lift),
        "lightness_gap": _robust_unit(lightness_gap),
        "rarity": _robust_unit(rarity),
    }
    # The detector is intentionally chromatic-first. Lightness receives a low
    # weight so that sky, reflections, and deep shadows do not automatically
    # outrank a locally unusual hue or saturation change.
    raw_score = (
        0.38 * feature_units["chromatic_delta"]
        + 0.23 * feature_units["chroma_lift"]
        + 0.17 * feature_units["local_delta_e"]
        + 0.07 * feature_units["lightness_gap"]
        + 0.15 * feature_units["rarity"]
    )

    small_region_factor = np.clip(np.sqrt(area_fraction / 0.0015), 0.35, 1.0)
    large_region_factor = np.where(
        area_fraction > 0.28, np.sqrt(0.28 / np.maximum(area_fraction, 1e-8)), 1.0
    )
    raw_score *= small_region_factor * large_region_factor
    scores = 100.0 * _robust_unit(raw_score, low=4.0, high=97.0)
    score_map = scores[labels]

    return {
        "rgb": rgb,
        "lab": lab,
        "labels": labels,
        "count": count,
        "areas": areas,
        "area_fraction": area_fraction,
        "median_lab": median_lab,
        "mean_rgb": mean_rgb,
        "adjacency": adjacency,
        "context_lab": context_lab,
        "local_delta_e": local_delta_e,
        "chroma_gap": chroma_gap,
        "chroma_lift": chroma_lift,
        "chromatic_delta": chromatic_delta,
        "lightness_gap": lightness_gap,
        "rarity": rarity,
        "feature_units": feature_units,
        "scores": scores,
        "score_map": score_map,
    }


def _candidate_masks(
    analysis: dict[str, Any], sensitivity: float, top_k: int
) -> list[np.ndarray]:
    labels = analysis["labels"]
    scores = analysis["scores"]
    area_fraction = analysis["area_fraction"]
    threshold = float(np.percentile(scores, np.clip(sensitivity, 55, 98)))
    selected = scores >= threshold
    selected &= area_fraction <= 0.32

    # Group only adjacent superpixels that are also chromatically similar. A
    # simple binary connected component can absorb unrelated background pieces
    # whenever several high-scoring regions touch at a corner.
    adjacency = analysis["adjacency"]
    median_lab = analysis["median_lab"]
    selected_ids = set(np.flatnonzero(selected).tolist())
    visited: set[int] = set()
    candidates: list[tuple[float, np.ndarray]] = []

    for seed in sorted(selected_ids, key=lambda idx: scores[idx], reverse=True):
        if seed in visited:
            continue
        component_ids: set[int] = set()
        stack = [seed]
        visited.add(seed)
        while stack:
            current = stack.pop()
            component_ids.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in selected_ids or neighbor in visited:
                    continue
                distance = float(
                    color.deltaE_ciede2000(median_lab[current], median_lab[neighbor])
                )
                if distance <= 13.0 and abs(scores[current] - scores[neighbor]) <= 32.0:
                    visited.add(neighbor)
                    stack.append(neighbor)

        ids = np.asarray(sorted(component_ids), dtype=int)
        mask = np.isin(labels, ids)
        fraction = float(mask.mean())
        if fraction < 0.00025 or fraction > 0.36:
            continue
        weights = analysis["areas"][ids]
        mean_score = float(np.average(scores[ids], weights=weights))
        max_score = float(np.max(scores[ids]))
        rank_score = 0.62 * max_score + 0.38 * mean_score
        candidates.append((rank_score, mask))

    candidates.sort(key=lambda item: item[0], reverse=True)

    # A fallback guarantees a useful result when the threshold leaves isolated
    # superpixels that were removed by morphology.
    if len(candidates) < top_k:
        used = np.zeros_like(labels, dtype=bool)
        for _, mask in candidates:
            used |= mask
        for segment_id in np.argsort(scores)[::-1]:
            mask = labels == int(segment_id)
            if np.any(mask & used):
                continue
            fraction = float(mask.mean())
            if 0.00025 <= fraction <= 0.32:
                candidates.append((float(scores[segment_id]), mask))
                used |= mask
            if len(candidates) >= top_k:
                break

    return [mask for _, mask in candidates[:top_k]]


def _candidate_metrics(
    analysis: dict[str, Any], masks: list[np.ndarray]
) -> list[dict[str, Any]]:
    labels = analysis["labels"]
    lab = analysis["lab"]
    rgb = analysis["rgb"]
    height, width = labels.shape
    output: list[dict[str, Any]] = []

    for rank, mask in enumerate(masks, start=1):
        segment_ids = np.unique(labels[mask])
        weights = analysis["areas"][segment_ids]
        segment_scores = analysis["scores"][segment_ids]
        score = 0.62 * float(np.max(segment_scores)) + 0.38 * float(
            np.average(segment_scores, weights=weights)
        )

        ring_radius = max(6.0, min(height, width) * 0.028)
        ring = morphology.isotropic_dilation(mask, radius=ring_radius) & ~mask
        if int(ring.sum()) < 25:
            ring = ~mask

        region_lab = np.median(lab[mask], axis=0)
        context_lab = np.median(lab[ring], axis=0)
        local_delta_e = float(color.deltaE_ciede2000(region_lab, context_lab))
        lightness_gap = float(abs(region_lab[0] - context_lab[0]))
        region_chroma = float(np.linalg.norm(region_lab[1:]))
        context_chroma = float(np.linalg.norm(context_lab[1:]))
        chroma_gap = float(abs(region_chroma - context_chroma))
        chroma_lift = float(max(region_chroma - context_chroma, 0.0))
        chromatic_delta = float(np.linalg.norm(region_lab[1:] - context_lab[1:]))
        rarity = float(np.average(analysis["rarity"][segment_ids], weights=weights))
        region_rgb = np.mean(rgb[mask], axis=0)
        coords = np.argwhere(mask)
        centroid_y, centroid_x = np.mean(coords, axis=0)

        output.append(
            {
                "rank": rank,
                "mask": mask,
                "score": float(np.clip(score, 0, 100)),
                "area_percent": float(100 * mask.mean()),
                "local_delta_e": local_delta_e,
                "lightness_gap": lightness_gap,
                "chroma_gap": chroma_gap,
                "chroma_lift": chroma_lift,
                "chromatic_delta": chromatic_delta,
                "rarity": rarity,
                "mean_rgb": region_rgb,
                "hex": _hex(region_rgb),
                "centroid": (float(centroid_x), float(centroid_y)),
                "feature_percentiles": {
                    "Local color gap": _percentile_rank(
                        analysis["local_delta_e"], local_delta_e
                    ),
                    "Chromatic distance": _percentile_rank(
                        analysis["chromatic_delta"], chromatic_delta
                    ),
                    "Chroma lift": _percentile_rank(
                        analysis["chroma_lift"], chroma_lift
                    ),
                    "Color rarity": _percentile_rank(analysis["rarity"], rarity),
                },
            }
        )
    return output


def _rerank_candidates(
    candidates: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """Rank a broad candidate pool using object-context color evidence.

    Segment scores are useful for proposing regions. The final ranking is
    recalculated after each region is compared with a surrounding ring. This
    reduces the chance that a tiny highlight wins simply because one
    superpixel is extreme.
    """

    if not candidates:
        return candidates

    chromatic = _robust_unit(
        np.asarray([item["chromatic_delta"] for item in candidates]), 0.0, 100.0
    )
    lift = _robust_unit(
        np.asarray([item["chroma_lift"] for item in candidates]), 0.0, 100.0
    )
    delta_e = _robust_unit(
        np.asarray([item["local_delta_e"] for item in candidates]), 0.0, 100.0
    )
    rarity = _robust_unit(
        np.asarray([item["rarity"] for item in candidates]), 0.0, 100.0
    )
    proposal = np.asarray([item["score"] for item in candidates]) / 100.0
    areas = np.asarray([item["area_percent"] for item in candidates])
    area_support = np.clip(np.sqrt(areas / 0.30), 0.58, 1.0)

    final = (
        0.42 * chromatic
        + 0.25 * lift
        + 0.13 * delta_e
        + 0.12 * rarity
        + 0.08 * proposal
    ) * area_support
    final = 100.0 * _robust_unit(final, 0.0, 100.0)

    for item, score in zip(candidates, final):
        item["score"] = float(score)
    candidates.sort(key=lambda item: item["score"], reverse=True)
    candidates = candidates[: int(top_k)]
    for rank, item in enumerate(candidates, start=1):
        item["rank"] = rank
    return candidates


def _overlay_image(
    rgb: np.ndarray, score_map: np.ndarray, candidates: list[dict[str, Any]]
) -> np.ndarray:
    normalized = _robust_unit(score_map, low=8.0, high=98.0)
    heat = (plt.get_cmap("inferno")(normalized)[..., :3] * 255).astype(np.uint8)
    alpha = (0.015 + 0.50 * normalized**1.65)[..., None]
    composite = np.clip(rgb * (1.0 - alpha) + heat * alpha, 0, 255).astype(np.uint8)

    outline_colors = [
        (255, 214, 102),
        (6, 214, 160),
        (17, 138, 178),
        (239, 71, 111),
        (155, 93, 229),
        (251, 133, 0),
        (0, 180, 216),
        (255, 0, 110),
    ]
    for index, candidate in enumerate(candidates):
        boundary = segmentation.find_boundaries(candidate["mask"], mode="outer")
        boundary = morphology.dilation(boundary, footprint=morphology.disk(1))
        composite[boundary] = outline_colors[index % len(outline_colors)]

    pil = Image.fromarray(composite)
    draw = ImageDraw.Draw(pil)
    for index, candidate in enumerate(candidates):
        x, y = candidate["centroid"]
        text = str(candidate["rank"])
        box = draw.textbbox((0, 0), text)
        text_width = box[2] - box[0]
        text_height = box[3] - box[1]
        radius = max(11, int(max(text_width, text_height) * 0.8))
        left, top = int(x - radius), int(y - radius)
        right, bottom = int(x + radius), int(y + radius)
        fill = outline_colors[index % len(outline_colors)]
        draw.ellipse((left, top, right, bottom), fill=fill, outline=(20, 24, 28), width=2)
        draw.text(
            (x - text_width / 2, y - text_height / 2 - 1),
            text,
            fill=(15, 18, 22),
        )

    # Add a compact legend so screenshots remain interpretable outside the app.
    footer_height = 58
    canvas = Image.new("RGB", (pil.width, pil.height + footer_height), (247, 246, 242))
    canvas.paste(pil, (0, 0))
    footer = ImageDraw.Draw(canvas)
    margin = max(18, int(pil.width * 0.04))
    bar_top = pil.height + 12
    bar_bottom = bar_top + 13
    bar_width = max(80, pil.width - 2 * margin)
    for offset in range(bar_width):
        value = offset / max(1, bar_width - 1)
        fill = tuple(
            np.rint(np.asarray(plt.get_cmap("inferno")(value)[:3]) * 255).astype(int)
        )
        footer.line(
            (margin + offset, bar_top, margin + offset, bar_bottom), fill=fill
        )
    low_label = "lower relative color contrast"
    high_label = "higher"
    footer.text((margin, bar_bottom + 6), low_label, fill=(55, 58, 62))
    high_box = footer.textbbox((0, 0), high_label)
    footer.text(
        (pil.width - margin - (high_box[2] - high_box[0]), bar_bottom + 6),
        high_label,
        fill=(55, 58, 62),
    )
    return np.asarray(canvas)


def _spatial_mosaic(rgb: np.ndarray, cells: int) -> np.ndarray:
    height, width = rgb.shape[:2]
    cells_x = int(np.clip(cells, 8, 36))
    cells_y = max(6, int(round(cells_x * height / width)))
    small = Image.fromarray(rgb).resize((cells_x, cells_y), Image.Resampling.BOX)
    scale = max(12, 900 // cells_x)
    mosaic = small.resize((cells_x * scale, cells_y * scale), Image.Resampling.NEAREST)
    mosaic = ImageOps.expand(mosaic, border=2, fill=(230, 230, 230))
    return np.asarray(mosaic)


def _dominant_palette(rgb: np.ndarray, colors_count: int = 7) -> np.ndarray:
    height, width = rgb.shape[:2]
    pixels = rgb.reshape(-1, 3)
    rng = np.random.default_rng(42)
    if len(pixels) > 30000:
        pixels = pixels[rng.choice(len(pixels), size=30000, replace=False)]
    lab_pixels = color.rgb2lab(pixels.reshape(-1, 1, 3) / 255.0).reshape(-1, 3)

    cluster_count = int(min(colors_count, max(2, len(lab_pixels))))
    model = MiniBatchKMeans(
        n_clusters=cluster_count,
        random_state=42,
        batch_size=2048,
        n_init="auto",
    )
    labels = model.fit_predict(lab_pixels)
    counts = np.bincount(labels, minlength=cluster_count).astype(float)
    proportions = counts / counts.sum()
    order = np.argsort(proportions)[::-1]
    centers_lab = model.cluster_centers_[order]
    proportions = proportions[order]
    centers_rgb = np.clip(
        color.lab2rgb(centers_lab.reshape(1, -1, 3)).reshape(-1, 3) * 255,
        0,
        255,
    )

    canvas_width, canvas_height = 1100, 230
    canvas = Image.new("RGB", (canvas_width, canvas_height), (247, 246, 242))
    draw = ImageDraw.Draw(canvas)
    cursor = 0
    for index, (center, proportion) in enumerate(zip(centers_rgb, proportions)):
        if index == len(proportions) - 1:
            next_cursor = canvas_width
        else:
            next_cursor = cursor + int(round(canvas_width * float(proportion)))
        color_tuple = tuple(np.rint(center).astype(int))
        draw.rectangle((cursor, 0, next_cursor, 165), fill=color_tuple)
        width = next_cursor - cursor
        if width >= 72:
            luminance = 0.2126 * center[0] + 0.7152 * center[1] + 0.0722 * center[2]
            text_color = (20, 23, 27) if luminance > 150 else (250, 250, 248)
            label = f"{100 * proportion:.1f}%"
            text_box = draw.textbbox((0, 0), label)
            draw.text(
                (
                    cursor + width / 2 - (text_box[2] - text_box[0]) / 2,
                    72,
                ),
                label,
                fill=text_color,
            )
        hex_label = _hex(center)
        if width >= 90:
            text_box = draw.textbbox((0, 0), hex_label)
            draw.text(
                (
                    cursor + width / 2 - (text_box[2] - text_box[0]) / 2,
                    188,
                ),
                hex_label,
                fill=(45, 48, 52),
            )
        cursor = next_cursor
    return np.asarray(canvas)


def _diagnostics_figure(
    analysis: dict[str, Any], candidates: list[dict[str, Any]]
) -> np.ndarray:
    figure, axes = plt.subplots(1, 2, figsize=(13.2, 5.2), dpi=130)
    figure.patch.set_facecolor("#F7F6F2")
    for axis in axes:
        axis.set_facecolor("#F7F6F2")

    median_lab = analysis["median_lab"]
    colors = np.clip(analysis["mean_rgb"] / 255.0, 0, 1)
    sizes = 18 + 3400 * np.sqrt(analysis["area_fraction"])
    axes[0].scatter(
        median_lab[:, 1],
        median_lab[:, 2],
        s=sizes,
        c=colors,
        alpha=0.62,
        edgecolors="#FFFFFF",
        linewidths=0.45,
    )
    marker_colors = ["#D6A700", "#00A67A", "#087FA8", "#D62C5E", "#7A42C1"]
    for index, candidate in enumerate(candidates):
        candidate_lab = color.rgb2lab(
            np.asarray(candidate["mean_rgb"], dtype=float).reshape(1, 1, 3) / 255.0
        ).reshape(3)
        axes[0].scatter(
            [candidate_lab[1]],
            [candidate_lab[2]],
            marker="*",
            s=245,
            color=marker_colors[index % len(marker_colors)],
            edgecolors="#16191D",
            linewidths=0.8,
            zorder=5,
        )
        axes[0].annotate(
            str(candidate["rank"]),
            (candidate_lab[1], candidate_lab[2]),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=9,
            color="#20242A",
            weight="bold",
        )
    axes[0].axhline(0, color="#C8C8C3", linewidth=0.8)
    axes[0].axvline(0, color="#C8C8C3", linewidth=0.8)
    axes[0].set_title("CIELAB color space", loc="left", fontsize=12, weight="bold")
    axes[0].set_xlabel("a*  ← green · red →")
    axes[0].set_ylabel("b*  ← blue · yellow →")
    axes[0].grid(color="#DAD9D4", linewidth=0.6, alpha=0.75)

    feature_names = [
        "Local color gap",
        "Chromatic distance",
        "Chroma lift",
        "Color rarity",
    ]
    if candidates:
        candidate_count = len(candidates)
        y_positions = np.arange(candidate_count)
        total_height = 0.72
        bar_height = total_height / len(feature_names)
        bar_colors = ["#E4572E", "#2E86AB", "#55A868", "#8172B2"]
        offsets = (np.arange(len(feature_names)) - 1.5) * bar_height
        for feature_index, feature_name in enumerate(feature_names):
            values = [
                candidate["feature_percentiles"][feature_name] for candidate in candidates
            ]
            axes[1].barh(
                y_positions + offsets[feature_index],
                values,
                height=bar_height * 0.86,
                label=feature_name,
                color=bar_colors[feature_index],
            )
        axes[1].set_yticks(y_positions)
        axes[1].set_yticklabels([f"Candidate {item['rank']}" for item in candidates])
        axes[1].invert_yaxis()
    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel("Percentile among regions in this image")
    axes[1].set_title("Why each region was flagged", loc="left", fontsize=12, weight="bold")
    axes[1].grid(axis="x", color="#DAD9D4", linewidth=0.6, alpha=0.75)
    axes[1].legend(frameon=False, fontsize=8, ncol=2, loc="lower right")

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#AAA9A4")
        axis.tick_params(colors="#3A3D42", labelsize=8)

    figure.tight_layout(pad=2.0)
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    array = np.asarray(canvas.buffer_rgba())[..., :3].copy()
    plt.close(figure)
    return array


def _results_table(candidates: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for candidate in candidates:
        rows.append(
            {
                "候选区域": f"#{candidate['rank']}",
                "相对色彩突出度 (0–100)": round(candidate["score"], 1),
                "画面面积 (%)": round(candidate["area_percent"], 2),
                "局部色差 ΔE00": round(candidate["local_delta_e"], 1),
                "色度距离 Δab": round(candidate["chromatic_delta"], 1),
                "明度差": round(candidate["lightness_gap"], 1),
                "彩度提升": round(candidate["chroma_lift"], 1),
                "代表色": candidate["hex"],
            }
        )
    return pd.DataFrame(rows)


def _summary(candidates: list[dict[str, Any]], sensitivity: float, segment_count: int) -> str:
    if not candidates:
        return (
            "No candidate regions were retained. Lower the sensitivity or increase the "
            "segmentation detail. This output measures color difference only."
        )
    first = candidates[0]
    return (
        f"检测到 {len(candidates)} 个候选区域。区域 #1 占画面 {first['area_percent']:.2f}%，"
        f"它与局部环境的 CIEDE2000 色差为 {first['local_delta_e']:.1f}。"
        f"当前灵敏度为 {sensitivity:.0f}，图像被划分为约 {segment_count} 个颜色区域。"
        "这些结果只表示同一张图片中的相对色彩异常，不表示美丑、文化价值或应当移除。"
    )


def analyze_color_context(
    image: Any,
    sensitivity: float = 84,
    segment_detail: int = 260,
    top_candidates: int = 5,
    mosaic_cells: int = 18,
) -> AnalysisResult:
    """Run color-only contextual anomaly analysis on one image."""

    rgb = _prepare_rgb(image)
    analysis = _analyze_segments(rgb, int(segment_detail))
    pool_size = max(int(top_candidates) * 3, 12)
    masks = _candidate_masks(analysis, float(sensitivity), pool_size)
    candidates = _candidate_metrics(analysis, masks)
    candidates = _rerank_candidates(candidates, int(top_candidates))

    return AnalysisResult(
        overlay=_overlay_image(rgb, analysis["score_map"], candidates),
        mosaic=_spatial_mosaic(rgb, int(mosaic_cells)),
        palette=_dominant_palette(rgb),
        diagnostics=_diagnostics_figure(analysis, candidates),
        table=_results_table(candidates),
        summary=_summary(candidates, float(sensitivity), analysis["count"]),
        score_map=analysis["score_map"],
        segment_labels=analysis["labels"],
    )
