from datalens.data import read_dataset
from datalens.mcp_client import call, connect


async def test_real_mcp_statistics_and_quality(context):
    _, store, scope, ident = context
    async with connect(store.root, scope) as server:
        listing = await server.list_tools()
        assert len(listing.tools) == 7
        summary = await call(server, "summarize_numeric", {"dataset_id": ident, "columns": ["revenue"]})
        assert next(x for x in summary["statistics"] if x["statistic"] == "sum")["revenue"] == 530
        quality = await call(server, "check_data_quality", {"dataset_id": ident})
        assert quality["missing"]["customer_note"] == 1
        groups = await call(server, "aggregate_data", {"dataset_id": ident, "group_by": "product", "value_column": "revenue"})
        assert groups["groups"][0] == {"product": "Honey", "revenue": 300}
        compare = await call(server, "compare_groups", {"dataset_id": ident, "group_by": "branch", "value_column": "revenue"})
        assert compare["groups"][0]["sum"] == 320
        filtered = await call(server, "filter_rows", {"dataset_id": ident, "column_name": "revenue", "operator": "gt", "value": "90"})
        assert filtered["matching_rows"] == 2


async def test_write_requires_matching_one_use_grant(context):
    _, store, scope, _ = context
    async with connect(store.root, scope) as server:
        assert "error" in await call(server, "save_report", {"content": "Test report"})
        token = store.grant(scope, {"content": "Approved report"})
        assert "error" in await call(server, "save_report", {"content": "Different report", "approval_token": token})
        saved = await call(server, "save_report", {"content": "Approved report", "approval_token": token})
        assert saved["saved"]
        assert (store.workspace(scope) / "reports" / saved["report_id"]).read_text() == "Approved report"
        assert "error" in await call(server, "save_report", {"content": "Approved report", "approval_token": token})


async def test_hostile_path_and_unknown_tool(context):
    _, store, scope, _ = context
    async with connect(store.root, scope) as server:
        result = await call(server, "inspect_dataset", {"dataset_id": "../../.env"})
        assert "error" in result
        assert "error" in await call(server, "shell", {"command": "cat .env"})
    assert read_dataset(store.workspace(scope), context[3]).shape == (6, 7)
