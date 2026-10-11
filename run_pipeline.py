import argparse
import src.download as dl
import sys

import yaml


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
        f = open(configPath, "r")
    except OSError:
        print("Could not read file: ", configPath)
        sys.exit()

    with f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    if not args.skip_download:
        dl.Download(data, args.verbose)
