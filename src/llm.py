import json
import os
from typing import Literal

from google.genai.types import JOB_STATES_ENDED, JOB_STATES_SUCCEEDED
import pandas as pd
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"
HAS_KEY = bool(KEY)

batch_job_name = None

client = genai.Client(api_key=KEY)
review = pd.read_csv("data/test/lmm.csv")

# tra_loi = client.models.generate_content(
#     model=MODEL,
#     contents="Trong một câu: đánh giá này khen gì, chê gì? Great location, so noisy.",
# )
# print(tra_loi.text)
Aspect = Literal[
    "location",
    "cleanliness",
    "host",
    "value",
    "noise",
    "amenities",
    "safty",
    "neighbors",
]


class ReviewInfo(BaseModel):
    sentiment: Literal["positive", "mixed", "negative"]
    aspects_positive: list[Aspect]  # khía cạnh được khen
    aspects_negative: list[Aspect]  # khía cạnh bị chê
    language: str = Field(
        description=('Mã ISO 639-1, vd "en", "es"; "und" nếu không xác định được')
    )


print(list(ReviewInfo.model_json_schema()["properties"]))


PROMPT_TEMPLATE = (
    "Bạn là công cụ trích xuất thông tin từ đánh giá về chỗ ở.\n"
    "Phân tích đánh giá sau và điền đúng schema. "
    "Chỉ gán khía cạnh THỰC SỰ được nhắc đến;\n"
    'đánh giá không có nội dung thì trả sentiment "mixed" '
    "và các danh sách rỗng.\n\n"
    "Review: {text}"
)


def ValidateLLM(json_input):
    try:
        ReviewInfo.model_validate_json(json_input)
    except ValidationError as loi:
        for e in loi.errors():
            print(e["type"], e["loc"])


# with open("data/test/llm.csv", "r", encoding="utf-8") as f:
#     LLM_CSV = json.load(f)

# LLM_CACHE = {} if HAS_KEY else dict(LLM_OUTPUT)


def OutputProcessing():
    pass


def RunLLM(reviews):
    with open("data/processed/batch_requests.jsonl", "w", encoding="utf-8") as f:
        for index, row in reviews.iterrows():
            request = {
                "key": str(index),
                "request": {
                    "contents": [
                        {
                            "parts": [
                                {"text": PROMPT_TEMPLATE.format(text=row["comments"])}
                            ]
                        }
                    ],
                    "generation_config": {
                        "response_mime_type": "application/json",
                        "response_schema": ReviewInfo.model_json_schema(),
                    },
                },
            }
            f.write(json.dumps(request) + "\n")

    batch_file = client.files.upload(file="data/processed/batch_requests.jsonl")
    assert batch_file.name is not None, "Upload batch_requests.jsonl that bai"

    global batch_job_name
    batch_job = client.batches.create(
        model=MODEL,
        src=batch_file.name,
        config={"display_name": "ltxldx-paris-review"},
    )
    batch_job_name = batch_job.name
    print(f"Created job: {batch_job_name}")


def GetLLMOutput():
    if batch_job_name is None:
        return

    batch_job = client.batches.get(name=batch_job_name)

    assert batch_job is not None, "batch_job is None"
    print(f"Polling status for job: {batch_job_name}")
    assert batch_job.state is not None, "batch_job.state is None"

    if batch_job.state.name == "JOB_STATE_SUCCEEDED":
        assert batch_job.dest is not None, "batch_job.dest is None"
        result_file_name = batch_job.dest.file_name
        print(f"Results are in file: {result_file_name}")

        assert result_file_name is not None, "result_file_name is None"
        print("Downloading result file content...")
        file_content = client.files.download(file=result_file_name)
        content_str = file_content.decode("utf-8")

        with open("data/processed/batch_output.jsonl", "w", encoding="utf-8") as f:
            f.write(content_str)
            print("Saved data/processed/batch_output.jsonl")

    else:
        print(f"Job did not succeed. Final state: {batch_job.state.name}")
        if batch_job.error:
            print(f"Error: {batch_job.error}")
