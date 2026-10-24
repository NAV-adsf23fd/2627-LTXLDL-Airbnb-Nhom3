import pandas as pd
import yaml

def clean_percent(val):
    if pd.isna(val): 
        return val # Giữ nguyên NaN
    if isinstance(val, (int, float)): 
        return float(val) # Nếu là số sẵn thì chỉ ép về float
    # Nếu là chuỗi thì xóa % và đổi sang float
    return float(str(val).replace("%", ""))


process = pd.read_csv(r"D:\Bài Tập\BaitaplonLTXLDL\2627-LTXLDL-Airbnb-Nhom3\data\processed\team-listings.csv")
areas = pd.read_csv(r"D:\Bài Tập\BaitaplonLTXLDL\2627-LTXLDL-Airbnb-Nhom3\data\processed\team-vung.csv")
revs = pd.read_csv(r"D:\Bài Tập\BaitaplonLTXLDL\2627-LTXLDL-Airbnb-Nhom3\data\processed\team-review.csv")
with open("configs/paris.yaml", "r",encoding="utf-8") as f:
    df = yaml.load(f,Loader=yaml.SafeLoader)
df["snapshots"]



#listings
for i in df["snapshots"]:
    tmp = "data/raw/"+ i.strftime("%Y-%m-%d") + "_listings.csv.gz"
    listings = pd.read_csv(tmp)
    abc=listings.merge(process,left_on="id",right_on="listing_id",how="right")
    ab = abc.merge(areas,on="analysis_area",how="left")
    ab = ab.drop(columns=["Lớp","Nhóm","Mã dữ liệu","listing_id","Unnamed: 0_x","Unnamed: 0_y"])
    ab["last_scraped"] = pd.to_datetime(ab["last_scraped"])
    ab["host_since"] = pd.to_datetime(ab["host_since"])
    ab["host_response_rate"] = ab["host_response_rate"].apply(clean_percent)
    ab["host_response_rate"] = ab["host_response_rate"]/100
    ab["bathrooms"] = ab["bathrooms_text"].str.extract(r'(\d+\.?\d*)').astype(float)
    ab["bathrooms_type"] = ab["bathrooms_text"].str.extract(r'([A-Za-z]+)')
    ab["calendar_last_scraped"] = pd.to_datetime(ab["calendar_last_scraped"])
    ab["first_review"] = pd.to_datetime(ab["first_review"])
    ab["last_review"] = pd.to_datetime(ab["last_review"])
    ab["host_is_superhost"] = ab["host_is_superhost"].map({"t":True,"f":False})
    print((ab["room_type"]=="Entire home/apt").sum())
    print((ab["room_type"]=="Private room").sum())
    print((ab["number_of_reviews"]==0).sum())
    print((ab["price"].isna()).sum())
    print(ab.loc[ab["analysis_area"]=="A01","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A02","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A03","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A04","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A05","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A06","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A07","id"].nunique())
    print(ab.loc[ab["analysis_area"]=="A08","id"].nunique())
    print(ab.info())



#calendar
for i in df["snapshots"]:
    tmp = "data/raw/"+ i.strftime("%Y-%m-%d") + "_calendar.csv.gz"
    calendar = pd.read_csv(tmp)
    abc = calendar.merge(process,on="listing_id",how="right")
    ab = abc.drop(columns=["Lớp","Nhóm","Mã dữ liệu","analysis_area","Unnamed: 0"])#xử lý cột dư ở một mốc ở dòng này
    ab["date"] = pd.to_datetime(ab["date"],format="%Y-%m-%d")
    ab["available"] = ab["available"].map({"t":True, "f":False})
    print(ab.info())



#reviews
for i in df["snapshots"]:
    tmp = "data/raw/" + i.strftime("%Y-%m-%d") + "_reviews.csv.gz"
    reviews = pd.read_csv(tmp)
    abc = reviews.merge(revs,left_on="id",right_on="review_id",how="right")
    ab = abc.drop(columns=["Lớp","Nhóm","Mã dữ liệu","Mẫu LLM","Nhãn tay","listing_id_y","Unnamed: 0","review_id"])
    ab = ab.rename(columns={"listing_id_x":"listing_id"})
    ab["date"] = pd.to_datetime(ab["date"],format="%Y-%m-%d")
    print(ab.info())


for i in df["snapshots"]:
    tmp = "data/raw/" + i.strftime("%Y-%m-%d") + "_reviews.csv.gz"
    reviews = pd.read_csv(tmp)
    abc = reviews.merge(revs,left_on="id",right_on="review_id",how="right")
    abc = abc.rename(columns={"listing_id_x":"listing_id"})
    abc["date"] = pd.to_datetime(abc["date"],format="%Y-%m-%d")
    abc = abc[
        abc["Mẫu LLM"] == "x"
    ]
    ab = abc.drop(columns=["Lớp","Nhóm","Mã dữ liệu","Nhãn tay","Mẫu LLM","listing_id_y","Unnamed: 0","review_id"])
    #dùng sql truy vấn chắc là nhanh hơn ngắn hơn nhiều:v
    print(ab.info())


for i in df["snapshots"]:
    tmp = "data/raw/" + i.strftime("%Y-%m-%d") + "_reviews.csv.gz"
    reviews = pd.read_csv(tmp)
    abc = reviews.merge(revs,left_on="id",right_on="review_id",how="right")
    abc = abc.rename(columns={"listing_id_x":"listing_id"})
    abc["date"] = pd.to_datetime(abc["date"],format="%Y-%m-%d")
    abc = abc[
        abc["Nhãn tay"] == "x"
    ]
    ab = abc.drop(columns=["Lớp","Nhóm","Mã dữ liệu","Nhãn tay","Mẫu LLM","listing_id_y","Unnamed: 0","review_id"])
    #dùng sql truy vấn chắc là nhanh hơn ngắn hơn nhiều:v
    print(ab.info())