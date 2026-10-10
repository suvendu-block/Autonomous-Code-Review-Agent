"""LangSmith tracer tests (PRINCIPLES §7 — every node gets a span)."""

import pytest

from app.tracing import Tracer, jsonable


class FakeRunTree:
    """Stands in for langsmith.run_trees.RunTree — no network."""

    def __init__(self, name=None, run_type=None, inputs=None, session_name=None,
                 ls_client=None, tags=None, parent=None):
        self.name = name
        self.run_type = run_type
        self.inputs = inputs
        self.session_name = session_name
        self.ls_client = ls_client
        self.tags = tags
        self.parent = parent
        self.children: list[FakeRunTree] = []
        self.posted = False
        self.patched = False
        self.outputs = None
        self.error = None

    def post(self, exclude_child_runs=True):
        self.posted = True

    def create_child(self, name, run_type=None, inputs=None):
        child = FakeRunTree(name=name, run_type=run_type, inputs=inputs, parent=self)
        self.children.append(child)
        return child

    def end(self, outputs=None, error=None):
        self.outputs = outputs
        self.error = error

    def patch(self, **kwargs):
        self.patched = True

    def get_url(self):
        return "https://smith.example/projects/p/1/r/root?poll=true"


def make_tracer() -> Tracer:
    return Tracer(
        "key", "proj", client=object(), run_tree_cls=FakeRunTree
    )


def test_disabled_tracer_is_noop() -> None:
    tracer = Tracer(None)
    assert tracer.enabled is False
    tracer.start_trace({})
    tracer.start_span("plan", {})
    tracer.end_span("plan", outputs={})
    tracer.finish_trace({})
    assert tracer.trace_url is None


def test_trace_and_spans_created() -> None:
    tracer = make_tracer()
    tracer.start_trace({"model": "m"})
    tracer.start_span("start", {"diff": "x"})
    tracer.end_span("start", outputs={"files": ["a.py"]})
    tracer.start_span("report", {})
    tracer.end_span("report", error="boom")
    tracer.finish_trace({"exit_code": 0})

    root = tracer._root
    assert root.posted and root.patched
    assert [c.name for c in root.children] == ["start", "report"]
    assert root.children[0].outputs == {"files": ["a.py"]}
    assert root.children[1].error == "boom"
    assert root.outputs == {"exit_code": 0}
    assert tracer.trace_url == "https://smith.example/projects/p/1/r/root?poll=true"
    assert root.session_name == "proj"


def test_failure_disables_tracing_without_raising() -> None:
    class Exploding(FakeRunTree):
        def post(self, exclude_child_runs=True):
            raise RuntimeError("no network")

    tracer = Tracer("key", "p", client=object(), run_tree_cls=Exploding)
    tracer.start_trace({})  # must not raise
    assert tracer.enabled is False
    tracer.start_span("plan", {})  # no-op after disable
    tracer.finish_trace({})


def test_span_end_without_start_is_safe() -> None:
    tracer = make_tracer()
    tracer.end_span("ghost", outputs={})  # must not raise


def test_jsonable_handles_models_and_odds() -> None:
    from app.models import Finding

    finding = Finding(file="a.py", severity="info", category="docs", title="t", detail="d")
    data = jsonable({"f": finding, "set": {1, 2}, "nested": (3,)})
    assert data["f"]["file"] == "a.py"
    assert sorted(data["set"]) == [1, 2]
    assert data["nested"] == [3]


@pytest.mark.parametrize("value", [None, "x", 1, 2.5, True])
def test_jsonable_primitives_passthrough(value) -> None:
    assert jsonable(value) == value
