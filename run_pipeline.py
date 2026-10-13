import argparse
import sys

import yaml

import src.download as dl

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Add config", type=str)
parser.add_argument(
    "-d", "--skip-download", help="Skip Download Data", action="store_true"
)
parser.add_argument("-l", "--skip-llm", help="Skip LLM", action="store_true")
parser.add_argument(
    "-v", "--verbose", help="Increase output verbosity", action="store_true"
)

args = parser.parse_args()

configPath = args.config


if args.skip_llm:
    print("skiped llm\n")


if args.config != None:
    try:
        with open(configPath, "r", encoding="utf-8") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
    except OSError:
        print("Could not read file: ", configPath)
        sys.exit()

    if not args.skip_download:
        dl.Download(data, args.verbose)
