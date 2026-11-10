import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

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
