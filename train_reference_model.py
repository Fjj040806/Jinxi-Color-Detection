"""Command-line trainer for the Jinxi positive-reference color model."""

from __future__ import annotations

import argparse
from pathlib import Path

from reference_model import train_reference_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Learn a transparent color memory from licensed positive reference images."
    )
    parser.add_argument("images", nargs="+", type=Path, help="Two or more reference images")
    parser.add_argument("--output", type=Path, default=Path("reference_model.json"))
    parser.add_argument(
        "--assets", type=Path, default=Path("static/reference-derived")
    )
    parser.add_argument("--segments", type=int, default=220)
    parser.add_argument("--prototypes", type=int, default=28)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = train_reference_model(
        args.images,
        args.output,
        args.assets,
        segment_detail=args.segments,
        prototype_count=args.prototypes,
    )
    print(
        f"Saved {model['prototype_count']} prototypes from "
        f"{model['reference_count']} references to {args.output}"
    )
    print(f"Model fingerprint: {model['fingerprint']}")


if __name__ == "__main__":
    main()
