# Nhóm 3 - Lập trình xử lý dữ liệu - Paris

Python version

```
3.12.14
```

Chạy pipeline với lần chạy đã lưu gần nhất, nếu không có sẽ tự động thoát
```
python run_pipeline.py
```

Lưu flags cho lần chạy này
```
--save-flags
```


Chạy với config

```
-c, --config
```

Thêm bước tải dữ liệu

```
-d, --download
```

Thêm bước chạy LLM

```
-l, --llm
```

In log chi tiết
```
-v, --verbose
```

Thêm bước lọc mẫu 
```
-f, --filter
```

Chạy qa
```
-q, --qa
```

### Để chạy LLM
Copy .env.example 
```
cp .env.example .env
```

Mở file .env điền API. Ví dụ
```
GEMINI_API_KEY="ABCXYZ"
```
