import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.chdir(r"d:\antigravity code\BTL Inside AIrbnd\2627-LTXLDL-Airbnb-Nhom3")
os.makedirs("figures", exist_ok=True)

# Thiết lập style đồ họa thanh lịch, chuẩn học thuật
plt.rcParams.update({
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.family": "sans-serif",
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#cccccc",
    "axes.grid": True,
    "grid.color": "#ebebeb",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
})

# ============================================================
# 1. KPI 1: THÁI (Doanh thu & Số lượng qua các snapshot)
# ============================================================
df_thai = pd.read_csv("data/processed/kpi/kpi_total_price.csv")
df_thai_sn = df_thai[df_thai["snapshot"] != "Toàn bộ (12 tháng)"].copy()

fig, ax1 = plt.subplots(figsize=(7, 4), dpi=300)
color_bar = "#1f77b4"
color_line = "#d62728"

x = np.arange(len(df_thai_sn))
bars = ax1.bar(x - 0.15, df_thai_sn["trung_binh"], width=0.3, color=color_bar, alpha=0.85, label="Doanh thu TB (EUR/năm)")
ax1.set_ylabel("Doanh thu trung bình (EUR)", color=color_bar, fontsize=10, fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(df_thai_sn["snapshot"], fontsize=9)
ax1.set_ylim(0, 50000)

for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 800, f"{yval:,.0f} €", ha='center', va='bottom', fontsize=8, fontweight="bold", color=color_bar)

ax2 = ax1.twinx()
lines = ax2.plot(x + 0.15, df_thai_sn["so_listing"], color=color_line, marker="o", linewidth=2.5, label="Số lượng listing hợp lệ")
ax2.set_ylabel("Số lượng listing", color=color_line, fontsize=10, fontweight="bold")
ax2.set_ylim(500, 1100)
ax2.grid(False)

for i, txt in enumerate(df_thai_sn["so_listing"]):
    ax2.annotate(f"{txt:,}", (x[i] + 0.15, txt + 15), ha='center', fontsize=8, fontweight="bold", color=color_line)

plt.title("KPI 1 (Thái): Doanh thu ước tính trung bình & Quy mô listing qua các quý", fontsize=11, fontweight="bold", pad=12)
fig.tight_layout()
plt.savefig("figures/kpi1_revenue.png")
plt.close()

# ============================================================
# 2. KPI 2: TÂN (Thị phần Pro Host & Phân tầng quy mô)
# ============================================================
df_tan_scale = pd.read_csv("data/processed/kpi/pro_host_scale/2026-03-21_kpi_pro_host_scale.csv")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4), dpi=300)

# Biểu đồ tròn: Cơ cấu listing theo nhóm quy mô
colors = ["#2b5c8f", "#4682b4", "#f4a261", "#e76f51", "#d62828"]
ax1.pie(df_tan_scale["Tỷ trọng listing (%)"], labels=df_tan_scale["Tên nhóm"], autopct="%1.1f%%",
        startangle=140, colors=colors, textprops={'fontsize': 8})
ax1.set_title("Cơ cấu Số lượng Listing\ntheo Nhóm Quy mô Host", fontsize=10, fontweight="bold")

# Biểu đồ cột ngang so sánh: Tỷ trọng Listing vs Tỷ trọng Doanh thu
y = np.arange(len(df_tan_scale))
width = 0.35
ax2.barh(y - width/2, df_tan_scale["Tỷ trọng listing (%)"], width, label="% Listing", color="#4682b4")
ax2.barh(y + width/2, df_tan_scale["Tỷ trọng doanh thu (%)"], width, label="% Doanh thu", color="#e76f51")
ax2.set_yticks(y)
ax2.set_yticklabels(df_tan_scale["Tên nhóm"], fontsize=9)
ax2.invert_yaxis()
ax2.set_xlabel("Tỷ trọng (%)", fontsize=9)
ax2.legend(fontsize=8)
ax2.set_title("So sánh Tỷ trọng Listing vs Doanh thu", fontsize=10, fontweight="bold")

fig.suptitle("KPI 2 (Tân): Phân tích Mức độ Chuyên nghiệp hóa (Pro Host Index)", fontsize=11, fontweight="bold")
fig.tight_layout()
plt.savefig("figures/kpi2_pro_host.png")
plt.close()

# ============================================================
# 3. KPI 3: TUẤN (So sánh thuộc tính nhóm Hot vs Không Hot)
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4), dpi=300)

groups = ["Không Hot (Bình thường)", "Hot (Cháy phòng)"]
prices = [236.0, 196.0]
superhost = [35.0, 61.45]

bars1 = ax1.bar(groups, prices, color=["#6c757d", "#28a745"], width=0.45, alpha=0.85)
ax1.set_ylabel("Giá trung vị (EUR/đêm)", fontsize=9, fontweight="bold")
ax1.set_ylim(0, 300)
for b in bars1:
    h = b.get_height()
    ax1.text(b.get_x() + b.get_width()/2., h + 6, f"{h:.0f} €\n(-17%)", ha='center', fontsize=8, fontweight="bold")
