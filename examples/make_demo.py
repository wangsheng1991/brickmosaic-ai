"""Create a copyright-free toy rocket image for the README demo."""

from pathlib import Path

from PIL import Image, ImageDraw


root = Path(__file__).resolve().parent
image = Image.new("RGB", (512, 512), "#e9f3fa")
draw = ImageDraw.Draw(image)
draw.ellipse((40, 38, 470, 470), fill="#a7d8ec")
draw.ellipse((80, 350, 430, 560), fill="#91c66d")
draw.polygon([(256, 55), (184, 220), (328, 220)], fill="#c82732")
draw.rounded_rectangle((184, 165, 328, 392), radius=28, fill="#f5f5f0", outline="#424d5c", width=5)
draw.polygon([(184, 290), (134, 395), (184, 375)], fill="#2d65aa")
draw.polygon([(328, 290), (378, 395), (328, 375)], fill="#2d65aa")
draw.ellipse((218, 210, 294, 286), fill="#3694cb", outline="#424d5c", width=7)
draw.polygon([(224, 390), (256, 465), (288, 390)], fill="#f3c62b")
image.save(root / "rocket.png")
