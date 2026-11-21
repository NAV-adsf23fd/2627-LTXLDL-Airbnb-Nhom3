import numpy as np
import pandas as pd
import os 
from src.utility import *
import json


os.makedirs("data/processed/kpi", exist_ok=True)

from pathlib import Path






def Thai(time):

    # ── 1. Xác định 4 snapshot (12 tháng qua) ─────────────────────────────
    snapshots = sorted(CONFIG.snapshots)          # sắp xếp tăng dần theo ngày
    snapshot_strs = [s.strftime("%Y-%m-%d") for s in snapshots]

    # ── 2. Đọc và gộp dữ liệu từ 4 folder trong processed ─────────────────
    frames = []
    for time in snapshot_strs:
        path = f"data/processed/{time}/{time}_processed-listings.csv"
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, usecols=["estimated_revenue_l365d"])
        df["snapshot"] = time
        frames.append(df)

    if not frames:
        return None

    all_listings = pd.concat(frames, ignore_index=True)

    # ── 3. Tính trung bình estimated_revenue_l365d ─────────────────────────
    # Lấy tất cả listing có dữ liệu (không NaN), kể cả revenue = 0
    valid = all_listings["estimated_revenue_l365d"].dropna()
    estimated_annual_revenue = valid.mean()

    # ── 4. Tạo bảng KPI và xuất ra file CSV trong processed ─────────────────
    summary = (
        all_listings.dropna(subset=["estimated_revenue_l365d"])
        .groupby("snapshot")["estimated_revenue_l365d"]
        .agg(
            so_listing="count",
            trung_binh="mean",
            trung_vi="median"
        )
        .round(2)
        .reset_index()
    )

    overall_row = pd.DataFrame([{
        "snapshot": "Toàn bộ (12 tháng)",
        "so_listing": len(valid),
        "trung_binh": round(estimated_annual_revenue, 2),
        "trung_vi": round(valid.median(), 2)
    }])
    kpi_df = pd.concat([summary, overall_row], ignore_index=True)
    kpi_df["kpi_name"] = "Estimated Annual Revenue"

    # Lưu file CSV vào data/processed/
    output_path = "data/processed/kpi/kpi_total_price.csv"
    kpi_df.to_csv(output_path, index=False, encoding="utf-8-sig")


def Van():
    pass


