import html
from typing import cast

import numpy as np
import pandas as pd

from src.utility import CONFIG, Filtered, Processed


def QAListings(time):
    listings = pd.read_csv(Filtered.listings[time])
    qa_cfg = CONFIG.qa

    listings["host_is_superhost"] = listings["host_is_superhost"] == "t"
    listings["host_identity_verified"] = listings["host_identity_verified"] == "t"
    listings["instant_bookable"] = listings["instant_bookable"] == "t"

    # ── 1. Loại bỏ bản ghi trùng lặp ─────────────────────────────────────
    # Giữ lần xuất hiện cuối cùng theo dedupe_keys (config: [id, last_scraped])
    dedupe_keys = [k for k in qa_cfg["dedupe_keys"] if k in listings.columns]
    if dedupe_keys:
        listings = listings.drop_duplicates(subset=dedupe_keys, keep="last")

    # ── 2. Làm sạch cột giá (price) ───────────────────────────────────────
    # InsideAirbnb lưu dạng "$1,234.00" – chuyển về float
    if "price" in listings.columns:
        listings["price"] = (
            listings["price"].astype(str).str.replace(r"[$,\s]", "", regex=True)
        )
        listings["price"] = pd.to_numeric(listings["price"], errors="coerce")

    # ── 3. Ép kiểu các cột số thường gặp ──────────────────────────────────
    numeric_cols = [
        "minimum_nights",
        "maximum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "calculated_host_listings_count",
        "availability_365",
        "accommodates",
        "bathrooms",
        "bedrooms",
        "beds",
        "latitude",
        "longitude",
    ]
    for col in numeric_cols:
        if col in listings.columns:
            listings[col] = pd.to_numeric(listings[col], errors="coerce")

    # ── 4. Gán cờ QA ──────────────────────────────────────────────────────

    # 4a. Giá âm, bằng 0 hoặc thiếu(NaN) (flag_price_invalid)
    if "price" in listings.columns:
        listings["flag_price_invalid"] = listings["price"].isna() | listings[
            "price"
        ].le(0)
        # 4b. Giá vượt ngưỡng ngoại lai (config: price_max_eur) (flag_price_outlier)
        price_max = qa_cfg.get("price_max_eur")
        if price_max is not None:
            listings["flag_price_outlier"] = listings["price"].gt(price_max)
        else:
            listings["flag_price_outlier"] = False
    else:
        listings["flag_price_invalid"] = False
        listings["flag_price_outlier"] = False

    # 4c. minimum_nights vượt ngưỡng (config: min_nights_cap = 365) (flag_min_night_extreme)
    min_nights_cap = qa_cfg.get("min_nights_cap", 365)
    if "minimum_nights" in listings.columns:
        listings["flag_min_nights_extreme"] = (
            listings["minimum_nights"].isna()
            | listings["minimum_nights"].lt(1)
            | listings["minimum_nights"].gt(min_nights_cap)
        )
    else:
        listings["flag_min_nights_extreme"] = False

    # 4d. Toạ độ địa lý nằm ngoài phạm vi hợp lệ (flag_invalid_coords)
    if "latitude" in listings.columns and "longitude" in listings.columns:
        listings["flag_invalid_coords"] = (
            listings["latitude"].isna()
            | listings["longitude"].isna()
            | listings["latitude"].abs().gt(90)
            | listings["longitude"].abs().gt(180)
        )
    else:
        listings["flag_invalid_coords"] = False

    # 4e. availability_365 nằm ngoài [0, 365] (flag_invalid_availability)
    if "availability_365" in listings.columns:
        listings["flag_invalid_availability"] = (
            listings["availability_365"].isna()
            | listings["availability_365"].lt(0)
            | listings["availability_365"].gt(365)
        )
    else:
        listings["flag_invalid_availability"] = False

    # 4f. Thiếu trường bắt buộc: name, host_id (flag_missing_name/host_id)
    for required_col in ["name", "host_id"]:
        flag_col = f"flag_missing_{required_col}"
        if required_col in listings.columns:
            listings[flag_col] = listings[required_col].isna() | (
                listings[required_col].astype(str).str.strip() == ""
            )
        else:
            listings[flag_col] = False

    # 4g. Cờ tổng hợp: True nếu bất kỳ cờ nào bật (flag_any)
    flag_cols = [c for c in listings.columns if c.startswith("flag_")]
    listings["flag_any"] = listings[flag_cols].any(axis=1)

    # Xuất file kết quả
    listings.to_csv(Processed.listings[time], index=False)


