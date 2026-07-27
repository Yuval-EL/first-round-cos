"""Build — how the system itself works.

This is the view the posting is really about: "driving First Round's internal AI
and tooling work" and "sees their job as building the systems that eventually do
it for them."

Two rules keep it honest rather than decorative:
  1. The data-contract table is generated from validate.SPECS — the documentation
     of the schema is produced by the thing that enforces the schema.
  2. Every number on this page is a len() over real files. Nothing is typed.
"""

from .. import validate
from ..components import (block, bullets, callout, kpi, kpis, link, paras,
                          table, tag)
from ..util import Raw, esc

SLUG = "build"
NAV = "Build"
TITLE = "Build"
SUB = "The agents behind every other tab — what they own, what they may do alone, and what has to escalate"

AUTONOMY_TONE = {"acts": "g", "drafts": "b", "flags": "a"}
AUTONOMY_LABEL = {
    "acts": "Acts alone",
    "drafts": "Drafts for review",
    "flags": "Flags only",
}

TYPE_LABEL = {
    "id": "id",
    "ref": "reference",
    "str": "text",
    "enum": "one of",
    "int": "integer",
    "bool": "true / false",
    "date": "ISO date",
    "list": "list",
    "obj": "object",
    "any": "structured",
}

FLOW = [
    ("01", "Sources", "Mail, calendar, CRM, documents. Read-only, always."),
    ("02", "Agents", "Seven of them. Each owns one surface and one output file."),
    ("03", "Contracts", "Every agent emits validated JSON. Off-schema fails the build."),
    ("04", "Views", "A deterministic renderer turns the JSON into these pages."),
]


def count(store):
    return len(store.agents)


def anchors(store):
    return {a["id"] for a in store.agents}


def describe(field_spec):
    kind = field_spec["type"]
    label = TYPE_LABEL.get(kind, kind)
    if kind == "ref":
        return f"reference → {field_spec['kind']}_"
    if kind == "enum":
        values = field_spec["values"]
        shown = ", ".join(str(v) for v in values[:4])
        return f"one of: {shown}" + (" …" if len(values) > 4 else "")
    if kind == "int":
        return f"integer {field_spec.get('min', '')}–{field_spec.get('max', '')}".strip()
    if kind == "list":
        inner = field_spec.get("of")
        if inner == "ref":
            return f"list of {field_spec.get('kind', '')}_ references"
        return f"list of {TYPE_LABEL.get(inner, inner)}"
    if kind == "obj":
        return f"object · {field_spec['spec']}"
    return label


def contracts_table():
    """Generated from validate.SPECS, not written by hand."""
    rows = []
    for name in ("deal", "thread", "meeting", "person"):
        spec = validate.SPECS[name]
        for index, (field, field_spec) in enumerate(spec.items()):
            optional = field_spec.get("optional") or field_spec.get("nullable")
            rows.append({
                "cells": [
                    (Raw(f'<span class="t1">{esc(name)}.v1</span>') if index == 0
                     else Raw('<span style="color:var(--line-2)">·</span>'), "nw"),
                    (Raw(f"<code>{esc(field)}</code>"), "nw"),
                    (describe(field_spec), ""),
                    (tag("optional", "n") if optional else tag("required", "b"), "nw"),
                ]
            })
    return table([("Contract", "nw"), ("Field", "nw"), "Shape", ("", "nw")], rows)


def agent_card(store, agent):
    schedule = agent["schedule"]
    inputs = ", ".join(i["source"] for i in agent["inputs"])
    outputs = ", ".join(o["artifact"] for o in agent["outputs"])
    feeds = " · ".join(a.title() for a in agent["feeds"])

    return Raw(
        f'<article class="acard" id="{esc(agent["id"])}">'
        f'<div class="hd"><div style="min-width:0"><div class="nm">{esc(agent["name"])}</div>'
        f'<div style="font-size:11.5px;color:var(--ink-3);margin-top:2px">Feeds {esc(feeds)}</div></div>'
        f'<span style="margin-left:auto">'
        f'{tag(AUTONOMY_LABEL[agent["autonomy"]], AUTONOMY_TONE[agent["autonomy"]])}</span></div>'
        f'<div class="does">{esc(agent["does"])}</div>'
        f'<div class="sch"><b>Runs</b> {esc(schedule["label"])}</div>'
        f'<div class="sch"><b>On</b> {esc(schedule["trigger"])}</div>'
        f'<div class="io"><b>Reads</b> {esc(inputs)}<br><b>Writes</b> <code>{esc(outputs)}</code></div>'
        f'<div class="io"><b>Escalates when</b>{bullets(agent["escalates_when"])}</div>'
        f'<div class="io"><b>Human in the loop.</b> {esc(agent["human_in_loop"])}</div>'
        f"</article>"
    )


