#!/usr/bin/env -S uv run --script
"""Check that every paper evaluating a method cites the method's own paper."""

from typing import TextIO
from collections.abc import Iterator
import csv
import json
import sys
from collections import defaultdict


def read_tsv_columns(f: TextIO, *columns: str, dialect: str="excel-tab") -> Iterator[tuple[str, ...]]:
    """DictReader (excel-tab) yielding the given columns as tuples.

    Raises ValueError on first iteration if required columns are missing.
    """
    reader = csv.DictReader(f, dialect=dialect)
    missing = [c for c in columns if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"{f.name}: missing column(s) {missing}; found {reader.fieldnames}")

    for row in reader:
        yield tuple(row[c] for c in columns)



def load_evaluated_pairs(path: str) -> set[tuple[str, str]]:
    """Return unique (evaluating paper, method id) pairs, ignoring other-* methods."""
    with open(path, encoding="utf-8", newline="") as f:
        return {
            (paper, method_id)
            for paper, method_id in read_tsv_columns(f, "paper-id", "method-id")
            if not method_id.startswith("other-")
        }


def main(citations_path: str, evals_path: str, methods_path: str) -> int:
    with open(citations_path, encoding="utf-8", newline="") as f:
        edges = set(read_tsv_columns(f, "citing", "cited"))

    citing_papers = {citing for citing, _ in edges}

    methods: dict[str, set[str]] = defaultdict(set)  # method id -> introducing paper-ids

    with open(methods_path) as f:
        for m in json.load(f):
            methods[m["id"]].add(m["paper-id"])

    pairs = load_evaluated_pairs(evals_path)

    missing, unknown_method, no_citations = [], [], []
    for paper, method_id in sorted(pairs):
        origin_papers = methods.get(method_id)
        if not origin_papers:
            unknown_method.append((paper, method_id))
            continue
        if paper in origin_papers:
            continue  # paper evaluates its own method
        if paper not in citing_papers:
            no_citations.append((paper, method_id))
            continue
        if not any((paper, o) in edges for o in origin_papers):
            missing.append((paper, method_id, sorted(origin_papers)))

    print(f"Checked {len(pairs)} (paper, method) evaluation pairs.\n")

    if missing:
        print(f"Missing citations ({len(missing)}):")
        for paper, method_id, origins in missing:
            print(f"  {paper} evaluates {method_id} but does not cite {', '.join(origins)}")
    if unknown_method:
        print(f"\nMethod id not found in methods file ({len(unknown_method)}):")
        for paper, method_id in unknown_method:
            print(f"  {paper}: {method_id}")
    if no_citations:
        print(f"\nEvaluating paper has no outgoing citations recorded ({len(no_citations)}):")
        for paper, method_id in no_citations:
            print(f"  {paper}: {method_id}")

    if not (missing or unknown_method or no_citations):
        print("All good.")
    return 1 if missing else 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(f"Usage: {sys.argv[0]} citations.tsv evaluations.tsv methods.json")
    sys.exit(main(*sys.argv[1:]))
