"""A small, approximate brick-inspired palette.

These RGB values are visual approximations, not manufacturer specifications or
part/color availability guarantees. No official palette database is bundled.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    name: str
    hex: str

    @property
    def rgb(self) -> tuple[int, int, int]:
        return tuple(bytes.fromhex(self.hex.removeprefix("#")))  # type: ignore[return-value]


PALETTE: tuple[Color, ...] = (
    Color("White", "#f4f4f4"),
    Color("Black", "#1f2329"),
    Color("Light gray", "#b9bec5"),
    Color("Dark gray", "#595e67"),
    Color("Red", "#c42828"),
    Color("Dark red", "#802a31"),
    Color("Orange", "#e97624"),
    Color("Yellow", "#f5cc2d"),
    Color("Lime", "#a3cb42"),
    Color("Green", "#29935d"),
    Color("Dark green", "#205d48"),
    Color("Blue", "#266db5"),
    Color("Dark blue", "#263f83"),
    Color("Light blue", "#8bc9de"),
    Color("Tan", "#d9bd91"),
    Color("Brown", "#865135"),
    Color("Pink", "#eb9cbd"),
    Color("Purple", "#8359a0"),
)
