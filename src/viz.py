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
