import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utility import CONFIG, Processed

# Tạo sẵn đường dẫn
FIG_DIR = Path("reports/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)
KPI_DIR = Path("data/processed/kpi")
KPI_DIR.mkdir(parents=True, exist_ok=True)

# Bắt buộc phải gọi hàm này để Processed.listings có dữ liệu (Tránh lỗi KeyError)
Processed.Create(CONFIG.snapshots, "processed", "csv")


# ============================================================
# 1. HÀM CỦA THÁI (Tính doanh thu)
# ============================================================
def Thai(time):
    snapshots = sorted(CONFIG.snapshots)
    snapshot_strs = [s.strftime("%Y-%m-%d") for s in snapshots]

    frames = []
    for t in snapshot_strs:
        path = f"data/processed/{t}/{t}_processed-listings.csv"
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, usecols=["estimated_revenue_l365d"])
        df["snapshot"] = t
        frames.append(df)

    if not frames:
        return None

    all_listings = pd.concat(frames, ignore_index=True)
    valid = all_listings["estimated_revenue_l365d"].dropna()
    estimated_annual_revenue = valid.mean()

    summary = (
        all_listings.dropna(subset=["estimated_revenue_l365d"])
        .groupby("snapshot")["estimated_revenue_l365d"]
        .agg(so_listing="count", trung_binh="mean", trung_vi="median")
        .round(2)
        .reset_index()
    )

    overall_row = pd.DataFrame(
        [
            {
                "snapshot": "Toàn bộ (12 tháng)",
                "so_listing": len(valid),
                "trung_binh": round(estimated_annual_revenue, 2),
                "trung_vi": round(valid.median(), 2),
            }
        ]
    )
    kpi_df = pd.concat([summary, overall_row], ignore_index=True)
    kpi_df["kpi_name"] = "Estimated Annual Revenue"

    output_path = KPI_DIR / "kpi_total_price.csv"
    kpi_df.to_csv(output_path, index=False, encoding="utf-8-sig")


