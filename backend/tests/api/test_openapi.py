"""The committed OpenAPI spec must match the code (regenerate with `uv run tsi openapi`)."""

from tsi.api.openapi import SPEC_PATH, openapi_document, render

V1_PATHS = {
    "/meta/current",
    "/rankings",
    "/teams",
    "/teams/{slug}",
    "/weeks/{season}/{week}/games",
    "/games/{game_id}",
    "/matchup",
    "/playoff",
}
# Owner-only (decision #139): served with the key, never in the public spec.
PRIVATE_PATHS = {"/book/ledger", "/model/report"}


def test_committed_spec_is_current() -> None:
    assert SPEC_PATH.read_text(encoding="utf-8") == render(openapi_document()), (
        "docs/api/openapi.json is stale: run `uv run tsi openapi` and commit it"
    )


def test_spec_covers_v1_with_clean_operation_ids() -> None:
    doc = openapi_document()
    ops = [path["get"] for path in doc["paths"].values()]

    assert set(doc["paths"]) == V1_PATHS
    assert not PRIVATE_PATHS & set(doc["paths"])
    ids = [op["operationId"] for op in ops]
    assert len(set(ids)) == len(ids) and all(i.startswith("get_") for i in ids)
    for op in ops:
        schema = op["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" in schema or schema.get("type") == "array"  # every response is typed
