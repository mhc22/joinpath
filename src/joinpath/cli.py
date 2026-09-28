from __future__ import annotations

import argparse
import json
import sys

from .plan import plan_question
from .schema import Schema


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="joinpath",
        description="Retrieve the schema subgraph an NL2SQL agent should be allowed to see.",
    )
    parser.add_argument("question", nargs="*", help="Natural language question")
    parser.add_argument("-s", "--schema", required=True, help="Path to schema JSON")
    parser.add_argument("--json", action="store_true", help="Machine-readable plan")
    parser.add_argument("--prompt", action="store_true", help="Print compact prompt block only")
    parser.add_argument("-k", "--top-k", type=int, default=4)
    args = parser.parse_args(argv)

    if args.question:
        question = " ".join(args.question)
    elif not sys.stdin.isatty():
        question = sys.stdin.read().strip()
    else:
        parser.error("provide a question")

    schema = Schema.from_path(args.schema)
    plan = plan_question(question, schema, top_k=args.top_k)

    if args.json:
        print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
    elif args.prompt:
        print(plan.compact_prompt())
    else:
        print(plan.summary())
        print()
        print(plan.compact_prompt())
    return 0 if plan.tables else 1


if __name__ == "__main__":
    raise SystemExit(main())
