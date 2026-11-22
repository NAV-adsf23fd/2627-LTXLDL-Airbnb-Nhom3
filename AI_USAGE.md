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
