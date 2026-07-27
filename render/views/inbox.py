"""Inbox — triage with a reading pane. Answers "managing and processing email
communication", which the posting is blunt about being most of the job.

Layout is master/detail rather than a list, because triage is something you work
through one item at a time.
"""

from ..components import (avatar, block, button, kpi, kpis, link, links,
                          noresult, searchbox, segmented, tag, toolbar)
from ..util import Raw, esc, fmt_time, shift_days

SLUG = "inbox"
NAV = "Inbox"
TITLE = "Inbox"
SUB = "Everything that arrived, ranked by what it costs to be slow — with the reply already written"

PRIORITY_TONE = {1: "r", 2: "a", 3: "b", 4: "n"}
PRIORITY_LABEL = {1: "P1", 2: "P2", 3: "P3", 4: "P4"}
ACTION_LABEL = {
    "respond_now": ("Respond now", "r"),
    "batch": ("Batch", "n"),
    "delegate": ("Delegate", "b"),
    "decline": ("Decline", "n"),
    "already_drafted": ("Closed", "g"),
}


def count(store):
    return len([t for t in store.threads if t["action"] in ("respond_now", "delegate")])


def anchors(store):
    return {t["id"] for t in store.threads}


def sort_key(thread):
    # priority ascending, then newest first inside a priority — a stable two-pass
    # sort rather than anything clever.
    return (thread["priority"], thread["id"])


def ordered(store):
    items = sorted(store.threads, key=lambda t: t["received"], reverse=True)
    items.sort(key=sort_key)
    return items


def when(thread, today):
    stamp = thread["received"]
    day = stamp[:10]
    if day == today:
        return fmt_time(stamp)
    if day == shift_days(today, -1):
        return "Yesterday"
    return f"{stamp[5:7]}/{stamp[8:10]}"


def row(store, thread):
    person = store.get(thread["from"])
    org = store.person_org(thread["from"])
    return Raw(
        f'<div class="trow" data-open="{esc(thread["id"])}" '
        f'data-f="{esc(" ".join(filters(thread)))}" '
        f'data-search="{esc(" ".join([person["name"], org or "", thread["subject"], thread["ask"], thread["why"]]).lower())}">'
        f'{avatar(person["name"])}'
        f'<div class="body">'
        f'<div class="l1"><span class="pdot p{thread["priority"]}"></span>'
        f'<span class="nm">{esc(person["name"])}{esc(" · " + org if org else "")}</span>'
        f'<span class="tm">{esc(when(thread, store.today))}</span></div>'
        f'<div class="sj">{esc(thread["subject"])}</div>'
        f'<div class="as">{esc(thread["ask"])}</div>'
        f"</div></div>"
    )


def filters(thread):
    out = [f"p{thread['priority']}", thread["action"].replace("_", "-")]
    if thread["draft_reply"]:
        out.append("drafted")
    return out


def pane(store, thread):
    person = store.get(thread["from"])
    org = store.person_org(thread["from"])
    action_label, action_tone = ACTION_LABEL[thread["action"]]

    tags = [
        tag(PRIORITY_LABEL[thread["priority"]], PRIORITY_TONE[thread["priority"]]),
        tag(thread["sla"], PRIORITY_TONE[thread["priority"]] if thread["priority"] < 3 else "n"),
        tag(action_label, action_tone),
    ]

    flags = ""
    if thread["red_flags"]:
        flags = ("<h4>Flags</h4><ul class=\"flaglist\">"
                 + "".join(f"<li>{esc(f)}</li>" for f in thread["red_flags"]) + "</ul>")

    about = ""
    related = [i for i in thread["about"] if i in store.ids]
    if related:
        about = f'<h4>Related</h4><div class="rd">{links(store, related)}</div>'

    if thread["draft_reply"]:
        draft = (
            f'<h4>Drafted reply</h4>'
            f'<div class="draft"><div class="draft-h"><span class="t">Draft — not sent</span>'
            f'{button("Copy", "btn", data_copy=thread["id"] + "_d")}</div>'
            f'<div class="draft-b" id="{esc(thread["id"])}_d">{esc(thread["draft_reply"])}</div></div>'
        )
    else:
        draft = ('<h4>Drafted reply</h4><div class="rd" style="color:var(--ink-3)">'
                 "None. This one does not get a reply.</div>")

    return Raw(
        f'<div class="md-pane" data-pane="{esc(thread["id"])}" id="{esc(thread["id"])}">'
        f'<div class="ph">{avatar(person["name"], "lg")}<div>'
        f'<div class="sj">{esc(thread["subject"])}</div>'
        f'<div class="fr">{link(store, thread["from"])}'
        f'{esc(" · " + org if org else "")} · {esc(person["email"])}</div></div></div>'
        f'<div class="tags">{"".join(str(t) for t in tags)}</div>'
        f'<h4>The ask</h4><div class="rd">{esc(thread["ask"])}</div>'
        f'<h4>Why it ranks here</h4><div class="rd">{esc(thread["why"])}</div>'
        f"{flags}"
        f'<h4>Message</h4><div class="quote">{esc(thread["excerpt"])}</div>'
        f"{draft}{about}</div>"
    )


def body(store):
    threads = ordered(store)
    p1 = [t for t in threads if t["priority"] == 1]
    drafted = [t for t in threads if t["draft_reply"]]
    no_reply = [t for t in threads if t["action"] in ("decline", "batch")]

    tiles = kpis([
        kpi("In the queue", len(threads), "since the last run", "ac"),
        kpi("Need you today", len(p1), "P1 — two-hour SLA", "r"),
        kpi("Replies drafted", f"{len(drafted)}/{len(threads)}", "waiting on send, not on writing", "g"),
        kpi("Off your plate", len(no_reply), "batched, declined, or delegated", "b"),
    ])

    counts = {}
    for thread in threads:
        for key in filters(thread):
            counts[key] = counts.get(key, 0) + 1
    options = [("all", "All", len(threads))]
    for key, label in (("p1", "P1"), ("p2", "P2"), ("p3", "P3"), ("p4", "P4"),
                       ("respond-now", "Respond now"), ("delegate", "Delegate")):
        if counts.get(key):
            options.append((key, label, counts[key]))

    rows = "".join(str(row(store, t)) for t in threads)
    panes = "".join(str(pane(store, t)) for t in threads)

    return Raw(
        str(tiles)
        + str(block(
            "Queue",
            Raw(str(toolbar(segmented(options), searchbox("Search sender, subject, reasoning")))
                + f'<div class="md" data-md data-filterable>'
                + f'<div class="md-list">{rows}</div><div>{panes}</div></div>'
                + str(noresult())),
            count=len(threads),
            note="Priority first, newest first inside a priority"))
    )
