"""Retrieval demonstration script.

Usage:
    python -m scripts.test_retrieval --query "What is required for Udyam registration?" --top-k 5
"""

from __future__ import annotations

import argparse
import json

from rag.config.settings import ensure_directories
from rag.config.logging_config import configure_logging, get_logger
from rag.retrieval.engine import RetrievalEngine

logger = get_logger("test_retrieval")


def main() -> None:
    configure_logging()
    ensure_directories()
    parser = argparse.ArgumentParser(
        description="Run a semantic retrieval demo against the knowledge base"
    )
    parser.add_argument(
        "--query", required=True,
        help="Natural language query"
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="Number of results to return"
    )
    args = parser.parse_args()

    engine = RetrievalEngine()
    result = engine.retrieve_guidance(
        query=args.query,
        business_context={},
        top_k=args.top_k,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
