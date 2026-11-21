from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.utility import Processed
from utility import CONFIG, Filtered

KPI_DIR = Path("data/processed")
FIG_DIR = Path("reports/figures")
TUAN_HOT_QUANTILE = 0.9  # Hot = top 10% reviews_per_month
TUAN_CURRENCY = "EUR"  # tiền tệ của cột price (đổi nếu không phải EUR)


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


# TUẤN – KPI 5: Tần suất hoạt động & Thu hút (Listing Engagement)
#
# active_rate  : số căn có number_of_reviews_ltm > 0 / tổng số căn      (tỷ lệ 0-1)
# hot_rate     : số căn có reviews_per_month >= P90 / tổng số căn        (tỷ lệ 0-1)
# median_reviews_per_month : median(reviews_per_month)                   (review/tháng)
# Phân tích Hot: so sánh giá, giá so với khu vực, Superhost giữa Hot và Không Hot
#
# Kết quả: 1 file duy nhất  data/processed/kpi_engagement_{time}.csv
# (dạng long: level | group | kpi | value | unit)
# ═════════════════════════════════════════════════════════════════════════
_TUAN_UNITS = {
    "n_listings": "căn",
    "active_rate": "tỷ lệ (0-1)",
    "hot_rate": "tỷ lệ (0-1)",
    "median_reviews_per_month": "review/tháng",
    "median_reviews_ltm": "review/12 tháng",
    "hot_lift": "lần so với toàn thành phố",
    "n": "căn",
    "median_price": f"{TUAN_CURRENCY}/đêm",
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
    hot_cut = df.loc[df["is_active"], "reviews_per_month"].quantile(TUAN_HOT_QUANTILE)
    df["is_hot"] = df["is_active"] & (df["reviews_per_month"] >= hot_cut)
    return df, hot_cut


def _tuan_kpi(time):
    KPI_DIR.mkdir(parents=True, exist_ok=True)
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
    out["unit"] = out["kpi"].map(_TUAN_UNITS)
    out = out[["level", "group", "kpi", "value", "unit"]]
    out.to_csv(KPI_DIR / f"kpi_engagement_{time}.csv", index=False)


def _tuan_do_thi(time, min_listings=30, top=15):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    k = pd.read_csv(KPI_DIR / f"kpi_engagement_{time}.csv")
    nb = (
        k[k["level"] == "neighbourhood"]
        .pivot(index="group", columns="kpi", values="value")
        .reset_index()
    )
    pf = (
        k[k["level"] == "hot_vs_not_hot"]
        .pivot(index="group", columns="kpi", values="value")
        .reset_index()
    )

    # 1. Top khu vực có tỷ lệ Hot cao (bỏ khu quá ít căn để tránh nhiễu)
    d = nb[nb["n_listings"] >= min_listings].nlargest(top, "hot_rate").iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(d["group"], d["hot_rate"] * 100)
    ax.set(
        title=f"Top {top} khu vực có tỷ lệ căn Hot cao nhất", xlabel="Tỷ lệ căn Hot (%)"
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"engagement_hot_rate_{time}.png", dpi=150)
    plt.close(fig)

    # 2. Căn sống vs căn Hot theo khu vực
    fig, ax = plt.subplots(figsize=(8, 6))
    y = list(range(len(d)))
    ax.barh([i + 0.2 for i in y], d["active_rate"] * 100, height=0.4, label="Căn sống")
    ax.barh([i - 0.2 for i in y], d["hot_rate"] * 100, height=0.4, label="Căn Hot")
    ax.set_yticks(y)
    ax.set_yticklabels(d["group"])
    ax.set(title="Căn sống vs căn Hot theo khu vực", xlabel="%")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"engagement_active_vs_hot_{time}.png", dpi=150)
    plt.close(fig)

    # 3. So sánh Hot vs Không Hot: giá so với khu vực, Superhost
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].bar(pf["group"], pf["median_price_ratio"])
    axes[0].axhline(1, ls="--", c="gray")
    axes[0].set(title="Giá / giá trung vị khu vực", ylabel="Tỷ lệ (1 = bằng mặt bằng)")
    axes[1].bar(pf["group"], pf["superhost_rate"] * 100)
    axes[1].set(title="Tỷ lệ Superhost", ylabel="%")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"engagement_hot_profile_{time}.png", dpi=150)
    plt.close(fig)


def Tuan(time):
    _tuan_kpi(time)
    _tuan_do_thi(time)


def Thanh():
    pass
