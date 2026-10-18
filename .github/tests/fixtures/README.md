# Saved receipt fixture

`pr8-summary.txt` contains verbatim summary rows extracted from the committed
`tools/run_all_tests.last-run.log` in the T8 engineer's branch, before review
changes. Only lines whose second field was PASS/FAIL/SKIPPED/BLOCKED were retained;
ordinary `make: ***` diagnostic lines are not summary rows.
Source commit: `3384093a407224d792558fb098a3ca8c3b06e854`.

This is MEASURED historical Mac software evidence, including the known
`link_bench` failures. `test_saved_real_receipt_inventory_and_future_locations`
uses its suite inventory to construct temporary, synthetic repository layouts.
It checks that the runner preserves every historical suite and discovers the
specified future locations. It does not turn these historical results into PASS
or replace the actual repository tests, which run separately in the aggregate.
