# File chạy thử mấy cái linh tinh

from src.evaluate import load
from src.utility import CONFIG, LoadConfig
from src.viz import *
from src.kpi import *


def Test():
    print("Hello world!")

    LoadConfig()
    # # 1. Chạy các hàm cần tính theo từng mốc thời gian (Tan, Tuan, Van)
    # for i in CONFIG.snapshots:
    #     time = i.strftime("%Y-%m-%d")
    #     print(f"Đang xử lý KPI cho mốc: {time}...")
    #
    #     Tan(time)  # KPI Pro Host
    #     Tuan(time)  # KPI Engagement
    #     Van(time)  # KPI Guest Satisfaction (có dùng LLM)
    #
    # # 2. Chạy các hàm tự động gộp tất cả các mốc (Thai, Thành)
    # print("Đang tính KPI Doanh thu (Thai)...")
    # # Hàm Thai(time) có vòng lặp bên trong tự gộp 4 mốc, nên chỉ cần gọi 1 lần.
    # # Truyền đại 1 mốc thời gian vào tham số cho hợp lệ, nó không dùng đến tham số này.
    # Thai(CONFIG.snapshots[0].strftime("%Y-%m-%d"))
    #
    # print("Đang tính KPI Tiện ích (thanh)...")
    # thanh()
    #
    # print("✅ HOÀN THÀNH! Kiểm tra thư mục data/processed/kpi/ để lấy kết quả.")

    # for i in CONFIG.snapshots:
    #     time = i.strftime("%Y-%m-%d")
    #     _tuan_do_thi(time)
    #     Tan(time)
    # plot_amenities_kpi(amenities["area_scores"], amenities["top_amenities"])

    # print(load("data/llm/llm-response.json"))
    RunKpi()
    RunViz()
