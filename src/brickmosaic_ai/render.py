"""Export a preview, printable grid, machine-readable plan and parts count."""

import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

from .core import Plan


def render_preview(plan: Plan, path: Path, *, cell: int = 24) -> None:
    margin = 16
    image = Image.new("RGB", (plan.width * cell + margin * 2, plan.height * cell + margin * 2), "#f5f4f0")
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(plan.grid):
        for x, index in enumerate(row):
            if index is None:
                continue
            left, top = margin + x * cell, margin + y * cell
            right, bottom = left + cell - 2, top + cell - 2
            draw.rounded_rectangle((left, top, right, bottom), radius=3, fill=plan.palette[index].hex, outline="#403f3e", width=1)
            stud = max(3, cell // 5)
            cx, cy = left + cell // 2, top + cell // 2
            draw.ellipse((cx - stud, cy - stud, cx + stud, cy + stud), outline="#ffffff", width=1)
    image.save(path)


def render_pattern_svg(plan: Plan, path: Path, *, cell: int = 25) -> None:
    """SVG stays sharp when printed; the grid is a 1x1-stud visual plan."""
    margin = 38
    legend_height = 56 + 26 * len(plan.counts)
    width = plan.width * cell + margin * 2
    height = plan.height * cell + margin * 2 + legend_height
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
        '<title id="title">Brick mosaic pattern and color legend</title>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{margin}" y="23" font-family="Arial,sans-serif" font-size="16" font-weight="bold">Brick Mosaic AI · {plan.width} × {plan.height} studs</text>',
    ]
    for y, row in enumerate(plan.grid):
        for x, index in enumerate(row):
            left, top = margin + x * cell, margin + y * cell
            fill = plan.palette[index].hex if index is not None else "#ffffff"
            elements.append(f'<rect x="{left}" y="{top}" width="{cell}" height="{cell}" fill="{fill}" stroke="#777" stroke-width="0.5"/>')
            if index is not None:
                elements.append(f'<circle cx="{left + cell / 2}" cy="{top + cell / 2}" r="{cell * 0.22:.1f}" fill="none" stroke="#333" stroke-opacity=".5"/>')
    for x in range(plan.width):
        if x % 5 == 0 or plan.width <= 20:
            elements.append(f'<text x="{margin + x * cell + cell / 2}" y="{margin - 7}" text-anchor="middle" font-family="Arial,sans-serif" font-size="9">{x + 1}</text>')
    for y in range(plan.height):
        if y % 5 == 0 or plan.height <= 20:
            elements.append(f'<text x="{margin - 8}" y="{margin + y * cell + cell * .7}" text-anchor="end" font-family="Arial,sans-serif" font-size="9">{y + 1}</text>')
    legend_top = margin + plan.height * cell + 28
    elements.append(f'<text x="{margin}" y="{legend_top}" font-family="Arial,sans-serif" font-size="14" font-weight="bold">Approximate 1×1 parts: {plan.total_studs}</text>')
    for offset, (index, count) in enumerate(plan.counts.most_common(), start=1):
        y = legend_top + offset * 26
        color = plan.palette[index]
        elements.append(f'<rect x="{margin}" y="{y - 13}" width="18" height="18" fill="{color.hex}" stroke="#555"/>')
        elements.append(f'<text x="{margin + 28}" y="{y}" font-family="Arial,sans-serif" font-size="12">{escape(color.name)} · {count} · {color.hex}</text>')
    elements.append("</svg>\n")
    path.write_text("".join(elements), encoding="utf-8")


def write_parts_csv(plan: Plan, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["color", "hex_approximation", "estimated_1x1_studs"])
        for index, count in plan.counts.most_common():
            color = plan.palette[index]
            writer.writerow([color.name, color.hex, count])


def write_plan_json(plan: Plan, path: Path) -> None:
    data = {
        "format": "brickmosaic-ai-v1", "width": plan.width, "height": plan.height,
        "unit": "1x1 visual stud", "total_studs": plan.total_studs,
        "palette": [{"index": index, "name": color.name, "hex_approximation": color.hex}
                    for index, color in enumerate(plan.palette) if plan.counts[index]],
        "grid": [list(row) for row in plan.grid],
        "warning": "Visual mosaic estimate only; part availability, color accuracy, support and physical buildability are not verified.",
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def export_plan(plan: Plan, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    render_preview(plan, directory / "mosaic.png")
    render_pattern_svg(plan, directory / "pattern.svg")
    write_parts_csv(plan, directory / "parts.csv")
    write_plan_json(plan, directory / "plan.json")
