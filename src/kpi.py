import json
import sys
from pathlib import Path

import pandas as pd


def Thai():
    pass


def Van():
    pass


def Tan():
    pass


def Tuan():
    pass


def amenities_kpi(
    listings,
    area_col="neighbourhood_cleansed",
    snapshot_col="snapshot",
    hot_quantile=0.75,
    top_n=5,
    out_path="data/processed/kpi_amenities.csv",
    verbose=True,
):
    """Tính KPI tiện ích; nhận bảng listings đã được QA và lọc."""
    if not isinstance(listings, pd.DataFrame):
        raise TypeError("listings phải là pandas DataFrame.")

    missing = {
        "amenities",
        area_col,
        snapshot_col,
    } - set(listings.columns)
    if missing:
        raise ValueError(f"Thiếu cột bắt buộc: {', '.join(sorted(missing))}.")

    id_col = "id" if "id" in listings.columns else "listing_id"
    if id_col not in listings.columns:
        raise ValueError("Thiếu cột id hoặc listing_id.")
    if not 0 < hot_quantile < 1:
        raise ValueError("hot_quantile phải nằm trong khoảng (0, 1).")

    data = listings.copy()

    # Phòng thủ nhẹ: chỉ parse JSON hợp lệ thành danh sách tên duy nhất.
    def parse_amenities(value):
        try:
            items = json.loads(str(value))
        except (json.JSONDecodeError, TypeError):
            return []
        if not isinstance(items, list):
            return []
        return sorted({
            " ".join(item.strip().lower().split())
            for item in items
            if isinstance(item, str) and item.strip()
        })

    data["amenities_list"] = data["amenities"].map(parse_amenities)
    data["amenities_count"] = data["amenities_list"].map(len)
    data = data[data["amenities_count"] > 0].copy()

    if data.empty:
        raise ValueError("Không còn listing hợp lệ để tính KPI.")

    # Điểm theo trung vị tiện ích trong từng snapshot.
    data["Amenities_Score"] = data.groupby(snapshot_col)["amenities_count"].transform(
        lambda count: count.div(count.median()).mul(100).round(2)
    )

    area_parts = []
    top_parts = []
    snapshot_summaries = []

    for snapshot, snapshot_data in data.groupby(snapshot_col, sort=False):
        snapshot_data = snapshot_data.copy()

        # Ưu tiên occupancy; availability là fallback khi snapshot cũ không có occupancy.
        if "estimated_occupancy_l365d" in snapshot_data.columns:
            occupancy = pd.to_numeric(
                snapshot_data["estimated_occupancy_l365d"],
                errors="coerce",
            )
        else:
            occupancy = None

        if occupancy is not None and occupancy.notna().any():
            threshold = occupancy.quantile(hot_quantile)
            hot = occupancy.ge(threshold)
            threshold_metric = "estimated_occupancy_l365d"
        elif "availability_365" in snapshot_data.columns:
            availability = pd.to_numeric(
                snapshot_data["availability_365"],
                errors="coerce",
            )
            if not availability.notna().any():
                raise ValueError(f"Snapshot {snapshot}: không có chỉ số nhu cầu hợp lệ.")
            threshold = availability.quantile(1 - hot_quantile)
            hot = availability.le(threshold)
            threshold_metric = "availability_365"
        else:
            raise ValueError(
                "Thiếu estimated_occupancy_l365d hoặc availability_365 "
                "để xác định nhóm cháy phòng."
            )

        snapshot_data["is_hot"] = hot.fillna(False)
        snapshot_summaries.append(
            {
                "snapshot": snapshot,
                "listing_count": len(snapshot_data),
                "median_amenities_count": snapshot_data["amenities_count"].median(),
                "hot_metric": threshold_metric,
                "hot_threshold": threshold,
                "hot_share_pct": round(float(hot.mean() * 100), 1),
            }
        )

        # KPI theo khu vực: quy mô, trung vị tiện ích và điểm trung vị.
        area = (
            snapshot_data.groupby(area_col, observed=True)
            .agg(
                n_listings=(id_col, "size"),
                median_amenities_count=("amenities_count", "median"),
                Amenities_Score_Median=("Amenities_Score", "median"),
            )
            .round(2)
            .reset_index()
        )
        area.insert(0, snapshot_col, snapshot)
        area["hot_metric"] = threshold_metric
        area_parts.append(area)

        # So số liệu hot với nhóm còn lại để tìm tiện ích có hiệu ứng khác biệt.
        hot_data = snapshot_data.loc[snapshot_data["is_hot"]]
        rest_data = snapshot_data.loc[~snapshot_data["is_hot"]]

        if hot_data.empty:
            raise ValueError(f"Snapshot {snapshot}: không có listing cháy phòng.")

        hot_count = hot_data["amenities_list"].explode().value_counts()
        rest_count = rest_data["amenities_list"].explode().value_counts()
        amenities = sorted(set(hot_count.index) | set(rest_count.index))

        top = pd.DataFrame({
            "amenity": amenities,
            "hot_share": [
                hot_count.get(name, 0) / len(hot_data) for name in amenities
            ],
            "rest_share": [
                rest_count.get(name, 0) / len(rest_data)
                if len(rest_data)
                else 0.0
                for name in amenities
            ],
        })
        top["share_difference"] = top["hot_share"] - top["rest_share"]
        top.insert(0, snapshot_col, snapshot)
        top = (
            top.sort_values(
                ["share_difference", "hot_share"],
                ascending=[False, False],
            )
            .head(max(1, int(top_n)))
            .copy()
        )
        top["rank"] = range(1, len(top) + 1)
        top["hot_metric"] = threshold_metric
        top_parts.append(top)

    area_scores = pd.concat(area_parts, ignore_index=True)
    top_amenities = pd.concat(top_parts, ignore_index=True)

    if out_path is not None:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        area_scores.to_csv(out_file, index=False)

    if verbose:
        print_amenities_report(
            area_scores,
            top_amenities,
            snapshot_summaries,
            hot_quantile=hot_quantile,
            area_col=area_col,
            snapshot_col=snapshot_col,
        )

    return {
        "area_scores": area_scores,
        "top_amenities": top_amenities,
    }