# ============================================================
# 2. HÀM CỦA TÂN (Pro Host)
# ============================================================
def Tan(time):
    CSV_PATH = Processed.listings[time]

    PRO_HOST_THRESHOLD = CONFIG.kpi.get("pro_host_threashold", 3)
    CURRENCY = CONFIG.currency
    TIER_BINS = CONFIG.kpi.get("tier_bins", [0, 1, 3, 100])
    TIER_LABELS = CONFIG.kpi.get("tier_labels", [0, 1, 2])
    TIER_NAMES = CONFIG.kpi.get("tier_names", ["Siêu nhỏ", "Nhỏ", "Lớn"])
    WINSOR_Q = CONFIG.kpi.get("winsor_q", 0.99)

    K = "calculated_host_listings_count"
    cols = ["id", K, "estimated_revenue_l365d", "estimated_occupancy_l365d"]
    df = pd.read_csv(CSV_PATH, usecols=cols).dropna(subset=[K]).copy()

    df["is_pro"] = df[K] > PRO_HOST_THRESHOLD
    df["tier"] = pd.cut(df[K], TIER_BINS, labels=TIER_LABELS)
    df["host_w"] = 1 / df[K]

    rev_cap = df["estimated_revenue_l365d"].quantile(WINSOR_Q)
    df["rev_w"] = df["estimated_revenue_l365d"].clip(upper=rev_cap)

    n = len(df)
    pro = df[df.is_pro]

    share_listing = df.is_pro.mean() * 100
    share_host = pro.host_w.sum() / df.host_w.sum() * 100
    share_rev = pro.rev_w.sum() / df.rev_w.sum() * 100
    share_nights = (
        pro.estimated_occupancy_l365d.sum() / df.estimated_occupancy_l365d.sum() * 100
    )
    avg_pro_portfolio = len(pro) / pro.host_w.sum()

    kpi = pd.DataFrame(
        [
            ("Tổng số listing phân tích", n, "listing"),
            ("Số listing của Pro Host", int(df.is_pro.sum()), "listing"),
            ("Pro Host Share – theo listing", round(share_listing, 2), "%"),
            ("Pro Host Share – theo chủ nhà (ước tính)", round(share_host, 2), "%"),
            ("Thị phần doanh thu của Pro Host", round(share_rev, 2), "%"),
            ("Thị phần số đêm có khách của Pro Host", round(share_nights, 2), "%"),
            (
                "Quy mô trung bình của 1 Pro Host",
                round(avg_pro_portfolio, 1),
                "listing / chủ nhà",
            ),
            (
                f"Ngưỡng cắt đuôi doanh thu (P{int(WINSOR_Q * 100)})",
                round(rev_cap),
                f"{CURRENCY} / năm",
            ),
        ],
        columns=["Chỉ số", "Giá trị", "Đơn vị"],
    )

    kpi["Giá trị"] = [
        f"{v:,.0f}"
        if float(v).is_integer() and u != "%" and "chủ nhà" not in u
        else f"{v:,.2f}"
        if u == "%"
        else f"{v:,.1f}"
        for v, u in zip(kpi["Giá trị"], kpi["Đơn vị"])
    ]

    g = df.groupby("tier", observed=False).agg(
        listings=("id", "size"),
        host_w=("host_w", "sum"),
        nights=("estimated_occupancy_l365d", "sum"),
        revenue=("rev_w", "sum"),
    )

    tier = pd.DataFrame(
        {
            "Nhóm (listing / chủ nhà)": TIER_LABELS,
            "Tên nhóm": TIER_NAMES,
            "Số listing (listing)": g.listings.values,
            "Tỷ trọng listing (%)": (g.listings / g.listings.sum() * 100)
            .round(1)
            .values,
            "Tỷ trọng chủ nhà – ước tính (%)": (g.host_w / g.host_w.sum() * 100)
            .round(2)
            .values,
            "Số đêm có khách (đêm / năm)": g.nights.round(0).astype(int).values,
            "Tỷ trọng số đêm (%)": (g.nights / g.nights.sum() * 100).round(1).values,
            f"Doanh thu* ({CURRENCY} / năm)": g.revenue.round(0).astype(int).values,
            "Tỷ trọng doanh thu (%)": (g.revenue / g.revenue.sum() * 100)
            .round(1)
            .values,
        }
    )

    os.makedirs(KPI_DIR / "pro_host_aggregate", exist_ok=True)
    kpi.to_csv(
        KPI_DIR / "pro_host_aggregate" / f"{time}_kpi_pro_host_aggregate.csv",
        index=False,
        encoding="utf-8-sig",
    )

    os.makedirs(KPI_DIR / "pro_host_scale", exist_ok=True)
    tier.to_csv(
        KPI_DIR / "pro_host_scale" / f"{time}_kpi_pro_host_scale.csv",
        index=False,
        encoding="utf-8-sig",
    )


# ============================================================
# 3. HÀM CỦA TUẤN (Engagement)
# ============================================================
def Tuan(time):
    ENGAGEMENT_HOT_QUANTILE = CONFIG.kpi.get("engagement_hot_quantile", 0.9)
    ENGAGEMENT_CURRENCY = CONFIG.currency

    df = pd.read_csv(Processed.listings[time])
    df = df[~df["flag_any"]].copy()
    df["number_of_reviews_ltm"] = df["number_of_reviews_ltm"].fillna(0)
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
    df["is_active"] = df["number_of_reviews_ltm"] > 0

    hot_cut = df.loc[df["is_active"], "reviews_per_month"].quantile(
        ENGAGEMENT_HOT_QUANTILE
    )
    df["is_hot"] = df["is_active"] & (df["reviews_per_month"] >= hot_cut)

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

    by_nb["hot_lift"] = by_nb["hot_rate"] / df["is_hot"].mean()
    nb_long = by_nb.melt(
        id_vars="neighbourhood_cleansed", var_name="kpi", value_name="value"
    ).rename(columns={"neighbourhood_cleansed": "group"})
    nb_long["level"] = "neighbourhood"

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

    overall = pd.DataFrame(
        {
            "level": "overall",
            "group": "all",
            "kpi": [
                "n_listings",
                "active_rate",
                "hot_rate",
                "hot_cut_reviews_per_month",
            ],
            "value": [len(df), df["is_active"].mean(), df["is_hot"].mean(), hot_cut],
        }
    )

    out = pd.concat([overall, nb_long, pf_long], ignore_index=True)

    os.makedirs(KPI_DIR / "engagement", exist_ok=True)
    out.to_csv(
        KPI_DIR / "engagement" / f"{time}_kpi_engagement.csv",
        index=False,
        encoding="utf-8-sig",
    )


