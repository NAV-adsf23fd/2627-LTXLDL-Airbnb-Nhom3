import argparse
import json
import sys
from types import SimpleNamespace

import src.download as dl
from src import llm
from src.utility import LoadConfig

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Add config", type=str)
parser.add_argument("-d", "--download", help="Download Data", action="store_true")
parser.add_argument("-l", "--llm", help="Run LLM", action="store_true")
parser.add_argument(
    "-v", "--verbose", help="Increase output verbosity", action="store_true"
)
parser.add_argument("-f", "--filter", help="Filtering team", action="store_true")
parser.add_argument(
    "--save-flags", help="Save this flags for later run", action="store_true"
)


args = parser.parse_args()

if len(sys.argv) == 1:
    try:
        with open("configs/lastest_run.json", "r", encoding="utf-8") as f:
            args = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
    except OSError:
        print("Could not read file: ", "configs/lastest_run.json")
        sys.exit()


if args.save_flags:
    with open("configs/lastest_run.json", "w", encoding="utf-8") as f:
        json.dump(vars(args), f, indent=4, ensure_ascii=False)


if args.config != None:
    LoadConfig(args.config)

    if args.download:
        dl.Download(args.verbose)

    if args.filter:
        dl.FilterSamples()


if args.llm:
    llm.RunLLM()
