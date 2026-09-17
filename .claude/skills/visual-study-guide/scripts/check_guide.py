"""
check_guide.py - structural checks for a visual-guide.html study page.

Usage:
    python .claude/skills/visual-study-guide/scripts/check_guide.py <path/to/visual-guide.html>

Exit code 0 when every check passes, 1 otherwise. Run it after every edit of
the page and fix everything it reports before publishing. The checks encode
the mistakes that were caught by eye on the first guide (text spilling out of
SVG boxes, prose capped at a narrow width, an index that scrolls away, a
template placeholder left in) so they never have to be caught by eye again.
"""

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------------------
# Text-width estimation for SVG labels.
# Widths are estimated from character counts because nothing here can render
# fonts. The factors are deliberately generous (slightly wider than IBM Plex
# really is) so a label that passes here will fit in the browser.
# ---------------------------------------------------------------------------
SANS_PX = 12.0
MONO_PX = 11.0
TINY_PX = 10.5
SANS_FACTOR = 0.58   # average glyph width as a fraction of font-size
MONO_FACTOR = 0.62
BOX_MARGIN = 4       # px of breathing room required inside a box on each side

REQUIRED_IDS = ["tldr", "build", "traps"]
REQUIRED_MARKERS = [
    ("<title>", "a <title> tag at the top of the file"),
    ('class="side"', "the sticky left index (<aside class=\"side\">)"),
    ('class="tldr', "the TL;DR section (<section id=\"tldr\" class=\"tldr\">)"),
    ('details class="trap"', "at least one exam-trap card (<details class=\"trap\">)"),
    ("prefers-color-scheme: dark", "the dark-theme media query"),
    ('[data-theme="dark"]', "the explicit dark-theme override block"),
    ("<figcaption>", "at least one figure caption"),
]
FORBIDDEN = [
    (re.compile(r"<!doctype", re.I), "a <!doctype> tag (the Artifact tool adds the skeleton itself)"),
    (re.compile(r"<html[\s>]", re.I), "an <html> tag (write page content only)"),
    (re.compile(r"<head[\s>]", re.I), "a <head> tag (put <title> and <style> at the top of the file instead)"),
    (re.compile(r"<body[\s>]", re.I), "a <body> tag (write page content only)"),
    (re.compile(r"max-width:\s*\d+ch"), "a max-width in ch units (prose must use the full column width)"),
    (re.compile(r"\{\{[A-Z_]+\}\}"), "a {{PLACEHOLDER}} left over from the template"),
    (re.compile(r"<script[^>]+src="), "an external <script src> (the page must be self-contained)"),
    (re.compile(r"<br\s*/?>"), "a manual <br> line break in prose (let text wrap naturally)"),
]

VOID_TAGS = {"link", "meta", "br", "hr", "img", "input", "path", "rect", "line",
             "polygon", "circle", "polyline", "ellipse", "use", "stop"}


class BalanceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            return
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack or self.stack[-1][0] != tag:
            top = self.stack[-1] if self.stack else None
            self.errors.append(f"line {self.getpos()[0]}: closing </{tag}> but open tag is {top}")
        else:
            self.stack.pop()


def check_balance(src, report):
    p = BalanceParser()
    p.feed(src)
    for e in p.errors:
        report.fail(f"tag balance: {e}")
    for tag, line in p.stack:
        report.fail(f"tag balance: <{tag}> opened at line {line} is never closed")
    if not p.errors and not p.stack:
        report.ok("every tag is closed and nested correctly")


def check_markers(src, report):
    for needle, what in REQUIRED_MARKERS:
        if needle in src:
            report.ok(f"has {what}")
        else:
            report.fail(f"missing {what}")
    for pattern, what in FORBIDDEN:
        m = pattern.search(src)
        if m:
            line = src.count("\n", 0, m.start()) + 1
            report.fail(f"line {line}: contains {what}")
    for sec_id in REQUIRED_IDS:
        if re.search(rf'<section[^>]*id="{sec_id}"', src):
            report.ok(f"section #{sec_id} present")
        else:
            report.fail(f"section #{sec_id} is missing")


def check_index_links(src, report):
    nav = re.search(r'<aside class="side".*?</aside>', src, re.S)
    if not nav:
        return
    targets = re.findall(r'href="#([^"]+)"', nav.group(0))
    ids = set(re.findall(r'<section[^>]*id="([^"]+)"', src))
    missing = [t for t in targets if t not in ids]
    if missing:
        report.fail(f"index links point at sections that do not exist: {missing}")
    else:
        report.ok(f"all {len(targets)} index links resolve to a section")
    unlisted = [i for i in ids if i not in targets]
    if unlisted:
        report.warn(f"sections not listed in the index: {unlisted}")


