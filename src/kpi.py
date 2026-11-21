def Thai():
    pass


def Van():
    pass


def Tan():
    pass


def Tuan():
    pass


def thanh(
    listings,
    area_col="neighbourhood_cleansed",
    snapshot_col="snapshot",
    hot_quantile=0.75,
    top_n=5,
    out_path="data/processed/kpi_amenities.csv",
    verbose=True,
):
    """Tính KPI tiện ích; nhận bảng listings đã được QA và lọc."""
    import json
    from pathlib import Path

    import pandas as pd

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

    return {
        "area_scores": area_scores,
        "top_amenities": top_amenities,
    }
