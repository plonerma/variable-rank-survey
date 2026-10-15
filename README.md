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
    ├── build.py (scripts to build the web page)
    └── data-extraction (scripts to extract data from Zotero)
        └── extract-methods.py (creates data/methods.json)
├── static (static files used on the web page)
├── templates (templates used for building the web page)
└── README.md (this file)
```


## Web Page

The webpage is defined via the jinja templates in the `templates` directory as well as the survey data in the `data` directory.


### Building the Web Page

Run `uv run scripts/build.py` to build the static HTML files.

#### Local Testing

Run `uv run scripts/build.py -l -r` to build the static HTML files: `-l` sets the URL to `/` and `-r` lets the script watch the template directory for changes.

In the build directory, use `uv run --no-project -m http.server` to run a development server (add a link to the static files in the build directory: `ln -s ../static`).
