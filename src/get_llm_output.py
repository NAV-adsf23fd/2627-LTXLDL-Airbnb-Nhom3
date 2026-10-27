import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=KEY)

job = client.batches.get(name="abc")

print(job.state)


if job.state == "JOB_STATE_SUCCEEDED":
    print("Xử lý xong! Đang tải kết quả về...")

    # 1. Lấy thông tin nơi chứa file kết quả
    # Thông thường, API sẽ gán đường dẫn file vào thuộc tính output_uri
    ket_qua_uri = job.output_uri
    print(f"Đường dẫn file trên cloud: {ket_qua_uri}")

    # 2. Tải file về (Tùy theo loại URI hệ thống trả về)

    # TRƯỜNG HỢP A: Nếu hệ thống dùng File API mặc định của Gemini
    # (Thường URI có dạng file hoặc được quản lý bởi client.files)
    try:
        # Tải nội dung từ cloud về
        response = client.files.get(name=ket_qua_uri)  # Hoặc client.files.download

        # Ghi ra một file jsonl trên máy tính của bạn
        with open("data/test/batch_output.jsonl", "wb") as f:
            f.write(response.content)
        print("Đã tải xong file batch_output.jsonl!")

    except Exception as e:
        print("Lỗi khi dùng File API tải về:", e)


ket_qua_hop_le = {}

# Đọc file kết quả tải về
with open("batch_output.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        ma = data["custom_id"]  # ID dòng ban đầu
        chuoi_json = data["response"]["body"]["candidates"][0]["content"]["parts"][0][
            "text"
        ]

        # Bắt buộc dùng Pydantic kiểm tra lại xem AI trả về có đúng format không
        try:
            r = ReviewInfo.model_validate_json(chuoi_json)
            ket_qua_hop_le[ma] = r
        except Exception as e:
            print(f"Lỗi format ở dòng {ma}")

# Đưa ngược vào DataFrame để phân tích tiếp
bang = {ma: r.model_dump() for ma, r in ket_qua_hop_le.items()}
nhan_df = pd.DataFrame.from_dict(bang, orient="index")
