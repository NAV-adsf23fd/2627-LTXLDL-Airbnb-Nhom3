# BẢN KHAI BÁO SỬ DỤNG TRÍ TUỆ NHÂN TẠO (AI USAGE STATEMENT)

**Môn học:** Lập trình xử lý dữ liệu (UET.DSE2049 4)  
**Nhóm sinh viên:** Nhóm 3 - Thị trường Paris  
**Dự án:** Phân tích Dữ liệu Lưu trú Ngắn hạn Inside Airbnb Paris phục vụ Cơ quan Quản lý Đô thị và Hiệp hội Du lịch Île-de-France  

---

## 1. Nguyên tắc Sử dụng AI có Trách nhiệm
Nhóm cam kết tuân thủ nghiêm ngặt chuẩn mực liêm chính học thuật và đạo đức nghề nghiệp:
- **Con người làm chủ (Human-in-the-loop):** Toàn bộ bài toán nghiệp vụ, thiết kế kiến trúc pipeline, logic kiểm định QA, bộ công thức tính toán 5 KPI và các nhận định kinh doanh cốt lõi do các thành viên nhóm thảo luận, xây dựng và chịu trách nhiệm 100%.
- **AI đóng vai trò trợ lý tăng cường (Augmented Intelligence):** Các mô hình AI được sử dụng có chủ đích nhằm giải quyết các bài toán xử lý ngôn ngữ tự nhiên (NLP) phức tạp và hỗ trợ rà soát, tối ưu cú pháp mã nguồn.

---

## 2. Các Mô hình và Công cụ AI đã Sử dụng

| Công cụ / Mô hình | Nhà cung cấp | Mục đích sử dụng cụ thể |
|---|---|---|
| **Gemini API (`gemini-3.5-flash-lite`)** | Google | Trích xuất cảm xúc (`sentiment`: positive/negative/mixed) và 7 khía cạnh dịch vụ (`aspects`: vị trí, sạch sẽ, chủ nhà, tiện nghi, giá trị, độ ồn, an toàn) từ bình luận du khách (`src/llm.py`). |
| **Antigravity / Coding Assistant** | Google DeepMind | Hỗ trợ gợi ý cú pháp Python (NumPy, Pandas vectorization, regex bóc tách HTML), format báo cáo và rà soát lỗi tương thích môi trường. |

---

## 3. Quy trình Kiểm định & Phòng chống Ảo giác (Anti-Hallucination)
Để đảm bảo kết quả trích xuất của LLM phản ánh đúng sự thật và không bị "ảo giác" (hallucination):
1. **Kiểm chứng trên tập nhãn tay (Ground Truth):** Nhóm đã tự tay gán nhãn độc lập cho **100 bình luận ngẫu nhiên** (`data/llm/label.json`) từ 4 snapshot để làm chuẩn đối chứng.
2. **Xây dựng mô hình Baseline đối chứng độc lập:** Nhóm lập trình một mô hình dựa trên quy tắc từ điển và biểu thức chính quy (Rule-based Regex) tại `src/baseline.py`.
3. **Đánh giá định lượng khắt khe (`src/evaluate.py`):**
   - **Sentiment Accuracy:** LLM đạt **90.0%** (vượt trội so với Baseline 82.0%).
   - **Aspect Extraction (Positive):** LLM đạt **F1-Score 77.52%** (Precision 84.92%, Recall 71.31%), cao hơn Baseline (F1-Score 67.83%).
   - **Đánh giá lỗi sai:** Nhóm đã phân tích ma trận nhầm lẫn (Confusion Matrix) để hiểu rõ các trường hợp LLM phân loại nhầm giữa cảm xúc "positive" và "mixed".

---

## 4. Bảo mật Dữ liệu & Đạo đức Sử dụng Khóa API
- Tuyệt đối **không commit khóa API thật** lên kho mã nguồn Git. Mọi khóa API được tải an toàn qua biến môi trường `.env` (mẫu tại `.env.example`).
- File cấu hình `.gitignore` đã chặn toàn bộ `.env`, `data/raw/` và các tệp sinh ra tự động để đảm bảo an toàn thông tin và bản quyền dữ liệu Inside Airbnb.

---

## 5. Công cụ đã dùng (vào việc gì)
Trong quá trình thực hiện dự án, nhóm đã linh hoạt sử dụng kết hợp các công cụ AI sau để tối ưu hóa hiệu suất làm việc:
*   **Claude:** Hỗ trợ viết code cấu trúc dữ liệu, xử lý logic các file xử lý dữ liệu phức tạp.
*   **Gemini:** Hỗ trợ phân tích ngữ cảnh, gỡ lỗi (debug) và tra cứu nhanh các lỗi phát sinh trong quá trình chạy script.
*   **ChatGPT:** Lên ý tưởng (brainstorm), viết khung code cho các module tính toán KPI và hỗ trợ thiết kế cấu trúc biểu đồ matplotlib.

