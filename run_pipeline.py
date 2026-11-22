import argparse
import json
import sys
from types import SimpleNamespace

import src.download as dl
import src.filtering as fi
from src import llm, qa, test
from src.baseline import RunBaseline
from src.evaluate import RunEvaluate
from src.kpi import RunKpi
from src.utility import *
from src.viz import RunViz

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Add config", type=str)
parser.add_argument("-d", "--download", help="Download Data", action="store_true")
parser.add_argument("-l", "--llm", help="Run LLM", action="store_true")
parser.add_argument("-f", "--filter", help="Filtering team", action="store_true")
parser.add_argument("-q", "--qa", help="Run qa", action="store_true")
parser.add_argument(
    "--save-flags", help="Save this flags for later run", action="store_true"
)
parser.add_argument("-t", "--test", action="store_true")
parser.add_argument("-b", "--baseline", action="store_true")
parser.add_argument("-e", "--evaluate", action="store_true")
parser.add_argument("-v", "--viz", action="store_true")
parser.add_argument("-k", "--kpi", action="store_true")


def Init():
    LoadConfig()
    Phancong.Create("pc", "csv")
    Team.Create("team", "csv")
    Raw.Create(CONFIG.snapshots, "raw", "csv.gz")
    Filtered.Create(CONFIG.snapshots, "filtered", "csv")
    Processed.Create(CONFIG.snapshots, "processed", "csv")

    Llm.Create("reviews", "llm", "csv")
    Llm.Create("response", "llm", "json")
    Llm.Create("clean_response", "llm", "json")
    Llm.Create("comments", "baseline", "json")


args = parser.parse_args()
Init()

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
    dl.Download()

if args.filter:
    dl.FilterSamples()
    fi.Filter()
    llm.GetReviews()

if args.test:
    test.Test()

if args.llm:
    llm.Init()
    llm.RunLLM()

if args.qa:
    for t in CONFIG.snapshots:
        time = t.strftime("%Y-%m-%d")
        qa.QAListings(time)
        qa.QACalendar(time)
        qa.QAReviews(time)
    llm.CleanLLM()

if args.baseline:
    RunBaseline()

if args.evaluate:
    RunEvaluate()

if args.kpi:
    RunKpi()

if args.viz:
    RunViz()
