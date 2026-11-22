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

    
def QAReport():
    """Tổng hợp bộ quy tắc QA + tác động số liệu → ghi reports/qa_report.csv.
    Gọi sau khi đã chạy QAListings / QAReviews / QACalendar cho tất cả snapshot.
    Không ảnh hưởng đến code QA hiện có.
    """
    import os

    times = [s.strftime("%Y-%m-%d") for s in sorted(CONFIG.snapshots)]

    # ── Đọc file đã QA ──────────────────────────────────────────────────────
    # Hỗ trợ cả 2 quy ước đặt tên: _processed-listings.csv (Processed.listings)
    # và _cleaned_listings.csv / _flagged_*.csv (tên file thực tế hiện có).
    def _load(path_dict, times, fallback_tpl=None, usecols=None):
        parts = []
        for t in times:
            p = path_dict.get(t, "")
            if not os.path.exists(p) and fallback_tpl:
                p = f"data/processed/{t}/{t}_{fallback_tpl}.csv"
            if os.path.exists(p):
                parts.append(pd.read_csv(p, usecols=usecols))
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    L = _load(Processed.listings, times, fallback_tpl="cleaned_listings")
    R = _load(Processed.reviews,  times, fallback_tpl="flagged_reviews")
    # Calendar lớn → chỉ đọc cột cần thiết
    C = _load(Processed.calendar, times, fallback_tpl="flagged_calendar",
              usecols=lambda c: c.startswith("flag_") or c in ("minimum_nights", "available"))

    # ── Hàm tiện ích ────────────────────────────────────────────────────────
    def _n(df, flag):
        """Trả về (count_flagged, total_rows)."""
        if flag not in df.columns or df.empty:
            return 0, 0
        return int(df[flag].sum()), len(df)

    def _avg(df, col, exclude_flag=None):
        """Trung bình cột `col`; loại bỏ dòng bị cờ nếu truyền exclude_flag."""
        if col not in df.columns or df.empty:
            return "N/A"
        s = pd.to_numeric(df[col], errors="coerce")
        if exclude_flag and exclude_flag in df.columns:
            s = s[~df[exclude_flag].astype(bool)]
        v = s.dropna().mean()
        return f"{v:,.2f}" if not pd.isna(v) else "N/A"

    def _avail(df, exclude_flag=None):
        """Tỷ lệ available == 't'."""
        if "available" not in df.columns or df.empty:
            return "N/A"
        s = df["available"].astype(str).str.lower()
        if exclude_flag and exclude_flag in df.columns:
            s = s[~df[exclude_flag].astype(bool)]
        return f"{s.eq('t').mean() * 100:.2f}%"

    # ── KPI trước/sau ────────────────────────────────────────────────────────
    p_all  = _avg(L, "price")
    p_ok   = _avg(L, "price",                   "flag_price_invalid")
    rev_b  = _avg(L, "estimated_revenue_l365d")
    rev_a  = _avg(L, "estimated_revenue_l365d",  "flag_any")
    mn_b   = _avg(C, "minimum_nights")
    mn_a   = _avg(C, "minimum_nights",           "flag_any")
    avb_b  = _avail(C)
    avb_a  = _avail(C, "flag_any")
    max_p  = f"{L['price'].dropna().max():,.0f}" if ("price" in L.columns and not L.empty) else "N/A"

    # ── Bảng quy tắc (tên → điều kiện → lý do → hành động) ─────────────────
    # Mỗi phần tử: (bang, flag, nhom_loi, dieu_kien, ly_do, hanh_dong, df, kpi_truoc, kpi_sau)
    RULES = [
        # ─── LISTINGS ───────────────────────────────────────────────────────
        ("listings", "flag_price_invalid",
         "Thiếu",
         "price.isna() | price <= 0",
         "Giá 0 / âm / NaN làm sai lệch doanh thu và giá trung bình.",
         "Gắn cờ flag_price_invalid = True (không xóa dữ liệu gốc).",
         L, f"{p_all} EUR/đêm (gộp cả giá 0/NaN)", f"{p_ok} EUR/đêm (loại bỏ giá 0/NaN)"),

        ("listings", "flag_price_outlier",
         "Ngoại lai",
         "price > price_max_eur  (5,000 EUR theo configs/paris.yaml)",
         "Giá cực đoan làm lệch phân phối thang đo.",
         "Gắn cờ flag_price_outlier = True.",
         L, f"Max = {max_p} EUR/đêm", "Không listing nào vượt ngưỡng 5,000 EUR/đêm"),

        ("listings", "flag_min_nights_extreme",
         "Ngoại lai",
         "minimum_nights < 1 | > 365 | isna()",
         "Vi phạm quy chuẩn lưu trú ngắn hạn Airbnb.",
         "Gắn cờ flag_min_nights_extreme = True.",
         L,
         f"TB {_avg(L, 'minimum_nights')} đêm",
         f"TB {_avg(L, 'minimum_nights', 'flag_min_nights_extreme')} đêm"),

        ("listings", "flag_invalid_coords",
         "Thiếu / Ngoại lai",
         "latitude / longitude isna()  hoặc ngoài phạm vi [-90,90] / [-180,180]",
         "Tọa độ sai chuẩn WGS84 làm lỗi bản đồ phân bố không gian.",
         "Gắn cờ flag_invalid_coords = True.",
         L, "Chứa tọa độ thiếu hoặc ngoài phạm vi", "100% tọa độ hợp lệ đưa vào phân tích bản đồ"),

        ("listings", "flag_invalid_availability",
         "Ngoại lai / Danh mục lệch",
         "availability_365 < 0 | > 365 | isna()",
         "Số ngày mở bán/năm bắt buộc nằm trong [0, 365].",
         "Gắn cờ flag_invalid_availability = True.",
         L,
         f"TB {_avg(L, 'availability_365')} ngày/năm",
         f"TB {_avg(L, 'availability_365', 'flag_invalid_availability')} ngày/năm"),

        ("listings", "flag_missing_name",
         "Thiếu",
         "name.isna() | name.strip() == ''",
         "Thiếu tên phòng không định danh được listing.",
         "Gắn cờ flag_missing_name = True.",
         L, "Có thể có listing thiếu tên", "100% listing hợp lệ có tên định danh"),

        ("listings", "flag_missing_host_id",
         "Thiếu",
         "host_id.isna() | host_id.strip() == ''",
         "Thiếu ID chủ nhà không phân loại được Pro Host (KPI Tân).",
         "Gắn cờ flag_missing_host_id = True.",
         L, "Có thể thiếu host_id", "100% listing hợp lệ có host_id"),

        ("listings", "flag_any",
         "Tổng hợp",
         "Bất kỳ cờ flag_* nào bằng True",
         "Bộ lọc tổng hợp để loại bỏ bản ghi rác khi tính KPI nghiệp vụ.",
         "Gán cờ flag_any = True.",
         L,
         f"Doanh thu ước tính năm (KPI 4): {rev_b} EUR",
         f"Doanh thu ước tính năm (KPI 4): {rev_a} EUR"),

        # ─── REVIEWS ────────────────────────────────────────────────────────
        ("reviews", "flag_html_in_comments",
         "Kiểu sai / Nhiễu",
         "comments chứa thẻ HTML  r'<[a-zA-Z/][^>]*>'",
         "Thẻ HTML gây nhiễu cho mô hình LLM phân tích khía cạnh.",
         "Gắn cờ flag_html_in_comments; bóc thẻ, lưu vào comment_clean.",
         R, "Chứa HTML thô trong cột comments", "100% văn bản sạch trong comment_clean"),

        ("reviews", "flag_empty_comments",
         "Thiếu",
         "comment_clean.strip() == ''",
         "Bình luận rỗng không có giá trị, lãng phí token LLM.",
         "Gắn cờ flag_empty_comments = True.",
         R, "Chứa bình luận trống", "100% review hợp lệ có nội dung thực tế"),

        ("reviews", "flag_missing_ids",
         "Thiếu",
         "id / listing_id / reviewer_id  bị NaN hoặc rỗng",
         "Thiếu khóa định danh, không thể JOIN review với listing.",
         "Gắn cờ flag_missing_ids = True.",
         R, "Có thể thiếu khóa định danh", "100% review có thể kết nối với listing"),

        ("reviews", "flag_duplicate_id",
         "Trùng (trong mốc)",
         "id.duplicated(keep=False)  đối với id hợp lệ",
         "Trùng lặp ID đánh giá làm thổi phồng số lượng review.",
         "Gắn cờ flag_duplicate_id = True.",
         R, "Có thể có review ID trùng lặp", "100% review ID duy nhất trong từng snapshot"),

        ("reviews", "flag_invalid_date",
         "Kiểu sai",
         "date không ép kiểu được thành datetime  format '%Y-%m-%d'",
         "Sai định dạng ngày làm gãy phân tích chuỗi thời gian.",
         "Gắn cờ flag_invalid_date = True.",
         R, "Có thể có ngày sai format", "100% timestamp hợp lệ cho chuỗi thời gian"),

        ("reviews", "flag_any",
         "Tổng hợp",
         "Bất kỳ cờ lỗi nào trong error_flags bằng True",
         "Tập mẫu sạch đưa vào phân tích khía cạnh LLM.",
         "Gán cờ flag_any = True.",
         R, "Toàn bộ reviews thô", "Reviews đạt chuẩn QA đưa vào pipeline LLM"),

        # ─── CALENDAR ───────────────────────────────────────────────────────
        ("calendar", "flag_missing",
         "Thiếu",
         "Bất kỳ cột bắt buộc nào bị NaN / rỗng",
         "Thiếu dữ liệu làm gãy chuỗi lịch quan sát 365 ngày.",
         "Gắn cờ flag_missing = True.",
         C, "Dòng lịch cần đủ 5 cột bắt buộc", "100% dòng lịch hợp lệ có đủ 5 thuộc tính"),

        ("calendar", "flag_wrong_type",
         "Kiểu sai",
         "listing_id / min_nights / max_nights không phải số nguyên hoặc date sai format",
         "Giá trị không đúng kiểu làm hỏng phép tổng hợp số học.",
         "Gắn cờ flag_wrong_type = True.",
         C, "Có thể có giá trị sai kiểu", "100% số nguyên và ngày ISO chuẩn"),

        ("calendar", "flag_outlier",
         "Ngoại lai",
         "listing_id <= 0 | min_nights <= 0 | > 365 | max_nights <= 0 | > 1,125 | max < min",
         "Mâu thuẫn logic nghiệp vụ đặt phòng.",
         "Gắn cờ flag_outlier = True.",
         C, f"TB min_nights: {mn_b} đêm", f"TB min_nights: {mn_a} đêm (loại ngoại lai)"),

        ("calendar", "flag_category_mismatch",
         "Danh mục lệch",
         "available không thuộc ['t', 'f']",
         "Trạng thái phòng bắt buộc là nhị phân t / f.",
         "Gắn cờ flag_category_mismatch = True.",
         C, f"Tỷ lệ sẵn sàng: {avb_b}", f"Tỷ lệ sẵn sàng: {avb_a} (chuẩn hóa danh mục)"),

        ("calendar", "flag_duplicate_within_snapshot",
         "Trùng (trong mốc)",
         "Trùng cặp khóa [listing_id, date] trong cùng snapshot",
         "Một phòng trong 1 ngày chỉ có đúng 1 trạng thái.",
         "Gắn cờ flag_duplicate_within_snapshot = True.",
         C, "Mỗi (listing_id, date) cần duy nhất", "100% cặp khóa duy nhất trong từng mốc"),

        ("calendar", "flag_key_overlap",
         "Trùng (giữa các mốc)",
         "Cặp [listing_id, date] xuất hiện đồng thời ở nhiều snapshot",
         "Các snapshot 3 tháng/lần; ngày tương lai giao thoa là bình thường.",
         "Gắn cờ flag_key_overlap = True  (thông tin, không phải lỗi kỹ thuật).",
         C, "Không phân biệt ngày mới và ngày giao thoa", "Nhận diện vùng đối soát liên kỳ"),

        ("calendar", "flag_conflict_across_snapshots",
         "Trùng (giữa các mốc) / Xung đột",
         "Trùng khóa nhưng khác trạng thái / số đêm giữa các snapshot",
         "Chủ nhà thay đổi chính sách đặt phòng giữa các đợt cào.",
         "Gắn cờ flag_conflict_across_snapshots = True.",
         C, "Lịch coi là dữ liệu tĩnh không đổi", "Đo lường tỷ lệ điều chỉnh chính sách của chủ nhà"),

        ("calendar", "flag_duplicate_across_snapshots",
         "Trùng (giữa các mốc) / Bản ghi tĩnh",
         "Toàn bộ bản ghi giống hệt nhau giữa các snapshot",
         "Bản ghi không thay đổi qua các chu kỳ quan sát.",
         "Gắn cờ flag_duplicate_across_snapshots = True.",
         C, "Không phân biệt dữ liệu tĩnh và động", "Tách nhóm phòng ổn định và điều chỉnh liên tục"),

        ("calendar", "flag_any",
         "Tổng hợp",
         "Bất kỳ cờ lỗi kỹ thuật nào (không tính cờ giao thoa mốc)",
         "Lọc sạch lỗi kỹ thuật trước khi tính tỷ lệ lấp đầy.",
         "Gán cờ flag_any = True.",
         C,
         f"Tỷ lệ phòng sẵn sàng: {avb_b}",
         f"Tỷ lệ phòng sẵn sàng: {avb_a}  (loại bỏ bản ghi lỗi)"),
    ]

    # ── Xuất CSV ─────────────────────────────────────────────────────────────
    rows = []
    for i, (bang, flag, nhom, dieu_kien, ly_do, hanh_dong, df, kpi_truoc, kpi_sau) in enumerate(RULES, start=1):
        n, total = _n(df, flag)
        pct = f"{n / total * 100:.2f}%" if total else "N/A"
        rows.append({
            "stt":                i,
            "bang_du_lieu":       bang,
            "ten_quy_tac":        flag,
            "nhom_loi":           nhom,
            "dieu_kien":          dieu_kien,
            "ly_do":              ly_do,
            "hanh_dong":          hanh_dong,
            "so_dong_tac_dong":   n,
            "tong_so_dong":       total,
            "ty_le_tac_dong_pct": pct,
            "kpi_truoc_qa":       kpi_truoc,
            "kpi_sau_qa":         kpi_sau,
        })

    os.makedirs("reports", exist_ok=True)
    out_path = "reports/qa_report.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[QAReport] Đã ghi {len(rows)} quy tắc → {out_path}")
    return out_path
if __name__ == "__main__":
    QAReport()
