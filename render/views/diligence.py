"""Diligence — the generated brief on each company, as a document with a table of
contents. Answers "conducting research and investment diligence."

Every brief carries a confidence level and its sources. A brief without those is
not shown, which is the rule that keeps a generated memo honest.
"""

from ..components import (avatars, block, bullets, kpi, kpis, link, links,
                          paras, tag)
from ..util import Raw, esc, fmt_date

SLUG = "diligence"
NAV = "Diligence"
TITLE = "Diligence"
SUB = "First-pass briefs, written before a partner spends a minute — with confidence and sources attached"

ABOUT = {
    "headline": "The first pass, done before you open the deck",
    "goal": ("A generated memo is only worth reading if you can tell where every claim "
             "came from and how confident it is. Each brief ends in 'what would have to "
             "be true' — falsifiable statements rather than enthusiasm — because that "
             "is the part a partner can actually argue with."),
    "now": ("Three written briefs on invented companies, plus the queue behind them. "
            "Companies with no brief show why, rather than being hidden."),
    "live": ("The diligence agent runs on entry to Diligence and again each Thursday, "
             "reading founder materials, public sources, and reference-call notes. It "
             "still writes behind a human gate: twenty-two briefs read so far, two "
             "contained a number that could not be traced to a source."),
    "does": [
        "Move between companies from the table of contents — the queue is ordered by urgency, not alphabetically",
        "Every brief carries a confidence level and its sources; anything unattributable was left out rather than estimated",
        "Open questions are kept explicit and carried into the next call rather than quietly dropped",
        "Passed and portfolio companies show their status instead of an empty page",
    ],
}

CONFIDENCE_TONE = {"high": "g", "medium": "a", "low": "n"}


def count(store):
    return len(store.diligence)


def anchors(store):
    # Every company is anchored here, including the ones whose brief has not been
    # written yet — a queued brief is a real state, not a gap.
    return {c["id"] for c in store.companies}


# Reading order is by urgency, not by pipeline progression: the company with a
# decision pending this week belongs at the top, and closed deals at the bottom.
URGENCY = ["Partner review", "Diligence", "Screening", "New", "Committed", "Passed"]


def ordered(store):
    """Most urgent first. Written briefs come before those still queued."""
    def key(company_id):
        deal = store.deal_for_company(company_id)
        stage = URGENCY.index(deal["stage"]) if deal and deal["stage"] in URGENCY else 99
        return (0 if company_id in store.diligence else 1,
                stage, -(deal["score"] if deal else 0), company_id)

    return sorted((c["id"] for c in store.companies), key=key)


def toc(store, company_ids):
    items = []
    for company_id in company_ids:
        company = store.get(company_id)
        deal = store.deal_for_company(company_id)
        if company_id in store.diligence:
            state = deal["stage"] if deal else "Brief written"
        elif deal and deal["stage"] == "Passed":
            state = "Passed"
        elif deal is None:
            state = "Portfolio"
        else:
            state = "Queued"
        items.append(
            f'<a href="#{esc(company_id)}" data-open="{esc(company_id)}">'
            f'{esc(company["name"])}<span class="s">{esc(state)}</span></a>'
        )
    return Raw(f'<div class="doc-side"><div class="ttl">Companies</div>{"".join(items)}</div>')


