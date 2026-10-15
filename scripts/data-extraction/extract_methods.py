#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "beautifulsoup4",
#     "pandas",
#     "requests",
#     "rich",
#     "python-slugify",
# ]
# ///

import re
from itertools import chain

from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.style import Style
import pandas as pd

from slugify import slugify

from zotero import ZoteroInterface


URL = "http://127.0.0.1:23119/better-bibtex/export?/library;name:My%20Library/collection/Variable-rank%20Adaptation/Methods.jzon"

SELECT_URL = "zotero://select/library/items/{item_key}"
TAG = "Variable-Rank Method"



console = Console()


class ZoteroItems(ZoteroInterface):
    debug = False

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
                console.rule(cls.select_link(item_properties))
                console.print(item)

            found_method = False
            for note in item["notes"]:
                if cls.has_tag(note, tag=TAG):
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
                    f"Found no method-note for {cls.select_link(item_properties)}",
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

if __name__ == "__main__":
    df = ZoteroItems.get_dataframe()

    df.to_json("data/methods.json", orient="records")
