import os
import sys
from typing import Any

import yaml

BASE_URL = "https://data.insideairbnb.com/"
RAW_LISTINGS = "listings.csv.gz"
RAW_CALENDAR = "calendar.csv.gz"
RAW_REVIEWS = "reviews.csv.gz"
RAW_NEIGHBOURHOODS = "neighbourhoods.geojson"

LISTINGS = "listings.csv"
CALENDAR = "calendar.csv"
REVIEWS = "reviews.csv"
AREAS = "areas.csv"

LLM_BASE = "data/llm/"
ASSIGNMENT_BASE = "data/assignment/"
RAW_BASE = "data/raw/"
PROCESSED_BASE = "data/processed/"
SAMPLE_BASE = "data/samples/"
FILTERED_BASE = "data/filtered/"

# BASES = [
#     LLM_BASE,
#     ASSIGNMENT_BASE,
#     RAW_BASE,
#     PROCESSED_BASE,
#     SAMPLE_BASE,
#     FILTERED_BASE,
# ]
#
# PC_LISTINGS = ASSIGNMENT_BASE + "pc-" + LISTINGS
# PC_REVIEWS = ASSIGNMENT_BASE + "pc-" + REVIEWS
# PC = ASSIGNMENT_BASE + "pc.csv"
# PC_AREAS = ASSIGNMENT_BASE + "pc-" + AREAS
#
# TEAM_LISTINGS = ASSIGNMENT_BASE + "team-" + LISTINGS
# TEAM_REVIEWS = ASSIGNMENT_BASE + "team-" + REVIEWS
# TEAM = ASSIGNMENT_BASE + "team.csv"
# TEAM_AREAS = ASSIGNMENT_BASE + "team-" + AREAS


class Base:
    def __init__(self, base) -> None:
        self.listings: str
        self.reviews: str
        self.areas: str
        self.base = base
        os.makedirs(base, exist_ok=True)

    def Create(self, tag, type):
        self.listings = f"{self.base}{tag}-listings.{type}"
        self.reviews = f"{self.base}{tag}-reviews.{type}"
        self.areas = f"{self.base}{tag}-areas.{type}"


class BaseHasSnapshots:
    def __init__(self, base) -> None:
        self.listings = {}
        self.reviews = {}
        self.neighbourhoods = {}
        self.calendar = {}
        self.base = base
        os.makedirs(base, exist_ok=True)

    def Create(self, snapshots, tag, type):
        for snapshot in snapshots:
            time = snapshot.strftime("%Y-%m-%d")
            os.makedirs(f"{self.base}{time}", exist_ok=True)
            self.listings[time] = f"{self.base}{time}/{time}_{tag}-listings.{type}"
            self.reviews[time] = f"{self.base}{time}/{time}_{tag}-reviews.{type}"
            self.calendar[time] = f"{self.base}{time}/{time}_{tag}-calendar.{type}"
            self.neighbourhoods[time] = (
                f"{self.base}{time}/{time}_{tag}-neighbourhoods.geojson"
            )


class FreeBase:
    def __init__(self, base) -> None:
        self.files = {}
        self.base = base
        os.makedirs(base, exist_ok=True)

    def Create(self, name, tag, type):
        self.files[name] = f"{self.base}_{tag}-{name}.{type}"


Raw = BaseHasSnapshots(RAW_BASE)
Team = Base(ASSIGNMENT_BASE)
Phancong = Base(ASSIGNMENT_BASE)
Llm = FreeBase(LLM_BASE)
Filtered = BaseHasSnapshots(FILTERED_BASE)
Processed = BaseHasSnapshots(PROCESSED_BASE)
Samples = FreeBase(SAMPLE_BASE)


def GetDataURL(time, type):
    if type == RAW_NEIGHBOURHOODS:
        return (
            BASE_URL + CONFIG.data_root + time + "/visualisations/" + type,
            "data/raw/" + time + "/" + time + "_raw-" + type,
        )
    else:
        return (
            BASE_URL + CONFIG.data_root + time + "/data/" + type,
            "data/raw/" + time + "/" + time + "_raw-" + type,
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
