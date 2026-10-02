"""Image sampling and deterministic brick-color assignment."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from .palette import PALETTE, Color


@dataclass(frozen=True)
class Plan:
    width: int
    height: int
    # None means no stud is needed at that coordinate.
    grid: tuple[tuple[int | None, ...], ...]
    palette: tuple[Color, ...]

    @property
    def counts(self) -> Counter[int]:
        return Counter(index for row in self.grid for index in row if index is not None)

    @property
    def total_studs(self) -> int:
        return sum(self.counts.values())


def _linear(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """Convert sRGB to CIE Lab (D65); nearest colors use Delta E 1976."""
    red, green, blue = (_linear(channel) for channel in rgb)
    x = (red * 0.4124564 + green * 0.3575761 + blue * 0.1804375) / 0.95047
    y = (red * 0.2126729 + green * 0.7151522 + blue * 0.0721750)
    z = (red * 0.0193339 + green * 0.1191920 + blue * 0.9503041) / 1.08883

    def f(value: float) -> float:
        return value ** (1 / 3) if value > 0.008856 else (7.787 * value + 16 / 116)

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _nearest(lab: tuple[float, float, float], candidates: tuple[int, ...], palette_labs: tuple[tuple[float, float, float], ...]) -> int:
    return min(candidates, key=lambda index: sum((a - b) ** 2 for a, b in zip(lab, palette_labs[index])))


def load_image(path: Path, *, ai_background: bool = False) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")
    if ai_background:
        try:
            from rembg import new_session, remove
        except ImportError as exc:
            raise RuntimeError('AI support is not installed. Run: pip install "brickmosaic-ai[ai]"') from exc
        # Explicit model: rembg's current default may have different license terms.
        try:
            image = remove(image, session=new_session("u2netp")).convert("RGBA")
        except Exception as exc:
            raise RuntimeError(f"Local AI background removal failed: {exc}") from exc
    return image


def make_plan(image: Image.Image, *, width: int = 48, height: int | None = None,
              max_colors: int = 12, alpha_threshold: int = 128,
              palette: tuple[Color, ...] = PALETTE) -> Plan:
    if not 1 <= width <= 128:
        raise ValueError("width must be between 1 and 128 studs")
    if height is None:
        height = max(1, round(image.height / image.width * width))
    if not 1 <= height <= 128:
        raise ValueError("height must be between 1 and 128 studs")
    if not 1 <= max_colors <= len(palette):
        raise ValueError(f"max_colors must be between 1 and {len(palette)}")
    if not 0 <= alpha_threshold <= 255:
        raise ValueError("alpha_threshold must be between 0 and 255")

    sampled = image.convert("RGBA").resize((width, height), Image.Resampling.BOX)
    rgba_bytes = sampled.tobytes()
    pixels = [tuple(rgba_bytes[index:index + 4]) for index in range(0, len(rgba_bytes), 4)]
    palette_labs = tuple(rgb_to_lab(color.rgb) for color in palette)
    all_indices = tuple(range(len(palette)))
    labs = [rgb_to_lab(pixel[:3]) if pixel[3] >= alpha_threshold else None for pixel in pixels]
    first_pass = [_nearest(lab, all_indices, palette_labs) if lab is not None else None for lab in labs]
    frequency = Counter(index for index in first_pass if index is not None)
    # Pick the most useful subset, then reassign every opaque cell within it.
    selected = tuple(index for index, _ in frequency.most_common(max_colors))
    grid_flat = [_nearest(lab, selected, palette_labs) if lab is not None and selected else None for lab in labs]
    grid = tuple(tuple(grid_flat[y * width:(y + 1) * width]) for y in range(height))
    return Plan(width=width, height=height, grid=grid, palette=palette)
