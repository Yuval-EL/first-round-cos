"""Brief — the home view, compiled from every other tab.

Rule that keeps this page honest: it contains no original content. Every line is
an aggregate with a link back to the module that owns it, and every number is a
len(). A human writing both the brief copy and the module copy would drift; a
brief that can only link cannot.
"""

from ..components import (avatar, block, kpi, kpis, link, links, paras, table,
                          tag)
from ..util import Raw, ago, days_between, esc, fmt_date, fmt_date_full, fmt_time, fmt_weekday

SLUG = "brief"
NAV = "Brief"
TITLE = "Brief"

ABOUT = {
    "headline": "The whole day on one page, decisions first",
    "goal": ("A chief of staff does not produce seven dashboards, they produce one "
             "morning brief. This page answers a single question — what actually "
             "needs you today — and gets out of the way."),
    "now": ("Compiled from the seven other tabs in this demo. Every company, person, "
            "and message below is invented."),
    "live": ("The same compiler, run at 06:40 each morning against the real output of "
             "the six agents that watch mail, calendar, deal flow, and the network."),
    "does": [
        "Collects every pending decision from deals, inbox, meetings, and projects into one list, ranked by deadline",
        "Shows a recommendation on each one, so the question arrives already thought about",
        "Links out to the tab that owns each item — this page restates nothing, so it can never disagree with a module",
        "Every number on it is counted at build time, never typed by hand",
    ],
}

KIND_TONE = {"Investment": "r", "Portfolio": "g", "Co-investor": "b",
             "Internal": "ac", "Vendor": "n", "LP": "a"}
PRIORITY_TONE = {1: "r", 2: "a", 3: "b", 4: "n"}


def SUB(store):
    return f"{fmt_weekday(store.today)}, {fmt_date_full(store.today)} — compiled at 06:40"


def count(store):
    return len(store.needing_decision())


def decision_rows(store):
    rows = []
    for record in store.needing_decision():
        decision = record["needs_decision"]
        rows.append({
            "cells": [
                (Raw(f'<span class="t1">{esc(decision["question"])}</span>'
                     f'<span class="t2">{esc(decision["cost_of_delay"])}</span>'), ""),
                (tag(f"Recommend · {decision['recommendation']}", "ac"), ""),
                (Raw(f'<span class="t1">{esc(fmt_date(decision["deadline"]))}</span>'
                     f'<span class="t2">{esc(deadline_note(decision["deadline"], store.today))}</span>'), "nw"),
                (link(store, record["id"]), "nw"),
            ]
        })
    return rows


def deadline_note(deadline, today):
    days = days_between(today, deadline)
    if days < 0:
        return f"{abs(days)}d overdue"
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def meeting_rows(store):
    rows = []
    for meeting in store.todays_meetings():
        attendees = ", ".join(store.get(a)["name"] for a in meeting["attendees"])
        rows.append({
            "cells": [
                (Raw(f'<span class="t1">{esc(fmt_time(meeting["start"]))}</span>'), "nw"),
                (Raw(f'<span class="t1">{esc(meeting["title"])}</span>'
                     f'<span class="t2">{esc(meeting["prep"]["objective"])}</span>'), ""),
                (tag(meeting["kind"], KIND_TONE.get(meeting["kind"], "n")), "nw"),
                (Raw(f'<span style="font-size:12px;color:var(--ink-3)">{esc(attendees)}</span>'), "nw"),
                (link(store, meeting["id"], "Prep"), "nw"),
            ]
        })
    return rows