def QAReviews(time):
    reviews = pd.read_csv(Filtered.reviews[time])

    comments_raw = reviews["comments"].fillna("").astype(str).map(html.unescape)

    tag_regex = r"<[a-zA-Z/][^>]*>"
    br_regex = r"(?i)<br\s*/?>"

    reviews["flag_html_in_comments"] = comments_raw.str.contains(tag_regex, regex=True)
    reviews["comment_clean"] = (
        comments_raw.str.replace(br_regex, " ", regex=True)
        .str.replace(tag_regex, "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    reviews["flag_empty_comments"] = reviews["comment_clean"].eq("")

    # ── 2. Kiểm tra thiếu khóa & Trùng lặp ID ──────────────────────────
    def is_blank(s):
        return s.isna() | s.astype(str).str.strip().eq("")

    reviews["flag_missing_ids"] = (
        is_blank(reviews["id"])
        | is_blank(reviews["listing_id"])
        | is_blank(reviews["reviewer_id"])
    )
    id_valid = ~is_blank(reviews["id"])
    reviews["flag_duplicate_id"] = reviews["id"].duplicated(keep=False) & id_valid

    # ── 3. Kiểm tra định dạng ngày hợp lệ ──────────────────────────────
    if "date" in reviews.columns:
        reviews["flag_invalid_date"] = pd.to_datetime(
            reviews["date"], format="%Y-%m-%d", errors="coerce"
        ).isna()
    else:
        reviews["flag_invalid_date"] = True

    # ── 4. Tạo cờ tổng hợp lỗi (flag_any) ───────────────────────────────
    error_flags = [
        "flag_empty_comments",
        "flag_missing_ids",
        "flag_duplicate_id",
        "flag_invalid_date",
    ]
    reviews["flag_any"] = reviews[error_flags].any(axis=1)

    reviews.to_csv(Processed.reviews[time], index=False)


def QACalendar(time):
    calendar = pd.read_csv(Filtered.calendar[time])

    calendar["available"] = calendar["available"] == "t"

    qa_cfg = CONFIG.qa
    required_columns = [
        "listing_id",
        "date",
        "available",
        "minimum_nights",
        "maximum_nights",
    ]
    missing_columns = set(required_columns) - set(calendar.columns)
    if missing_columns:
        raise ValueError(
            f"Calendar for {time} is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    minimum_nights_cap = qa_cfg.get("min_nights_cap", 365)
    maximum_nights_cap = qa_cfg.get("max_nights_cap", 1125)

    # 1. Đánh dấu giá trị thiếu
    missing_values = calendar[required_columns].isna()
    for column in required_columns:
        if pd.api.types.is_object_dtype(
            calendar[column].dtype
        ) or pd.api.types.is_string_dtype(calendar[column].dtype):
            missing_values[column] |= (
                calendar[column].astype("string").str.strip().eq("").fillna(False)
            )
    calendar["flag_missing"] = missing_values.any(axis=1)

    # 2. Kiểm tra kiểu dữ liệu
    listing_ids = cast(
        pd.Series, pd.to_numeric(calendar["listing_id"], errors="coerce")
    )
    minimum_nights = cast(
        pd.Series, pd.to_numeric(calendar["minimum_nights"], errors="coerce")
    )
    maximum_nights = cast(
        pd.Series, pd.to_numeric(calendar["maximum_nights"], errors="coerce")
    )
    dates = pd.to_datetime(calendar["date"], format="%Y-%m-%d", errors="coerce")

    calendar["flag_wrong_type"] = (
        (calendar["listing_id"].notna() & listing_ids.isna())
        | (listing_ids.notna() & listing_ids.mod(1).ne(0))
        | (calendar["minimum_nights"].notna() & minimum_nights.isna())
        | (minimum_nights.notna() & minimum_nights.mod(1).ne(0))
        | (calendar["maximum_nights"].notna() & maximum_nights.isna())
        | (maximum_nights.notna() & maximum_nights.mod(1).ne(0))
        | (calendar["date"].notna() & dates.isna())
    )

    # 3. Đánh dấu giá trị ngoại lai
    calendar["flag_outlier"] = (
        (listing_ids.notna() & listing_ids.le(0))
        | (minimum_nights.notna() & minimum_nights.le(0))
        | (minimum_nights.notna() & minimum_nights.gt(minimum_nights_cap))
        | (maximum_nights.notna() & maximum_nights.le(0))
        | (maximum_nights.notna() & maximum_nights.gt(maximum_nights_cap))
        | (
            minimum_nights.notna()
            & maximum_nights.notna()
            & maximum_nights.lt(minimum_nights)
        )
    )

    # 4. Kiểm tra danh mục available chỉ nhận "t" hoặc "f"
    availability = calendar["available"].astype("string").str.strip().str.lower()
    calendar["flag_category_mismatch"] = calendar[
        "available"
    ].notna() & ~availability.isin(["t", "f"])

    # 5. Đánh dấu trùng trong snapshot theo khóa listing_id + date
    valid_keys = (
        listing_ids.notna()
        & listing_ids.gt(0)
        & listing_ids.mod(1).eq(0)
        & dates.notna()
    )
    normalized_keys = pd.DataFrame(
        {
            "listing_id": listing_ids.loc[valid_keys],
            "date": dates.loc[valid_keys].dt.strftime("%Y-%m-%d"),
        },
        index=calendar.index[valid_keys],
    )
    calendar["flag_duplicate_within_snapshot"] = False
    calendar.loc[normalized_keys.index, "flag_duplicate_within_snapshot"] = (
        normalized_keys.duplicated(keep=False).to_numpy()
    )

    # 6. So sánh các trường calendar với những snapshot còn lại
    def normalized_hashes(frame):
        normalized = frame[required_columns].copy()
        for column in ("listing_id", "minimum_nights", "maximum_nights"):
            numeric_values = cast(
                pd.Series, pd.to_numeric(normalized[column], errors="coerce")
            )
            normalized[column] = numeric_values.where(
                numeric_values.mod(1).eq(0)
            ).astype("Int64")
        normalized["date"] = (
            pd.to_datetime(normalized["date"], format="%Y-%m-%d", errors="coerce")
            .dt.strftime("%Y-%m-%d")
            .astype("string")
        )
        normalized["available"] = (
            normalized["available"].astype("string").str.strip().str.lower()
        )
        key_hash = pd.util.hash_pandas_object(  # type: ignore
            normalized[["listing_id", "date"]], index=False
        ).to_numpy()
        row_hash = pd.util.hash_pandas_object(normalized, index=False).to_numpy()  # type: ignore
        return key_hash, row_hash

    cur_key, cur_row = normalized_hashes(calendar)
    other_times = [
        snapshot.strftime("%Y-%m-%d")
        if hasattr(snapshot, "strftime")
        else str(snapshot)
        for snapshot in CONFIG.snapshots
    ]
    other_times = [snapshot for snapshot in other_times if snapshot != str(time)]

    key_overlap = np.zeros(len(calendar), dtype=bool)
    conflict = np.zeros(len(calendar), dtype=bool)
    identical = np.zeros(len(calendar), dtype=bool)
    for other_time in other_times:
        other_path = Filtered.calendar[other_time]
        other = pd.read_csv(other_path, usecols=required_columns)
        other_missing_columns = set(required_columns) - set(other.columns)
        if other_missing_columns:
            raise ValueError(
                f"Calendar for {other_time} is missing required columns: "
                f"{sorted(other_missing_columns)}"
            )

        other_key, other_row = normalized_hashes(other)
        del other
        same_key = np.isin(cur_key, other_key)
        same_row = np.isin(cur_row, other_row)
        key_overlap |= same_key
        conflict |= same_key & ~same_row
        identical |= same_row
        del other_key, other_row, same_key, same_row

    calendar["flag_key_overlap"] = key_overlap
    calendar["flag_conflict_across_snapshots"] = conflict
    calendar["flag_duplicate_across_snapshots"] = identical

    # 7. Cờ tổng hợp
    info_flags = {
        "flag_key_overlap",
        "flag_conflict_across_snapshots",
        "flag_duplicate_across_snapshots",
    }
    flag_columns = [
        column
        for column in calendar
        if column.startswith("flag_") and column != "flag_any"
    ]
    error_flags = [column for column in flag_columns if column not in info_flags]
    calendar["flag_any"] = calendar[error_flags].any(axis=1)

    # END_TOO:

    calendar.to_csv(Processed.calendar[time], index=False)