def parse_attrs(tag_src):
    return dict(re.findall(r'([a-zA-Z\-:]+)="([^"]*)"', tag_src))


def estimate_width(text, classes, extra_attrs):
    n = len(text)
    if "mono" in classes:
        return n * MONO_PX * MONO_FACTOR
    if "tiny" in classes:
        return n * TINY_PX * SANS_FACTOR
    size = float(extra_attrs.get("font-size", SANS_PX))
    return n * size * SANS_FACTOR


def check_svgs(src, report):
    svgs = list(re.finditer(r"<svg\b(.*?)>(.*?)</svg>", src, re.S))
    if not svgs:
        report.warn("no inline <svg> found (a guide normally has at least one drawn figure)")
        return
    for idx, m in enumerate(svgs, start=1):
        head, body = m.group(1), m.group(2)
        attrs = parse_attrs(head)
        label = f"svg #{idx}"
        if "role" not in attrs or "aria-label" not in attrs:
            report.fail(f'{label}: needs role="img" and an aria-label describing the mechanism')
        vb = attrs.get("viewBox", "")
        try:
            _, _, vb_w, vb_h = [float(v) for v in vb.split()]
        except ValueError:
            report.fail(f"{label}: missing or malformed viewBox")
            continue
        before = src[: m.start()]
        if not re.search(r"<figure[^>]*>\s*<div class=\"fig-scroll\">\s*$", before):
            report.warn(f"{label}: should sit inside <figure><div class=\"fig-scroll\"> so it can scroll on narrow screens")

        rects = []
        for r in re.finditer(r"<rect\b([^>]*)/?>", body):
            a = parse_attrs(r.group(1))
            try:
                rects.append((float(a["x"]), float(a["y"]), float(a["width"]), float(a["height"])))
            except (KeyError, ValueError):
                pass

        overflow = 0
        for t in re.finditer(r"<text\b([^>]*)>(.*?)</text>", body, re.S):
            a = parse_attrs(t.group(1))
            raw = re.sub(r"<[^>]+>", "", t.group(2))
            text = html.unescape(raw).strip()
            if not text:
                continue
            try:
                x, y = float(a.get("x", "nan")), float(a.get("y", "nan"))
            except ValueError:
                continue
            classes = a.get("class", "").split()
            w = estimate_width(text, classes, a)
            anchor = a.get("text-anchor", "start")
            if anchor == "middle":
                left, right = x - w / 2, x + w / 2
            elif anchor == "end":
                left, right = x - w, x
            else:
                left, right = x, x + w
            if left < 0 or right > vb_w or y > vb_h or y < 0:
                report.fail(f'{label}: label "{text}" runs outside the viewBox ({vb_w:.0f}x{vb_h:.0f})')
                overflow += 1
                continue
            # innermost rect whose area contains the anchor point
            containing = [r for r in rects if r[0] <= x <= r[0] + r[2] and r[1] <= y <= r[1] + r[3]]
            if not containing:
                continue
            rx, ry, rw, rh = min(containing, key=lambda r: r[2] * r[3])
            if left < rx + BOX_MARGIN or right > rx + rw - BOX_MARGIN:
                need = int(w + 2 * BOX_MARGIN + 1)
                report.fail(
                    f'{label}: label "{text}" (~{w:.0f}px) does not fit its {rw:.0f}px-wide box at '
                    f"x={rx:.0f},y={ry:.0f}; widen the box to at least {need}px or shorten the label"
                )
                overflow += 1
        if overflow == 0:
            report.ok(f"{label}: every label fits its box and the viewBox")


class Report:
    def __init__(self):
        self.failures = 0
        self.lines = []

    def ok(self, msg):
        self.lines.append(f"  ok    {msg}")

    def warn(self, msg):
        self.lines.append(f"  warn  {msg}")

    def fail(self, msg):
        self.failures += 1
        self.lines.append(f"  FAIL  {msg}")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"not found: {path}")
        sys.exit(2)
    src = path.read_text(encoding="utf-8")
    report = Report()

    title = re.search(r"<title>(.*?)</title>", src[:8192])
    if title:
        words = title.group(1).split()
        if 2 <= len(words) <= 5 and not re.search(r"[:\-–—]", title.group(1)):
            report.ok(f'title "{title.group(1)}" is a short name')
        else:
            report.warn(f'title "{title.group(1)}" should be a 2-4 word name with no dash or colon')

    check_markers(src, report)
    check_balance(src, report)
    check_index_links(src, report)
    check_svgs(src, report)

    size_kb = len(src.encode("utf-8")) // 1024
    report.ok(f"file size {size_kb} KB")

    print(f"check_guide: {path}")
    print("\n".join(report.lines))
    if report.failures:
        print(f"\n{report.failures} problem(s) to fix before publishing.")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