ax1.set_title("Giá trung vị mỗi đêm", fontsize=10, fontweight="bold")

bars2 = ax2.bar(groups, superhost, color=["#6c757d", "#17a2b8"], width=0.45, alpha=0.85)
ax2.set_ylabel("Tỷ lệ đạt danh hiệu Superhost (%)", fontsize=9, fontweight="bold")
ax2.set_ylim(0, 80)
for b in bars2:
    h = b.get_height()
    ax2.text(b.get_x() + b.get_width()/2., h + 2, f"{h:.1f}%", ha='center', fontsize=8, fontweight="bold")
ax2.set_title("Tỷ lệ Chủ nhà đạt Superhost", fontsize=10, fontweight="bold")

fig.suptitle("KPI 3 (Tuấn): Đặc trưng tạo nên nhóm Listing 'Cháy phòng' (Hot Listings)", fontsize=11, fontweight="bold")
fig.tight_layout()
plt.savefig("figures/kpi3_engagement.png")
plt.close()

# ============================================================
# 4. KPI 4: THÀNH (Top tiện ích tạo khác biệt cho nhóm Hot)
# ============================================================
df_top_amen = pd.read_csv("data/processed/kpi/kpi_amenities_top.csv")
df_top_03 = df_top_amen[df_top_amen["snapshot"] == "2026-03-21"].sort_values("share_difference", ascending=True)

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
y = np.arange(len(df_top_03))
bars = ax.barh(y, df_top_03["share_difference"] * 100, color="#ff7f0e", alpha=0.85, height=0.6)
ax.set_yticks(y)
ax.set_yticklabels(df_top_03["amenity"].str.title(), fontsize=8.5)
ax.set_xlabel("Chênh lệch tỷ lệ xuất hiện giữa nhóm Hot và nhóm còn lại (%)", fontsize=9)
for b in bars:
    w = b.get_width()
    ax.text(w + 0.5, b.get_y() + b.get_height()/2., f"+{w:.1f}%", va='center', fontsize=8, fontweight="bold", color="#d35400")
ax.set_xlim(0, 32)
plt.title("KPI 4 (Thành): Top 10 Tiện ích Tạo Sức Hút Vượt Trội Cho Listing Cháy Phòng", fontsize=10.5, fontweight="bold", pad=12)
fig.tight_layout()
plt.savefig("figures/kpi4_amenities.png")
plt.close()

# ============================================================
# 5. KPI 5: VÂN (Mối quan hệ Điểm đánh giá & Phàn nàn)
# ============================================================
df_van = pd.read_csv("data/processed/kpi/van_satisfaction/2026-03-21_kpi_van_satisfaction.csv")
df_van_valid = df_van[df_van["score_group"] != "Chưa có đánh giá"].copy()

fig, ax1 = plt.subplots(figsize=(7.5, 3.8), dpi=300)
x = np.arange(len(df_van_valid))
bars = ax1.bar(x - 0.15, df_van_valid["Số căn hộ"], width=0.3, color="#2b5c8f", label="Số lượng căn hộ", alpha=0.85)
ax1.set_ylabel("Số lượng căn hộ", color="#2b5c8f", fontsize=9, fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(df_van_valid["score_group"], fontsize=9)
ax1.set_ylim(0, 1100)

for b in bars:
    h = b.get_height()
    ax1.text(b.get_x() + b.get_width()/2., h + 15, f"{h:,}", ha='center', fontsize=8, fontweight="bold", color="#2b5c8f")

ax2 = ax1.twinx()
lines = ax2.plot(x + 0.15, df_van_valid["Tỷ lệ Phàn nàn (%)"], color="#c0392b", marker="s", linewidth=2.5, label="Tỷ lệ phàn nàn LLM (%)")
ax2.set_ylabel("Tỷ lệ phàn nàn LLM (%)", color="#c0392b", fontsize=9, fontweight="bold")
ax2.set_ylim(-0.1, 1.2)
ax2.grid(False)

for i, txt in enumerate(df_van_valid["Tỷ lệ Phàn nàn (%)"]):
    ax2.annotate(f"{txt:.2f}%", (x[i] + 0.15, txt + 0.05), ha='center', fontsize=8, fontweight="bold", color="#c0392b")

plt.title("KPI 5 (Vân): Phân bổ Nhóm Sao và Tỷ lệ Phàn nàn Trích xuất từ LLM", fontsize=10.5, fontweight="bold", pad=12)
fig.tight_layout()
plt.savefig("figures/kpi5_satisfaction.png")
plt.close()

print("ALL 5 FIGURES CREATED SUCCESSFULLY!")
