"""Local front end: a thin HTTP layer over the same functions the CLI calls.

Bound to 127.0.0.1 only. Writes require a custom header and a local Host, so another
website open in the browser cannot trigger them.
"""

from __future__ import annotations

import json
import re
import traceback
from dataclasses import asdict
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

from fedcast import config, dag, forecast, journey, ledger, snapshot
from fedcast.human import documents as docs_store
from fedcast.human.store import load_views
from fedcast.human.views import View
from fedcast.scorecard import SCORECARD, TILT_BY_STRENGTH, TILT_CAP

LEDGER = config.ROOT / "ledger" / "forecasts.jsonl"
VIEWS = config.ROOT / "human" / "views.yaml"
WATCHLIST = config.ROOT / "human" / "watchlist.yaml"
DOCS = config.ROOT / "human" / "documents"
INDEX = Path(__file__).parent / "index.html"
AUTHOR = "tankahming123"

_VIEWS_HEADER = """# H2 views. Each one tilts the human_adjusted forecast by a bounded amount until it expires.
# strength: 1 = mild (3 pp), 2 = firm (6 pp), 3 = strong (10 pp). Total tilt is capped at 10 pp.
# The rationale is recorded for the audit trail and post-meeting review; it does not change the number.
"""
_WATCHLIST_HEADER = """# H1 standing directives. Every active item must be addressed explicitly in each trace:
#   "<id>: checked - found / not found, evidence <snapshot item ids>"
# Adding, editing or retiring an item is a system change and goes through the eval gate.
"""
# Which scorecard dimensions the current build can already enforce or measure.
_SCORECARD_STATUS = {
    "S7": "Enforced in code and tests",
    "S9": "Measured by Verify ledger",
    "S10": "Enforced: views and directives are the only human inputs",
}


def _snapshot_by_hash(h: str) -> snapshot.Snapshot | None:
    dirs = list(config.SNAPSHOT_DIR.glob(f"*_{h[:12]}"))
    return snapshot.load(dirs[0]) if dirs else None


def _load_watchlist() -> list[dict]:
    if not WATCHLIST.exists():
        return []
    return (yaml.safe_load(WATCHLIST.read_text(encoding="utf-8")) or {}).get("items") or []


def _next_id(prefix: str, existing: list[str]) -> str:
    nums = [int(m.group(1)) for i in existing if (m := re.fullmatch(rf"{prefix}-(\d+)", i))]
    return f"{prefix}-{max(nums, default=0) + 1:03d}"


def state() -> dict:
    today = date.today()
    out: dict = {"today": today.isoformat(), "tilt": {"cap": TILT_CAP, "by_strength": TILT_BY_STRENGTH}}

    try:
        path = snapshot.latest(config.SNAPSHOT_DIR)
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        cal = snapshot.load(path).get("calendar")
        out["snapshot"] = {"name": path.name, "as_of": manifest["as_of"], "created_at": manifest["created_at"],
                           "complete": manifest["complete"], "missing": manifest["missing"],
                           "n_items": len(manifest["items"]), "next_meeting": cal["next_meeting"]}
    except FileNotFoundError:
        out["snapshot"] = None

    entries = ledger.read(LEDGER)
    try:
        ledger.verify(LEDGER)
        out["chain_ok"] = True
    except ValueError as exc:
        out["chain_ok"] = False
        out["chain_error"] = str(exc)
    out["ledger"] = [{"seq": e["seq"], "created_at": e["created_at"], "meeting": e["forecast"]["meeting"],
                      "snapshot": e["forecast"]["snapshot_hash"][:12], "code": e["code_version"],
                      "machine_only": e["forecast"]["machine_only"],
                      "human_adjusted": e["forecast"]["human_adjusted"],
                      "n_views": len(e["forecast"]["human"]["views_applied"])} for e in entries]

    out["views"] = [{**v.model_dump(mode="json"), "active": v.is_active(today)} for v in load_views(VIEWS)]
    out["watchlist"] = _load_watchlist()
    frozen_ids = set()
    if out["snapshot"]:
        frozen_ids = {k.split("human.doc.", 1)[1] for k in manifest["items"] if k.startswith("human.doc.")}
    out["documents"] = [{**d.model_dump(mode="json"), "text": d.text[:400], "chars": len(d.text),
                         "in_snapshot": d.id in frozen_ids} for d in docs_store.load_documents(DOCS)]

    out["latest"] = None
    if entries:
        last = entries[-1]
        snap = _snapshot_by_hash(last["forecast"]["snapshot_hash"])
        out["latest"] = {"entry": last, "journey": journey.build(last, snap) if snap else None,
                         "dag": dag.build(last, snap, out["watchlist"]) if snap else None}
        if out["snapshot"]:
            out["latest"]["stale"] = not out["snapshot"]["name"].endswith(last["forecast"]["snapshot_hash"][:12])

    out["scorecard"] = [{**asdict(d), "status": _SCORECARD_STATUS.get(d.id, "Not measured yet: needs the LLM agents")}
                        for d in SCORECARD]
    return out


# --- actions ------------------------------------------------------------------------------------

def act_snapshot(_: dict) -> dict:
    from fedcast.collect import build

    snap = build(date.today())
    try:
        path = snap.write(config.SNAPSHOT_DIR)
    except FileExistsError:
        return {"message": "Nothing has changed since the last snapshot, so no new one was written."}
    msg = f"Snapshot {path.name} saved with {len(snap.items)} items."
    if snap.missing:
        msg += f" {len(snap.missing)} sources are missing: " + ", ".join(snap.missing)
    return {"message": msg}


