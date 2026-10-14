# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "staticjinja",
# ]
# ///

import argparse
from staticjinja import Site


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--reload", action='store_true')
    args = parser.parse_args()

    site = Site.make_site(outpath="build")

    # enable automatic reloading
    site.render(use_reloader=args.reload)
