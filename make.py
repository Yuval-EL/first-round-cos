#!/usr/bin/env python3
"""Build the site: load -> validate -> render -> write.

    python make.py           build docs/
    python make.py --check   rebuild in memory and prove the output is unchanged

Everything on the site comes from data/ through this script. Nothing in docs/ is
hand-edited, which is what --check exists to prove.

Standard library only. No build step, no dependencies, no network.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path

from render import shell
from render.model import Store
from render.validate import validate
from render.views import (brief, build, day, dealflow, diligence, inbox,
                          network, projects)

# The nav is generated from this list, so a view that does not exist here simply
# is not part of the product — partial builds can never render broken links.
VIEWS = [brief, dealflow, diligence, inbox, day, network, projects, build]

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "docs"

ANCHOR_RE = re.compile(r'id="((?:per|co|deal|thr|mtg|prj|agt)_[a-z0-9_]+)"')
LINK_RE = re.compile(r'href="[a-z]+\.html#((?:per|co|deal|thr|mtg|prj|agt)_[a-z0-9_]+)"')


def filename(view):
    return "index.html" if view.SLUG == "brief" else f"{view.SLUG}.html"


def render_all(store):
    # Ask every view what it will anchor before rendering any of it, so href()
    # can decline to link at an entity nothing shows.
    rendered = set()
    for view in VIEWS:
        if hasattr(view, "anchors"):
            rendered.update(view.anchors(store))
    store.rendered = rendered

    pages = {}
    for view in VIEWS:
        pages[filename(view)] = shell.page(store, view, view.body(store), VIEWS)
    return pages


def audit_links(pages):
    """Every entity linked to must actually be rendered somewhere. Catches the
    case where a card is referenced but filtered out of its owning view."""
    anchors, links = set(), set()
    for html in pages.values():
        anchors.update(ANCHOR_RE.findall(html))
        links.update(LINK_RE.findall(html))
    return sorted(links - anchors)


def write(pages):
    OUT.mkdir(exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8", newline="\n")
    for name, html in sorted(pages.items()):
        # newline="\n" matters: text-mode writes on Windows would emit CRLF and
        # make byte-identical regeneration platform-dependent.
        (OUT / name).write_text(html, encoding="utf-8", newline="\n")


def check(pages):
    """Byte comparison, not text comparison — a CRLF that crept in is drift."""
    drift = []
    for name, html in sorted(pages.items()):
        path = OUT / name
        if not path.exists():
            drift.append(f"{name}: missing from docs/")
            continue
        on_disk = path.read_bytes()
        fresh = html.encode("utf-8")
        if on_disk == fresh:
            continue
        diff = difflib.unified_diff(
            on_disk.decode("utf-8", "replace").splitlines(),
            html.splitlines(),
            fromfile=f"docs/{name}", tofile="regenerated", lineterm="", n=1)
        body = "\n".join(list(diff)[:40])
        drift.append(body or f"{name}: differs only in line endings")
    return drift


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and diff against docs/ without writing")
    args = parser.parse_args()

    store = Store(DATA, live_pages={filename(v) for v in VIEWS})

    errors, warnings = validate(store)
    for warning in warnings:
        print(f"  warn  {warning}")
    if errors:
        print(f"\n{len(errors)} validation error(s):", file=sys.stderr)
        for error in errors:
            print(f"  error {error}", file=sys.stderr)
        return 1

    pages = render_all(store)

    broken = audit_links(pages)
    if broken:
        print(f"\n{len(broken)} link(s) point at entities no view renders:", file=sys.stderr)
        for entity_id in broken:
            print(f"  error dangling anchor: {entity_id}", file=sys.stderr)
        return 1

    if args.check:
        drift = check(pages)
        if drift:
            print("\ndocs/ does not match a fresh render:", file=sys.stderr)
            for item in drift:
                print(item, file=sys.stderr)
            return 1
        print(f"ok  {len(pages)} page(s) regenerate byte for byte")
        return 0

    write(pages)
    entities = len(store.ids)
    print(f"ok  {len(pages)} page(s), {entities} entities, "
          f"{store.edge_count()} edges -> docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