def Tan(time):
    """
    Phân tích mức độ chuyên nghiệp hóa (Pro Host) của thị trường lưu trú ngắn hạn
    Bản có đơn vị đầy đủ cho các bảng và biểu đồ.
    """
    # ============================================================
    # 1. THAM SỐ
    # ============================================================
    CSV_PATH = Processed.listings[time]
    PRO_HOST_THRESHOLD = CONFIG.kpi["pro_host_threashold"]                     # > 3 listing = Pro Host
    CURRENCY = CONFIG.currency
    TIER_BINS = CONFIG.kpi["tier_bins"]
    TIER_LABELS = CONFIG.kpi["tier_labels"]
    TIER_NAMES = CONFIG.kpi["tier_names"]
    WINSOR_Q = CONFIG.kpi["winsor_q"]             # cắt đuôi doanh thu ở phân vị 99


    # ============================================================
    # 2. ĐỌC & CHUẨN BỊ DỮ LIỆU
    # ============================================================
    K = "calculated_host_listings_count"
    cols = ["id", K, "estimated_revenue_l365d", "estimated_occupancy_l365d"]
    df = pd.read_csv(CSV_PATH, usecols=cols).dropna(subset=[K]).copy()

    df["is_pro"] = df[K] > PRO_HOST_THRESHOLD
    df["tier"] = pd.cut(df[K], TIER_BINS, labels=TIER_LABELS)

    # Trọng số 1/k: chủ nhà có k listing xuất hiện ~k lần trong mẫu theo listing,
    # nên gán mỗi listing trọng số 1/k để quy về "đơn vị = chủ nhà".
    df["host_w"] = 1 / df[K]

    # Doanh thu có giá trị cực đoan -> cắt đuôi (winsorize) để không làm lệch tỷ trọng
    rev_cap = df["estimated_revenue_l365d"].quantile(WINSOR_Q)
    df["rev_w"] = df["estimated_revenue_l365d"].clip(upper=rev_cap)

    # ============================================================
    # 3. TÍNH KPI
    # ============================================================
    n = len(df)
    pro = df[df.is_pro]

    share_listing = df.is_pro.mean() * 100
    share_host = pro.host_w.sum() / df.host_w.sum() * 100
    share_rev = pro.rev_w.sum() / df.rev_w.sum() * 100
    share_nights = pro.estimated_occupancy_l365d.sum() / df.estimated_occupancy_l365d.sum() * 100
    avg_pro_portfolio = len(pro) / pro.host_w.sum()      # số listing TB của 1 Pro Host

    # ---------- Bảng 1: KPI tổng hợp ----------
    kpi = pd.DataFrame([
        ("Tổng số listing phân tích", n, "listing"),
        ("Số listing của Pro Host", int(df.is_pro.sum()), "listing"),
        ("Pro Host Share – theo listing", round(share_listing, 2), "%"),
        ("Pro Host Share – theo chủ nhà (ước tính)", round(share_host, 2), "%"),
        ("Thị phần doanh thu của Pro Host", round(share_rev, 2), "%"),
        ("Thị phần số đêm có khách của Pro Host", round(share_nights, 2), "%"),
        ("Quy mô trung bình của 1 Pro Host", round(avg_pro_portfolio, 1), "listing / chủ nhà"),
        (f"Ngưỡng cắt đuôi doanh thu (P{int(WINSOR_Q*100)})", round(rev_cap), f"{CURRENCY} / năm"),
    ], columns=["Chỉ số", "Giá trị", "Đơn vị"])
    # Định dạng cột "Giá trị": số đếm hiển thị số nguyên, tỷ lệ hiển thị 2 chữ số thập phân
    kpi["Giá trị"] = [f"{v:,.0f}" if float(v).is_integer() and u != "%" and "chủ nhà" not in u
                    else f"{v:,.2f}" if u == "%" else f"{v:,.1f}"
                    for v, u in zip(kpi["Giá trị"], kpi["Đơn vị"])]

    # ---------- Bảng 2: theo nhóm quy mô ----------
    g = df.groupby("tier", observed=False).agg(
        listings=("id", "size"), host_w=("host_w", "sum"),
        nights=("estimated_occupancy_l365d", "sum"), revenue=("rev_w", "sum"))
    tier = pd.DataFrame({
        "Nhóm (listing / chủ nhà)": TIER_LABELS,
        "Tên nhóm": TIER_NAMES,
        "Số listing (listing)": g.listings.values,
        "Tỷ trọng listing (%)": (g.listings / g.listings.sum() * 100).round(1).values,
        "Tỷ trọng chủ nhà – ước tính (%)": (g.host_w / g.host_w.sum() * 100).round(2).values,
        "Số đêm có khách (đêm / năm)": g.nights.round(0).astype(int).values,
        "Tỷ trọng số đêm (%)": (g.nights / g.nights.sum() * 100).round(1).values,
        f"Doanh thu* ({CURRENCY} / năm)": g.revenue.round(0).astype(int).values,
        "Tỷ trọng doanh thu (%)": (g.revenue / g.revenue.sum() * 100).round(1).values,
    })
    tier_pct = pd.DataFrame({
        "listing": g.listings / g.listings.sum() * 100,
        "nights": g.nights / g.nights.sum() * 100,
        "revenue": g.revenue / g.revenue.sum() * 100}).reset_index(drop=True)

    # ============================================================
    # 4. IN & LƯU BẢNG
    # ============================================================
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 50)
    pd.set_option("display.max_colwidth", 90)


    os.makedirs("data/processed/kpi/pro_host_aggregate",exist_ok=True)
    kpi.to_csv("data/processed/kpi/pro_host_aggregate/"+{time}+"_kpi_pro_host_aggregate.csv", index=False, encoding="utf-8-sig")
    os.makedirs("data/processed/kpi/pro_host_scale",exist_ok=True)
    tier.to_csv("data/processed/pro_host_scale/"+{time}+"_kpi_pro_host_scale.csv", index=False, encoding="utf-8-sig")


