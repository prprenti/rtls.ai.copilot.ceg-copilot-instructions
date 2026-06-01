from __future__ import annotations

from validation_mcp.benchmarks import compare_render_modes, estimate_tokens, summarize_payload


def test_estimate_tokens_grows_with_payload_size() -> None:
    assert estimate_tokens("short") < estimate_tokens("this payload is much longer than short")


def test_summarize_payload_reports_non_zero_size() -> None:
    summary = summarize_payload('{"count": 1}')
    assert summary.bytes_utf8 > 0
    assert summary.estimated_tokens > 0


def test_compare_render_modes_prefers_compact_payload() -> None:
    summary = compare_render_modes(iterations=5, warmups=1)
    assert summary.compact_smaller is True
    assert summary.compact_tokens_lower is True
    assert isinstance(summary.compact_p95_not_worse, bool)


def test_compare_render_modes_requires_positive_iterations() -> None:
    from pytest import raises

    with raises(ValueError, match=r"^iterations must be >= 1$"):
        compare_render_modes(iterations=0, warmups=0)