import json
import re

import numpy as np
import pandas as pd

from src.utility import Llm

ASPECT_POSITIVE = {
    "location": (
        r"great location|perfect location|amazing location|excellent location|"
        r"wonderful location|ideal location|good location|superb location|"
        r"fantastic location|lovely location|beautiful location|great spot|"
        r"perfect spot|perfectly located|great neighborhood|great neighbourhood|"
        r"beautiful neighborhood|beautiful neighbourhood|lovely neighborhood|"
        r"lovely neighbourhood|wonderful neighborhood|wonderful neighbourhood|"
        r"central|centrally located|convenient|conveniently|walkable|"
        r"walking distance|close to|near metro|near the metro|near station|"
        r"nearby|easy access|easy to reach|easy to get|well located|well-located|"
        r"great proximity|steps away|minutes from|right in the heart|heart of"
    ),
    "cleanliness": (
        r"clean|very clean|extremely clean|spotless|spotlessly clean|tidy|neat|"
        r"pristine|immaculate|well-maintained|well maintained|fresh|freshly|"
        r"great condition|pristine condition"
    ),
    "host": (
        r"helpful|very helpful|extremely helpful|friendly|welcoming|responsive|"
        r"very responsive|accommodating|attentive|kind|generous|thoughtful|"
        r"superhost|great host|amazing host|wonderful host|excellent host|"
        r"good host|perfect host|fantastic host|lovely host|communicative|"
        r"warm|hospitable|welcoming host|attentive host"
    ),
    "noise": (
        r"quiet|very quiet|peaceful|very peaceful|silent|silence|calm|tranquil|"
        r"no noise|quiet street|quiet area|soundproof|well soundproof"
    ),
    "amenities": (
        r"well equipped|well-equipped|fully equipped|fully stocked|well appointed|"
        r"well-appointed|great kitchen|has everything|everything we needed|"
        r"everything you need|comfortable bed|comfy bed|great shower|"
        r"good water pressure|great water pressure|air conditioning|air con|"
        r"heating|elevator|lift|balcony|terrace|garden|washer|dryer|"
        r"washing machine|great amenities|good amenities|excellent amenities|"
        r"fast wifi|great wifi|good wifi|wifi works"
    ),
    "value": (
        r"good value|great value|excellent value|good value for money|"
        r"value for money|worth the money|worth it|worth every penny|affordable|"
        r"reasonably priced|reasonable price|great price|good price|bargain|"
        r"cheap|inexpensive|great deal|good deal|perfect value|great for the price"
    ),
    "safety": (
        r"safe|very safe|felt safe|felt very safe|secure|well-lit|well lit|"
        r"safe area|safe neighborhood|safe neighbourhood|safe street|"
        r"residential area|secure building"
    ),
    "neighbors": (
        r"friendly neighbors|friendly neighbours|nice neighbors|nice neighbours|"
        r"great neighbors|great neighbours|quiet neighborhood|quiet neighbourhood|"
        r"lovely neighborhood|lovely neighbourhood|great neighborhood|"
        r"great neighbourhood|wonderful neighborhood|wonderful neighbourhood|"
        r"beautiful neighborhood|beautiful neighbourhood|friendly people|"
        r"friendly locals|nice people|lovely locals|great community"
    ),
}