def print_amenities_report(
    area_scores,
    top_amenities,
    snapshot_summaries,
    hot_quantile=0.75,
    area_col="neighbourhood_cleansed",
    snapshot_col="snapshot",
):
    """In báo cáo tổng hợp KPI tiện ích."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

    latest_summary = max(snapshot_summaries, key=lambda row: row["snapshot"])
    latest_snapshot = latest_summary["snapshot"]
    latest_areas = area_scores.loc[area_scores[snapshot_col] == latest_snapshot]
    latest_top = top_amenities.loc[
        top_amenities[snapshot_col] == latest_snapshot
    ].sort_values("rank")

    highest = latest_areas.loc[latest_areas["Amenities_Score_Median"].idxmax()]
    lowest = latest_areas.loc[latest_areas["Amenities_Score_Median"].idxmin()]
    hot_metric = latest_summary["hot_metric"]
    threshold_unit = (
        "đêm / năm"
        if hot_metric == "estimated_occupancy_l365d"
        else "ngày trống / năm"
    )

    summary = pd.DataFrame(
        [
            {"Chỉ số": "Số snapshot phân tích", "Giá trị": len(snapshot_summaries), "Đơn vị": "mốc"},
            {"Chỉ số": "Số khu vực", "Giá trị": len(latest_areas), "Đơn vị": "khu vực"},
            {
                "Chỉ số": "Tổng số listing đưa vào KPI (mốc mới nhất)",
                "Giá trị": latest_summary["listing_count"],
                "Đơn vị": "listing",
            },
            {
                "Chỉ số": "Số tiện ích trung vị toàn thành phố",
                "Giá trị": latest_summary["median_amenities_count"],
                "Đơn vị": "tiện ích / listing",
            },
            {
                "Chỉ số": (
                    "Amenities Score trung vị theo khu vực cao nhất: "
                    f"{highest[area_col]}"
                ),
                "Giá trị": highest["Amenities_Score_Median"],
                "Đơn vị": "điểm (100 = trung vị snapshot)",
            },
            {
                "Chỉ số": (
                    "Amenities Score trung vị theo khu vực thấp nhất: "
                    f"{lowest[area_col]}"
                ),
                "Giá trị": lowest["Amenities_Score_Median"],
                "Đơn vị": "điểm (100 = trung vị snapshot)",
            },
            {"Chỉ số": 'Chỉ báo "cháy phòng"', "Giá trị": hot_metric, "Đơn vị": "-"},
            {
                "Chỉ số": "Ngưỡng cháy phòng",
                "Giá trị": latest_summary["hot_threshold"],
                "Đơn vị": threshold_unit,
            },
        ]
    )

    by_snapshot = pd.DataFrame(
        [
            {
                "Snapshot": row["snapshot"],
                "Số listing (listing)": row["listing_count"],
                "Số tiện ích trung vị (tiện ích / listing)": row[
                    "median_amenities_count"
                ],
                "Chỉ báo hot": row["hot_metric"],
                "Ngưỡng hot": row["hot_threshold"],
                "Tỷ lệ nhóm hot thực tế (%)": row["hot_share_pct"],
            }
            for row in snapshot_summaries
        ]
    )

    area_columns = {
        area_col: "Khu vực",
        "n_listings": "Số listing (listing)",
        "median_amenities_count": "Số tiện ích trung vị (tiện ích / listing)",
        "Amenities_Score_Median": "Amenities Score trung vị (điểm)",
    }
    highest_areas = (
        latest_areas.sort_values("Amenities_Score_Median", ascending=False)
        .head(5)
        .assign(**{"Nhóm": "Cao nhất"})
    )
    lowest_areas = (
        latest_areas.sort_values("Amenities_Score_Median", ascending=True)
        .head(5)
        .assign(**{"Nhóm": "Thấp nhất"})
    )
    by_area = pd.concat([highest_areas, lowest_areas], ignore_index=True)
    by_area = by_area.rename(columns=area_columns)[
        [
            "Nhóm",
            "Khu vực",
            "Số listing (listing)",
            "Số tiện ích trung vị (tiện ích / listing)",
            "Amenities Score trung vị (điểm)",
        ]
    ]

    by_amenity = pd.DataFrame(
        {
            "Hạng": latest_top["rank"],
            "Tiện ích": latest_top["amenity"],
            "Tỷ lệ nhóm hot (%)": (latest_top["hot_share"] * 100).round(1),
            "Tỷ lệ nhóm còn lại (%)": (latest_top["rest_share"] * 100).round(1),
            "Chênh lệch (điểm %)": (latest_top["share_difference"] * 100).round(1),
        }
    )

    def print_table(title, table):
        print(title)
        with pd.option_context("display.width", 200, "display.max_columns", None):
            print(table.to_string(index=False))
        print()

    print_table(
        f"=== BẢNG 1. KPI TỔNG HỢP (snapshot mới nhất: {latest_snapshot}) ===",
        summary,
    )
    print_table("=== BẢNG 2. THEO SNAPSHOT (THỜI GIAN) ===", by_snapshot)
    print_table(
        "=== BẢNG 3. KHU VỰC THEO AMENITIES SCORE (mốc mới nhất) ===",
        by_area,
    )
    print(
        f"=== BẢNG 4. TIỆN ÍCH CỦA NHÓM CHÁY PHÒNG SO VỚI CÒN LẠI "
        "(mốc mới nhất) ==="
    )
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(by_amenity.to_string(index=False))
    print(
        f"(*) Nhóm cháy phòng = top {hot_quantile * 100:.0f}% theo chỉ báo trên; "
        "estimated_occupancy_l365d là số ước tính từ review, không phải lượt đặt thật."
    )
