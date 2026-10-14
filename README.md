# Variable-Rank Survey


This repository contains data and a presentation page for the paper "Variable-Rank Adaptation: A Comprehensive Survey of Rank Budgeting LoRA Variants".




## Repository Structure

The repository contains the **survey data** (`data`) as well as files to build the web page.

```
├── .github  (github workflow to build the web page)
├── data (survey data)
    ├── group-config.yaml  (definition of the taxonomy and design dimensions)
    ├── methods.json  (methods extracted from Zotero via a script)
    ├── papers.json  (papers exported from within Zotero)
    └── ...
├── scripts
    ├── buiild.py (scripts to build the web page)
    └── extract-methods.py (scripts to extract method notes from Zotero)
├── static (static files used on the web page)
├── templates (templates used for building the web page)
└── README.md (this file)
```


## Web Page

The webpage is defined via the jinja templates in the `templates` directory as well as the survey data in the `data` directory.


### Building the Web Page

Run `uv run scripts/build.py` to build the static HTML files.

Use `cd build; uv run --no-project -m http.server` to run a development server.
