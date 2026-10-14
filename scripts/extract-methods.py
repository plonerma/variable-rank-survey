#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "beautifulsoup4",
#     "click",
#     "pandas",
#     "requests",
#     "rich",
#     "python-slugify",
# ]
# ///

import re
import requests
from requests.exceptions import ConnectionError
from itertools import chain

from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.style import Style
import click
import pandas as pd

from slugify import slugify

URL = "http://127.0.0.1:23119/better-bibtex/export?/library;name:My%20Library/collection/Variable-rank%20Adaptation/Methods.jzon"

SELECT_URL = "zotero://select/library/items/{item_key}"
TAG = "Variable-Rank Method"



GROUP_DIMENSIONS = {
    "growth": {
        "granularity": ("\\dimension{granularity}", "P{5em}"),
        "selection criterion": ("\\dimension{criterion}", "C"),
        "reparametrization": ("\\dimension{parametrization}", "C"),
        "orthonormalization": ("\\dimension{orthonormalization}", "C"),
        "initialization": ("\\dimension{initialization}", "C"),
    },
    "pre-allocation": {
        "granularity": ("\\dimension{granularity}", "P{5em}"),
        "selection source": ("\\dimension{signal}", "C"),
        "selection criterion": ("\\dimension{criterion}", "C"),
        "initialization": ("\\dimension{initialization}", "C"),
    },
    "pruning_mid-tuning": {
        "granularity": ("\\dimension{granularity}", "P{5em}"),
        "selection criterion": ("\\dimension{criterion}", "C"),
        "reparametrization": ("\\dimension{parametrization}", "C"),
        "orthonormalization": ("\\dimension{orthonormalization}", "C"),
        "sparsity induction": ("\\dimension{sparsity}", "C"),
    },
    "pruning_post-tuning": {
        "granularity": ("\\dimension{granularity}", "P{5em}"),
        "selection criterion": ("\\dimension{criterion}", "C"),
        "reparametrization": ("\\dimension{parametrization}", "C"),
        "orthonormalization": ("\\dimension{orthonormalization}", "C"),
        "sparsity induction": ("\\dimension{sparsity}", "C"),
    },
    "redistribution": {
        "granularity": ("\\dimension{granularity}", "P{5em}"),
        "selection criterion": ("\\dimension{criterion}", "C"),
        "redistribution mode": ("\\dimension{redistribution}", "C"),
        "reparametrization": ("\\dimension{parametrization}", "C"),
    },
    "trial-based search": {
        "granularity": ("\\dimension{granularity}", "P{5em}"),
        "search algorithm":  ("\\dimension{search algorithm}", "C"),
        #"selection criterion": ("\\dimension{criterion}", "C"),
    },
}


REQUIRED_PROPERTIES = [
    "cite-key", "method", "type", "sub-type", "base model compression",
    "code available",
    "code url provided",
]



console = Console()

def select_link(item):
    selectURL = SELECT_URL.format(item_key=item["item-key"])
    text = item["cite-key"]
    return f"[link={selectURL}]{text}[/link]"

