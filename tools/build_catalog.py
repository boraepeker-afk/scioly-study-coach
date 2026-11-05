"""Build docs/catalog.json: links to Science Olympiad practice tests, sorted by event.

Sources (links and metadata only; test files stay on scioly.org):
  - Scioly.org Test Exchange   https://scioly.org/tests   (via its /api/tests/list endpoint)
  - Scioly.org wiki archive    https://scioly.org/wiki/Scioly.org:Test_Exchange

Respects robots.txt (Crawl-delay: 3, no /wiki/index.php). Run: python3 tools/build_catalog.py
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://scioly.org"
UA = "SciOlyStudyCoach-catalog/1.0 (personal study site; links only)"
DELAY = 3
OUT = Path(__file__).resolve().parent.parent / "docs" / "catalog.json"
_last = 0.0


def fetch(url, body=None):
    global _last
    wait = DELAY - (time.time() - _last)
    if wait > 0:
        time.sleep(wait)
    headers = {"User-Agent": UA}
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read().decode("utf-8", "replace")
            _last = time.time()
            return data
        except urllib.error.HTTPError as e:
            _last = time.time()
            if e.code < 500 or attempt == 3:
                raise
            print(f"  {e.code} on {url}, retrying in {10 * (attempt + 1)}s", file=sys.stderr)
            time.sleep(10 * (attempt + 1))


def exchange_tests():
    tests, page = [], 1
    while True:
        res = json.loads(fetch(BASE + "/api/tests/list", {"filters": {}, "page": page, "sort": []}))
        tests += res["tests"]
        print(f"  exchange page {page}: {len(tests)}/{res['total']}", file=sys.stderr)
        if not res["tests"] or len(tests) >= res["total"]:
            return tests
        page += 1


class ArchiveParser(HTMLParser):
    """Walks the wiki archive: h2 = event, h3 = topic group, li with a nested list of file links = one test set."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = None          # tag of the heading being read
        self.head_text = ""
        self.event = None
        self.group = ""
        self.stack = []              # open <li> frames: {"label": str, "files": [], "in_sub": bool}
        self.anchor = None           # current <a>: {"href", "text"}
        self.sets = []
        self.full_sets = []
        self.in_content = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "mw-parser-output" in (a.get("class") or ""):
            self.in_content = True
        if not self.in_content:
            return
        if tag in ("h2", "h3"):
            self.heading, self.head_text = tag, ""
        elif tag == "li" or tag == "dd":
            self.stack.append({"label": "", "files": [], "sub": False, "tag": tag})
        elif tag in ("ul", "dl") and self.stack:
            self.stack[-1]["sub"] = True
        elif tag == "a":
            self.anchor = {"href": a.get("href", ""), "text": ""}

    def handle_data(self, data):
        if self.heading:
            self.head_text += data
        if self.anchor is not None:
            self.anchor["text"] += data
        if self.stack and not self.stack[-1]["sub"]:
            self.stack[-1]["label"] += data

    def handle_endtag(self, tag):
        if not self.in_content:
            return
        if tag == self.heading:
            text = re.sub(r"\s+", " ", self.head_text).strip()
            if tag == "h2":
                self.event = None if text in ("Full Sets", "Contents") else text
                self.group = ""
            else:
                self.group = text
            self.heading = None
        elif tag == "a" and self.anchor is not None:
            href, text = self.anchor["href"], re.sub(r"\s+", " ", self.anchor["text"]).strip()
            self.anchor = None
            if not self.stack:
                return
            if href.startswith("/w/images/") or "drive.google.com" in href or "docs.google.com" in href:
                url = BASE + href if href.startswith("/") else href
                self.stack[-1]["files"].append({"kind": text or "File", "url": url})
        elif tag in ("li", "dd") and self.stack:
            f = self.stack.pop()
            label = re.sub(r"\s+", " ", f["label"]).strip(" :-–")
            if not f["files"]:
                return
            if self.event is None:
                # Full tournament sets: each entry is a Drive folder; its anchor text is the name
                for x in f["files"]:
                    self.full_sets.append({"name": x["kind"], "url": x["url"]})
            elif f["sub"]:
                self.sets.append({"event": self.event, "group": self.group, "label": label or f["files"][0]["kind"], "files": f["files"]})
            elif self.stack:
                # A bare file link inside a parent item: let the parent own it
                self.stack[-1]["files"] += f["files"]
            else:
                for x in f["files"]:
                    self.sets.append({"event": self.event, "group": self.group, "label": x["kind"], "files": [x]})


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main():
    print("Fetching Test Exchange…", file=sys.stderr)
    ex = exchange_tests()
    print("Fetching wiki archive…", file=sys.stderr)
    p = ArchiveParser()
    p.feed(fetch(BASE + "/wiki/Scioly.org:Test_Exchange"))

    events = {}

    def ev(name):
        k = norm(name)
        if k not in events:
            events[k] = {"name": name, "wiki": BASE + "/wiki/" + name.replace(" ", "_"), "exchange": [], "archive": []}
        return events[k]

    for t in ex:
        ev(t["event"])["exchange"].append({
            "url": f"{BASE}/tests/{t['url_id']}", "season": t["season"], "division": t["division"],
            "tournament": t["tournament"], "topics": t["topics"] or "",
            "rating": t["ratings"]["overallQuality"], "ratings": t["ratings"]["count"],
        })
    for s in p.sets:
        ev(s["event"])["archive"].append({k: s[k] for k in ("group", "label", "files")})

    for e in events.values():
        e["exchange"].sort(key=lambda x: (-x["season"], x["tournament"]))
    out = {
        "built": time.strftime("%Y-%m-%d"),
        "sources": [BASE + "/tests", BASE + "/wiki/Scioly.org:Test_Exchange"],
        "events": sorted(events.values(), key=lambda e: e["name"]),
        "fullSets": p.full_sets,
    }
    OUT.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    n_ex = sum(len(e["exchange"]) for e in out["events"])
    n_ar = sum(len(e["archive"]) for e in out["events"])
    print(f"Wrote {OUT}: {len(out['events'])} events, {n_ex} exchange tests, {n_ar} archive sets, {len(p.full_sets)} full sets", file=sys.stderr)
    assert n_ex == len(ex), "every exchange test must land in an event"


if __name__ == "__main__":
    main()
