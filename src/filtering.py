import os

import pandas as pd

from src.utility import *

LoadConfig()

team_listings = pd.read_csv(TEAM_LISTINGS, usecols=["listing_id", "analysis_area"])
team_areas = pd.read_csv(TEAM_VUNG, index_col=0)
team_reviews = pd.read_csv(
    TEAM_REVIEW, usecols=["review_id", "Mẫu LLM", "Nhãn tay"], encoding="utf-8"
)


def FilterListings(time):
    listings_path = "data/raw/" + time + "/" + time + "_listings.csv.gz"
    listings = pd.read_csv(listings_path)

    listings = listings.merge(
        team_listings, left_on="id", right_on="listing_id", how="right"
    )
    listings = listings.merge(team_areas, on="analysis_area", how="left")
    listings = listings.drop(
        columns=[
            "listing_id",
            "analysis_area",
        ]
    )
    listings.to_csv(
        "data/filtered/" + time + "/" + time + "_filtered_listings.csv",
        index=False,
        encoding="utf-8",
    )


def FilterCalendar(time):
    calendar_path = "data/raw/" + time + "/" + time + "_calendar.csv.gz"
    calendar = pd.read_csv(calendar_path)

    calendar = calendar.merge(team_listings, on="listing_id", how="right")
    calendar = calendar.drop(columns=["analysis_area"])
    calendar.to_csv(
        "data/filtered/" + time + "/" + time + "_filtered_calendar.csv",
        index=False,
        encoding="utf-8",
    )


def FilterReview(time):
    review_path = "data/raw/" + time + "/" + time + "_reviews.csv.gz"
    reviews = pd.read_csv(review_path)
    reviews = reviews.merge(
        team_reviews, left_on="id", right_on="review_id", how="right"
    )
    reviews = reviews.drop(
        columns=[
            "review_id",
        ]
    )
    reviews.to_csv(
        "data/filtered/" + time + "/" + time + "_filtered_review.csv",
        index=False,
        encoding="utf-8",
    )


for i in CONFIG.snapshots:
    time = i.strftime("%Y-%m-%d")
    os.makedirs("data/filtered" + "/" + time, exist_ok=True)

    FilterListings(time)
    FilterReview(time)
    FilterCalendar(time)
