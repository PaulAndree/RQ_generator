"""Explicitly verify saved outputs and delivered telemetry for a completed run."""

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from dotenv import dotenv_values

from rq_generator.models import Card, ChunkStore, validate_outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--expect-content", action="store_true")
    args = parser.parse_args()
    config = {**dotenv_values(), **os.environ}
    chunks = ChunkStore.model_validate_json((args.output / "chunks.json").read_text())
    cards = [Card.model_validate(c) for c in json.loads(
        (args.output / "document_cards.json").read_text())["cards"]]
    validate_outputs(chunks, cards)
    state = json.loads((args.output / "run_state.json").read_text())
    run_id = state["run_id"]
    now = datetime.now(UTC)
    start = now - timedelta(days=1)
    summary = {"cards": len(cards), "chunks": len(chunks.chunks), "run_id": run_id}
    with httpx.Client(timeout=15) as client:
        loki = client.get(config.get("LOKI_URL", "http://127.0.0.1:3101").rstrip("/")
                          + "/loki/api/v1/query_range", params={
                              "query": '{service="rq-generator",environment="'
                              + args.environment + '"} | json | run_id="' + run_id + '"',
                              "start": int(start.timestamp() * 1e9),
                              "end": int(now.timestamp() * 1e9), "limit": 1000})
        loki.raise_for_status()
        events = [json.loads(value[1]) for stream in loki.json()["data"]["result"]
                  for value in stream["values"]]
        operations = [e.get("operation") for e in events]
        assert operations.count("card_completed") == len(cards)
        assert "run_completed" in operations
        assert ("card_content" in operations) is args.expect_content
        summary["loki_operations"] = sorted(set(operations))
        prometheus = client.get(config.get("PROMETHEUS_URL", "http://127.0.0.1:9094").rstrip("/")
                                + "/api/v1/query", params={
                                    "query": 'rq_generator_document_successes{environment="'
                                    + args.environment + '"}'})
        prometheus.raise_for_status()
        result = prometheus.json()["data"]["result"]
        assert result and float(result[0]["value"][1]) == len(cards)
        summary["prometheus_successes"] = float(result[0]["value"][1])
        response = client.get(config["LANGFUSE_BASE_URL"].rstrip("/")
                              + "/api/public/v2/observations", auth=(
                                  config["LANGFUSE_PUBLIC_KEY"], config["LANGFUSE_SECRET_KEY"]),
                              params={"traceId": run_id, "limit": 1000,
                                      "fields": "core,basic,model,usage,io",
                                      "fromStartTime": start.isoformat(), "toStartTime": now.isoformat()})
        response.raise_for_status()
        observations = [o for o in response.json()["data"] if o["traceId"] == run_id]
        assert any(o.get("name") == "folder-run" for o in observations)
        generations = [o for o in observations if o.get("type") == "GENERATION"]
        assert generations and all(o.get("model") == config.get("OLLAMA_MODEL", "qwen3:14b")
                                   for o in generations)
        assert any(o.get("inputUsage", 0) > 0 and o.get("outputUsage", 0) > 0 for o in generations)
        assert any(bool(o.get("input")) or bool(o.get("output")) for o in generations) is args.expect_content
        summary["langfuse_generations"] = len(generations)
        summary["langfuse_error_observations"] = sum(o.get("level") == "ERROR" for o in observations)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
