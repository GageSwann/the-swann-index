"""The committed OpenAPI spec must match the code (regenerate with `uv run tsi openapi`)."""

from tsi.api.openapi import SPEC_PATH, openapi_document, render

V1_PATHS = {
    "/meta/current",
    "/rankings",
    "/teams",
    "/teams/{slug}",
    "/weeks/{season}/{week}/games",
    "/games/{game_id}",
    "/book/ledger",
    "/model/report",
    "/matchup",
    "/playoff",
}


def test_committed_spec_is_current() -> None:
    assert SPEC_PATH.read_text(encoding="utf-8") == render(openapi_document()), (
        "docs/api/openapi.json is stale: run `uv run tsi openapi` and commit it"
    )


def test_spec_covers_v1_with_clean_operation_ids() -> None:
    doc = openapi_document()
    ops = [path["get"] for path in doc["paths"].values()]

    assert set(doc["paths"]) == V1_PATHS
    ids = [op["operationId"] for op in ops]
    assert len(set(ids)) == len(ids) and all(i.startswith("get_") for i in ids)
    for op in ops:
        schema = op["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" in schema or schema.get("type") == "array"  # every response is typed
