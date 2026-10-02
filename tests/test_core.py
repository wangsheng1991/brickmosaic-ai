import csv
import json

import pytest
from PIL import Image

from brickmosaic_ai.cli import main
from brickmosaic_ai.core import make_plan, rgb_to_lab
from brickmosaic_ai.palette import PALETTE
from brickmosaic_ai.render import export_plan


def test_palette_colors_have_distinct_lab_values():
    labs = [rgb_to_lab(color.rgb) for color in PALETTE]
    assert len(labs) == len(set(labs))
    assert rgb_to_lab((255, 255, 255))[0] > rgb_to_lab((0, 0, 0))[0]


def test_transparency_is_an_empty_stud():
    image = Image.new("RGBA", (2, 1), (255, 0, 0, 255))
    image.putpixel((1, 0), (0, 0, 0, 0))
    plan = make_plan(image, width=2, height=1)
    assert plan.total_studs == 1
    assert plan.grid[0][1] is None


def test_color_limit_and_aspect_ratio():
    image = Image.new("RGB", (4, 2), (250, 0, 0))
    image.putpixel((0, 0), (0, 0, 255))
    plan = make_plan(image, width=4, max_colors=1)
    assert (plan.width, plan.height) == (4, 2)
    assert len(plan.counts) == 1
    assert plan.total_studs == 8


@pytest.mark.parametrize("options", [{"width": 0}, {"width": 129}, {"height": 129}, {"max_colors": 0}, {"alpha_threshold": 256}])
def test_invalid_sizes_fail(options):
    with pytest.raises(ValueError):
        make_plan(Image.new("RGB", (2, 2)), **options)


def test_exports_agree_on_total(tmp_path):
    image = Image.new("RGB", (3, 2), (220, 30, 30))
    plan = make_plan(image, width=3, height=2)
    export_plan(plan, tmp_path)
    assert (tmp_path / "mosaic.png").is_file()
    assert "<svg" in (tmp_path / "pattern.svg").read_text()
    data = json.loads((tmp_path / "plan.json").read_text())
    with (tmp_path / "parts.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert data["total_studs"] == sum(int(row["estimated_1x1_studs"]) for row in rows) == 6
    assert data["grid"] == [list(row) for row in plan.grid]


def test_cli_smoke_and_missing_image(tmp_path, capsys):
    source = tmp_path / "source.png"
    Image.new("RGB", (8, 8), (250, 200, 30)).save(source)
    assert main([str(source), "--width", "8", "--max-colors", "3", "-o", str(tmp_path / "output")]) == 0
    assert "8×8" in capsys.readouterr().out
    assert (tmp_path / "output" / "parts.csv").exists()
    assert main([str(tmp_path / "missing.png")]) == 2


def test_ai_uses_explicit_model(monkeypatch, tmp_path):
    """The AI path must never silently use rembg's possibly restricted default."""
    import sys
    import types

    from brickmosaic_ai.core import load_image

    source = tmp_path / "source.png"
    Image.new("RGB", (4, 4), "white").save(source)
    called = {}

    def new_session(model):
        called["model"] = model
        return object()

    def remove(image, session):
        assert session is not None
        return image

    monkeypatch.setitem(sys.modules, "rembg", types.SimpleNamespace(new_session=new_session, remove=remove))
    assert load_image(source, ai_background=True).size == (4, 4)
    assert called["model"] == "u2netp"
