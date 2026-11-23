"""Style the generated night calendar and give every column a visible foundation."""
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
PATH = Path("profile-3d-contrib/profile-night-green.svg")
PALETTE = [
    ("#a9b4ae", "#89958e", "#74847b"),
    ("#b2e6b9", "#69a67c", "#45845c"),
    ("#79ce91", "#4b9c69", "#327e51"),
    ("#42ae68", "#348c58", "#216e41"),
    ("#218548", "#287e47", "#185e32"),
]


def pulse(animation, low, high):
    animation.attrib.update(values=f"{low};{high};{high};{low};{low}", dur="6s",
                            keyTimes="0;0.35;0.5;0.85;1", repeatCount="indefinite",
                            calcMode="spline", keySplines=";".join(["0.45 0 0.55 1"] * 4))


def style_calendar(path):
    tree = ET.parse(path)
    root = tree.getroot()
    style = root.find(f"{{{SVG}}}style")
    for level, colors in enumerate(PALETTE):
        for face, color in zip(("top", "left", "right"), colors):
            selector = rf"(\.cont-{face}-{level}\s*\{{\s*fill:\s*)[^;]+"
            style.text, matches = re.subn(selector, rf"\g<1>{color}", style.text)
            if matches != 1:
                raise ValueError(f"Missing calendar color for {face} {level}")

    tiles = root.find(f"{{{SVG}}}g")
    # A raised column shares the footprint of its ground tile.
    slope = math.tan(math.radians(30))
    ground = ET.Element(f"{{{SVG}}}g", id="calendar-ground", attrib={"aria-hidden": "true"})
    tiles.insert(0, ground)
    cells = []
    for tile in tiles.findall(f"{{{SVG}}}g"):
        top = tile.find(f"{{{SVG}}}rect")
        if top is None or not top.get("class", "").startswith("cont-top-"):
            continue
        x, y = map(float, tile.attrib["transform"][10:-1].split())
        motion = tile.find(f"{{{SVG}}}animateTransform")
        ground_y = float(motion.attrib["values"].split(";")[0].split()[1]) if motion is not None else y
        if motion is not None:
            # Preserve the generator's daily activity ordering, even within
            # the same color bucket. Compress tall columns for readability.
            raw_rise = ground_y - y
            rise = 36 * raw_rise / (raw_rise + 18)
            end = f"{x:g} {ground_y - rise:.2f}"
            tile.set("transform", f"translate({end})")
            pulse(motion, f"{x:g} {ground_y - rise * 0.4:.3f}", end)
            for side in tile.findall(f"{{{SVG}}}rect")[1:]:
                animation = side.find(f"{{{SVG}}}animate")
                initial = float(animation.attrib["values"].split(";")[0])
                height = f"{initial + rise / 1.15:.2f}"
                side.set("height", height)
                pulse(animation, f"{initial + rise * 0.4 / 1.15:.3f}", height)
        week = (x + ground_y / slope) / 2
        weekday = (x - ground_y / slope) / 2
        cells.append((week, weekday, tile, motion is not None))
    if not cells:
        raise ValueError("No calendar dates found")

    # Round away the upstream SVG's subpixel projection noise.
    first = min(w for w, _, _, _ in cells)
    low = min(d for _, d, _, _ in cells)
    last = max((w for w, _, _, active in cells if active), default=max(w for w, _, _, _ in cells))
    columns = round((last - first) / 20) + 1
    rows = round((max(d for _, d, _, _ in cells) - low) / 20) + 1
    for week, _, tile, _ in cells:
        if round((week - first) / 20) >= columns:
            tiles.remove(tile)

    def point(u, v, drop=0):
        return f"{u+v:.2f},{(u-v)*slope+drop:.2f}"

    def polygon(points, color):
        ET.SubElement(ground, f"{{{SVG}}}polygon", fill=color, points=" ".join(points))

    # A continuous rim meets the outer faces of the last week's blocks.
    end, high = first + columns * 20 - 2, low + rows * 20 - 2
    polygon([point(first, low), point(end, low), point(end, high), point(first, high)], "#74847b")
    polygon([point(end, low), point(end, high), point(end, high, 3), point(end, low, 3)], "#62736a")
    polygon([point(first, low), point(end, low), point(end, low, 3), point(first, low, 3)], "#89958e")
    for col in range(columns):
        for row in range(rows):
            u, v = first + col * 20, low + row * 20
            polygon([point(u, v), point(u+18, v), point(u+18, v+18), point(u, v+18)], PALETTE[0][0])
    tiles.set("transform", "translate(50 18) scale(0.89)")
    tree.write(Path("assets/contribution-calendar-animated.svg"), encoding="utf-8")


if __name__ == "__main__":
    style_calendar(PATH)
