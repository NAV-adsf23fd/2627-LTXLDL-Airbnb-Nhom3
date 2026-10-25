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
    snapshots = [t.strftime("%Y-%m-%d") for t in CONFIG.snapshots]
    os.makedirs("data/raw", exist_ok=True)

    for t in snapshots:
        os.makedirs("data/raw/" + t, exist_ok=True)
        if verbose:
            print(
                "Downloading...\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + LISTINGS,
                "\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + CALENDAR,
                "\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + REVIEWS,
                "\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + NEIGHBOURHOODS,
                "\n",
            )

        urllib.request.urlretrieve(*GetDataURL(t, LISTINGS))
        urllib.request.urlretrieve(*GetDataURL(t, CALENDAR))
        urllib.request.urlretrieve(*GetDataURL(t, REVIEWS))
        urllib.request.urlretrieve(*GetDataURL(t, NEIGHBOURHOODS))
