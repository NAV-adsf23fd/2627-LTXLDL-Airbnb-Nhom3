import argparse
import src.llm as llm
import pandas as pd
import json
import sys
from types import SimpleNamespace

import src.download as dl
from src.utility import LoadConfig

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Add config", type=str)
parser.add_argument(
    "-d", "--skip-download", help="Skip Download Data", action="store_true"
)
parser.add_argument("-l", "--skip-llm", help="Skip LLM", action="store_true")
parser.add_argument(
    "-v", "--verbose", help="Increase output verbosity", action="store_true"
)
parser.add_argument(
    "-f", "--skip-filter", help="Skip filtering samples", action="store_true"
)
parser.add_argument(
    "--save-flags", help="Save this flags for later run", action="store_true"
)
parser.add_argument("--run-llm", action="store_true")
parser.add_argument("--quick-check", action="store_true")
parser.add_argument("--get-llm", action="store_true")

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

    if not args.skip_download:
        dl.Download(args.verbose)

    if not args.skip_filter:
        dl.FilterSamples()


def TestLLM():
    if args.run_llm:
        rv = pd.read_csv("data/test/llm.csv")
        llm.RunLLM(rv["reviews"])
    elif args.quick_check:
        llm.QuickCheckBatch()
    elif args.get_llm:
        llm.GetLLMOutput()
        llm.OutputProcessing()


if not args.skip_llm:
    TestLLM()
