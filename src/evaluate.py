import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ASPECT_FIELDS = ("aspects_positive", "aspects_negative")


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data["results"]
    return {r["review_id"]: r.get("info", {}) for r in items}


def P_R_FScore(tp, fp, fn):  # true positive, false positive, false negative
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1_score = (
        2 * precision * recall / (precision + recall) if precision + recall else 0.0
    )
    return precision, recall, f1_score


def Evaluate(label, prediction):
    # Chỉ chấm các review có nhãn tay
    ids = [i for i in label if i in prediction]
    missing = [i for i in label if i not in prediction]
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
        label_sentiment = label[i].get("sentiment")
        prediction_sentiment = prediction[i].get("sentiment")

        if label_sentiment == prediction_sentiment:
            correct += 1

        confusion[(label_sentiment, prediction_sentiment)] += 1
    out["sentiment_accuracy"] = correct / n
    out["confusion"] = dict(confusion)

    # 2) Aspects: P/R/F1 (micro) và theo từng aspect
    for field in ASPECT_FIELDS:
        tp = fp = fn = 0
        per_aspect = defaultdict(lambda: [0, 0, 0])  # aspect -> [tp, fp, fn]
        exact = 0
        for i in ids:
            label_sentiment, prediction_sentiment = (
                set(label[i].get(field) or []),
                set(prediction[i].get(field) or []),
            )
            tp += len(label_sentiment & prediction_sentiment)
            fp += len(prediction_sentiment - label_sentiment)
            fn += len(label_sentiment - prediction_sentiment)

            if label_sentiment == prediction_sentiment:
                exact += 1

            for aspect in label_sentiment & prediction_sentiment:
                per_aspect[aspect][0] += 1
            for aspect in prediction_sentiment - label_sentiment:
                per_aspect[aspect][1] += 1
            for aspect in label_sentiment - prediction_sentiment:
                per_aspect[aspect][2] += 1

        P, R, F = P_R_FScore(tp, fp, fn)
        out[field] = {
            "precision": P,
            "recall": R,
            "f1": F,
            "exact_match": exact / n,
            "per_aspect": {
                aspect: P_R_FScore(*value)
                + (value[0] + value[2],)  # value[0] + value[2] = tp + fn
                for aspect, value in sorted(per_aspect.items())
            },
        }
    return out


def report(res):
    print(f"Số review chấm: {res['n']}  (thiếu trong dự đoán: {len(res['missing'])})")
    print(f"\nSentiment accuracy : {res['sentiment_accuracy']:.2%}")
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
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("So sánh hiệu năng: LLM vs Baseline", fontsize=16, fontweight="bold")

    def draw(ax, title, ylabel, data, rot=30):
        pd.DataFrame(data).fillna(0).plot(
            kind="bar", ax=ax, color=["#4C72B0", "#DD8452"], rot=rot
        )
        ax.set(title=title, ylabel=ylabel, ylim=(0, 1.08))

    draw(
        ax1,
        "Sentiment Accuracy",
        "Tỷ lệ đúng",
        {
            "LLM": {"Acc": resllm["sentiment_accuracy"]},
            "Baseline": {"Acc": resbaseline["sentiment_accuracy"]},
        },
        rot=0,
    )
    for c in ax1.containers:
        ax1.bar_label(c, fmt="{:.2%}", padding=3, fontweight="bold")

    for ax, field, title in [
        (ax2, "aspects_positive", "Aspects Positive (Khen)"),
        (ax3, "aspects_negative", "Aspects Negative (Chê)"),
    ]:
        draw(
            ax,
            f"F1-Score: {title}",
            "F1-Score",
            {
                m: {a: f1 for a, (_, _, f1, _) in res[field]["per_aspect"].items()}
                for m, res in [("LLM", resllm), ("Baseline", resbaseline)]
            },
        )

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def RunEvaluate():
    label = load("data/llm/label.json")
    llm = load("data/llm/llm-response.json")
    baseline = load("data/llm/baseline-comments.json")

    resllm = Evaluate(label, llm)
    report(resllm)

    resbaseline = Evaluate(label, baseline)
    report(resbaseline)

    res_serializable_llm = dict(resllm)
    res_serializable_llm["confusion"] = {
        f"{label_sentiment}->{prediction_sentiment}": count
        for (label_sentiment, prediction_sentiment), count in resllm[
            "confusion"
        ].items()
    }

    res_serializable_baseline = dict(resbaseline)
    res_serializable_baseline["confusion"] = {
        f"{label_sentiment}->{prediction_sentiment}": count
        for (label_sentiment, prediction_sentiment), count in resbaseline[
            "confusion"
        ].items()
    }
    with open("data/llm/out_evaluate_llm.json", "w", encoding="utf-8") as f:
        json.dump(res_serializable_llm, f, ensure_ascii=False, indent=2)

    with open("data/llm/out_evaluate_baseline.json", "w", encoding="utf-8") as f:
        json.dump(res_serializable_baseline, f, ensure_ascii=False, indent=2)

    plot_evaluation(resllm, resbaseline, out_path="figures/llm-baseline/comparison.png")
