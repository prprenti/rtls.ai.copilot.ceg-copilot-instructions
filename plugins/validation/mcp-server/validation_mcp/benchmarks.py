from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Sequence

from validation_mcp.runtime.output import render_json_response, shape_named_list_result


SAMPLE_ROWS = [
    {
        "id": 101,
        "name": "fc_mem_101",
        "status": "failed",
        "owner": "jdoe",
        "i_team": "hub.memss.hub",
        "metadata": {
            "signals": [f"signal_{index}" for index in range(12)],
            "summary": "Representative nested failure metadata for response-size comparisons.",
        },
    },
    {
        "id": 102,
        "name": "fc_mem_102",
        "status": "failed",
        "owner": "asmith",
        "i_team": "hub.memss.hub",
        "metadata": {
            "signals": [f"signal_{index}" for index in range(12, 24)],
            "summary": "The compact render should stay smaller than the pretty JSON used today.",
        },
    },
]


@dataclass(frozen=True)
class TimingSummary:
    iterations: int
    warmups: int
    min_ms: float
    median_ms: float
    p95_ms: float
    max_ms: float
    mean_ms: float


@dataclass(frozen=True)
class PayloadSummary:
    bytes_utf8: int
    chars: int
    estimated_tokens: int


@dataclass(frozen=True)
class RenderComparison:
    pretty_timing: TimingSummary
    compact_timing: TimingSummary
    pretty_payload: PayloadSummary
    compact_payload: PayloadSummary
    compact_smaller: bool
    compact_tokens_lower: bool
    compact_p95_not_worse: bool


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def summarize_payload(text: str) -> PayloadSummary:
    return PayloadSummary(
        bytes_utf8=len(text.encode("utf-8")),
        chars=len(text),
        estimated_tokens=estimate_tokens(text),
    )


def summarize_timings(samples_ms: Sequence[float], *, warmups: int) -> TimingSummary:
    if not samples_ms:
        raise ValueError("iterations must be >= 1")
    ordered = sorted(samples_ms)
    p95_index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return TimingSummary(
        iterations=len(samples_ms),
        warmups=warmups,
        min_ms=round(min(ordered), 3),
        median_ms=round(statistics.median(ordered), 3),
        p95_ms=round(ordered[p95_index], 3),
        max_ms=round(max(ordered), 3),
        mean_ms=round(statistics.fmean(ordered), 3),
    )


def benchmark_render(callback: Callable[[], str], *, iterations: int, warmups: int) -> TimingSummary:
    for _ in range(warmups):
        callback()

    samples_ms: list[float] = []
    for _ in range(iterations):
        started_at = time.perf_counter()
        callback()
        samples_ms.append((time.perf_counter() - started_at) * 1000)
    return summarize_timings(samples_ms, warmups=warmups)


def build_sample_payload() -> dict[str, Any]:
    return shape_named_list_result("failure_clusters", SAMPLE_ROWS)


def compare_render_modes(*, iterations: int = 50, warmups: int = 3) -> RenderComparison:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if warmups < 0:
        raise ValueError("warmups must be >= 0")

    payload = build_sample_payload()

    def pretty_render() -> str:
        return render_json_response(payload, pretty=True)

    def compact_render() -> str:
        return render_json_response(payload, pretty=False)

    pretty_timing = benchmark_render(pretty_render, iterations=iterations, warmups=warmups)
    compact_timing = benchmark_render(compact_render, iterations=iterations, warmups=warmups)
    pretty_payload = summarize_payload(pretty_render())
    compact_payload = summarize_payload(compact_render())

    return RenderComparison(
        pretty_timing=pretty_timing,
        compact_timing=compact_timing,
        pretty_payload=pretty_payload,
        compact_payload=compact_payload,
        compact_smaller=compact_payload.bytes_utf8 < pretty_payload.bytes_utf8,
        compact_tokens_lower=compact_payload.estimated_tokens < pretty_payload.estimated_tokens,
        compact_p95_not_worse=compact_timing.p95_ms <= pretty_timing.p95_ms,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare pretty and compact validation MCP JSON rendering")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmups", type=int, default=3)
    args = parser.parse_args()

    result = compare_render_modes(iterations=args.iterations, warmups=args.warmups)
    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
        return

    print("Pretty payload:", asdict(result.pretty_payload))
    print("Compact payload:", asdict(result.compact_payload))
    print("Pretty timing:", asdict(result.pretty_timing))
    print("Compact timing:", asdict(result.compact_timing))
    print(
        "Summary:",
        {
            "compact_smaller": result.compact_smaller,
            "compact_tokens_lower": result.compact_tokens_lower,
            "compact_p95_not_worse": result.compact_p95_not_worse,
        },
    )


if __name__ == "__main__":
    main()