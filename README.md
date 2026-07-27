# Chief of Staff

An agentic chief-of-staff system for an early-stage investor: eight modules
covering deal flow, diligence, inbox, calendar, relationships, projects, and the
agents that run them.

**Live: https://yuval-el.github.io/first-round-cos/**

---

## Everything here is synthetic

Every company, founder, message, meeting, and project on this site is invented
for the demo. No real portfolio company, employee, or communication appears
anywhere in it. The architecture is real; the world is not.

I built the world because I do not have access to a real one. That is the honest
way to demonstrate a system you cannot yet point at live data — build a test
harness and let someone judge the output.

## What it is

The posting for Chief of Staff to Josh Kopelman describes a job with seven
surfaces and one layer above them:

| Module | The line it answers |
|---|---|
| **Brief** | "Ensuring Josh is ready for every meeting and moment — prioritizing his time and days around what matters most" |
| **Deal Flow** | "Managing and tracking new investment opportunities" |
| **Diligence** | "Conducting research and investment diligence" |
| **Inbox** | "Managing and processing email communication" |
| **Day** | "Ensuring Josh is ready for every meeting" |
| **Network** | "Managing and tracking relationships and communication within the First Round community and partner networks" |
| **Projects** | "Managing Josh's projects and events" |
| **Build** | "Driving First Round's internal AI and tooling work" |

That last one is the point. Seven agents produce everything on the other seven
tabs; the **Build** tab documents what each one owns, what it may do without a
human, and what has to escalate. It also contains a section called *Where this
should not be trusted*, which is the part usually left out.

## Run it

Python 3.11+. No dependencies, no build step, no network.

```bash
python make.py           # load → validate → render → write docs/
python make.py --check   # rebuild in memory, prove docs/ is unchanged, byte for byte
```

`--check` is the important one. Every page in `docs/` is generated from the JSON
in `data/`; none of it is hand-written HTML. `--check` re-renders and compares
bytes, so that claim is verifiable rather than asserted.

```
ok  8 page(s), 62 entities, 103 edges -> docs/
ok  8 page(s) regenerate byte for byte
```

## How it is put together

```
data/*.json          the world — one file per noun
data/diligence/      one long-form brief per company
render/validate.py   the schema, and the thing that enforces it
render/model.py      id resolution and the backlink index
render/shell.py      design tokens, app chrome, the page wrapper
render/components.py the component layer — the only file that escapes HTML
render/views/*.py    one module per tab
make.py              orchestration, --check, and the link audit
```

**Coherence is the hard part**, not the rendering. Eight views showing one world
will contradict each other unless something stops them. Four rules do:

1. One entity file per noun. Views hold ordering and framing, never facts.
2. Every cross-reference is a typed id (`per_sasha_lin`, `deal_veriform`), never
   a name — so a person's name is written in exactly one place in the repo.
3. Every number on screen is a `len()` or a derivation. None are typed by hand.
4. The Brief only links. It restates nothing, so it cannot drift from the modules.

A backlink index scans every record for id-shaped strings — including inside
prose — and inverts them. That is what lets one founder appear correctly on four
tabs, and it is also what catches a typo'd id buried in a sentence.

## What the build refuses to ship

`make.py` writes nothing unless all of this passes:

- **Shape.** A declarative spec per record type. Unknown fields are errors, which
  is what stops dead fields accumulating.
- **References.** Every id resolves — including ids mentioned in prose, with a
  "did you mean" on failure.
- **Contradictions.** A deal past Diligence with no brief. A date later than the
  day the world is set on. An owed reply with no thread to explain it. A meeting
  that ends before it starts.
- **Dead links.** After rendering, every `href="x.html#id"` is checked against
  every `id=` actually emitted. If a view links at something no view renders, the
  build fails rather than shipping a link that goes nowhere.

The data-contract table on the **Build** tab is generated from the validator, so
the documentation of the schema cannot drift from the schema.

## Notes

- Static HTML with CSS and JS inlined into each page. No framework, no database,
  no CDN, no network at view time. It works from a URL, from a zip, or from
  `file://`, and there is very little that can break.
- Eight separate pages rather than one app, so a bug in one tab cannot blank
  another, and every card has a real, linkable URL.
- `data/meta.json` holds `today`. Nothing calls `datetime.now()`, which is both a
  determinism requirement and what lets the world sit on a fixed day.

---

Built as a work sample for the Chief of Staff role at First Round.
