import json
import os
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
    global USER_PROMPT
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

    USER_PROMPT = f"Phân tích toàn bộ reviews trong đối tượng JSON này:\n\n{json.dumps(reviews['comments'].to_dict(), ensure_ascii=False)}"


def GetReviews():
    team_review = pd.read_csv(Team.reviews)
    review_list = []

    for t in CONFIG.snapshots:
        time = t.strftime("%Y-%m-%d")
        rv = pd.read_csv(Raw.reviews[time]).set_index("id")["comments"]
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
    response = client.models.generate_content(
        model=MODEL,
        contents=USER_PROMPT,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=BatchReviewOutput,
            temperature=0.1,
        ),
    )
    assert response.text is not None, "response is None"

    parsed_json = json.loads(response.text)
    with open(Llm.files["response"], "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, ensure_ascii=False, indent=4)
