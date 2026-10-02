from datetime import date

import pytest

from fedcast import dag
from fedcast.human import documents as ds
from fedcast.snapshot import Item
from tests.test_journey_ui import entry_for, full_snapshot


def doc(id_="H5-001", **kw):
    base = dict(id=id_, title="Bank lending standards note", author="t", added_on=date(2026, 10, 2),
                source="own analysis", relevance="related",
                text="Senior loan officer survey shows standards tightening for the third quarter running.")
    return ds.Document(**{**base, **kw})


def test_roundtrip_through_markdown(tmp_path):
    ds.save(tmp_path, doc())
    loaded = ds.load_documents(tmp_path)
    assert loaded == [doc()]
    assert ds.next_id(loaded) == "H5-002"


def test_cannot_overwrite_by_accident(tmp_path):
    ds.save(tmp_path, doc())
    with pytest.raises(FileExistsError):
        ds.save(tmp_path, doc(title="Different title"))


def test_free_form_relevance_is_rejected():
    with pytest.raises(Exception):
        doc(relevance="kind of")


def test_documents_appear_in_the_graph_as_frozen_evidence_feeding_only_the_analysts():
    snap = full_snapshot()
    snap.add(Item.make("human.doc.H5-001", "human_document", "human/documents/H5-001.md", doc().model_dump(mode="json")))
    g = dag.build(entry_for(snap, []), snap)
    node = next(n for n in g["nodes"] if n["id"] == "documents")
    assert node["status"] == "frozen" and node["detail"]["rows"][0][0] == "H5-001"
    targets = {e["to"] for e in g["edges"] if e["from"] == "documents"}
    assert targets == {"model.llm"}
    assert all(e["status"] == "planned" for e in g["edges"] if e["from"] == "documents")
