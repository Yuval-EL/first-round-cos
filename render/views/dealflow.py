"""Deal Flow — a pipeline board. Answers "managing and tracking new investment
opportunities."

Layout is a board rather than a list because the question a partner actually asks
of deal flow is "what is where", not "what arrived".
"""

from ..components import (avatars, board, block, bullets, callout, column,
                          disclosure, kpi, kpis, link, meter, noresult, paras,
                          searchbox, segmented, tag, toolbar)
from ..util import Raw, ago, esc, fmt_date, shift_days

SLUG = "dealflow"
NAV = "Deal Flow"
TITLE = "Deal Flow"
SUB = "Everything inbound, scored against the thesis and ranked by what it costs to be slow"

ABOUT = {
    "headline": "What is where, and what it costs to be slow",
    "goal": ("The useful question about deal flow is not what arrived, it is what is "
             "sitting in which stage and which one has a clock on it. A board answers "
             "that at a glance; a list does not."),
    "now": ("Five invented companies at different stages, with invented founders, "
            "rounds, and scores."),
    "live": ("The intake agent reads the deals alias every fifteen minutes, extracts "
             "company, round, ask, and source, and scores each against the thesis. It "
             "files, it never promotes — a human moves every stage past Screening."),
    "does": [
        "Filter by source or stage and search across companies, sectors, and reasoning",
        "Open 'Why' on any card for the four-axis score breakdown and the next step",
        "Anything needing a partner decision is lifted out of the board into a callout at the top",
        "Jump straight from a card to that company's diligence brief",
    ],
}

# stage -> (tone, board order)
STAGES = [
    ("New", "b"),
    ("Screening", "b"),
    ("Diligence", "a"),
    ("Partner review", "r"),
    ("Committed", "g"),
    ("Passed", "n"),
]
STAGE_TONE = dict(STAGES)
STAGE_ORDER = [s for s, _ in STAGES]
CLOSED = ("Passed", "Committed")

SOURCE_LABEL = {
    "warm_intro": "Warm intro",
    "portfolio_referral": "Portfolio",
    "cofund": "Co-investor",
    "inbound_cold": "Cold",
    "conference": "Event",
}
SOURCE_TONE = {"warm_intro": "g", "portfolio_referral": "g", "cofund": "b",
               "inbound_cold": "n", "conference": "n"}


def count(store):
    return len([d for d in store.deals if d["stage"] not in CLOSED])


def anchors(store):
    return {d["id"] for d in store.deals}


def score_tone(score):
    return "g" if score >= 8 else "a" if score >= 6 else "n"


def deal_card(store, deal):
    company = store.get(deal["company"])
    source = deal["source"]
    team = [store.get(p)["name"] for p in company["team"]]

    tags = [tag(SOURCE_LABEL.get(source["kind"], source["kind"]),
                SOURCE_TONE.get(source["kind"], "n"))]
    if deal.get("needs_decision"):
        tags.append(tag("Needs you", "r", dot=True))

    brief_href = store.href(deal["company"]) if deal["company"] in store.diligence else None
    brief_link = (f'<a class="lnk" href="{esc(brief_href)}">Brief</a>' if brief_href else "")

    btn, panel = disclosure(
        f"{deal['id']}_why", "Why",
        Raw("<h4>Read</h4>" + str(paras(deal["thesis_fit"]))
            + "<h4>Score</h4>"
            + str(bullets([f"{k.title()} {v}/10" for k, v in deal["score_breakdown"].items()]))
            + "<h4>Next</h4>" + str(paras(deal["next_step"]))))

    via = ""
    if source.get("via"):
        via = Raw(f' via {link(store, source["via"])}')

    return Raw(
        f'<article class="dcard" id="{esc(deal["id"])}" '
        f'data-search="{esc(" ".join([company["name"], company["sector"], company["one_liner"], deal["thesis_fit"]] + team).lower())}" '
        f'data-f="{esc(" ".join(filters(deal)))}">'
        f'<div class="top">{"".join(str(t) for t in tags)}'
        f'<span style="margin-left:auto;font-size:11.5px;color:var(--ink-3)">{esc(ago(deal["updated"], store.today))}</span></div>'
        f'<div class="nm">{esc(company["name"])}</div>'
        f'<div class="ol">{esc(company["one_liner"])}</div>'
        f'<div class="mrow"><span class="rnd">{esc(deal["round"])}</span></div>'
        f'<div class="mrow">{esc(company["sector"])} · {esc(company["hq"])}{via}</div>'
        f'<div class="sc">{meter(deal["score"], 10, score_tone(deal["score"]))}'
        f'<span class="v">{esc(deal["score"])}/10</span></div>'
        f'<div class="foot">{avatars(team)}{btn}{brief_link}</div>'
        f"{panel}</article>"
    )


