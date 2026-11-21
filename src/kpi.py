import os
import json
import pandas as pd
from src.utility import CONFIG, LoadConfig
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch

def Thai():
    if not hasattr(CONFIG, "snapshots"):
        LoadConfig()

    # ── 1. Xác định 4 snapshot (12 tháng qua) ─────────────────────────────
    snapshots = sorted(CONFIG.snapshots)          # sắp xếp tăng dần theo ngày
    snapshot_strs = [s.strftime("%Y-%m-%d") for s in snapshots]

    # ── 2. Đọc và gộp dữ liệu từ 4 folder trong processed ─────────────────
    frames = []
    for time in snapshot_strs:
        path = f"data/processed/{time}/{time}_cleaned_listings.csv"
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
    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/kpi_thai.csv"
    kpi_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return kpi_df


def Van():
    pass


def Tan():
    pass

def Tuan():
    pass


def Thanh():
    pass

if __name__ == "__main__":
    Thai()