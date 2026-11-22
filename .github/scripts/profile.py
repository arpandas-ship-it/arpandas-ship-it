import json
import math
import os
from collections import Counter
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

def fetch(url):
    headers = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "User-Agent": "profile-graphics"}
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)

def radar(cx, title, names, values):
    def points(radii):
        pairs = []
        for i, radius in enumerate(radii):
            angle = i * 2 * math.pi / len(names) - math.pi / 2
            pairs.append((cx + radius * math.cos(angle), 160 + radius * math.sin(angle)))
        return pairs

    def polygon(radii, style):
        coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in points(radii))
        return f'<polygon points="{coords}" {style}/>'

    body = f'<text x="{cx}" y="30">{title}</text>'
    if len(names) < 3:
        return body + f'<text x="{cx}" y="160">At least three languages needed</text>'
    for ring in (25, 50, 75):
        body += polygon([ring] * len(names), 'fill="none" stroke="#314039"')
    maximum = max(values)
    body += polygon([75 * n / maximum for n in values], 'fill="#319459" fill-opacity=".48" stroke="#60db91"')
    for (x, y), name in zip(points([106] * len(names)), names):
        body += f'<text x="{x:.1f}" y="{y:.1f}" font-size="12">{escape(name)}</text>'
    return body

def svg(width, height, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
            f'<rect width="100%" height="100%" rx="10" fill="#101715"/>'
            f'<g fill="#d0e1d6" font-family="monospace" text-anchor="middle">{content}</g></svg>')

def main():
    owner = os.environ["USERNAME"]
    repos = []
    page = 1
    while True:
        batch = fetch(f"https://api.github.com/users/{owner}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    sizes, counts = Counter(), Counter()
    for repo in repos:
        if not repo["fork"]:
            languages = fetch(repo["languages_url"])
            sizes.update(languages)
            counts.update(languages.keys())
    names = [key for key, _ in sizes.most_common(6)]
    charts = radar(175, "Code size by language", names, [sizes[n] for n in names])
    charts += radar(525, "Repos using each language", names, [counts[n] for n in names])
    Path("assets/radar.svg").write_text(svg(700, 290, charts), encoding="utf-8")
    metrics = [(len(repos), "Public repos"), (sum(r["stargazers_count"] for r in repos), "Stars received"),
               (sum(r["forks_count"] for r in repos), "Forks received")]
    content = ""
    for i, (value, label) in enumerate(metrics):
        x = 110 + 220 * i
        content += f'<text x="{x}" y="44" fill="#64d893" font-size="27">{value}</text><text x="{x}" y="72">{label}</text>'
    Path("assets/numbers.svg").write_text(svg(660, 96, content), encoding="utf-8")

if __name__ == "__main__":
    main()