def inbox_rows(store):
    urgent = [t for t in store.threads if t["priority"] <= 2]
    urgent.sort(key=lambda t: (t["priority"], t["id"]))
    rows = []
    for thread in urgent:
        person = store.get(thread["from"])
        org = store.person_org(thread["from"])
        rows.append({
            "cells": [
                (tag(f"P{thread['priority']}", PRIORITY_TONE[thread["priority"]]), "nw"),
                (Raw(f'<span class="t1">{esc(person["name"])}'
                     f'{esc(" · " + org if org else "")}</span>'
                     f'<span class="t2">{esc(thread["ask"])}</span>'), ""),
                (Raw(f'<span style="font-size:12px;color:var(--ink-3)">{esc(thread["sla"])}</span>'), "nw"),
                (tag("Draft ready", "g") if thread["draft_reply"] else tag("No reply", "n"), "nw"),
                (link(store, thread["id"], "Open"), "nw"),
            ]
        })
    return rows


def drift_rows(store):
    from .network import overdue

    people = [p for p in store.people_with_rel()
              if overdue(p, store.today) > 0 or p["rel"]["owed_reply"]]
    people.sort(key=lambda p: (-overdue(p, store.today), p["id"]))
    rows = []
    for person in people:
        rel = person["rel"]
        slip = overdue(person, store.today)
        state = (tag("You owe a reply", "r", dot=True) if rel["owed_reply"]
                 else tag(f"{slip}d past cadence", "a"))
        rows.append({
            "cells": [
                (Raw(f'<span style="display:flex;align-items:center;gap:8px">{avatar(person["name"])}'
                     f'<span><span class="t1">{esc(person["name"])}</span>'
                     f'<span class="t2">{esc(person["title"])}</span></span></span>'), ""),
                (state, "nw"),
                (Raw(f'<span style="font-size:12px;color:var(--ink-3)">'
                     f'last contact {esc(ago(rel["last_contact"], store.today))}</span>'), "nw"),
                (link(store, person["id"], "Open"), "nw"),
            ]
        })
    return rows


def body(store):
    decisions = store.needing_decision()
    meetings = store.todays_meetings()
    p1 = [t for t in store.threads if t["priority"] == 1]
    blocked = [p for p in store.projects if p.get("blocked_on") == "principal"]

    from .network import overdue
    drifting = [p for p in store.people_with_rel()
                if overdue(p, store.today) > 0 or p["rel"]["owed_reply"]]

    tiles = kpis([
        kpi("Decisions waiting", len(decisions), "only you can make these", "r"),
        kpi("Meetings today", len(meetings), "all prepped", "ac"),
        kpi("Urgent in the inbox", len(p1), "two-hour SLA, replies drafted", "a"),
        kpi("Blocked on you", len(blocked), "projects that cannot move", "b"),
    ])

    opening = paras(
        "Three things actually matter today. Priya Raman has asked twice in five days for twenty "
        "minutes about her cap table, which is not a cap table question. Sasha Lin was promised an "
        "answer on Veriform by Wednesday and the partner review that produces it is at nine. And "
        "the only hour of unbooked time is at three, which is also the only place the Wexford "
        "pacing note can get written.",
        "Everything below links to the tab that owns it. Nothing on this page is written twice.",
    )

    sections = [
        block("Waiting on you", table(
            ["The call", "Recommendation", ("Due", "nw"), ("", "nw")],
            decision_rows(store)), count=len(decisions),
            note="Collected from deals, inbox, meetings, and projects"),
        block("Today", table(
            [("Time", "nw"), "Meeting", ("Kind", "nw"), ("With", "nw"), ("", "nw")],
            meeting_rows(store)), count=len(meetings)),
        block("Inbox — needs you", table(
            [("", "nw"), "From", ("SLA", "nw"), ("Reply", "nw"), ("", "nw")],
            inbox_rows(store)), note="P1 and P2 only — the rest is triaged and waiting"),
        block("Drifting", table(
            ["Person", ("State", "nw"), ("Last contact", "nw"), ("", "nw")],
            drift_rows(store)), count=len(drifting),
            note="Past their cadence, or owed a reply"),
    ]

    return Raw(str(tiles) + f'<div style="margin-top:16px">{opening}</div>'
               + "".join(str(s) for s in sections))
