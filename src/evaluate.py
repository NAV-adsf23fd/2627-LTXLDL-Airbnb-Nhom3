"""So sánh kết quả dự đoán (LLM / baseline) với nhãn tay (label.json).

Chạy:
    python src/evaluate.py --label label.json --pred data/llm/llm-response.json --out llm_eval.json
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

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
        raise ValueError("Không có review_id nào trùng giữa file nhãn tay và file dự đoán.")

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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="label.json")
    ap.add_argument("--pred", default="data/llm/llm-response.json")
    ap.add_argument("--out", default="llm_eval.json")
    a = ap.parse_args()

    res = evaluate(load(a.label), load(a.pred))
    report(res)

    res_serializable = dict(res)
    res_serializable["confusion"] = {
        f"{g}->{p}": c for (g, p), c in res["confusion"].items()
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res_serializable, f, ensure_ascii=False, indent=2)