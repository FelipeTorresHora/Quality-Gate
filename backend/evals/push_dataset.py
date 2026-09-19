#!/usr/bin/env python3
"""Push the git-versioned AI review golden dataset to LangSmith as qg-ai-review-v1.

The JSON files in evals/datasets/ai_review/ are the source of truth. LangSmith is
the optional runner. Requires LANGSMITH_API_KEY. Does not call OpenAI.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DATASET_NAME = "qg-ai-review-v1"
DATASET_DIR = Path(__file__).resolve().parent / "datasets" / "ai_review"


def load_examples() -> list[dict]:
    examples = []
    for path in sorted(DATASET_DIR.glob("*.json")):
        payload = json.loads(path.read_text())
        examples.append(
            {
                "id": payload["id"],
                "inputs": payload["inputs"],
                "outputs": payload["outputs"],
            }
        )
    return examples


def main() -> int:
    if not os.environ.get("LANGSMITH_API_KEY"):
        print("LANGSMITH_API_KEY is not set; skip dataset push.", file=sys.stderr)
        return 0

    from langsmith import Client

    examples = load_examples()
    client = Client()
    try:
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
    except Exception:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="PR Quality Gate AI review golden examples (code evaluators).",
        )
    existing = {
        example.metadata.get("example_id")
        for example in client.list_examples(dataset_id=dataset.id)
    }
    created = 0
    for example in examples:
        if example["id"] in existing:
            continue
        client.create_example(
            dataset_id=dataset.id,
            inputs=example["inputs"],
            outputs=example["outputs"],
            metadata={"example_id": example["id"]},
        )
        created += 1
    print(f"dataset={DATASET_NAME} examples={len(examples)} created={created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
