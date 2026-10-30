import pandas as pd

from src.utility import *


def FilterListings(time):
    listings = pd.read_csv(Raw.listings[time])

    listings = listings.merge(
        team_listings, left_on="id", right_on="listing_id", how="right"
    )
    listings = listings.merge(team_areas, on="analysis_area", how="left")
    listings = listings.drop(
        columns=[
            "listing_id",
            "analysis_area",
            "Thành phố",
            "listing_url",
            "scrape_id",
            "source",
            "picture_url",
            "host_url",
            "host_profile_url",
            "host_location",
            "host_thumbnail_url",
            "host_picture_url",
            "host_has_profile_pic",
            "license",
        ]
    )
    listings.to_csv(
        Filtered.listings[time],
        index=False,
        encoding="utf-8",
    )


def FilterCalendar(time):
    calendar = pd.read_csv(Raw.calendar[time])

    calendar = calendar.merge(team_listings, on="listing_id", how="right")
    calendar = calendar.drop(columns=["analysis_area"])
    calendar.to_csv(
        Filtered.calendar[time],
        index=False,
        encoding="utf-8",
    )


def FilterReviews(time):
    reviews = pd.read_csv(Raw.reviews[time])
    reviews = reviews.merge(
        team_reviews, left_on="id", right_on="review_id", how="right"
    )
    reviews = reviews.drop(
        columns=[
            "review_id",
            "Mẫu LLM",
        ]
    )
    reviews.to_csv(
        Filtered.reviews[time],
        index=False,
        encoding="utf-8",
    )


def Filter():
    global team_listings
    global team_areas
    global team_reviews

    team_listings = pd.read_csv(Team.listings, usecols=["listing_id", "analysis_area"])
    team_areas = pd.read_csv(Team.areas, index_col=0)
    team_reviews = pd.read_csv(
        Team.reviews, usecols=["review_id", "Mẫu LLM", "Nhãn tay"], encoding="utf-8"
    )

    for i in CONFIG.snapshots:
        time = i.strftime("%Y-%m-%d")
        FilterListings(time)
        FilterReviews(time)
        FilterCalendar(time)
