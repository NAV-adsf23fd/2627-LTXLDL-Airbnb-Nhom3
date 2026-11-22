import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch

from src.kpi import thanh
from src.utility import *

LoadConfig()


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


# tan


BG, INK, MUTED = "#F7F6F2", "#1F2937", "#6B7280"
PRO_C, IND_C = "#E76F51", "#2A9D8F"


def style(ax, grid="y"):
    for s in ("top", "right", "left" if grid == "x" else "bottom"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid, color="#E5E7EB", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def title(ax, main, sub=None):
    ax.set_title(
        main,
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=INK,
        pad=26 if sub else 12,
    )
    if sub:
        ax.text(0, 1.03, sub, transform=ax.transAxes, fontsize=9, color=MUTED)


def Tan(time):
    CSV_PATH = Processed.listings[time]
    TIER_COLORS = CONFIG.kpi["tier_colors"]
    WINSOR_Q = CONFIG.kpi["winsor_q"]  # cắt đuôi doanh thu ở phân vị 99

    PRO_HOST_THRESHOLD = CONFIG.kpi.get("pro_host_threashold", 3)
    CURRENCY = CONFIG.currency

    TIER_BINS = CONFIG.kpi.get("tier_bins", [0, 1, 3, 100])
    TIER_LABELS = CONFIG.kpi.get("tier_labels", [0, 1, 2])

    # Xử lý lỗi config (nếu có)
    is_valid_bins = (
        isinstance(TIER_BINS, list)
        and len(TIER_BINS) >= 2
        and all(TIER_BINS[i] < TIER_BINS[i + 1] for i in range(len(TIER_BINS) - 1))
    )
    if not is_valid_bins:
        TIER_BINS = [0, 1, 3, 100]
        TIER_LABELS = [0, 1, 2]

    TIER_NAMES = CONFIG.kpi.get("tier_names", ["Siêu nhỏ", "Nhỏ", "Lớn"])
    WINSOR_Q = CONFIG.kpi.get("winsor_q", 0.99)

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Segoe UI", "Arial", "DejaVu Sans"],
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
        }
    )
    K = "calculated_host_listings_count"
    cols = ["id", K, "estimated_revenue_l365d", "estimated_occupancy_l365d"]

    df = pd.read_csv(CSV_PATH, usecols=cols).dropna(subset=[K]).copy()

    # --- SỬA LỖI TẠI ĐÂY: Điền 0 cho các giá trị NaN ---
    df["estimated_revenue_l365d"] = df["estimated_revenue_l365d"].fillna(0)
    df["estimated_occupancy_l365d"] = df["estimated_occupancy_l365d"].fillna(0)

    df["is_pro"] = df[K] > PRO_HOST_THRESHOLD
    df["tier"] = pd.cut(df[K], TIER_BINS, labels=TIER_LABELS)
    df["host_w"] = 1 / df[K]

    rev_cap = df["estimated_revenue_l365d"].quantile(WINSOR_Q)
    # --- SỬA LỖI TẠI ĐÂY: Nếu rev_cap là NaN thì gán bằng 0 ---
    if pd.isna(rev_cap):
        rev_cap = 0

    df["rev_w"] = df["estimated_revenue_l365d"].clip(upper=rev_cap)

    n = len(df)
    pro = df[df.is_pro]

    share_listing = df.is_pro.mean() * 100

    # --- SỬA LỖI TẠI ĐÂY: Kiểm tra mẫu số trước khi chia ---
    total_host_w = df.host_w.sum()
    share_host = (pro.host_w.sum() / total_host_w * 100) if total_host_w > 0 else 0.0

    total_rev = df.rev_w.sum()
    share_rev = (pro.rev_w.sum() / total_rev * 100) if total_rev > 0 else 0.0

    total_nights = df.estimated_occupancy_l365d.sum()
    share_nights = (
        (pro.estimated_occupancy_l365d.sum() / total_nights * 100)
        if total_nights > 0
        else 0.0
    )
    g = df.groupby("tier", observed=False).agg(
        listings=("id", "size"),
        host_w=("host_w", "sum"),
        nights=("estimated_occupancy_l365d", "sum"),
        revenue=("rev_w", "sum"),
    )
    tier_pct = pd.DataFrame(
        {
            "listing": g.listings / g.listings.sum() * 100,
            "nights": g.nights / g.nights.sum() * 100,
            "revenue": g.revenue / g.revenue.sum() * 100,
        }
    ).reset_index(drop=True)
    total_pro_w = pro.host_w.sum()
    avg_pro_portfolio = (len(pro) / total_pro_w) if total_pro_w > 0 else 0.0
    fig = plt.figure(figsize=(18, 10.5))
    gs = GridSpec(
        2,
        2,
        height_ratios=[0.42, 1],
        width_ratios=[1, 1.5],
        hspace=0.5,
        wspace=0.22,
        left=0.035,
        right=0.975,
        top=0.86,
        bottom=0.17,
    )
    fig.text(
        0.035,
        0.955,
        "Mức độ chuyên nghiệp hóa của thị trường lưu trú ngắn hạn",
        fontsize=24,
        fontweight="bold",
    )
    fig.text(
        0.035,
        0.915,
        f"Phân tích {n:,} listing  •  Pro Host = chủ nhà quản lý hơn {PRO_HOST_THRESHOLD} listing",
        fontsize=12,
        color=MUTED,
    )

    # ---- Hàng 1: thẻ KPI ----
    axk = fig.add_subplot(gs[0, :])
    axk.axis("off")
    axk.set_xlim(0, 1)
    axk.set_ylim(0, 1)
    cards = [
        (
            f"{share_listing:.1f} %",
            "PRO HOST SHARE · THEO LISTING",
            f"{int(df.is_pro.sum())} / {n:,} listing thuộc chủ nhà >{PRO_HOST_THRESHOLD} listing",
            PRO_C,
        ),
        (
            f"{share_host:.1f} %",
            "PRO HOST SHARE · THEO CHỦ NHÀ",
            "% chủ nhà · ước tính, hiệu chỉnh sai lệch lấy mẫu",
            "#B5523B",
        ),
        (
            f"{share_rev:.1f} %",
            "THỊ PHẦN DOANH THU CỦA PRO",
            f"% tổng doanh thu · cắt đuôi ở P{int(WINSOR_Q * 100)}",
            "#E9A23B",
        ),
        (
            f"~{avg_pro_portfolio:.0f} listing",
            "QUY MÔ TB CỦA 1 PRO HOST",
            "listing / chủ nhà chuyên nghiệp",
            IND_C,
        ),
    ]
    w, gap = 0.235, 0.02
    for i, (big, lab, sub, c) in enumerate(cards):
        x0 = i * (w + gap)
        axk.add_patch(
            FancyBboxPatch(
                (x0, 0.05),
                w,
                0.9,
                boxstyle="square,pad=0",
                transform=axk.transAxes,
                fc="white",
                ec="#E5E7EB",
                lw=1.2,
            )
        )
        axk.add_patch(
            FancyBboxPatch(
                (x0, 0.05),
                0.006,
                0.9,
                boxstyle="square,pad=0",
                transform=axk.transAxes,
                fc=c,
                ec="none",
            )
        )
        axk.text(
            x0 + 0.02,
            0.76,
            lab,
            fontsize=10,
            color=MUTED,
            fontweight="bold",
            va="center",
        )
        axk.text(
            x0 + 0.02, 0.45, big, fontsize=32, color=c, fontweight="bold", va="center"
        )
        axk.text(x0 + 0.02, 0.15, sub, fontsize=9.5, color=MUTED, va="center")

    # ---- Hàng 2 trái: donut cơ cấu ----
    ax = fig.add_subplot(gs[1, 0])
    vals = tier_pct["listing"].values
    ax.pie(
        vals,
        colors=TIER_COLORS,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.38, edgecolor=BG, linewidth=3),
    )
    ax.text(
        0,
        0.08,
        f"{share_listing:.0f} %",
        ha="center",
        va="center",
        fontsize=32,
        fontweight="bold",
        color=PRO_C,
    )
    ax.text(
        0,
        -0.22,
        "listing của\nPro Host",
        ha="center",
        va="center",
        fontsize=10,
        color=MUTED,
    )
    ax.legend(
        handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in TIER_COLORS],
        labels=[
            f"{l} listing/chủ nhà · {nm}: {v:.1f} % ({int(c)} listing)"
            for l, nm, v, c in zip(TIER_LABELS, TIER_NAMES, vals, g.listings)
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.03),
        frameon=False,
        fontsize=9.5,
    )
    title(ax, "Cơ cấu listing theo quy mô chủ nhà", "Đơn vị: % tổng số listing")

    # ---- Hàng 2 giữa: mỗi nhóm chiếm bao nhiêu thị trường ----
    ax = fig.add_subplot(gs[1, 1])
    x = np.arange(len(TIER_LABELS))
    bw = 0.26
    series = [
        ("listing", "% số listing", "#9CA3AF"),
        ("nights", "% số đêm có khách", "#F4A261"),
        ("revenue", "% doanh thu", "#E76F51"),
    ]
    for j, (key, lab, c) in enumerate(series):
        bars = ax.bar(
            x + (j - 1) * bw, tier_pct[key], bw * 0.92, color=c, label=lab, zorder=3
        )
        for b in bars:
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height() + 0.8,
                f"{b.get_height():.0f}%",
                ha="center",
                fontsize=8.5,
                color=INK,
            )
    ax.axvline(1.5, color=INK, ls=(0, (4, 4)), lw=1.2)
    ax.text(
        1.55,
        ax.get_ylim()[1] * 0.97,
        f"Pro Host (>{PRO_HOST_THRESHOLD} listing) →",
        fontsize=10,
        color=PRO_C,
        fontweight="bold",
        va="top",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{l} listing\n{nm}" for l, nm in zip(TIER_LABELS, TIER_NAMES)], fontsize=9.5
    )
    ax.set_xlabel("Quy mô chủ nhà (số listing / chủ nhà)")
    ax.set_ylabel("Tỷ trọng so với toàn thị trường (%)")
    ax.legend(
        frameon=False, ncol=1, loc="upper right", bbox_to_anchor=(1, 0.98), fontsize=9.5
    )
    style(ax)
    title(
        ax,
        "Mỗi nhóm chiếm bao nhiêu thị trường?",
        f"Đơn vị: % · doanh thu đã cắt đuôi ở P{int(WINSOR_Q * 100)}",
    )

    fig.text(
        0.035,
        0.025,
        "Ghi chú: '% chủ nhà' ước tính bằng trọng số 1/calculated_host_listings_count để bù sai lệch lấy mẫu theo listing. "
        f"Doanh thu và số đêm có khách là số ước tính của dataset; đơn vị tiền tệ ({CURRENCY}) cần kiểm tra theo nguồn dữ liệu.",
        fontsize=9,
        color=MUTED,
    )
    os.makedirs("figures/pro_host", exist_ok=True)
    plt.savefig(
        "figures/pro_host/" + time + "-pro_host_dashboard.png", dpi=160, facecolor=BG
    )


