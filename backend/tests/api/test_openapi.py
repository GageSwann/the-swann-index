"""The committed OpenAPI spec must match the code (regenerate with `uv run tsi openapi`)."""

from tsi.api.openapi import SPEC_PATH, openapi_document, render

# College football's endpoints, under /cfb (#183).
V1_PATHS = {
    "/meta/current",
    "/rankings",
    "/rankings/top",
    "/teams",
    "/teams/{slug}",
    "/weeks/{season}/{week}/games",
    "/games/{game_id}",
    "/games-of-week",
    "/playoff",
}
CFB_PATHS = {f"/cfb{path}" for path in V1_PATHS}
# Owner-only (decision #139): served with the key, never in the public spec.
PRIVATE_PATHS = {"/book/ledger", "/model/report", "/cfb/book/ledger", "/cfb/model/report"}


def test_committed_spec_is_current() -> None:
    assert SPEC_PATH.read_text(encoding="utf-8") == render(openapi_document()), (
        "docs/api/openapi.json is stale: run `uv run tsi openapi` and commit it"
    )


def test_spec_covers_v1_with_clean_operation_ids() -> None:
    doc = openapi_document()
    ops = [path["get"] for path in doc["paths"].values()]

    assert set(doc["paths"]) == CFB_PATHS
    assert not PRIVATE_PATHS & set(doc["paths"])
    ids = {path: doc["paths"][path]["get"]["operationId"] for path in doc["paths"]}
    assert len(set(ids.values())) == len(ids)
    assert all(ids[path].startswith("get_") for path in CFB_PATHS)
    for op in ops:
        schema = op["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" in schema or schema.get("type") == "array"  # every response is typed
