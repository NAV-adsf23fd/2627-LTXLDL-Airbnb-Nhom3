import sys
from typing import Any

import yaml

BASE_URL = "https://data.insideairbnb.com/"
LISTINGS = "data/listings.csv.gz"
CALENDAR = "data/calendar.csv.gz"
REVIEWS = "data/reviews.csv.gz"
NEIGHBOURHOODS = "visualisations/neighbourhoods.geojson"

PC_LISTINGS = "data/samples/pc-listings.csv"
PC_REVIEW = "data/samples/pc-review.csv"
PC = "data/samples/pc.csv"
PC_VUNG = "data/samples/pc-vung.csv"

TEAM_LISTINGS = "data/processed/team-listings.csv"
TEAM_REVIEW = "data/processed/team-review.csv"
TEAM = "data/processed/team.csv"
TEAM_VUNG = "data/processed/team-vung.csv"


# class giup share giua nhieu file
class Share:
    def __str__(self) -> str:  # ham print instance
        return str(self.__dict__)


CONFIG: Any = Share()  # tranh bao loi lsp


def LoadConfig(path="configs/paris.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
            CONFIG.__dict__.clear()
            CONFIG.__dict__.update(config)
    except OSError:
        print("Could not read file: ", path)
        sys.exit()
