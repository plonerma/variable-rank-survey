import requests
import json


class ZoteroInterface():
    URL = "http://127.0.0.1:23119/better-bibtex/export?/library;name:My%20Library/collection/Variable-rank%20Adaptation/Methods.jzon"
    SELECT_URL = "zotero://select/library/items/{itemKey}"


    @classmethod
    def select_link(cls, item=None, itemKey: str | None = None):
        """https://stackoverflow.com/a/71309268"""
        if itemKey is None:
            assert item is not None
            itemKey = item["item-key"]
        selectURL = cls.SELECT_URL.format(itemKey=itemKey)

        text = itemKey

        # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
        escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

        return escape_mask.format("", selectURL, text)

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