# thanh


def plot_amenities_kpi(area_scores, top_amenities):
    AREA_COL = CONFIG.kpi.get("area_col", "neighbourhood_cleansed")
    snapshot_col = "snapshot"
    out_path = "figures/amenities_kpi.png"
    min_listings = 30
    """Vẽ và lưu biểu đồ KPI tiện ích."""
    if not isinstance(area_scores, pd.DataFrame):
        raise TypeError("area_scores phải là pandas DataFrame.")
    if not isinstance(top_amenities, pd.DataFrame):
        raise TypeError("top_amenities phải là pandas DataFrame.")
    if area_scores.empty:
        raise ValueError("area_scores không được rỗng.")

    required_area = {
        snapshot_col,
        AREA_COL,
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
        raise ValueError(
            f"area_scores không có giá trị hợp lệ trong cột {snapshot_col}."
        )

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

    area_plot = latest_area.loc[latest_area["n_listings"] >= min_listings].sort_values(
        "Amenities_Score_Median", ascending=True
    )
    if area_plot.empty:
        area_ax.text(0.5, 0.5, "Không có khu vực đủ số listing.", ha="center")
        area_ax.set_yticks([])
    else:
        area_ax.barh(
            area_plot[AREA_COL].astype(str),
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

    heatmap = (
        area_scores.pivot(
            index=AREA_COL,
            columns=snapshot_col,
            values="median_amenities_count",
        )
        .reindex(columns=snapshots)
        .sort_index()
    )
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

    plt.savefig("figures/kpi_amenities.png", dpi=160)


# tuan


def _tuan_do_thi(time):
    os.makedirs("figures/engagement", exist_ok=True)
    os.makedirs("figures/engagement/" + time, exist_ok=True)
    min_listings = 30
    top = 15
    k = pd.read_csv(
        "data/processed/kpi" + "/engagement/" + time + "_kpi_engagement.csv"
    )

    nb = (
        k[k["level"] == "neighbourhood"]
        .pivot(index="group", columns="kpi", values="value")
        .reset_index()
    )
    if nb.empty or "n_listings" not in nb.columns:
        print(f"[{time}] Bỏ qua biểu đồ engagement do thiếu dữ liệu neighbourhood.")
        return

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
    fig.savefig("figures/engagement/" + time + "/kpi_engagement_hot_rate.png", dpi=160)
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
    fig.savefig(
        "figures/engagement/" + time + "/kpi_engagement_active_and_hot.png", dpi=160
    )
    plt.close(fig)

    # 3. So sánh Hot vs Không Hot: giá so với khu vực, Superhost
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].bar(pf["group"], pf["median_price_ratio"])
    axes[0].axhline(1, ls="--", c="gray")
    axes[0].set(title="Giá / giá trung vị khu vực", ylabel="Tỷ lệ (1 = bằng mặt bằng)")
    axes[1].bar(pf["group"], pf["superhost_rate"] * 100)
    axes[1].set(title="Tỷ lệ Superhost", ylabel="%")
    fig.tight_layout()
    fig.savefig("figures/engagement/" + time + "/kpi_engagement.png", dpi=160)
    plt.close(fig)


def RunViz():
    amenities = thanh()
    for i in CONFIG.snapshots:
        time = i.strftime("%Y-%m-%d")
        _tuan_do_thi(time)
        Tan(time)
        plt.close("all")

    plot_amenities_kpi(amenities["area_scores"], amenities["top_amenities"])
    plt.close("all")
    print("Đã vẽ xong toàn bộ biểu đồ.")