class ZoteroItems():
    debug = False

    @classmethod
    def get_all_items(cls):
        try:
            r = requests.get(URL)
            r.raise_for_status()

            json = r.json()

            return json["items"]
        except ConnectionError:
            console.print(
                "Could retrieve Zotero collection: Make sure zotero is running!",
                style="red",
            )
            quit(1)

    @classmethod
    def note_has_tag(cls, note, tag: str = TAG):
        for t in note["tags"]:
            if t["tag"] == TAG:
                return True
        return False

    @classmethod
    def get_methods(cls):
        all_method_ids = set()

        for item in cls.get_all_items():
            if item["itemType"] == "note":
                continue

            item_properties = {
                "paper-id": item["citationKey"],
            }


            if cls.debug:
                console.rule(select_link(item_properties))
                console.print(item)

            found_method = False
            for note in item["notes"]:
                if cls.note_has_tag(note):
                    html = BeautifulSoup(note["note"], features="html.parser")

                    method = {**item_properties}

                    for p in chain(html.find_all("h1"), html.find_all("p")):
                        if ":" not in p.text:
                            continue
                        key, value = p.text.split(":", 1)
                        value = value.strip()

                        if len(value) == 0:
                            continue
                        elif value in ("n/a", "-"):
                            value = None

                        key = key.strip().lower()

                        method[key] = value

                    if method["method"] is None:
                        console.print("Method without name (ignoring):", style="red")
                        console.print(method)

                        continue

                    else:
                        yield method
                        found_method = True

                    method["name"] = method["method"]
                    del method["method"]
                    #method["id"] = method["paper-id"] + "_" + slugify(method["name"], replacements=[("+", "plus")])
                    method["id"] = slugify(method["name"], replacements=[("+", "plus")])

                    assert method["id"] not in all_method_ids
                    all_method_ids.add(method["id"])

                    console.print(method)

            if not found_method:
                console.print(
                    f"Found no method-note for {select_link(item_properties)}",
                    style="red",
                )

    @classmethod
    def get_dataframe(cls):
        methods = cls.get_methods()

        df = pd.DataFrame.from_records(methods)

        pattern = re.compile(r"((\s)?\([^\)]*\))")

        def clean_type(t: str) -> str:
            if pd.isna(t):
                return ""

            t = re.sub(pattern, "", t)
            t = t.replace("training", "tuning").strip()

            if t == "-":
                return ""
            else:
                return t

        df["sub-type-clean"] = df["sub-type"].apply(clean_type)
        df["type-clean"] = df["type"].apply(clean_type)

        df["type-path"] = df["type-clean"].str.cat(df["sub-type-clean"].fillna(""), sep="_").str.strip("_")


        return df


def dataframe_to_table(df):
    df = df.copy()
    df = df.fillna("")
    df = df.astype(str)

    def make_link(url):
        if url is None or len(url) == 0 or url == "-":
            return url
        else:
            return Text(url, style=Style(link=url))

    df["code url"] = df["code url"].apply(make_link)

    table = Table(row_styles=["on grey11", ""])
    for col in df.columns:
        table.add_column(col)

    for row in df.values:
        try:
            table.add_row(*row)
        except:
            print(row)
            raise

    return table







def export_group_tables(df):
    df = df.copy()
    
    for group, group_data in df.groupby("type-path"):
        group_data = group_data.sort_values(by=["date"])

        path = f"latex/{group}.tex"


        if group not in GROUP_DIMENSIONS:
            console.print(f"Skipping group {group}")
            continue

        console.print(f"Saving {path}")

        with open(path, "w") as f:
            f.write("% This file is automatically generated. Changes will not persist!\n%\n")
            f.write(r"\newcolumntype{C}{>{\centering\arraybackslash}X}%" + "\n")
            f.write(r"\newcolumntype{P}[1]{>{\centering\arraybackslash}p{#1}}%" + "\n")

            f.write("\\begin{tabularx}{\\linewidth}{p{9em}" + "".join(v[1] for v in GROUP_DIMENSIONS[group].values()) + "}\n")
            f.write("\\toprule\n")
            f.write(" & ".join(["Method", *(v[0] for v in GROUP_DIMENSIONS[group].values())]))
            f.write(" \\\\\n")
            f.write("\\midrule\n")

            for _, method in group_data.iterrows():
                method = method.copy()
                method[method.isna()] = ""


                cells = [
                    "\\method{{{method}}} \\citep{{{cite-key}}}".format(**method)
                ]

                for dim in GROUP_DIMENSIONS[group].keys():
                    cells.append(method[dim].replace("&", "\\&"))

                f.write(" & ".join(cells))
                f.write(" \\\\\n")
            f.write("\\bottomrule\n")
            f.write("\\end{tabularx}")


@click.command()
@click.option("--debug", is_flag=True)
@click.option("--latex", is_flag=True)
def run(debug: bool = False, latex: bool = False):
    df = ZoteroItems.get_dataframe()

    df.to_json("data/methods.json", orient="records")

    if latex:
        export_group_tables(df)


if __name__ == "__main__":
    run()
