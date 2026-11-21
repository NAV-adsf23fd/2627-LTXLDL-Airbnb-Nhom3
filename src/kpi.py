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
            print(f"[Thai] Bỏ qua snapshot {time}: file không tồn tại ({path})")
            continue
        df = pd.read_csv(path, usecols=["estimated_revenue_l365d"])
        df["snapshot"] = time
        frames.append(df)

    if not frames:
        print("[Thai] Không tìm thấy dữ liệu nào trong data/processed/.")
        return None

    all_listings = pd.concat(frames, ignore_index=True)

    # ── 3. Tính trung bình estimated_revenue_l365d ─────────────────────────
    # Chỉ lấy các dòng có giá trị hợp lệ (> 0)
    valid = all_listings["estimated_revenue_l365d"].dropna()
    valid = valid[valid > 0]

    estimated_annual_revenue = valid.mean()

    # ── 4. In kết quả ──────────────────────────────────────────────────────
    print("=" * 50)
    print("KPI 4 – Doanh thu ước tính năm (Estimated Annual Revenue)")
    print("=" * 50)
    print(f"  Số snapshot đọc : {len(frames)} ({', '.join(snapshot_strs)})")
    print(f"  Số listing hợp lệ: {len(valid):,}")
    print(f"  Trung bình estimated_revenue_l365d: {estimated_annual_revenue:,.2f}")
    print()

    # Thống kê bổ sung theo từng snapshot
    summary = (
        all_listings[all_listings["estimated_revenue_l365d"] > 0]
        .groupby("snapshot")["estimated_revenue_l365d"]
        .agg(so_listing="count", trung_binh="mean", trung_vi="median")
        .round(2)
    )
    print(summary.to_string())
    print("=" * 50)

    return estimated_annual_revenue


def Van():
    pass


def Tan():
    pass

def Tuan():
    pass


def Thanh():
    pass

if __name__ == "__main__":
    print("--- CHẠY KPI THÁI ---")
    Thai()