# ============================================================
# 4. HÀM CỦA THÀNH (Amenities)
# ============================================================
def parse_amenities(value):
    try:
        items = json.loads(str(value))
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    return sorted(
        {
            " ".join(item.strip().lower().split())
            for item in items
            if isinstance(item, str) and item.strip()
        }
    )


def thanh():
    AREA_COL = CONFIG.kpi.get("area_col", "neighbourhood_cleansed")
    AMENITIES_HOT_QUANTILE = CONFIG.kpi.get("amenities_hot_quantile", 0.9)
    TOP_N = CONFIG.kpi.get("top_n", 10)

    snapshots = sorted(CONFIG.snapshots)
    listing_frames = []

    for snapshot in snapshots:
        time = (
            snapshot.strftime("%Y-%m-%d") if hasattr(snapshot, "strftime") else snapshot
        )
        listing_path = Path(Processed.listings[time])

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
            listing_path, usecols=lambda c: c in needed_columns
        )
        snapshot_listings["snapshot"] = time
        listing_frames.append(snapshot_listings)

    listings = pd.concat(listing_frames, ignore_index=True)

    data = listings.copy()
    data["amenities_list"] = data["amenities"].map(parse_amenities)
    data["amenities_count"] = data["amenities_list"].map(len)
    data = data[data["amenities_count"] > 0].copy()

    if data.empty:
        raise ValueError("Không còn listing hợp lệ để tính KPI.")

    data["Amenities_Score"] = data.groupby("snapshot")["amenities_count"].transform(
        lambda count: count.div(count.median()).mul(100).round(2)
    )

    area_parts = []
    top_parts = []

    for snapshot, snapshot_data in data.groupby("snapshot", sort=False):
        snapshot_data = snapshot_data.copy()

        if "estimated_occupancy_l365d" in snapshot_data.columns:
            occupancy = pd.to_numeric(
                snapshot_data["estimated_occupancy_l365d"], errors="coerce"
            )
        else:
            occupancy = None

        if occupancy is not None and occupancy.notna().any():
            threshold = occupancy.quantile(AMENITIES_HOT_QUANTILE)
            hot = occupancy.ge(threshold)
            threshold_metric = "estimated_occupancy_l365d"
        elif "availability_365" in snapshot_data.columns:
            availability = pd.to_numeric(
                snapshot_data["availability_365"], errors="coerce"
            )
            threshold = availability.quantile(1 - AMENITIES_HOT_QUANTILE)
            hot = availability.le(threshold)
            threshold_metric = "availability_365"
        else:
            raise ValueError("Thiếu estimated_occupancy_l365d hoặc availability_365.")

        snapshot_data["is_hot"] = hot.fillna(False)

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

        area.insert(0, "snapshot", snapshot)
        area["hot_metric"] = threshold_metric
        area_parts.append(area)

        hot_data = snapshot_data.loc[snapshot_data["is_hot"]]
        rest_data = snapshot_data.loc[~snapshot_data["is_hot"]]

        if hot_data.empty:
            continue

        hot_count = hot_data["amenities_list"].explode().value_counts()
        rest_count = rest_data["amenities_list"].explode().value_counts()
        amenities = sorted(set(hot_count.index) | set(rest_count.index))

        top = pd.DataFrame(
            {
                "amenity": amenities,
                "hot_share": [
                    hot_count.get(name, 0) / len(hot_data) for name in amenities
                ],
                "rest_share": [
                    rest_count.get(name, 0) / len(rest_data) if len(rest_data) else 0.0
                    for name in amenities
                ],
            }
        )

        top["share_difference"] = top["hot_share"] - top["rest_share"]
        top.insert(0, "snapshot", snapshot)
        top = (
            top.sort_values(["share_difference", "hot_share"], ascending=[False, False])
            .head(max(1, int(TOP_N)))
            .copy()
        )
        top["rank"] = range(1, len(top) + 1)
        top["hot_metric"] = threshold_metric
        top_parts.append(top)

    area_scores = pd.concat(area_parts, ignore_index=True)
    top_amenities = pd.concat(top_parts, ignore_index=True)

    os.makedirs(KPI_DIR, exist_ok=True)
    area_scores.to_csv(
        KPI_DIR / "kpi_amenities_area.csv", index=False, encoding="utf-8-sig"
    )
    top_amenities.to_csv(
        KPI_DIR / "kpi_amenities_top.csv", index=False, encoding="utf-8-sig"
    )
