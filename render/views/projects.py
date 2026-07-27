"""Projects — special projects and events. Answers "managing Josh's projects and
events" and "initiating and leading special projects."

The only column that earns its place is the one separating what is blocked on the
principal from what is blocked on somebody else.
"""

from ..components import (avatars, block, callout, disclosure, kpi, kpis, link,
                          links, paras, table, tag)
from ..util import Raw, esc, fmt_date, until

SLUG = "projects"
NAV = "Projects"
TITLE = "Projects"
SUB = "What is moving, what is not, and specifically what is waiting on you"

STATUS_TONE = {"On track": "g", "At risk": "a", "Blocked": "r", "Shipped": "b"}
STATUS_ORDER = ["Blocked", "At risk", "On track", "Shipped"]


def count(store):
    return len([p for p in store.projects if p.get("blocked_on") == "principal"])


def anchors(store):
    return {p["id"] for p in store.projects}


def sort_key(project):
    order = STATUS_ORDER.index(project["status"]) if project["status"] in STATUS_ORDER else 99
    return (order, project["due"], project["id"])


def body(store):
    projects = sorted(store.projects, key=sort_key)
    on_you = [p for p in projects if p.get("blocked_on") == "principal"]
    decisions = [p for p in projects if p.get("needs_decision")]

    tiles = kpis([
        kpi("Active", len(projects), "running right now", "ac"),
        kpi("Blocked on you", len(on_you), "nothing moves until you move", "r"),
        kpi("At risk", len([p for p in projects if p["status"] == "At risk"]),
            "a date that will slip without a change", "a"),
        kpi("Needs a call", len(decisions), "a choice only you can make", "b"),
    ])

    head = str(tiles)
    for project in decisions:
        decision = project["needs_decision"]
        recommend = tag(f"Recommend · {decision['recommendation']}", "ac")
        inner = Raw(str(paras(decision["question"], decision["why"]))
                    + f'<div style="margin-top:8px;display:flex;gap:7px;flex-wrap:wrap;'
                      f'align-items:center">{recommend}'
                      f'{tag("By " + fmt_date(decision["deadline"]), "n")}</div>')
        head += f'<div style="margin-top:14px">{callout("Open question", inner)}</div>'

    rows = []
    for project in projects:
        people = [store.get(p)["name"] for p in project["people"]]
        blocked = project.get("blocked_on")
        blocked_cell = (str(tag("You", "r", dot=True)) if blocked == "principal"
                        else str(tag(blocked.title(), "a")) if blocked
                        else '<span style="color:var(--ink-3)">—</span>')
        due_slip = until(project["due"], store.today)
        due_cell = (f'<span class="t1">{esc(fmt_date(project["due"]))}</span>'
                    f'<span class="t2">{esc(due_slip)}</span>')
        name_cell = (f'<span class="t1">{esc(project["name"])}</span>'
                     f'<span class="t2">{esc(project["summary"])}</span>')
        next_cell = f'<span style="color:var(--ink-2)">{esc(project["next_step"])}</span>'
        rows.append({
            "attrs": {"id": project["id"]},
            "cells": [
                (Raw(name_cell), ""),
                (tag(project["status"], STATUS_TONE.get(project["status"], "n")), "nw"),
                (Raw(blocked_cell), "nw"),
                (Raw(due_cell), "nw"),
                (Raw(next_cell), ""),
                (avatars(people), "nw"),
            ],
        })

    grid = table(
        ["Project", "Status", "Blocked on", ("Due", "nw"), "Where it stands", "Who"],
        rows)

    return Raw(head + str(block("All projects", grid, count=len(projects),
                                note="Blocked first, then by due date")))
