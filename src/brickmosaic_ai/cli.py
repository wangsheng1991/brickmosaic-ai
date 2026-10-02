"""Command-line entry point."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import load_image, make_plan
from .render import export_plan


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="brickmosaic",
        description="Turn an image into a local brick mosaic preview, grid and approximate parts list.",
    )
    command.add_argument("--version", action="version", version=f"brickmosaic-ai {__version__}")
    command.add_argument("image", type=Path, help="Input JPG, PNG or other Pillow-supported image")
    command.add_argument("-o", "--output", type=Path, default=Path("output"), help="Output directory (default: ./output)")
    command.add_argument("--width", type=int, default=48, help="Width in 1×1 studs, 1–128 (default: 48)")
    command.add_argument("--height", type=int, help="Height in studs; defaults to image aspect ratio")
    command.add_argument("--max-colors", type=int, default=12, help="Maximum number of palette colors, 1–18 (default: 12)")
    command.add_argument("--alpha-threshold", type=int, default=128, help="Pixels below this alpha are left empty, 0–255")
    command.add_argument("--ai-background", action="store_true", help="Remove background locally with U²-Net (u2netp); requires [ai] extra")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.image.is_file():
        print(f"Input file not found: {args.image}", file=sys.stderr)
        return 2
    try:
        image = load_image(args.image, ai_background=args.ai_background)
        plan = make_plan(image, width=args.width, height=args.height,
                         max_colors=args.max_colors, alpha_threshold=args.alpha_threshold)
        export_plan(plan, args.output)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {plan.width}×{plan.height} mosaic ({plan.total_studs} studs, {len(plan.counts)} colors) to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
