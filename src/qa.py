import pandas as pd


def ExportFile(file, name, time):
    file.to_csv(f"data/processed/{time}/{time}_flagged_{name}.csv")


def QAListings(time):
    listings = pd.read_csv(f"data/filtered/{time}/{time}_filtered_listings.csv.gz")

    # TODO: chỉ được viết vào đây
    # ->

    # END_TOO:

    export = ...  # Điền vào đây tên dữ liệu cần lưu

    ExportFile(export, "listings", time)


def QAReview(time):
    reviews = pd.read_csv(f"data/filtered/{time}/{time}_filtered_reviews.csv.gz")

    # TODO: chỉ được viết vào đây
    # ->

    # END_TOO:

    export = ...  # Điền vào đây tên dữ liệu cần lưu

    ExportFile(export, "reviews", time)


def QACalendar(time):
    calendar = pd.read_csv(f"data/filtered/{time}/{time}_filtered_calendar.csv.gz")

    # TODO: chỉ được viết vào đây
    # ->

    # END_TOO:

    export = ...  # Điền vào đây tên dữ liệu cần lưu

    ExportFile(export, "calendar", time)
