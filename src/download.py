import os
import urllib.request
import pandas as pd

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


def FilterSamples(configs):
    os.makedirs("data/processed", exist_ok=True)

    pc_listings = pd.read_csv(PC_LISTINGS)
    team_listings = pc_listings.loc[
        (pc_listings["Nhóm"] == configs["nhom"])
        & (pc_listings["Lớp"] == configs["lop"])
    ]
    team_listings.to_csv(TEAM_LISTINGS)

    pc_review = pd.read_csv(PC_REVIEW)
    team_review = pc_review.loc[
        (pc_review["Nhóm"] == configs["nhom"]) & (pc_review["Lớp"] == configs["lop"])
    ]
    team_review.to_csv(TEAM_REVIEW)

    pc_phancong = pd.read_csv(PC)
    team_phancong = pc_phancong.loc[
        (pc_phancong["Nhóm"] == configs["nhom"])
        & (pc_phancong["Lớp"] == configs["lop"])
    ]
    team_phancong.to_csv(TEAM)

    pc_vung = pd.read_csv(PC_VUNG)
    team_vung = pc_vung.loc[(pc_vung["Thành phố"] == configs["city"])]
    team_vung.to_csv(TEAM_VUNG)


def Download(config, verbose):
    data_root = config["data_root"]
    snapshots = [t.strftime("%Y-%m-%d") for t in config["snapshots"]]
    os.makedirs("data/raw", exist_ok=True)

    for t in snapshots:
        if verbose:
            print(
                "Downloading...\n",
                BASE_URL + data_root + t + "/" + LISTINGS,
                "\n",
                BASE_URL + data_root + t + "/" + CALENDAR,
                "\n",
                BASE_URL + data_root + t + "/" + REVIEWS,
                "\n",
                BASE_URL + data_root + t + "/" + NEIGHBOURHOODS,
                "\n",
            )

        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + LISTINGS,
            "data/raw/" + t + "_" + "listings.csv.gz",
        )
        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + CALENDAR,
            "data/raw/" + t + "_" + "calendar.csv.gz",
        )
        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + REVIEWS,
            "data/raw/" + t + "_" + "reviews.csv.gz",
        )
        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + NEIGHBOURHOODS,
            "data/raw/" + t + "_" + "neighbourhoods.csv.gz",
        )
