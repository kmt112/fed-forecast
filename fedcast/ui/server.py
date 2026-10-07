"""Local front end: a thin HTTP layer over the same functions the CLI calls.

Bound to 127.0.0.1 only. Writes require a custom header and a local Host, so another
website open in the browser cannot trigger them.
"""

from __future__ import annotations

import json
import re
import threading
from email.parser import BytesParser
from email.policy import default as email_policy
import traceback
from dataclasses import asdict
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

from fedcast import config, dag, forecast, journey, ledger, snapshot
from fedcast.human import documents as docs_store
from fedcast.human import prediction_markets as pm_store
from fedcast.human.extract import SUPPORTED, extract_text
from fedcast.human.store import load_views
from fedcast.human.views import View
from fedcast.llm import analyst as analyst_mod
from fedcast.scorecard import SCORECARD, TILT_BY_STRENGTH, TILT_CAP

LEDGER = config.ROOT / "ledger" / "forecasts.jsonl"
VIEWS = config.ROOT / "human" / "views.yaml"
WATCHLIST = config.ROOT / "human" / "watchlist.yaml"
DOCS = config.ROOT / "human" / "documents"
MARKETS = config.ROOT / "human" / "prediction_markets.yaml"
INDEX = Path(__file__).parent / "index.html"
AUTHOR = "tankahming123"

JOB: dict = {"running": False, "progress": [], "started_at": None, "finished_at": None, "error": None}

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
        analyses = analyst_mod.latest_all(last["forecast"]["snapshot_hash"])
        out["latest"] = {"entry": last, "journey": journey.build(last, snap) if snap else None,
                         "dag": dag.build(last, snap, out["watchlist"], analyses) if snap else None,
                         "analyses": {k: _trim_analysis(v) for k, v in analyses.items()}}
        if out["snapshot"]:
            out["latest"]["stale"] = not out["snapshot"]["name"].endswith(last["forecast"]["snapshot_hash"][:12])
    out["job"] = JOB

    out["markets"] = [{**m.model_dump(mode="json"), "in_snapshot": f"human.pm.{m.id}" in (manifest["items"] if out["snapshot"] else {})}
                      for m in pm_store.load_markets(MARKETS)]
    out["scorecard"] = [{**asdict(d), "status": _SCORECARD_STATUS.get(d.id, "Not measured yet: needs the LLM agents")}
                        for d in SCORECARD]
    return out


def _trim_analysis(rec: dict | None) -> dict | None:
    if not rec:
        return None
    last = rec["runs"][-1]
    out = {k: rec[k] for k in ("analyst", "arm", "prompt_version", "created_at", "backend", "summary")}
    out["prompt_chars"] = rec.get("prompt_chars")
    if rec["analyst"] == "naive":
        out["last"] = {"probabilities": last["probabilities"], "reasoning": last["completion"]["output"].get("reasoning", "")}
    else:
        o = last["completion"]["output"]
        out["last"] = {"summary": o.get("summary", ""), "confidence": o.get("confidence"), "watchouts": o.get("watchouts", []),
                       "verification": last["verification"], "model": last["completion"].get("model"),
                       "duration_s": last["completion"].get("duration_s")}
    return out


