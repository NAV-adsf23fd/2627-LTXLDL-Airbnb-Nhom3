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
    calendar = pd.read_csv(f"data/filtered/{time}/{time}_filtered_calendar.csv")

    import numpy as np
    import os

    from src.utility import CONFIG, LoadConfig

    if not hasattr(CONFIG, "snapshots"):
        LoadConfig()

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
    listing_ids = pd.to_numeric(calendar["listing_id"], errors="coerce")
    minimum_nights = pd.to_numeric(calendar["minimum_nights"], errors="coerce")
    maximum_nights = pd.to_numeric(calendar["maximum_nights"], errors="coerce")
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
    calendar["flag_category_mismatch"] = (
        calendar["available"].notna() & ~availability.isin(["t", "f"])
    )

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
            numeric_values = pd.to_numeric(normalized[column], errors="coerce")
            normalized[column] = numeric_values.where(
                numeric_values.mod(1).eq(0)
            ).astype("Int64")
        normalized["date"] = (
            pd.to_datetime(
                normalized["date"], format="%Y-%m-%d", errors="coerce"
            )
            .dt.strftime("%Y-%m-%d")
            .astype("string")
        )
        normalized["available"] = (
            normalized["available"].astype("string").str.strip().str.lower()
        )
        key_hash = pd.util.hash_pandas_object(
            normalized[["listing_id", "date"]], index=False
        ).to_numpy()
        row_hash = pd.util.hash_pandas_object(
            normalized, index=False
        ).to_numpy()
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
        other_path = (
            f"data/filtered/{other_time}/{other_time}_filtered_calendar.csv"
        )
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

    export = calendar
    os.makedirs(os.path.join("data", "processed", time), exist_ok=True)

    ExportFile(export, "calendar", time)