def filters(deal):
    out = ["open" if deal["stage"] not in CLOSED else "closed"]
    out.append(deal["source"]["kind"].replace("_", "-"))
    if deal.get("needs_decision"):
        out.append("decide")
    return out


def decision_card(store, deal):
    decision = deal["needs_decision"]
    company = store.get(deal["company"])
    inner = (
        f'<div style="font-size:14.5px;font-weight:650;letter-spacing:-.015em">'
        f'{esc(decision["question"])}</div>'
        + str(paras(decision["why"]))
        + '<div style="margin-top:9px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">'
        + str(tag(f"Recommend · {decision['recommendation']}", "ac"))
        + str(tag(f"By {fmt_date(decision['deadline'])}", "r"))
        + f'{link(store, deal["id"], company["name"] + " in pipeline")}</div>'
        + f'<div style="margin-top:8px;font-size:12.5px;color:var(--ink-2)">'
        f'<b>Cost of delay.</b> {esc(decision["cost_of_delay"])}</div>'
    )
    return callout("Waiting on you", Raw(inner))


def body(store):
    deals = store.deals
    live = [d for d in deals if d["stage"] not in CLOSED]
    decisions = [d for d in deals if d.get("needs_decision")]
    window = shift_days(store.today, -14)
    fresh = [d for d in deals if d["first_seen"] >= window]
    warm = [d for d in deals if d["source"]["kind"] in ("warm_intro", "portfolio_referral", "cofund")]

    tiles = kpis([
        kpi("Live in pipeline", len(live), "not yet passed or committed", "ac"),
        kpi("Waiting on you", len(decisions), "blocked on a partner call", "r"),
        kpi("New in 14 days", len(fresh), f"since {fmt_date(window)}", "b"),
        kpi("Warm-sourced", f"{round(100 * len(warm) / len(deals))}%",
            f"{len(warm)} of {len(deals)} came through the network", "g"),
    ])

    head = str(tiles)
    for deal in decisions:
        head += f'<div style="margin-top:14px">{decision_card(store, deal)}</div>'

    counts = {}
    for deal in deals:
        for key in filters(deal):
            counts[key] = counts.get(key, 0) + 1

    options = [("all", "All", len(deals)), ("open", "Live", counts.get("open", 0)),
               ("decide", "Needs you", counts.get("decide", 0)),
               ("warm-intro", "Warm intro", counts.get("warm-intro", 0)),
               ("inbound-cold", "Cold", counts.get("inbound-cold", 0))]
    options = [o for o in options if o[2]]

    columns = []
    for stage in STAGE_ORDER:
        cards = sorted([d for d in deals if d["stage"] == stage],
                       key=lambda d: (-d["score"], d["id"]))
        if not cards:
            continue
        columns.append(column(stage.lower().replace(" ", "-"), stage,
                              STAGE_TONE[stage], [deal_card(store, c) for c in cards]))

    return Raw(
        head
        + str(block("Pipeline",
                    Raw(str(toolbar(segmented(options), searchbox("Search companies, sectors, notes")))
                        + str(board(columns)) + str(noresult())),
                    count=len(deals),
                    note="Sorted by score inside each stage"))
    )