def _analysis_job(names: list[str], runs: int) -> None:
    import yaml

    from fedcast.llm.api_backend import make_backend
    from fedcast.llm.backend import ReplayBackend

    try:
        snap = snapshot.load(snapshot.latest(config.SNAPSHOT_DIR))
        watchlist = _load_watchlist()
        backend = ReplayBackend(config.ROOT / "analyses" / "replay", make_backend())
        log = lambda m: JOB["progress"].append(m.strip())
        for name in names:
            if name == "naive":
                rec = analyst_mod.run_naive(snap, backend, runs=runs, log=log)
            else:
                rec = analyst_mod.run_specialist(analyst_mod.SPECIALISTS[name], snap, backend, watchlist, runs=runs, log=log)
            analyst_mod.save(rec)
            s = rec["summary"]
            JOB["progress"].append(f"{name}: " + (f"tilt {s['tilt_mean_bp']:+.1f} bp, {s['groundedness_pct_mean']:.0f}% grounded, "
                                                  f"{s['leakage_total']} leaked" if name != "naive" else "done"))
    except Exception as exc:  # the UI shows the failure; nothing is half-written
        JOB["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        JOB["running"] = False
        JOB["finished_at"] = datetime.now().replace(microsecond=0).isoformat()


def act_analyse(body: dict) -> dict:
    if JOB["running"]:
        raise ValueError("an analysis is already running")
    names = body.get("analysts") or list(analyst_mod.SPECIALISTS) + ["naive"]
    runs = max(1, min(10, int(body.get("runs") or 1)))
    JOB.update({"running": True, "progress": [f"starting {', '.join(names)} ({runs} run(s) each)"],
                "started_at": datetime.now().replace(microsecond=0).isoformat(), "finished_at": None, "error": None})
    threading.Thread(target=_analysis_job, args=(names, runs), daemon=True).start()
    return {"message": "Analysts started. Each call takes about a minute; progress shows below the buttons."}


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


def act_upload_document(fields: dict, filename: str, data: bytes) -> dict:
    if len(data) > 20_000_000:
        raise ValueError("file is larger than 20 MB")
    text = extract_text(filename, data)
    docs = docs_store.load_documents(DOCS)
    doc = docs_store.Document(id=docs_store.next_id(docs), title=(fields.get("title") or filename).strip(),
                              author=AUTHOR, added_on=date.today(),
                              source=(fields.get("source") or f"uploaded file {filename}").strip(),
                              relevance=fields.get("relevance") or "unsure", text=text)
    docs_store.save(DOCS, doc)
    (DOCS / "files").mkdir(parents=True, exist_ok=True)
    (DOCS / "files" / f"{doc.id}{Path(filename).suffix.lower()}").write_bytes(data)
    return {"message": f"Document {doc.id} saved: {len(text):,} characters extracted from {filename}. "
                       "Take a new snapshot to freeze it into the evidence."}


def _parse_multipart(content_type: str, body: bytes) -> tuple[dict, str | None, bytes | None]:
    msg = BytesParser(policy=email_policy).parsebytes(
        b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + body)
    fields, filename, data = {}, None, None
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if part.get_filename():
            filename, data = part.get_filename(), part.get_payload(decode=True)
        elif name:
            fields[name] = part.get_payload(decode=True).decode("utf-8", errors="replace")
    return fields, filename, data


def act_add_market(body: dict) -> dict:
    items = pm_store.load_markets(MARKETS)
    prices = {k: float(v) for k, v in (body.get("prices") or {}).items() if v not in ("", None)}
    cal = snapshot.load(snapshot.latest(config.SNAPSHOT_DIR)).get("calendar")
    entry = pm_store.MarketOdds(id=pm_store.next_id(items), venue=body.get("venue") or "polymarket",
                                meeting=date.fromisoformat(body.get("meeting") or cal["next_meeting"]),
                                observed_at=datetime.now().replace(microsecond=0), author=AUTHOR,
                                url=str(body.get("url") or "").strip(), prices=prices,
                                volume_usd=float(body["volume_usd"]) if body.get("volume_usd") else None,
                                note=str(body.get("note") or "").strip())
    pm_store.save_markets(MARKETS, items + [entry])
    return {"message": f"Odds {entry.id} saved ({entry.venue}, sums to {sum(prices.values()):.0f}%). "
                       "Take a new snapshot to freeze them, then run a forecast."}


def act_withdraw_market(body: dict) -> dict:
    items = pm_store.load_markets(MARKETS)
    if body["id"] not in [m.id for m in items]:
        raise ValueError("unknown entry " + str(body["id"]))
    pm_store.save_markets(MARKETS, [m.model_copy(update={"status": "withdrawn"}) if m.id == body["id"] else m for m in items])
    return {"message": f"Odds {body['id']} withdrawn; they stay on file but will not enter new snapshots."}


def act_withdraw_document(body: dict) -> dict:
    docs = {d.id: d for d in docs_store.load_documents(DOCS)}
    if body["id"] not in docs:
        raise ValueError("unknown document " + str(body["id"]))
    docs_store.save(DOCS, docs[body["id"]].model_copy(update={"status": "withdrawn"}), overwrite=True)
    return {"message": f"Document {body['id']} withdrawn. It stays on file but will not enter new snapshots."}


ACTIONS = {"/api/snapshot": act_snapshot, "/api/forecast": act_forecast, "/api/replay": act_replay,
           "/api/views": act_add_view, "/api/views/expire": act_expire_view, "/api/watchlist": act_add_directive,
           "/api/documents": act_add_document, "/api/documents/upload": act_add_document, "/api/documents/withdraw": act_withdraw_document,
           "/api/markets": act_add_market, "/api/markets/withdraw": act_withdraw_market,
           "/api/analyse": act_analyse}


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
            raw = self.rfile.read(length)
            ctype = self.headers.get("Content-Type") or ""
            if ctype.startswith("multipart/form-data"):
                fields, filename, data = _parse_multipart(ctype, raw)
                if not filename:
                    raise ValueError("no file in the upload")
                result = act_upload_document(fields, filename, data)
            else:
                result = action(json.loads(raw or b"{}"))
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
