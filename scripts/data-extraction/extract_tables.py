#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "pymupdf",
# ]
# ///




import json
from urllib.request import url2pathname
from urllib.parse import urlparse
from pathlib import Path

import pymupdf

from zotero import ZoteroInterface


class ZoteroTables(ZoteroInterface):
    @classmethod
    def get_annotation_trees(cls):
        """Get all papers with table annotations."""

        pdf_paper_map = {}  # Map PDF key to paper data

        for item in cls.get_items(itemType="annotation"):
            if not cls.has_tag(item["data"], "results-table"):
                continue

            parentKey = item["data"]["parentItem"]

            if parentKey not in pdf_paper_map:
                pdf = cls.get_items(parentKey)
                paper = cls.get_items(pdf["data"]["parentItem"])["data"]


                del paper["collections"]
                del paper["tags"]
                del paper["dateAdded"]
                del paper["dateModified"]
                del paper["relations"]

                pdf_paper_map[parentKey] = {
                    "annotations": [],
                    "pdf": pdf,
                    **paper,
                }

            item_data = item["data"]
            item_data["annotationPosition"] = json.loads(item_data["annotationPosition"])

            del item_data["tags"]
            del item_data["dateAdded"]
            del item_data["dateModified"]
            del item_data["relations"]

            pdf_paper_map[parentKey]["annotations"].append(item_data)

        return pdf_paper_map.values()


def extract():
    print("Extracting result tables")

    base_path = Path("data/tables")
    base_path.mkdir(parents=True, exist_ok=True)

    table_index = {}

    for paperData in ZoteroTables.get_annotation_trees():
        print("===", ZoteroInterface.select_link(itemKey=paperData["key"]))
        #print(paperData)

        p = urlparse(paperData["pdf"]["links"]["enclosure"]["href"])
        pdf_path = url2pathname(p.path)

        doc = pymupdf.open(pdf_path)

        tables_ids = []

        for annotation in paperData["annotations"]:
            pos = annotation["annotationPosition"]
            
            print("Extracting screenshot from page", pos["pageIndex"])

            page = doc[pos["pageIndex"]]

            left, bottom, right, top = pos["rects"][0]

            clip = pymupdf.Rect(left, page.rect.height - top, right, page.rect.height - bottom)
            pixmap = page.get_pixmap(dpi=600, clip=clip)
            annotation_key = annotation["key"]
            pixmap.save(base_path / f"{annotation_key}.png")

            with open(base_path / f"{annotation_key}.txt", "w") as f:
                f.write(annotation["annotationComment"])

            tables_ids.append(annotation_key)

        table_index[paperData["citationKey"]] = tables_ids

    with open("data/table_index.json", "w") as f:
        json.dump(table_index, f)




if __name__ == "__main__":
    extract()
