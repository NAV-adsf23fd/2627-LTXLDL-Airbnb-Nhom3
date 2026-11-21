def Thai():
    pass


def Van():
    pass


def Tan():
    """
    Phân tích mức độ chuyên nghiệp hóa (Pro Host) của thị trường lưu trú ngắn hạn
    Bản có đơn vị đầy đủ cho các bảng và biểu đồ.
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import FancyBboxPatch
    import os 

    # ============================================================
    # 1. THAM SỐ
    # ============================================================
    CSV_PATH = "data/processed/2026-03-21/2026-03-21_processed-listings.csv"
    THRESHOLD = 3                       # > 3 listing = Pro Host
    CURRENCY = "USD"                    # !! dataset không ghi đơn vị tiền, hãy kiểm tra nguồn rồi sửa
    TIER_BINS = [0, 1, 3, 10, 50, np.inf]
    TIER_LABELS = ["1", "2–3", "4–10", "11–50", "50+"]
    TIER_NAMES = ["Cá nhân", "Nhỏ lẻ", "Chuyên nghiệp", "Công ty QL", "Quy mô lớn"]
    TIER_COLORS = ["#2A9D8F", "#8AB17D", "#E9C46A", "#F4A261", "#E76F51"]
    WINSOR_Q = 0.99                     # cắt đuôi doanh thu ở phân vị 99

    BG, INK, MUTED = "#F7F6F2", "#1F2937", "#6B7280"
    PRO_C, IND_C = "#E76F51", "#2A9D8F"

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Segoe UI", "Arial", "DejaVu Sans"],
        "figure.facecolor": BG, "axes.facecolor": BG,
        "axes.edgecolor": "#D1D5DB", "axes.labelcolor": MUTED,
        "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    })

    # ============================================================
    # 2. ĐỌC & CHUẨN BỊ DỮ LIỆU
    # ============================================================
    K = "calculated_host_listings_count"
    cols = ["id", K, "estimated_revenue_l365d", "estimated_occupancy_l365d"]
    df = pd.read_csv(CSV_PATH, usecols=cols).dropna(subset=[K]).copy()

    df["is_pro"] = df[K] > THRESHOLD
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

    print("\n=== BẢNG 1. KPI TỔNG HỢP ===")
    print(kpi.to_string(index=False, justify="left"))
    print("\n=== BẢNG 2. THEO NHÓM QUY MÔ CHỦ NHÀ ===")
    print(tier.to_string(index=False))
    print(f"(*) Doanh thu đã cắt đuôi ở P{int(WINSOR_Q*100)} = {rev_cap:,.0f} {CURRENCY}/năm")

    os.makedirs("data/processed/kpi", exist_ok=True)
    kpi.to_csv("data/processed/kpi/bang1_kpi.csv", index=False, encoding="utf-8-sig")
    tier.to_csv("data/processed/kpi/bang2_nhom_quy_mo.csv", index=False, encoding="utf-8-sig")

    # ============================================================
    # 5. VẼ DASHBOARD (KPI + cơ cấu + thị phần)
    # ============================================================
    def style(ax, grid="y"):
        for s in ("top", "right", "left" if grid == "x" else "bottom"):
            ax.spines[s].set_visible(False)
        ax.grid(axis=grid, color="#E5E7EB", lw=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)

    def title(ax, main, sub=None):
        ax.set_title(main, loc="left", fontsize=13, fontweight="bold", color=INK,
                    pad=26 if sub else 12)
        if sub:
            ax.text(0, 1.03, sub, transform=ax.transAxes, fontsize=9, color=MUTED)

    fig = plt.figure(figsize=(18, 10.5))
    gs = GridSpec(2, 2, height_ratios=[0.42, 1], width_ratios=[1, 1.5],
                hspace=0.5, wspace=0.22, left=0.035, right=0.975, top=0.86, bottom=0.17)
    fig.text(0.035, 0.955, "Mức độ chuyên nghiệp hóa của thị trường lưu trú ngắn hạn",
            fontsize=24, fontweight="bold")
    fig.text(0.035, 0.915,
            f"Phân tích {n:,} listing  •  Pro Host = chủ nhà quản lý hơn {THRESHOLD} listing",
            fontsize=12, color=MUTED)

    # ---- Hàng 1: thẻ KPI ----
    axk = fig.add_subplot(gs[0, :]); axk.axis("off")
    axk.set_xlim(0, 1); axk.set_ylim(0, 1)
    cards = [
        (f"{share_listing:.1f} %", "PRO HOST SHARE · THEO LISTING",
        f"{int(df.is_pro.sum())} / {n:,} listing thuộc chủ nhà >{THRESHOLD} listing", PRO_C),
        (f"{share_host:.1f} %", "PRO HOST SHARE · THEO CHỦ NHÀ",
        "% chủ nhà · ước tính, hiệu chỉnh sai lệch lấy mẫu", "#B5523B"),
        (f"{share_rev:.1f} %", "THỊ PHẦN DOANH THU CỦA PRO",
        f"% tổng doanh thu · cắt đuôi ở P{int(WINSOR_Q*100)}", "#E9A23B"),
        (f"~{avg_pro_portfolio:.0f} listing", "QUY MÔ TB CỦA 1 PRO HOST",
        "listing / chủ nhà chuyên nghiệp", IND_C),
    ]
    w, gap = 0.235, 0.02
    for i, (big, lab, sub, c) in enumerate(cards):
        x0 = i * (w + gap)
        axk.add_patch(FancyBboxPatch((x0, 0.05), w, 0.9, boxstyle="square,pad=0",
                                    transform=axk.transAxes, fc="white", ec="#E5E7EB", lw=1.2))
        axk.add_patch(FancyBboxPatch((x0, 0.05), 0.006, 0.9, boxstyle="square,pad=0",
                                    transform=axk.transAxes, fc=c, ec="none"))
        axk.text(x0 + 0.02, 0.76, lab, fontsize=10, color=MUTED, fontweight="bold", va="center")
        axk.text(x0 + 0.02, 0.45, big, fontsize=32, color=c, fontweight="bold", va="center")
        axk.text(x0 + 0.02, 0.15, sub, fontsize=9.5, color=MUTED, va="center")

    # ---- Hàng 2 trái: donut cơ cấu ----
    ax = fig.add_subplot(gs[1, 0])
    vals = tier_pct["listing"].values
    ax.pie(vals, colors=TIER_COLORS, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.38, edgecolor=BG, linewidth=3))
    ax.text(0, 0.08, f"{share_listing:.0f} %", ha="center", va="center",
            fontsize=32, fontweight="bold", color=PRO_C)
    ax.text(0, -0.22, "listing của\nPro Host", ha="center", va="center", fontsize=10, color=MUTED)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in TIER_COLORS],
            labels=[f"{l} listing/chủ nhà · {nm}: {v:.1f} % ({int(c)} listing)"
                    for l, nm, v, c in zip(TIER_LABELS, TIER_NAMES, vals, g.listings)],
            loc="upper center", bbox_to_anchor=(0.5, 0.03), frameon=False, fontsize=9.5)
    title(ax, "Cơ cấu listing theo quy mô chủ nhà", "Đơn vị: % tổng số listing")

    # ---- Hàng 2 giữa: mỗi nhóm chiếm bao nhiêu thị trường ----
    ax = fig.add_subplot(gs[1, 1])
    x = np.arange(len(TIER_LABELS)); bw = 0.26
    series = [("listing", "% số listing", "#9CA3AF"),
            ("nights", "% số đêm có khách", "#F4A261"),
            ("revenue", "% doanh thu", "#E76F51")]
    for j, (key, lab, c) in enumerate(series):
        bars = ax.bar(x + (j - 1) * bw, tier_pct[key], bw * 0.92, color=c, label=lab, zorder=3)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8, f"{b.get_height():.0f}%",
                    ha="center", fontsize=8.5, color=INK)
    ax.axvline(1.5, color=INK, ls=(0, (4, 4)), lw=1.2)
    ax.text(1.55, ax.get_ylim()[1] * 0.97, f"Pro Host (>{THRESHOLD} listing) →", fontsize=10,
            color=PRO_C, fontweight="bold", va="top")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{l} listing\n{nm}" for l, nm in zip(TIER_LABELS, TIER_NAMES)], fontsize=9.5)
    ax.set_xlabel("Quy mô chủ nhà (số listing / chủ nhà)")
    ax.set_ylabel("Tỷ trọng so với toàn thị trường (%)")
    ax.legend(frameon=False, ncol=1, loc="upper right", bbox_to_anchor=(1, 0.98), fontsize=9.5)
    style(ax)
    title(ax, "Mỗi nhóm chiếm bao nhiêu thị trường?",
        f"Đơn vị: % · doanh thu đã cắt đuôi ở P{int(WINSOR_Q*100)}")

    fig.text(0.035, 0.025,
            "Ghi chú: '% chủ nhà' ước tính bằng trọng số 1/calculated_host_listings_count để bù sai lệch lấy mẫu theo listing. "
            f"Doanh thu và số đêm có khách là số ước tính của dataset; đơn vị tiền tệ ({CURRENCY}) cần kiểm tra theo nguồn dữ liệu.",
            fontsize=9, color=MUTED)

    plt.savefig("pro_host_dashboard.png", dpi=160, facecolor=BG)
    plt.show()

def Tuan():
    pass


def Thanh():
    pass
