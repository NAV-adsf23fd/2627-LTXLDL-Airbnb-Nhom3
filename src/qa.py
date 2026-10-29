import pandas as pd


def ExportFile(file, name, time):
    file.to_csv(f"data/processed/{time}/{time}_flagged_{name}.csv")


def QAListings(time):
    listings = pd.read_csv(f"data/filtered/{time}/{time}_filtered_listings.csv.gz")
    qa_cfg = CONFIG.qa

    # ── 1. Loại bỏ bản ghi trùng lặp ─────────────────────────────────────
    # Giữ lần xuất hiện cuối cùng theo dedupe_keys (config: [id, last_scraped])
    dedupe_keys = [k for k in qa_cfg["dedupe_keys"] if k in listings.columns]
    if dedupe_keys:
        listings = listings.drop_duplicates(subset=dedupe_keys, keep="last")

    # ── 2. Làm sạch cột giá (price) ───────────────────────────────────────
    # InsideAirbnb lưu dạng "$1,234.00" – chuyển về float
    if "price" in listings.columns:
        listings["price"] = (
            listings["price"]
            .astype(str)
            .str.replace(r"[$,\s]", "", regex=True)
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
        listings["flag_price_invalid"] = (
            listings["price"].isna() | listings["price"].le(0)
        )
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

    #Xuất file kết quả
    export = listings
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
