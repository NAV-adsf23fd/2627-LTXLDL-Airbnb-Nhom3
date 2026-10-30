%cd /home/van/Documents/Coding/Projects/LTXLDL-UET26
import pandas as pd
import yaml
import sys
#%%

try:
    with open("configs/paris.yaml", "r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
except OSError:
    print("Could not read file")
    sys.exit()

team_rv = pd.read_csv("data/processed/team-review.csv")
review_list = []

for t in config["snapshots"]:
    time = t.strftime("%Y-%m-%d")
    path = f"data/raw/{time}/{time}_reviews.csv.gz"
    rv = pd.read_csv(path).set_index("id")["comments"]
    mrv = rv.to_frame().merge(team_rv[["review_id", "Mẫu LLM"]], left_on="id", right_on="review_id", how="right")
    mrv = mrv[mrv["Mẫu LLM"].notna()].drop(columns=["Mẫu LLM"])
    review_list.append(mrv)

#%%
reviews = pd.concat(review_list, axis=0, ignore_index=False).drop_duplicates(subset=["review_id"], keep="last").set_index("review_id").dropna()

reviews["comments"] = reviews["comments"].str.replace(r"\r?<br/>", "", regex=True)


#%%
reviews.to_csv("data/processed/reviews.csv")

#%%
verbose = False
reviews = pd.read_csv("data/processed/reviews.csv")
if verbose:
    print(reviews[reviews["comments"].isna()], "\n")
    print((reviews.isna()).sum(), "\n")
    print(len(reviews.dropna()), "\n")

reviews = reviews.dropna()
reviews["comments"] = reviews["comments"].str.replace(r"\r?<br>", "", regex=True)
if verbose:
    print(reviews.head())

reviews[["review_id", "comments"]].set_index("review_id").to_csv("data/processed/reviews.csv")
#print(reviews[["review_id", "comments"]])
#print(reviews.info())

#%%
listrv = []
for t in config["snapshots"]:
    time = t.strftime("%Y-%m-%d")
    path = f"data/raw/{time}/{time}_reviews.csv.gz"
    rv = pd.read_csv(path).set_index("id")["comments"]
    listrv.append(rv)


    

    
