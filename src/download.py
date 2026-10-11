import csv
import urllib.request
import datetime

BASE_URL = "https://data.insideairbnb.com/"
LISTINGS = "data/listings.csv.gz"
CALENDAR = "data/calendar.csv.gz"
REVIEWS = "data/reviews.csv.gz"
NEIGHBOURHOODS = "visualisations/neighbourhoods.geojson"


def Download(data, verbose):
    data_root = data["data_root"]
    snapshots = [t.strftime("%Y-%m-%d") for t in data["snapshots"]]
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

        # urllib.request.urlretrieve(
        #     BASE_URL + data_root + t + "/" + LISTINGS,
        #     "data/raw/" + t + "_" + "listings.csv.gz",
        # )
        # urllib.request.urlretrieve(
        #     BASE_URL + data_root + t + "/" + CALENDAR,
        #     "data/raw/" + t + "_" + "calendar.csv.gz",
        # )
        # urllib.request.urlretrieve(
        #     BASE_URL + data_root + t + "/" + REVIEWS,
        #     "data/raw/" + t + "_" + "reviews.csv.gz",
        # )
        # urllib.request.urlretrieve(
        #     BASE_URL + data_root + t + "/" + NEIGHBOURHOODS,
        #     "data/raw/" + t + "_" + "neighbourhoods.csv.gz",
        # )
