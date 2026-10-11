import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Add config", type=str)
parser.add_argument(
    "-d", "--skip-download", help="Skip Download Data", action="store_true"
)
parser.add_argument("-l", "--skip-llm", help="Skip LLM", action="store_true")
args = parser.parse_args()

configPath = args.config

if args.skip_download:
    print("skiped download\n")
if args.skip_llm:
    print("skiped llm\n")
