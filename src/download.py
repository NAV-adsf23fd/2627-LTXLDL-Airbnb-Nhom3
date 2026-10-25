import os
import urllib.request

import pandas as pd

from src.utility import *


def FilterSamples():
    os.makedirs("data/processed", exist_ok=True)

    pc_listings = pd.read_csv(PC_LISTINGS)
    team_listings = pc_listings.loc[
        (pc_listings["Nhóm"] == CONFIG.nhom) & (pc_listings["Lớp"] == CONFIG.lop)
    ]
    team_listings.to_csv(TEAM_LISTINGS)

    pc_review = pd.read_csv(PC_REVIEW)
    team_review = pc_review.loc[
        (pc_review["Nhóm"] == CONFIG.nhom) & (pc_review["Lớp"] == CONFIG.lop)
    ]
    team_review.to_csv(TEAM_REVIEW)

    pc_phancong = pd.read_csv(PC)
    team_phancong = pc_phancong.loc[
        (pc_phancong["Nhóm"] == CONFIG.nhom) & (pc_phancong["Lớp"] == CONFIG.lop)
    ]
    team_phancong.to_csv(TEAM)

    pc_vung = pd.read_csv(PC_VUNG)
    team_vung = pc_vung.loc[(pc_vung["Thành phố"] == CONFIG.city)]
    team_vung.to_csv(TEAM_VUNG)


def Download(verbose):
    data_root = CONFIG.data_root
    snapshots = [t.strftime("%Y-%m-%d") for t in CONFIG.snapshots]
    os.makedirs("data/raw", exist_ok=True)

    for t in snapshots:
        os.makedirs("data/raw/" + t, exist_ok=True)
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
            "data/raw/" + t + "/" + t + "_" + "listings.csv.gz",
        )
        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + CALENDAR,
            "data/raw/" + t + "/" + t + "_" + "calendar.csv.gz",
        )
        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + REVIEWS,
            "data/raw/" + t + "/" + t + "_" + "reviews.csv.gz",
        )
        urllib.request.urlretrieve(
            BASE_URL + data_root + t + "/" + NEIGHBOURHOODS,
            "data/raw/" + t + "/" + t + "_" + "neighbourhoods.geojson",
        )
