"""Product primitives.

Every function escapes its string arguments. View code never calls esc(); it
passes plain values, or Raw(...) for HTML it already assembled. That keeps the
escaping audit to a single file.
"""

from .util import Raw, esc

TONES = ("r", "a", "b", "g", "n", "ac")

AVATAR_COLORS = ("#3f3cd4", "#0f766e", "#b91c5c", "#9a5b06", "#1d4ed8",
                 "#6b21a8", "#0e7490", "#4d7c0f")


# ------------------------------------------------------------------ atoms

def tag(text, tone="n", dot=False):
    tone = tone if tone in TONES else "n"
    cls = f"tag t-{tone}" + (" dot" if dot else "")
    return Raw(f'<span class="{cls}">{esc(text)}</span>')


def initials(name):
    parts = [p for p in str(name).replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar(name, size=""):
    colour = AVATAR_COLORS[sum(ord(c) for c in str(name)) % len(AVATAR_COLORS)]
    cls = f"av {size}".strip()
    return Raw(f'<span class="{cls}" style="background:{colour}" title="{esc(name)}">'
               f"{esc(initials(name))}</span>")


def avatars(names, size="sm"):
    return Raw('<span class="avstack">' + "".join(str(avatar(n, size)) for n in names) + "</span>")


def meter(value, maximum=10, tone=None):
    pct = 0 if not maximum else max(0, min(100, round(100 * value / maximum)))
    cls = f"meter t-{tone}" if tone in TONES else "meter"
    return Raw(f'<span class="{cls}"><i style="width:{pct}%"></i></span>')


def kpi(label, value, sub=None, tone=None):
    cls = f"kpi t-{tone}" if tone in TONES else "kpi"
    sub_html = f'<div class="s">{esc(sub)}</div>' if sub else ""
    return Raw(f'<div class="{cls}"><div class="k">{esc(label)}</div>'
               f'<div class="v">{esc(value)}</div>{sub_html}</div>')


def kpis(tiles):
    return Raw('<div class="kpis">' + "".join(str(t) for t in tiles) + "</div>")


def link(store, entity_id, label=None):
    """Resolve an id to a link. Degrades to plain text when the owning view is
    not part of this build — never a dead link."""
    text = label if label is not None else store.label(entity_id)
    href = store.href(entity_id)
    if href is None:
        return Raw(esc(text))
    return Raw(f'<a class="lnk" href="{esc(href)}">{esc(text)}</a>')


def links(store, entity_ids, sep=" · "):
    return Raw(esc(sep).join(str(link(store, i)) for i in entity_ids))


def button(label, cls="btn", **attrs):
    extra = "".join(f' {k.replace("_", "-")}="{esc(v)}"' for k, v in attrs.items())
    return Raw(f'<button type="button" class="{esc(cls)}"{extra}>{esc(label)}</button>')


# --------------------------------------------------------------- containers

def block(title, inner, count=None, note=None):
    count_html = f'<span class="n">{esc(count)}</span>' if count is not None else ""
    note_html = f'<span class="note">{esc(note)}</span>' if note else ""
    return Raw(f'<div class="blk"><div class="blk-h"><h2>{esc(title)}</h2>'
               f'{count_html}{note_html}</div>{esc(inner)}</div>')


def segmented(options):
    """options: [(value, label, count)] — first entry is selected by default."""
    parts = []
    for index, (value, label, count) in enumerate(options):
        active = " active" if index == 0 else ""
        n = f'<span class="n">{esc(count)}</span>' if count is not None else ""
        parts.append(f'<button type="button" class="{active.strip()}" data-f="{esc(value)}">'
                     f"{esc(label)}{n}</button>")
    return Raw(f'<div class="seg">{"".join(parts)}</div>')


def searchbox(placeholder):
    glass = ('<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/>'
             '<path d="M20 20l-3.5-3.5"/></svg>')
    return Raw(f'<div class="srch">{glass}<input type="search" '
               f'placeholder="{esc(placeholder)}" aria-label="{esc(placeholder)}"></div>')


def toolbar(*items):
    return Raw('<div class="bar">' + "".join(str(i) for i in items) + "</div>")


def disclosure(uid, label, inner_html):
    btn = Raw(f'<button type="button" class="btn" data-toggle="{esc(uid)}" '
              f'aria-expanded="false" aria-controls="{esc(uid)}">{esc(label)}</button>')
    panel = Raw(f'<div class="dtl" id="{esc(uid)}"><div class="dtl-in">{esc(inner_html)}</div></div>')
    return btn, panel


def callout(heading, inner_html):
    return Raw(f'<div class="callout"><div class="h">{esc(heading)}</div>{esc(inner_html)}</div>')


def table(headers, rows):
    head = []
    for header in headers:
        if isinstance(header, (list, tuple)):
            head.append(f'<th class="{esc(header[1])}">{esc(header[0])}</th>')
        else:
            head.append(f"<th>{esc(header)}</th>")

    body = []
    for cells in rows:
        attrs = ""
        if isinstance(cells, dict):
            attrs = "".join(f' {k}="{esc(v)}"' for k, v in cells.get("attrs", {}).items())
            cells = cells["cells"]
        tds = []
        for cell in cells:
            if isinstance(cell, (list, tuple)):
                tds.append(f'<td class="{esc(cell[1])}">{esc(cell[0])}</td>')
            else:
                tds.append(f"<td>{esc(cell)}</td>")
        body.append(f"<tr{attrs}>" + "".join(tds) + "</tr>")

    return Raw(f'<div class="tbl"><div class="tbl-scroll"><table>'
               f'<thead><tr>{"".join(head)}</tr></thead>'
               f'<tbody>{"".join(body)}</tbody></table></div></div>')


def empty(big, sub=None):
    sub_html = f"<div>{esc(sub)}</div>" if sub else ""
    return Raw(f'<div class="panelbox empty"><div class="big">{esc(big)}</div>{sub_html}</div>')


def noresult(text="Nothing matches that filter."):
    return Raw(f'<div class="noresult">{esc(text)}</div>')


def lede(text):
    return Raw(f'<p class="lede">{esc(text)}</p>')


def bullets(items):
    return Raw("<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>")


def paras(*chunks):
    return Raw("".join(f"<p>{esc(c)}</p>" for c in chunks if c))


# ------------------------------------------------------------------- board

def column(key, name, tone, cards):
    colour = {"r": "var(--r)", "a": "var(--a)", "b": "var(--b)",
              "g": "var(--g)", "n": "var(--line-2)", "ac": "var(--accent)"}.get(tone, "var(--line-2)")
    return Raw(
        f'<div class="col" data-group="{esc(key)}">'
        f'<div class="col-h"><span class="dot" style="background:{colour}"></span>'
        f'<span class="nm">{esc(name)}</span><span class="n">{len(cards)}</span></div>'
        f'<div class="col-list">' + "".join(str(c) for c in cards) + "</div></div>"
    )


def board(columns, filterable=True):
    attr = " data-filterable" if filterable else ""
    return Raw(f'<div class="board"{attr}>' + "".join(str(c) for c in columns) + "</div>")
