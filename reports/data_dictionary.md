# TỪ ĐIỂN DỮ LIỆU (DATA DICTIONARY) - INSIDE AIRBNB PARIS

Dự án phân tích dữ liệu lưu trú ngắn hạn Paris với 4 mốc thời gian thu thập: **2025-12-13, 2026-03-21, 2026-06-16, 2026-09-16**.

---

## 1. Bảng `listings` (Thông tin Căn hộ / Phòng lưu trú)

| Tên trường | Kiểu dữ liệu | Mô tả ý nghĩa nghiệp vụ |
|---|---|---|
| `id` | `int64` | Khóa chính duy nhất định danh listing phòng trên Airbnb. |
| `name` | `string` | Tên tiêu đề quảng cáo phòng do chủ nhà đặt. |
| `host_id` | `int64` | Khóa ngoại định danh chủ nhà (Host). |
| `host_name` | `string` | Tên hiển thị của chủ nhà. |
| `host_is_superhost` | `boolean` | Cờ đánh dấu chủ nhà có đạt danh hiệu Superhost (Chủ nhà siêu cấp) hay không (`t`/`f`). |
| `host_identity_verified` | `boolean` | Cờ xác thực danh tính chủ nhà qua giấy tờ tùy thân (`t`/`f`). |
| `neighbourhood_cleansed` | `string` | Tên quận hành chính chính thức của Paris (ví dụ: Louvre, Bourse, Buttes-Montmartre, Passy...). |
| `latitude`, `longitude` | `float64` | Tọa độ địa lý (Vĩ độ, Kinh độ) theo hệ quy chiếu WGS84. |
| `property_type` | `string` | Loại hình bất động sản (Entire rental unit, Private room, Loft...). |
| `room_type` | `string` | Loại phòng (Entire home/apt, Private room, Shared room, Hotel room). |
| `accommodates` | `int64` | Sức chứa tối đa số lượng khách lưu trú. |
| `bathrooms`, `bedrooms`, `beds` | `float64` | Số lượng phòng tắm, phòng ngủ và giường. |
| `amenities` | `string (json)` | Danh sách tiện ích phòng ở định dạng mảng JSON string. |
| `price` | `float64` | Giá thuê mỗi đêm bằng đơn vị **EUR** (đã được làm sạch bỏ ký tự `$`, `,`). |
| `minimum_nights`, `maximum_nights` | `int64` | Số đêm thuê tối thiểu và tối đa theo chính sách của chủ nhà. |
| `availability_365` | `int64` | Số ngày phòng sẵn sàng đón khách trong chu kỳ 365 ngày tới [0, 365]. |
| `number_of_reviews` | `int64` | Tổng số lượng đánh giá mà căn hộ nhận được từ khi hoạt động. |
| `number_of_reviews_ltm` | `int64` | Số lượng đánh giá nhận được trong 12 tháng qua. |
| `reviews_per_month` | `float64` | Tốc độ nhận đánh giá trung bình mỗi tháng (thước đo độ năng động). |
| `review_scores_rating` | `float64` | Điểm đánh giá tổng thể (thang điểm 1.0 đến 5.0 sao). |
| `review_scores_cleanliness` | `float64` | Điểm đánh giá khía cạnh sạch sẽ (thang điểm 1.0 đến 5.0). |
| `review_scores_location` | `float64` | Điểm đánh giá vị trí thuận lợi (thang điểm 1.0 đến 5.0). |
| `calculated_host_listings_count` | `int64` | Tổng số lượng listing mà chủ nhà đó sở hữu trong toàn thành phố (chỉ số xác định Pro Host). |
| `estimated_occupancy_l365d` | `float64` | Số đêm có khách ước tính trong 12 tháng qua (ước tính Inside Airbnb). |
| `estimated_revenue_l365d` | `float64` | Doanh thu ước tính trong 12 tháng qua bằng **EUR** (`price` × số đêm ước tính). |
| `flag_*` | `boolean` | Các cờ kiểm soát chất lượng dữ liệu được gán trong quá trình QA (`flag_price_invalid`, `flag_price_outlier`, `flag_any`...). |

---

## 2. Bảng `reviews` (Đánh giá của Khách hàng)

| Tên trường | Kiểu dữ liệu | Mô tả ý nghĩa nghiệp vụ |
|---|---|---|
| `listing_id` | `int64` | Khóa ngoại tham chiếu đến căn hộ được đánh giá. |
| `id` | `int64` | Khóa chính duy nhất định danh bản ghi review. |
| `date` | `date` | Ngày khách gửi đánh giá (định dạng chuẩn `YYYY-MM-DD`). |
| `reviewer_id` | `int64` | Khóa định danh tài khoản du khách để lại đánh giá. |
| `reviewer_name` | `string` | Tên du khách. |
| `comments` | `string` | Toàn văn nội dung nhận xét gốc của khách (có thể chứa mã HTML thô). |
| `comment_clean` | `string` | Nội dung nhận xét đã được bóc sạch thẻ HTML, giải mã thực thể và chuẩn hóa khoảng trắng. |
| `flag_*` | `boolean` | Cờ QA: `flag_html_in_comments`, `flag_empty_comments`, `flag_missing_ids`, `flag_invalid_date`, `flag_any`. |

---

## 3. Bảng `calendar` (Lịch khả dụng & Đặt phòng 365 ngày)

| Tên trường | Kiểu dữ liệu | Mô tả ý nghĩa nghiệp vụ |
|---|---|---|
| `listing_id` | `int64` | Khóa ngoại tham chiếu căn hộ. |
| `date` | `date` | Ngày cụ thể trong lịch quan sát 365 ngày tới (`YYYY-MM-DD`). |
| `available` | `boolean` | Trạng thái phòng trong ngày: `t` (Còn trống / sẵn sàng đón khách), `f` (Đã được đặt hoặc chủ nhà khóa lịch). |
| `price` | `float64` | Giá niêm yết cụ thể áp dụng cho ngày hôm đó (EUR). |
| `minimum_nights` | `int64` | Số đêm tối thiểu áp dụng riêng cho ngày đặt đó. |
| `maximum_nights` | `int64` | Số đêm tối đa áp dụng riêng cho ngày đặt đó. |
| `flag_key_overlap` | `boolean` | Cờ ghi nhận ngày quan sát bị giao thoa giữa các snapshot định kỳ 3 tháng. |
| `flag_conflict_across_snapshots` | `boolean` | Cờ phát hiện sự điều chỉnh giá hoặc chính sách phòng của chủ nhà đối với cùng một ngày tương lai giữa 2 lần cào. |
| `flag_duplicate_across_snapshots` | `boolean` | Cờ ghi nhận bản ghi tĩnh không có bất kỳ thay đổi nào qua các chu kỳ. |
| `flag_any` | `boolean` | Cờ tổng hợp lỗi kỹ thuật (thiếu trường, sai kiểu, ngoại lai số đêm). |