ENGAGEMENT_HOT_QUANTILE = CONFIG.kpi["engagement_hot_quantile"]  # Hot = top 10% reviews_per_month
ENGAGEMENT_CURRENCY = CONFIG.currency  # tiền tệ của cột price (đổi nếu không phải EUR)

ENGAGEMENT_UNITS = {
    "n_listings": "căn",
    "active_rate": "tỷ lệ (0-1)",
    "hot_rate": "tỷ lệ (0-1)",
    "median_reviews_per_month": "review/tháng",
    "median_reviews_ltm": "review/12 tháng",
    "hot_lift": "lần so với toàn thành phố",
    "n": "căn",
    "median_price": f"{ENGAGEMENT_CURRENCY}/đêm",
    "median_price_ratio": "lần so với giá trung vị khu vực",
    "superhost_rate": "tỷ lệ (0-1)",
    "verified_rate": "tỷ lệ (0-1)",
    "instant_bookable_rate": "tỷ lệ (0-1)",
    "median_accommodates": "khách",
    "median_availability_365": "ngày/năm",
    "hot_cut_reviews_per_month": "review/tháng",
}

def _tuan_load(time):
    df = pd.read_csv(Processed.listings[time])
    df = df[~df["flag_any"]].copy()  # chỉ tính KPI sau QA
    df["number_of_reviews_ltm"] = df["number_of_reviews_ltm"].fillna(0)
    # Căn chưa có review → reviews_per_month NaN: coi là 0 (không hoạt động)
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
    df["is_active"] = df["number_of_reviews_ltm"] > 0
    hot_cut = df.loc[df["is_active"], "reviews_per_month"].quantile(ENGAGEMENT_HOT_QUANTILE)
    df["is_hot"] = df["is_active"] & (df["reviews_per_month"] >= hot_cut)
    return df, hot_cut

def _tuan_kpi(time):
    df, hot_cut = _tuan_load(time)

    # ── KPI theo khu vực ────────────────────────────────────────────────
    g = df.groupby("neighbourhood_cleansed")
    by_nb = pd.DataFrame(
        {
            "n_listings": g.size(),
            "active_rate": g["is_active"].mean(),
            "hot_rate": g["is_hot"].mean(),
            "median_reviews_per_month": g["reviews_per_month"].median(),
            "median_reviews_ltm": g["number_of_reviews_ltm"].median(),
        }
    ).reset_index()
    # lift > 1: khu này có nhiều căn Hot hơn mức trung bình toàn thành phố
    by_nb["hot_lift"] = by_nb["hot_rate"] / df["is_hot"].mean()
    nb_long = by_nb.melt(
        id_vars="neighbourhood_cleansed", var_name="kpi", value_name="value"
    ).rename(columns={"neighbourhood_cleansed": "group"})
    nb_long["level"] = "neighbourhood"

    # ── Điều gì chung ở căn Hot? ────────────────────────────────────────
    # price_ratio = giá / giá trung vị khu vực → loại bỏ ảnh hưởng vị trí,
    # < 1 nghĩa là rẻ hơn mặt bằng khu vực ("giá rẻ?")
    nb_median = df.groupby("neighbourhood_cleansed")["price"].transform("median")
    df["price_ratio"] = df["price"] / nb_median

    profile = (
        df.groupby("is_hot")
        .agg(
            n=("id", "size"),
            median_price=("price", "median"),
            median_price_ratio=("price_ratio", "median"),
            superhost_rate=("host_is_superhost", "mean"),
            verified_rate=("host_identity_verified", "mean"),
            instant_bookable_rate=("instant_bookable", "mean"),
            median_accommodates=("accommodates", "median"),
            median_availability_365=("availability_365", "median"),
        )
        .reset_index()
    )
    pf_long = profile.melt(id_vars="is_hot", var_name="kpi", value_name="value")
    pf_long["group"] = pf_long["is_hot"].map({True: "Hot", False: "Không Hot"})
    pf_long = pf_long.drop(columns="is_hot")
    pf_long["level"] = "hot_vs_not_hot"

    # ── Toàn thành phố ──────────────────────────────────────────────────
    overall = pd.DataFrame(
        {
            "level": "overall",
            "group": "all",
            "kpi": ["n_listings", "active_rate", "hot_rate", "hot_cut_reviews_per_month"],
            "value": [len(df), df["is_active"].mean(), df["is_hot"].mean(), hot_cut],
        }
    )

    out = pd.concat([overall, nb_long, pf_long], ignore_index=True)
    out["unit"] = out["kpi"].map(ENGAGEMENT_UNITS)
    out = out[["level", "group", "kpi", "value", "unit"]]
    os.makedirs("data/processed/kpi/engagement",exist_ok=True)
    out.to_csv("data/processed/kpi/engagement"+{time}+"kpi_engagement.csv", index=False, encoding="utf-8-sig")
