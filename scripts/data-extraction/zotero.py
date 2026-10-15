import requests
import json


class ZoteroInterface():
    URL = "http://127.0.0.1:23119/better-bibtex/export?/library;name:My%20Library/collection/Variable-rank%20Adaptation/Methods.jzon"
    SELECT_URL = "zotero://select/library/items/{itemKey}"


    @classmethod
    def select_link(cls, item=None, itemKey: str | None = None):
        if itemKey is None:
            assert item is not None
            itemKey = item["item-key"]
        selectURL = cls.SELECT_URL.format(itemKey=itemKey)

        text = itemKey
        return f"[link={selectURL}]{text}[/link]"



    @classmethod
    def get_all_items(cls):
        try:
            r = requests.get(cls.URL)
            r.raise_for_status()

            json = r.json()

            return json["items"]
        except ConnectionError:
            msg = "Could retrieve Zotero collection: Make sure zotero is running!"
            raise RuntimeError(msg)

    @classmethod
    def has_tag(cls, item, tag: str):
        if "tags" not in item:
            return False

        for t in item["tags"]:
            if t["tag"] == tag:
                return True
        return False

    @classmethod
    def get_result_tables(cls):
        for item in cls.get_all_items():
            if item["itemType"] == "note":
                continue

    @classmethod
    def get_items(cls, itemKey: str | None = None, **kw):
        url = "http://localhost:23119/api/users/0/items"

        if itemKey is not None:
            url += f"/{itemKey}"

        if len(kw) > 0:
            params = "&".join(f"{k}={v}" for k, v in kw.items())
            url += f"?{params}"

        try:
            r = requests.get(url)
            r.raise_for_status()

            return r.json()

        except ConnectionError:
            msg = "Could retrieve Zotero collection: Make sure zotero is running!"
            raise RuntimeError(msg)


    @classmethod
    def get_annotation_tree(cls):
        pdf_items = {}

        for item in cls.get_items(itemType="annotation"):
            if not cls.has_tag(item["data"], "results-table"):
                continue

            parentKey = item["data"]["parentItem"]

            if parentKey not in pdf_items:
                pdf = cls.get_items(parentKey)
                paper = cls.get_items(pdf["data"]["parentItem"])["data"]


                del paper["collections"]
                del paper["tags"]
                del paper["dateAdded"]
                del paper["dateModified"]
                del paper["relations"]

                pdf_items[parentKey] = {
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

            pdf_items[parentKey]["annotations"].append(item_data)

        return pdf_items


