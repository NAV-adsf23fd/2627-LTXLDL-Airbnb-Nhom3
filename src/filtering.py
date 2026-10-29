import os

import pandas as pd

from src.utility import *

LoadConfig()

team_listings = pd.read_csv(TEAM_LISTINGS, usecols=["listing_id", "analysis_area"])
areas = pd.read_csv(TEAM_VUNG, index_col=0)
revs = pd.read_csv(
    TEAM_REVIEW, usecols=["review_id", "Mẫu LLM", "Nhãn tay"], encoding="utf-8"
)

for i in CONFIG.snapshots:
    os.makedirs("data/filtered" + "/" + i.strftime("%Y-%m-%d"), exist_ok=True)
    tmp_listing = (
        "data/raw/"
        + i.strftime("%Y-%m-%d")
        + "/"
        + i.strftime("%Y-%m-%d")
        + "_listings.csv.gz"
    )
    listings = pd.read_csv(tmp_listing)
    a = listings.merge(team_listings, left_on="id", right_on="listing_id", how="right")
    aa = a.merge(areas, on="analysis_area", how="left")
    aa = aa.drop(
        columns=[
            "listing_id",
            "analysis_area",
        ]
    )
    aa.to_csv(
        "data/filtered/" + i.strftime("%Y-%m-%d") + "/" + "filtered_listings.csv",
        index=False,
        encoding="utf-8",
    )

    tmp_calendar = (
        "data/raw/"
        + i.strftime("%Y-%m-%d")
        + "/"
        + i.strftime("%Y-%m-%d")
        + "_calendar.csv.gz"
    )
    calendar = pd.read_csv(tmp_calendar)
    b = calendar.merge(team_listings, on="listing_id", how="right")
    bb = b.drop(columns=["analysis_area"])
    bb.to_csv(
        "data/filtered/" + i.strftime("%Y-%m-%d") + "/" + "filtered_calendar.csv",
        index=False,
        encoding="utf-8",
    )

    tmp_reviews = (
        "data/raw/"
        + i.strftime("%Y-%m-%d")
        + "/"
        + i.strftime("%Y-%m-%d")
        + "_reviews.csv.gz"
    )
    reviews = pd.read_csv(tmp_reviews)
    c = reviews.merge(revs, left_on="id", right_on="review_id", how="right")
    cc = c.drop(
        columns=[
            "review_id",
        ]
    )
    cc.to_csv(
        "data/filtered/" + i.strftime("%Y-%m-%d") + "/" + "filtered_review.csv",
        index=False,
        encoding="utf-8",
    )