ASPECT_NEGATIVE = {
    "location": (
        r"far from|far away|inconvenient|inconveniently|bad location|"
        r"poor location|terrible location|awful location|hard to reach|"
        r"hard to get to|difficult to reach|difficult to get to|not close|"
        r"not near|not central|remote|isolated"
    ),
    "cleanliness": (
        r"dirty|very dirty|unclean|filthy|grimy|dusty|dust|stained|stain|"
        r"smelly|smell|bad smell|bad odor|bad odour|odor|odour|mold|mould|"
        r"ants|bugs|insects|hair|not clean|poorly cleaned|needs cleaning|"
        r"needs a clean|stinks|stink|unhygienic|messy|untidy|"
        r"dirty bathroom|dirty floor|dirty kitchen"
    ),
    "host": (
        r"unhelpful|unfriendly|unresponsive|rude|ignored|ignore|unavailable|"
        r"not responsive|not helpful|not friendly|bad host|terrible host|"
        r"awful host|poor host|horrible host|poor communication|"
        r"bad communication|slow response|late response|not communicative|"
        r"inhospitable"
    ),
    "noise": (
        r"noisy|very noisy|noise|very loud|loud|too loud|disturbing|disturbance|"
        r"woken up|wake up|sleepless|couldn't sleep|construction|drilling|"
        r"renovation|barking|sirens|traffic noise|thin walls|thin wall|"
        r"no insulation|no soundproof|street noise|noisy neighbors|"
        r"noisy neighbours|loud neighbors|loud neighbours|noisy street|"
        r"loud street"
    ),
    "amenities": (
        r"broken|not working|doesn't work|didn't work|out of order|leak|leaking|"
        r"no wifi|no wi-fi|no internet|bad wifi|slow wifi|weak wifi|"
        r"no hot water|no heating|no air conditioning|no air con|no ac|"
        r"lack of amenities|poor amenities|missing amenities|no soap|no towels|"
        r"no shampoo|no toilet paper|no toiletries|uncomfortable bed|hard bed|"
        r"bad bed"
    ),
    "value": (
        r"expensive|very expensive|overpriced|pricey|poor value|bad value|"
        r"not worth|not worth the money|not worth it|waste of money|"
        r"too expensive|over priced|unreasonable price|not good value"
    ),
    "safety": (
        r"unsafe|very unsafe|dangerous|sketchy|risky|crime|criminal|felt unsafe|"
        r"not safe|not secure|scary|bad area|bad neighborhood|bad neighbourhood|"
        r"rough area|rough neighborhood|rough neighbourhood"
    ),
    "neighbors": (
        r"noisy neighbors|noisy neighbours|loud neighbors|loud neighbours|"
        r"bad neighbors|bad neighbours|rude neighbors|rude neighbours|"
        r"terrible neighbors|terrible neighbours|awful neighbors|"
        r"awful neighbours|unfriendly neighbors|unfriendly neighbours|"
        r"annoying neighbors|annoying neighbours"
    ),
}


def wrap_bounds(pattern):
    alts = [a.strip() for a in pattern.split("|") if a.strip()]
    return r"\b(?:" + "|".join(alts) + r")\b"


ASPECT_POSITIVE = {k: wrap_bounds(v) for k, v in ASPECT_POSITIVE.items()}
ASPECT_NEGATIVE = {k: wrap_bounds(v) for k, v in ASPECT_NEGATIVE.items()}


def ExtractAspectsRow(text):
    pos, neg = [], []
    for aspect in ASPECT_POSITIVE:
        p = len(re.findall(ASPECT_POSITIVE[aspect], text, flags=re.IGNORECASE))
        n = len(re.findall(ASPECT_NEGATIVE[aspect], text, flags=re.IGNORECASE))
        if p > n:
            pos.append(aspect)
        elif n > p:
            neg.append(aspect)
    return pos, neg


def SaveJson(comments, path):
    results = []
    for idx, row in comments.iterrows():
        pos = (
            row["aspects_positive"] if isinstance(row["aspects_positive"], list) else []
        )
        neg = (
            row["aspects_negative"] if isinstance(row["aspects_negative"], list) else []
        )

        results.append(
            {
                "review_id": str(idx),
                "info": {
                    "sentiment": row["sentiment"],
                    "aspects_positive": pos,
                    "aspects_negative": neg,
                    "language": "en",  # Mặc định tiếng Anh
                },
            }
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=4)


def RunBaseline():
    comments = pd.read_csv(Llm.files["reviews"], dtype={"review_id": "string"})
    comments = comments.set_index("review_id")

    extracted = comments["comments"].apply(ExtractAspectsRow)
    comments["aspects_positive"] = [x[0] for x in extracted]
    comments["aspects_negative"] = [x[1] for x in extracted]

    n_pos = comments["aspects_positive"].apply(len)
    n_neg = comments["aspects_negative"].apply(len)
    comments["sentiment"] = np.select(
        [n_pos > n_neg, n_pos < n_neg],
        ["positive", "negative"],
        default="mixed",
    )

    SaveJson(comments, Llm.files["comments"])