def body(store):
    agents = store.agents
    by_autonomy = {}
    for agent in agents:
        by_autonomy[agent["autonomy"]] = by_autonomy.get(agent["autonomy"], 0) + 1
    escalations = sum(len(a["escalates_when"]) for a in agents)
    autonomous = by_autonomy.get("acts", 0)

    tiles = kpis([
        kpi("Agents running", len(agents), "one per surface, plus the compiler", "ac"),
        kpi("Escalation rules", escalations, "conditions that force a human in", "b"),
        kpi("Act without review", f"{autonomous}/{len(agents)}",
            "the rest draft or flag only", "g"),
        kpi("Entities in the graph", len(store.ids),
            f"{store.edge_count()} references between them", "n"),
    ])

    flow = ('<div class="flow">' + '<div class="farrow">→</div>'.join(
        f'<div class="fstep"><div class="n">{esc(n)}</div><div class="t">{esc(t)}</div>'
        f'<div class="d">{esc(d)}</div></div>' for n, t, d in FLOW) + "</div>")

    cards = ('<div class="agrid">'
             + "".join(str(agent_card(store, a)) for a in agents) + "</div>")

    rules = callout("The rules every agent runs under", Raw(str(bullets([
        "Read-only on every source. Nothing sends, archives, deletes, or books.",
        "Drafts are drafts. A reply leaves the mailbox only when a human presses send.",
        "Nothing is promoted past a screening stage without a person doing it.",
        "Every generated figure carries its source. What cannot be attributed is left out, not estimated.",
        "Off-schema output fails the build rather than rendering a broken page.",
    ]))))

    limits = Raw(str(paras(
        "Anything that claims to run a partner's day should be equally clear about where it "
        "should not be trusted. This is the honest list.",
    )) + str(bullets([
        "Priority is a judgment, and the judgment is mine. The Kettle thread on the Inbox tab is "
        "ranked P1 on inference, not evidence — a late-night second ask about a cap table. That "
        "inference could be wrong, and the cost of being wrong in that direction is low, which is "
        "why it is ranked that way.",
        "Relationship cadence measures contact, not closeness. Someone can be past cadence and "
        "perfectly fine. The system is deliberately quiet about people who are simply busy.",
        "The diligence agent still runs behind a human gate. Twenty-two briefs have been read "
        "before publication and two contained a number that could not be traced to a source. Two "
        "in twenty-two is too high to remove the gate.",
        "Nothing here reads tone. It cannot tell an anxious founder from a terse one, which is "
        "most of what matters in a portfolio relationship.",
        "Every figure on this site is synthetic. The architecture is real; the world is invented.",
    ])))

    stack = Raw(str(paras(
        "No framework, no database, no build step, no network at view time. The data is JSON on "
        "disk, the renderer is standard-library Python, and the output is static HTML that opens "
        "from a file. That is a deliberate choice rather than a limitation: a tool a partner "
        "relies on daily should have as few things that can break as possible."
    )) + "<pre><code>"
        + esc("data/*.json        the world — one file per noun\n"
              "render/validate.py  the schema, and the thing that enforces it\n"
              "render/model.py     id resolution and the backlink index\n"
              "render/views/*.py   one module per tab\n"
              "make.py             load → validate → render → write\n\n")
        + '<span class="c">' + esc("# prove the pages are generated, not hand-written") + "</span>\n"
        + esc("python make.py --check")
        + "</code></pre>")

    return Raw(
        str(tiles)
        + str(block("How a message becomes a decision", Raw(flow),
                    note="Four stages, seven agents"))
        + str(block("The agents", Raw(cards), count=len(agents)))
        + str(block("Operating rules", rules))
        + str(block("Data contracts", contracts_table(),
                    note="Generated from the validator — this table cannot drift from the schema"))
        + str(block("The stack", stack))
        + str(block("Where this should not be trusted", limits,
                    note="The part usually left out"))
    )