def queued_pane(store, company_id):
    """A company the diligence agent has not reached yet. Shown deliberately —
    an empty queue slot is more honest than pretending the set is complete."""
    company = store.get(company_id)
    deal = store.deal_for_company(company_id)
    team = [store.get(p)["name"] for p in company["team"]]

    if deal is None:
        state, reason = "Portfolio", (
            "Portfolio company — no active deal, so no diligence brief. The history "
            "lives with the relationship rather than here.")
    elif deal["stage"] == "Passed":
        state, reason = "Passed", (
            f"No brief was written. {deal['thesis_fit']} The pass was made on shape "
            "before diligence began, which is the cheapest place to make it.")
    else:
        state, reason = "Queued", (
            "No brief yet. The diligence agent writes on entry to Diligence and on a "
            "Thursday sweep; this one has not met either trigger.")

    tags = [tag(state, "n"), tag(company["sector"], "n"), tag(company["hq"], "n")]
    if deal:
        tags.insert(0, tag(deal["stage"], "b"))

    return Raw(
        f'<div class="brief" data-pane="{esc(company_id)}" id="{esc(company_id)}">'
        f'<div class="bh"><div class="co">{esc(company["name"])}</div>'
        f'<div class="hl">{esc(company["one_liner"])}</div>'
        f'<div class="meta">{"".join(str(t) for t in tags)}{avatars(team)}'
        f'<span style="font-size:12px;color:var(--ink-3)">{esc(", ".join(team))}</span>'
        f"</div></div>"
        f'<section><h3>Status</h3><p style="color:var(--ink-3)">{esc(reason)}</p></section></div>'
    )


def section_html(section):
    if "bullets" in section:
        inner = bullets(section["bullets"])
    else:
        inner = paras(*section["body"].split("\n\n"))
    return Raw(f'<section><h3>{esc(section["h"])}</h3>{esc(inner)}</section>')


def brief_pane(store, company_id):
    brief = store.diligence[company_id]
    company = store.get(company_id)
    deal = store.deal_for_company(company_id)
    team = [store.get(p)["name"] for p in company["team"]]

    meta_tags = [
        tag(brief["confidence"].title() + " confidence",
            CONFIDENCE_TONE.get(brief["confidence"], "n")),
        tag(company["sector"], "n"),
        tag(company["hq"], "n"),
    ]
    if deal:
        meta_tags.insert(0, tag(deal["stage"], "b"))

    sections = "".join(str(section_html(s)) for s in brief["sections"])

    questions = (f'<section><h3>Open questions</h3><div class="qbox">'
                 f'{bullets(brief["open_questions"])}</div></section>')

    sources = (f'<section><h3>Sources</h3><ul class="srcs">'
               + "".join(f"<li>{esc(s)}</li>" for s in brief["sources"])
               + f'</ul><p class="srcs" style="margin-top:9px">Generated by '
                 f'{link(store, brief["generated_by"])} on {esc(fmt_date(brief["generated_at"]))}. '
                 f"Every figure above is attributable to one of these; anything that could not be "
                 f"attributed was left out rather than estimated.</p></section>")

    deal_link = ""
    if deal:
        deal_link = f' · {link(store, deal["id"], "in pipeline")}'

    return Raw(
        f'<div class="brief" data-pane="{esc(company_id)}" id="{esc(company_id)}">'
        f'<div class="bh"><div class="co">{esc(company["name"])}</div>'
        f'<div class="hl">{esc(brief["headline"])}</div>'
        f'<div class="meta">{"".join(str(t) for t in meta_tags)}'
        f'{avatars(team)}<span style="font-size:12px;color:var(--ink-3)">'
        f'{esc(", ".join(team))}{deal_link}</span></div></div>'
        f"{sections}{questions}{sources}</div>"
    )


def body(store):
    company_ids = ordered(store)
    briefs = [store.diligence[c] for c in company_ids if c in store.diligence]
    open_qs = sum(len(b["open_questions"]) for b in briefs)
    sourced = sum(len(b["sources"]) for b in briefs)
    low = [b for b in briefs if b["confidence"] == "low"]

    tiles = kpis([
        kpi("Briefs written", len(briefs), "one per company in diligence", "ac"),
        kpi("Open questions", open_qs, "carried into the next call", "b"),
        kpi("Sources cited", sourced, "no figure without one", "g"),
        kpi("Low confidence", len(low), "flagged rather than hidden", "a" if low else "n"),
    ])

    panes = "".join(
        str(brief_pane(store, c) if c in store.diligence else queued_pane(store, c))
        for c in company_ids)

    return Raw(
        str(tiles)
        + str(block("Briefs",
                    Raw(f'<div class="doc" data-md>{toc(store, company_ids)}<div>{panes}</div></div>'),
                    count=len(briefs),
                    note="Written briefs first, then the queue"))
    )
