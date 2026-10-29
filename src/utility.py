import sys
from typing import Any

import pandas as pd
from pandas.errors import AttributeConflictWarning
import yaml

BASE_URL = "https://data.insideairbnb.com/"
LISTINGS = "listings.csv.gz"
CALENDAR = "calendar.csv.gz"
REVIEWS = "reviews.csv.gz"
NEIGHBOURHOODS = "neighbourhoods.geojson"

PC_LISTINGS = "data/phancong/pc-listings.csv"
PC_REVIEW = "data/phancong/pc-review.csv"
PC = "data/phancong/pc.csv"
PC_VUNG = "data/phancong/pc-vung.csv"

TEAM_LISTINGS = "data/processed/team-listings.csv"
TEAM_REVIEW = "data/processed/team-review.csv"
TEAM = "data/processed/team.csv"
TEAM_VUNG = "data/processed/team-vung.csv"


def GetDataURL(time, type):
    if type == NEIGHBOURHOODS:
        return (
            BASE_URL + CONFIG.data_root + time + "/visualisations/" + type,
            "data/raw/" + time + "/" + time + "_" + type,
        )
    else:
        return (
            BASE_URL + CONFIG.data_root + time + "/data/" + type,
            "data/raw/" + time + "/" + time + "_" + type,
        )


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


def GetComment():
    merged_review = None
    review_list = []
    # test = pd.read_csv("data/raw/2025-12-13/2025-12-13_" + REVIEWS).set_index("id")
    # print(test["comments"].head())
    team_rv = pd.read_csv(TEAM_REVIEW)

    for t in CONFIG.snapshots:
        time = t.strftime("%Y-%m-%d")
        path = "data/raw/" + time + "/" + time + "_" + REVIEWS
        review = pd.read_csv(path).set_index("id")
        review_list.append(review["comments"])
        merged_review = pd.concat(review_list, axis=0, ignore_index=False)

    assert merged_review is not None, "merged_review is empty"
    merged_review.to_csv("data/processed/reviews.csv")
    print(merged_review.iloc[[0, 5001, 10001, 15001]])