def act_forecast(_: dict) -> dict:
    snap = snapshot.load(snapshot.latest(config.SNAPSHOT_DIR))
    if not snap.complete:
        raise ValueError(f"The latest snapshot is missing {len(snap.missing)} sources. Take a new snapshot first.")
    entry = ledger.append(LEDGER, forecast.run(snap, load_views(VIEWS)))
    return {"message": f"Forecast recorded as ledger entry #{entry['seq']}."}


def act_replay(_: dict) -> dict:
    n = ledger.verify(LEDGER)
    current = forecast._code_version()
    results = []
    for e in ledger.read(LEDGER):
        want = e["forecast"]
        snap = _snapshot_by_hash(want["snapshot_hash"])
        ok = False
        if snap:
            views = [View(**v) for v in want["human"]["views_applied"]]
            ok = json.loads(json.dumps(forecast.compute(snap, views))) == want
        results.append({"seq": e["seq"], "ok": ok, "older_code": e["code_version"] != current})
    good = sum(r["ok"] for r in results)
    older = sum(1 for r in results if not r["ok"] and r["older_code"])
    msg = f"Tamper check passed: the chain of {n} entries is intact. {good} of {n} recompute to an exact match."
    if older:
        msg += f" {older} recorded under earlier code no longer reproduce with today's code (methodology changed since)."
    return {"message": msg, "results": results}


def act_add_view(body: dict) -> dict:
    views = load_views(VIEWS)
    view = View(id=_next_id("H2", [v.id for v in views]), author=AUTHOR,
                created_at=datetime.now().replace(microsecond=0),
                expires_on=date.fromisoformat(body["expires_on"]), direction=body["direction"],
                strength=int(body["strength"]), rationale=str(body["rationale"]).strip())
    _write_views(views + [view])
    return {"message": f"View {view.id} saved. Run a forecast to apply it."}


def act_expire_view(body: dict) -> dict:
    views = load_views(VIEWS)
    if body["id"] not in [v.id for v in views]:
        raise ValueError("unknown view " + str(body["id"]))
    yesterday = date.today() - timedelta(days=1)
    _write_views([v.model_copy(update={"expires_on": yesterday}) if v.id == body["id"] else v for v in views])
    return {"message": f"View {body['id']} expired. It stays on record but no longer tilts new forecasts."}


def _write_views(views: list[View]) -> None:
    data = {"views": [v.model_dump(mode="json") for v in views]}
    VIEWS.write_text(_VIEWS_HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def act_add_directive(body: dict) -> dict:
    text = str(body["directive"]).strip()
    if len(text) < 10:
        raise ValueError("Please describe what to watch for in at least 10 characters.")
    items = _load_watchlist()
    item = {"id": _next_id("H1", [i["id"] for i in items]), "added_on": date.today().isoformat(),
            "author": AUTHOR, "directive": text, "status": "active"}
    WATCHLIST.write_text(_WATCHLIST_HEADER + yaml.safe_dump({"items": items + [item]}, sort_keys=False,
                                                            allow_unicode=True), encoding="utf-8")
    return {"message": f"Directive {item['id']} saved. The LLM analysts will have to address it once they exist."}


def act_add_document(body: dict) -> dict:
    docs = docs_store.load_documents(DOCS)
    doc = docs_store.Document(id=docs_store.next_id(docs), title=str(body["title"]).strip(), author=AUTHOR,
                              added_on=date.today(), source=str(body.get("source") or "").strip(),
                              relevance=body.get("relevance") or "unsure", text=str(body["text"]).strip())
    docs_store.save(DOCS, doc)
    return {"message": f"Document {doc.id} saved. Take a new snapshot to freeze it into the evidence."}


def act_withdraw_document(body: dict) -> dict:
    docs = {d.id: d for d in docs_store.load_documents(DOCS)}
    if body["id"] not in docs:
        raise ValueError("unknown document " + str(body["id"]))
    docs_store.save(DOCS, docs[body["id"]].model_copy(update={"status": "withdrawn"}), overwrite=True)
    return {"message": f"Document {body['id']} withdrawn. It stays on file but will not enter new snapshots."}


ACTIONS = {"/api/snapshot": act_snapshot, "/api/forecast": act_forecast, "/api/replay": act_replay,
           "/api/views": act_add_view, "/api/views/expire": act_expire_view, "/api/watchlist": act_add_directive,
           "/api/documents": act_add_document, "/api/documents/withdraw": act_withdraw_document}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload, content_type="application/json") -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _local(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self) -> None:
        if not self._local():
            return self._send(403, {"error": "local access only"})
        if self.path in ("/", "/index.html"):
            return self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/state":
            return self._send(200, state())
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self._local() or self.headers.get("X-FedCast") != "1":
            return self._send(403, {"error": "local access only"})
        action = ACTIONS.get(self.path)
        if not action:
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            result = action(body)
            self._send(200, {**result, "state": state()})
        except Exception as exc:
            traceback.print_exc()
            self._send(400, {"error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:  # keep the console quiet
        pass


def serve(port: int = 8765, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"FedCast is running at {url}  (Ctrl+C to stop)")
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
