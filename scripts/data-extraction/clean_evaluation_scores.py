#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ruamel.yaml",
# ]
# ///
from typing import Any
import csv
import json
from pathlib import Path
from ruamel.yaml import YAML


yaml = YAML()

CLEANING_DATA_PATH  = _dir = Path(__file__).parent / "cleaning_data"


class EntryCleaner():
    def __init__(
        self,
        model_rules=CLEANING_DATA_PATH / "model_names.yaml",
        metric_rules=CLEANING_DATA_PATH / "metric_names.yaml",
        task_rules=CLEANING_DATA_PATH / "task_names.yaml",
        method_rules=CLEANING_DATA_PATH / "method_mentions.yaml",
    ):
        pass
        with open(model_rules) as _f:
            self.model_rules = yaml.load(_f)

        with open(metric_rules) as _f:
            self.metric_rules = yaml.load(_f)

        with open(task_rules) as _f:
            self.task_rules = yaml.load(_f)

        with open(method_rules) as _f:
            self.method_rules = yaml.load(_f)

    @staticmethod
    def get_slug(name):
        if not isinstance(name, str):
            return None
        else:
            return name.lower().replace(" ", "").replace("_", "").replace("-", "")

    def is_valid(self, entry) -> bool:
        if entry.get("model") is None or self.get_slug(entry["model"]) in self.model_rules["invalid"]:
            return False

        if entry.get("evaluation_task") is None or self.get_slug(entry["evaluation_task"]) in self.task_rules["invalid"]:
            return False

        if entry.get("metric_name") is None or self.get_slug(entry["metric_name"]) in self.metric_rules["invalid"]:
            return False

        return True

    def __call__(self, entry: dict[str, Any], skip_invalid: bool = True) -> dict[str, Any] | None:
        if skip_invalid and not self.is_valid(entry):
            return None

        entry["model"] = self.model_rules["canonical"].get(self.get_slug(entry["model"]))
        entry["evaluation_task"] = self.task_rules["canonical"].get(self.get_slug(entry["evaluation_task"]))
        entry["metric_name"] = self.task_rules["canonical"].get(self.get_slug(entry["metric_name"]), None)

        for method in self.method_rules:
            if entry["method"].strip() == method["mention"] and entry["paper-id"] in method["papers"]:
                if len(method["id"]) == 0 and skip_invalid:
                    return
                else:
                    entry["method-id"] = method["id"]
                    return entry

        if not skip_invalid:
            return entry


def load_extracted_scores():
    table_paper_map = {}

    with open("data/table_index.json") as f:
        for paperId, tables in json.load(f).items():
            for table in tables:
                table_paper_map[table] = paperId

    results_path = Path("data/extracted_scores")

    clean_entries = EntryCleaner()

    rows: list[dict[str, Any]] = []

    fieldnames: list[str] = ["method-id", "paper-id"]

    for p in results_path.glob("*.json"):
        with p.open() as f:
            table_data = json.load(f)

        for entry in table_data["entries"]:
            entry["paper-id"] = table_paper_map[p.stem]

            e = clean_entries(entry)

            if e:
                fieldnames.extend(k for k in e.keys() if k not in fieldnames)
                rows.append(e)

    with open("data/evaluation_results.tsv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, dialect=csv.excel_tab)

        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    load_extracted_scores()




