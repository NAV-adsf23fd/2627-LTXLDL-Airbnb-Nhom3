import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ASPECT_FIELDS = ("aspects_positive", "aspects_negative")


def _norm_str(val):
    return str(val).strip().lower() if val is not None else ""


def _norm_aspects(val):
    if not isinstance(val, list):
        return set()
    return {str(x).strip().lower() for x in val if x is not None and str(x).strip()}


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("results", data) if isinstance(data, dict) else data
    return {
        str(r["review_id"]).strip(): r.get("info", {})
        for r in items
        if str(r.get("review_id", "")).strip()
    }


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def evaluate(label, pred):
    # Chỉ chấm các review có nhãn tay
    ids = [i for i in label if i in pred]
    missing = [i for i in label if i not in pred]
    n = len(ids)

    if n == 0:
        raise ValueError(
            "Không có review_id nào trùng giữa file nhãn tay và file dự đoán."
        )

    out = {"n": n, "missing": missing}

    # 1) Sentiment: accuracy + confusion
    correct = 0
    confusion = defaultdict(int)
    for i in ids:
        g = _norm_str(label[i].get("sentiment"))
        p = _norm_str(pred[i].get("sentiment"))
        correct += g == p
        confusion[(g, p)] += 1
    out["sentiment_acc"] = correct / n
    out["confusion"] = dict(confusion)

    # 2) Language: accuracy
    out["language_acc"] = (
        sum(
            _norm_str(label[i].get("language")) == _norm_str(pred[i].get("language"))
            for i in ids
        )
        / n
    )

    # 3) Aspects: P/R/F1 (micro) và theo từng aspect
    for field in ASPECT_FIELDS:
        tp = fp = fn = 0
        per = defaultdict(lambda: [0, 0, 0])  # aspect -> [tp, fp, fn]
        exact = 0
        for i in ids:
            g, p = _norm_aspects(label[i].get(field)), _norm_aspects(pred[i].get(field))
            tp += len(g & p)
            fp += len(p - g)
            fn += len(g - p)
            exact += g == p
            for a in g & p:
                per[a][0] += 1
            for a in p - g:
                per[a][1] += 1
            for a in g - p:
                per[a][2] += 1
        P, R, F = prf(tp, fp, fn)
        out[field] = {
            "precision": P,
            "recall": R,
            "f1": F,
            "exact_match": exact / n,
            "per_aspect": {a: prf(*v) + (v[0] + v[2],) for a, v in sorted(per.items())},
        }
    return out


def report(res):
    print(f"Số review chấm: {res['n']}  (thiếu trong dự đoán: {len(res['missing'])})")
    print(f"\nSentiment accuracy : {res['sentiment_acc']:.2%}")
    print(f"Language accuracy  : {res['language_acc']:.2%}")
    print("\nConfusion sentiment (nhãn tay -> dự đoán):")
    for (g, p), c in sorted(res["confusion"].items()):
        print(f"  {g:>8} -> {p:<8} {c}")
    for field in ASPECT_FIELDS:
        r = res[field]
        print(
            f"\n[{field}]  P={r['precision']:.2%}  R={r['recall']:.2%}  "
            f"F1={r['f1']:.2%}  exact-match={r['exact_match']:.2%}"
        )
        print(f"  {'aspect':<13}{'P':>8}{'R':>8}{'F1':>8}{'support':>9}")
        for a, (p, rc, f1, sup) in r["per_aspect"].items():
            print(f"  {a:<13}{p:>8.2%}{rc:>8.2%}{f1:>8.2%}{sup:>9}")


def plot_evaluation(resllm, resbaseline, out_path="figures/eval_comparison.png"):
    """Vẽ biểu đồ so sánh LLM và Baseline."""

    # Tạo thư mục nếu chưa có
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    # Thiết lập giao diện biểu đồ
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(
        "So sánh hiệu năng: LLM vs Baseline (Regex)", fontsize=16, fontweight="bold"
    )

    # --- BIỂU ĐỒ 1: Sentiment Accuracy ---
    acc_data = pd.DataFrame(
        {
            "Model": ["LLM", "Baseline"],
            "Accuracy": [resllm["sentiment_acc"], resbaseline["sentiment_acc"]],
        }
    )
    acc_data.plot(
        kind="bar",
        x="Model",
        y="Accuracy",
        ax=axes[0],
        color=["#4C72B0", "#DD8452"],
        legend=False,
    )
    axes[0].set_title("Sentiment Accuracy", fontsize=14)
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Tỷ lệ đúng")
    axes[0].set_xticklabels(["LLM", "Baseline"], rotation=0)
    # Ghi số liệu lên đầu cột
    for p in axes[0].patches:
        axes[0].annotate(
            f"{p.get_height():.2%}",
            (p.get_x() + p.get_width() / 2.0, p.get_height()),
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    # Hàm phụ trợ để vẽ biểu đồ Aspect F1
    def plot_aspect_f1(field, title, ax):
        # Lấy dữ liệu F1 của từng aspect
        llm_data = {a: v[2] for a, v in resllm[field]["per_aspect"].items()}
        base_data = {a: v[2] for a, v in resbaseline[field]["per_aspect"].items()}

        # Gộp vào DataFrame (đảm bảo hiển thị đủ aspect kể cả khi 1 model bị thiếu)
        df = pd.DataFrame({"LLM": llm_data, "Baseline": base_data}).fillna(0)

        # Vẽ
        df.plot(kind="bar", ax=ax, color=["#4C72B0", "#DD8452"])
        ax.set_title(title, fontsize=14)
        ax.set_ylim(0, 1)
        ax.set_ylabel("F1-Score")
        ax.set_xticklabels(df.index, rotation=45, ha="right")
        ax.legend(title="Model")

    # --- BIỂU ĐỒ 2 & 3: Aspect F1 ---
    plot_aspect_f1("aspects_positive", "F1-Score: Aspects Positive (Khen)", axes[1])
    plot_aspect_f1("aspects_negative", "F1-Score: Aspects Negative (Chê)", axes[2])

    # Căn chỉnh khoảng cách
    plt.tight_layout()

    # Lưu file
    plt.savefig(out_path, dpi=300, bbox_inches="tight")


def RunEvaluate():
    label = load("data/llm/label.json")
    llm = load("data/llm/llm-response.json")
    baseline = load("data/llm/baseline-comments.json")

    resllm = evaluate(label, llm)
    report(resllm)

    resbaseline = evaluate(label, baseline)
    report(resbaseline)

    res_serializable_llm = dict(resllm)
    res_serializable_llm["confusion"] = {
        f"{g}->{p}": c for (g, p), c in resllm["confusion"].items()
    }

    res_serializable_baseline = dict(resbaseline)
    res_serializable_baseline["confusion"] = {
        f"{g}->{p}": c for (g, p), c in resbaseline["confusion"].items()
    }
    with open("data/llm/out_evaluate_llm.json", "w", encoding="utf-8") as f:
        json.dump(res_serializable_llm, f, ensure_ascii=False, indent=2)

    with open("data/llm/out_evaluate_baseline.json", "w", encoding="utf-8") as f:
        json.dump(res_serializable_baseline, f, ensure_ascii=False, indent=2)

    plot_evaluation(resllm, resbaseline, out_path="figures/eval_comparison.png")