def Tuan(time):
    _tuan_kpi(time)



AREA_COL = CONFIG.kpi["area_col"]
AMENITIES_HOT_QUANTILE = CONFIG.kpi["amenities_hot_quantile"]
TOP_N = CONFIG.kpi["top_n"]

def parse_amenities(value):
    try:
        items = json.loads(str(value))
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    return sorted({
        " ".join(item.strip().lower().split())
        for item in items
        if isinstance(item, str) and item.strip()
    })

def thanh():
    snapshots = sorted(CONFIG.snapshots)
    listing_frames = []
    snapshot_col="snapshot"
    out_path="data/processed/kpi/kpi_amenities.csv"
    for snapshot in snapshots:
        time = (
            snapshot.strftime("%Y-%m-%d")
            if hasattr(snapshot, "strftime")
            else snapshot
        )
        listing_path = "data/processed/"+time+"/"+time+"_processed-listings.csv"
        if listing_path is None:
            listing_path = (
                Path(Processed.base)
                / time
                / f"{time}_processed-listings.csv"
            )
        listing_path = Path(listing_path)
        if not listing_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy dữ liệu snapshot {time}: {listing_path}"
            )

        columns = set(pd.read_csv(listing_path, nrows=0).columns)
        id_col = "id" if "id" in columns else "listing_id"
        needed_columns = {
            "amenities",
            AREA_COL,
            id_col,
            "estimated_occupancy_l365d",
            "availability_365",
        }
        snapshot_listings = pd.read_csv(
            listing_path,
            usecols=lambda column: column in needed_columns,
        )
        snapshot_listings[snapshot_col] = time
        listing_frames.append(snapshot_listings)
    
    """Tính KPI tiện ích; nhận bảng listings đã được QA và lọc."""
    listings = pd.read_csv(Processed.listings[time])
    
    if not isinstance(listings, pd.DataFrame):
        raise TypeError("listings phải là pandas DataFrame.")

    missing = {
        "amenities",
        AREA_COL,
        snapshot_col,
    } - set(listings.columns)
    if missing:
        raise ValueError(f"Thiếu cột bắt buộc: {', '.join(sorted(missing))}.")

    id_col = "id" if "id" in listings.columns else "listing_id"
    if id_col not in listings.columns:
        raise ValueError("Thiếu cột id hoặc listing_id.")
    if not 0 < AMENITIES_HOT_QUANTILE < 1:
        raise ValueError("hot_quantile phải nằm trong khoảng (0, 1).")

    data = listings.copy()

    # Phòng thủ nhẹ: chỉ parse JSON hợp lệ thành danh sách tên duy nhất.
    

    data["amenities_list"] = data["amenities"].map(parse_amenities)
    data["amenities_count"] = data["amenities_list"].map(len)
    data = data[data["amenities_count"] > 0].copy()

    if data.empty:
        raise ValueError("Không còn listing hợp lệ để tính KPI.")

    # Điểm theo trung vị tiện ích trong từng snapshot.
    data["Amenities_Score"] = data.groupby(snapshot_col)["amenities_count"].transform(
        lambda count: count.div(count.median()).mul(100).round(2)
    )

    area_parts = []
    top_parts = []
    snapshot_summaries = []

    for snapshot, snapshot_data in data.groupby(snapshot_col, sort=False):
        snapshot_data = snapshot_data.copy()

        # Ưu tiên occupancy; availability là fallback khi snapshot cũ không có occupancy.
        if "estimated_occupancy_l365d" in snapshot_data.columns:
            occupancy = pd.to_numeric(
                snapshot_data["estimated_occupancy_l365d"],
                errors="coerce",
            )
        else:
            occupancy = None

        if occupancy is not None and occupancy.notna().any():
            threshold = occupancy.quantile(AMENITIES_HOT_QUANTILE)
            hot = occupancy.ge(threshold)
            threshold_metric = "estimated_occupancy_l365d"
        elif "availability_365" in snapshot_data.columns:
            availability = pd.to_numeric(
                snapshot_data["availability_365"],
                errors="coerce",
            )
            if not availability.notna().any():
                raise ValueError(f"Snapshot {snapshot}: không có chỉ số nhu cầu hợp lệ.")
            threshold = availability.quantile(1 - AMENITIES_HOT_QUANTILE)
            hot = availability.le(threshold)
            threshold_metric = "availability_365"
        else:
            raise ValueError(
                "Thiếu estimated_occupancy_l365d hoặc availability_365 "
                "để xác định nhóm cháy phòng."
            )

        snapshot_data["is_hot"] = hot.fillna(False)
        snapshot_summaries.append(
            {
                "snapshot": snapshot,
                "listing_count": len(snapshot_data),
                "median_amenities_count": snapshot_data["amenities_count"].median(),
                "hot_metric": threshold_metric,
                "hot_threshold": threshold,
                "hot_share_pct": round(float(hot.mean() * 100), 1),
            }
        )

        # KPI theo khu vực: quy mô, trung vị tiện ích và điểm trung vị.
        area = (
            snapshot_data.groupby(AREA_COL, observed=True)
            .agg(
                n_listings=(id_col, "size"),
                median_amenities_count=("amenities_count", "median"),
                Amenities_Score_Median=("Amenities_Score", "median"),
            )
            .round(2)
            .reset_index()
        )
        area.insert(0, snapshot_col, snapshot)
        area["hot_metric"] = threshold_metric
        area_parts.append(area)

        # So số liệu hot với nhóm còn lại để tìm tiện ích có hiệu ứng khác biệt.
        hot_data = snapshot_data.loc[snapshot_data["is_hot"]]
        rest_data = snapshot_data.loc[~snapshot_data["is_hot"]]

        if hot_data.empty:
            raise ValueError(f"Snapshot {snapshot}: không có listing cháy phòng.")

        hot_count = hot_data["amenities_list"].explode().value_counts()
        rest_count = rest_data["amenities_list"].explode().value_counts()
        amenities = sorted(set(hot_count.index) | set(rest_count.index))

        top = pd.DataFrame({
            "amenity": amenities,
            "hot_share": [
                hot_count.get(name, 0) / len(hot_data) for name in amenities
            ],
            "rest_share": [
                rest_count.get(name, 0) / len(rest_data)
                if len(rest_data)
                else 0.0
                for name in amenities
            ],
        })
        top["share_difference"] = top["hot_share"] - top["rest_share"]
        top.insert(0, snapshot_col, snapshot)
        top = (
            top.sort_values(
                ["share_difference", "hot_share"],
                ascending=[False, False],
            )
            .head(max(1, int(TOP_N)))
            .copy()
        )
        top["rank"] = range(1, len(top) + 1)
        top["hot_metric"] = threshold_metric
        top_parts.append(top)

    area_scores = pd.concat(area_parts, ignore_index=True)
    top_amenities = pd.concat(top_parts, ignore_index=True)
    area_scores.to_csv(out_file, index=False)


for i in CONFIG.snapshots:
    time = i.strftime("%Y-%m-%d")
    Tan(time)
    Tuan(time)
thanh()
Thai()#chỉ mốc cuối
    #tấn thái tuấn phải truyền tham số mốc tgian, thành không cần
    #bị báo keyerror ở Processed.listings[time]