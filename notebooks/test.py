import pandas as pd
import numpy as np


# %%
nhom = 3
lop = "UET.DSE2049 4"

listings = pd.read_csv("../data/raw/pc-listings.csv")
newlistings = listings.loc[(listings["Nhóm"] == nhom) & (listings["Lớp"] == lop)]

review = pd.read_csv("../data/raw/pc-review.csv")
newreview = review.loc[(review["Nhóm"] == nhom) & (review["Lớp"] == lop)]

phancong = pd.read_csv("../data/raw/pc.csv")
newphancong = phancong.loc[(phancong["Nhóm"] == nhom) & (phancong["Lớp"] == lop)]

vung = pd.read_csv("../data/raw/pc-vung.csv")
newvung = vung.loc[(vung["Thành phố"] == "Paris")]

# %%

listings1 = pd.read_csv("../data/raw/2025-09-12_listings.csv.gz")
#print(listings1.loc[listings1["id"] == 220063])
#print(listings.loc[listings["listing_id"] == 220063])

#%%
review1 = pd.read_csv("../data/raw/2025-09-12_reviews.csv.gz")
id = 220063
reviewid = 609682
#print(review1.loc[(review1["listing_id"] == id)&(review1["id"] == reviewid)])
#print(review.loc[(review["listing_id"] == id) & (review["review_id"] == reviewid)])

banggop = review1.merge(newreview, left_on=["listing_id", "id"], right_on=["listing_id", "review_id"], how="inner")
