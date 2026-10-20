# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "staticjinja",
#     "ruamel.yaml",
#     "python-slugify",
# ]
# ///
from typing import TextIO
from collections.abc import Iterator
import csv
import argparse
import json
from pathlib import Path
from staticjinja import Site
from urllib.parse import urlparse
from ruamel.yaml import YAML
from slugify import slugify



PAPERS_PATH = "data/papers.json"
METHODS_PATH = "data/methods.json"
GROUP_CONFIG_PATH = "data/group-config.yaml"
CITATIONS_PATH = "data/citations.tsv"
EVALUATIONS_PATH = "data/evaluation_results.tsv"
CSL_STYLE = "./association-for-computational-linguistics.csl"


def render_paper_details(site, template, **kw):
    survey_data = site.env.globals["survey_data"]

    for paper in survey_data["papers"].values():
        out = Path(site.outpath) / "papers" / Path(paper["id"].lower()).with_suffix(".html")
        out.parent.mkdir(exist_ok=True)

        print("Writing", paper["id"], "to", out)
        template.stream(paper=paper, **kw).dump(str(out), encoding="utf-8")


def render_method_details(site, template, **kw):
    survey_data = site.env.globals["survey_data"]

    for method in survey_data["methods"].values():
        out = Path(site.outpath) / "methods" / Path(method["id"].lower()).with_suffix(".html")
        out.parent.mkdir(exist_ok=True)

        print("Writing", method["id"], "to", out)
        template.stream(method=method, **kw).dump(str(out), encoding="utf-8")


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


def load_survey_data(metadata):
    with open(PAPERS_PATH) as f:
        papers = json.load(f)

    with open(METHODS_PATH) as f:
        methods = json.load(f)

    yaml = YAML()

    with open(GROUP_CONFIG_PATH) as f:
        group_config = yaml.load(f)

    for paper in papers:
        for author in paper["author"]:
            author["full"] = author["literal"] if "literal" in author else author["given"] + " " + author["family"]
            author["short"] = author["literal"] if "literal" in author else author["family"]

        if (len(paper["author"]) > 2):
            paper["authors_short"] = f"{paper['author'][0]['short']} et al."
        else:
            paper["authors_short"] = " & ".join(map(lambda a: a["short"], paper["author"]))

        paper["url"] = f"{metadata['url']}papers/{paper['id'].lower()}.html"
        paper["year"] = paper["issued"]["date-parts"][0][0]
        paper["proposed_methods"] = []
        paper["evaluated_methods"] = []
        paper["cited_papers"] = []
        paper["cited_by_papers"] = []
        paper["evaluated_tasks"] = []
        
    papers = {paper["id"]: paper for paper in papers}

    for group in group_config["groups"].values():
        group["methods"] = []
        group["id"] = slugify(group["name"])

    for method in methods:
        method["url"] = f"{metadata['url']}methods/{method['id']}.html"
        method["paper"] = papers[method["paper-id"]]
        papers[method["paper-id"]]["proposed_methods"].append(method)

        group_config["groups"][method["type-path"]]["methods"].append(method)
        method["group"] = group_config["groups"][method["type-path"]]

        method["evaluated_in"] = []

    methods = {method["id"]: method for method in methods}

    with open(EVALUATIONS_PATH, encoding="utf-8", newline="") as f:
        for paper, method, task in read_tsv_columns(f, "paper-id", "method-id", "evaluation_task"):
            if len(task)>0 and task not in papers[paper]["evaluated_tasks"]:
                papers[paper]["evaluated_tasks"].append(task)

            if method.startswith("other-"):
                # Common method, not part of surveyed methods
                continue

            if paper not in methods[method]["evaluated_in"]:
                methods[method]["evaluated_in"].append(paper) 

            if method not in papers[paper]["evaluated_methods"]:
                papers[paper]["evaluated_methods"].append(method)

    with open(CITATIONS_PATH, encoding="utf-8", newline="") as f:
        for citing, cited in read_tsv_columns(f, "citing", "cited"):
            if citing not in papers[cited]["cited_by_papers"]:
                papers[cited]["cited_by_papers"].append(citing)

            if cited not in papers[citing]["cited_papers"]:
                papers[citing]["cited_papers"].append(cited)

    return {
        "papers": papers,
        "methods": methods,
        "group_config": group_config,
    }



def load_metadata():
    with open("templates/metadata.json") as f:
        metadata = json.load(f)

    metadata["affiliations"] = []
    affiliation_names = []

    for i, author in enumerate(metadata["author"]):
        for a in author["affiliation"]:
            if a["name"] not in affiliation_names:
                if i > 0:
                    metadata["affiliations_shared"] = False

                metadata["affiliations"].append(a)
                affiliation_names.append(a["name"])

            a["index"] = affiliation_names.index(a["name"])

        if len(author["affiliation"]) < len(affiliation_names):
            metadata["affiliations_shared"] = False

    return metadata

if __name__ == "__main__":
    # Parser for --reload flag
    parser = argparse.ArgumentParser(prog="Web page builder")

    parser.add_argument(
        "-r", "--reload", action="store_true",
        help="watch for changes and rebuild page when changes have been detected"
    )

    parser.add_argument(
        "-l", "--local", action="store_true",
        help="set metadata url to `/` for local testing."
    )

    args = parser.parse_args()
    
    # Load data
    metadata = load_metadata()

    if args.local:
        metadata["url"] = "/"

    survey_data = load_survey_data(metadata)

    site = Site.make_site(
        # Make the data available in all templates
        env_globals={
            "metadata": metadata,
            "survey_data": survey_data,
        },
        # These pages will not be rendered directly. Instead, a detail page per paper/method is rendered.
        rules=[
            ("paper-detail.html", render_paper_details),
            ("method-detail.html", render_method_details),
        ],
        # Utilities for use in the jinja templates
        filters={
            "url_path": lambda url: urlparse(str(url)).path,
            "doi_url": lambda doi: doi if doi.startswith("http") else f"https://doi.org/{doi}",
            "url_domain": lambda url: urlparse(str(url)).netloc.split(":")[0],
        },
        outpath="build"
    )

    site.render(use_reloader=args.reload)
