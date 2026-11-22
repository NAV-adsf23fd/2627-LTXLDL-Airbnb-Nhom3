import json
import os
import time  # Thêm thư viện time để sleep
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.utility import CONFIG, Llm, Raw, Team

Aspect = Literal[
    "location",
    "cleanliness",
    "host",
    "value",
    "noise",
    "amenities",
    "safety",
    "neighbors",
]


class ReviewInfo(BaseModel):
    sentiment: Literal["positive", "mixed", "negative"]
    aspects_positive: list[Aspect]  # khía cạnh được khen
    aspects_negative: list[Aspect]  # khía cạnh bị chê
    language: str = Field(
        description=('Mã ISO 639-1, vd "en", "es"; "und" nếu không xác định được')
    )


class IdentifiableReview(BaseModel):
    review_id: str = Field(
        description="Mã ID chuỗi gốc của đánh giá lấy từ dữ liệu đầu vào"
    )
    info: ReviewInfo


class BatchReviewOutput(BaseModel):
    results: list[IdentifiableReview] = Field(
        description="Danh sách kết quả phân tích cho từng đánh giá đầu vào."
    )


def Init():
    global reviews
    global SYSTEM_INSTRUCTION
    global KEY
    global MODEL
    global client

    load_dotenv()

    KEY = os.getenv("GEMINI_API_KEY")
    MODEL = "gemini-3.5-flash-lite"
    client = genai.Client(api_key=KEY)

    reviews = pd.read_csv(Llm.files["reviews"]).set_index("review_id")

    SYSTEM_INSTRUCTION = (
        "Bạn là công cụ trích xuất thông tin từ đánh giá về chỗ ở.\n"
        "Phân tích đánh giá sau và điền đúng schema. "
        "Chỉ gán khía cạnh THỰC SỰ được nhắc đến;\n"
        'đánh giá không có nội dung thì trả sentiment "mixed" '
        "và các danh sách rỗng.\n"
        "Bạn phải đánh giá toàn bộ item trong input đối tượng JSON và bắt buộc phải điền chính xác mã ID tương ứng vào thuộc tính 'review_id' của từng phần tử."
    )
    # Đã xóa biến USER_PROMPT ở đây vì sẽ tạo động trong vòng lặp


def GetReviews():
    team_review = pd.read_csv(Team.reviews)
    review_list = []

    for t in CONFIG.snapshots:
        time_str = t.strftime("%Y-%m-%d")
        rv = pd.read_csv(Raw.reviews[time_str]).set_index("id")["comments"]
        rv = rv.to_frame().merge(
            team_review[["review_id", "Mẫu LLM"]],
            left_on="id",
            right_on="review_id",
            how="right",
        )
        rv = rv[rv["Mẫu LLM"].notna()].drop(columns=["Mẫu LLM"])
        review_list.append(rv)

    reviews = (
        pd.concat(review_list, axis=0, ignore_index=False)
        .drop_duplicates(subset=["review_id"], keep="last")
        .set_index("review_id")
        .dropna()
    )
    reviews["comments"] = reviews["comments"].str.replace(r"\r?<br/>", "", regex=True)

    reviews.to_csv(Llm.files["reviews"])


def RunLLM():
    all_results = []
    batch_size = 20  # Số lượng review xử lý mỗi lần (20 là an toàn cho free tier)

    # Chuyển DataFrame thành list các cặp (review_id, comment)
    review_items = list(reviews["comments"].to_dict().items())
    total_batches = (len(review_items) + batch_size - 1) // batch_size

    print(f"Bắt đầu xử lý {len(review_items)} reviews trong {total_batches} batches...")

    for i in range(0, len(review_items), batch_size):
        batch = dict(review_items[i : i + batch_size])
        prompt = f"Phân tích toàn bộ reviews trong đối tượng JSON này:\n\n{json.dumps(batch, ensure_ascii=False)}"

        print(f"  -> Đang xử lý batch {i // batch_size + 1} / {total_batches}...")

        # Thử lại tối đa 3 lần nếu có lỗi mạng hoặc rate limit
        success = False
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=BatchReviewOutput,
                        temperature=0.1,
                    ),
                )

                if response.text:
                    parsed_json = json.loads(response.text)
                    # Nối kết quả của batch này vào danh sách tổng
                    all_results.extend(parsed_json.get("results", []))
                    success = True
                    break  # Thành công thì thoát vòng lặp thử lại

            except Exception as e:
                print(
                    f"     [!] Lỗi batch {i // batch_size + 1} (Lần thử {attempt + 1}/3): {e}"
                )
                time.sleep(5)  # Đợi 5 giây rồi thử lại

        if not success:
            print(f"     [X] Bỏ qua batch {i // batch_size + 1} sau 3 lần thử.")

        # Nghỉ 2 giây giữa các batch để tránh bị chặn 429 (Rate Limit)
        time.sleep(2)

    # Lưu toàn bộ kết quả ra file
    with open(Llm.files["test_response"], "w", encoding="utf-8") as f:
        json.dump({"results": all_results}, f, ensure_ascii=False, indent=4)

    print(
        f"✅ Đã hoàn thành! Tổng cộng lưu được {len(all_results)} kết quả vào {Llm.files['response']}"
    )
