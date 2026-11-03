import os
import urllib.request

import pandas as pd

from src.utility import *


def FilterSamples():
    pc_listings = pd.read_csv(Phancong.listings)
    team_listings = pc_listings.loc[
        (pc_listings["Nhóm"] == CONFIG.nhom) & (pc_listings["Lớp"] == CONFIG.lop)
    ]
    team_listings.to_csv(Team.listings)

    pc_review = pd.read_csv(Phancong.reviews)
    team_review = pc_review.loc[
        (pc_review["Nhóm"] == CONFIG.nhom) & (pc_review["Lớp"] == CONFIG.lop)
    ]
    team_review.to_csv(Team.reviews)

    pc_vung = pd.read_csv(Phancong.areas)
    team_vung = pc_vung.loc[(pc_vung["Thành phố"] == CONFIG.city)]
    team_vung.to_csv(Team.areas)


def Download(verbose):
    snapshots = [t.strftime("%Y-%m-%d") for t in CONFIG.snapshots]

    for t in snapshots:
        os.makedirs(f"data/raw/{t}", exist_ok=True)
        if verbose:
            print(
                "Downloading...\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + RAW_LISTINGS,
                "\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + RAW_CALENDAR,
                "\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + RAW_REVIEWS,
                "\n",
                BASE_URL + CONFIG.data_root + t + "/data/" + RAW_NEIGHBOURHOODS,
                "\n",
            )

        urllib.request.urlretrieve(*GetDataURL(t, RAW_LISTINGS))
        urllib.request.urlretrieve(*GetDataURL(t, RAW_CALENDAR))
        urllib.request.urlretrieve(*GetDataURL(t, RAW_REVIEWS))
        urllib.request.urlretrieve(*GetDataURL(t, RAW_NEIGHBOURHOODS))