---

## 6. Các Prompt then chốt
Dưới đây là 5 câu lệnh (prompt) quan trọng nhất nhóm đã sử dụng để định hình kiến trúc và giải quyết các bài toán chính của dự án:

1.  **Thiết lập tính toán KPI ban đầu** 
    *   **Prompt:** *"Từ file csv hãy viết code python cho tôi để ra kết quả kpi như ảnh thứ nhất, vẽ sơ đồ bằng mathplotlib và cho tôi biết bạn dùng các cột nào trong file csv để phục vụ tính toán."*
    *   **Áp dụng:** File `kpi.py` và module vẽ biểu đồ ban đầu.
2.  **Tối ưu hóa kiến trúc dự án**
    *   **Prompt:** *"Có cách nào để tách phần code tính toán và code vẽ biểu đồ thành 2 file riêng biệt trong một dự án mà không ảnh hưởng gì đến kết quả không?"*
    *   **Áp dụng:** Tách logic ra file `viz.py` và `kpi.py`.
3.  **Kiểm tra và review code**
    *   **Prompt:** *"Kiểm tra xem code này của tôi đã phù hợp với yêu cầu KPI mà tôi gửi lúc nãy chưa."*
    *   **Áp dụng:** File `kpi.py` (để review và tinh chỉnh logic tính toán).
4.  **Lên quy trình cho KPI phức tạp & Ứng dụng LLM**
    *   **Prompt:** *"Tôi cần thực hiện những bước nào để làm KPI 'Đánh giá chất lượng dịch vụ thực tế dưới góc nhìn của khách thuê'. Tôi muốn phân nhóm các căn hộ theo sao (< 4 sao, 4-4.5 sao, > 4.5 sao). Và tôi cũng muốn ứng dụng với LLM."*
    *   **Áp dụng:** File `kpi.py` (xử lý logic phân cụm và tích hợp AI đánh giá).
5.  **Thiết kế module Data Quality (QA)**
    *   **Prompt:** *"Hãy giúp tôi thiết kế và hoàn thiện lớp QAListing trong module qa.py để thực hiện kiểm tra chất lượng (QA) và làm sạch bảng dữ liệu listings của Airbnb."*
    *   **Áp dụng:** File `qa.py` và luồng làm sạch dữ liệu đầu vào.

---

## 7. AI sai ở đâu (Ví dụ thực tế)
Dù hỗ trợ rất tốt trong việc sinh code, AI vẫn gặp sai sót trong dự án thực tế của nhóm:
*   **Vấn đề đánh giá bằng LLM:** Khi nhóm yêu cầu AI ứng dụng mô hình ngôn ngữ lớn (LLM) để đánh giá các phản hồi/review, kết quả trả về chưa thực sự chuẩn xác. 
*   **Ví dụ cụ thể:** AI dùng phản hồi thuần (raw output) từ LLM một cách máy móc, dẫn đến việc phân loại không nhất quán (đôi khi bối cảnh đánh giá của khách là tích cực nhưng có dùng từ ngữ dễ gây nhầm lẫn thì LLM vẫn phân loại sai). Nhóm đã phải can thiệp để làm sạch kết quả trả về của LLM trước khi đưa vào phân nhóm.

---

## 8. Nhóm kiểm chứng thế nào
Để đảm bảo chất lượng và độ tin cậy của code do AI sinh ra, nhóm đã áp dụng quy trình kiểm chứng nghiêm ngặt:
1.  **Chạy thử độc lập:** Copy nguyên bản code được render từ AI vào một môi trường/file test độc lập để chạy thử.
2.  **Đối chiếu kết quả (Cross-check):** Kiểm tra đối chiếu output của code AI sinh ra với bảng dữ liệu CSV và các chỉ số tính toán thủ công xem có khớp không.
3.  **Xác định lỗi/Thiếu sót:** Tìm ra các bug, các trường hợp (edge cases) mà AI chưa tính tới hoặc xử lý sai logic nghiệp vụ.
4.  **Tinh chỉnh (Iterative Prompting):** Dùng chính lỗi phát hiện được để prompt lại AI, yêu cầu sửa lỗi. Quá trình này lặp đi lặp lại cho đến khi đoạn code chạy hoàn hảo và đáp ứng đúng 100% yêu cầu đặt ra mới được đưa vào dự án chính.