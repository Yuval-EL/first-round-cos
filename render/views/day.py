"""Day — the calendar as a timeline, with a prep brief attached to every meeting.

Answers "ensuring Josh is ready for every meeting and moment — prioritizing his
time and days around what matters most."
"""

from ..components import (avatars, block, bullets, callout, disclosure, kpi,
                          kpis, link, links, paras, tag)
from ..util import Raw, esc, fmt_time, fmt_weekday, fmt_date_full

SLUG = "day"
NAV = "Day"
TITLE = "Day"

KIND_TONE = {"Investment": "r", "Portfolio": "g", "Co-investor": "b",
             "Internal": "ac", "Vendor": "n", "LP": "a"}


def SUB(store):
    return (f"{fmt_weekday(store.today)}, {fmt_date_full(store.today)} — "
            "every meeting with the prep already done")


def count(store):
    return len(store.todays_meetings())


def anchors(store):
    return {m["id"] for m in store.todays_meetings()}


def minutes(meeting):
    start = int(meeting["start"][11:13]) * 60 + int(meeting["start"][14:16])
    end = int(meeting["end"][11:13]) * 60 + int(meeting["end"][14:16])
    return end - start


def duration_label(meeting):
    total = minutes(meeting)
    if total < 60:
        return f"{total}m"
    hours, mins = divmod(total, 60)
    return f"{hours}h" if not mins else f"{hours}h{mins:02d}"


def prep_html(store, meeting):
    prep = meeting["prep"]
    parts = [f"<h4>Objective</h4>{paras(prep['objective'])}"]
    if prep["context"]:
        parts.append(f"<h4>What you need to know</h4>{bullets(prep['context'])}")
    if prep["asks"]:
        parts.append(f"<h4>Worth asking</h4>{bullets(prep['asks'])}")
    if prep["watch_outs"]:
        parts.append(f"<h4>Watch out</h4>{bullets(prep['watch_outs'])}")
    open_threads = [t for t in prep["open_threads"] if t in store.ids]
    if open_threads:
        parts.append(f"<h4>Open with them</h4><div>{links(store, open_threads)}</div>")
    return Raw("".join(str(p) for p in parts))


def slot(store, meeting):
    tone = KIND_TONE.get(meeting["kind"], "n")
    attendees = [store.get(a)["name"] for a in meeting["attendees"]]
    btn, panel = disclosure(f"{meeting['id']}_prep", "Prep", prep_html(store, meeting))

    flagged = bool(meeting.get("needs_decision"))
    tags = [tag(meeting["kind"], tone)]
    if flagged:
        tags.append(tag("Recommend declining", "r", dot=True))

    related = [i for i in meeting["about"] if i in store.ids]
    related_html = f'<span style="font-size:12px;color:var(--ink-3)">{links(store, related)}</span>' if related else ""

    return Raw(
        f'<div class="slot t-{tone}">'
        f'<div class="clock">{esc(fmt_time(meeting["start"]))}'
        f'<span class="dur">{esc(duration_label(meeting))}</span></div>'
        f'<article class="mcard" id="{esc(meeting["id"])}">'
        f'<div style="display:flex;gap:7px;flex-wrap:wrap;align-items:center">'
        f'{"".join(str(t) for t in tags)}</div>'
        f'<div class="ttl" style="margin-top:8px">{esc(meeting["title"])}</div>'
        f'<div class="obj">{esc(meeting["prep"]["objective"])}</div>'
        f'<div class="who">{avatars(attendees)}'
        f'<span style="font-size:12px;color:var(--ink-3)">{esc(", ".join(attendees))}</span></div>'
        f'<div class="foot">{btn}{related_html}</div>{panel}</article></div>'
    )


def body(store):
    meetings = store.todays_meetings()
    booked = sum(minutes(m) for m in meetings)
    flagged = [m for m in meetings if m.get("needs_decision")]

    # Largest uninterrupted gap between 08:00 and 18:00.
    day_start, day_end = 8 * 60, 18 * 60
    busy = sorted((int(m["start"][11:13]) * 60 + int(m["start"][14:16]),
                   int(m["end"][11:13]) * 60 + int(m["end"][14:16])) for m in meetings)
    cursor, largest = day_start, 0
    for start, end in busy:
        largest = max(largest, start - cursor)
        cursor = max(cursor, end)
    largest = max(largest, day_end - cursor)

    hours, mins = divmod(booked, 60)
    gap_h, gap_m = divmod(largest, 60)

    tiles = kpis([
        kpi("Meetings", len(meetings), "08:00 to 17:00", "ac"),
        kpi("Booked", f"{hours}h{mins:02d}", "of a ten-hour day", "b"),
        kpi("Longest clear block", f"{gap_h}h{gap_m:02d}", "the only place real work fits", "g"),
        kpi("Flagged", len(flagged), "recommended for decline", "r" if flagged else "n"),
    ])

    head = str(tiles)
    for meeting in flagged:
        decision = meeting["needs_decision"]
        recommend = tag(f"Recommend · {decision['recommendation']}", "ac")
        inner = Raw(str(paras(decision["question"], decision["why"]))
                    + f'<div style="margin-top:8px">{recommend}</div>')
        head += f'<div style="margin-top:14px">{callout("Protect the calendar", inner)}</div>'

    timeline = '<div class="tl">' + "".join(str(slot(store, m)) for m in meetings) + "</div>"

    return Raw(head + str(block("Timeline", Raw(timeline), count=len(meetings),
                                note="Prep is generated the evening before")))
