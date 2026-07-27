"""Network — relationship health. Answers "managing and tracking relationships
and communication within the community and partner networks."

The useful question is not "who do I know" but "who is drifting", so the default
sort is by how far past cadence someone is.
"""

from ..components import (avatar, block, button, kpi, kpis, link, links, meter,
                          noresult, searchbox, segmented, tag, toolbar)
from ..util import Raw, ago, days_between, esc, fmt_date

SLUG = "network"
NAV = "Network"
TITLE = "Network"
SUB = "Who matters, how long it has been, and the shortest warm path to anyone new"

TIER_TONE = {"core": "ac", "active": "b", "dormant": "n"}
TIER_LABEL = {"core": "Core", "active": "Active", "dormant": "Dormant"}


def count(store):
    return len([p for p in store.people_with_rel() if overdue(p, store.today) > 0])


def anchors(store):
    # Only people with an explicit cadence are tracked here. A vendor rep is not
    # a relationship, and linking to one would be a lie about what this holds.
    return {p["id"] for p in store.people_with_rel()}


def overdue(person, today):
    rel = person["rel"]
    return days_between(rel["last_contact"], today) - rel["cadence_days"]


def health_tone(person, today):
    slip = overdue(person, today)
    if slip > 0:
        return "r" if slip > person["rel"]["cadence_days"] * 0.5 else "a"
    return "g"


def filters(person, today):
    out = [person["rel"]["tier"]]
    if overdue(person, today) > 0:
        out.append("drifting")
    if person["rel"]["owed_reply"]:
        out.append("owed")
    return out


def person_card(store, person):
    rel = person["rel"]
    today = store.today
    slip = overdue(person, today)
    elapsed = days_between(rel["last_contact"], today)
    tone = health_tone(person, today)
    org = store.person_org(person["id"])

    tags = [tag(TIER_LABEL[rel["tier"]], TIER_TONE[rel["tier"]])]
    if rel["owed_reply"]:
        tags.append(tag("You owe a reply", "r", dot=True))
    elif slip > 0:
        tags.append(tag(f"{slip}d past cadence", "a"))

    paths = ""
    if rel["intro_paths"]:
        route = rel["intro_paths"][0]
        paths = (f'<div style="margin-top:9px;font-size:12px;color:var(--ink-3)">'
                 f'Warm path · {links(store, route, " → ")}</div>')

    elsewhere = store.backlink_ids(person["id"], kinds=("threads", "meetings", "deals", "projects"))
    seen_in = ""
    if elsewhere:
        seen_in = (f'<div style="font-size:12px;color:var(--ink-3)">Also in · '
                   f'{links(store, elsewhere[:4])}</div>')

    return Raw(
        f'<article class="pcard" id="{esc(person["id"])}" '
        f'data-f="{esc(" ".join(filters(person, today)))}" '
        f'data-search="{esc(" ".join([person["name"], person["title"], org or "", rel["note"]]).lower())}">'
        f'<div class="hd">{avatar(person["name"], "lg")}<div style="min-width:0">'
        f'<div class="nm">{esc(person["name"])}</div>'
        f'<div class="ti">{esc(person["title"])}</div></div></div>'
        f'<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">'
        f'{"".join(str(t) for t in tags)}</div>'
        f'<div class="note">{esc(rel["note"])}</div>'
        f'<div class="cad"><div class="cadrow"><span>Last contact {esc(ago(rel["last_contact"], today))}</span>'
        f'<span>{esc(elapsed)}d / {esc(rel["cadence_days"])}d</span></div>'
        f'{meter(min(elapsed, rel["cadence_days"] * 2), rel["cadence_days"] * 2, tone)}</div>'
        f"{paths}"
        f'<div class="foot">{seen_in}</div></article>'
    )


def body(store):
    today = store.today
    people = store.people_with_rel()
    people.sort(key=lambda p: (-overdue(p, today), p["id"]))

    drifting = [p for p in people if overdue(p, today) > 0]
    owed = [p for p in people if p["rel"]["owed_reply"]]
    core = [p for p in people if p["rel"]["tier"] == "core"]

    tiles = kpis([
        kpi("Tracked", len(people), "people with an explicit cadence", "ac"),
        kpi("Core relationships", len(core), "the ones worth protecting", "b"),
        kpi("Past cadence", len(drifting), "drifting, not yet lost", "a"),
        kpi("Replies you owe", len(owed), "each has an open thread", "r"),
    ])

    counts = {}
    for person in people:
        for key in filters(person, today):
            counts[key] = counts.get(key, 0) + 1
    options = [("all", "Everyone", len(people))]
    for key, label in (("owed", "You owe"), ("drifting", "Drifting"),
                       ("core", "Core"), ("active", "Active"), ("dormant", "Dormant")):
        if counts.get(key):
            options.append((key, label, counts[key]))

    cards = ('<div class="pgrid" data-filterable>'
             + "".join(str(person_card(store, p)) for p in people) + "</div>")

    return Raw(
        str(tiles)
        + str(block("Relationships",
                    Raw(str(toolbar(segmented(options), searchbox("Search people, firms, notes")))
                        + cards + str(noresult())),
                    count=len(people),
                    note="Sorted by how far past cadence"))
    )
