from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utility import CAM, XANH


def MoreExpensiveThanMedian(listing, title):
    listing = listing.dropna(subset=["price"])
    trungvi = listing["price"].median()
    mau = np.where(listing["price"] > trungvi, CAM, XANH)

    _fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.scatter(
        listing["longitude"], listing["latitude"], s=6, c=mau, alpha=0.45, linewidths=0
    )
    ax.set_aspect("equal")  # 1 độ kinh = 1 độ vĩ trên hình
    ax.set_title(
        title,
        loc="left",
        fontweight="bold",
    )
    ax.set_xlabel("kinh độ")
    ax.set_ylabel("vĩ độ")
    plt.show()


def ReviewPerMonth(review, title, bound, start):
    thang = (
        review[review["date"] < bound]
        .set_index("date")
        .resample("ME")
        .size()
        .loc[start:]
    )

    _fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(thang.index, thang.values, color=XANH)
    ax.set_title(title)
    ax.set_ylabel("số đánh giá / tháng")
    plt.show()


def RawPerMonthAndMeanPerRolling(raw, ylabel, rolling, bound, left, right):
    thang_du = raw[raw["date"] < bound].set_index("date").resample("ME").size()
    _nam = thang_du.groupby(thang_du.index.year).sum()  # tổng theo năm, để so sánh

    _fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(
        thang_du.index,
        thang_du.values,
        color="k",
        linestyle="-",
        lw=1,
        label="mỗi tháng",
    )
    ax.plot(
        thang_du.rolling(rolling).mean(),
        color=CAM,
        linestyle="--",
        lw=2,
        label=f"trung bình {rolling} tháng",
    )
    ax.set_xlim(left, right)
    ax.set_ylabel(f"{ylabel} / tháng")
    ax.legend()
    plt.show()


def Choropleth(file, listing):
    geo = gpd.read_file(file)
    co_gia = listing.dropna(subset=["price"])

    kpi = (
        co_gia.groupby("neighbourhood")
        .agg(gia=("price", "median"), n=("price", "size"))
        .reset_index()
    )
    ban_do = geo.merge(kpi, on="neighbourhood", how="left")
    ban_do["gia_hien"] = ban_do["gia"].where(
        ban_do["n"] >= 30
    )  # dưới 30 chỗ ở: không tô

    ax = ban_do.plot(
        column="gia_hien",
        cmap="Blues",
        legend=True,
        edgecolor="#999",
        linewidth=0.5,
        missing_kwds={"color": "#eeeeee", "hatch": "///"},
        legend_kwds={"label": "giá trung vị (CLP/đêm)"},
    )
    ax.set_axis_off()
    plt.show()


def plot_amenities_kpi(
    area_scores,
    top_amenities,
    area_col="neighbourhood_cleansed",
    snapshot_col="snapshot",
    out_path="figures/amenities_kpi.png",
    min_listings=30,
):
    """Vẽ và lưu biểu đồ KPI tiện ích."""
    if not isinstance(area_scores, pd.DataFrame):
        raise TypeError("area_scores phải là pandas DataFrame.")
    if not isinstance(top_amenities, pd.DataFrame):
        raise TypeError("top_amenities phải là pandas DataFrame.")
    if area_scores.empty:
        raise ValueError("area_scores không được rỗng.")

    required_area = {
        snapshot_col,
        area_col,
        "n_listings",
        "median_amenities_count",
        "Amenities_Score_Median",
        "hot_metric",
    }
    missing_area = required_area - set(area_scores.columns)
    if missing_area:
        raise ValueError(
            f"Thiếu cột trong area_scores: {', '.join(sorted(missing_area))}."
        )

    required_top = {
        snapshot_col,
        "amenity",
        "hot_share",
        "rest_share",
        "share_difference",
        "rank",
        "hot_metric",
    }
    missing_top = required_top - set(top_amenities.columns)
    if missing_top:
        raise ValueError(
            f"Thiếu cột trong top_amenities: {', '.join(sorted(missing_top))}."
        )

    snapshots = area_scores[snapshot_col].dropna().sort_values().unique()
    if len(snapshots) == 0:
        raise ValueError(f"area_scores không có giá trị hợp lệ trong cột {snapshot_col}.")

    latest_snapshot = snapshots[-1]
    latest_area = area_scores.loc[area_scores[snapshot_col] == latest_snapshot]
    latest_top = top_amenities.loc[
        top_amenities[snapshot_col] == latest_snapshot
    ].sort_values("rank")
    hot_metric = latest_area["hot_metric"].iloc[0]

    fig = plt.figure(figsize=(16, 10))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.3])
    area_ax = fig.add_subplot(grid[0, 0])
    top_ax = fig.add_subplot(grid[0, 1])
    heatmap_ax = fig.add_subplot(grid[1, :])

    area_plot = latest_area.loc[
        latest_area["n_listings"] >= min_listings
    ].sort_values("Amenities_Score_Median", ascending=True)
    if area_plot.empty:
        area_ax.text(0.5, 0.5, "Không có khu vực đủ số listing.", ha="center")
        area_ax.set_yticks([])
    else:
        area_ax.barh(
            area_plot[area_col].astype(str),
            area_plot["Amenities_Score_Median"],
            color=XANH,
        )
        area_ax.invert_yaxis()
    area_ax.axvline(100, color=CAM, linestyle="--", linewidth=1)
    area_ax.set_xlabel("Điểm (100 = trung vị snapshot)")
    area_ax.set_title(f"Điểm tiện ích theo khu vực — {latest_snapshot}")

    if latest_top.empty:
        top_ax.text(0.5, 0.5, "Không có tiện ích để hiển thị.", ha="center")
        top_ax.set_xticks([])
    else:
        positions = np.arange(len(latest_top))
        width = 0.38
        top_ax.bar(
            positions - width / 2,
            latest_top["hot_share"],
            width,
            label="Căn cháy phòng",
            color=CAM,
        )
        top_ax.bar(
            positions + width / 2,
            latest_top["rest_share"],
            width,
            label="Căn còn lại",
            color=XANH,
        )
        top_ax.set_xticks(
            positions,
            latest_top["amenity"].astype(str),
            rotation=35,
            ha="right",
        )
        top_ax.legend()
    top_ax.set_ylabel("Tỷ lệ listing")
    top_ax.set_title(f"Top tiện ích — {latest_snapshot}")

    heatmap = area_scores.pivot(
        index=area_col,
        columns=snapshot_col,
        values="median_amenities_count",
    ).reindex(columns=snapshots).sort_index()
    image = heatmap_ax.imshow(
        heatmap.to_numpy(dtype=float),
        aspect="auto",
        interpolation="nearest",
        cmap="YlGnBu",
    )
    heatmap_ax.set_xticks(
        np.arange(len(heatmap.columns)),
        heatmap.columns.astype(str),
        rotation=35,
        ha="right",
    )
    heatmap_ax.set_yticks(
        np.arange(len(heatmap.index)),
        heatmap.index.astype(str),
    )
    heatmap_ax.set_xlabel("Snapshot")
    heatmap_ax.set_ylabel("Khu vực")
    heatmap_ax.set_title("Số tiện ích trung vị theo khu vực và snapshot")
    colorbar = fig.colorbar(image, ax=heatmap_ax)
    colorbar.set_label("Số tiện ích / listing")
    fig.suptitle(f"Chỉ số cháy phòng: {hot_metric}")
    fig.tight_layout()

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_file, dpi=150)
    finally:
        plt.close(fig)
