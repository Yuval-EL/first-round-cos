"""The Store: loads the data files, resolves ids, and builds the backlink index.

Coherence rules this file enforces structurally:
  R1  One entity file per noun. Views own zero entity data.
  R2  Every cross-reference is a prefix-typed id, never a name. An entity's
      display name is written in exactly one place in the whole repo.
  R3  Counts come from len() over these collections, never from typed numbers.
"""

import json
from collections import defaultdict
from pathlib import Path

from .util import ID_RE

# Which view owns (and therefore anchors) each kind of entity.
ROUTE = {
    "per": "network.html",
    "co": "diligence.html",
    "deal": "dealflow.html",
    "thr": "inbox.html",
    "mtg": "day.html",
    "prj": "projects.html",
    "agt": "build.html",
}

# file stem -> (attribute name, id prefix)
COLLECTIONS = (
    ("people", "people", "per"),
    ("companies", "companies", "co"),
    ("deals", "deals", "deal"),
    ("threads", "threads", "thr"),
    ("meetings", "meetings", "mtg"),
    ("projects", "projects", "prj"),
    ("agents", "agents", "agt"),
)

DECISION_KINDS = ("deal", "thread", "project", "meeting")


def kind_of(entity_id):
    return entity_id.split("_", 1)[0]


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class Store:
    def __init__(self, data_dir, live_pages=None):
        # live_pages is the set of files make.py will actually write. Anything
        # routing to a page that is not being built degrades to plain text
        # instead of a dead link, so cutting a view under time pressure is safe.
        self.live_pages = live_pages
        # Filled in by make.py once every view has declared what it anchors.
        self.rendered = None
        self.data_dir = Path(data_dir)
        self.meta = _read(self.data_dir / "meta.json")
        self.today = self.meta["today"]

        self.by_kind = {}
        for stem, attr, _prefix in COLLECTIONS:
            path = self.data_dir / f"{stem}.json"
            records = _read(path) if path.exists() else []
            setattr(self, attr, records)
            self.by_kind[attr] = records

        self.diligence = {}
        dil_dir = self.data_dir / "diligence"
        if dil_dir.exists():
            for path in sorted(dil_dir.glob("co_*.json")):
                brief = _read(path)
                self.diligence[brief["company"]] = brief

        self.by_id = {}
        for records in self.by_kind.values():
            for record in records:
                self.by_id[record["id"]] = record

        self.ids = set(self.by_id)
        self._backlinks = self._build_backlinks()

    # ---------- resolution ----------

    def get(self, entity_id):
        return self.by_id[entity_id]

    def label(self, entity_id):
        record = self.by_id.get(entity_id)
        if record is None:
            return entity_id
        kind = kind_of(entity_id)
        if kind == "deal":
            company = self.by_id.get(record["company"])
            return company["name"] if company else record["company"]
        if kind == "thr":
            return record["subject"]
        if kind == "mtg":
            return record["title"]
        return record.get("name", entity_id)

    def href(self, entity_id):
        """The one place a cross-view URL is formed, so an id renders the same
        way from every view. Companies anchor on the Diligence page.

        Returns None when nothing in this build actually renders the entity —
        an untracked person, or a view that was cut. Callers degrade to plain
        text, so a link is never emitted that would land nowhere."""
        page = ROUTE[kind_of(entity_id)]
        if self.live_pages is not None and page not in self.live_pages:
            return None
        if self.rendered is not None and entity_id not in self.rendered:
            return None
        return f"{page}#{entity_id}"

    def person_org(self, person_id):
        person = self.by_id.get(person_id) or {}
        org_id = person.get("org")
        return self.by_id.get(org_id, {}).get("name") if org_id else None

    def deal_for_company(self, company_id):
        for deal in self.deals:
            if deal["company"] == company_id:
                return deal
        return None

    # ---------- backlinks ----------

    def _build_backlinks(self):
        """Scan every record for id-shaped strings, wherever they appear —
        including inside prose — and invert. This is what lets one founder show
        up correctly in four views with her name written only once."""
        index = defaultdict(set)
        for attr, records in self.by_kind.items():
            for record in records:
                hits = set()
                _scan(record, hits)
                hits.discard(record["id"])
                for target in hits:
                    index[target].add((attr, record["id"]))
        for company_id, brief in self.diligence.items():
            hits = set()
            _scan(brief, hits)
            hits.discard(company_id)
            for target in hits:
                index[target].add(("diligence", company_id))
        return {key: sorted(value) for key, value in index.items()}

    def backlinks(self, entity_id):
        return self._backlinks.get(entity_id, [])

    def backlink_ids(self, entity_id, kinds=None):
        out = [rid for attr, rid in self.backlinks(entity_id)
               if kinds is None or attr in kinds]
        return sorted(set(out))

    def edge_count(self):
        return sum(len(v) for v in self._backlinks.values())

    # ---------- derived collections ----------

    def needing_decision(self):
        """Every entity carrying a needs_decision block, in one list. The Brief
        collects these polymorphically: one schema, four sources."""
        out = []
        for attr in ("deals", "threads", "projects", "meetings"):
            for record in self.by_kind.get(attr, []):
                if record.get("needs_decision"):
                    out.append(record)
        out.sort(key=lambda r: (r["needs_decision"].get("deadline", "9999-99-99"), r["id"]))
        return out

    def threads_by_priority(self, priority):
        return [t for t in self.threads if t["priority"] == priority]

    def todays_meetings(self):
        items = [m for m in self.meetings if m["start"][:10] == self.today]
        items.sort(key=lambda m: (m["start"], m["id"]))
        return items

    def people_with_rel(self):
        return [p for p in self.people if p.get("rel")]


def _scan(node, hits):
    if isinstance(node, str):
        hits.update(ID_RE.findall(node))
    elif isinstance(node, list):
        for value in node:
            _scan(value, hits)
    elif isinstance(node, dict):
        for value in node.values():
            _scan(value, hits)
