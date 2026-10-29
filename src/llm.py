import json
import os
import time
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"
HAS_KEY = bool(KEY)


client = genai.Client(api_key=KEY)
review = pd.read_csv("data/test/lmm.csv")


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


PROMPT_TEMPLATE = (
    "Bạn là công cụ trích xuất thông tin từ đánh giá về chỗ ở.\n"
    "Phân tích đánh giá sau và điền đúng schema. "
    "Chỉ gán khía cạnh THỰC SỰ được nhắc đến;\n"
    'đánh giá không có nội dung thì trả sentiment "mixed" '
    "và các danh sách rỗng."
)


def Test():
    tra_loi = client.interactions.create(
        model=MODEL,
        input="Trong một câu: đánh giá này khen gì, chê gì? Great location, so noisy.",
    )
    print(tra_loi.output_text)


def ValidateLLM(json_input, valid_results):
    id = json_input["key"]

    if "error" in json_input:
        print(f"Lỗi API tại key {id}: {json_input['error']}")
        return

    json_string = json_input["response"]["candidates"][0]["content"]["parts"][0]["text"]
    try:
        r = ReviewInfo.model_validate_json(json_string)
        valid_results[id] = r
    except ValidationError as loi:
        print(f"Lỗi validate tại key {id}:")
        for e in loi.errors():
            print(e["type"], e["loc"])


def OutputProcessing():
    valid_results = {}
    with open("data/processed/batch_output.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                ValidateLLM(json.loads(line), valid_results)

    dict_results = {k: v.model_dump() for k, v in valid_results.items()}
    with open("data/processed/llm_cache.json", "w", encoding="utf-8") as f:
        json.dump(dict_results, f, indent=4, ensure_ascii=False)


def MakeLLMRequest(reviews):
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/batch_requests.jsonl", "w", encoding="utf-8") as f:
        for index, row in reviews.to_frame().iterrows():
            request = {
                "key": str(index),
                "request": {
                    "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                    "contents": [{"parts": [{"text": str(row["comments"])}]}],
                    "generation_config": {
                        "response_mime_type": "application/json",
                        "response_schema": ReviewInfo.model_json_schema(),
                    },
                },
            }
            f.write(json.dumps(request) + "\n")


def RunLLM():
    batch_file = client.files.upload(
        file="data/processed/batch_requests.jsonl",
        config=types.UploadFileConfig(
            display_name="my-batch-requests", mime_type="jsonl"
        ),
    )
    assert batch_file.name is not None, "Upload batch_requests.jsonl that bai"
    assert batch_file.state is not None, "batch_file.state is None"
    assert batch_file.state.name is not None, "batch_file.state.name is None"
    print("Uploaded file succeesfully")

    while batch_file.state.name == "PROCESSING":
        assert batch_file.name is not None, "Upload batch_requests.jsonl that bai"

        time.sleep(2)
        batch_file = client.files.get(name=batch_file.name)
        assert batch_file.state is not None, "batch_file.state is None"

    assert (batch_file.state.name == "FAILED") is not True, (
        "Failed to upload batch_file"
    )

    print("Processed file succeesfully")

    assert batch_file.name is not None, "batch_file is None"
    batch_job = client.batches.create(
        model=MODEL,
        src=batch_file.name,
        config={"display_name": "ltxldx-paris-review"},
    )
    print("Created batch job succeesfully")
    batch_job_name = batch_job.name
    assert batch_job_name is not None, "batch_job_name is None"
    with open("configs/batch_job_name.txt", "w", encoding="utf-8") as f:
        f.write(batch_job_name)
    print(f"Created job: {batch_job_name}")


def QuickCheckBatch():
    with open("configs/batch_job_name", "r", encoding="utf-8") as f:
        batch_job_name = f.read()

    if batch_job_name is None:
        print("Invalid batch_job_name")
        return

    batch_job = client.batches.get(name=batch_job_name)
    assert batch_job.state is not None, "Invalid batch_job_name.state"
    print(batch_job.state.name)


def GetLLMOutput():
    with open("configs/batch_job_name", "r", encoding="utf-8") as f:
        batch_job_name = f.read()
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
