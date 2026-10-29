import os

import pandas as pd

from src.utility import *


def clean_percent(val):
    if pd.isna(val):
        return val  # Giữ nguyên NaN
    if isinstance(val, (int, float)):
        return float(val)  # Nếu là số sẵn thì chỉ ép về float
    # Nếu là chuỗi thì xóa % và đổi sang float
    return float(str(val).replace("%", ""))


team_listings = pd.read_csv(TEAM_LISTINGS)
areas = pd.read_csv(TEAM_VUNG)
revs = pd.read_csv(TEAM_REVIEW)


# listings
for i in CONFIG.snapshots:
    os.makedirs("data/processed/" + i.strftime("%Y-%m-%d"), exist_ok=True)
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
            "Lớp",
            "Nhóm",
            "Mã dữ liệu",
            "listing_id",
            "Unnamed: 0",
            "Unnamed: 0_x",
            "Unnamed: 0_y",
        ],
        errors="ignore",
    )
    aa["last_scraped"] = pd.to_datetime(aa["last_scraped"])
    aa["host_since"] = pd.to_datetime(aa["host_since"])
    aa["host_response_rate"] = aa["host_response_rate"].apply(clean_percent)
    aa["host_response_rate"] = aa["host_response_rate"] / 100
    aa["host_acceptance_rate"] = aa["host_acceptance_rate"].apply(clean_percent)
    aa["host_acceptance_rate"] = aa["host_acceptance_rate"] / 100
    aa["bathrooms"] = aa["bathrooms_text"].str.extract(r"(\d+\.?\d*)").astype(float)
    aa["bathrooms_type"] = aa["bathrooms_text"].str.extract(r"([A-Za-z]+)")
    aa["calendar_last_scraped"] = pd.to_datetime(aa["calendar_last_scraped"])
    aa["first_review"] = pd.to_datetime(aa["first_review"])
    aa["last_review"] = pd.to_datetime(aa["last_review"])
    aa["host_is_superhost"] = aa["host_is_superhost"].map({"t": True, "f": False})
    aa["host_has_profile_pic"] = aa["host_has_profile_pic"].map({"t": True, "f": False})
    aa["host_identity_verified"] = aa["host_identity_verified"].map(
        {"t": True, "f": False}
    )
    aa["instant_bookable"] = aa["instant_bookable"].map({"t": True, "f": False})
    aa["has_availability"] = aa["has_availability"].map({"t": True, "f": False})
    # TODO
    # QA: loại bỏ duplicate theo dedupe_keys từ config
    aa = aa.drop_duplicates(subset=CONFIG.qa["dedupe_keys"], keep="first")
    # QA: cap minimum_nights theo min_nights_cap
    aa["minimum_nights"] = aa["minimum_nights"].clip(upper=CONFIG.qa["min_nights_cap"])
    aa.to_csv(
        "data/processed/" + i.strftime("%Y-%m-%d") + "/" + "cleaned_listings.csv",
        index=False,
    )

    # calendar
    tmp_calendar = (
        "data/raw/"
        + i.strftime("%Y-%m-%d")
        + "/"
        + i.strftime("%Y-%m-%d")
        + "_calendar.csv.gz"
    )
    calendar = pd.read_csv(tmp_calendar)
    b = calendar.merge(team_listings, on="listing_id", how="right")
    bb = b.drop(
        columns=["Lớp", "Nhóm", "Mã dữ liệu", "analysis_area", "Unnamed: 0"],
        errors="ignore",
    )
    bb["date"] = pd.to_datetime(bb["date"], format="%Y-%m-%d")
    bb["available"] = bb["available"].map({"t": True, "f": False})
    # TODO
    # QA: loại bỏ duplicate (listing_id + date)
    bb = bb.drop_duplicates(subset=["listing_id", "date"], keep="first")
    bb.to_csv(
        "data/processed/" + i.strftime("%Y-%m-%d") + "/" + "cleaned_calendar.csv",
        index=False,
    )

    # reviews
    tmp_reviews = (
        "data/raw/"
        + i.strftime("%Y-%m-%d")
        + "/"
        + i.strftime("%Y-%m-%d")
        + "_reviews.csv.gz"
    )
    reviews = pd.read_csv(tmp_reviews)
    c = reviews.merge(revs, left_on="id", right_on="review_id", how="right")
    c = c.rename(columns={"listing_id_x": "listing_id"})
    c["date"] = pd.to_datetime(c["date"], format="%Y-%m-%d")
    cc = c.drop(
        columns=[
            "Lớp",
            "Nhóm",
            "Mã dữ liệu",
            "listing_id_y",
            "Unnamed: 0",
            "review_id",
        ],
        errors="ignore",
    )
    # TODO
    # QA: loại bỏ reviews có comments rỗng hoặc null
    cc = cc[cc["comments"].notna() & (cc["comments"].str.strip() != "")]

    d = cc.copy()
    d = d[d["Mẫu LLM"] == "x"]
    dd = d.drop(columns=["Mẫu LLM", "Nhãn tay"])
    # kết thúc mỗi vòng for sẽ xuất 1 file csv vào folder processed chính là dữ liệu sạch
    # TODO
    dd.to_csv(
        "data/processed/" + i.strftime("%Y-%m-%d") + "/" + "cleaned_reviews_LLM.csv",
        index=False,
    )

    e = cc.copy()
    e = e[e["Nhãn tay"] == "x"]
    ee = e.drop(columns=["Mẫu LLM", "Nhãn tay"])
    # TODO
    ee.to_csv(
        "data/processed/"
        + i.strftime("%Y-%m-%d")
        + "/"
        + "cleaned_reviews_nhantay.csv",
        index=False,
    )

    fin = cc.drop(columns=["Mẫu LLM", "Nhãn tay"])
    fin.to_csv(
        "data/processed/" + i.strftime("%Y-%m-%d") + "/" + "cleaned_reviews.csv",
        index=False,
    )
