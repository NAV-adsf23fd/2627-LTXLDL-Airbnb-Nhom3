import pandas as pd

from utility import CONFIG, Filtered


def Thai():
    pass


def Van():
    for t in CONFIG.snapshots:
        time = t.strftime("%Y-%m-%d")
        listing = pd.read_csv(Filtered.listings[time])
        review_scores = listing[
            [
                "review_scores_rating",
                "review_scores_accuracy",
                "review_scores_cleanliness",
                "review_scores_checkin",
                "review_scores_communication",
                "review_scores_location",
                "review_scores_value",
            ]
        ]


def Tan():
    pass


def Tuan():
    pass


def Thanh():
    pass
